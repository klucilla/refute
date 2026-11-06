"""v0.5.1 WP3 (b): the sinusoid test per harmonic, discovery version 3
(docs/plans/v0.5.1-acceptance.md). Mechanism cases on synthetic data with development seeds; the
rate cases (200 trials on acceptance seeds) run in the acceptance scripts on frozen code."""

from __future__ import annotations

import math

import numpy as np
import pytest

from refute.core.sensitivity import enforce_sensitivity
from refute.core.verdict import Severity, TestStatus
from refute.packs.tess import battery_v5 as v5
from refute.packs.tess import battery_v51 as v51
from refute.packs.tess import synthetic as syn
from refute.packs.tess.params import CorrectionsParams, StrongerParams, TessTestPlan
from refute.packs.tess.power import TESS_REGISTRY, TESS_REGISTRY_V3, registry_for
from refute.packs.tess.synthetic import discovery_v05_plan_dict
from refute.packs.tess.types import Candidate, LightCurveData

SP = StrongerParams()
CP = CorrectionsParams()


def _v3_plan_dict() -> dict:
    d = discovery_v05_plan_dict()
    d["discovery"]["version"] = 3
    d["corrections"] = {}
    return d


def _lc(seed, period=3.3, t0=2001.1, depth=1500e-6, duration=0.12, trend=None, sinus=None,
        sigma=1000e-6, sectors=(2000.0, 2027.4)):  # fmt: skip
    rng = np.random.default_rng(seed)
    t = np.concatenate([syn.sector_times(s) for s in sectors])
    sector = np.concatenate(
        [np.full(syn.sector_times(s).size, i + 1) for i, s in enumerate(sectors)]
    )
    flux = np.ones_like(t)
    if depth:
        flux -= syn.trapezoid(t, period, t0, depth, duration, 0.1)
    if sinus is not None:
        p, amp = sinus
        flux += amp * np.sin(2 * math.pi * t / p + 0.7)
    if trend is not None:
        p, amp = trend
        flux *= 1.0 + amp * np.sin(2 * math.pi * t / p + 1.3)
    flux += sigma * rng.standard_normal(t.size)
    return LightCurveData(t, flux, np.full(t.size, sigma), sector, np.full(t.size, 2020))


def _cand(period=3.3, t0=2001.1, depth=1500e-6, duration=0.12):
    return Candidate(
        period=period,
        t0=t0,
        duration=duration,
        depth=depth,
        depth_err=depth / 10,
        snr=20.0,
        log_likelihood=0.0,
        sde=10.0,
        n_transits=10,
    )


# --- the schema ----------------------------------------------------------------------------


def test_version_3_needs_the_corrections_section_and_only_it():
    plan = TessTestPlan.model_validate(_v3_plan_dict())
    assert plan.v05 and plan.v051
    assert registry_for(plan) is TESS_REGISTRY_V3
    bad = _v3_plan_dict()
    del bad["corrections"]
    with pytest.raises(ValueError, match="corrections"):
        TessTestPlan.model_validate(bad)
    v05 = discovery_v05_plan_dict()
    v05["corrections"] = {}
    with pytest.raises(ValueError, match="corrections"):
        TessTestPlan.model_validate(v05)


def test_a_version_2_plan_dumps_and_runs_exactly_as_before():
    plan = TessTestPlan.model_validate(discovery_v05_plan_dict())
    assert not plan.v051
    assert registry_for(plan) is TESS_REGISTRY
    assert "corrections" not in plan.model_dump(mode="json")


def test_the_v3_registry_changes_only_the_sinusoid():
    assert set(TESS_REGISTRY_V3) == set(TESS_REGISTRY)
    for name in TESS_REGISTRY:
        if name != "sinusoid":
            assert TESS_REGISTRY_V3[name] == TESS_REGISTRY[name]
    assert TESS_REGISTRY_V3["sinusoid"] == {"P/2": "rule", "P": "rule?", "2P": "rule?"}


# --- the harmonic domain (#203; rows 3.5, 3.6) ---------------------------------------------


@pytest.mark.parametrize("period", [12.0, 15.0])
def test_long_periods_test_p_half_and_p_and_leave_2p_not_applicable(period):
    lc = _lc(1, period=period, t0=2003.0)
    result = v51.check_sinusoid(lc, _cand(period=period, t0=2003.0), SP, CP, seed=3)
    assert result.status is not TestStatus.INCONCLUSIVE
    blocks = result.sensitivity
    assert blocks["2P"] == {"applicable": False, "reason": blocks["2P"]["reason"]}
    assert "detectable" in blocks["P/2"] and "detectable" in blocks["P"]
    # the v0.5 test refused the same candidate before reading data
    old = v5.check_sinusoid(lc, _cand(period=period, t0=2003.0), SP, seed=3)
    assert old.status is TestStatus.INCONCLUSIVE and "domain" in old.message


