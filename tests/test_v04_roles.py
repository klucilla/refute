"""v0.4 WP1 (issue #174): test roles, the temporal diagnostic, the method status and case
completeness. Cases 1.1 to 1.13 of docs/plans/v0.4-acceptance.md. Synthetic data only."""

from __future__ import annotations

import copy
import json

import pytest
from pydantic import ValidationError

from conftest import target_entry
from refute.core.verdict import (
    NOT_RUN_AT_STAGE,
    Severity,
    TestResult,
    TestStatus,
    aggregate_roles,
    defer_tests,
    diagnostic_state,
)
from refute.packs.tess.exporter import _fields
from refute.packs.tess.params import DiscoveryParams, TessTestPlan
from refute.packs.tess.pipeline import (
    build_result,
    conclude_analysis,
    expected_tests,
)
from refute.packs.tess.report import render_report
from refute.packs.tess.synthetic import (
    discovery_plan_dict,
    discovery_section,
    fast_plan_dict,
    scenario_data,
)

DECISIVE = [
    "snr",
    "odd_even",
    "secondary_eclipse",
    "plausibility",
    "centroid_shift",
    "aperture_depth",
    "nearby_contamination",
    "period_alias",
    "systematics",
]
ROLES = {**{n: "decisive" for n in DECISIVE}, "holdout_by_year": "diagnostic"}


def _result(name, status=TestStatus.PASS, severity=Severity.FATAL, coverage=5):
    if name == "snr":
        severity = Severity.GATE
    return TestResult(name, status, severity, f"{name} {status.value}", coverage=coverage)


def _decisive_pass():
    return [_result(n) for n in DECISIVE]


def _agg(results):
    return aggregate_roles(results, ROLES, DECISIVE, ["holdout_by_year"])


# --- unit cases on the aggregation ------------------------------------------------------------


def test_1_1_a_diagnostic_fail_never_changes_the_verdict():
    out = _agg([*_decisive_pass(), _result("holdout_by_year", TestStatus.FAIL)])
    assert out.verdict.value == "SURVIVED"
    assert diagnostic_state(out.diagnostics["holdout_by_year"]) == "fail"
    assert all(r.name != "holdout_by_year" for r in out.decisive)


@pytest.mark.parametrize(
    ("status", "state"), [(TestStatus.PASS, "pass"), (TestStatus.INCONCLUSIVE, "inconclusive")]
)
def test_1_2_the_verdict_is_the_same_for_every_diagnostic_state(status, state):
    out = _agg([*_decisive_pass(), _result("holdout_by_year", status)])
    assert out.verdict.value == "SURVIVED"
    assert diagnostic_state(out.diagnostics["holdout_by_year"]) == state


def test_1_2_not_run_diagnostic_keeps_the_verdict():
    out = _agg(_decisive_pass())
    assert out.verdict.value == "SURVIVED"
    assert diagnostic_state(out.diagnostics["holdout_by_year"]) == "not_run"


def test_1_3_a_zero_coverage_diagnostic_pass_is_inconclusive():
    out = _agg([*_decisive_pass(), _result("holdout_by_year", TestStatus.PASS, coverage=0)])
    assert out.diagnostics["holdout_by_year"].status is TestStatus.INCONCLUSIVE
    assert out.verdict.value == "SURVIVED"


def test_1_4_a_missing_required_diagnostic_makes_the_case_incomplete():
    out = _agg(_decisive_pass())
    assert out.missing_diagnostics == ["holdout_by_year"]
    assert out.diagnostics_complete is False
    assert out.verdict.value == "SURVIVED"


def test_1_5_a_decisive_fatal_fail_refutes():
    results = _decisive_pass()
    results[1] = _result("odd_even", TestStatus.FAIL, Severity.FATAL)
    out = _agg([*results, _result("holdout_by_year")])
    assert out.verdict.value == "REFUTED"
    assert "odd_even" in out.reason


