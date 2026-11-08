"""v0.5.2 stage 1: the task-count and cost worksheet, and the options for the acceptance's cost
(the maintainer's decision of 2026-11-08, #216, item 1 (a)). Development seeds only; no acceptance
seed is computed (the schedule's seed function is replaced by a constant, for counting). It decides
nothing. ``method_status: not_validated``.

Three parts, each a sub-command, each writing a JSON next to this file:

- ``probe``: the cost per unit of each kind of work, against the number of processes.
- ``sizes``: what the equivalence criterion of the proposal needs per cell (a Monte Carlo of the
  fixed design and of sequential designs on pulls with a known law; see the docstring of ``sizes``).
- ``table``: the totals of each option, from the two above and the unit counts of the v0.5.1
  acceptance schedule.

Usage (from the project root): ``scripts/launch_affinity.ps1 -Script <this file> -Arguments probe
-Log .cache/v052/worksheet/probe``, then ``.venv/Scripts/python.exe <this file> sizes``, ``table``.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "docs/validation/v0.5.1/acceptance"))
import a0 as runner  # noqa: E402

WORKERS = (1, 4, 8, 16)
UNITS_PER_POINT = 32
C1_CURVES_PER_FAMILY = 3
C1_WORKERS = 4
TOLERANCE_MEAN = 0.1
TOLERANCE_SD = 0.1
FAMILYWISE = 0.05
CERTIFICATION = 0.90
LOOKS = (0.25, 0.5, 0.75, 1.0)
REPS = 4000


def dev_seed(kind: str, i: int) -> int:
    return int(
        hashlib.sha256(f"refute-v052-dev:worksheet:{kind}:{i}".encode()).hexdigest()[:16], 16
    )


def task_a01(i):
    return runner.unit_a01(("correlated", "full", i, dev_seed("a01", i)))


def task_a02(i):
    return runner.unit_group(("a02", "correlated", "full", 2, i, dev_seed("a02", i)))


def task_a05(i):
    return runner.unit_a05(("p1", 3.0, "equal", "correlated", "full", 2, i, dev_seed("a05", i)))


def task_a08(i):
    return runner.unit_a08(("group", "correlated", "full", 2, 3.0, i, dev_seed("a08", i)))


TASKS = {"a01": task_a01, "a02": task_a02, "a05": task_a05, "a08": task_a08}


def _measure(arg):
    name, i = arg
    started = time.process_time()
    TASKS[name](i)
    return time.process_time() - started


def _warm():
    from refute.packs.tess import a0, battery_v51, power  # noqa: F401
    from refute.packs.tess import battery_v51_diff as _d  # noqa: F401

    runner._plan()
    runner.c.noise_curve(0, "white", 1)


def c1_curve(arg):
    """One development curve of a C1 family through the paired chain, as C1' would run it."""
    from refute.packs.tess.calib05 import c1
    from refute.packs.tess.calib05.steps import v04_test_plan
    from refute.packs.tess.calib051.plans import pair
    from refute.packs.tess.detrend import detrend
    from refute.packs.tess.discover.paired import _outcome as paired_outcome
    from refute.packs.tess.pipeline import attack_candidate, global_prewhitening
    from refute.packs.tess.search import search_period

    family, i = arg
    started = time.process_time()
    try:
        data, _ = c1.generate(family, c1.development_seed(family, i))
    except c1.GenerationFailedError:
        return {"family": family, "cpu_seconds": time.process_time() - started, "failed": True}
    p04, p3 = pair(v04_test_plan(ROOT))
    flat = detrend(data.lc, p04.detrend)
    pw, searched = global_prewhitening(data, p04, flat)
    cand = search_period(searched, p04.search).candidate
    paired_outcome(data, cand, p04, 2, None, None, pw)
    attack_candidate(data, cand, p3, None, None, pw)
    return {"family": family, "cpu_seconds": time.process_time() - started, "failed": False}


