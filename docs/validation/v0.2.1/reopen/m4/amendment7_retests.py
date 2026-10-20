"""The numbers of the two retests of map Amendment 7, for the record (the decision is the tests').

Computes, with the code of the commit that runs it, exactly what the two retests assert:
P2 (white ``planet``, seeds 5000 to 5009: the ratios corrected SNR / BLS ``depth_snr`` and their
median) and the timing retest (``synthetic.PLANET``, seeds 2000 to 2014: the number of transits,
the median of error / Carter, the fractions of |pull| <= 1 and <= 2, the median pull). Writes
``amendment7-retests.json`` next to this file.

Run from the worktree root, with the virtual environment's Python:
``docs/validation/v0.2.1/reopen/m4/amendment7_retests.py``.
"""

import json
import sys
from pathlib import Path

import numpy as np

from refute.packs.tess import synthetic
from refute.packs.tess.events import per_point_sigma, transit_mask
from refute.packs.tess.params import TessTestPlan
from refute.packs.tess.pipeline import analyze_data
from refute.packs.tess.timing import corrected_transit_times

HERE = Path(__file__).resolve().parent
CADENCE = 120.0 / 86400.0
PLANET = synthetic.PLANET
TAU = PLANET.ingress_fraction * PLANET.duration
CARTER = (600e-6 / PLANET.depth) * np.sqrt(TAU * CADENCE / 2.0)


def plan_on():
    plan = synthetic.fast_plan_dict()
    plan["gauntlet"] = {"corrections": {"enabled": True}}
    return TessTestPlan.model_validate(plan)


def p2():
    plan = plan_on()
    ratios = []
    for seed in range(5000, 5010):
        analysis = analyze_data(synthetic.scenario_data("planet", seed, "white"), plan)
        snr = next(t for t in analysis.tests if t.name == "snr")
        ratios.append(snr.metrics["snr"] / snr.metrics["bls_depth_snr"])
    return {"seeds": [5000, 5009], "ratios": ratios, "median": float(np.median(ratios))}


def timing():
    plan = plan_on()
    errors, pulls = [], []
    for seed in range(2000, 2015):
        lc, _ = synthetic.make_lightcurve(PLANET, seed=seed)
        sigma = per_point_sigma(
            lc, transit_mask(lc.time, PLANET.period, PLANET.t0, PLANET.duration)
        )
        result = corrected_transit_times(lc, PLANET.period, PLANET.t0, PLANET.duration, sigma, plan)
        for t in result.times:
            truth = PLANET.t0 + t.epoch * PLANET.period
            errors.append(t.error)
            pulls.append((t.time - truth) / t.error)
    pulls = np.asarray(pulls)
    return {
        "seeds": [2000, 2014],
        "n_transits": int(pulls.size),
        "median_error_over_carter": float(np.median(np.asarray(errors) / CARTER)),
        "frac_pull_le_1": float(np.mean(np.abs(pulls) <= 1.0)),
        "frac_pull_le_2": float(np.mean(np.abs(pulls) <= 2.0)),
        "median_pull": float(np.median(pulls)),
    }


out = {"p2": p2(), "timing": timing(), "platform": sys.platform, "numpy": np.__version__}
(HERE / "amendment7-retests.json").write_text(
    json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
)
print(json.dumps(out, indent=2, sort_keys=True))
