"""v0.5 WP1 to WP3 in the TESS pack (docs/plans/v0.5-acceptance.md): the claim schema, the
registry, the sensitivity blocks and the v0.5 tests. Mechanism cases on synthetic data; the
rate cases of the acceptance (200 trials on acceptance seeds) run in the acceptance scripts."""

from __future__ import annotations

import math

import numpy as np
import pytest
from pydantic import ValidationError

from refute.core.chi2 import chi2_isf, chi2_sf, ncx2_sf
from refute.core.sensitivity import enforce_sensitivity
from refute.core.verdict import Severity, TestStatus
from refute.packs.tess import battery_v5 as v5
from refute.packs.tess.events import EventDepths
from refute.packs.tess.params import SecondaryParams, StrongerParams, TessTestPlan
from refute.packs.tess.pipeline import analyze_data, expected_tests
from refute.packs.tess.power import TESS_REGISTRY
from refute.packs.tess.synthetic import (
    discovery_plan_dict,
    discovery_v05_plan_dict,
    fast_plan_dict,
    scenario_data,
)
from refute.packs.tess.types import Candidate

SP = StrongerParams()


def _events(depths, errors, centers=None):
    n = len(depths)
    epochs = np.arange(n)
    centers = np.asarray(centers if centers is not None else 1000.0 + 3.0 * epochs, dtype=float)
    return EventDepths(
        epochs, centers, np.asarray(depths, float), np.asarray(errors, float), np.full(n, 60)
    )


def _candidate(period=3.0, duration=0.1, depth=1e-3, t0=1000.0):
    return Candidate(
        period=period,
        t0=t0,
        duration=duration,
        depth=depth,
        depth_err=1e-4,
        snr=10.0,
        log_likelihood=0.0,
        sde=10.0,
        n_transits=5,
    )


# --- the chi-square helpers (exact references) --------------------------------------------


def test_chi2_tails_match_exact_values():
    # dof 2: sf(x) = exp(-x/2); dof 1: sf(9) = P(|Z| > 3)
    assert chi2_sf(5.991464547107979, 2) == pytest.approx(0.05, rel=1e-10)
    assert chi2_sf(9.0, 1) == pytest.approx(0.0026997960632601866, rel=1e-9)
    assert chi2_isf(0.05, 2) == pytest.approx(5.991464547107979, rel=1e-9)
    assert chi2_isf(0.00135, 5) > chi2_isf(0.05, 5)


@pytest.mark.parametrize("lam", [0.5, 7.849, 30.0, 400.0])
def test_noncentral_tail_matches_the_dof_1_closed_form(lam):
    # dof 1: P(X > x) = Phi(sqrt(lam) - sqrt(x)) + Phi(-sqrt(lam) - sqrt(x))
    x = 3.841458820694124
    phi = lambda z: 0.5 * math.erfc(-z / math.sqrt(2.0))  # noqa: E731
    exact = phi(math.sqrt(lam) - math.sqrt(x)) + phi(-math.sqrt(lam) - math.sqrt(x))
    assert ncx2_sf(x, 1, lam) == pytest.approx(exact, rel=1e-8, abs=1e-12)


# --- the claim schema (case 1.5; #30) -----------------------------------------------------


def test_a_plan_without_the_v05_section_dumps_as_before():
    for plan in (fast_plan_dict(), discovery_plan_dict()):
        dumped = TessTestPlan.model_validate(plan).model_dump(mode="json")
        assert "stronger" not in dumped
    v04 = TessTestPlan.model_validate(discovery_plan_dict()).model_dump(mode="json")
    assert v04["discovery"]["version"] == 1


def test_version_2_and_the_section_go_together():
    with pytest.raises(ValidationError, match="stronger"):
        TessTestPlan.model_validate({**discovery_v05_plan_dict(), "stronger": None})
    with pytest.raises(ValidationError, match="stronger"):
        TessTestPlan.model_validate({**discovery_plan_dict(), "stronger": {}})
    with pytest.raises(ValidationError, match="stronger"):
        TessTestPlan.model_validate({**fast_plan_dict(), "stronger": {}})
    assert TessTestPlan.model_validate(discovery_v05_plan_dict()).v05


def test_a_decisive_test_without_a_registered_rule_is_refused_at_load():
    plan = discovery_v05_plan_dict()
    plan["discovery"]["diagnostic"] = []
    plan["discovery"]["required_diagnostics"] = []
    plan["discovery"]["decisive"].append("holdout_by_year")  # no rule in v0.5
    with pytest.raises(ValidationError, match="holdout_by_year"):
        TessTestPlan.model_validate(plan)


