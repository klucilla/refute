"""Synthetic TESS-like data with injected signals (used by the test suite).

Nothing here touches the network. Signals are trapezoids: a planet transit at
phase 0, optional odd/even depth differences, and an optional eclipse at phase
0.5 (eclipsing binaries). White Gaussian noise and a slow sinusoidal trend can be
added. Each sector has two 13-day orbits separated by a 1-day downlink gap.

From v0.2 every scenario also has auxiliary data for the battery:

- a pixel scene per sector: the target (and optionally one neighbor) as Gaussian
  point-spread functions integrated over 11 x 11 pixels, a SPOC-like aperture
  (pixels holding at least 2% of the target's light) and the target position;
- SAP flux (the PDCSAP signal diluted by CROWDSAP), a flat background and
  momentum dumps every 3.3 days;
- the TIC neighbor list (empty unless a scenario adds a neighbor).

``write_synthetic_cache`` can write all of it as SPOC-like FITS files, so the
FITS readers of the adapter are exercised offline.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from refute.core.hashing import sha256_file
from refute.core.io import write_json
from refute.packs.tess.adapter import (
    FETCH_SCHEMA,
    FETCH_SCHEMA_V1,
    MOMENTUM_DUMP_BIT,
    manifest_path,
    product_info,
)
from refute.packs.tess.params import DataParams
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

# Sector start times (BTJD): one sector in 2018 and one in 2020.
TWO_YEARS = (1325.0, 2061.0)
THREE_YEARS = (1325.0, 1700.0, 2061.0)
PIXEL_SCALE_ARCSEC = 21.0
TARGET_RA, TARGET_DEC = 150.0, -30.0


@dataclass(frozen=True)
class SignalSpec:
    period: float
    t0: float
    depth: float
    duration: float
    ingress_fraction: float = 0.15
    secondary_depth: float = 0.0
    odd_depth_factor: float = 1.0


def sector_times(
    start: float, cadence_minutes: float = 2.0, orbit_days: float = 13.0
) -> np.ndarray:
    step = cadence_minutes / 1440.0
    first = np.arange(start, start + orbit_days, step)
    second = np.arange(start + orbit_days + 1.0, start + 2 * orbit_days + 1.0, step)
    return np.concatenate([first, second])


def trapezoid(
    time: np.ndarray,
    period: float,
    t0: float,
    depth: float,
    duration: float,
    ingress_fraction: float,
    phase: float = 0.0,
) -> np.ndarray:
    """Fractional flux deficit of a trapezoid signal centered at ``t0 + (n + phase) * P``."""
    dt = np.mod(time - t0 - phase * period + 0.5 * period, period) - 0.5 * period
    half = duration / 2.0
    ingress = max(ingress_fraction * duration, 1e-6)
    shape = np.clip((half - np.abs(dt)) / ingress, 0.0, 1.0)
    return depth * shape


def signal_model(time: np.ndarray, spec: SignalSpec) -> np.ndarray:
    deficit = trapezoid(
        time, spec.period, spec.t0, spec.depth, spec.duration, spec.ingress_fraction
    )
    if spec.odd_depth_factor != 1.0:
        epoch = np.round((time - spec.t0) / spec.period).astype(int)
        deficit = np.where(epoch % 2 != 0, deficit * spec.odd_depth_factor, deficit)
    if spec.secondary_depth > 0:
        deficit = deficit + trapezoid(
            time,
            spec.period,
            spec.t0,
            spec.secondary_depth,
            spec.duration,
            spec.ingress_fraction,
            phase=0.5,
        )
    return 1.0 - deficit


def make_lightcurve(
    spec: SignalSpec | None,
    *,
    sector_starts: tuple[float, ...] = TWO_YEARS,
    sector_numbers: tuple[int, ...] | None = None,
    noise_ppm: float = 600.0,
    trend_amplitude: float = 0.0,
    trend_period_days: float = 6.0,
    seed: int = 0,
    inject_years: tuple[int, ...] | None = None,
) -> tuple[LightCurveData, list[SectorInfo]]:
    """Synthetic light curve. ``spec=None`` gives pure noise.

    ``inject_years`` limits the injected signal to those observing years (used to
    build signals that are absent from a hidden year).
    """
    rng = np.random.default_rng(seed)
    numbers = sector_numbers or tuple(range(1, len(sector_starts) + 1))
    times, fluxes, errors, sectors, years, infos = [], [], [], [], [], []
    sigma = noise_ppm * 1e-6
    for number, start in zip(numbers, sector_starts, strict=True):
        t = sector_times(start)
        year = btjd_to_year(float(t.min()))
        model = np.ones_like(t)
        if spec is not None and (inject_years is None or year in inject_years):
            model = signal_model(t, spec)
        if trend_amplitude:
            model = model * (1.0 + trend_amplitude * np.sin(2 * np.pi * t / trend_period_days))
        f = model + rng.normal(0.0, sigma, t.size)
        times.append(t)
        fluxes.append(f)
        errors.append(np.full(t.size, sigma))
        sectors.append(np.full(t.size, number))
        years.append(np.full(t.size, year))
        infos.append(
            SectorInfo(
                sector=number,
                year=year,
                t_start=float(t.min()),
                t_end=float(t.max()),
                n_points=int(t.size),
                filename=f"synthetic_sector_{number:02d}.npz",
            )
        )
    lc = LightCurveData(
        np.concatenate(times),
        np.concatenate(fluxes),
        np.concatenate(errors),
        np.concatenate(sectors),
        np.concatenate(years),
    )
    return lc, infos


def make_star(
    tic_id: int = 1,
    radius: float | None = 1.0,
    radius_err: float | None = 0.05,
    mass: float | None = 1.0,
    logg: float | None = 4.44,
    tmag: float | None = 10.0,
    disposition: str | None = None,
) -> StarInfo:
    return StarInfo(
        tic_id=tic_id,
        radius_rsun=radius,
        radius_err_rsun=radius_err,
        mass_msun=mass,
        mass_err_msun=0.05 if mass else None,
        teff_k=5800.0,
        logg_cgs=logg,
        tmag=tmag,
        tic_version="synthetic",
        source="synthetic (refute.packs.tess.synthetic)",
        retrieved_utc=None,
        disposition=disposition,
        duplicate_id=None,
        ra_deg=TARGET_RA,
        dec_deg=TARGET_DEC,
    )


SYNTHETIC_PRODUCT = ProductInfo(
    product="synthetic light curve (refute.packs.tess.synthetic)",
    author="synthetic",
    exptime_seconds=120,
    flux_column="flux",
    quality_bitmask="none",
    quality_bitmask_value=None,
    reader="numpy.load",
)


# --- pixel scenes and auxiliary data ---------------------------------------------------


@dataclass(frozen=True)
class Scene:
    """A synthetic pixel scene: target and optional neighbor, Gaussian PSFs."""

    shape: tuple[int, int] = (11, 11)
    target_xy: tuple[float, float] = (5.0, 5.0)
    target_flux: float = 50_000.0
    psf_sigma: float = 0.9
    neighbor_xy: tuple[float, float] | None = None
    neighbor_ratio: float = 0.0
    pixel_noise: float = 5e-5
    aperture_min_fraction: float = 0.02


def psf_image(scene: Scene, xy: tuple[float, float]) -> np.ndarray:
    """Fraction of a Gaussian point source's light falling in each pixel."""
    ny, nx = scene.shape
    scale = math.sqrt(2.0) * scene.psf_sigma

    def edges(n: int, center: float) -> np.ndarray:
        bounds = np.arange(n + 1) - 0.5
        cdf = np.array([0.5 * (1.0 + math.erf((b - center) / scale)) for b in bounds])
        return np.diff(cdf)

    return np.outer(edges(ny, xy[1]), edges(nx, xy[0]))