def test_beyond_every_harmonic_domain_the_test_is_inconclusive_with_its_class():
    lc = _lc(1, period=41.0, t0=2003.0, sectors=(2000.0, 2027.4, 2054.8))
    result = v51.check_sinusoid(lc, _cand(period=41.0, t0=2003.0), SP, CP, seed=3)
    assert result.status is TestStatus.INCONCLUSIVE
    assert result.metrics["inconclusive_class"] == "outside_domain"


def test_a_sinusoid_at_fourteen_days_found_as_a_box_is_flagged():
    lc = _lc(2, period=14.0, t0=2003.0, depth=0.0, sinus=(14.0, 3000e-6))
    cand = _cand(period=14.0, t0=2003.0, depth=2000e-6, duration=0.3)
    result = v51.check_sinusoid(lc, cand, SP, CP, seed=3)
    assert result.status is TestStatus.FAIL
    assert result.severity is Severity.WARNING


# --- the joint model with the star's other variability (rows 3.2, 3.7) ---------------------


def test_a_planet_on_a_trending_star_becomes_decidable_and_is_not_flagged():
    # the development diagnosis: v0.5 refused a PASS on trending stars (beta from the trend);
    # a trend at a period unrelated to the harmonics (4.7 d against 1.65, 3.3 and 6.6 d)
    detectable_v51, detectable_v5, fails = 0, 0, 0
    for seed in range(6):
        lc = _lc(100 + seed, trend=(4.7, 1000e-6), sigma=1000e-6, depth=300e-6)
        cand = _cand(depth=300e-6)
        new = v51.check_sinusoid(lc, cand, SP, CP, seed=3)
        old = v5.check_sinusoid(lc, cand, SP, seed=3)
        fails += new.status is TestStatus.FAIL
        blocks = [b for b in new.sensitivity.values() if "detectable" in b]
        detectable_v51 += all(b["detectable"] for b in blocks)
        detectable_v5 += bool(old.sensitivity["main"]["detectable"])
        assert new.metrics["extra_frequencies"], "the trend is modelled as an extra frequency"
    assert fails == 0
    assert detectable_v51 == 6
    assert detectable_v5 == 0


def test_variability_within_one_over_the_span_of_a_harmonic_is_carried_by_that_harmonic():
    # a trend at 6.1 d is within 1 / T_span of 2P = 6.6 d: it is not an extra frequency, so the
    # 2P harmonic carries it and the warning says so (variability at a harmonic is flagged)
    lc = _lc(100, trend=(6.1, 2000e-6), sigma=2000e-6, depth=700e-6)
    result = v51.check_sinusoid(lc, _cand(depth=700e-6), SP, CP, seed=3)
    assert result.status is TestStatus.FAIL
    assert "2P" in result.message


def test_variability_near_a_tested_harmonic_is_not_removed_as_an_extra_frequency():
    period = 3.3
    lc = _lc(7, depth=0.0, sinus=(period * 1.002, 3000e-6))
    cand = _cand(period=period, depth=2000e-6)
    result = v51.check_sinusoid(lc, cand, SP, CP, seed=3)
    span = float(lc.time.max() - lc.time.min())
    for row in result.metrics["extra_frequencies"]:
        assert abs(row["frequency_per_day"] - 1.0 / period) > 1.0 / span
    assert result.status is TestStatus.FAIL


def test_a_box_only_curve_has_no_flagged_harmonic_and_passes_with_sensitivity():
    lc = _lc(11)
    result = v51.check_sinusoid(lc, _cand(), SP, CP, seed=3)
    assert result.status is TestStatus.PASS
    assert enforce_sensitivity([result], TESS_REGISTRY_V3)[0].status is TestStatus.PASS


# --- the engine on the per-harmonic blocks (row 3.8 (b); sabotage) --------------------------


def test_a_not_applicable_harmonic_never_makes_a_pass_on_its_own():
    lc = _lc(11)
    result = v51.check_sinusoid(lc, _cand(), SP, CP, seed=3)
    blocks = dict(result.sensitivity)
    blocks["P/2"] = {"applicable": False, "reason": "forced"}
    forced = result.__class__(**{**result.__dict__, "sensitivity": blocks})
    out = enforce_sensitivity([forced], TESS_REGISTRY_V3)[0]
    assert out.status is TestStatus.INCONCLUSIVE


def test_an_undetectable_applicable_harmonic_refuses_the_pass():
    lc = _lc(11, sigma=20000e-6)
    result = v51.check_sinusoid(lc, _cand(), SP, CP, seed=3)
    assert result.status is TestStatus.PASS
    assert enforce_sensitivity([result], TESS_REGISTRY_V3)[0].status is TestStatus.INCONCLUSIVE
