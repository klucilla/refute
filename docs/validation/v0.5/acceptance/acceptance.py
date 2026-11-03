"""The rate cases of the v0.5 acceptance documents (docs/plans/v0.5-acceptance.md, WP1 to WP4),
on synthetic data with known truth. Version 2, after Codex's NO-GO review of version 1 (commit
bc89ab4, never run on the acceptance seeds).

Each trial builds its data from its seed, measures the candidate at the known ephemeris as the v0.5
pipeline does (detrending with the transits masked, the red-noise error model), runs the test,
keeps the test's own sensitivity blocks, applies the engine's rule, and records the final status,
the emitted severity, the reason and a **construction check**: whether the trial is the case's
intended construction ("a": the declared alternative, detectable by the test's rule; "b": below
the rule; "c": no effect, detectable). A case is decided only when every scheduled trial ran, none
raised an error, and every trial meets its construction; then by the binomial band of the
acceptance conventions: "FAILs at least at rate p" = a FAIL count at or above the lower 2.5 %
quantile of Binomial(N, p); "false-failure rate at most a" = a FAIL count at or below the upper
97.5 % quantile of Binomial(N, a); "never PASS" = zero PASS.

Noise models (the acceptance conventions): ``white`` (Gaussian, 1000 ppm per point), ``red``
(plus an AR(1) series of half the white level and a one-hour correlation time), ``trend`` (white
plus a stellar trend, 2000 ppm at 6 days, as the synthetic scenarios use).

Seeds: ``--seeds dev`` uses the development rule (construction checks, smoke runs, the cost
projection); ``--seeds accept`` uses the acceptance rule, unseen until the one acceptance run, which
must run the whole matrix with 200 trials (400 for the error pulls). A case that fails is recorded;
its test is diagnostic only in v0.5 (docs/plans/v0.5-plan.md, section 3); nothing is retuned. The
exit code is 1 when any case is not PASS.

Every trial's emitted severity is checked against the test's declared severity; the summary
(``--out``, ``--md``) carries the SHA-256 of the per-trial record (``--detail``).

usage: acceptance.py --seeds dev|accept --out <json> --md <md> --detail <json> [--trials N]
       [--workers N] [--cases a,b]   (--trials and --cases only with --seeds dev)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from functools import lru_cache
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
CADENCE = 2.0 / 1440.0
WHITE = 1000e-6
RED = 500e-6
TAU = 1.0 / 24.0
TREND = (0.002, 6.0)
NOISES = ("white", "red", "trend")
ACCEPT_TRIALS = 200
PULL_TRIALS = 400


def seed_of(rule: str, case: str, i: int) -> int:
    prefix = {"dev": "refute-v05-dev", "accept": "refute-v05-accept"}[rule]
    return int(hashlib.sha256(f"{prefix}:{case}:{i}".encode()).hexdigest()[:16], 16)


# --- binomial bands (no scipy) ---------------------------------------------------------------


def lower_quantile(n: int, p: float, q: float = 0.025) -> int:
    """The smallest k with P(X <= k) >= q, X ~ Binomial(n, p)."""
    total = 0.0
    for k in range(n + 1):
        total += math.comb(n, k) * p**k * (1 - p) ** (n - k)
        if total >= q:
            return k
    return n


def upper_quantile(n: int, p: float) -> int:
    return lower_quantile(n, p, 0.975)


# --- synthetic data on explicit time grids ---------------------------------------------------


@lru_cache(maxsize=1)
def _plan():
    from refute.packs.tess.params import TessTestPlan
    from refute.packs.tess.synthetic import discovery_v05_plan_dict

    return TessTestPlan.model_validate(discovery_v05_plan_dict())


def _segments(starts_ends):
    return np.concatenate([np.arange(a, b, CADENCE) for a, b in starts_ends])


def _lc(time, model, seed: int, noise: str, sectors=None):
    """A light curve on ``time`` with ``model`` (flux), white noise and the noise model."""
    from refute.packs.tess.synthetic import ar1_series
    from refute.packs.tess.types import LightCurveData

    rng = np.random.default_rng(seed)
    sector = np.ones(time.size, int) if sectors is None else sectors
    flux = model + rng.normal(0.0, WHITE, time.size)
    if noise == "red":
        red_rng = np.random.default_rng([seed, 1])
        for s in np.unique(sector):
            sel = sector == s
            flux[sel] += ar1_series(time[sel], RED, TAU, red_rng)
    elif noise == "trend":
        flux = flux * (1.0 + TREND[0] * np.sin(2 * np.pi * time / TREND[1]))
    return LightCurveData(time, flux, np.full(time.size, WHITE), sector, np.full(time.size, 2019))


def _box(time, period, t0, duration, depth):
    dt = np.abs(np.mod(time - t0 + 0.5 * period, period) - 0.5 * period)
    return np.where(dt <= duration / 2.0, depth, 0.0)


def _candidate(period, t0, duration, depth, depth_err=None):
    from refute.packs.tess.types import Candidate

    return Candidate(period, t0, duration, depth, depth_err or depth / 20.0, 20.0, 0.0, 10.0, 5)


def _events(lc, cand, phase=0.0):
    from refute.packs.tess.detrend import detrend
    from refute.packs.tess.events import per_event_depths, transit_mask
    from refute.packs.tess.rednoise import event_noise

    plan = _plan()
    half = plan.detrend.transit_mask_half_width_durations * cand.duration
    flat = detrend(lc, plan.detrend, mask=transit_mask(lc.time, cand.period, cand.t0, half))
    noise = event_noise(flat, None, cand.period, cand.t0, cand.duration, plan)
    ev = per_event_depths(
        flat, cand.period, cand.t0, cand.duration, CADENCE, plan.gauntlet.events, phase, None, noise
    )
    return flat, ev


def _jsonable(x):
    """Plain JSON values (numpy scalars and arrays included)."""
    if isinstance(x, dict):
        return {str(k): _jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_jsonable(v) for v in x]
    if isinstance(x, np.ndarray):
        return _jsonable(x.tolist())
    if isinstance(x, np.bool_):
        return bool(x)
    if isinstance(x, np.integer):
        return int(x)
    if isinstance(x, np.floating):
        return float(x)
    return x


def _out(test, constructed: bool, **details):
    """One trial's record: the status after the engine's rule, the emitted severity, the reason,
    the construction check, the sub-check probabilities the decision rested on, the test's full
    (realized) sensitivity blocks and metrics, and the construction quantities in ``details``."""
    from refute.core.sensitivity import enforce_sensitivity
    from refute.packs.tess.power import TESS_REGISTRY

    (final,) = enforce_sensitivity([test], TESS_REGISTRY)
    blocks = {
        k: v.get("probability", v.get("applicable", v.get("category")))
        for k, v in (test.sensitivity or {}).items()
    }
    return _jsonable(
        {
            "status": final.status.value,
            "severity": final.severity.value,
            "reason": final.message[:200],
            "constructed": bool(constructed),
            "blocks": blocks,
            "sensitivity": test.sensitivity or {},
            "metrics": test.metrics or {},
            **details,
        }
    )


def _detectable(test, sub: str = "main") -> bool:
    block = (test.sensitivity or {}).get(sub) or {}
    return bool(block.get("detectable"))


def _built(kind: str, detectable: bool) -> bool:
    """The construction check: "a" and "c" need the rule detectable, "b" needs it not."""
    return detectable if kind in ("a", "c") else not detectable


# --- the standard layout: one sector-like stretch, P = 3 d ------------------------------------

P, T0, DUR = 3.0, 1000.3, 0.1


def _std_time():
    return _segments([(1000.0, 1013.0), (1014.0, 1027.0), (1100.0, 1113.0), (1114.0, 1127.0)])


def _std_lc(seed, noise, model_fn):
    t = _std_time()
    sectors = np.where(t < 1050, 1, 2)
    return _lc(t, 1.0 - model_fn(t), seed, noise, sectors)


# --- WP1 rules ---------------------------------------------------------------------------------


def odd_even(seed, noise, kind):
    from refute.packs.tess import power
    from refute.packs.tess.gauntlet import check_odd_even

    plan = _plan()
    depth = {"a": 3000e-6, "b": 150e-6, "c": 3000e-6}[kind]
    odd = 0.0 if kind in ("a", "b") else 1.0

    def model(t):
        epoch = np.round((t - T0) / P).astype(int)
        return _box(t, P, T0, DUR, depth) * np.where(epoch % 2 != 0, odd, 1.0)

    lc = _std_lc(seed, noise, model)
    _, ev = _events(lc, _candidate(P, T0, DUR, depth))
    test = power.attach(check_odd_even(ev, plan.gauntlet.odd_even), None)
    test = power.attach(test, power.odd_even_blocks(test, depth, plan.stronger))
    return _out(test, _built(kind, _detectable(test)))


def secondary(seed, noise, kind):
    from refute.packs.tess.battery_v5 import check_secondary_two_sided

    plan = _plan()
    big, small = 3000e-6, 50e-6
    depth, effect, sub = {
        "a": (big, big, "dip"),
        "b": (small, small, "dip"),
        "c": (big, 0.0, "dip"),
        "ratio-0.3": (big, 0.3 * big, "dip"),
        "ratio-1.0": (big, big, "dip"),
        "bright-a": (big, -0.5 * big, "brightening"),
        "bright-b": (small, -0.5 * small, "brightening"),
    }[kind]

    def model(t):
        return _box(t, P, T0, DUR, depth) + _box(t, P, T0 + 0.5 * P, DUR, effect)

    lc = _std_lc(seed, noise, model)
    cand = _candidate(P, T0, DUR, depth)
    _, primary = _events(lc, cand)
    _, half = _events(lc, cand, 0.5)
    test = check_secondary_two_sided(
        primary, half, plan.gauntlet.secondary_eclipse, plan.stronger, seed
    )
    built_kind = "b" if kind.endswith("b") else ("c" if kind == "c" else "a")
    return _out(test, _built(built_kind, _detectable(test, sub)))


# Row 3.3: a sinusoid "found as a box". A 3-day sinusoid does not survive the 1-day detrending,
# so the variability has period SIN_P = 0.83 d, where the engine's own box estimator (the search's
# detrending, then ``finalize_candidate`` at SIN_P with a 2-hour trial box) finds, on the
# noise-free signal, a box at T0 whose depth is half the semi-amplitude (ratio 2.006; frozen
# before the acceptance run, recorded in every trial).
SIN_P = 0.83
SIN_AMP = {"a": 2000e-6, "b": 40e-6}


def _std_curve(flux_fn):
    from refute.packs.tess.types import LightCurveData

    t = _std_time()
    flux = 1.0 - flux_fn(t)
    return LightCurveData(
        t, flux, np.full(t.size, WHITE), np.where(t < 1050, 1, 2), np.full(t.size, 2019)
    )


@lru_cache(maxsize=4)
def _sin_box(amp: float):
    """The box the engine finds on the noise-free sinusoid of semi-amplitude ``amp``."""
    from refute.packs.tess.detrend import detrend
    from refute.packs.tess.search import finalize_candidate

    plan = _plan()
    lc = _std_curve(lambda t: amp * np.cos(2 * np.pi * (t - T0) / SIN_P))
    flat = detrend(lc, plan.detrend)
    return finalize_candidate(
        flat, SIN_P, 2.0 / 24.0, plan.search, 10.0, np.full(flat.time.size, WHITE)
    )


def sinusoid(seed, noise, kind):
    from refute.packs.tess.battery_v5 import check_sinusoid

    sp = _plan().stronger
    if kind == "c":  # 3.8: a box-only curve (no variability)
        depth = 2000e-6
        lc = _std_lc(seed, noise, lambda t: _box(t, P, T0, DUR, depth))
        test = check_sinusoid(lc, _candidate(P, T0, DUR, depth), sp, seed)
        return _out(test, _detectable(test))
    # 3.3 ("a") and 1.8 ("b"): variability at SIN_P, minimum at T0, found as a box
    amp = SIN_AMP[kind]
    cand = _sin_box(amp)
    ratio = amp / cand.depth
    lc = _std_lc(seed, noise, lambda t: amp * np.cos(2 * np.pi * (t - T0) / SIN_P))
    test = check_sinusoid(lc, cand, sp, seed)
    fit = (test.metrics or {}).get("fits", {}).get("P", {})
    err = fit.get("semi_amplitude_err_ppm")
    design_significance = amp * 1e6 / err if err else None
    geometry = 1.9 <= ratio <= 2.1 and abs(cand.t0 - T0) <= cand.duration / 2.0
    if kind == "a":
        # the row's construction: semi-amplitude twice the apparent depth, significance above 15
        # (design). The realized block is recorded, not required: it is the worst of P/2, P and
        # 2P, and its fits at P/2 and 2P carry the unmodeled variability at P in their beta
        # (the development runs: probability near 0 while the test FAILs at P).
        built = geometry and design_significance is not None and design_significance > 15.0
    else:  # below the rule
        built = geometry and not _detectable(test)
    return _out(
        test,
        built,
        semi_amplitude_ppm=amp * 1e6,
        apparent_depth_ppm=cand.depth * 1e6,
        amplitude_over_depth=ratio,
        box_t0=cand.t0,
        box_duration=cand.duration,
        design_significance=design_significance,
    )


# --- WP2: exact event counts on explicit windows ------------------------------------------------


def _window_time(n: int, period: float, duration: float, partial=()):
    """Exactly ``n`` covered event windows in one contiguous stretch (so the red-noise model has
    its bins): from one day before the first event to one day after the last; an index in
    ``partial`` loses the first 40 % of its in-event span to a short hole (shorter than an edge
    gap), keeping both baseline bands (a partial event)."""
    start, end = T0 - 1.0, T0 + (n - 1) * period + 1.0
    cuts = sorted(
        (T0 + k * period - duration / 2.0, T0 + k * period - duration / 2.0 + 0.4 * duration)
        for k in partial
    )
    segments, cursor = [], start
    for a, b in cuts:
        segments.append((cursor, a))
        cursor = b
    segments.append((cursor, end))
    return _segments(segments)


def _sigma_measured(t, period: float, duration: float, seed: int, noise: str) -> float:
    """The median per-event error the engine measures on this trial's own noise (the same seed,
    no signal): the SNR of a WP2 construction is stated in the errors of its noise model, so a
    correlated-noise trial is not weaker than its white twin by construction."""
    lc0 = _lc(t, np.ones_like(t), seed, noise)
    _, ev0 = _events(lc0, _candidate(period, T0, duration, 1e-3))
    return float(np.median(ev0.errors))


def _snr_depth(snr: float, n: int, sigma: float) -> float:
    """The per-event depth that gives ``n`` equal events a total SNR ``snr``."""
    return snr * sigma / math.sqrt(n)


def _design(ev, truth: dict[int, float], base: float):
    """The trial's measured events with their depths replaced by the injected ones (``truth`` by
    epoch, ``base`` elsewhere): the WP2 rows state their constructions by design ("the dip's SNR
    set so the rule is detectable by a margin"), and both WP2 sensitivity blocks are computed
    from the observed depths, so the construction check runs the test on the noise-free depths
    with the trial's own errors. The realized block still decides the status."""
    import dataclasses

    depths = np.array([truth.get(int(e), base) for e in ev.epochs], dtype=float)
    return dataclasses.replace(ev, depths=depths)


def single_event(seed, noise, kind):
    from refute.packs.tess.battery_v5 import check_single_event

    sp = _plan().stronger
    shape, n = kind.split("-")[0], int(kind.split("-")[1])
    period = 2.0
    duration = 4.0 / 24.0 if shape in ("one", "weak") else DUR
    t = _window_time(n, period, duration)
    sigma = _sigma_measured(t, period, duration, seed, noise)
    if shape == "equal":  # total SNR 12 in N equal events
        depth = _snr_depth(12.0, n, sigma)
        flux = 1.0 - _box(t, period, T0, duration, depth)
        truth, base = {}, depth
    else:  # one 4-hour dip at epoch 1, the other windows empty; dip SNR 25 or 1.5 ("weak")
        dip_snr = 25.0 if shape == "one" else 1.5
        depth = dip_snr * sigma
        flux = 1.0 - np.where(np.abs(t - (T0 + period)) <= duration / 2.0, depth, 0.0)
        truth, base = {1: depth}, 0.0
    lc = _lc(t, flux, seed, noise)
    _, ev = _events(lc, _candidate(period, T0, duration, depth))
    test = check_single_event(ev, sp, seed)
    ev_design = _design(ev, truth, base)
    design_test = check_single_event(ev_design, sp, seed)
    kind_c = {"equal": "c", "one": "a", "weak": "b"}[shape]
    built = len(ev) == n and _built(kind_c, _detectable(design_test))
    return _out(test, built, **_wp2_record(ev, ev_design, design_test, test, sigma))


def event_consistency(seed, noise, kind):
    from refute.packs.tess.battery_v5 import check_event_consistency

    sp = _plan().stronger
    shape, n = kind.split("-")[0], int(kind.split("-")[1])
    period = 2.0
    partial = (1, 3) if shape == "partial" else ()
    t = _window_time(n, period, DUR, partial)
    sigma = _sigma_measured(t, period, DUR, seed, noise)
    snr = {"null": 12.0, "strong": 30.0, "deep": 20.0, "weak": 2.0, "partial": 30.0}[shape]
    depth = _snr_depth(snr, n, sigma)
    flux = 1.0 - _box(t, period, T0, DUR, depth)
    truth = {}
    if shape in ("deep", "weak"):  # the event at epoch 2 deepened by a full depth
        flux -= np.where(np.abs(t - (T0 + 2 * period)) <= DUR / 2.0, depth, 0.0)
        truth = {2: 2.0 * depth}
    lc = _lc(t, flux, seed, noise)
    _, ev = _events(lc, _candidate(period, T0, DUR, depth))
    test = check_event_consistency(ev, sp)
    ev_design = _design(ev, truth, depth)
    design_test = check_event_consistency(ev_design, sp)
    record = _wp2_record(ev, ev_design, design_test, test, sigma)
    if shape == "null":
        # Row 2.1 says "SNR 12, detectable by a margin"; for event_consistency the two cannot
        # both hold: at total SNR 12 the per-event SNR (4.9, 2.7, 1.9 at N = 6, 20, 40) leaves
        # "one event off by a full depth" below the rule (the development runs: INCONCLUSIVE
        # at N = 6 too). A recorded interpretation of the row: this construction checks the
        # event count only and records both detectabilities; a FAIL is a false failure whatever
        # the sensitivity. The detectable null is case 1.8-event_consistency-c.
        return _out(test, len(ev) == n, **record)
    kind_c = {"strong": "c", "deep": "a", "weak": "b", "partial": "c"}[shape]
    built = len(ev) == n and _built(kind_c, _detectable(design_test))
    return _out(test, built, **record)


def _wp2_record(ev, ev_design, design_test, test, sigma: float) -> dict:
    """The WP2 construction quantities: epochs, injected depths, measured depths and errors, the
    design SNR from the injected depths and the complete error vector (inverse-variance), the
    design (injected) and realized sensitivity blocks, and the median error used to set the
    depth."""
    w = 1.0 / np.square(ev.errors)
    design_snr = float(np.sum(ev_design.depths * w) / np.sqrt(np.sum(w))) if len(ev) else None
    return {
        "n_events": len(ev),
        "epochs": ev.epochs,
        "injected_depths": ev_design.depths,
        "measured_depths": ev.depths,
        "errors": ev.errors,
        "sigma_used": sigma,
        "design_snr": design_snr,
        "design_sensitivity": design_test.sensitivity or {},
        "design_detectable": _detectable(design_test),
        "detectable": _detectable(test),
    }


def edge_events(seed, noise, kind):
    """Half the events 0.15 d after a segment start (near an edge), half mid-segment."""
    from refute.packs.tess.battery_v5 import check_edge_events

    sp = _plan().stronger
    period, n_pairs = 2.0, 10
    # segment j covers events 2j (0.15 d after its start) and 2j + 1 (mid-segment)
    segments = [(T0 + 2 * j * period - 0.15, T0 + 2 * j * period + 3.35) for j in range(n_pairs)]
    t = _segments(segments)
    depth = {"a": 3000e-6, "b": 100e-6, "c": 3000e-6, "ramp": 0.0}[kind]
    edge_factor = 1.5 if kind in ("a", "b") else 1.0
    epoch = np.round((t - T0) / period).astype(int)
    flux = 1.0 - _box(t, period, T0, DUR, depth) * np.where(epoch % 2 == 0, edge_factor, 1.0)
    if kind == "ramp":  # 2.6: no transit; a detrending-like ramp at every segment start
        starts = np.array([a for a, _ in segments])
        idx = np.searchsorted(starts, t, side="right") - 1
        flux -= 3 * WHITE * np.exp(-(t - starts[idx]) / 0.3)
    lc = _lc(t, flux, seed, noise)
    cand = _candidate(period, T0, DUR, max(depth, 1000e-6))
    flat, ev = _events(lc, cand)
    test = check_edge_events(flat.time, ev, DUR, _plan().gauntlet.snr.min_snr, sp)
    if kind == "ramp":
        return _out(test, True, n_events=len(ev))
    near_half = test.metrics.get("fraction_near_edges", 0) >= 0.5
    comparison = (test.sensitivity or {}).get("comparison") or {}
    detectable = bool(comparison.get("detectable"))
    return _out(test, near_half and _built(kind, detectable), n_events=len(ev))


# --- pixel tests -------------------------------------------------------------------------------


def _final(lc, period, t0, duration):
    from refute.packs.tess.detrend import detrend
    from refute.packs.tess.events import per_point_sigma, transit_mask
    from refute.packs.tess.search import finalize_candidate

    plan = _plan()
    half = plan.detrend.transit_mask_half_width_durations * duration
    flat = detrend(lc, plan.detrend, mask=transit_mask(lc.time, period, t0, half))
    sigma = per_point_sigma(flat, transit_mask(flat.time, period, t0, half))
    return finalize_candidate(flat, period, duration, plan.search, 10.0, sigma)


NEIGHBOR = dict(period=5.1, t0=1326.2, duration=2.4 / 24)


def _blend(seed, noise, offset, depth, **kw):
    from refute.packs.tess.synthetic import SignalSpec, make_blend_sky

    red = {"red_noise_ppm": 150.0} if noise == "red" else {}
    spec = SignalSpec(depth=depth, **NEIGHBOR)
    lc, _, aux = make_blend_sky(spec, offset, seed=seed, **red, **kw)
    if noise == "trend":
        from refute.packs.tess.types import LightCurveData

        lc = LightCurveData(
            lc.time,
            lc.flux * (1 + TREND[0] * np.sin(2 * np.pi * lc.time / TREND[1])),
            lc.flux_err,
            lc.sector,
            lc.year,
        )
    return lc, aux


def _planet_pixels(seed, noise):
    from refute.packs.tess.synthetic import (
        PLANET,
        THREE_YEARS,
        make_aux,
        make_lightcurve,
        with_sky_jacobian,
    )

    red = {"red_noise_ppm": 150.0} if noise == "red" else {}
    trend = {"trend_amplitude": TREND[0], "trend_period_days": TREND[1]} if noise == "trend" else {}
    lc, _ = make_lightcurve(
        PLANET, sector_starts=THREE_YEARS, seed=seed, noise_ppm=300.0, **red, **trend
    )
    aux = make_aux(lc, seed=seed)
    pixels = [with_sky_jacobian(px) for px in aux.pixels]
    return lc, pixels, aux.sectors, _final(lc, PLANET.period, PLANET.t0, PLANET.duration)


def centroid(seed, noise, kind):
    from refute.packs.tess.centroid_v5 import check_centroid_v5

    plan = _plan()
    if kind == "c":  # 4.5: an on-target planet, three clean sectors
        _lc_, pixels, sectors, cand = _planet_pixels(seed, noise)
        test = check_centroid_v5(pixels, sectors, cand, plan, seed)
        return _out(
            test, _detectable(test), qualified=len(test.metrics.get("qualified_sectors", {}))
        )
    if kind == "opposite":  # 4.6: two independent sectors, sources 3 px in opposite sky directions
        parts = []
        for k, sign in enumerate((1.0, -1.0)):
            lc, aux = _blend(
                seed + k,
                noise,
                (sign * 63.0, 0.0),
                0.08,
                sector_starts=(1325.0 + 27.4 * k,),
                sector_numbers=(k + 1,),
                pixel_noise=2e-4,
            )
            parts.append((lc, aux))
        from refute.packs.tess.types import LightCurveData

        # the candidate comes from both sectors' light curves, as a real candidate would
        both = LightCurveData(
            *(
                np.concatenate([getattr(lc, f) for lc, _ in parts])
                for f in ("time", "flux", "flux_err", "sector", "year")
            )
        )
        cand = _final(both, NEIGHBOR["period"], NEIGHBOR["t0"], NEIGHBOR["duration"])
        pixels = [p for _, aux in parts for p in aux.pixels]
        sectors = [s for _, aux in parts for s in aux.sectors]
        test = check_centroid_v5(pixels, sectors, cand, plan, seed)
        disagree = test.message.startswith("sectors disagree")
        # an integration check beside the fixture of row 4.6: two independent pixel sectors;
        # whether both qualify is the test's behaviour, counted against the rule when they do
        # not; each sector's offset error (px) recorded from the production sector_offset
        from refute.packs.tess.centroid_v5 import sector_offset

        crowd = {a.sector: a.crowdsap for a in sectors}
        errors = {}
        for px in pixels:
            r = sector_offset(px, cand, plan, crowd.get(px.sector), seed)
            if isinstance(r, dict) and "cov_sky" in r:
                errors[str(px.sector)] = np.sqrt(np.diag(r["cov_sky"])) / r["pixel_scale"]
        return _out(test, len(pixels) == 2, disagree=disagree, offset_errors_px=errors)
    offset, depth = {"a": ((42.0, 0.0), 0.08), "b": ((10.5, 0.0), 0.002)}[kind]
    lc, aux = _blend(seed, noise, offset, depth, **({"pixel_noise": 5e-3} if kind == "b" else {}))
    cand = _final(lc, NEIGHBOR["period"], NEIGHBOR["t0"], NEIGHBOR["duration"])
    test = check_centroid_v5(aux.pixels, aux.sectors, cand, plan, seed)
    qualified = len(test.metrics.get("qualified_sectors", {}))
    if kind == "a":
        return _out(test, qualified >= 2 and _detectable(test), qualified=qualified)
    return _out(test, not _detectable(test), qualified=qualified)


def centroid_fixture(seed, noise, kind):
    """Row 4.6 as written: two sectors whose sky offsets are 3 px in opposite directions with
    errors of 0.3 px (isotropic covariance), drawn from the seed, combined by the production
    ``combine`` and decided by the production heterogeneity rule (``chi2_sf`` against
    ``chi2_alpha``, as ``check_centroid_v5`` does). The pixel experiment is case
    4.6-centroid-opposite-pixels. ``noise`` does not apply (the offset errors are given)."""
    from refute.core.chi2 import chi2_sf
    from refute.packs.tess.centroid_v5 import combine

    sp = _plan().stronger
    scale = 21.0  # arcsec per pixel; the decision is invariant to it
    rng = np.random.default_rng(seed)
    cov = (0.3 * scale) ** 2 * np.eye(2)
    rows = [
        {
            "offset_sky": np.array([s * 3.0 * scale, 0.0]) + rng.normal(0.0, 0.3 * scale, 2),
            "cov_sky": cov,
        }
        for s in (1.0, -1.0)
    ]
    _mean, _cov, chi2 = combine(rows)
    p = chi2_sf(chi2, 2)
    disagree = bool(p < sp.chi2_alpha)
    return _jsonable(
        {
            "status": "INCONCLUSIVE" if disagree else "AGREE",
            "severity": "fatal",
            "reason": f"sectors disagree (heterogeneity p = {p:.2g})" if disagree else "agree",
            "constructed": True,
            "disagree": disagree,
            "offsets_arcsec": [r["offset_sky"] for r in rows],
            "offset_error_px": 0.3,
            "heterogeneity_chi2": chi2,
            "heterogeneity_p": p,
        }
    )


def aperture(seed, noise, kind):
    from refute.packs.tess import power
    from refute.packs.tess.battery import check_aperture_depth

    plan = _plan()
    if kind == "c":
        _lc_, pixels, _sectors, cand = _planet_pixels(seed, noise)
    else:  # a neighbor 2 px away (inside the larger aperture); "b": a faint eclipse
        depth = 0.08 if kind == "a" else 0.004
        lc, aux = _blend(
            seed, noise, (42.0, 0.0), depth, **({"pixel_noise": 2e-3} if kind == "b" else {})
        )
        pixels = aux.pixels
        cand = _final(lc, NEIGHBOR["period"], NEIGHBOR["t0"], NEIGHBOR["duration"])
    test = check_aperture_depth(pixels, cand, plan)
    test = power.attach(test, power.aperture_blocks(test, plan.stronger, seed))
    return _out(test, _built(kind, _detectable(test)))


def systematics(seed, noise, kind):
    """SAP versus PDCSAP ("sap-*") and the background rise ("bkg-*"), on a planet's sectors."""
    from refute.packs.tess import power
    from refute.packs.tess.battery import check_systematics
    from refute.packs.tess.synthetic import make_sector_aux

    plan = _plan()
    part, sub = kind.split("-")
    depth = 3000e-6 if sub in ("a", "c") else 150e-6
    lc = _std_lc(seed, noise, lambda t: _box(t, P, T0, DUR, depth))
    rng = np.random.default_rng([seed, 7])
    crowd = 0.9
    box = {s: _box(lc.time[lc.sector == s], P, T0, DUR, 1.0) for s in lc.sectors}
    rel = plan.gauntlet.systematics.max_sap_rel_diff + plan.stronger.sap_alternative_increment
    frac = (
        plan.gauntlet.systematics.max_background_fraction
        + plan.stronger.background_alternative_increment
    )
    bkg = None
    if part == "bkg" and sub in ("a", "b"):
        bkg = {s: frac * crowd * depth * box[s] for s in lc.sectors}
        if sub == "b":  # below the rule: a noisy background (the construction, 5e-3 per cadence)
            bkg = {s: v + rng.normal(0.0, 5e-3, v.size) for s, v in bkg.items()}
    aux = make_sector_aux(
        lc, crowd, rng, dumps={s: np.array([1200.0]) for s in lc.sectors}, background_series=bkg
    )
    if part == "sap" and sub in ("a", "b"):  # the SAP depth (1 + rel) times the expected one
        aux = [replace(a, sap_flux=1.0 + (1.0 + rel) * crowd * (a.pdcsap_flux - 1.0)) for a in aux]
    cand = _candidate(P, T0, DUR, depth)
    test = check_systematics(aux, cand, plan)
    test = power.attach(test, power.systematics_blocks(test, aux, cand, plan, seed))
    detect = _detectable(test, "sap" if part == "sap" else "background")
    if sub == "c":
        detect = _detectable(test, "sap") and _detectable(test, "background")
    return _out(test, _built(sub, detect))


# --- 1.10 error pulls and 1.11 period_alias ------------------------------------------------------


def pulls(seed, noise, kind):
    """One transit-free curve at a pseudo ephemeris. Row 1.10's 400 windows per noise model are
    400 independent curves: the decided per-event pull is this curve's first measured window
    (``event_pull``), and its group-mean pull is that of all its measured windows (one group per
    curve, 400 groups). Every window's pull is recorded as well (``event_pulls``), reported apart
    and not decided (the windows of one curve share its noise and its detrending)."""
    from refute.packs.tess.events import group_mean

    lc = _std_lc(seed, noise, lambda t: np.zeros_like(t))
    _, ev = _events(lc, _candidate(P, T0 + 0.37, DUR, 1e-3))
    g = group_mean(ev.depths, ev.errors)
    pulls_all = ev.depths / ev.errors
    return _jsonable(
        {
            "status": "MEASURED",
            "constructed": len(ev) >= 3 and bool(np.all(np.isfinite(pulls_all))),
            "event_pull": pulls_all[0] if len(ev) else None,
            "event_pulls": pulls_all,
            "group_pull": g.mean / g.error,
            "group_n": len(ev),
            "floor_used": bool(g.scatter_error is not None and g.scatter_error > g.white_error),
        }
    )


def period_alias(seed, noise, kind):
    from refute.packs.tess.battery import check_period_alias
    from refute.packs.tess.power import period_alias_blocks

    plan = _plan()
    depth = 3000e-6
    lc = _std_lc(seed, noise, lambda t: 0.5 * depth * np.cos(2 * np.pi * (t - T0) / P))
    cand = _candidate(P, T0, DUR, depth)
    test = check_period_alias(lc, cand, plan)
    first = period_alias_blocks(lc, cand, plan, check_period_alias, seed)["main"]
    again = period_alias_blocks(lc, cand, plan, check_period_alias, seed)["main"]
    return {
        "status": test.status.value,
        "severity": test.severity.value,
        "constructed": True,
        "detectable": bool(first["detectable"]),
        "deterministic": first == again,
    }


# --- the matrix -----------------------------------------------------------------------------------
# name: (function, kind, rule, parameter)

CASES = {
    "1.8-odd_even-a": (odd_even, "a", "fail_at_least", 0.95),
    "1.8-odd_even-b": (odd_even, "b", "never_pass", None),
    "1.8-odd_even-c": (odd_even, "c", "false_fail_at_most", 0.0027),
    "1.8-secondary-dip-a": (secondary, "a", "fail_at_least", 0.95),
    "1.8-secondary-dip-b": (secondary, "b", "never_pass", None),
    "1.8-secondary-c": (secondary, "c", "false_fail_at_most", 0.0027),
    "3.1-brightening-a": (secondary, "bright-a", "fail_at_least", 0.95),
    "3.1-brightening-b": (secondary, "bright-b", "never_pass", None),
    "3.2-dip-ratio-0.3": (secondary, "ratio-0.3", "fail_at_least", 0.95),
    "3.2-dip-ratio-1.0": (secondary, "ratio-1.0", "fail_at_least", 0.95),
    "1.8-sinusoid-a": (sinusoid, "a", "fail_at_least", 0.95),
    "1.8-sinusoid-b": (sinusoid, "b", "never_pass", None),
    "3.8-sinusoid-c": (sinusoid, "c", "false_fail_at_most", 0.0027),
    **{
        f"2.1-single_event-equal-{n}": (single_event, f"equal-{n}", "false_fail_at_most", 0.0027)
        for n in (6, 20, 40)
    },
    **{
        f"2.2-single_event-one-{n}": (single_event, f"one-{n}", "fail_at_least", 0.95)
        for n in (6, 20, 40)
    },
    "1.8-single_event-b": (single_event, "weak-6", "never_pass", None),
    **{
        f"2.1-event_consistency-null-{n}": (
            event_consistency,
            f"null-{n}",
            "false_fail_at_most",
            0.0027,
        )
        for n in (6, 20, 40)
    },
    "2.3-event_consistency-deep-6": (event_consistency, "deep-6", "fail_at_least", 0.95),
    "1.8-event_consistency-b": (event_consistency, "weak-6", "never_pass", None),
    "1.8-event_consistency-c": (event_consistency, "strong-6", "false_fail_at_most", 0.0027),
    "2.7-event_consistency-partial-6": (
        event_consistency,
        "partial-6",
        "false_fail_at_most",
        0.0027,
    ),
    "1.8-edge-a": (edge_events, "a", "fail_at_least", 0.95),
    "1.8-edge-b": (edge_events, "b", "never_pass", None),
    "2.5-edge-c": (edge_events, "c", "false_fail_at_most", 0.0027),
    "2.6-edge-ramps": (edge_events, "ramp", "never_pass", None),
    "4.1-centroid-a": (centroid, "a", "fail_at_least", 0.95),
    "1.8-centroid-b": (centroid, "b", "never_pass", None),
    "4.5-centroid-c": (centroid, "c", "false_fail_else_pass", 0.0027),
    "4.6-centroid-opposite": (centroid_fixture, "", "disagree_at_least", 0.95),
    "4.6-centroid-opposite-pixels": (centroid, "opposite", "disagree_at_least", 0.95),
    "1.8-aperture-a": (aperture, "a", "fail_at_least", 0.95),
    "1.8-aperture-b": (aperture, "b", "never_pass", None),
    "1.8-aperture-c": (aperture, "c", "false_fail_at_most", 0.0027),
    "1.8-systematics-sap-a": (systematics, "sap-a", "fail_at_least", 0.95),
    "1.8-systematics-sap-b": (systematics, "sap-b", "never_pass", None),
    "1.8-systematics-bkg-a": (systematics, "bkg-a", "fail_at_least", 0.95),
    "1.8-systematics-bkg-b": (systematics, "bkg-b", "never_pass", None),
    "1.8-systematics-c": (systematics, "sap-c", "false_fail_at_most", 0.0027),
    "1.10-pulls": (pulls, "", "pulls", None),
    "1.11-period_alias": (period_alias, "", "alias", 0.9),
}


# The stellar-trend variant is itself a sinusoidal variability (6 d, twice the cases' period of
# 3 d): it contradicts the sinusoid cases' "no variability" and "variability at P" constructions,
# so those cases run in white and correlated noise only.
NO_TREND = {"1.8-sinusoid-a", "1.8-sinusoid-b", "3.8-sinusoid-c"}


# Cases whose inputs are given, not generated from noisy data: one run, noise "none".
FIXTURES = {"4.6-centroid-opposite"}

# The severity each test must emit (docs/plans/v0.5-plan.md, section 3.10; the v0.4 tests keep
# theirs); every trial's emitted severity is checked against it.
SEVERITY = {
    odd_even: "fatal",
    secondary: "warning",
    sinusoid: "warning",
    single_event: "fatal",
    event_consistency: "fatal",
    edge_events: "warning",
    centroid: "fatal",
    centroid_fixture: "fatal",
    aperture: "fatal",
    systematics: "warning",
    period_alias: "fatal",
}


def noises_for(name: str) -> tuple[str, ...]:
    if name in FIXTURES:
        return ("none",)
    return tuple(n for n in NOISES if not (n == "trend" and name in NO_TREND))


def trials_for(name: str, trials: int) -> int:
    return PULL_TRIALS if name == "1.10-pulls" and trials == ACCEPT_TRIALS else trials


def run_task(task):
    name, noise, i, rule = task
    fn, kind, _rule, _param = CASES[name]
    seed = seed_of(rule, f"{name}:{noise}", i)
    started = time.process_time()
    try:
        out = fn(seed, noise, kind)
    except Exception as exc:  # noqa: BLE001 - recorded: an error invalidates the case
        out = {"status": "ERROR", "error": f"{type(exc).__name__}: {exc}", "constructed": False}
    out.update(case=name, noise=noise, i=i, cpu=time.process_time() - started)
    return out


def decide(name: str, rows: list[dict], expected: int) -> dict:
    fn, _kind, kind, param = CASES[name]
    n = len(rows)
    count = {
        s: sum(r["status"] == s for r in rows) for s in ("PASS", "FAIL", "INCONCLUSIVE", "ERROR")
    }
    constructed = sum(bool(r.get("constructed")) for r in rows)
    row = {"n": n, "expected_trials": expected, **count, "constructed": constructed}
    valid = n == expected and count["ERROR"] == 0 and constructed == n
    required = SEVERITY.get(fn)
    wrong = [
        r["i"] for r in rows if required and r["status"] != "ERROR" and r["severity"] != required
    ]
    row["severity_required"] = required
    row["severity_wrong_trials"] = wrong
    ok = False
    if kind == "fail_at_least":
        need = lower_quantile(n, param)
        row["rule"] = f"FAIL >= {need} (lower 2.5 % of Bin({n}, {param}))"
        ok = count["FAIL"] >= need
    elif kind == "false_fail_at_most":
        limit = upper_quantile(n, param)
        row["rule"] = f"FAIL <= {limit} (upper 97.5 % of Bin({n}, {param}))"
        ok = count["FAIL"] <= limit
    elif kind == "false_fail_else_pass":
        limit = upper_quantile(n, param)
        row["rule"] = f"FAIL <= {limit} (upper 97.5 % of Bin({n}, {param})); every other trial PASS"
        ok = count["FAIL"] <= limit and count["FAIL"] + count["PASS"] == n
    elif kind == "never_pass":
        row["rule"] = "no PASS"
        ok = count["PASS"] == 0
    elif kind == "disagree_at_least":
        need = lower_quantile(n, param)
        disagree = sum(bool(r.get("disagree")) for r in rows)
        row["rule"] = f"INCONCLUSIVE 'sectors disagree' >= {need}"
        row["disagree"] = disagree
        ok = disagree >= need
    elif kind == "pulls":
        # decided: one window per curve and one group per curve (see ``pulls``); a missing
        # value is an invalid trial (not constructed), never a smaller denominator
        events = np.array([r["event_pull"] for r in rows if r.get("event_pull") is not None])
        groups = np.array([r["group_pull"] for r in rows if r.get("group_pull") is not None])
        every = np.array([p for r in rows for p in r.get("event_pulls", [])])
        floor = sum(bool(r.get("floor_used")) for r in rows)
        valid = valid and events.size == n and groups.size == n
        row.update(
            event_pull_sd=float(np.std(events, ddof=1)) if events.size > 1 else None,
            event_pull_mean=float(np.mean(events)) if events.size else None,
            event_pulls=int(events.size),
            group_pull_sd=float(np.std(groups, ddof=1)) if groups.size > 1 else None,
            group_pull_mean=float(np.mean(groups)) if groups.size else None,
            group_pulls=int(groups.size),
            all_windows_sd=float(np.std(every, ddof=1)) if every.size > 1 else None,
            all_windows_mean=float(np.mean(every)) if every.size else None,
            all_windows=int(every.size),
            floor_used=floor,
            rule="one window and one group per curve: pull sd in [0.9, 1.1] and |mean| <= 0.1",
        )
        ok = all(
            sd is not None and 0.9 <= sd <= 1.1 and abs(mean) <= 0.1
            for sd, mean in (
                (row["event_pull_sd"], row["event_pull_mean"]),
                (row["group_pull_sd"], row["group_pull_mean"]),
            )
        )
    elif kind == "alias":
        detectable = [r for r in rows if r.get("detectable")]
        fails = sum(r["status"] == "FAIL" for r in detectable)
        need = lower_quantile(len(detectable), param) if detectable else 0
        deterministic = all(r.get("deterministic") for r in rows)
        row.update(
            detectable=len(detectable),
            fail_when_detectable=fails,
            deterministic=deterministic,
            rule=f"deterministic; detectable in >= 95 % of trials; FAIL >= {need} among them",
        )
        ok = deterministic and len(detectable) >= 0.95 * n and fails >= need
    ok = ok and not wrong
    row["result"] = "PASS" if (valid and ok) else ("INVALID" if not valid else "FAIL")
    return row


NOTES = [
    "WP2 depths are set in the errors the engine measures on each trial's own noise (the same "
    "seed, no signal): the cases test the engine at a fixed engine-estimated SNR, conditional on "
    "the realization, not at a fixed physical depth. The design SNR from the injected depths and "
    "the complete error vector is recorded per trial.",
    "WP2 construction checks are by design: the test is re-run on the injected, noise-free depths "
    "with the trial's measured errors (both WP2 sensitivity blocks are computed from observed "
    "depths). The realized block decides the status; a case below the rule by design does not "
    "guarantee that its realized block stays below it (single_event's alternative is defined at "
    "the observed total SNR). Both blocks are recorded.",
    "Row 2.1 for event_consistency: total SNR 12 and 'detectable by a margin' cannot both hold "
    "(per-event SNR 4.9, 2.7, 1.9 at N = 6, 20, 40); the construction checks the event count "
    "only, a FAIL is a false failure whatever the sensitivity, and the detectable null is case "
    "1.8-event_consistency-c (total SNR 30, N = 6).",
    "Row 3.3: the variability has period 0.83 d (a 3-day sinusoid does not survive the 1-day "
    "detrending); the engine's box estimator on the noise-free signal gives the apparent depth "
    "(semi-amplitude / depth = 2.006); the design significance (true semi-amplitude over the "
    "fit's error at P) is recorded and must exceed 15.",
    "Row 1.10: 400 windows per noise model are 400 independent curves, one window decided per "
    "curve, and 400 groups (one per curve, all its windows); the pulls of every window are "
    "reported apart, not decided.",
    "Row 4.6: a fixture with the row's errors (0.3 px) through the production combination and "
    "heterogeneity rule; the pixel experiment is reported beside it with each sector's measured "
    "offset error.",
    "Row 1.11: the period_alias sensitivity simulation draws white noise internally, also in the "
    "correlated-noise trials; those trials do not validate a correlated internal simulation.",
    "The stellar-trend variant (a 6-day sinusoid) is not run for the sinusoid cases: it is itself "
    "the variability those cases construct or exclude.",
]


def provenance() -> dict:
    import astropy

    def git(*args):
        # fail closed: a git error never reads as a clean tree or an empty commit
        done = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
        if done.returncode != 0:
            raise SystemExit(f"git {' '.join(args)} failed: {done.stderr.strip()}")
        return done.stdout.strip()

    commit = git("rev-parse", "--verify", "HEAD")
    if len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
        raise SystemExit(f"not a commit id: {commit!r}")
    acceptance = (ROOT / "docs" / "plans" / "v0.5-acceptance.md").read_bytes()
    return {
        "commit": commit,
        "dirty": bool(
            git(
                "status",
                "--porcelain",
                "--",
                "src",
                "docs/validation/v0.5",
                "pyproject.toml",
                "uv.lock",
            )
        ),
        "acceptance_sha256": hashlib.sha256(acceptance).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "astropy": astropy.__version__,
        "plan": _plan().model_dump(mode="json"),
        "noise": {"white": WHITE, "red": RED, "tau_days": TAU, "trend": TREND},
    }


def main(argv) -> int:
    from refute.core.runner import default_workers

    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", choices=("dev", "accept"), required=True)
    ap.add_argument("--trials", type=int, default=ACCEPT_TRIALS)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--md", type=Path, required=True)
    ap.add_argument("--detail", type=Path, required=True)
    ap.add_argument("--workers", type=int, default=default_workers())
    ap.add_argument("--cases", default="")
    args = ap.parse_args(argv)
    if args.seeds == "accept" and (args.cases or args.trials != ACCEPT_TRIALS):
        print("the acceptance run is the whole matrix with 200 trials")
        return 2
    if args.out.exists() or args.md.exists() or args.detail.exists():
        print("refusing to overwrite: each run is written once")
        return 2
    prov = provenance()
    if args.seeds == "accept" and prov["dirty"]:
        print("the acceptance run needs committed code (src, docs/validation/v0.5, the lock files)")
        return 2
    names = [c for c in args.cases.split(",") if c] or list(CASES)
    tasks = [
        (name, noise, i, args.seeds)
        for name in names
        for noise in noises_for(name)
        for i in range(trials_for(name, args.trials))
    ]
    wall = time.time()
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        rows = list(pool.map(run_task, tasks, chunksize=2))
    cpu = sum(r["cpu"] for r in rows)
    results = {}
    for name in names:
        for noise in noises_for(name):
            sel = [r for r in rows if r["case"] == name and r["noise"] == noise]
            results[f"{name}/{noise}"] = decide(name, sel, trials_for(name, args.trials))
    # every trial (the construction quantities, the full blocks) goes to its own file, which can
    # exceed the 5 MB limit of git (CLAUDE.md): the summary carries its SHA-256
    detail = (json.dumps({"trials_detail": rows}, sort_keys=True) + "\n").encode("utf-8")
    args.detail.parent.mkdir(parents=True, exist_ok=True)
    args.detail.write_bytes(detail)
    record = {
        "seeds": args.seeds,
        "trials": args.trials,
        "workers": args.workers,
        "processor_seconds": cpu,
        "wall_seconds": time.time() - wall,
        "provenance": prov,
        "notes": NOTES,
        "results": results,
        "detail": {
            "file": args.detail.name,
            "bytes": len(detail),
            "sha256": hashlib.sha256(detail).hexdigest(),
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes((json.dumps(record, indent=1, sort_keys=True) + "\n").encode("utf-8"))
    lines = [
        f"# v0.5 acceptance rate cases ({args.seeds} seeds)",
        "",
        "Synthetic data with known truth (docs/plans/v0.5-acceptance.md, revision 2). A case is "
        "decided only when every scheduled trial ran without error and met its construction; "
        "INVALID otherwise. A FAIL is a recorded result: the test is diagnostic only in v0.5; "
        "nothing is retuned. `method_status: not_validated`.",
        "",
        f"Commit {prov['commit'][:7]} (dirty: {prov['dirty']}); processor time "
        f"{cpu / 3600:.2f} h over {args.workers} workers. Record: `{args.out.name}`; every "
        f"trial: `{args.detail.name}` (SHA-256 {record['detail']['sha256']}).",
        "",
        "Recorded interpretations and limits:",
        "",
        *(f"- {note}" for note in NOTES),
        "",
        "| Case / noise | N | PASS | FAIL | INCONCLUSIVE | Errors | Constructed | Rule | Result |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for key, r in results.items():
        extra = ""
        if "event_pull_sd" in r:
            extra = (
                f" (events sd {r['event_pull_sd']:.3f}, mean {r['event_pull_mean']:.3f}; groups "
                f"sd {r['group_pull_sd']:.3f}, mean {r['group_pull_mean']:.3f}; floor used "
                f"{r['floor_used']}; all {r['all_windows']} windows: sd "
                f"{r['all_windows_sd']:.3f}, mean {r['all_windows_mean']:.3f}, not decided)"
            )
        if "detectable" in r:
            extra = f" (detectable {r['detectable']}, FAIL among them {r['fail_when_detectable']})"
        if "disagree" in r:
            extra = f" (disagree {r['disagree']})"
        if r.get("severity_wrong_trials"):
            extra += f" (wrong severity in {len(r['severity_wrong_trials'])} trials)"
        lines.append(
            f"| {key} | {r['n']} | {r['PASS']} | {r['FAIL']} | {r['INCONCLUSIVE']} | "
            f"{r['ERROR']} | {r['constructed']} | {r['rule']}{extra} | **{r['result']}** |"
        )
    lines.append("")
    args.md.write_bytes("\n".join(lines).encode("utf-8"))
    bad = sorted(k for k, r in results.items() if r["result"] != "PASS")
    print(f"{len(results) - len(bad)} of {len(results)} PASS; not PASS: {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