def scene_aperture(scene: Scene) -> np.ndarray:
    return psf_image(scene, scene.target_xy) >= scene.aperture_min_fraction


def crowding(scene: Scene) -> float:
    """Fraction of the aperture's flux that comes from the target (SPOC CROWDSAP)."""
    aperture = scene_aperture(scene)
    target = float(psf_image(scene, scene.target_xy)[aperture].sum())
    other = 0.0
    if scene.neighbor_xy is not None:
        other = scene.neighbor_ratio * float(psf_image(scene, scene.neighbor_xy)[aperture].sum())
    return target / (target + other)


def render_pixels(
    sector: int,
    time: np.ndarray,
    target_series: np.ndarray,
    scene: Scene,
    rng: np.random.Generator,
    neighbor_series: np.ndarray | None = None,
) -> PixelData:
    """Flux cube: target (and neighbor) PSFs scaled by their relative flux series."""
    cube = scene.target_flux * target_series[:, None, None] * psf_image(scene, scene.target_xy)
    if scene.neighbor_xy is not None:
        series = np.ones(time.size) if neighbor_series is None else neighbor_series
        cube = cube + (
            scene.target_flux
            * scene.neighbor_ratio
            * series[:, None, None]
            * psf_image(scene, scene.neighbor_xy)
        )
    noise = scene.pixel_noise * scene.target_flux
    cube = cube + rng.normal(0.0, noise, cube.shape)
    return PixelData(
        sector=sector,
        time=time.copy(),
        flux=cube,
        flux_err=np.full(cube.shape, noise),
        aperture=scene_aperture(scene),
        target_xy=scene.target_xy,
        filename=f"synthetic_tpf_{sector:02d}.fits",
    )


