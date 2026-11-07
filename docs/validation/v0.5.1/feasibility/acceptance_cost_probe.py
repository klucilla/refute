"""v0.5.1: the processor cost of one unit of each acceptance row type, on development seeds only
(``refute-v051-dev:cost-<kind>:<i>``), to project the acceptance run against the development cap
(plan, amendment 9: stop if the projection passes 45 processor-hours). It decides nothing and
reads no acceptance seed.

Units: ``a0_event`` (one transit-free ephemeris through A0's per-event errors,
``a0.empirical_events``), ``a0_group`` (one transit-free ephemeris through the version-3
``odd_even``: A0's per-event errors and the group variance with the shortcut's bootstrap), and
``c1_v3`` (one C1 curve through the paired chain of the v0.4 and version-3 batteries,
``calib051.tasks.run_c1``: the unit of the combined gates).

Usage: .venv/Scripts/python.exe docs/validation/v0.5.1/feasibility/acceptance_cost_probe.py
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def seed(text: str) -> int:
    return int(hashlib.sha256(text.encode()).hexdigest()[:16], 16)


def transit_free(s: int, sectors: int, correlated: bool):
    from refute.packs.tess import synthetic as syn

    starts = tuple(2000.0 + 27.4 * j for j in range(sectors))
    lc, infos = syn.make_lightcurve(
        None,
        sector_starts=starts,
        noise_ppm=1000.0,
        seed=s,
        red_noise_ppm=500.0 if correlated else 0.0,
    )
    return lc


def candidate(rng):
    from refute.packs.tess.types import Candidate

    period = float(rng.uniform(1.0, 10.0))
    return Candidate(
        period=period,
        t0=2000.0 + float(rng.uniform(0, period)),
        duration=0.12,
        depth=0.001,
        depth_err=0.0001,
        snr=10.0,
        log_likelihood=0.0,
        sde=0.0,
        n_transits=0,
    )


def unit_a0_event(i: int) -> float:
    from refute.packs.tess import a0
    from refute.packs.tess.events import per_event_depths
    from refute.packs.tess.params import TessTestPlan
    from refute.packs.tess.synthetic import discovery_v051_plan_dict

    plan = TessTestPlan.model_validate(discovery_v051_plan_dict())
    s = seed(f"refute-v051-dev:cost-a0_event:{i}")
    lc = transit_free(s, 2, True)
    started = time.process_time()
    cand = candidate(np.random.default_rng(s))
    cadence = 2.0 / 1440.0
    events = per_event_depths(
        lc, cand.period, cand.t0, cand.duration, cadence, plan.gauntlet.events, 0.0, None, None
    )
    a0.empirical_events(lc, cand, events, plan.gauntlet.events, cadence)
    return time.process_time() - started


def unit_a0_group(i: int) -> float:
    from refute.packs.tess import battery_v51 as v51
    from refute.packs.tess.params import TessTestPlan
    from refute.packs.tess.synthetic import discovery_v051_plan_dict

    plan = TessTestPlan.model_validate(discovery_v051_plan_dict())
    s = seed(f"refute-v051-dev:cost-a0_group:{i}")
    lc = transit_free(s, 3, True)
    started = time.process_time()
    cand = candidate(np.random.default_rng(s))
    v51.check_odd_even(lc, cand, plan.gauntlet, plan.stronger, 2.0 / 1440.0, False, s)
    return time.process_time() - started


def unit_c1_v3(i: int) -> float:
    from refute.packs.tess.calib05.steps import v04_test_plan
    from refute.packs.tess.calib051 import tasks

    family = ("P", "SE", "V1", "PX")[i % 4]
    started = time.process_time()
    rec = tasks.run_c1(
        tasks.C1Task(family, i, seed(f"refute-v051-dev:cost-c1:{i}"), v04_test_plan(ROOT))
    )
    _ = rec["status"]
    return time.process_time() - started


def main() -> None:
    out = {"label": "development seeds only; it decides nothing"}
    for name, fn, n in (("a0_event", unit_a0_event, 6), ("a0_group", unit_a0_group, 6),
                        ("c1_v3", unit_c1_v3, 4)):  # fmt: skip
        times = [fn(i) for i in range(n)]
        out[name] = {"n": n, "cpu_seconds": times, "mean": float(np.mean(times))}
        print(name, round(float(np.mean(times)), 2), flush=True)
    with open(HERE / "acceptance-cost-probe.json", "x", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    main()