def probe():
    from refute.packs.tess.calib05 import c1

    out = {
        "label": "development probes of cost; it decides nothing",
        "method_status": "not_validated",
    }
    scan = {}
    for name in TASKS:
        scan[name] = {}
        for workers in WORKERS:
            with ProcessPoolExecutor(max_workers=workers, initializer=_warm) as pool:
                list(pool.map(_measure, [(name, 10_000 + j) for j in range(workers)]))
                start = time.perf_counter()
                cpu = list(pool.map(_measure, [(name, i) for i in range(UNITS_PER_POINT)]))
                wall = time.perf_counter() - start
            scan[name][str(workers)] = {
                "units": UNITS_PER_POINT,
                "wall_seconds": wall,
                "units_per_second": UNITS_PER_POINT / wall,
                "cpu_seconds_per_unit": float(np.mean(cpu)),
            }
            print(name, workers, scan[name][str(workers)], flush=True)
    out["scan"] = scan
    families = list(c1.FAMILIES)
    args = [(f, i) for f in families for i in range(C1_CURVES_PER_FAMILY)]
    with ProcessPoolExecutor(max_workers=C1_WORKERS, initializer=_warm) as pool:
        start = time.perf_counter()
        rows = list(pool.map(c1_curve, args))
        wall = time.perf_counter() - start
    out["c1"] = {
        "workers": C1_WORKERS,
        "wall_seconds": wall,
        "curves": len(rows),
        "failed": sum(r["failed"] for r in rows),
        "per_family_cpu_seconds": {
            f: float(np.mean([r["cpu_seconds"] for r in rows if r["family"] == f]))
            for f in families
        },
    }
    out["c1"]["mean_cpu_seconds"] = float(np.mean([r["cpu_seconds"] for r in rows]))
    (HERE / "worksheet-probe.json").write_text(
        json.dumps(out, indent=1, sort_keys=True) + "\n", "utf-8"
    )
    print(json.dumps(out["c1"], indent=1))


# --- the sizes ----------------------------------------------------------------------------------


def _z_star(cells):
    """The simultaneous critical value (Bonferroni over cells, two parameters and two tails)."""
    return float(stats.norm.ppf(1.0 - FAMILYWISE / (4.0 * cells)))


def _certified(mean, sd, n, z):
    half_mean = z * sd / np.sqrt(n)
    half_sd = z * sd / np.sqrt(2.0 * (n - 1))
    mean_ok = np.abs(mean) + half_mean < TOLERANCE_MEAN
    sd_ok = (sd - half_sd > 1.0 - TOLERANCE_SD) & (sd + half_sd < 1.0 + TOLERANCE_SD)
    return mean_ok & sd_ok


def _draw(rng, n, mu, sigma, reps):
    mean = rng.normal(mu, sigma / np.sqrt(n), reps)
    s2 = sigma**2 * rng.chisquare(n - 1, reps) / (n - 1)
    return mean, np.sqrt(s2)


def _fixed_n(z, rng):
    """The smallest n (on a grid of 100) certifying a calibrated cell at the target probability."""
    for n in range(400, 40_001, 100):
        m, s = _draw(rng, n, 0.0, 1.0, REPS)
        if np.mean(_certified(m, s, n, z)) >= CERTIFICATION:
            return n
    return None


