"""v0.5.1 WP4: the INCONCLUSIVE classes (docs/plans/v0.5.1-acceptance.md, rows 4.1 to 4.3).

The class rule (``refute.core.inconclusive``), the TESS table of the shared v0.4 and v0.5
functions (``refute.packs.tess.inconclusive``), and the reporting of version-3 claims in
``verdict.json``, ``report.md`` and ``case.json``. Synthetic data only."""

from __future__ import annotations

import copy
import json
import re
from dataclasses import replace
from pathlib import Path

import pytest

from refute.core import inconclusive as inc
from refute.core.io import dumps_json
from refute.core.sensitivity import enforce_sensitivity
from refute.core.verdict import Severity, TestResult, TestStatus, enforce_coverage
from refute.packs.tess.discover.case import build_case
from refute.packs.tess.inconclusive import TESS_TABLE
from refute.packs.tess.params import TessTestPlan
from refute.packs.tess.pipeline import (
    TessAnalyzer,
    analyze_data,
    build_result,
    conclude_analysis,
)
from refute.packs.tess.report import render_report
from refute.packs.tess.synthetic import (
    discovery_v05_plan_dict,
    discovery_v051_plan_dict,
    scenario_data,
)

SRC = Path(__file__).resolve().parents[1] / "src" / "refute" / "packs" / "tess"
TARGET = {"key": "TIC-1", "tic_id": 1, "kind": "exploration", "name": "synthetic", "published": {}}
CONTEXT = {"claim_id": "synthetic", "claim_kind": "discover", "hypothesis": "h"}


def _inc(name="t", message="m", coverage=None, **metrics):
    return TestResult(name, TestStatus.INCONCLUSIVE, Severity.FATAL, message,
                      metrics=metrics, coverage=coverage)  # fmt: skip


# --- the class rule ---------------------------------------------------------------------------


def test_the_order_of_the_class_rule():
    explicit = _inc(message="PASS refused: x", inconclusive_class="outside_domain")
    assert inc.classify(explicit, TESS_TABLE, deferred=True) == ("not_enough_data", "stage")
    assert inc.classify(explicit, TESS_TABLE) == ("outside_domain", "test")
    passed = TestResult("t", TestStatus.PASS, Severity.FATAL, "ok", coverage=0)
    (refused,) = enforce_coverage([passed])
    assert inc.classify(refused, TESS_TABLE) == ("not_enough_data", "coverage_rule")
    passed = TestResult("t", TestStatus.PASS, Severity.FATAL, "ok", coverage=3)
    (refused,) = enforce_sensitivity([passed], {"t": {"main": "rule"}})
    assert refused.status is TestStatus.INCONCLUSIVE
    assert inc.classify(refused, TESS_TABLE) == ("insufficient_sensitivity", "sensitivity_rule")
    tic = _inc("plausibility", "no TIC stellar radius available")
    assert inc.classify(tic, TESS_TABLE) == ("missing_input", "table")
    assert inc.classify(_inc("x", "unknown", 0), TESS_TABLE) == ("not_enough_data", "fallback")
    assert inc.classify(_inc("x", "unknown", 5), TESS_TABLE) == (
        "insufficient_sensitivity", "fallback")  # fmt: skip


def test_an_unknown_explicit_class_is_a_code_error():
    with pytest.raises(ValueError, match="unknown INCONCLUSIVE class"):
        inc.classify(_inc(inconclusive_class="probably_fine"), TESS_TABLE)


def test_annotate_touches_only_inconclusive_results_and_copies_metrics():
    ok = TestResult("a", TestStatus.PASS, Severity.FATAL, "ok", coverage=1)
    bad = _inc("b", "no candidate")
    out = inc.annotate([ok, bad], TESS_TABLE)
    assert out[0] is ok
    assert out[1].metrics == {"inconclusive_class": "not_enough_data",
                              "inconclusive_class_source": "table"}  # fmt: skip
    assert bad.metrics == {}


def test_the_verdict_class_follows_the_priority():
    tests = inc.annotate(
        [_inc("a", inconclusive_class="insufficient_sensitivity"),
         _inc("b", inconclusive_class="not_enough_data")], TESS_TABLE)  # fmt: skip
    assert inc.verdict_class(tests) == "not_enough_data"
    tests.append(inc.annotate([_inc("c", inconclusive_class="missing_input")], TESS_TABLE)[0])
    assert inc.verdict_class(tests) == "missing_input"
    assert inc.verdict_class([]) is None
    assert inc.with_classes("could not be decided: a, c", tests) == (
        "could not be decided: a (insufficient_sensitivity), c (missing_input)")  # fmt: skip
    assert inc.with_classes("fatal failure in: a", tests) == "fatal failure in: a"


