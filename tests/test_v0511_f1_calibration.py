"""v0.5.11 step 1: the F1 calibration rule of the frozen specification (docs/plans/v0.5.11-spec.md,
section 4), checked with the test-only reference evaluator, before any `src/` change.

For each seed 1-200, synthetic.make_lightcurve(PLANET, seed=seed) with its defaults (white noise)
and with **CORRELATED_PROFILE (correlated noise), at the true P, t0 and T. Each family must have
all 200 results assessed and at most four OE_box > 3. Exploratory; a software check, not a
population error rate.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from refute.packs.tess.synthetic import CORRELATED_PROFILE, PLANET, make_lightcurve

sys.path.insert(0, str(Path(__file__).resolve().parent))
from screen_reference import f1_reference  # noqa: E402

SEEDS = range(1, 201)
MAX_EXCEEDANCES = 4


def family_counts(correlated: bool) -> dict:
    kwargs = dict(CORRELATED_PROFILE) if correlated else {}
    assessed = unavailable = exceed = 0
    for seed in SEEDS:
        lc, _ = make_lightcurve(PLANET, seed=seed, **kwargs)
        r = f1_reference(lc.time, lc.flux, lc.flux_err, PLANET.period, PLANET.t0, PLANET.duration)
        if r.state == "not_assessed":
            unavailable += 1
            continue
        assessed += 1
        exceed += r.metrics["oe_box"] > 3.0
    return {"assessed": assessed, "unavailable": unavailable, "exceedances": exceed}


@pytest.mark.parametrize("correlated", [False, True], ids=["white", "correlated"])
def test_the_f1_calibration_rule_holds(correlated):
    c = family_counts(correlated)
    assert c["assessed"] == 200, c
    assert c["exceedances"] <= MAX_EXCEEDANCES, c