def test_a_v04_claim_cannot_name_a_v05_test():
    plan = discovery_plan_dict()
    plan["discovery"]["decisive"].append("single_event")
    with pytest.raises(ValidationError, match="unknown tests"):
        TessTestPlan.model_validate(plan)


def test_every_registered_test_has_a_known_kind():
    from refute.core.sensitivity import registry_problems

    assert registry_problems(list(TESS_REGISTRY), TESS_REGISTRY, exempt=[]) == []


def test_the_v05_tests_are_expected_only_in_a_v05_claim():
    assert "single_event" not in expected_tests(False)
    assert "single_event" in expected_tests(False, True)


# --- single_event and event_consistency (WP2) ---------------------------------------------


def test_equal_events_pass_single_event_with_sensitivity():
    result = v5.check_single_event(_events([1e-3] * 6, [2e-4] * 6), SP, seed=1)
    assert result.status is TestStatus.PASS
    assert result.sensitivity["main"]["detectable"] is True
    (kept,) = enforce_sensitivity([result], TESS_REGISTRY)
    assert kept.status is TestStatus.PASS


def test_one_dominant_event_fails_single_event():
    result = v5.check_single_event(_events([3e-3, 0, 0, 0, 0, 0], [2e-4] * 6), SP, seed=1)
    assert result.status is TestStatus.FAIL
    assert result.severity is Severity.FATAL


@pytest.mark.parametrize("n", [0, 1, 2])
def test_too_few_events_are_inconclusive(n):
    events = _events([1e-3] * n, [2e-4] * n)
    assert v5.check_single_event(events, SP, seed=1).status is TestStatus.INCONCLUSIVE
    assert v5.check_event_consistency(events, SP).status is TestStatus.INCONCLUSIVE


def test_weak_events_cannot_pass_single_event():
    # 3 events at SNR 0.7 each: the alternative (one event holding a total SNR of 1.2) is not
    # detectable, so the PASS is refused
    result = v5.check_single_event(_events([1e-4] * 3, [1.4e-4] * 3), SP, seed=1)
    assert result.sensitivity["main"]["detectable"] is False
    (out,) = enforce_sensitivity([result], TESS_REGISTRY)
    assert out.status is TestStatus.INCONCLUSIVE


def test_a_deviant_event_fails_event_consistency():
    events = _events([1e-3, 1e-3, 1e-3, 1e-3, 1e-3, 3e-3], [1e-4] * 6)
    result = v5.check_event_consistency(events, SP)
    assert result.status is TestStatus.FAIL
    assert result.sensitivity["main"]["detectable"] is True


def test_consistent_events_pass_event_consistency():
    rng = np.random.default_rng(5)
    depths = 1e-3 + 1e-4 * rng.standard_normal(8)
    result = v5.check_event_consistency(_events(depths, [1e-4] * 8), SP)
    assert result.status is TestStatus.PASS


# --- edge_events (WP2) --------------------------------------------------------------------


def test_events_away_from_edges_pass_with_the_comparison_not_applicable():
    time = np.arange(0.0, 26.0, 0.0014)
    events = _events([1e-3] * 4, [1e-4] * 4, centers=[5.0, 8.0, 11.0, 17.0])
    result = v5.check_edge_events(time, events, 0.1, 7.1, SP)
    assert result.status is TestStatus.PASS
    assert result.sensitivity["comparison"] == {
        "applicable": False,
        "reason": result.sensitivity["comparison"]["reason"],
    }
    (kept,) = enforce_sensitivity([result], TESS_REGISTRY)
    assert kept.status is TestStatus.PASS


def test_edge_events_with_a_different_depth_fail_as_a_warning():
    time = np.concatenate([np.arange(0.0, 13.0, 0.0014), np.arange(14.0, 27.0, 0.0014)])
    # 3 events near edges (0.05, 12.95, 14.05) deeper than the 3 others
    centers = [0.05, 12.95, 14.05, 4.0, 7.0, 20.0]
    events = _events([3e-3, 3e-3, 3e-3, 1e-3, 1e-3, 1e-3], [1e-4] * 6, centers=centers)
    result = v5.check_edge_events(time, events, 0.1, 7.1, SP)
    assert result.status is TestStatus.FAIL
    assert result.severity is Severity.WARNING


