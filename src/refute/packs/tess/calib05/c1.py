"""C1 of the v0.5 calibration: the synthetic population study (the design frozen in
docs/plans/v0.5-acceptance.md, section C1, on 2026-11-03; calibration/v0.5/PROTOCOL.md, section 3).

- ``generate(family, seed)``: one star of a family with known truth: 2, 3 or 4 sectors at drawn
  starts (PA always 3), white noise log-uniform in [300, 3000] ppm, correlated noise (AR(1), half
  the white level, tau one hour) and a stellar trend each in half the stars (NW: white only; NR:
  correlated only), the trapezoid transit of the acceptance document with its depth solved from
  the target expected SNR by the fixed point (a generation failure is recorded, never redrawn),
  and the pixel data of ``synthetic.Scene`` with the sector-rotated Jacobian.
- ``run_task``: both batteries on the same candidate (``discover.paired.paired_chain``, stage 2:
  the full battery), with the identity of the shared candidate for the planet families.
- ``metrics``: per family and battery the four verdict counts in the eligible set, the number
  outside it by reason, Wilson 95 % intervals, the paired transitions, and the decision rules
  D1 to D5 (PASS, FAIL or NOT DECIDABLE; none blocks the phase).

Implementation choices fixed here (the acceptance document leaves them open): the sector numbers
are ``j + 1``; a star's parameters come from ``default_rng(seed)``, its white noise from
``default_rng([seed, 2])`` and its correlated noise from ``default_rng([seed, 3])``; sinusoids
and edge ramps are additive, the trend multiplicative; PA's artifact is in the pixels only (the
light curve is the target's); PX uses ``synthetic.make_blend_sky`` (the generator written for this
family, the neighbor at a fixed sky offset), with its stellar trend applied to the light curve
and to the PDCSAP and SAP series, not to the pixels. **PX's noise streams are an exception:**
``make_blend_sky`` draws the target's white noise from ``make_lightcurve``'s own
``default_rng(seed)``, its correlated noise from ``default_rng([seed, 1])``, and the pixel and
auxiliary noise from another ``default_rng(seed)``; PX's parameters come from ``default_rng(seed)``
as for every family. Each is a separate generator object, so no draw depends on another's order.
"""

from __future__ import annotations

import dataclasses
import hashlib
import math
import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from refute.packs.tess import synthetic as syn
from refute.packs.tess.calib05.values import C1
from refute.packs.tess.types import LightCurveData, SectorInfo, btjd_to_year

FAMILIES = tuple(C1.sizes)
PLANET_FAMILIES = ("P", "PG", "PV", "PA")
CADENCE_DAYS = 2.0 / 1440.0
TAU_DAYS = 1.0 / 24.0
GM_SUN = 1.32712440018e20  # m^3 s^-2
R_SUN = 6.957e8  # m
FIRST_START = 2000.0
SECTOR_STEP = 27.4
SECTOR_SLOTS = 30


class GenerationFailedError(Exception):
    """The star cannot be generated as specified (no convergence, no counted window, no
    transit, a neighbor depth above 1); recorded with its seed and reason, never redrawn."""


def development_seed(family: str, i: int) -> int:
    """Development seeds (construction checks and the cost prefix):
    ``int(SHA-256("refute-v05-c1-dev:<family>:<i>")[:16], 16)``."""
    text = f"{C1.seed_prefix}-dev:{family}:{i}"
    return int(hashlib.sha256(text.encode()).hexdigest()[:16], 16)


def confirmation_seed(randomness_hex: str, family: str, i: int) -> int:
    """Confirmation seeds (the acceptance document, C1, Seeds):
    ``int(SHA-256(<randomness hex> + "refute-v05-c1:<family>:<i>")[:16], 16)``."""
    text = f"{randomness_hex}{C1.seed_prefix}:{family}:{i}"
    return int(hashlib.sha256(text.encode()).hexdigest()[:16], 16)


