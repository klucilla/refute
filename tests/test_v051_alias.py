"""v0.5.1 WP3 (c): period_alias in discovery version 3 (docs/plans/v0.5.1-acceptance.md).
Mechanism cases on synthetic data; the rate rows run in the acceptance scripts on frozen code."""

from __future__ import annotations

import math

import numpy as np
import pytest
from scipy.stats import beta

from refute.core.sensitivity import enforce_sensitivity
from refute.core.verdict import TestStatus
from refute.packs.tess import power
from refute.packs.tess import synthetic as syn
from refute.packs.tess.battery import check_period_alias
from refute.packs.tess.params import TessTestPlan
from refute.packs.tess.power import TESS_REGISTRY_V3
from refute.packs.tess.synthetic import discovery_v05_plan_dict
from refute.packs.tess.types import Candidate, LightCurveData


def _plans():
    v2 = TessTestPlan.model_validate(discovery_v05_plan_dict())
    d = discovery_v05_plan_dict()
    d["discovery"]["version"] = 3
    d["v051"] = {}
    return v2, TessTestPlan.model_validate(d)


def _lc(seed, depth=2000e-6, sinus=False, period=3.3, t0=2001.1, duration=0.12):
    rng = np.random.default_rng(seed)
    t = np.concatenate([syn.sector_times(2000.0), syn.sector_times(2027.4)])
    sector = np.where(t < 2027, 1, 2)
    flux = np.ones_like(t)
    if sinus:
        flux += depth / 2 * np.cos(2 * math.pi * (t - t0) / period + 0.4)
    else:
        flux -= syn.trapezoid(t, period, t0, depth, duration, 0.1)
    flux += 500e-6 * rng.standard_normal(t.size)
    return LightCurveData(t, flux, np.full(t.size, 500e-6), sector, np.full(t.size, 2020))


def _cand(depth=2000e-6, period=3.3, t0=2001.1, duration=0.12):
    return Candidate(period=period, t0=t0, duration=duration, depth=depth, depth_err=depth / 10,
                     snr=20.0, log_likelihood=0.0, sde=10.0, n_transits=10)  # fmt: skip


def test_version_3_uses_four_harmonics_and_version_2_keeps_two():
    v2, v3 = _plans()
    assert power.period_alias_plan(v3).gauntlet.period_alias.sine_harmonics == 4
    assert v2.gauntlet.period_alias.sine_harmonics == 2
    assert v3.gauntlet.period_alias.sine_harmonics == 2  # the plan itself is not changed


def test_the_exact_lower_bound_decides_detectability():
    assert beta.ppf(0.05, 100, 1) == pytest.approx(0.05 ** (1 / 100))
    assert beta.ppf(0.05, 90, 11) < 0.9  # 90 of 100 is not evidence of 0.9


def test_a_planet_passes_with_a_detectable_rule_and_a_sinusoid_fails():
    _, v3 = _plans()
    plan = power.period_alias_plan(v3)
    planet = check_period_alias(_lc(1), _cand(), plan)
    assert planet.status is TestStatus.PASS
    blocks = power.period_alias_blocks_v51(_lc(1), _cand(), plan, check_period_alias, seed=7)
    assert blocks["main"]["realizations"] == 100
    assert blocks["main"]["detectable"] is (blocks["main"]["probability"] >= 0.9)
    passed = power.attach(planet, blocks)
    assert enforce_sensitivity([passed], TESS_REGISTRY_V3)[0].status is TestStatus.PASS
    sinus = check_period_alias(_lc(2, sinus=True), _cand(), plan)
    assert sinus.status is TestStatus.FAIL


def test_the_sensitivity_simulation_is_deterministic():
    _, v3 = _plans()
    plan = power.period_alias_plan(v3)
    a = power.period_alias_blocks_v51(_lc(3), _cand(), plan, check_period_alias, seed=11)
    b = power.period_alias_blocks_v51(_lc(3), _cand(), plan, check_period_alias, seed=11)
    assert a == b