# --- the TESS table ---------------------------------------------------------------------------

# every INCONCLUSIVE message of the shared v0.4 and v0.5 functions a version-3 claim can reach
# (their leading literal text), with the class the table must give
SHARED_MESSAGES = [
    ("odd_even", "no candidate", "not_enough_data"),
    ("snr", "no in-transit cadence: the corrected SNR cannot be computed", "not_enough_data"),
    (
        "snr",
        "noise model undetermined: the corrected SNR cannot be computed",
        "insufficient_sensitivity",
    ),
    ("secondary_eclipse", "no data covers phase 0.5", "not_enough_data"),
    ("secondary_eclipse", "no primary events measured", "not_enough_data"),
    ("plausibility", "TIC row has disposition SPLIT (duplicate_id none): ...", "missing_input"),
    ("plausibility", "no TIC stellar radius available", "missing_input"),
    (
        "plausibility",
        "TIC stellar radius has no uncertainty; reliability cannot be assessed",
        "missing_input",
    ),
    ("plausibility", "TIC stellar radius too uncertain (0.40 > 0.3)", "insufficient_sensitivity"),
    (
        "plausibility",
        "companion radius is plausible, but no stellar mass to check the duration",
        "missing_input",
    ),
    ("centroid_shift", "no target pixel data", "missing_input"),
    ("centroid_shift", "qualification failed: 2 of 3 sector(s) do not qualify", "not_enough_data"),
    ("centroid_shift", "single sector", "not_enough_data"),
    ("centroid_shift", "no qualified sector", "not_enough_data"),
    ("centroid_shift", "sectors disagree (heterogeneity p = 0.001)", "insufficient_sensitivity"),
    ("nearby_contamination", "no TIC neighbor query available", "missing_input"),
    ("nearby_contamination", "no TIC magnitude for the target", "missing_input"),
    ("nearby_contamination", "crowding not checked: no CROWDSAP value (...)", "missing_input"),
    ("period_alias", "noise_undetermined: no sector has enough bins", "not_enough_data"),
    ("period_alias", "too_few_cadences: only 10 in-transit cadences", "not_enough_data"),
    ("period_alias", "only 10 in-transit cadences (< 30, one transit's worth)", "not_enough_data"),
    ("period_alias", "singular_design: the design is singular", "insufficient_sensitivity"),
    ("period_alias", "non_finite_statistic: ...", "insufficient_sensitivity"),
    ("period_alias", "box_depth_not_positive: ...", "insufficient_sensitivity"),
    ("period_alias", "box_gain_small_dip_not_explained: ...", "insufficient_sensitivity"),
    ("eb_catalog", "no target coordinates for the catalog cross-match", "missing_input"),
    ("eb_catalog", "no record of which catalogs were scanned", "missing_input"),
    (
        "eb_catalog",
        "the catalogs were not scanned around TIC-1 (not in the extraction)",
        "missing_input",
    ),
    (
        "eb_catalog",
        "extraction radius 10 arcsec is smaller than the match radius 21 arcsec",
        "missing_input",
    ),
    ("single_event", "only 1 measured event(s)", "not_enough_data"),
    ("single_event", "the total SNR is not positive", "insufficient_sensitivity"),
    (
        "event_consistency",
        "only 1 measured event(s) (phase-0.5 windows excluded: ...)",
        "not_enough_data",
    ),
    ("edge_events", "no measured event", "not_enough_data"),
    ("edge_events", "every measured event is near a segment edge", "not_enough_data"),
    ("edge_events", "the events away from edges give SNR 3.1 < 7.1", "insufficient_sensitivity"),
    ("holdout_by_year", "data from 1 observing year(s); at least 2 are needed", "not_enough_data"),
    ("holdout_by_year", "no hidden year could be tested", "not_enough_data"),
    ("holdout_by_year", "necessary year(s) undecided: 2019 (x)", "not_enough_data"),
]


@pytest.mark.parametrize(("name", "message", "cls"), SHARED_MESSAGES)
def test_every_shared_inconclusive_message_matches_a_table_row(name, message, cls):
    assert inc.classify(_inc(name, message, 0), TESS_TABLE) == (cls, "table")


# the number of INCONCLUSIVE returns in each shared module when the table was written; a new one
# must be added to SHARED_MESSAGES and to the table before this number is updated
SHARED_SITES = {
    "battery.py": 14,
    "battery_v5.py": 11,
    "gauntlet.py": 7,
    "centroid_v5.py": 4,
    "ebcatalog.py": 6,
    "holdout.py": 15,
}


