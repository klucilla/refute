"""TESS data adapter: SPOC 2-minute light curves from MAST, cached in ``.cache/``.

``fetch`` (network) downloads every SPOC 120-s light curve of the target with
lightkurve, queries the TESS Input Catalog (TIC) through astroquery, and writes a
fetch manifest with SHA-256 hashes, source URLs and retrieval times.

``load`` (offline) reads only cached files, verifies every hash against the fetch
manifest, applies the SPOC quality bitmask, keeps ``PDCSAP_FLUX``, removes NaNs
and normalizes each sector by its median. It returns raw normalized data:
detrending is done by the analysis, not here.
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
    LightCurveData,
    ProductInfo,
    SectorInfo,
    StarInfo,
    TessData,
    btjd_to_year,
)

FETCH_SCHEMA = "refute-tess-fetch-1"
MAST_DOWNLOAD_URL = "https://mast.stsci.edu/api/v0.1/Download/file?uri="
TIC_SOURCE = "TESS Input Catalog via MAST (astroquery.mast.Catalogs, catalog='TIC')"


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

    tic_version = str(row["version"]) if "version" in columns else None
    return StarInfo(
        tic_id=int(tic_id),
        radius_rsun=col("rad"),
        radius_err_rsun=col("e_rad"),
        mass_msun=col("mass"),
        mass_err_msun=col("e_mass"),
        teff_k=col("Teff"),
        logg_cgs=col("logg"),
        tmag=col("Tmag"),
        tic_version=tic_version,
        source=TIC_SOURCE,
        retrieved_utc=_utc_now(),
    )


def _quality_bitmask_value(name: str) -> int | None:
    """Numeric value of lightkurve's named TESS quality bitmask."""
    try:
        from lightkurve.utils import TessQualityFlags
    except ImportError:
        return None
    if name == "default":
        return int(TessQualityFlags.DEFAULT_BITMASK)
    return None


class TessAdapter:
    """Implements :class:`refute.core.pack.DataAdapter` for TESS SPOC light curves."""

    def fetch(self, target: dict[str, Any], test_plan: dict[str, Any], cache_dir: Path) -> dict:
        import lightkurve as lk

        plan = TessTestPlan.model_validate(test_plan)
        data = plan.data
        tic_id = int(target["tic_id"])
        download_dir = Path(cache_dir) / "lightkurve"
        download_dir.mkdir(parents=True, exist_ok=True)
        query = f"TIC {tic_id}"
        result = lk.search_lightcurve(
            query, mission=data.mission, author=data.author, exptime=data.exptime_seconds
        )
        table = result.table
        if "target_name" in table.colnames:
            keep = [str(name).strip() == str(tic_id) for name in table["target_name"]]
            result = result[np.asarray(keep, dtype=bool)]
            table = result.table
        if len(result) == 0:
            raise DataError(f"no {data.author} {data.exptime_seconds}-s light curves for {query}")

        files = []
        for index in range(len(result)):
            row = table[index]
            lc = result[index].download(
                download_dir=str(download_dir),
                quality_bitmask=data.quality_bitmask,
                flux_column=data.flux_column,
            )
            if lc is None:
                raise DataError(f"download failed for {row['productFilename']}")
            path = Path(lc.meta["FILENAME"]).resolve()
            uri = str(row["dataURI"]) if "dataURI" in table.colnames else None
            files.append(
                {
                    "name": path.name,
                    "path": path.relative_to(Path(cache_dir).resolve()).as_posix(),
                    "format": "spoc-fits",
                    "sha256": sha256_file(path),
                    "bytes": path.stat().st_size,
                    "sector": int(lc.meta.get("SECTOR")),
                    "obs_id": str(row["obs_id"]) if "obs_id" in table.colnames else None,
                    "data_uri": uri,
                    "url": MAST_DOWNLOAD_URL + quote(uri, safe=":/") if uri else None,
                }
            )
        files.sort(key=lambda f: (f["sector"], f["name"]))
        star = query_tic(tic_id)
        manifest = {
            "schema": FETCH_SCHEMA,
            "tic_id": tic_id,
            "target_key": f"TIC-{tic_id}",
            "retrieved_utc": _utc_now(),
            "query": {
                "service": "MAST via lightkurve.search_lightcurve",
                "target": query,
                "mission": data.mission,
                "author": data.author,
                "exptime_seconds": data.exptime_seconds,
                "n_results": len(files),
            },
            "product": {
                "product": "TESS SPOC 2-min light curve (LC FITS)",
                "author": data.author,
                "exptime_seconds": data.exptime_seconds,
                "flux_column": data.flux_column,
                "quality_bitmask": data.quality_bitmask,
                "quality_bitmask_value": _quality_bitmask_value(data.quality_bitmask),
                "reader": f"lightkurve {_pkg_version('lightkurve')}",
            },
            "files": files,
            "star": star.to_dict(),
            "software": {
                "lightkurve": _pkg_version("lightkurve"),
                "astroquery": _pkg_version("astroquery"),
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
        if manifest.get("schema") != FETCH_SCHEMA:
            raise DataError(f"unsupported fetch manifest {path}")
        return load_from_manifest(manifest, Path(cache_dir), plan.data)


def _read_spoc(path: Path, data: DataParams) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
    import lightkurve as lk

    lc = lk.read(str(path), quality_bitmask=data.quality_bitmask, flux_column=data.flux_column)
    lc = lc.remove_nans().normalize()
    meta = {"camera": lc.meta.get("CAMERA"), "ccd": lc.meta.get("CCD")}
    return (
        np.asarray(lc.time.value, dtype=float),
        np.asarray(lc.flux.value, dtype=float),
        np.asarray(lc.flux_err.value, dtype=float),
        meta,
    )


def _read_npz(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
    with np.load(path) as archive:
        return (
            np.asarray(archive["time"], dtype=float),
            np.asarray(archive["flux"], dtype=float),
            np.asarray(archive["flux_err"], dtype=float),
            {"camera": None, "ccd": None},
        )


def load_from_manifest(manifest: dict[str, Any], cache_dir: Path, data: DataParams) -> TessData:
    times, fluxes, errors, sectors, years, infos = [], [], [], [], [], []
    for record in manifest["files"]:
        path = Path(cache_dir) / record["path"]
        if not path.is_file():
            raise DataError(f"cached file missing: {record['path']}")
        digest = sha256_file(path)
        if digest != record["sha256"]:
            raise DataError(f"cached file {record['name']} does not match its recorded SHA-256")
        if record["format"] == "spoc-fits":
            t, f, e, meta = _read_spoc(path, data)
        elif record["format"] == "synthetic-npz":
            t, f, e, meta = _read_npz(path)
        else:
            raise DataError(f"unknown file format {record['format']}")
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
                camera=meta.get("camera"),
                ccd=meta.get("ccd"),
                filename=record["name"],
                sha256=record["sha256"],
                url=record.get("url"),
            )
        )
    if not times:
        raise DataError("no usable cadences in the cached light curves")
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
    )