# --- geometry and the expected SNR ------------------------------------------------------------


def a_over_rstar(period_days: float) -> float:
    """a / R_* from Kepler's third law for a 1.0 M_sun, 1.0 R_sun star."""
    p = period_days * 86400.0
    return (GM_SUN * p * p / (4.0 * math.pi**2)) ** (1.0 / 3.0) / R_SUN


def durations(period: float, k: float, b: float) -> tuple[float, float]:
    """Total and flat durations (days) of the acceptance document; raises GenerationFailedError when
    ``(1 + k)^2 <= b^2`` (no transit)."""
    if (1.0 + k) ** 2 <= b * b:
        raise GenerationFailedError("no transit: (1 + k)^2 <= b^2")
    ar = a_over_rstar(period)
    total = period / math.pi * math.asin(min(1.0, math.sqrt((1.0 + k) ** 2 - b * b) / ar))
    inner = max(0.0, (1.0 - k) ** 2 - b * b)
    flat = period / math.pi * math.asin(min(1.0, math.sqrt(inner) / ar))
    return total, flat


def ar1_mean_factor(x: float) -> float:
    """The variance of the mean of an AR(1) process over ``x`` correlation times, per unit
    variance: ``2 (x - 1 + exp(-x)) / x^2``."""
    return 2.0 * (x - 1.0 + math.exp(-x)) / (x * x)


def window_variances(
    time: np.ndarray, period: float, t0: float, duration: float, sigma_w: float, sigma_r: float
) -> list[float]:
    """For each counted transit window (holding at least half of a full window's cadences), the
    variance of its mean depth: ``sigma_w^2 / n_i + sigma_r^2 f(T / tau)``."""
    full = duration / CADENCE_DAYS
    first = math.ceil((time.min() - t0) / period - 0.5)
    last = math.floor((time.max() - t0) / period + 0.5)
    out = []
    sorted_time = np.sort(time)
    red = sigma_r**2 * ar1_mean_factor(duration / TAU_DAYS) if sigma_r > 0 else 0.0
    for n in range(first, last + 1):
        mid = t0 + n * period
        lo = np.searchsorted(sorted_time, mid - duration / 2.0, side="left")
        hi = np.searchsorted(sorted_time, mid + duration / 2.0, side="right")
        count = int(hi - lo)
        if count > 0 and count >= 0.5 * full:
            out.append(sigma_w**2 / count + red)
    return out


def sigma_total(variances: list[float]) -> float:
    if not variances:
        raise GenerationFailedError("no transit window counts")
    return 1.0 / math.sqrt(sum(1.0 / v for v in variances))


def solve_depth(
    time: np.ndarray,
    period_geom: float,
    period_windows: float,
    t0: float,
    b: float,
    target_snr: float,
    sigma_w: float,
    sigma_r: float,
    fold: float = 1.0,
) -> tuple[float, float, float]:
    """The fixed point of the acceptance document: from ``k_0 = 0``, ``T(k_j)`` at
    ``period_geom``, the windows at ``period_windows``, ``d_{j+1} = SNR sigma_tot / fold``,
    ``k_{j+1} = sqrt(d_{j+1})``, until ``|d_{j+1} - d_j| <= 1e-6 d_{j+1}``; at most 50 steps.
    Returns (depth, total duration, flat duration)."""
    depth, k = 0.0, 0.0
    for _ in range(50):
        total, flat = durations(period_geom, k, b)
        new = (
            target_snr
            * sigma_total(window_variances(time, period_windows, t0, total, sigma_w, sigma_r))
            / fold
        )
        if abs(new - depth) <= 1e-6 * new:
            total, flat = durations(period_geom, math.sqrt(new), b)
            return new, total, flat
        depth, k = new, math.sqrt(new)
    raise GenerationFailedError("the depth did not converge in 50 steps")


# --- the star -----------------------------------------------------------------------------