def _sequential(z_at_look, n_max, truth, rng, looks):
    """Group-sequential looks: at each look a cell stops as accepted if it is certified, or as
    miscalibrated if an interval lies wholly outside a tolerance; the increments are simulated
    exactly for the mean and by a chi-square for the variance. Returns (expected n, P(accepted),
    P(miscalibrated))."""
    mu, sigma = truth
    n_done = np.zeros(REPS)
    verdict = np.zeros(REPS, dtype=int)  # 0 running/undecided, 1 accepted, -1 miscalibrated
    total, ss, count = np.zeros(REPS), np.zeros(REPS), np.zeros(REPS)
    prev = 0
    for k, frac in enumerate(looks):
        n = int(math.ceil(frac * n_max))
        step = n - prev
        batch_mean = rng.normal(mu, sigma / np.sqrt(step), REPS)
        batch_ss = sigma**2 * rng.chisquare(step - 1, REPS) if step > 1 else np.zeros(REPS)
        new_count = count + step
        delta = batch_mean - np.divide(total, count, out=np.zeros(REPS), where=count > 0)
        ss = ss + batch_ss + (count * step / new_count) * delta**2
        total = total + batch_mean * step
        count = new_count
        prev = n
        running = verdict == 0
        m = total / count
        s = np.sqrt(ss / (count - 1))
        z = z_at_look[k]
        half_mean, half_sd = z * s / np.sqrt(count), z * s / np.sqrt(2.0 * (count - 1))
        accept = _certified(m, s, count, z)
        out_mean = np.abs(m) - half_mean > TOLERANCE_MEAN
        out_sd = (s - half_sd > 1.0 + TOLERANCE_SD) | (s + half_sd < 1.0 - TOLERANCE_SD)
        reject = out_mean | out_sd
        verdict[running & accept] = 1
        verdict[running & ~accept & reject] = -1
        n_done[running] = n
    return float(n_done.mean()), float(np.mean(verdict == 1)), float(np.mean(verdict == -1))


def sizes():
    """For cell counts M, the simultaneous critical value and the n certifying a calibrated cell at
    90 %; then a fixed design (one look) and sequential designs (four looks): O'Brien-Fleming-type
    (critical value ``z sqrt(1/t)``, the alpha-spending analogue), Pocock-type (a constant 1.2 z, an
    illustrative inflation of the critical value), and a confidence-sequence-type width (a constant
    1.5 z, illustrative). Each is evaluated on a calibrated cell, a mean-biased (0.05) cell and a
    clearly miscalibrated cell (mean 0.2, sd 1.2). The pulls are independent Gaussians: an
    idealization, and the critical values are Bonferroni: conservative against a max-t bootstrap."""
    rng = np.random.default_rng(20261108)
    out = {"label": "development sizing; it decides nothing", "method_status": "not_validated"}
    truths = (
        ("calibrated", (0.0, 1.0)),
        ("biased_0.05", (0.05, 1.0)),
        ("miscalibrated_0.2_1.2", (0.2, 1.2)),
    )
    for cells in (150, 500, 1500):
        z = _z_star(cells)
        n_fixed = _fixed_n(z, rng)
        block = {"z_star": z, "n_fixed_90pct": n_fixed}
        designs = {
            "fixed": ((1.0,), [z], 1.0),
            "obrien_fleming_type": (LOOKS, [z / math.sqrt(t) for t in LOOKS], 1.05),
            "pocock_type_1.2z": (LOOKS, [1.2 * z] * len(LOOKS), 1.2**2 * 1.05),
            "confidence_sequence_type_1.5z": (LOOKS, [1.5 * z] * len(LOOKS), 1.5**2 * 1.05),
        }
        for name, (looks, z_at, scale) in designs.items():
            n_max = int(math.ceil(n_fixed * scale))
            rows = {}
            for label, truth in truths:
                e, acc, rej = _sequential(z_at, n_max, truth, rng, looks)
                rows[label] = {"expected_n": e, "accepted": acc, "miscalibrated": rej}
            block[name] = {"n_max": n_max, "by_truth": rows}
        out[f"cells_{cells}"] = block
    (HERE / "worksheet-sizes.json").write_text(
        json.dumps(out, indent=1, sort_keys=True) + "\n", "utf-8"
    )
    print(json.dumps(out, indent=1, sort_keys=True))


# --- the table ----------------------------------------------------------------------------------


def _unit_counts():
    """The units of each A0 section at 400 per row, from its schedule; the seed function replaced
    by a constant, so that no acceptance seed is computed."""
    runner.c.accept_seed = lambda *_a, **_k: 0
    return {s: len(runner.schedule(s)) for s in runner.SECTIONS if not s.startswith("sabotage")}


KIND_OF_SECTION = {
    "a01": "a01",
    "a02": "a02",
    "a04": "a02",
    "a05": "a05",
    "a06": "a01",
    "a07": "a02",
    "a08": "a08",
}