def test_when_the_other_events_are_too_weak_edge_events_is_inconclusive():
    time = np.concatenate([np.arange(0.0, 13.0, 0.0014), np.arange(14.0, 27.0, 0.0014)])
    centers = [0.05, 12.95, 14.05, 4.0]
    events = _events([3e-3, 3e-3, 3e-3, 1e-4], [1e-4] * 4, centers=centers)
    assert v5.check_edge_events(time, events, 0.1, 7.1, SP).status is TestStatus.INCONCLUSIVE


# --- secondary_eclipse, two-sided (WP3) ---------------------------------------------------


def test_a_brightening_at_phase_half_is_a_warning_never_a_pass():
    primary = _events([1e-3] * 6, [1e-4] * 6)
    secondary = _events([-5e-4] * 6, [1e-4] * 6)
    result = v5.check_secondary_two_sided(primary, secondary, SecondaryParams(), SP, seed=2)
    assert result.status is TestStatus.FAIL
    assert result.severity is Severity.WARNING
    assert "brightening" in result.message


def test_a_deep_secondary_dip_is_only_a_warning_in_v05():
    primary = _events([1e-3] * 6, [1e-4] * 6)
    secondary = _events([8e-4] * 6, [1e-4] * 6)
    result = v5.check_secondary_two_sided(primary, secondary, SecondaryParams(), SP, seed=2)
    assert result.status is TestStatus.FAIL
    assert result.severity is Severity.WARNING


def test_no_secondary_passes_with_both_blocks():
    primary = _events([1e-3] * 6, [1e-4] * 6)
    secondary = _events([0.0] * 6, [1e-4] * 6)
    result = v5.check_secondary_two_sided(primary, secondary, SecondaryParams(), SP, seed=2)
    assert result.status is TestStatus.PASS
    (kept,) = enforce_sensitivity([result], TESS_REGISTRY)
    assert kept.status is TestStatus.PASS


# --- duty_cycle and sinusoid (WP3) --------------------------------------------------------


def test_duty_cycle():
    assert v5.check_duty_cycle(_candidate(period=1.0, duration=0.6), SP).status is TestStatus.FAIL
    ok = v5.check_duty_cycle(_candidate(period=1.0, duration=0.3), SP)
    assert ok.status is TestStatus.PASS
    assert enforce_sensitivity([ok], TESS_REGISTRY)[0].status is TestStatus.PASS


def test_the_sinusoid_test_is_inconclusive_beyond_its_domain():
    data = scenario_data("noise")
    result = v5.check_sinusoid(data.lc, _candidate(period=12.0), SP, seed=3)
    assert result.status is TestStatus.INCONCLUSIVE
    assert "domain" in result.message


def test_a_strong_sinusoid_at_the_period_is_flagged():
    data = scenario_data("sinusoid")
    from refute.packs.tess.synthetic import SINUSOID_PERIOD

    cand = _candidate(period=SINUSOID_PERIOD, duration=0.12, depth=4e-3, t0=1325.3)
    result = v5.check_sinusoid(data.lc, cand, SP, seed=3)
    assert result.status is TestStatus.FAIL
    assert result.severity is Severity.WARNING
    assert "box_depth_after_sinusoid_ppm" in result.metrics


def test_a_box_only_curve_has_no_significant_sinusoid():
    data = scenario_data("planet")
    from refute.packs.tess.synthetic import PLANET

    cand = _candidate(
        period=PLANET.period, duration=PLANET.duration, depth=PLANET.depth, t0=PLANET.t0
    )
    result = v5.check_sinusoid(data.lc, cand, SP, seed=3)
    assert result.status is not TestStatus.FAIL


# --- the whole chain on a synthetic planet ------------------------------------------------


def test_a_v05_analysis_runs_every_test_and_applies_the_rule():
    data = scenario_data("planet")
    plan = TessTestPlan.model_validate(discovery_v05_plan_dict())
    analysis = analyze_data(data, plan, stage=1)
    names = {t.name for t in analysis.tests}
    for name in ("single_event", "event_consistency", "edge_events", "sinusoid", "duty_cycle"):
        assert name in names
    for test in analysis.tests:
        if test.status is TestStatus.PASS and test.severity is not Severity.GATE:
            assert test.sensitivity, f"{test.name} passed without a sensitivity block"
    assert analysis.verdict in {"SURVIVED", "WEAKENED", "REFUTED", "INCONCLUSIVE"}


def test_a_v04_analysis_is_unchanged_by_the_v05_code():
    data = scenario_data("planet")
    plan = TessTestPlan.model_validate(discovery_plan_dict())
    analysis = analyze_data(data, plan, stage=1)
    assert all(t.sensitivity is None for t in analysis.tests)
    assert {t.name for t in analysis.tests}.isdisjoint({"single_event", "sinusoid"})
