"""v0.5.2 stage 2: the unit costs the budget needs beyond A0: the sinusoid decision, a period search
at the fast and the claim plans, a whole analysis at the claim plan, and A0 on many-sector curves.
Development seeds; it decides nothing. ``method_status: not_validated``.

Usage: ``scripts/launch_affinity.ps1 -Script <this file> -Log .cache/v052/s2/probe-other``;
writes ``probe-other-costs.json``.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))
import a0v4  # noqa: E402

v3 = a0v4.v3
c = v3.c
REPEATS = 6


def curve(seed, sectors=2, noise="correlated"):
    from refute.packs.tess import synthetic as syn
    from refute.packs.tess.types import LightCurveData

    lc, _ = c.noise_curve(seed, noise, sectors)
    cand = v3._candidate(lc.time, np.random.default_rng([seed, 1]), depth=2e-3)
    planet = syn.trapezoid(lc.time, cand.period, cand.t0, 2e-3, cand.duration, 0.1)
    phase = 2.0 * np.pi * (lc.time - cand.t0) / (cand.period * 0.5)
    flux = lc.flux - planet + 2e-3 * np.cos(phase)
    return LightCurveData(lc.time, flux, lc.flux_err, lc.sector, lc.year), cand


def seconds(fn, items):
    started = time.process_time()
    for item in items:
        fn(item)
    return (time.process_time() - started) / len(items)


def main() -> None:
    from refute.packs.tess import battery_v52 as v52
    from refute.packs.tess import pipeline as pl
    from refute.packs.tess import synthetic as syn
    from refute.packs.tess.params import TessTestPlan
    from refute.packs.tess.pipeline import analyze_data, search_period

    fast = TessTestPlan.model_validate(syn.discovery_v052_plan_dict())
    full_raw = syn.discovery_v052_plan_dict()
    full_raw.pop("search", None)
    full = TessTestPlan.model_validate(full_raw)
    curves = [curve(70000 + i) for i in range(REPEATS)]
    out = {}

    def sinusoid(item):
        lc, cand = item
        v52.check_sinusoid(
            lc, cand, fast.stronger, fast.v051, fast.gauntlet.events, c.CADENCE, True, 3
        )

    out["sinusoid_decision_2_sectors"] = seconds(sinusoid, curves)
    flats = [(pl.detrend(lc, fast.detrend), cand) for lc, cand in curves]
    out["search_fast_plan_2_sectors"] = seconds(lambda x: search_period(x[0], fast.search), flats)
    out["search_claim_plan_2_sectors"] = seconds(
        lambda x: search_period(x[0], full.search), flats[:2]
    )
    scenario = [syn.scenario_data("planet", seed=70 + i) for i in range(2)]
    out["analysis_fast_plan"] = seconds(lambda d: analyze_data(d, fast), scenario)
    out["analysis_claim_plan"] = seconds(lambda d: analyze_data(d, full), scenario[:1])

    for sectors in (5, 8, 12, 20):
        plan = v3._plan()
        items = []
        for i in range(3):
            seed = 71000 + sectors * 100 + i
            lc, _ = c.noise_curve(seed, "correlated", sectors)
            items.append((lc, v3._candidate(lc.time, np.random.default_rng([seed, 1]))))

        def many(item, plan=plan):
            lc, cand = item
            choice = v52.choose_sectors(
                lc.time, lc.sector, cand, plan.gauntlet.events, c.CADENCE, True
            )
            p = a0v4.prepare(lc, cand, plan)
            sub = p.flat.select(np.isin(p.flat.sector, choice.chosen))
            from refute.packs.tess import a0_v4

            measure = a0_v4.comb_measure(
                p.preprocess, p.raw.time, sub, cand.duration, p.half, plan.gauntlet.events,
                c.CADENCE,
            )  # fmt: skip
            events = a0v4.events_of(sub, cand, plan)
            a0_v4.empirical_events(
                sub, cand, events, plan.gauntlet.events, c.CADENCE, measure, False
            )

        out[f"a0_selected_from_{sectors}_sectors"] = seconds(many, items)
    print(json.dumps(out, indent=1, sort_keys=True), flush=True)
    (HERE / "probe-other-costs.json").write_text(
        json.dumps(
            {
                "label": "unit costs at one worker, measured on few curves; it decides nothing",
                "method_status": "not_validated",
                "cpu_seconds_per_unit": out,
            },
            indent=1,
            sort_keys=True,
        )
        + "\n",
        "utf-8",
    )


if __name__ == "__main__":
    main()