def dump_times(start: float, end: float, spacing: float = 3.3, offset: float = 1.7) -> np.ndarray:
    return np.arange(start + offset, end, spacing)


def make_sector_aux(
    lc: LightCurveData,
    crowdsap: float,
    rng: np.random.Generator,
    dumps: dict[int, np.ndarray] | None = None,
    background_series: dict[int, np.ndarray] | None = None,
) -> list[SectorAux]:
    out = []
    for sector in lc.sectors:
        sel = lc.sector == sector
        t, f = lc.time[sel], lc.flux[sel]
        sap = 1.0 + crowdsap * (f - 1.0)
        bkg = 0.01 + rng.normal(0.0, 2e-5, t.size)
        if background_series is not None and sector in background_series:
            bkg = bkg + background_series[sector]
        sector_dumps = dumps[sector] if dumps is not None else dump_times(t.min(), t.max())
        out.append(
            SectorAux(
                sector=int(sector),
                time=t.copy(),
                pdcsap_flux=f.copy(),
                sap_flux=sap,
                sap_bkg=bkg,
                dump_times=np.asarray(sector_dumps, dtype=float),
                crowdsap=crowdsap,
                flfrcsap=0.9,
            )
        )
    return out


def make_aux(
    lc: LightCurveData,
    *,
    scene: Scene | None = None,
    neighbors: list[Neighbor] | None = None,
    seed: int = 0,
) -> AuxData:
    """Auxiliary data consistent with ``lc``: the target's light follows ``lc``."""
    scene = scene or Scene()
    rng = np.random.default_rng(seed + 1000)
    pixels = []
    for sector in lc.sectors:
        sel = lc.sector == sector
        pixels.append(render_pixels(int(sector), lc.time[sel], lc.flux[sel], scene, rng))
    return AuxData(
        sectors=make_sector_aux(lc, crowding(scene), rng),
        pixels=pixels,
        neighbors=list(neighbors or []),
        neighbor_radius_arcsec=120.0,
    )


def make_blend(
    neighbor_spec: SignalSpec,
    *,
    scene: Scene,
    sector_starts: tuple[float, ...] = TWO_YEARS,
    noise_ppm: float = 300.0,
    trend_amplitude: float = 0.0,
    seed: int = 0,
) -> tuple[LightCurveData, list[SectorInfo], AuxData]:
    """A blend: the neighbor carries the signal; the light curve is the SPOC-like
    crowding-corrected aperture photometry of the rendered pixels."""
    rng = np.random.default_rng(seed)
    base, sectors = make_lightcurve(
        None,
        sector_starts=sector_starts,
        noise_ppm=noise_ppm,
        trend_amplitude=trend_amplitude,
        seed=seed,
    )
    aperture = scene_aperture(scene)
    c = crowding(scene)
    flux = np.empty(len(base))
    pixels = []
    for sector in base.sectors:
        sel = base.sector == sector
        t = base.time[sel]
        px = render_pixels(
            int(sector), t, base.flux[sel], scene, rng, signal_model(t, neighbor_spec)
        )
        ap = px.flux[:, aperture].sum(axis=1)
        ap = ap / np.median(ap)
        flux[sel] = (ap - (1.0 - c)) / c
        pixels.append(px)
    lc = LightCurveData(base.time, flux, base.flux_err, base.sector, base.year)
    sep = math.dist(scene.target_xy, scene.neighbor_xy or scene.target_xy) * PIXEL_SCALE_ARCSEC
    neighbors = [
        Neighbor(
            tic_id=2,
            tmag=10.0 - 2.5 * math.log10(scene.neighbor_ratio),
            separation_arcsec=sep,
        )
    ]
    aux = AuxData(
        sectors=make_sector_aux(lc, c, rng),
        pixels=pixels,
        neighbors=neighbors,
        neighbor_radius_arcsec=120.0,
    )
    return lc, sectors, aux