@pytest.mark.parametrize(("module", "count"), sorted(SHARED_SITES.items()))
def test_the_shared_modules_have_no_unlisted_inconclusive_return(module, count):
    text = (SRC / module).read_text(encoding="utf-8")
    found = len(re.findall(r"TestStatus\.INCONCLUSIVE|_inconclusive\(", text))
    assert found == count, f"{module}: update SHARED_MESSAGES and TESS_TABLE"


def test_every_table_class_is_known():
    assert {cls for _, _, cls in TESS_TABLE} <= set(inc.CLASSES)


# --- row 4.1: through the analyzer ------------------------------------------------------------


def _v3_plan(**v051):
    d = copy.deepcopy(discovery_v051_plan_dict())
    d["v051"] = dict(v051)
    return TessTestPlan.model_validate(d)


@pytest.fixture(scope="module")
def v3_run():
    # no auxiliary data (pixels, SAP): missing_input; no sinusoid harmonic in its domain:
    # outside_domain
    data = replace(scenario_data("planet_three_years"), aux=None)
    plan = _v3_plan(sinusoid_harmonic_max_period_days=0.01)
    analysis = analyze_data(data, plan, stage=2)
    return data, plan, analysis


def _outputs(data, plan, analysis):
    result = build_result(TARGET, data, plan, analysis, CONTEXT)
    case = build_case(result, TARGET, None, None)
    return result, render_report(result, CONTEXT), case


def test_4_1_every_inconclusive_of_a_version_3_claim_has_a_class(v3_run):
    data, plan, analysis = v3_run
    result, report, case = _outputs(data, plan, analysis)
    assert result["v05"]["discovery_version"] == 3
    inconclusive = [t for t in result["tests"] if t["status"] == "INCONCLUSIVE"]
    assert inconclusive
    for t in inconclusive:
        assert t["metrics"]["inconclusive_class"] in inc.CLASSES
        assert t["metrics"]["inconclusive_class_source"] != "fallback", t["name"]
        assert f"| {t['name']} | INCONCLUSIVE ({t['metrics']['inconclusive_class']}) |" in report
    classes = {t["name"]: t["metrics"]["inconclusive_class"] for t in inconclusive}
    assert classes["sinusoid"] == "outside_domain"
    assert classes["aperture_depth"] == "missing_input"
    assert classes["systematics"] == "missing_input"
    v051 = result["v051"]
    assert v051["inconclusive_classes"] == {
        name: {"class": cls, "source": next(
            t["metrics"]["inconclusive_class_source"] for t in inconclusive if t["name"] == name)}
        for name, cls in classes.items()
    }  # fmt: skip
    case_tests = {t["name"]: t for t in case["analyses"]["tests"]}
    for name, cls in classes.items():
        assert case_tests[name]["inconclusive_class"] == cls
    assert case["analyses"]["inconclusive_class"] == v051["inconclusive_class"]
    if result["verdict"] == "INCONCLUSIVE" and v051["inconclusive_condition"] is None:
        assert v051["inconclusive_class"] in inc.CLASSES
        assert "INCONCLUSIVE verdict: class" in report
        assert "(" in result["verdict_reason"]


def test_4_1_a_test_not_run_at_this_stage_is_not_enough_data(v3_run):
    data, plan, analysis = v3_run
    staged = conclude_analysis(analysis.search, analysis.flattened_search, analysis.gauntlet,
                               analysis.holdout, False, plan=plan, stage=1)  # fmt: skip
    assert staged.deferred
    result, report, case = _outputs(data, plan, staged)
    for name in staged.deferred:
        entry = result["v051"]["inconclusive_classes"][name]
        assert entry == {"class": "not_enough_data", "source": "stage"}


def test_4_1_insufficient_sensitivity_is_reported_in_the_three_outputs(v3_run):
    data, plan, analysis = v3_run
    refused = TestResult("duty_cycle", TestStatus.PASS, Severity.FATAL, "ok", coverage=1)
    (refused,) = enforce_sensitivity([refused], {"duty_cycle": {"main": "rule"}})
    tests = [t if t.name != "duty_cycle" else refused for t in analysis.gauntlet.tests]
    gauntlet = replace(analysis.gauntlet, tests=tests)
    again = conclude_analysis(analysis.search, analysis.flattened_search, gauntlet,
                              analysis.holdout, False, plan=plan, stage=2)  # fmt: skip
    result, report, case = _outputs(data, plan, again)
    entry = result["v051"]["inconclusive_classes"]["duty_cycle"]
    assert entry == {"class": "insufficient_sensitivity", "source": "sensitivity_rule"}
    assert "| duty_cycle | INCONCLUSIVE (insufficient_sensitivity) |" in report
    case_tests = {t["name"]: t for t in case["analyses"]["tests"]}
    assert case_tests["duty_cycle"]["inconclusive_class"] == "insufficient_sensitivity"