def test_a_missing_decisive_test_is_inconclusive():
    results = [r for r in _decisive_pass() if r.name != "period_alias"]
    out = _agg([*results, _result("holdout_by_year")])
    assert out.verdict.value == "INCONCLUSIVE"
    assert "period_alias" in out.reason


def test_results_without_a_role_are_refused():
    with pytest.raises(ValueError, match="without a declared role"):
        aggregate_roles([_result("snr")], {}, [], [])


@pytest.mark.parametrize(
    ("severity", "verdict"), [(Severity.WARNING, "WEAKENED"), (Severity.FATAL, "REFUTED")]
)
def test_1_13_the_emitted_severity_decides(severity, verdict):
    results = _decisive_pass()
    results[2] = _result("secondary_eclipse", TestStatus.FAIL, severity)
    out = _agg([*results, _result("holdout_by_year")])
    assert out.verdict.value == verdict


def test_1_7_deferred_tests_are_inconclusive_with_zero_coverage():
    results, deferred = defer_tests(
        [_result("snr"), _result("centroid_shift"), _result("aperture_depth")],
        {"centroid_shift": 2, "aperture_depth": 2},
        1,
    )
    assert deferred == ["centroid_shift", "aperture_depth"]
    for r in results[1:]:
        assert r.status is TestStatus.INCONCLUSIVE
        assert r.coverage == 0
        assert r.message.startswith(NOT_RUN_AT_STAGE)
        assert r.severity is Severity.FATAL
    assert results[0].status is TestStatus.PASS


# --- 1.10: the claim's roles are checked at load time ---------------------------------------


def _section(**change):
    section = copy.deepcopy(discovery_section())
    section.update(change)
    return section


@pytest.mark.parametrize(
    ("change", "match"),
    [
        ({"diagnostic": ["holdout_by_year", "snr"]}, "both decisive and diagnostic"),
        ({"decisive": [*DECISIVE, "snr"]}, "twice"),
        ({"required_diagnostics": ["period_alias"]}, "role 'diagnostic'"),
        ({"required_diagnostics": ["not_a_test"]}, "not among the claim's tests"),
        ({"decisive": [*DECISIVE[1:]], "diagnostic": ["holdout_by_year", "snr"]}, "gate"),
        ({"stages": {"snr": 2}}, "stage 1"),
        ({"stages": {"eb_catalog": 2}}, "without a role"),
        ({"decisive": [*DECISIVE, "made_up"]}, "unknown tests"),
        ({"inputs": {"protocol": "ABC"}}, "SHA-256"),
        ({"method_status": "validated"}, "method_status"),
    ],
)
def test_1_10_inconsistent_roles_are_refused(change, match):
    with pytest.raises(ValidationError, match=match):
        DiscoveryParams.model_validate(_section(**change))


# --- integration through conclude_analysis and build_result (1.6 to 1.9, 1.11, 1.12) ---------


def _plan(stage_plan=True):
    return TessTestPlan.model_validate(discovery_plan_dict() if stage_plan else fast_plan_dict())


def _conclude(analysis, plan, stage=None):
    return conclude_analysis(
        analysis.search,
        analysis.flattened_search,
        analysis.gauntlet,
        analysis.holdout,
        False,
        plan=plan,
        stage=stage,
    )


def _record(name, analysis, plan):
    target = target_entry(1, "exploration", None, name=name)
    return build_result(target, scenario_data(name), plan, analysis, {})


def test_1_12_the_holdout_reaches_the_temporal_diagnostic_and_never_the_verdict(
    scenario_results,
):
    # "vanishing": the transit is only in 2018, so the legacy verdict is REFUTED by the holdout.
    legacy = scenario_results["vanishing"]
    assert legacy.verdict == "REFUTED" and "holdout_by_year" in legacy.verdict_reason, (
        "premise: the legacy verdict is refuted by the holdout"
    )
    roles = _conclude(legacy, _plan(), stage=2)
    assert "holdout_by_year" not in roles.verdict_reason
    assert roles.verdict != "REFUTED" or "holdout_by_year" not in roles.verdict_reason
    assert roles.roles.diagnostics["holdout_by_year"].status is TestStatus.FAIL
    assert all(t.name != "holdout_by_year" for t in roles.roles.decisive)
    record = _record("vanishing", roles, _plan())
    assert record["temporal_diagnostic"]["state"] == "fail"
    assert record["expected_tests"] == [n for n in expected_tests(False) if n != "holdout_by_year"]
    assert record["required_diagnostics"] == ["holdout_by_year"]
    assert record["discovery"]["diagnostics_complete"] is True