def make_data(
    lc: LightCurveData,
    sectors: list[SectorInfo],
    star: StarInfo | None,
    tic_id: int = 1,
    aux: AuxData | None = None,
) -> TessData:
    return TessData(
        target_key=f"TIC-{tic_id}",
        tic_id=tic_id,
        lc=lc,
        sectors=sectors,
        star=star,
        product=SYNTHETIC_PRODUCT,
        manifest={"files": [{"name": s.filename, "sha256": s.sha256} for s in sectors]},
        aux=aux,
    )


# --- SPOC-like FITS files ----------------------------------------------------------------


def write_spoc_lightcurve_fits(
    path: Path, aux: SectorAux, flux_err: np.ndarray, camera: int = 1, ccd: int = 1
) -> Path:
    """A minimal SPOC-like light-curve file. Momentum dumps are extra flagged cadences."""
    from astropy.io import fits

    scale = 50_000.0
    dumps = np.asarray(aux.dump_times, dtype=float)
    time = np.concatenate([aux.time, dumps])
    order = np.argsort(time, kind="stable")
    n_dump = dumps.size

    def column(values: np.ndarray, fill: float) -> np.ndarray:
        return np.concatenate([values, np.full(n_dump, fill)])[order]

    quality = np.concatenate([np.zeros(aux.time.size), np.full(n_dump, MOMENTUM_DUMP_BIT)])
    columns = [
        fits.Column(name="TIME", format="D", array=time[order]),
        fits.Column(name="PDCSAP_FLUX", format="E", array=column(aux.pdcsap_flux * scale, 1.0)),
        fits.Column(name="PDCSAP_FLUX_ERR", format="E", array=column(flux_err * scale, 1.0)),
        fits.Column(name="SAP_FLUX", format="E", array=column(aux.sap_flux * scale, 1.0)),
        fits.Column(name="SAP_BKG", format="E", array=column(aux.sap_bkg * scale, 0.0)),
        fits.Column(name="QUALITY", format="J", array=quality[order].astype(np.int32)),
    ]
    primary = fits.PrimaryHDU()
    primary.header.update({"TELESCOP": "TESS", "SECTOR": aux.sector, "CAMERA": camera, "CCD": ccd})
    table = fits.BinTableHDU.from_columns(columns)
    table.header["CROWDSAP"] = aux.crowdsap
    table.header["FLFRCSAP"] = aux.flfrcsap
    fits.HDUList([primary, table]).writeto(path, overwrite=True)
    return path


def write_spoc_tpf_fits(path: Path, px: PixelData, ra: float, dec: float) -> Path:
    """A minimal SPOC-like target pixel file with a TAN WCS in the aperture HDU."""
    from astropy.io import fits

    n, ny, nx = px.flux.shape
    columns = [
        fits.Column(name="TIME", format="D", array=px.time),
        fits.Column(name="FLUX", format=f"{nx * ny}E", dim=f"({nx},{ny})", array=px.flux),
        fits.Column(name="FLUX_ERR", format=f"{nx * ny}E", dim=f"({nx},{ny})", array=px.flux_err),
        fits.Column(name="QUALITY", format="J", array=np.zeros(n, dtype=np.int32)),
    ]
    primary = fits.PrimaryHDU()
    primary.header.update({"TELESCOP": "TESS", "SECTOR": px.sector, "RA_OBJ": ra, "DEC_OBJ": dec})
    aperture = np.where(px.aperture, 3, 1).astype(np.int32)
    image = fits.ImageHDU(aperture, name="APERTURE")
    tx, ty = px.target_xy or (nx / 2, ny / 2)
    image.header.update(
        {
            "CTYPE1": "RA---TAN",
            "CTYPE2": "DEC--TAN",
            "CRVAL1": ra,
            "CRVAL2": dec,
            "CRPIX1": tx + 1.0,
            "CRPIX2": ty + 1.0,
            "CDELT1": -PIXEL_SCALE_ARCSEC / 3600.0,
            "CDELT2": PIXEL_SCALE_ARCSEC / 3600.0,
            "CUNIT1": "deg",
            "CUNIT2": "deg",
        }
    )
    fits.HDUList([primary, fits.BinTableHDU.from_columns(columns), image]).writeto(
        path, overwrite=True
    )
    return path