def table():
    probe_doc = json.loads((HERE / "worksheet-probe.json").read_text("utf-8"))
    size_doc = json.loads((HERE / "worksheet-sizes.json").read_text("utf-8"))
    counts = _unit_counts()
    best = {}
    for name, rows in probe_doc["scan"].items():
        pick = max(rows.items(), key=lambda kv: kv[1]["units_per_second"])
        best[name] = {
            "workers": int(pick[0]),
            "units_per_second": pick[1]["units_per_second"],
            "cpu_seconds_per_unit": pick[1]["cpu_seconds_per_unit"],
            "cpu_seconds_at_16_workers": rows["16"]["cpu_seconds_per_unit"],
            "units_per_second_at_16_workers": rows["16"]["units_per_second"],
        }
    out = {
        "label": "development worksheet; it decides nothing",
        "method_status": "not_validated",
        "units_at_400_per_row": counts,
        "best_worker_count_per_kind": best,
    }

    def total(section_factor):
        cpu = wall = 0.0
        for section, n in counts.items():
            kind = KIND_OF_SECTION[section]
            units = n * section_factor.get(section, 1.0)
            cpu += units * best[kind]["cpu_seconds_per_unit"] / 3600.0
            wall += units / best[kind]["units_per_second"]
        return {"cpu_hours": cpu, "machine_days": wall / 86400.0}

    scale = {}
    for cells in (150, 500, 1500):
        s = size_doc[f"cells_{cells}"]
        scale[str(cells)] = {
            "n_fixed": s["n_fixed_90pct"],
            "expected_n_calibrated": {
                k: s[k]["by_truth"]["calibrated"]["expected_n"]
                for k in (
                    "fixed",
                    "obrien_fleming_type",
                    "pocock_type_1.2z",
                    "confidence_sequence_type_1.5z",
                )
            },
            "expected_n_miscalibrated": {
                k: s[k]["by_truth"]["miscalibrated_0.2_1.2"]["expected_n"]
                for k in (
                    "fixed",
                    "obrien_fleming_type",
                    "pocock_type_1.2z",
                    "confidence_sequence_type_1.5z",
                )
            },
        }
    out["per_cell_sizes"] = scale
    options = {}
    n500 = scale["500"]["n_fixed"]
    factor = n500 / 400.0
    every = {s: factor for s in counts}
    options["A: the v0.5.1 grid, fixed sample, 500-cell family"] = total(every)
    no_a05 = dict(every)
    no_a05["a05"] = 400.0 / 400.0
    options["B: A with the A0.5 patterns kept at 400 per row (diagnostic only)"] = total(no_a05)
    grouped = {s: factor / 3.0 for s in counts}
    options["C: A with the three coverage strata grouped by a validated envelope (factor 1/3)"] = (
        total(grouped)
    )
    obf = scale["500"]["expected_n_calibrated"]["obrien_fleming_type"] / 400.0
    options["D: A with O'Brien-Fleming-type looks, every cell calibrated"] = total(
        {s: obf for s in counts}
    )
    options["E: the v0.5.1 grid at its 400 per row (reference)"] = total({s: 1.0 for s in counts})
    out["options"] = options
    c1 = probe_doc["c1"]
    out["c1_prime_2400_curves_cpu_hours"] = 2400 * c1["mean_cpu_seconds"] / 3600.0
    out["c1_probe_mean_cpu_seconds_per_curve"] = c1["mean_cpu_seconds"]
    (HERE / "worksheet-table.json").write_text(
        json.dumps(out, indent=1, sort_keys=True) + "\n", "utf-8"
    )
    print(json.dumps(out, indent=1, sort_keys=True))


if __name__ == "__main__":
    command = sys.argv[1:] or [""]
    if command[0] == "probe":
        probe()
    elif command[0] == "sizes":
        sizes()
    elif command[0] == "table":
        table()
    else:
        raise SystemExit("usage: worksheet.py probe|sizes|table")
