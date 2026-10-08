"""Domain-agnostic coverage rule (core): no check may PASS without having examined data.

These tests use only the core verdict model, with made-up test names, so they hold
for any domain pack, present or future (a paper-replication pack in v0.3 would hit
the same rule with zero claims extracted or zero tests collected)."""

from refute.core.verdict import (
    DiscoveryVerdict,
    Severity,
    TestResult,
    TestStatus,
    aggregate,
    enforce_coverage,
)


def t(name, status, severity, coverage, unit="items"):
    return TestResult(name, status, severity, "msg", coverage=coverage, coverage_unit=unit)


GATE_OK = t("gate", TestStatus.PASS, Severity.GATE, 10)


def test_pass_with_zero_coverage_becomes_inconclusive():
    (out,) = enforce_coverage([t("claims", TestStatus.PASS, Severity.FATAL, 0, "claims")])
    assert out.status is TestStatus.INCONCLUSIVE
    assert "examined 0 claims" in out.message


def test_pass_without_declared_coverage_becomes_inconclusive():
    (out,) = enforce_coverage([TestResult("x", TestStatus.PASS, Severity.FATAL, "ok")])
    assert out.status is TestStatus.INCONCLUSIVE
    assert "declared no coverage" in out.message


def test_pass_with_coverage_is_kept_and_other_statuses_are_untouched():
    kept = t("datasets", TestStatus.PASS, Severity.FATAL, 3)
    failed = t("split", TestStatus.FAIL, Severity.FATAL, 0)
    unknown = t("seed", TestStatus.INCONCLUSIVE, Severity.WARNING, 0)
    assert enforce_coverage([kept, failed, unknown]) == [kept, failed, unknown]


def test_vacuous_pass_can_never_survive():
    results = [GATE_OK, t("collected_tests", TestStatus.PASS, Severity.FATAL, 0)]
    verdict, reason = aggregate(results)
    assert verdict is DiscoveryVerdict.INCONCLUSIVE
    assert "collected_tests" in reason


def test_vacuous_gate_is_inconclusive():
    verdict, _ = aggregate([t("gate", TestStatus.PASS, Severity.GATE, 0)])
    assert verdict is DiscoveryVerdict.INCONCLUSIVE


def test_real_passes_still_survive():
    results = [GATE_OK, t("a", TestStatus.PASS, Severity.FATAL, 5)]
    assert aggregate(results)[0] is DiscoveryVerdict.SURVIVED


def test_missing_expected_test_is_never_survived():
    results = [GATE_OK, t("a", TestStatus.PASS, Severity.FATAL, 5)]
    verdict, reason = aggregate(results, expected=["gate", "a", "b"])
    assert verdict is DiscoveryVerdict.INCONCLUSIVE
    assert "expected tests missing: b" in reason
    assert aggregate(results, expected=["gate", "a"])[0] is DiscoveryVerdict.SURVIVED


def test_a_fatal_failure_still_refutes_when_a_test_is_missing():
    results = [GATE_OK, t("a", TestStatus.FAIL, Severity.FATAL, 5)]
    assert aggregate(results, expected=["gate", "a", "b"])[0] is DiscoveryVerdict.REFUTED


def test_coverage_round_trips_through_dicts():
    original = t("rows", TestStatus.PASS, Severity.FATAL, 42, "catalog rows")
    assert TestResult.from_dict(original.to_dict()) == original