@dataclass
class Star:
    family: str
    seed: int
    starts: tuple[float, ...]
    numbers: tuple[int, ...]
    sigma_w: float
    red: bool
    trend: dict[str, float] | None
    truth: dict[str, Any] = field(default_factory=dict)


def _draw_star(family: str, seed: int, rng: np.random.Generator) -> Star:
    n = 3 if family == "PA" else int(rng.choice([2, 3, 4]))
    slots = sorted(int(j) for j in rng.choice(SECTOR_SLOTS, size=n, replace=False))
    starts = tuple(FIRST_START + SECTOR_STEP * j for j in slots)
    numbers = tuple(j + 1 for j in slots)
    sigma_w = math.exp(rng.uniform(math.log(300.0), math.log(3000.0))) * 1e-6
    red = bool(rng.random() < 0.5)
    has_trend = bool(rng.random() < 0.5)
    if family == "NW":
        red, has_trend = False, False
    elif family == "NR":
        red, has_trend = True, False
    trend = None
    if has_trend:
        trend = {
            "amplitude": float(rng.uniform(0.0, 2000.0)) * 1e-6,
            "period_days": float(rng.uniform(3.0, 10.0)),
            "phase": float(rng.uniform(0.0, 2.0 * math.pi)),
        }
    return Star(family, seed, starts, numbers, sigma_w, red, trend)


def _times(star: Star) -> tuple[np.ndarray, np.ndarray]:
    times = [syn.sector_times(s) for s in star.starts]
    numbers = [np.full(t.size, n) for t, n in zip(times, star.numbers, strict=True)]
    return np.concatenate(times), np.concatenate(numbers)


def _sinusoid(t: np.ndarray, period: float, amplitude: float, phase: float) -> np.ndarray:
    return amplitude * np.sin(2.0 * np.pi * t / period + phase)


def _transit_truth(rng, star: Star, t: np.ndarray, snr_range, b_range, family: str) -> dict:
    period = math.exp(rng.uniform(math.log(0.7), math.log(12.0)))
    b = float(rng.uniform(*b_range))
    t0 = float(t.min() + rng.uniform(0.0, period))
    snr = float(rng.uniform(*snr_range))
    sigma_r = star.sigma_w / 2.0 if star.red else 0.0
    depth, total, flat = solve_depth(t, period, period, t0, b, snr, star.sigma_w, sigma_r)
    return {
        "kind": "transit",
        "period_days": period,
        "t0_btjd": t0,
        "impact": b,
        "target_snr": snr,
        "depth": depth,
        "duration_days": total,
        "flat_days": flat,
        "ingress_fraction": (total - flat) / (2.0 * total),
    }


