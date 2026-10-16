"""The procedural coverage rule for a proven absence (decided by the maintainer on
2026-10-16): a gate failed because a declared artifact answered HTTP 404 or 410 in all of
the N attempts reaches NOT_REPRODUCIBLE, although it examined no example; any other zero
coverage stays INCONCLUSIVE."""

import pytest

from refute.core.paper import (
    ABSENT_HTTP_STATUSES,
    FailureCause,
    GateFailure,
    aggregate_claim,
    proven_absence,
)
from refute.core.verdict import PaperVerdict, Severity, TestResult, TestStatus

ABSENT = GateFailure(FailureCause.ARTIFACT_ABSENT, 3, 3)


def gate(status=TestStatus.FAIL, coverage=0, statuses=(404, 410, 404), name="data_present"):
    metrics = {} if statuses is None else {ABSENT_HTTP_STATUSES: list(statuses)}
    return TestResult(name, status, Severity.GATE, "fetch", metrics=metrics, coverage=coverage)


def verdict(result, failure):
    base = [TestResult("environment_build", TestStatus.PASS, Severity.GATE, "ok", coverage=1)]
    if result.name != "environment_build":
        base.append(result)
    else:
        base = [result]
    return aggregate_claim(
        base, [], [], metric_recompute_applies=False, failures={result.name: failure}
    ).verdict


def test_a_proven_absence_is_not_reproducible_with_zero_coverage():
    assert proven_absence(gate(), ABSENT)
    assert verdict(gate(), ABSENT) is PaperVerdict.NOT_REPRODUCIBLE
    # also with no declared coverage, and on another gate (an absent artifact applies to
    # every gate of the base reproduction)
    assert verdict(gate(coverage=None), ABSENT) is PaperVerdict.NOT_REPRODUCIBLE
    assert verdict(gate(name="environment_build"), ABSENT) is PaperVerdict.NOT_REPRODUCIBLE


@pytest.mark.parametrize(
    ("result", "failure", "why"),
    [
        (gate(statuses=None), ABSENT, "no recorded statuses"),
        (gate(statuses=(404, 503, 404)), ABSENT, "one attempt was not an absence"),
        (gate(statuses=(404, 404)), ABSENT, "fewer statuses than attempts"),
        (gate(statuses=(404, 404, True)), ABSENT, "a status that is not an int"),
        (gate(), GateFailure(FailureCause.ARTIFACT_ABSENT, 2, 3), "incomplete attempts"),
        (gate(), GateFailure(FailureCause.ARTIFACT_ABSENT, 0, 0), "no attempt required"),
        (gate(), GateFailure(FailureCause.TRANSIENT_NETWORK), "another cause"),
        (gate(), GateFailure(FailureCause.UNDETERMINED), "an undetermined cause"),
        (gate(), None, "no recorded cause"),
    ],
)
def test_any_other_zero_coverage_stays_inconclusive(result, failure, why):
    assert not proven_absence(result, failure), why
    assert verdict(result, failure) is PaperVerdict.INCONCLUSIVE, why


GATES = ("environment_build", "data_present", "run_completed", "metric_extracted")


def gate_verdict(name, result, failure):
    """The verdict with every gate before ``name`` passing and ``result`` in its place."""
    base = []
    for g in GATES:
        if g == name:
            base.append(result)
            break
        base.append(TestResult(g, TestStatus.PASS, Severity.GATE, "ok", coverage=1))
    return aggregate_claim(base, [], [], metric_recompute_applies=False, failures={name: failure})


@pytest.mark.parametrize("name", GATES)
@pytest.mark.parametrize("statuses", [None, (404, 503, 404), (404, 404), ("404", 404, 404)])
def test_an_absence_without_its_evidence_is_inconclusive_also_with_coverage(name, statuses):
    """Codex review of #106: with a positive coverage the zero-coverage rule does not
    apply, and the attribution itself requires the HTTP evidence of every attempt."""
    result = gate(coverage=5, statuses=statuses, name=name)
    got = gate_verdict(name, result, ABSENT)
    assert got.verdict is PaperVerdict.INCONCLUSIVE, got.reason
    assert "HTTP 404 or 410" in got.reason


@pytest.mark.parametrize("name", GATES)
def test_an_absence_with_its_evidence_is_not_reproducible_on_every_gate(name):
    for coverage in (0, 5):
        got = gate_verdict(name, gate(coverage=coverage, name=name), ABSENT)
        assert got.verdict is PaperVerdict.NOT_REPRODUCIBLE, (coverage, got.reason)


def test_a_pass_without_coverage_is_never_a_pass():
    passed = gate(status=TestStatus.PASS)
    assert not proven_absence(passed, ABSENT)
    assert verdict(passed, ABSENT) is PaperVerdict.INCONCLUSIVE


def test_an_absence_on_a_non_gate_check_is_not_this_rule():
    """The rule is for the gates of the base reproduction only."""
    fatal = TestResult(
        "base_reproduction",
        TestStatus.FAIL,
        Severity.FATAL,
        "x",
        metrics={ABSENT_HTTP_STATUSES: [404, 404, 404]},
        coverage=0,
    )
    gates = [
        TestResult(g, TestStatus.PASS, Severity.GATE, "ok", coverage=1)
        for g in ("environment_build", "data_present", "run_completed", "metric_extracted")
    ]
    got = aggregate_claim([*gates, fatal], [], [], metric_recompute_applies=False)
    assert got.verdict is PaperVerdict.INCONCLUSIVE
