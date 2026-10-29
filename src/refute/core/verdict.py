"""Verdict model and deterministic aggregation.

A claim is never "proven". It survives the attacks, or it does not.
See ``docs/verdicts.md``.
"""

from __future__ import annotations

import enum
from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from typing import Any


class DiscoveryVerdict(enum.StrEnum):
    SURVIVED = "SURVIVED"
    WEAKENED = "WEAKENED"
    REFUTED = "REFUTED"
    INCONCLUSIVE = "INCONCLUSIVE"


class PaperVerdict(enum.StrEnum):
    """Verdicts for published-paper claims (used from v0.3 on).

    ``INCONCLUSIVE``: Refute could not decide for reasons on its side (for example an
    exhausted budget or the hang guard); never a failure of the artifact. The rules
    are in ``refute.core.paper`` and ``docs/verdicts.md``.
    """

    REPRODUCED = "REPRODUCED"
    FRAGILE = "FRAGILE"
    NOT_REPRODUCED = "NOT_REPRODUCED"
    NOT_REPRODUCIBLE = "NOT_REPRODUCIBLE"
    INCONCLUSIVE = "INCONCLUSIVE"


class TestStatus(enum.StrEnum):
    __test__ = False  # not a pytest test class

    PASS = "PASS"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"


class Severity(enum.StrEnum):
    """What a failure of this test means.

    - ``gate``: the signal itself is not significant; nothing can be attacked.
    - ``fatal``: the failure refutes the claim.
    - ``warning``: the failure weakens the claim.
    """

    GATE = "gate"
    FATAL = "fatal"
    WARNING = "warning"


@dataclass
class TestResult:
    """Outcome of one deterministic falsification test.

    ``coverage`` is the amount of data the check actually examined (for example
    transits measured, cadences used, catalog rows scanned), in ``coverage_unit``.
    Every domain pack must declare it. A PASS with no declared coverage, or with
    zero coverage, is never accepted: :func:`enforce_coverage` turns it into
    INCONCLUSIVE (a check that examined nothing has not shown anything).
    """

    __test__ = False  # not a pytest test class

    name: str
    status: TestStatus
    severity: Severity
    message: str
    metrics: dict[str, Any] = field(default_factory=dict)
    thresholds: dict[str, Any] = field(default_factory=dict)
    inputs: dict[str, Any] = field(default_factory=dict)
    coverage: int | None = None
    coverage_unit: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "severity": self.severity.value,
            "message": self.message,
            "metrics": self.metrics,
            "thresholds": self.thresholds,
            "inputs": self.inputs,
            "coverage": self.coverage,
            "coverage_unit": self.coverage_unit,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TestResult:
        return cls(
            name=data["name"],
            status=TestStatus(data["status"]),
            severity=Severity(data["severity"]),
            message=data.get("message", ""),
            metrics=dict(data.get("metrics", {})),
            thresholds=dict(data.get("thresholds", {})),
            inputs=dict(data.get("inputs", {})),
            coverage=data.get("coverage"),
            coverage_unit=data.get("coverage_unit", ""),
        )


def enforce_coverage(results: Sequence[TestResult]) -> list[TestResult]:
    """Turn every PASS without positive declared coverage into INCONCLUSIVE.

    Domain-agnostic rule: no check may PASS without evidence that it examined data.
    """
    out = []
    for result in results:
        if result.status is TestStatus.PASS and not (
            result.coverage is not None and result.coverage > 0
        ):
            why = (
                "declared no coverage"
                if result.coverage is None
                else f"examined 0 {result.coverage_unit or 'items'}"
            )
            result = replace(
                result,
                status=TestStatus.INCONCLUSIVE,
                message=f"PASS refused: the check {why} ({result.message})",
            )
        out.append(result)
    return out


class Role(enum.StrEnum):
    """The role of a test in a claim that declares roles (v0.4, issue #174).

    A *decisive* test enters the verdict through :func:`aggregate`. A *diagnostic* test is
    measured and reported, never aggregated: it cannot change the verdict.
    """

    DECISIVE = "decisive"
    DIAGNOSTIC = "diagnostic"


NOT_RUN_AT_STAGE = "not run at this stage"


def defer_tests(
    results: Sequence[TestResult], stages: dict[str, int], stage: int
) -> tuple[list[TestResult], list[str]]:
    """Replace every result whose declared stage is later than ``stage`` by an INCONCLUSIVE
    with zero coverage and the reason ``NOT_RUN_AT_STAGE`` (never a PASS). The severity is
    kept. Returns the results and the names of the deferred tests."""
    out, deferred = [], []
    for result in results:
        needed = int(stages.get(result.name, 1))
        if needed > stage:
            deferred.append(result.name)
            result = TestResult(
                result.name,
                TestStatus.INCONCLUSIVE,
                result.severity,
                f"{NOT_RUN_AT_STAGE} (stage {stage}; this test runs at stage {needed})",
                coverage=0,
                coverage_unit=result.coverage_unit,
            )
        out.append(result)
    return out, deferred


