"""H3 part 1 measurement (docs/validation/v0.2.1/H3-acceptance.md). No network.

Each task builds one synthetic light curve (signal, noise, N train transits, seed) and
evaluates only the blind-holdout round that hides 2020, with and without the
timing-error floor of option A (applied at every N). The floor is applied by wrapping
``holdout.measure_transit_times`` inside each worker; the engine is not modified.

Usage (from the repository root):

    uv run python docs/validation/v0.2.1/H3/measure.py docs/validation/v0.2.1/H3/results.json

``--workers`` defaults to ``os.cpu_count() - 2``. The published results were produced
with 24 workers pinned off the first four physical cores; the output does not depend
on the number of workers or on the affinity (each task is deterministic in its seed).
"""

from __future__ import annotations

import argparse
import json
import math
import os
from dataclasses import replace

import numpy as np

from refute.core.runner import run_processes
from refute.packs.tess import holdout
from refute.packs.tess import synthetic as s
from refute.packs.tess.params import TessTestPlan
from refute.packs.tess.types import LightCurveData, SectorInfo, btjd_to_year

TRAIN_START, HIDDEN_START = 1325.0, 2061.0
EB = s.SignalSpec(period=2.9, t0=1326.1, depth=0.005, duration=3 / 24, secondary_depth=0.0015)
SIGNALS = {"planet": s.PLANET, "false_positive": EB, "vanishing": s.PLANET}
NS = (3, 4, 5, 6, 7, 8)
NOISES = ("white", "red")
SEEDS = range(60)
CADENCE = 2.0 / 1440.0


def orbit_for(spec: s.SignalSpec, n: int) -> float | None:
    """Shortest orbit length (0.05 d grid, 2-16 d) with exactly n transits in the train
    year, each at least one duration from every edge and the gap, and no other transit
    overlapping the data."""
    d = spec.duration
    for o in np.round(np.arange(2.0, 16.0 + 1e-9, 0.05), 2):
        orbits = [
            (TRAIN_START, TRAIN_START + o),
            (TRAIN_START + o + 1.0, TRAIN_START + 2 * o + 1.0),
        ]
        k0 = math.floor((TRAIN_START - spec.t0) / spec.period) - 1
        k1 = math.ceil((orbits[1][1] - spec.t0) / spec.period) + 1
        good, bad = 0, 0
        for k in range(k0, k1 + 1):
            t = spec.t0 + k * spec.period
            overlaps = [a for a, b in orbits if t + d / 2 > a and t - d / 2 < b]
            if not overlaps:
                continue
            if any(t - a >= 1.5 * d and b - t >= 1.5 * d for a, b in orbits):
                good += 1
            else:
                bad += 1
        if good == n and bad == 0:
            return float(o)
    return None


def build(signal: str, noise: str, n: int, seed: int):
    spec = SIGNALS[signal]
    o = orbit_for(spec, n)
    rng = np.random.default_rng(seed)
    times, fluxes, errors, secs, years, infos = [], [], [], [], [], []
    for number, (start, orbit) in enumerate(((TRAIN_START, o), (HIDDEN_START, 13.0)), 1):
        t = s.sector_times(start, orbit_days=orbit)
        year = btjd_to_year(float(t.min()))
        model = np.ones_like(t)
        if not (signal == "vanishing" and year == 2020):
            model = s.signal_model(t, spec)
        model = model * (1.0 + 0.002 * np.sin(2 * np.pi * t / 6.0))
        f = model + rng.normal(0.0, 600e-6, t.size)
        if noise == "red":
            phi = math.exp(-CADENCE / (1.0 / 24.0))
            ar = np.empty(t.size)
            ar[0] = rng.normal(0.0, 600e-6)
            innov = rng.normal(0.0, 600e-6 * math.sqrt(1 - phi * phi), t.size)
            for i in range(1, t.size):
                ar[i] = phi * ar[i - 1] + innov[i]
            f = f + ar
        times.append(t)
        fluxes.append(f)
        errors.append(np.full(t.size, 600e-6))
        secs.append(np.full(t.size, number))
        years.append(np.full(t.size, year))
        infos.append(
            SectorInfo(number, year, float(t.min()), float(t.max()), int(t.size), f"s{number}.npz")
        )
    lc = LightCurveData(*(np.concatenate(x) for x in (times, fluxes, errors, secs, years)))
    return lc, infos, o


_REAL_MEASURE = holdout.measure_transit_times


def _floored(lc, period, t0, duration, depth, sigma, **kwargs):
    times = _REAL_MEASURE(lc, period, t0, duration, depth, sigma, **kwargs)
    floor = float(np.median(sigma)) / depth * math.sqrt(duration * kwargs["cadence_days"] / 2.0)
    return [replace(t, error=max(t.error, floor)) for t in times]


def task(arg):
    signal, noise, n, seed, floor = arg
    lc, sectors, orbit = build(signal, noise, n, seed)
    spec = SIGNALS[signal]
    plan = TessTestPlan.model_validate(s.fast_plan_dict())
    holdout.measure_transit_times = _floored if floor else _REAL_MEASURE
    try:
        spans = [(x.t_start, x.t_end) for x in sectors if x.year == 2020]
        prepared = holdout.plan_round(lc.select(lc.year != 2020), spans, 2020, plan)
        result = holdout._round(lc, sectors, 2020, plan)
    finally:
        holdout.measure_transit_times = _REAL_MEASURE
    out = {
        "signal": signal,
        "noise": noise,
        "n": n,
        "seed": seed,
        "floor": floor,
        "orbit": orbit,
        "status": result.status.value,
        "n_times": result.metrics.get("n_transit_times"),
        "ephemeris": False,
        "other": False,
        "pulls": [],
        "losses": 0,
        "dev3": 0,
    }
    train, eph = prepared.train, prepared.ephemeris
    if train is not None and abs(train.period - spec.period) / spec.period > 0.01:
        out["other"] = True
    if eph is None or out["other"] or signal == "vanishing":
        return out
    out["ephemeris"] = True
    read = result.status.value in ("PASS", "FAIL")
    for start, end in spans:
        k0 = math.ceil((start - spec.t0) / spec.period)
        k1 = math.floor((end - spec.t0) / spec.period)
        for k in range(k0, k1 + 1):
            t_true = spec.t0 + k * spec.period
            m = round((t_true - eph.t_ref) / spec.period) + eph.n_ref
            t_pred, sig = eph.predict(m)
            err = abs(t_pred - t_true)
            pull = err / sig if sig > 0 else math.inf
            out["pulls"].append(pull)
            out["dev3"] += pull > 3
            if read and err > train.duration / 2 + plan.gauntlet.holdout_by_year.timing_sigma * sig:
                out["losses"] += 1
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("output", help="path of the JSON results file")
    parser.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 1) - 2))
    args = parser.parse_args()
    tasks = [
        (sig, noi, n, seed, floor)
        for sig in SIGNALS
        for noi in NOISES
        for n in NS
        for seed in SEEDS
        for floor in (False, True)
    ]
    results = run_processes(task, tasks, args.workers)
    with open(args.output, "w", encoding="utf-8") as fh:
        json.dump(results, fh)
    print(f"{len(results)} rounds written to {args.output}")


if __name__ == "__main__":
    main()
