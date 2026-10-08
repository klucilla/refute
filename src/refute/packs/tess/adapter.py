"""TESS data adapter: SPOC 2-minute light curves and target pixel files from MAST.

``fetch`` (network) downloads, one file at a time, every SPOC 120-s light curve
(and, from v0.2, every SPOC 120-s target pixel file) of the target with
lightkurve, checks that each file is complete (its size equals the size declared
by its FITS headers), queries the TESS Input Catalog (TIC) for the target and for
the sources around it, and writes a fetch manifest with SHA-256 hashes, source
URLs and retrieval times. A file found incomplete is deleted from the cache before
the error is raised, so a retry really downloads it again (issue #1).

``load`` (offline) reads only cached files, verifies every hash against the fetch
manifest and reads the FITS files directly with astropy:

- light curves: cadences with ``QUALITY & bitmask == 0`` (lightkurve's ``default``
  TESS bitmask, whose numeric value is recorded) and finite time, PDCSAP flux and
  error are kept; each sector is divided by its median PDCSAP flux. SAP flux and
  SAP background of the same cadences are kept for the v0.2 battery, and the
  times of every momentum dump (quality bit 32) are taken from the raw quality
  column before any cadence is removed;
- target pixel files: the background-subtracted flux cube, the SPOC optimal
  aperture (aperture image bit 2) and the target position from the file's WCS.
  Only the cadences kept in the same sector's light curve are used, so the pixel
  tests see the same data as the official SPOC light curve (a target pixel file
  also contains cadences whose PDCSAP flux SPOC left empty).

It returns raw normalized data: detrending is done by the analysis, not here.
"""

from __future__ import annotations

import json
import math
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any
from urllib.parse import quote

import numpy as np

from refute.core.hashing import sha256_file
from refute.core.io import read_json, write_json
from refute.packs.tess.params import DataParams, TessTestPlan
from refute.packs.tess.types import (
    AuxData,
    LightCurveData,
    Neighbor,
    PixelData,
    ProductInfo,
    SectorAux,
    SectorInfo,
    StarInfo,
    TessData,
    btjd_to_year,
)

FETCH_SCHEMA_V1 = "refute-tess-fetch-1"
FETCH_SCHEMA = "refute-tess-fetch-2"
SUPPORTED_SCHEMAS = (FETCH_SCHEMA_V1, FETCH_SCHEMA)
MAST_DOWNLOAD_URL = "https://mast.stsci.edu/api/v0.1/Download/file?uri="
TIC_SOURCE = "TESS Input Catalog via MAST (astroquery.mast.Catalogs, catalog='TIC')"
FITS_BLOCK = 2880
MOMENTUM_DUMP_BIT = 32
APERTURE_OPTIMAL_BIT = 2
CADENCE_MATCH_DAYS = 1e-5  # about 1 s; TESS 2-min cadences are 120 s apart


class DataError(Exception):
    """Cached data are missing, incomplete or do not match their recorded hashes."""


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _pkg_version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def manifest_path(cache_dir: Path, tic_id: int) -> Path:
    return Path(cache_dir) / "refute" / "tess" / f"TIC-{tic_id}.json"