def generate(family: str, seed: int):
    """One star of ``family`` (``TessData`` and its truth); raises GenerationFailedError."""
    if family not in FAMILIES:
        raise ValueError(f"unknown family {family!r}")
    rng = np.random.default_rng(seed)
    star = _draw_star(family, seed, rng)
    t, sector = _times(star)
    sigma_r = star.sigma_w / 2.0 if star.red else 0.0
    model = np.ones_like(t)
    truth: dict[str, Any] = {"family": family}
    pixels_extra = None

    if family in ("P", "PG", "PV", "PA"):
        snr_range = (10.0, 30.0) if family == "PA" else (7.1, 30.0)
        b_range = (0.9, 1.0) if family == "PG" else (0.0, 0.8)
        tr = _transit_truth(rng, star, t, snr_range, b_range, family)
        truth.update(tr)
        model = model - syn.trapezoid(
            t,
            tr["period_days"],
            tr["t0_btjd"],
            tr["depth"],
            tr["duration_days"],
            tr["ingress_fraction"],
        )
        if family == "PV":
            p = tr["period_days"]
            while True:
                r = float(rng.uniform(1.3, 3.7))
                if all(abs(r - m) > 0.02 * m for m in (0.5, 1.0, 2.0, 3.0)):
                    break
            amp = float(rng.uniform(0.5, 3.0)) * tr["depth"]
            phase = float(rng.uniform(0.0, 2.0 * math.pi))
            model = model + _sinusoid(t, r * p, amp, phase)
            truth["variability"] = {"period_days": r * p, "ratio": r, "amplitude": amp}
        if family == "PA":
            pixels_extra = _artifact(rng, star, t, sector, tr)
            truth["artifact"] = pixels_extra["record"]
    elif family == "EB1":
        tr = _transit_truth(rng, star, t, (7.1, 30.0), (0.0, 0.8), family)
        ratio = float(rng.uniform(0.2, 1.0))
        truth.update(tr, kind="eclipsing_binary", secondary_ratio=ratio)
        model = model - syn.trapezoid(
            t,
            tr["period_days"],
            tr["t0_btjd"],
            tr["depth"],
            tr["duration_days"],
            tr["ingress_fraction"],
        )
        model = model - syn.trapezoid(
            t,
            tr["period_days"],
            tr["t0_btjd"],
            ratio * tr["depth"],
            tr["duration_days"],
            tr["ingress_fraction"],
            phase=0.5,
        )
    elif family == "EB2":
        found = math.exp(rng.uniform(math.log(0.7), math.log(12.0)))
        true_period = 2.0 * found
        b = float(rng.uniform(0.0, 0.8))
        t0 = float(t.min() + rng.uniform(0.0, true_period))
        snr = float(rng.uniform(7.1, 30.0))
        r = float(rng.uniform(0.5, 0.9))
        depth, total, flat = solve_depth(
            t, true_period, found, t0, b, snr, star.sigma_w, sigma_r, fold=(1.0 + r) / 2.0
        )
        ingress = (total - flat) / (2.0 * total)
        truth.update(
            kind="eclipsing_binary_2p",
            period_days=found,
            true_period_days=true_period,
            t0_btjd=t0,
            impact=b,
            target_snr=snr,
            depth=depth,
            secondary_ratio=r,
            duration_days=total,
            flat_days=flat,
            ingress_fraction=ingress,
        )
        model = model - syn.trapezoid(t, true_period, t0, depth, total, ingress)
        model = model - syn.trapezoid(t, true_period, t0, r * depth, total, ingress, phase=0.5)
    elif family in ("V1", "V2"):
        period = math.exp(rng.uniform(math.log(0.7), math.log(10.0)))
        amp = math.exp(rng.uniform(math.log(0.5), math.log(5.0))) * star.sigma_w
        if family == "V1":
            phase = float(rng.uniform(0.0, 2.0 * math.pi))
            model = model + _sinusoid(t, period, amp, phase)
            truth.update(kind="sinusoid", period_days=period, amplitude=amp)
        else:
            f0 = 1.0 / period
            d1, d2 = float(rng.uniform(0.01, 0.05)), float(rng.uniform(0.01, 0.05))
            freqs = (f0, f0 * (1.0 + d1), f0 * (1.0 + d2))
            for f in freqs:
                model = model + _sinusoid(
                    t, 1.0 / f, amp / math.sqrt(3.0), float(rng.uniform(0.0, 2.0 * math.pi))
                )
            truth.update(kind="multi_periodic", frequencies=list(freqs), amplitude=amp)
    elif family == "SE":
        hours = float(rng.uniform(3.0, 8.0))
        width = hours / 24.0
        centre = float(t[int(rng.integers(0, t.size))])
        snr = float(rng.uniform(8.0, 20.0))
        inside = np.abs(t - centre) <= width / 2.0
        count = int(inside.sum())
        var = star.sigma_w**2 / max(count, 1)
        if sigma_r > 0:
            var += sigma_r**2 * ar1_mean_factor(width / TAU_DAYS)
        depth = snr * math.sqrt(var)
        model = model - np.where(inside, depth, 0.0)
        truth.update(
            kind="single_event",
            centre_btjd=centre,
            duration_hours=hours,
            target_snr=snr,
            depth=depth,
        )
    elif family == "ER":
        a = float(rng.uniform(1.0, 3.0)) * star.sigma_w
        ramps = np.zeros_like(t)
        for s in star.starts:
            for orbit_start in (s, s + 14.0):
                after = t >= orbit_start
                elapsed = np.clip(t - orbit_start, 0.0, None)
                ramps = ramps - np.where(after, a * np.exp(-elapsed / 0.3), 0.0)
        model = model + ramps
        truth.update(kind="edge_ramps", amplitude=a)
    elif family in ("NW", "NR"):
        truth.update(kind="noise")
    elif family == "PX":
        return _px(rng, star, seed, truth)

    flux = _noisy(model, t, sector, star)
    lc = LightCurveData(t, flux, np.full(t.size, star.sigma_w), sector, _years(t, sector))
    infos = _sector_infos(lc, star)
    aux = syn.make_aux(lc, scene=syn.Scene(), seed=seed)
    if pixels_extra is not None:
        aux = pixels_extra["apply"](aux)
    data = syn.with_sky_jacobians(syn.make_data(lc, infos, syn.make_star(), 1, aux))
    truth.update(_noise_truth(star))
    return data, truth


