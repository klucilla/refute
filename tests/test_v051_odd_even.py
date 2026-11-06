"""v0.5.1 WP3 (d): odd_even with the matched-trapezoid estimator and A0's errors, discovery
version 3 (docs/plans/v0.5.1-acceptance.md). Mechanism cases on synthetic data; the rate rows
(3d.1 to 3d.4) run in the acceptance scripts on frozen code."""

from __future__ import annotations

import math

import numpy as np

from refute.core.verdict import TestStatus
from refute.packs.tess import battery_v51 as v51
from refute.packs.tess import synthetic as syn
from refute.packs.tess.params import TessTestPlan
from refute.packs.tess.synthetic import discovery_v05_plan_dict
from refute.packs.tess.types import Candidate, LightCurveData

CADENCE = 2.0 / 1440.0


def _plan():
    d = discovery_v05_plan_dict()
    d["discovery"]["version"] = 3
    d["v051"] = {}
    return TessTestPlan.model_validate(d)


def _flat(seed, depth, ratio=1.0, period=3.3, t0=2001.1, duration=0.12, sigma=1000e-6):
    """A flattened curve (baseline 1): a planet (ratio 1) or a binary folded at half its period
    (the even events ``ratio`` times as deep)."""
    rng = np.random.default_rng(seed)
    starts = (2000.0, 2027.4, 2054.8)
    t = np.concatenate([syn.sector_times(s) for s in starts])
    sector = np.concatenate(
        [np.full(syn.sector_times(s).size, i + 1) for i, s in enumerate(starts)]
    )
    epoch = np.round((t - t0) / period).astype(int)
    model = syn.trapezoid(t, period, t0, depth, duration, 0.1)
    model = np.where(epoch % 2 == 0, model * ratio, model)
    flux = 1.0 - model + sigma * rng.standard_normal(t.size)
    return LightCurveData(t, flux, np.full(t.size, sigma), sector, np.full(t.size, 2020))


def _cand(depth, period=3.3, t0=2001.1, duration=0.12):
    return Candidate(period=period, t0=t0, duration=duration, depth=depth, depth_err=depth / 10,
                     snr=20.0, log_likelihood=0.0, sde=10.0, n_transits=20)  # fmt: skip


def test_the_estimator_is_close_to_the_cramer_rao_error_in_white_noise():
    plan = _plan()
    depth, sigma, duration = 800e-6, 1000e-6, 0.12
    ratios = []
    for seed in range(4):
        r = v51.check_odd_even(_flat(seed, depth), _cand(depth), plan.gauntlet, plan.stronger,
                               CADENCE, False, seed=1)  # fmt: skip
        assert r.status in (TestStatus.PASS, TestStatus.FAIL)
        n_odd, n_even = r.metrics["n_odd"], r.metrics["n_even"]
        # Cramer-Rao for a trapezoid amplitude (ingress 0.1): sum s^2 per event
        n_in = duration / CADENCE
        info = n_in * (1 - 4 * 0.1 / 3)  # the flat part plus two linear ramps
        cr = math.hypot(sigma / math.sqrt(info * n_odd), sigma / math.sqrt(info * n_even))
        err = math.hypot(r.metrics["depth_odd_err_ppm"], r.metrics["depth_even_err_ppm"]) * 1e-6
        ratios.append(err / cr)
    assert np.median(ratios) <= 1.25


def test_a_folded_binary_with_unequal_eclipses_fails():
    plan = _plan()
    fails = 0
    for seed in range(3):
        r = v51.check_odd_even(_flat(10 + seed, 2000e-6, ratio=0.5), _cand(1500e-6), plan.gauntlet,
                               plan.stronger, CADENCE, False, seed=1)  # fmt: skip
        fails += r.status is TestStatus.FAIL
    assert fails == 3


def test_the_result_carries_its_sensitivity_and_the_full_depth_alternative():
    plan = _plan()
    r = v51.check_odd_even(_flat(20, 1500e-6), _cand(1500e-6), plan.gauntlet, plan.stronger,
                           CADENCE, False, seed=1)  # fmt: skip
    block = r.sensitivity["main"]
    assert block["alternative"] == 1500.0
    assert block["rule_id"] == "gaussian-1"
    assert r.metrics["estimator"].startswith("matched trapezoid")


def test_inconclusive_results_carry_the_phase_half_exclusion_reason(monkeypatch):
    from refute.packs.tess import a0

    plan = _plan()
    reason = "phase-0.5 windows excluded: a secondary detected"
    flat, cand = _flat(30, 1500e-6), _cand(1500e-6)
    monkeypatch.setattr(a0, "stratum_error", lambda *a, **k: (None, {}))
    r = v51.check_odd_even(flat, cand, plan.gauntlet, plan.stronger, CADENCE, True, seed=1)
    assert r.status is TestStatus.INCONCLUSIVE and reason in r.message
    assert r.metrics["inconclusive_class"] == "not_enough_data"
    r = v51.check_odd_even(flat, cand, plan.gauntlet, plan.stronger, CADENCE, False, seed=1)
    assert reason not in r.message
    monkeypatch.undo()
    monkeypatch.setattr(a0, "group_variance", lambda *a, **k: None)
    r = v51.check_odd_even(flat, cand, plan.gauntlet, plan.stronger, CADENCE, True, seed=1)
    assert r.status is TestStatus.INCONCLUSIVE and reason in r.message
    assert r.metrics["inconclusive_class"] == "insufficient_sensitivity"
