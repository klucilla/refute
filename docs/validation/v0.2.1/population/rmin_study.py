"""The ``R_min`` study (docs/validation/v0.2.1/reopen/m4-implementation-map.md, Amendment 19; its
implementation, Amendment 26): the evaluator's side of the scenarios.

The study's light curves are the population harness's (``population_v2.build_case``, the frozen
version 2, loaded through version 3, which captures the M4 configuration). This module holds the
pure functions of the scenarios, computed from a case's **recorded final parameters** only (no
random generator is run again):

- ``deficit_and_trend``: the generator's transit deficit ``D(t)`` (``1 - signal_model``) and its
  multiplicative trend (``1`` for ``pure_noise``), as ``build_case`` builds them;
- ``alter_last_year``: the disappearing (``s = 0``) and weakened (``s = 0.3``) scenarios,
  ``flux + (1 - s) D(t) trend(t)`` on the cadences of the last observing year, the noise untouched;
- ``noiseless_model``: the scenario's complete model without noise (the signal times the trend,
  plus the variability, with the alteration where it applies), the twin's input.

The evaluator keeps the parameters and the scenario; the analysis receives only the light curve
and the metadata.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import population_v3 as v3  # noqa: E402

pv2 = v3.pv2

SCENARIOS = {"constant": 1.0, "disappearing": 0.0, "weakened": 0.3}
STUDY_MECHANISMS = ("two_years", "three_years", "few_train", "variability_some_years")


def _check(case: dict) -> None:
    if case["class"] != "planet" or case["mechanism"] not in STUDY_MECHANISMS:
        raise ValueError(f"{case['id']}: not a planet of the study's mechanisms")


def deficit_and_trend(case: dict, p: dict, time: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """The generator's ``D(t)`` and trend at ``time`` (``build_case``, the model before the
    noise)."""
    from refute.packs.tess import synthetic

    _check(case)
    t = np.asarray(time, dtype=float)
    deficit = 1.0 - synthetic.signal_model(t, pv2._signal_spec(synthetic, case, p, p["depth"]))
    if case["mechanism"] == "pure_noise":
        trend = np.ones_like(t)
    else:
        trend = 1.0 + pv2.TREND_AMPLITUDE * np.sin(2 * np.pi * t / pv2.TREND_PERIOD_DAYS)
    return deficit, trend


def _last_year_mask(year: np.ndarray) -> np.ndarray:
    year = np.asarray(year)
    return year == year.max()


def alter_last_year(
    case: dict, p: dict, time: np.ndarray, year: np.ndarray, flux: np.ndarray, s: float
) -> np.ndarray:
    """``flux + (1 - s) D(t) trend(t)`` on the last observing year's cadences; the other cadences
    and the noise unchanged. ``s = 1`` returns the flux as it is."""
    flux = np.asarray(flux, dtype=float)
    if s == 1.0:
        return flux.copy()
    deficit, trend = deficit_and_trend(case, p, time)
    last = _last_year_mask(year)
    return np.where(last, flux + (1.0 - s) * deficit * trend, flux)


def noiseless_model(
    case: dict, p: dict, time: np.ndarray, year: np.ndarray, s: float = 1.0
) -> np.ndarray:
    """The scenario's model without noise: ``(signal + (1 - s_y) D) trend + variability``, with
    ``s_y = s`` in the last observing year and 1 elsewhere (``build_case``'s model, altered as the
    scenario is; with ``s = 1`` the very products of ``build_case``)."""
    from refute.packs.tess import synthetic

    t = np.asarray(time, dtype=float)
    year = np.asarray(year)
    deficit, trend = deficit_and_trend(case, p, t)
    signal = synthetic.signal_model(t, pv2._signal_spec(synthetic, case, p, p["depth"]))
    factor = np.where(_last_year_mask(year), s, 1.0)
    model = (signal + (1.0 - factor) * deficit) * trend
    if "var_amplitude" in p:
        present = year != p.get("var_absent_year")
        model = model + np.where(
            present,
            p["var_amplitude"] * np.sin(2 * np.pi * (t - p["var_phase"]) / p["var_period"]),
            0.0,
        )
    return model


# --- the study's timing lot (Amendment 26, 6) ------------------------------------------------

TIMING_PREFIX = "refute-v0.2.1-rmin-timing"
# The rule fixed by Amendment 26, 6: per noise model, without variability 10 near and 10
# measurable (two_years, three_years, few_train in the proportion 2 : 1 : 1); with variability the
# indexes 200 to 209 of each band.
TIMING_INDEXES = {
    "near": (0, 1, 2, 3, 4, 100, 101, 102, 150, 151, *range(200, 210)),
    "measurable": (0, 1, 2, 3, 4, 100, 101, 150, 151, 152, *range(200, 210)),
}
R_VALUES = (8, 10, 12, 15, 20)
THREAD_ENV = {
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
}


def group_of(case: dict) -> str:
    noise = "white" if case["noise"] == "white" else "AR(1)"
    variability = (
        "variability" if case["mechanism"] == "variability_some_years" else "no variability"
    )
    return f"{noise}, {variability}"


def timing_cases() -> list[dict]:
    """The 80 targets of the timing lot, in the order of the population harness."""
    out = []
    for case in pv2.population_cases("confirm:" + TIMING_PREFIX):
        if case["class"] != "planet" or case["band"] not in TIMING_INDEXES:
            continue
        if case["index"] in TIMING_INDEXES[case["band"]]:
            out.append(case)
    return out


def calibration_identity() -> dict:
    ident = v3.STATE["identity"]
    return {k: ident[k] for k in ("path", "sha256", "block_sha256")}


def time_target(case: dict) -> dict:
    """One target of the timing lot: the generation, then each scenario's rounds (with the twin)
    and its derivation and aggregation over the five R. Only times are returned: no record, count
    or outcome leaves this function (Amendment 26, 6)."""
    import os
    import time

    from refute.packs.tess.holdout import calibration_measurement, derive_round
    from refute.packs.tess.types import LightCurveData

    if v3.STATE["problem"] is not None:
        raise RuntimeError(f"the M4 configuration is not loaded: {v3.STATE['problem']}")
    plan = v3._plan()
    identity = calibration_identity()
    c = plan.gauntlet.corrections
    min_snr = plan.gauntlet.holdout_by_year.min_snr
    start = time.perf_counter()
    blob, _ = pv2.build_case(case)
    meta, arrays = pv2.deserialize(blob)
    data = pv2.parts_to_data(meta, arrays)
    generation = time.perf_counter() - start
    p, lc = meta["parameters"], data.lc
    times = {}
    for scenario, s in SCENARIOS.items():
        t0 = time.perf_counter()
        flux = alter_last_year(case, p, lc.time, lc.year, lc.flux, s)
        raw = LightCurveData(lc.time, flux, lc.flux_err, lc.sector, lc.year)
        model = noiseless_model(case, p, lc.time, lc.year, s)
        records = [
            calibration_measurement(
                raw, data.sectors, year, plan, identity=identity, twin_model=model
            )
            for year in raw.years
        ]
        t1 = time.perf_counter()
        for r_min in R_VALUES:
            outcomes = [
                derive_round(rec, r_min, c.capacity_b, c.capacity_s, min_snr) for rec in records
            ]
            _ = (any(o["status"] == "FAIL" for o in outcomes), any(o["eligible"] for o in outcomes))
        t2 = time.perf_counter()
        times[scenario] = {"rounds": t1 - t0, "aggregation": t2 - t1, "total": t2 - t0}
        del records, outcomes
    return {
        "target": f"{TIMING_PREFIX}/{case['id']}",
        "group": group_of(case),
        "generation_seconds": generation,
        "scenarios": times,
        "pid": os.getpid(),
        "identity_block_sha256": identity["block_sha256"],
    }


def run_timing_lot(out: Path, workers: int = 6) -> dict:
    """Run the timing lot on 6 spawned workers (the caller's affinity, logical processors 0 to 7,
    is inherited) and write its dated record to ``out`` (never replaced)."""
    import json
    import multiprocessing
    import os
    import statistics
    import subprocess
    import time
    from concurrent.futures import ProcessPoolExecutor
    from datetime import UTC, datetime

    if out.exists():
        raise SystemExit(f"{out} exists; not replaced")
    if v3.STATE["problem"] is not None:
        raise SystemExit(f"the M4 configuration is not loaded: {v3.STATE['problem']}")
    os.environ.update(THREAD_ENV)
    cases = timing_cases()
    head = subprocess.run(
        ["git", "-C", str(v3.CHECKOUT_ROOT), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    dirty = subprocess.run(
        ["git", "-C", str(v3.CHECKOUT_ROOT), "status", "--porcelain", "--untracked-files=no"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    if dirty:
        raise SystemExit("the checkout has uncommitted changes: the record names a commit")
    started = datetime.now(UTC).isoformat(timespec="seconds")
    wall = time.perf_counter()
    ctx = multiprocessing.get_context("spawn")
    with ProcessPoolExecutor(max_workers=workers, mp_context=ctx) as pool:
        results = list(pool.map(time_target, cases))
    wall = time.perf_counter() - wall
    expected = calibration_identity()["block_sha256"]
    if any(r["identity_block_sha256"] != expected for r in results):
        raise SystemExit("a worker measured another corrections block")
    summary: dict = {}
    for group in sorted({r["group"] for r in results}):
        rows = [r for r in results if r["group"] == group]
        entry = {
            "targets": len(rows),
            "generation": {
                "median": statistics.median(r["generation_seconds"] for r in rows),
                "max": max(r["generation_seconds"] for r in rows),
            },
        }
        for scenario in SCENARIOS:
            values = [r["scenarios"][scenario]["total"] for r in rows]
            entry[scenario] = {"median": statistics.median(values), "max": max(values)}
        summary[group] = entry
    ident = v3.STATE["identity"]
    record = {
        "format": "refute-v0.2.1-rmin-timing/1",
        "note": "times only (map Amendment 26, 6): no outcome, pull, rate or count is recorded",
        "started_utc": started,
        "code_commit": head,
        "configuration": {k: ident[k] for k in ("name", "path", "sha256", "block_sha256")},
        "workers": workers,
        "thread_env": THREAD_ENV,
        "wall_seconds": wall,
        "targets": len(results),
        "light_curves": len(results) * len(SCENARIOS),
        "per_target": [{k: v for k, v in r.items() if k != "pid"} for r in results],
        "summary": summary,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8", newline="\n")
    return record


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="mode", required=True)
    t = sub.add_parser("timing", help="run the study's timing lot (Amendment 26, 6)")
    t.add_argument("--out", required=True)
    t.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()
    run_timing_lot(Path(args.out), args.workers)