def _float_or_none(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if np.ma.is_masked(value) or not math.isfinite(number):
        return None
    return number


def _str_or_none(value: Any) -> str | None:
    if value is None or np.ma.is_masked(value):
        return None
    text = str(value).strip()
    return text if text and text.lower() not in {"--", "nan", "none"} else None


# --- FITS completeness ---------------------------------------------------------------


def fits_expected_size(path: Path | str) -> int | None:
    """Size in bytes that a FITS file must have, from its headers alone.

    Every HDU is a header of 2880-byte blocks followed by its data, padded to a
    multiple of 2880 bytes. The data size is ``|BITPIX|/8 * GCOUNT * (PCOUNT +
    NAXIS1 * ... * NAXISn)``. Returns None if the headers cannot be parsed (for
    example because the file stops inside a header).
    """
    data = Path(path).read_bytes()
    offset, total = 0, 0
    while offset < len(data):
        cards: dict[str, str] = {}
        end_found = False
        while not end_found:
            block = data[offset : offset + FITS_BLOCK]
            if len(block) < FITS_BLOCK:
                return None
            offset += FITS_BLOCK
            total += FITS_BLOCK
            for i in range(0, FITS_BLOCK, 80):
                card = block[i : i + 80].decode("ascii", errors="replace")
                key = card[:8].strip()
                if key == "END":
                    end_found = True
                    break
                if card[8:10] == "= ":
                    cards[key] = card[10:].split("/")[0].strip()
        try:
            bitpix = abs(int(cards["BITPIX"]))
            naxis = int(cards["NAXIS"])
            dims = [int(cards[f"NAXIS{i}"]) for i in range(1, naxis + 1)]
            pcount = int(cards.get("PCOUNT", "0"))
            gcount = int(cards.get("GCOUNT", "1"))
        except (KeyError, ValueError):
            return None
        size = 0
        if naxis > 0:
            size = bitpix // 8 * gcount * (pcount + math.prod(dims))
        padded = -(-size // FITS_BLOCK) * FITS_BLOCK
        offset += padded
        total += padded
    return total


def check_fits_complete(path: Path | str) -> None:
    """Raise :class:`DataError` unless the file size equals the size its headers declare."""
    path = Path(path)
    expected = fits_expected_size(path)
    actual = path.stat().st_size
    if expected is None or expected != actual:
        raise DataError(
            f"incomplete FITS file {path.name}: {actual} bytes, headers declare "
            f"{expected if expected is not None else 'unreadable headers'}"
        )


def discard_if_incomplete(path: Path, cache_root: Path) -> bool:
    """Delete a cached FITS file that is incomplete. Only files inside the cache are touched."""
    path = Path(path).resolve()
    if not path.is_file() or Path(cache_root).resolve() not in path.parents:
        return False
    try:
        check_fits_complete(path)
    except DataError:
        path.unlink()
        return True
    return False


def download_checked(product: Any, row_name: str, download_dir: Path, **kwargs: Any) -> Path:
    """Download one product with lightkurve and check that the file is complete.

    If the download fails or the file is incomplete, any incomplete cached copy is
    deleted before the error is raised, so the next attempt downloads it again.
    """
    download_dir = Path(download_dir)
    try:
        obj = product.download(download_dir=str(download_dir), **kwargs)
    except Exception as exc:  # noqa: BLE001 - re-raised as DataError after cleanup
        removed = [
            p for p in download_dir.rglob(row_name) if discard_if_incomplete(p, download_dir)
        ]
        note = f"; removed {len(removed)} incomplete cached file(s)" if removed else ""
        raise DataError(f"download failed for {row_name}: {exc}{note}") from exc
    if obj is None:
        raise DataError(f"download failed for {row_name}")
    path = Path(getattr(obj, "path", None) or obj.meta["FILENAME"]).resolve()
    if discard_if_incomplete(path, download_dir):
        raise DataError(f"incomplete download of {row_name}; the cached file was removed")
    return path


# --- TIC -----------------------------------------------------------------------------


def query_tic(tic_id: int) -> StarInfo:
    """Stellar parameters from the TIC (network)."""
    from astroquery.mast import Catalogs

    table = Catalogs.query_criteria(catalog="Tic", ID=int(tic_id))
    if len(table) == 0:
        raise DataError(f"TIC {tic_id} not found in the TESS Input Catalog")
    row = table[0]
    columns = set(table.colnames)

    def col(name: str) -> float | None:
        return _float_or_none(row[name]) if name in columns else None

    def text(name: str) -> str | None:
        return _str_or_none(row[name]) if name in columns else None

    return StarInfo(
        tic_id=int(tic_id),
        radius_rsun=col("rad"),
        radius_err_rsun=col("e_rad"),
        mass_msun=col("mass"),
        mass_err_msun=col("e_mass"),
        teff_k=col("Teff"),
        logg_cgs=col("logg"),
        tmag=col("Tmag"),
        tic_version=text("version"),
        source=TIC_SOURCE,
        retrieved_utc=_utc_now(),
        disposition=text("disposition"),
        duplicate_id=text("duplicate_id"),
        ra_deg=col("ra"),
        dec_deg=col("dec"),
    )


def query_neighbors(star: StarInfo, radius_arcsec: float) -> dict[str, Any]:
    """TIC sources within ``radius_arcsec`` of the target (network)."""
    import astropy.units as u
    from astropy.coordinates import SkyCoord
    from astroquery.mast import Catalogs

    if star.ra_deg is None or star.dec_deg is None:
        raise DataError(f"TIC {star.tic_id} has no coordinates; cannot query neighbors")
    center = SkyCoord(star.ra_deg * u.deg, star.dec_deg * u.deg)
    table = Catalogs.query_region(center, radius=radius_arcsec * u.arcsec, catalog="TIC")
    columns = set(table.colnames)
    rows = []
    for row in table:
        tic = int(row["ID"])
        if tic == star.tic_id:
            continue
        ra, dec = _float_or_none(row["ra"]), _float_or_none(row["dec"])
        if ra is None or dec is None:
            continue
        sep = float(center.separation(SkyCoord(ra * u.deg, dec * u.deg)).arcsec)
        rows.append(
            Neighbor(
                tic_id=tic,
                tmag=_float_or_none(row["Tmag"]) if "Tmag" in columns else None,
                separation_arcsec=sep,
                disposition=_str_or_none(row["disposition"]) if "disposition" in columns else None,
            ).to_dict()
        )
    rows.sort(key=lambda n: (n["separation_arcsec"], n["tic_id"]))
    return {
        "source": TIC_SOURCE + ", cone query (query_region)",
        "radius_arcsec": radius_arcsec,
        "retrieved_utc": _utc_now(),
        "sources": rows,
    }


def _quality_bitmask_value(name: str) -> int | None:
    """Numeric value of lightkurve's named TESS quality bitmask."""
    try:
        from lightkurve.utils import TessQualityFlags
    except ImportError:
        return None
    if name == "default":
        return int(TessQualityFlags.DEFAULT_BITMASK)
    return None


# --- fetch ---------------------------------------------------------------------------


def _file_record(path: Path, cache_dir: Path, fmt: str, row: Any, table: Any) -> dict[str, Any]:
    from astropy.io import fits

    uri = str(row["dataURI"]) if "dataURI" in table.colnames else None
    return {
        "name": path.name,
        "path": path.relative_to(Path(cache_dir).resolve()).as_posix(),
        "format": fmt,
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
        "sector": int(fits.getheader(path, 0)["SECTOR"]),
        "obs_id": str(row["obs_id"]) if "obs_id" in table.colnames else None,
        "data_uri": uri,
        "url": MAST_DOWNLOAD_URL + quote(uri, safe=":/") if uri else None,
    }


def _matching(result: Any, tic_id: int) -> Any:
    table = result.table
    if "target_name" in table.colnames:
        keep = [str(name).strip() == str(tic_id) for name in table["target_name"]]
        result = result[np.asarray(keep, dtype=bool)]
    return result


def product_info(data: DataParams) -> dict[str, Any]:
    return {
        "product": "TESS SPOC 2-min light curve (LC FITS)",
        "author": data.author,
        "exptime_seconds": data.exptime_seconds,
        "flux_column": data.flux_column,
        "quality_bitmask": data.quality_bitmask,
        "quality_bitmask_value": _quality_bitmask_value(data.quality_bitmask),
        "reader": f"astropy {_pkg_version('astropy')} (astropy.io.fits)",
    }


class TessAdapter:
    """Implements :class:`refute.core.pack.DataAdapter` for TESS SPOC data."""

    def fetch(self, target: dict[str, Any], test_plan: dict[str, Any], cache_dir: Path) -> dict:
        import lightkurve as lk

        plan = TessTestPlan.model_validate(test_plan)
        data = plan.data
        tic_id = int(target["tic_id"])
        download_dir = Path(cache_dir) / "lightkurve"
        download_dir.mkdir(parents=True, exist_ok=True)
        query = f"TIC {tic_id}"
        result = _matching(
            lk.search_lightcurve(
                query, mission=data.mission, author=data.author, exptime=data.exptime_seconds
            ),
            tic_id,
        )
        if len(result) == 0:
            raise DataError(f"no {data.author} {data.exptime_seconds}-s light curves for {query}")
        files = []
        table = result.table
        for index in range(len(result)):  # one file at a time (issue #1)
            row = table[index]
            path = download_checked(result[index], str(row["productFilename"]), download_dir)
            files.append(_file_record(path, cache_dir, "spoc-fits", row, table))

        pixel_files = []
        if data.target_pixel_files:
            tpfs = _matching(
                lk.search_targetpixelfile(
                    query, mission=data.mission, author=data.author, exptime=data.exptime_seconds
                ),
                tic_id,
            )
            tpf_table = tpfs.table
            for index in range(len(tpfs)):
                row = tpf_table[index]
                path = download_checked(
                    tpfs[index], str(row["productFilename"]), download_dir, quality_bitmask="none"
                )
                pixel_files.append(_file_record(path, cache_dir, "spoc-tpf", row, tpf_table))

        files.sort(key=lambda f: (f["sector"], f["name"]))
        pixel_files.sort(key=lambda f: (f["sector"], f["name"]))
        star = query_tic(tic_id)
        neighbors = query_neighbors(star, data.neighbor_radius_arcsec)
        manifest = {
            "schema": FETCH_SCHEMA,
            "tic_id": tic_id,
            "target_key": f"TIC-{tic_id}",
            "retrieved_utc": _utc_now(),
            "query": {
                "service": "MAST via lightkurve.search_lightcurve and search_targetpixelfile",
                "target": query,
                "mission": data.mission,
                "author": data.author,
                "exptime_seconds": data.exptime_seconds,
                "n_results": len(files),
                "n_pixel_files": len(pixel_files),
            },
            "product": product_info(data),
            "files": files,
            "pixel_files": pixel_files,
            "star": star.to_dict(),
            "neighbors": neighbors,
            "software": {
                "lightkurve": _pkg_version("lightkurve"),
                "astroquery": _pkg_version("astroquery"),
                "astropy": _pkg_version("astropy"),
            },
        }
        write_json(manifest_path(cache_dir, tic_id), manifest)
        return manifest

    def load(self, target: dict[str, Any], test_plan: dict[str, Any], cache_dir: Path) -> TessData:
        plan = TessTestPlan.model_validate(test_plan)
        tic_id = int(target["tic_id"])
        path = manifest_path(cache_dir, tic_id)
        if not path.is_file():
            raise DataError(
                f"no cached data for TIC {tic_id}: run without --offline (or `refute fetch`)"
            )
        manifest = read_json(path)
        if manifest.get("schema") not in SUPPORTED_SCHEMAS:
            raise DataError(f"unsupported fetch manifest {path}")
        return load_from_manifest(manifest, Path(cache_dir), plan.data)


# --- readers -------------------------------------------------------------------------


def read_spoc_lightcurve(path: Path, bitmask: int) -> dict[str, Any]:
    """Read a SPOC light-curve FITS file with astropy (see the module docstring)."""
    from astropy.io import fits

    with fits.open(path, memmap=False) as hdul:
        header0, header1 = hdul[0].header, hdul[1].header
        table = hdul[1].data
        names = set(table.columns.names)
        time = np.asarray(table["TIME"], dtype=float)
        flux = np.asarray(table["PDCSAP_FLUX"], dtype=float)
        err = np.asarray(table["PDCSAP_FLUX_ERR"], dtype=float)
        quality = np.asarray(table["QUALITY"], dtype=np.int64)
        sap = np.asarray(table["SAP_FLUX"], dtype=float) if "SAP_FLUX" in names else None
        bkg = np.asarray(table["SAP_BKG"], dtype=float) if "SAP_BKG" in names else None
        crowd = _float_or_none(header1.get("CROWDSAP"))
        flfrc = _float_or_none(header1.get("FLFRCSAP"))
        camera, ccd = header0.get("CAMERA"), header0.get("CCD")
    dumps = time[((quality & MOMENTUM_DUMP_BIT) != 0) & np.isfinite(time)]
    keep = (quality & bitmask) == 0
    keep &= np.isfinite(time) & np.isfinite(flux) & np.isfinite(err)
    median = float(np.nanmedian(flux[keep])) if np.any(keep) else float("nan")
    out: dict[str, Any] = {
        "time": time[keep],
        "flux": flux[keep] / median,
        "flux_err": err[keep] / median,
        "camera": int(camera) if camera is not None else None,
        "ccd": int(ccd) if ccd is not None else None,
        "dump_times": np.sort(dumps),
        "crowdsap": crowd,
        "flfrcsap": flfrc,
        "sap_flux": None,
        "sap_bkg": None,
    }
    if sap is not None and bkg is not None:
        sap_k, bkg_k = sap[keep], bkg[keep]
        sap_median = float(np.nanmedian(sap_k)) if sap_k.size else float("nan")
        out["sap_flux"] = sap_k / sap_median
        out["sap_bkg"] = bkg_k / sap_median
    return out


def _target_xy(hdul: Any) -> tuple[float, float] | None:
    """Target position in array coordinates, from the aperture HDU's WCS."""
    import warnings

    from astropy.wcs import WCS, FITSFixedWarning

    ra, dec = hdul[0].header.get("RA_OBJ"), hdul[0].header.get("DEC_OBJ")
    if ra is None or dec is None:
        return None
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FITSFixedWarning)
            wcs = WCS(hdul[2].header)
        if not wcs.has_celestial:
            return None
        x, y = wcs.celestial.all_world2pix([[float(ra), float(dec)]], 0)[0]
    except Exception:  # noqa: BLE001 - an unreadable WCS means "position unknown"
        return None
    if not (math.isfinite(x) and math.isfinite(y)):
        return None
    return float(x), float(y)


def read_spoc_tpf(path: Path, bitmask: int) -> dict[str, Any]:
    """Read a SPOC target pixel file with astropy: flux cube, aperture and target position."""
    from astropy.io import fits

    with fits.open(path, memmap=False) as hdul:
        table = hdul[1].data
        time = np.asarray(table["TIME"], dtype=float)
        flux = np.asarray(table["FLUX"], dtype=float)
        err = np.asarray(table["FLUX_ERR"], dtype=float)
        quality = np.asarray(table["QUALITY"], dtype=np.int64)
        aperture = (np.asarray(hdul[2].data, dtype=np.int64) & APERTURE_OPTIMAL_BIT) != 0
        target = _target_xy(hdul)
    keep = ((quality & bitmask) == 0) & np.isfinite(time)
    keep &= np.isfinite(flux).reshape(flux.shape[0], -1).any(axis=1)
    return {
        "time": time[keep],
        "flux": flux[keep],
        "flux_err": err[keep],
        "aperture": aperture,
        "target_xy": target,
    }


def matching_cadences(reference: np.ndarray, times: np.ndarray) -> np.ndarray:
    """Mask of ``times`` that equal a time in ``reference`` within CADENCE_MATCH_DAYS."""
    reference = np.sort(np.asarray(reference, dtype=float))
    times = np.asarray(times, dtype=float)
    if reference.size == 0 or times.size == 0:
        return np.zeros(times.size, dtype=bool)
    index = np.clip(np.searchsorted(reference, times), 1, reference.size - 1)
    nearest = np.minimum(np.abs(times - reference[index - 1]), np.abs(times - reference[index]))
    if reference.size == 1:
        nearest = np.abs(times - reference[0])
    return nearest <= CADENCE_MATCH_DAYS


def _read_npz(path: Path) -> dict[str, Any]:
    with np.load(path) as archive:
        return {
            "time": np.asarray(archive["time"], dtype=float),
            "flux": np.asarray(archive["flux"], dtype=float),
            "flux_err": np.asarray(archive["flux_err"], dtype=float),
            "camera": None,
            "ccd": None,
        }


def _bitmask(manifest: dict[str, Any], data: DataParams) -> int:
    value = (manifest.get("product") or {}).get("quality_bitmask_value")
    if value is None:
        value = _quality_bitmask_value(data.quality_bitmask)
    if value is None:
        raise DataError("cannot determine the numeric value of the quality bitmask")
    return int(value)


def _verified(record: dict[str, Any], cache_dir: Path) -> Path:
    path = Path(cache_dir) / record["path"]
    if not path.is_file():
        raise DataError(f"cached file missing: {record['path']}")
    if sha256_file(path) != record["sha256"]:
        raise DataError(f"cached file {record['name']} does not match its recorded SHA-256")
    return path


def load_from_manifest(manifest: dict[str, Any], cache_dir: Path, data: DataParams) -> TessData:
    times, fluxes, errors, sectors, years, infos = [], [], [], [], [], []
    aux_sectors: list[SectorAux] = []
    for record in manifest["files"]:
        path = _verified(record, cache_dir)
        if record["format"] == "spoc-fits":
            read = read_spoc_lightcurve(path, _bitmask(manifest, data))
        elif record["format"] == "synthetic-npz":
            read = _read_npz(path)
        else:
            raise DataError(f"unknown file format {record['format']}")
        t, f, e = read["time"], read["flux"], read["flux_err"]
        good = np.isfinite(t) & np.isfinite(f) & np.isfinite(e)
        t, f, e = t[good], f[good], e[good]
        if t.size == 0:
            continue
        year = btjd_to_year(float(t.min()))
        sector = int(record["sector"])
        times.append(t)
        fluxes.append(f)
        errors.append(e)
        sectors.append(np.full(t.size, sector))
        years.append(np.full(t.size, year))
        infos.append(
            SectorInfo(
                sector=sector,
                year=year,
                t_start=float(t.min()),
                t_end=float(t.max()),
                n_points=int(t.size),
                camera=read.get("camera"),
                ccd=read.get("ccd"),
                filename=record["name"],
                sha256=record["sha256"],
                url=record.get("url"),
            )
        )
        if read.get("sap_flux") is not None:
            aux_sectors.append(
                SectorAux(
                    sector=sector,
                    time=t,
                    pdcsap_flux=f,
                    sap_flux=read["sap_flux"][good],
                    sap_bkg=read["sap_bkg"][good],
                    dump_times=read["dump_times"],
                    crowdsap=read["crowdsap"],
                    flfrcsap=read["flfrcsap"],
                )
            )
    if not times:
        raise DataError("no usable cadences in the cached light curves")

    pixels: list[PixelData] = []
    for record in manifest.get("pixel_files", []):
        path = _verified(record, cache_dir)
        if record["format"] != "spoc-tpf":
            raise DataError(f"unknown pixel file format {record['format']}")
        read = read_spoc_tpf(path, _bitmask(manifest, data))
        sector = int(record["sector"])
        lc_times = [t for t, s in zip(times, sectors, strict=True) if int(s[0]) == sector]
        keep = matching_cadences(lc_times[0] if lc_times else np.zeros(0), read["time"])
        pixels.append(
            PixelData(
                sector=sector,
                time=read["time"][keep],
                flux=read["flux"][keep],
                flux_err=read["flux_err"][keep],
                aperture=read["aperture"],
                target_xy=read["target_xy"],
                filename=record["name"],
                sha256=record["sha256"],
                n_dropped_cadences=int((~keep).sum()),
            )
        )

    aux = None
    if manifest.get("schema") == FETCH_SCHEMA:
        record = manifest.get("neighbors")
        aux = AuxData(
            sectors=aux_sectors,
            pixels=pixels,
            neighbors=[Neighbor(**n) for n in record["sources"]] if record else None,
            neighbor_radius_arcsec=record.get("radius_arcsec") if record else None,
        )

    lc = LightCurveData(
        np.concatenate(times),
        np.concatenate(fluxes),
        np.concatenate(errors),
        np.concatenate(sectors),
        np.concatenate(years),
    )
    star_dict = manifest.get("star")
    star = StarInfo(**star_dict) if star_dict else None
    product = ProductInfo(**manifest["product"])
    return TessData(
        target_key=manifest["target_key"],
        tic_id=int(manifest["tic_id"]),
        lc=lc,
        sectors=sorted(infos, key=lambda s: s.t_start),
        star=star,
        product=product,
        manifest=json.loads(json.dumps(manifest)),
        aux=aux,
    )