def _noisy(model: np.ndarray, t: np.ndarray, sector: np.ndarray, star: Star) -> np.ndarray:
    rng_w = np.random.default_rng([star.seed, 2])
    rng_r = np.random.default_rng([star.seed, 3])
    flux = model.copy()
    if star.trend is not None:
        tr = star.trend
        flux = flux * (
            1.0 + tr["amplitude"] * np.sin(2 * np.pi * t / tr["period_days"] + tr["phase"])
        )
    flux = flux + rng_w.normal(0.0, star.sigma_w, t.size)
    if star.red:
        for n in star.numbers:
            sel = sector == n
            flux[sel] = flux[sel] + syn.ar1_series(t[sel], star.sigma_w / 2.0, TAU_DAYS, rng_r)
    return flux


def _years(t: np.ndarray, sector: np.ndarray) -> np.ndarray:
    """Each cadence's year: the year of its sector's first cadence (as ``make_lightcurve``)."""
    out = np.empty(t.size, dtype=int)
    for n in np.unique(sector):
        sel = sector == n
        out[sel] = btjd_to_year(float(t[sel].min()))
    return out


def _sector_infos(lc: LightCurveData, star: Star) -> list[SectorInfo]:
    infos = []
    for n in star.numbers:
        t = lc.time[lc.sector == n]
        infos.append(
            SectorInfo(
                sector=int(n),
                year=btjd_to_year(float(t.min())),
                t_start=float(t.min()),
                t_end=float(t.max()),
                n_points=int(t.size),
                filename=f"synthetic_sector_{n:02d}.npz",
            )
        )
    return infos


def _noise_truth(star: Star) -> dict[str, Any]:
    return {
        "sectors": list(star.numbers),
        "sigma_white_ppm": star.sigma_w * 1e6,
        "correlated": star.red,
        "trend": star.trend,
    }


def _artifact(rng, star: Star, t: np.ndarray, sector: np.ndarray, tr: dict) -> dict:
    """PA: in one drawn sector, a point source 2 px from the target (random angle) whose flux is
    0.5 % of the target's during 0.3 day centred on the first transit of that sector with data,
    zero otherwise; in the pixels only."""
    chosen = int(star.numbers[int(rng.integers(0, len(star.numbers)))])
    angle = float(rng.uniform(0.0, 2.0 * math.pi))
    ts = t[sector == chosen]
    p, t0 = tr["period_days"], tr["t0_btjd"]
    n = math.ceil((ts.min() - t0) / p)
    centre = None
    while t0 + n * p <= ts.max():
        mid = t0 + n * p
        if np.any(np.abs(ts - mid) <= tr["duration_days"] / 2.0):
            centre = mid
            break
        n += 1
    record = {"sector": chosen, "angle_rad": angle, "centre_btjd": centre, "ratio": 0.005}

    def apply(aux):
        if centre is None:
            return aux
        scene = syn.Scene(
            neighbor_xy=(5.0 + 2.0 * math.cos(angle), 5.0 + 2.0 * math.sin(angle)),
            neighbor_ratio=0.005,
        )
        pixels = []
        for px in aux.pixels:
            if px.sector != chosen:
                pixels.append(px)
                continue
            box = (np.abs(px.time - centre) <= 0.15).astype(float)
            extra = (
                scene.target_flux
                * scene.neighbor_ratio
                * box[:, None, None]
                * syn.psf_image(scene, scene.neighbor_xy)
            )
            pixels.append(dataclasses.replace(px, flux=px.flux + extra))
        return dataclasses.replace(aux, pixels=pixels)

    return {"record": record, "apply": apply}


