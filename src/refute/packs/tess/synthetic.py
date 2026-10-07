"""Synthetic TESS-like light curves with injected signals (used by the test suite).

Nothing here touches the network. Signals are trapezoids: a planet transit at
phase 0, optional odd/even depth differences, and an optional eclipse at phase
0.5 (eclipsing binaries). White Gaussian noise and a slow sinusoidal trend can be
added. Each sector has two 13-day orbits separated by a 1-day downlink gap.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from refute.core.hashing import sha256_file
from refute.core.io import write_json
from refute.packs.tess.adapter import FETCH_SCHEMA, manifest_path
from refute.packs.tess.types import (
    LightCurveData,
    ProductInfo,
    SectorInfo,
    StarInfo,
    TessData,
    btjd_to_year,
)

# Sector start times (BTJD): one sector in 2018 and one in 2020.
TWO_YEARS = (1325.0, 2061.0)
THREE_YEARS = (1325.0, 1700.0, 2061.0)


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
) -> StarInfo:
    return StarInfo(
        tic_id=tic_id,
        radius_rsun=radius,
        radius_err_rsun=radius_err,
        mass_msun=mass,
        mass_err_msun=0.05 if mass else None,
        teff_k=5800.0,
        logg_cgs=logg,
        tmag=10.0,
        tic_version="synthetic",
        source="synthetic (refute.packs.tess.synthetic)",
        retrieved_utc=None,
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


def make_data(
    lc: LightCurveData, sectors: list[SectorInfo], star: StarInfo | None, tic_id: int = 1
) -> TessData:
    return TessData(
        target_key=f"TIC-{tic_id}",
        tic_id=tic_id,
        lc=lc,
        sectors=sectors,
        star=star,
        product=SYNTHETIC_PRODUCT,
        manifest={"files": [{"name": s.filename, "sha256": s.sha256} for s in sectors]},
    )


def write_synthetic_cache(
    cache_dir: Path,
    tic_id: int,
    lc: LightCurveData,
    star: StarInfo | None,
) -> dict:
    """Write a light curve into the cache in the adapter's format (offline end-to-end tests)."""
    cache_dir = Path(cache_dir)
    folder = cache_dir / "synthetic" / f"TIC-{tic_id}"
    folder.mkdir(parents=True, exist_ok=True)
    files = []
    for sector in lc.sectors:
        sel = lc.sector == sector
        path = folder / f"sector_{sector:02d}.npz"
        np.savez(path, time=lc.time[sel], flux=lc.flux[sel], flux_err=lc.flux_err[sel])
        files.append(
            {
                "name": path.name,
                "path": path.relative_to(cache_dir).as_posix(),
                "format": "synthetic-npz",
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
                "sector": int(sector),
                "obs_id": None,
                "data_uri": None,
                "url": None,
            }
        )
    manifest = {
        "schema": FETCH_SCHEMA,
        "tic_id": tic_id,
        "target_key": f"TIC-{tic_id}",
        "retrieved_utc": "synthetic",
        "query": {"service": "synthetic"},
        "product": SYNTHETIC_PRODUCT.to_dict(),
        "files": files,
        "star": star.to_dict() if star else None,
        "software": {},
    }
    write_json(manifest_path(cache_dir, tic_id), manifest)
    return manifest


# --- Named scenarios used by the test suite -------------------------------------------

FAST_SEARCH = {"period_max_days": 6.0, "durations_hours": [1.0, 2.0, 3.0, 4.0]}
PLANET = SignalSpec(period=3.7, t0=1326.3, depth=0.002, duration=2.5 / 24)
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
    else:
        raise ValueError(f"unknown scenario {name}")
    return make_data(lc, sectors, star)


def analyze_scenario(name: str):
    """Top-level (picklable) helper: full analysis of a named scenario with the fast plan."""
    from refute.packs.tess.params import TessTestPlan
    from refute.packs.tess.pipeline import analyze_data

    return analyze_data(scenario_data(name), TessTestPlan.model_validate(fast_plan_dict()))