def _record(path: Path, cache_dir: Path, fmt: str, sector: int) -> dict:
    return {
        "name": path.name,
        "path": path.relative_to(cache_dir).as_posix(),
        "format": fmt,
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
        "sector": int(sector),
        "obs_id": None,
        "data_uri": None,
        "url": None,
    }


def write_synthetic_cache(
    cache_dir: Path,
    tic_id: int,
    lc: LightCurveData,
    star: StarInfo | None,
    aux: AuxData | None = None,
) -> dict:
    """Write synthetic data into the cache in the adapter's format (offline tests).

    Without ``aux`` the light curve is written as numpy files with a v1 manifest.
    With ``aux`` every sector is written as SPOC-like light-curve and target pixel
    FITS files with a v2 manifest, including the neighbor list.
    """
    cache_dir = Path(cache_dir)
    folder = cache_dir / "synthetic" / f"TIC-{tic_id}"
    folder.mkdir(parents=True, exist_ok=True)
    files, pixel_files = [], []
    if aux is None:
        for sector in lc.sectors:
            sel = lc.sector == sector
            path = folder / f"sector_{sector:02d}.npz"
            np.savez(path, time=lc.time[sel], flux=lc.flux[sel], flux_err=lc.flux_err[sel])
            files.append(_record(path, cache_dir, "synthetic-npz", sector))
        product = SYNTHETIC_PRODUCT.to_dict()
        schema = FETCH_SCHEMA_V1
    else:
        for sector_aux in aux.sectors:
            sel = lc.sector == sector_aux.sector
            path = folder / f"tess-s{sector_aux.sector:04d}-{tic_id:016d}_lc.fits"
            write_spoc_lightcurve_fits(path, sector_aux, lc.flux_err[sel])
            files.append(_record(path, cache_dir, "spoc-fits", sector_aux.sector))
        for px in aux.pixels:
            path = folder / f"tess-s{px.sector:04d}-{tic_id:016d}_tp.fits"
            write_spoc_tpf_fits(path, px, TARGET_RA, TARGET_DEC)
            pixel_files.append(_record(path, cache_dir, "spoc-tpf", px.sector))
        product = product_info(DataParams())
        schema = FETCH_SCHEMA
    manifest = {
        "schema": schema,
        "tic_id": tic_id,
        "target_key": f"TIC-{tic_id}",
        "retrieved_utc": "synthetic",
        "query": {"service": "synthetic"},
        "product": product,
        "files": files,
        "star": star.to_dict() if star else None,
        "software": {},
    }
    if aux is not None:
        manifest["pixel_files"] = pixel_files
        manifest["neighbors"] = {
            "source": "synthetic",
            "radius_arcsec": aux.neighbor_radius_arcsec,
            "retrieved_utc": "synthetic",
            "sources": [n.to_dict() for n in aux.neighbors or []],
        }
    write_json(manifest_path(cache_dir, tic_id), manifest)
    return manifest


# --- Named scenarios used by the test suite -------------------------------------------