def _px(rng, star: Star, seed: int, truth: dict):
    """PX: ``synthetic.make_blend_sky`` with the neighbor 1.5 to 3 px away (random angle), flux
    ratio uniform in [0.1, 0.5]; the eclipse depth in the target's light curve solved by the
    target-SNR rule (target in [7.1, 30]) and the neighbor's own depth derived from it."""
    t, _ = _times(star)
    sigma_r = star.sigma_w / 2.0 if star.red else 0.0
    sep_px = float(rng.uniform(1.5, 3.0))
    angle = float(rng.uniform(0.0, 2.0 * math.pi))
    ratio = float(rng.uniform(0.1, 0.5))
    tr = _transit_truth(rng, star, t, (7.1, 30.0), (0.0, 0.8), "PX")
    offset = (
        sep_px * syn.PIXEL_SCALE_ARCSEC * math.cos(angle),
        sep_px * syn.PIXEL_SCALE_ARCSEC * math.sin(angle),
    )
    # the crowding of the scene make_blend_sky draws (the same in every sector: the sector
    # Jacobians are rotations by multiples of 90 degrees, which map the pixel grid to itself)
    jac = np.asarray(syn.sector_jacobian(int(star.numbers[0])), dtype=float)
    dx, dy = np.linalg.solve(jac, np.asarray(offset, dtype=float))
    scene = syn.Scene(neighbor_xy=(5.0 + float(dx), 5.0 + float(dy)), neighbor_ratio=ratio)
    c = syn.crowding(scene)
    neighbor_depth = tr["depth"] * c / (1.0 - c)
    if neighbor_depth > 1.0:
        raise GenerationFailedError(f"the neighbor depth {neighbor_depth:.3f} is above 1")
    spec = syn.SignalSpec(
        period=tr["period_days"],
        t0=tr["t0_btjd"],
        depth=neighbor_depth,
        duration=tr["duration_days"],
        ingress_fraction=tr["ingress_fraction"],
    )
    lc, infos, aux = syn.make_blend_sky(
        spec,
        offset,
        neighbor_ratio=ratio,
        sector_starts=star.starts,
        noise_ppm=star.sigma_w * 1e6,
        seed=seed,
        red_noise_ppm=sigma_r * 1e6,
        sector_numbers=star.numbers,
    )
    if star.trend is not None:
        tr_ = star.trend
        factor = 1.0 + tr_["amplitude"] * np.sin(
            2 * np.pi * lc.time / tr_["period_days"] + tr_["phase"]
        )
        lc = LightCurveData(lc.time, lc.flux * factor, lc.flux_err, lc.sector, lc.year)
        sectors = []
        for sa in aux.sectors:
            f = 1.0 + tr_["amplitude"] * np.sin(
                2 * np.pi * sa.time / tr_["period_days"] + tr_["phase"]
            )
            sectors.append(
                dataclasses.replace(sa, pdcsap_flux=sa.pdcsap_flux * f, sap_flux=sa.sap_flux * f)
            )
        aux = dataclasses.replace(aux, sectors=sectors)
    truth.update(
        tr,
        kind="off_target",
        separation_px=sep_px,
        angle_rad=angle,
        flux_ratio=ratio,
        crowdsap=c,
        neighbor_depth=neighbor_depth,
    )
    truth.update(_noise_truth(star))
    data = syn.make_data(lc, infos, syn.make_star(), 1, aux)
    return data, truth