def test_1_7_stage_1_defers_the_pixel_tests_through_the_pipeline(scenario_results):
    out = _conclude(scenario_results["planet"], _plan(), stage=1)
    tests = {t.name: t for t in out.tests}
    for name in ("centroid_shift", "aperture_depth"):
        assert tests[name].status is TestStatus.INCONCLUSIVE
        assert tests[name].coverage == 0
        assert NOT_RUN_AT_STAGE in tests[name].message
    assert out.verdict == "INCONCLUSIVE"
    assert "centroid_shift" in out.verdict_reason
    assert out.deferred == ["centroid_shift", "aperture_depth"]


def test_1_8_a_stage_1_fatal_fail_refutes(scenario_results):
    legacy = scenario_results["eb_odd_even"]
    assert any(t.name == "odd_even" and t.status is TestStatus.FAIL for t in legacy.tests), (
        "premise: odd_even fails on the eb_odd_even scenario"
    )
    out = _conclude(legacy, _plan(), stage=1)
    assert out.verdict == "REFUTED"


def test_1_6_a_plan_without_roles_keeps_todays_verdict_and_record(scenario_results):
    for name in ("planet", "vanishing", "eb_odd_even", "noise"):
        legacy = scenario_results[name]
        again = _conclude(legacy, _plan(stage_plan=False))
        assert (again.verdict, again.verdict_reason) == (legacy.verdict, legacy.verdict_reason)
        assert again.roles is None
        plan = _plan(stage_plan=False)
        a = json.dumps(_record(name, legacy, plan), sort_keys=True, default=str)
        b = json.dumps(_record(name, again, plan), sort_keys=True, default=str)
        assert a == b
        for key in ("method_status", "temporal_diagnostic", "discovery", "required_diagnostics"):
            assert key not in _record(name, legacy, plan)


def test_1_11_a_plan_without_discovery_dumps_as_before():
    dumped = TessTestPlan.model_validate(fast_plan_dict()).model_dump(mode="json")
    assert set(dumped) == {"data", "detrend", "search", "gauntlet"}
    with_section = TessTestPlan.model_validate(discovery_plan_dict()).model_dump(mode="json")
    assert set(with_section) == {"data", "detrend", "search", "gauntlet", "discovery"}


def test_1_9_method_status_in_the_record_the_report_and_the_exporter(scenario_results):
    plan = _plan()
    out = _conclude(scenario_results["planet"], plan, stage=2)
    record = _record("planet", out, plan)
    assert record["method_status"] == "not_validated"
    assert record["method_status_reference"] == "docs/validation/v0.2.1/closing-2026-10-27.md"
    report = render_report(record, {"claim_kind": "discover"})
    assert "not_validated" in report and "Meaning of SURVIVED" in report
    fields = _fields(record)
    assert fields["method_status"] == "not_validated"
    assert fields["temporal_diagnostic"] == record["temporal_diagnostic"]["state"]
    assert "not validated" in fields["notes"]


def test_1_9_an_error_record_of_a_discover_claim_has_the_fields():
    from refute.packs.tess.pipeline import TessAnalyzer

    record = TessAnalyzer().error_result(
        target_entry(1, "exploration", None), "boom", {"claim_kind": "discover", "stage": 1}
    )
    assert record["method_status"] == "not_validated"
    assert record["temporal_diagnostic"]["state"] == "not_run"
    assert "method_status" not in TessAnalyzer().error_result(
        target_entry(1, "planet", 3.7), "boom", {"claim_kind": "replicate"}
    )