FAST_SEARCH = {"period_max_days": 6.0, "durations_hours": [1.0, 2.0, 3.0, 4.0]}
PLANET = SignalSpec(period=3.7, t0=1326.3, depth=0.002, duration=2.5 / 24)
BLEND_SCENE = Scene(neighbor_xy=(7.0, 5.0), neighbor_ratio=0.3)
BLEND_NEIGHBOR = SignalSpec(period=2.3, t0=1325.8, depth=0.08, duration=2.0 / 24)
SINUSOID_PERIOD = 0.7
# v0.2.1 H7: a weak eclipse at this period under a stronger sinusoid at SINUSOID_PERIOD
# (2.9 / 0.7 is not commensurate), so the search finds the variability, not the eclipse.
# Scenario "fp_variability_dominates"; not in SCENARIOS (only the H7 tests use it).
FP_VARIABILITY_PERIOD = 2.9
# v0.2.1 H4: scenario "variability_train_only" (not in SCENARIOS): the planet_three_years
# transit plus a SINUSOID_PERIOD sinusoid present in 2018 and 2019 and absent in 2020.
VARIABILITY_TRAIN_YEARS = (2018, 2019)
SCENARIOS = (
    "planet",
    "planet_three_years",
    "noise",
    "eb_secondary",
    "eb_odd_even",
    "eb_equal",
    "vanishing",
    "no_radius",
    "single_year",
    "blend",
    "sinusoid",
)


def fast_plan_dict() -> dict:
    """A test plan with a narrower search, so the test suite runs quickly."""
    return {"search": dict(FAST_SEARCH)}


def scenario_data(name: str, seed: int = 3) -> TessData:
    """Synthetic data for a named scenario (see ``SCENARIOS``)."""
    star = make_star()
    trend = {"trend_amplitude": 0.002, "seed": seed}
    if name == "planet":
        lc, sectors = make_lightcurve(PLANET, **trend)
    elif name == "planet_three_years":
        lc, sectors = make_lightcurve(PLANET, sector_starts=THREE_YEARS, **trend)
    elif name == "noise":
        lc, sectors = make_lightcurve(None, **trend)
    elif name == "eb_secondary":
        spec = SignalSpec(
            period=2.9, t0=1326.1, depth=0.005, duration=3 / 24, secondary_depth=0.0015
        )
        lc, sectors = make_lightcurve(spec, **trend)
    elif name == "eb_odd_even":
        spec = SignalSpec(
            period=1.8, t0=1325.7, depth=0.006, duration=2 / 24, odd_depth_factor=0.75
        )
        lc, sectors = make_lightcurve(spec, **trend)
    elif name == "eb_equal":
        spec = SignalSpec(period=1.6, t0=1325.9, depth=0.2, duration=3 / 24, ingress_fraction=0.5)
        lc, sectors = make_lightcurve(spec, **trend)
    elif name == "vanishing":
        lc, sectors = make_lightcurve(PLANET, inject_years=(2018,), **trend)
    elif name == "no_radius":
        lc, sectors = make_lightcurve(PLANET, **trend)
        star = make_star(radius=None)
    elif name == "single_year":
        lc, sectors = make_lightcurve(PLANET, sector_starts=(1325.0, 1353.0), **trend)
    elif name == "blend":
        lc, sectors, aux = make_blend(
            BLEND_NEIGHBOR, scene=BLEND_SCENE, trend_amplitude=0.002, seed=seed
        )
        return make_data(lc, sectors, star, aux=aux)
    elif name == "sinusoid":
        lc, sectors = make_lightcurve(None, noise_ppm=600.0, seed=seed)
        wave = 0.004 * np.sin(2 * np.pi * (lc.time - 1325.3) / SINUSOID_PERIOD)
        lc = LightCurveData(lc.time, lc.flux + wave, lc.flux_err, lc.sector, lc.year)
    elif name == "variability_train_only":
        lc, sectors = make_lightcurve(PLANET, sector_starts=THREE_YEARS, **trend)
        wave = 0.004 * np.sin(2 * np.pi * (lc.time - 1325.3) / SINUSOID_PERIOD)
        wave = np.where(np.isin(lc.year, VARIABILITY_TRAIN_YEARS), wave, 0.0)
        lc = LightCurveData(lc.time, lc.flux + wave, lc.flux_err, lc.sector, lc.year)
    elif name == "fp_variability_dominates":
        spec = SignalSpec(period=FP_VARIABILITY_PERIOD, t0=1326.1, depth=0.001, duration=3 / 24)
        lc, sectors = make_lightcurve(spec, **trend)
        wave = 0.004 * np.sin(2 * np.pi * (lc.time - 1325.3) / SINUSOID_PERIOD)
        lc = LightCurveData(lc.time, lc.flux + wave, lc.flux_err, lc.sector, lc.year)
    else:
        raise ValueError(f"unknown scenario {name}")
    return make_data(lc, sectors, star, aux=make_aux(lc, seed=seed))