# --- one task -------------------------------------------------------------------------------


def identity(truth: dict[str, Any], found: dict[str, Any] | None) -> bool:
    """The shared candidate matches the true signal (planet families): period within 1 % and the
    epoch, folded at the true period, within half the true duration of the true epoch."""
    if not found or found.get("period_days") is None:
        return False
    p, t0, dur = truth["period_days"], truth["t0_btjd"], truth["duration_days"]
    if abs(float(found["period_days"]) - p) / p > 0.01:
        return False
    phase = (float(found["t0_btjd"]) - t0) / p
    return abs(phase - round(phase)) * p <= 0.5 * dur


@dataclass(frozen=True)
class C1Task:
    family: str
    index: int
    seed: int
    test_plan_v04: dict


def run_task(task: C1Task) -> dict[str, Any]:
    """One curve; ``cpu_seconds`` covers the whole task, also when it fails."""
    from refute.packs.tess.calib05.plans import pair
    from refute.packs.tess.discover.paired import paired_chain

    started = time.process_time()
    record: dict[str, Any] = {"family": task.family, "index": task.index, "seed": str(task.seed)}
    try:
        data, truth = generate(task.family, task.seed)
    except GenerationFailedError as exc:
        record.update({"status": "GENERATION_FAILURE", "reason": str(exc)})
        record["cpu_seconds"] = time.process_time() - started
        return record
    record["truth"] = truth
    try:
        p04, p05 = pair(task.test_plan_v04)
        chain = paired_chain(data, p04, p05, stage=2)
        record["chain"] = chain
        record["status"] = "OK"
        if task.family in PLANET_FAMILIES:
            record["identity"] = identity(truth, chain["v05"]["candidate"])
    except Exception as exc:  # noqa: BLE001 - recorded: the task stays in its denominators
        record.update({"status": "ERROR", "reason": f"{type(exc).__name__}: {exc}"})
    record["cpu_seconds"] = time.process_time() - started
    return record


# --- metrics --------------------------------------------------------------------------------


def wilson(successes: int, trials: int) -> list[float] | None:
    from refute.packs.tess.discover.injection import wilson_interval

    return wilson_interval(successes, trials) if trials else None


def family_metrics(records: list[dict[str, Any]], family: str) -> dict[str, Any]:
    """The eligible set (planet families: gate passed and identity; others: gate passed), the
    four verdict counts per battery, the counts outside it by reason, and the transitions."""
    from refute.packs.tess.discover.paired import transitions, verdict_counts

    mine = [r for r in records if r["family"] == family]
    outside: dict[str, int] = {}
    eligible = []
    for r in mine:
        if r["status"] != "OK":
            outside[r["status"].lower()] = outside.get(r["status"].lower(), 0) + 1
        elif not r["chain"]["v04"]["gate_passed"]:
            outside["gate_not_passed"] = outside.get("gate_not_passed", 0) + 1
        elif family in PLANET_FAMILIES and not r.get("identity"):
            outside["identity_not_matched"] = outside.get("identity_not_matched", 0) + 1
        else:
            eligible.append(r)
    n = len(eligible)
    out: dict[str, Any] = {"curves": len(mine), "eligible": n, "outside": outside}
    for battery in ("v04", "v05"):
        counts = verdict_counts([r["chain"][battery]["verdict"] for r in eligible])
        out[battery] = {
            "counts": counts,
            "wilson_95": {k: wilson(v, n) for k, v in counts.items()},
            "survived_or_weakened": counts["SURVIVED"] + counts["WEAKENED"],
        }
    out["transitions"] = transitions(
        [(r["chain"]["v04"]["verdict"], r["chain"]["v05"]["verdict"]) for r in eligible]
    )
    out["_eligible"] = eligible
    return out


