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
    """Verdicts for published-paper claims (used from v0.3 on)."""

    REPRODUCED = "REPRODUCED"
    FRAGILE = "FRAGILE"
    NOT_REPRODUCED = "NOT_REPRODUCED"
    NOT_REPRODUCIBLE = "NOT_REPRODUCIBLE"


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
