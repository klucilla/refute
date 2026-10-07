"""Verdict model and deterministic aggregation.

A claim is never "proven". It survives the attacks, or it does not.
See ``docs/verdicts.md``.
"""

from __future__ import annotations

import enum
from collections.abc import Sequence
from dataclasses import dataclass, field
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
    """Outcome of one deterministic falsification test."""

    __test__ = False  # not a pytest test class

    name: str
    status: TestStatus
    severity: Severity
    message: str
    metrics: dict[str, Any] = field(default_factory=dict)
    thresholds: dict[str, Any] = field(default_factory=dict)
    inputs: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "severity": self.severity.value,
            "message": self.message,
            "metrics": self.metrics,
            "thresholds": self.thresholds,
            "inputs": self.inputs,
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
        )


def aggregate(results: Sequence[TestResult]) -> tuple[DiscoveryVerdict, str]:
    """Combine test results into one verdict. The rules are applied in order:

    1. a gate test that did not PASS            -> INCONCLUSIVE
    2. any fatal FAIL                           -> REFUTED
    3. any INCONCLUSIVE test                    -> INCONCLUSIVE
    4. any warning FAIL                         -> WEAKENED
    5. otherwise                                -> SURVIVED
    """
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
    inconclusive = [r.name for r in results if r.status is TestStatus.INCONCLUSIVE]
    if inconclusive:
        return DiscoveryVerdict.INCONCLUSIVE, "could not be decided: " + ", ".join(inconclusive)
    warnings = [
        r.name for r in results if r.status is TestStatus.FAIL and r.severity is Severity.WARNING
    ]
    if warnings:
        return DiscoveryVerdict.WEAKENED, "warning failure in: " + ", ".join(warnings)
    return DiscoveryVerdict.SURVIVED, "every test passed"