# Row 4.2's fixtures: the outputs of the code before WP4 (6f8d805), recorded by
# tests/fixtures/v051_wp4/make_fixtures.py on a synthetic claim (Codex's end-of-round review of
# round 4, objection 3). The analysis itself is compared differentially with the code of the v0.5.0
# calibration lock on the machine that runs the tests (tests/test_v051_wp5.py, row 5.2 (a), the
# synthetic discover plans included): recorded analysis bytes do not travel between machines
# (tests/baseline_code.py). These tests use what does travel: rendering recorded verdicts, and the
# error records.
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "v051_wp4"


def _fixture(name: str) -> str:
    return (FIXTURES / name).read_bytes().decode("utf-8")


@pytest.mark.parametrize("label", ["v04", "v05"])
def test_4_2_the_recorded_verdicts_render_the_same_report_and_case(label):
    # report.md and case.json are pure functions of verdict.json: the recorded verdict renders
    # the recorded bytes with the WP4 code
    result = json.loads(_fixture(f"verdict-{label}.json"))
    assert render_report(result, CONTEXT) == _fixture(f"report-{label}.md")
    assert dumps_json(build_case(result, TARGET, None, None)) == _fixture(f"case-{label}.json")


def test_4_2_an_earlier_error_record_keeps_its_bytes():
    plan = discovery_v05_plan_dict()
    error = TessAnalyzer().error_result(TARGET, "boom", CONTEXT, test_plan=plan)
    assert dumps_json(error) == _fixture("error-v05.json")
    assert dumps_json(TessAnalyzer().error_result(TARGET, "boom", CONTEXT)) == _fixture(
        "error-v05.json"
    )


def test_a_version_3_error_record_carries_its_condition():
    plan = _v3_plan().model_dump(mode="json")
    error = TessAnalyzer().error_result(TARGET, "boom", CONTEXT, test_plan=plan)
    assert error["verdict"] == "INCONCLUSIVE"
    assert error["v051"] == {"inconclusive_class": None, "inconclusive_condition": "analysis_error",
                             "inconclusive_classes": {}}  # fmt: skip
    fetch = TessAnalyzer().error_result(TARGET, "data fetch failed: x", CONTEXT, test_plan=plan)
    assert fetch["v051"]["inconclusive_condition"] == "data_fetch_failed"
    assert "INCONCLUSIVE verdict: condition `analysis_error`" in render_report(error, CONTEXT)
    case = build_case(error, TARGET, None, None)
    assert case["analyses"]["inconclusive_condition"] == "analysis_error"
    assert inc.tally([error])["inconclusive_by_condition"] == {"analysis_error": 1}


# --- row 4.3: the tallies ---------------------------------------------------------------------


def test_4_3_the_tallies_count_verdicts_classes_and_conditions_apart():
    def rec(verdict, cls=None, condition=None, tests=None):
        v051 = {"inconclusive_class": cls, "inconclusive_condition": condition}
        return {"verdict": verdict, "v051": {**v051, "inconclusive_classes": tests or {}}}

    records = [
        rec("SURVIVED"),
        rec("WEAKENED"),
        rec("REFUTED", tests={"a": {"class": "not_enough_data", "source": "table"}}),
        rec("INCONCLUSIVE", "missing_input",
            tests={"a": {"class": "missing_input", "source": "table"},
                   "b": {"class": "not_enough_data", "source": "fallback"}}),
        rec("INCONCLUSIVE", "insufficient_sensitivity"),
        rec("INCONCLUSIVE", condition="gate_not_passed"),
    ]  # fmt: skip
    t = inc.tally(records)
    assert t["verdicts"] == {"SURVIVED": 1, "WEAKENED": 1, "REFUTED": 1, "INCONCLUSIVE": 3}
    assert t["inconclusive_by_class"] == {"outside_domain": 0, "insufficient_sensitivity": 1,
                                          "missing_input": 1, "not_enough_data": 0}  # fmt: skip
    assert t["inconclusive_by_condition"] == {"gate_not_passed": 1}
    assert t["inconclusive_unclassified"] == 0
    assert t["inconclusive_tests_by_class"]["not_enough_data"] == 2
    assert t["tests_classified_by_fallback"] == 1
    assert sum(t["inconclusive_by_class"].values()) + sum(
        t["inconclusive_by_condition"].values()) == t["verdicts"]["INCONCLUSIVE"]  # fmt: skip