def _rule(decidable: bool, passed: bool) -> str:
    if not decidable:
        return "NOT DECIDABLE"
    return "PASS" if passed else "FAIL"


def decision_rules(fam: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """D1 to D5 of the acceptance document (none blocks the phase)."""
    floor = C1.not_decidable_below
    rules: dict[str, Any] = {}
    d1 = {}
    for family in ("SE", "V1", "V2", "EB1", "EB2", "ER", "NW", "NR"):
        f = fam[family]
        n = f["eligible"]
        s05, s04 = f["v05"]["counts"]["SURVIVED"], f["v04"]["counts"]["SURVIVED"]
        upper = wilson(s05, n)[1] if n else None
        d1[family] = {
            "eligible": n,
            "v05_survived": s05,
            "v04_survived": s04,
            "v05_survived_upper_wilson": upper,
            "v05_survived_or_weakened": f["v05"]["survived_or_weakened"],
            "result": _rule(n >= floor, upper is not None and upper <= 0.10 and s05 <= s04),
        }
    rules["D1"] = d1
    p = fam["P"]
    n = p["eligible"]
    kept05 = p["v05"]["survived_or_weakened"] / n if n else None
    kept04 = p["v04"]["survived_or_weakened"] / n if n else None
    ref05 = p["v05"]["counts"]["REFUTED"]
    ref_upper = wilson(ref05, n)[1] if n else None
    rules["D2"] = {
        "eligible": n,
        "v05_kept": kept05,
        "v04_kept": kept04,
        "v05_refuted_fraction": ref05 / n if n else None,
        "v05_refuted_upper_wilson": ref_upper,
        "result": _rule(
            n >= floor,
            kept05 is not None
            and kept05 >= kept04 - 0.10
            and ref05 / n <= 0.05
            and ref_upper <= 0.10,
        ),
    }
    d3 = {}
    for family in ("PG", "PV", "PA"):
        f = fam[family]
        n = f["eligible"]
        ref = f["v05"]["counts"]["REFUTED"]
        upper = wilson(ref, n)[1] if n else None
        d3[family] = {
            "eligible": n,
            "v05_refuted_fraction": ref / n if n else None,
            "v05_refuted_upper_wilson": upper,
            "result": _rule(n >= floor, n > 0 and ref / n <= 0.10 and upper <= 0.20),
        }
    rules["D3"] = d3
    subset = [r for r in fam["P"]["_eligible"] if r["truth"]["target_snr"] >= 15.0]
    inconclusive = sum(r["chain"]["v05"]["verdict"] == "INCONCLUSIVE" for r in subset)
    rules["D4"] = {
        "subset": len(subset),
        "v05_inconclusive_fraction": inconclusive / len(subset) if subset else None,
        "result": _rule(len(subset) >= floor, bool(subset) and inconclusive / len(subset) <= 0.30),
    }
    x = fam["PX"]
    n = x["eligible"]
    ref = x["v05"]["counts"]["REFUTED"]
    rules["D5"] = {
        "eligible": n,
        "v05_refuted_fraction": ref / n if n else None,
        "note": "measures the remaining decisive tests: no decisive centroid in the v0.5 battery "
        "(the S2 decision); a PASS does not show that the per-sector centroid was accepted",
        "result": _rule(n >= floor, n > 0 and ref / n >= 0.80),
    }
    return rules


def metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Every family's metrics and the decision rules; generation failures counted apart."""
    fam = {f: family_metrics(records, f) for f in FAMILIES}
    rules = decision_rules(fam)
    for f in fam.values():
        f.pop("_eligible")
    return {
        "families": fam,
        "decision_rules": rules,
        "note": "synthetic data with known truth; method_status: not_validated; no rule blocks "
        "the phase; curves are independent stars",
    }