DIAGNOSTIC_STATES = {
    TestStatus.PASS: "pass",
    TestStatus.FAIL: "fail",
    TestStatus.INCONCLUSIVE: "inconclusive",
}


def diagnostic_state(result: TestResult | None) -> str:
    """``pass`` / ``fail`` / ``inconclusive`` for a diagnostic result, ``not_run`` for none.
    The names are deliberately not ``confirmed`` or ``contradicted``."""
    return "not_run" if result is None else DIAGNOSTIC_STATES[result.status]


@dataclass
class RoleAggregate:
    """The verdict of a claim with roles, and what the diagnostics showed."""

    verdict: DiscoveryVerdict
    reason: str
    decisive: list[TestResult]
    diagnostics: dict[str, TestResult | None]
    missing_diagnostics: list[str]

    @property
    def diagnostics_complete(self) -> bool:
        return not self.missing_diagnostics


def aggregate_roles(
    results: Sequence[TestResult],
    roles: dict[str, str],
    expected_decisive: Sequence[str],
    required_diagnostics: Sequence[str],
) -> RoleAggregate:
    """The verdict from the decisive tests only, with the rules of :func:`aggregate` unchanged.

    Every result needs a declared role. Diagnostics are returned apart (after the coverage
    rule, so a diagnostic that examined nothing is INCONCLUSIVE, never PASS) and never reach
    :func:`aggregate`. A required diagnostic absent from ``results`` is listed in
    ``missing_diagnostics`` (the case is then incomplete); the verdict does not change.
    """
    results = enforce_coverage(results)
    unknown = sorted({r.name for r in results} - set(roles))
    if unknown:
        raise ValueError("results without a declared role: " + ", ".join(unknown))
    decisive = [r for r in results if Role(roles[r.name]) is Role.DECISIVE]
    by_name = {r.name: r for r in results if Role(roles[r.name]) is Role.DIAGNOSTIC}
    verdict, reason = aggregate(decisive, expected=expected_decisive)
    diagnostics = {name: by_name.get(name) for name in required_diagnostics}
    for name, result in by_name.items():
        diagnostics.setdefault(name, result)
    missing = [name for name in required_diagnostics if by_name.get(name) is None]
    return RoleAggregate(verdict, reason, decisive, diagnostics, missing)


def aggregate(
    results: Sequence[TestResult], expected: Sequence[str] | None = None
) -> tuple[DiscoveryVerdict, str]:
    """Combine test results into one verdict. The rules are applied in order:

    0. a PASS without positive coverage counts as INCONCLUSIVE (``enforce_coverage``)
    1. a gate test that did not PASS            -> INCONCLUSIVE
    2. any fatal FAIL                           -> REFUTED
    3. any expected test missing, or any INCONCLUSIVE test -> INCONCLUSIVE
    4. any warning FAIL                         -> WEAKENED
    5. otherwise                                -> SURVIVED

    ``expected`` lists the tests that must be present; a result set missing any of
    them can never be SURVIVED or WEAKENED.
    """
    results = enforce_coverage(results)
    gates = [r for r in results if r.severity is Severity.GATE]
    if not gates:
        raise ValueError("aggregate() needs at least one gate test")
    for gate in gates:
        if gate.status is not TestStatus.PASS:
            return (
                DiscoveryVerdict.INCONCLUSIVE,
                f"gate test '{gate.name}' is {gate.status.value}: no significant signal to attack",
            )
    fatal = [
        r.name for r in results if r.status is TestStatus.FAIL and r.severity is Severity.FATAL
    ]
    if fatal:
        return DiscoveryVerdict.REFUTED, "fatal failure in: " + ", ".join(fatal)
    missing = sorted(set(expected or []) - {r.name for r in results})
    if missing:
        return DiscoveryVerdict.INCONCLUSIVE, "expected tests missing: " + ", ".join(missing)
    inconclusive = [r.name for r in results if r.status is TestStatus.INCONCLUSIVE]
    if inconclusive:
        return DiscoveryVerdict.INCONCLUSIVE, "could not be decided: " + ", ".join(inconclusive)
    warnings = [
        r.name for r in results if r.status is TestStatus.FAIL and r.severity is Severity.WARNING
    ]
    if warnings:
        return DiscoveryVerdict.WEAKENED, "warning failure in: " + ", ".join(warnings)
    return DiscoveryVerdict.SURVIVED, "every test passed"