def analyze_scenario(name: str):
    """Top-level (picklable) helper: full analysis of a named scenario with the fast plan."""
    return analyze_scenario_seed((name, 3))


def analyze_scenario_seed(task: tuple[str, int]):
    """Top-level (picklable) helper: full analysis of ``(scenario name, seed)`` with the
    fast plan."""
    from refute.packs.tess.params import TessTestPlan
    from refute.packs.tess.pipeline import analyze_data

    name, seed = task
    return analyze_data(scenario_data(name, seed), TessTestPlan.model_validate(fast_plan_dict()))


def analyze_scenario_with_catalog(task: dict):
    """Top-level (picklable) helper: full analysis of ``task["name"]`` and
    ``task["seed"]`` with the fast plan and a synthetic eclipsing-binary catalog made
    of ``task["rows"]`` (``refute-eb-catalog-1`` rows), scanned around the target;
    ``task["eb_catalog"]`` overrides ``gauntlet.eb_catalog``."""
    from refute.packs.tess.ebcatalog import COLUMNS, parse_catalog
    from refute.packs.tess.params import TessTestPlan
    from refute.packs.tess.pipeline import analyze_data

    data = scenario_data(task["name"], task["seed"])
    plan = fast_plan_dict()
    plan["gauntlet"] = {"eb_catalog": dict(task.get("eb_catalog") or {})}
    rows = list(task.get("rows") or [])
    catalog = parse_catalog("\n".join([",".join(COLUMNS), *rows]) + "\n")
    scan = {
        "format": "refute-eb-catalog-scan-1",
        "radius_arcsec": 120.0,
        "snapshots": [{"file": "synthetic.csv", "sha256": "0" * 64, "rows": max(1, len(rows))}],
        "per_target": {data.target_key: {}},
    }
    return analyze_data(
        data, TessTestPlan.model_validate(plan), catalogs=catalog, catalog_scan=scan
    )


HIDDEN_REPLACEMENTS = ("noise", "signal", "nothing")


def replace_year_flux(lc: LightCurveData, year: int, variant: str, seed: int) -> LightCurveData:
    """``lc`` with the flux of one observing year replaced (times, errors, sectors and
    years kept): ``noise`` is white noise at the scenario level, ``signal`` a deep
    eclipse at another period plus that noise, ``nothing`` a constant flux."""
    if variant not in HIDDEN_REPLACEMENTS:
        raise ValueError(f"unknown replacement {variant}")
    rng = np.random.default_rng(10_000 + seed)
    sel = lc.year == year
    time = lc.time[sel]
    if variant == "nothing":
        new = np.ones(time.size)
    else:
        new = 1.0 + rng.normal(0.0, 600e-6, time.size)
        if variant == "signal":
            new -= trapezoid(time, 1.3, 1325.2, 0.02, 2.0 / 24, 0.15)
    flux = lc.flux.copy()
    flux[sel] = new
    return LightCurveData(lc.time, flux, lc.flux_err, lc.sector, lc.year)


def holdout_scenario_seed(task: dict):
    """Top-level (picklable) helper: the blind holdout alone for ``task["name"]`` and
    ``task["seed"]`` with the fast plan, ``task["holdout"]`` overriding
    ``holdout_by_year`` and an optional ``task["replace"] = (year, variant)``
    (see :func:`replace_year_flux`)."""
    from refute.packs.tess.holdout import run_holdout
    from refute.packs.tess.params import TessTestPlan

    plan = fast_plan_dict()
    plan["gauntlet"] = {"holdout_by_year": dict(task.get("holdout") or {})}
    data = scenario_data(task["name"], task["seed"])
    lc = data.lc
    if task.get("replace") is not None:
        year, variant = task["replace"]
        lc = replace_year_flux(lc, year, variant, task["seed"])
    return run_holdout(lc, data.sectors, TessTestPlan.model_validate(plan))
