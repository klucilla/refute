"""Verdict of one paper claim, and the result of a paper.

Implements docs/verdicts.md ("Paper verdicts (from v0.3)") and
docs/validation/v0.3/wp2-acceptance.md, criteria W2.2-W2.7. The discovery
aggregation in ``refute.core.verdict.aggregate`` is not used here and is unchanged.

Order for one claim (the first rule that matches decides):

0. coverage: a PASS with zero or undeclared coverage, or below the positive minimum,
   is INCONCLUSIVE; a FAIL with zero or undeclared coverage, or below the negative
   minimum, is INCONCLUSIVE (with no declared minimum, both minimums are 1);
1. a gate of the base reproduction that did not pass: NOT_REPRODUCIBLE when the
   failure is recorded as a failure of the artifact's documented procedure with
   complete attempts, INCONCLUSIVE for every other or unknown cause;
2. a valid fatal failure (``base_reproduction``, and ``metric_recompute`` where it
   applies): NOT_REPRODUCED;
3. a base reproduction that is incomplete: INCONCLUSIVE;
4. any attack with a valid failure and its prerequisites met: FRAGILE;
5. any expected attack missing or INCONCLUSIVE: INCONCLUSIVE, with the status
   "Basic reproduction obtained; robustness inconclusive";
6. otherwise: REPRODUCED.

The inputs are checked before any rule runs: a duplicate name, a result nobody
declared, or a minimum or cause that names no check is an error (``ValueError``), so
no evidence is silently dropped.
"""

from __future__ import annotations

import enum
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace

from refute.core.verdict import PaperVerdict, Severity, TestResult, TestStatus, enforce_coverage

BASE_GATES = ("environment_build", "data_present", "run_completed", "metric_extracted")
BASE_REPRODUCTION = "base_reproduction"
METRIC_RECOMPUTE = "metric_recompute"
ROBUSTNESS_INCONCLUSIVE = "Basic reproduction obtained; robustness inconclusive"
NEGATIVE = frozenset(
    {PaperVerdict.FRAGILE, PaperVerdict.NOT_REPRODUCED, PaperVerdict.NOT_REPRODUCIBLE}
)


class FailureCause(enum.StrEnum):
    """Why a gate did not pass (docs/verdicts.md, "Attribution").

    The first three are failures of the artifact's own documented procedure; only
    they can give NOT_REPRODUCIBLE, and only with complete attempts (``GateFailure``).
    """

    BUILD_LADDER = "artifact_build_ladder"  # every rung ran to its end and failed
    DOCUMENTED_COMMAND = "artifact_documented_command"  # fails in the built environment
    ARTIFACT_ABSENT = "artifact_absent"  # answers as absent in all of the N attempts
    BUDGET_EXHAUSTED = "budget_exhausted"
    OPERATIONAL_GUARD = "operational_guard"
    REFUTE_ERROR = "refute_error"
    TRANSIENT_NETWORK = "transient_network"
    INTERRUPTED = "interrupted"
    UNDETERMINED = "undetermined"


# The gates on which each artifact cause can be recorded.
ARTIFACT_CAUSE_GATES: dict[FailureCause, frozenset[str]] = {
    FailureCause.BUILD_LADDER: frozenset({"environment_build"}),
    FailureCause.DOCUMENTED_COMMAND: frozenset(
        {"data_present", "run_completed", "metric_extracted"}
    ),
    FailureCause.ARTIFACT_ABSENT: frozenset(BASE_GATES),
}


@dataclass(frozen=True)
class GateFailure:
    """The recorded cause of a failed gate and the attempts behind it.

    ``attempts_required`` is fixed before the lock: the rungs of the build ladder, the
    runs of the documented command, or the N attempts that found an artifact absent.
    """

    cause: FailureCause | str
    attempts_completed: int = 0
    attempts_required: int = 1

    @property
    def known_cause(self) -> FailureCause:
        try:
            return FailureCause(self.cause)
        except ValueError:
            return FailureCause.UNDETERMINED


@dataclass(frozen=True)
class CoverageMinimum:
    """Minimum coverage of one check, for a positive and for a negative conclusion."""

    positive: int = 1
    negative: int = 1

    def __post_init__(self) -> None:
        if self.positive < 1 or self.negative < 1:
            raise ValueError("coverage minimums must be at least 1")


def prerequisite_names(attack: str) -> tuple[str, str]:
    """The names of the two prerequisites of an attack: its run and its metric."""
    return f"{attack}:run", f"{attack}:metric"


@dataclass
class Attack:
    """One attack on a claim: its two prerequisites (its own run and its own metric,
    both required, named by ``prerequisite_names``) and its result. A missing
    prerequisite makes the attack INCONCLUSIVE."""

    name: str
    run: TestResult | None = None
    metric: TestResult | None = None
    result: TestResult | None = None


@dataclass
class ClaimVerdict:
    verdict: PaperVerdict
    reason: str
    status: str = ""
    basic_reproduction_obtained: bool = False
    attacks_not_executed: list[str] = field(default_factory=list)
    attacks_incomplete: list[str] = field(default_factory=list)
    incomplete_coverage: bool = False


# An attack result may declare in ``metrics`` the coverage of a complete run of the
# attack (for example 5 seeds). A result below it is recorded as incomplete even when
# it is a valid failure.
EXPECTED_COVERAGE = "expected_coverage"


def _is_incomplete(result: TestResult) -> bool:
    expected = result.metrics.get(EXPECTED_COVERAGE)
    return expected is not None and (result.coverage or 0) < expected


def apply_minimum_coverage(result: TestResult, minimum: CoverageMinimum | None) -> TestResult:
    """Below the positive minimum a PASS gives no conclusion; below the negative
    minimum a FAIL gives no conclusion. With no minimum given, both are 1, so a FAIL
    that examined nothing never gives a negative conclusion. Zero or undeclared
    coverage of a PASS is handled first by ``enforce_coverage``."""
    minimum = minimum or CoverageMinimum()
    (result,) = enforce_coverage([result])
    if result.status is TestStatus.FAIL and result.coverage is None:
        return replace(
            result,
            status=TestStatus.INCONCLUSIVE,
            message=f"FAIL refused: the check declared no coverage ({result.message})",
        )
    if result.status is TestStatus.PASS and result.coverage < minimum.positive:
        return replace(
            result,
            status=TestStatus.INCONCLUSIVE,
            message=(
                f"PASS refused: coverage {result.coverage} below the positive minimum "
                f"{minimum.positive} ({result.message})"
            ),
        )
    if result.status is TestStatus.FAIL and result.coverage < minimum.negative:
        return replace(
            result,
            status=TestStatus.INCONCLUSIVE,
            message=(
                f"FAIL refused: coverage {result.coverage} below the negative minimum "
                f"{minimum.negative} ({result.message})"
            ),
        )
    return result


def _unique(names: Sequence[str], what: str) -> None:
    seen: set[str] = set()
    for name in names:
        if name in seen:
            raise ValueError(f"duplicate {what} '{name}'")
        seen.add(name)


def _gate_failure_verdict(name: str, gate: TestResult, failure: GateFailure | None) -> ClaimVerdict:
    if failure is None:
        failure = GateFailure(FailureCause.UNDETERMINED)
    cause = failure.known_cause
    if gate.status is TestStatus.FAIL and cause in ARTIFACT_CAUSE_GATES:
        if name not in ARTIFACT_CAUSE_GATES[cause]:
            return ClaimVerdict(
                PaperVerdict.INCONCLUSIVE,
                f"base gate '{name}' failed; cause {cause.value} does not apply to this gate",
            )
        if failure.attempts_required < 1 or failure.attempts_completed < failure.attempts_required:
            return ClaimVerdict(
                PaperVerdict.INCONCLUSIVE,
                f"base gate '{name}' failed ({cause.value}) with incomplete attempts: "
                f"{failure.attempts_completed} of {failure.attempts_required}",
                incomplete_coverage=True,
            )
        return ClaimVerdict(
            PaperVerdict.NOT_REPRODUCIBLE,
            f"base gate '{name}' failed: the artifact's documented procedure failed "
            f"({cause.value}, {failure.attempts_completed} of "
            f"{failure.attempts_required} attempts)",
        )
    return ClaimVerdict(
        PaperVerdict.INCONCLUSIVE,
        f"base gate '{name}' is {gate.status.value} (cause: {cause.value})",
        incomplete_coverage=gate.status is TestStatus.INCONCLUSIVE,
    )


def aggregate_claim(
    base: Sequence[TestResult],
    attacks: Sequence[Attack],
    expected_attacks: Sequence[str],
    *,
    metric_recompute_applies: bool,
    failures: Mapping[str, GateFailure] | None = None,
    minimums: Mapping[str, CoverageMinimum] | None = None,
) -> ClaimVerdict:
    """Verdict of one paper claim (docs/verdicts.md, "Order of verdicts for one claim").

    ``base`` holds the gates of the base reproduction (``BASE_GATES``) and its fatal
    checks: ``base_reproduction`` and, when ``metric_recompute_applies`` (decided per
    claim before the lock), ``metric_recompute``. Any other name in ``base`` is an
    error. ``attacks`` may hold only names from ``expected_attacks``. ``failures``
    gives the recorded cause of every failed gate; a missing or unknown cause is
    ``UNDETERMINED``. ``minimums`` gives the minimum coverage of each check by name.
    """
    minimums = dict(minimums or {})
    failures = dict(failures or {})
    fatal = (
        (BASE_REPRODUCTION, METRIC_RECOMPUTE) if metric_recompute_applies else (BASE_REPRODUCTION,)
    )

    # inputs: no duplicate, no undeclared result, no minimum or cause that names nothing
    _unique([r.name for r in base], "base check")
    _unique([a.name for a in attacks], "attack")
    _unique(list(expected_attacks), "expected attack")
    undeclared = sorted({r.name for r in base} - set(BASE_GATES) - set(fatal))
    if undeclared:
        raise ValueError("base results not declared for this claim: " + ", ".join(undeclared))
    unexpected = sorted({a.name for a in attacks} - set(expected_attacks))
    if unexpected:
        raise ValueError("attacks not expected for this claim: " + ", ".join(unexpected))
    for a in attacks:
        if a.result is not None and a.result.name != a.name:
            raise ValueError(f"attack '{a.name}' carries a result named '{a.result.name}'")
        for given, declared in zip((a.run, a.metric), prerequisite_names(a.name), strict=True):
            if given is not None and given.name != declared:
                raise ValueError(f"attack '{a.name}' carries a prerequisite named '{given.name}'")
    # the declared checks, whether or not their results arrived
    known = set(BASE_GATES) | set(fatal) | set(expected_attacks)
    for name in expected_attacks:
        known.update(prerequisite_names(name))
    unknown = sorted(set(minimums) - known)
    if unknown:
        raise ValueError("minimum coverage given for unknown checks: " + ", ".join(unknown))
    unknown = sorted(set(failures) - set(BASE_GATES))
    if unknown:
        raise ValueError("failure causes given for names that are not gates: " + ", ".join(unknown))

    checked = {r.name: apply_minimum_coverage(r, minimums.get(r.name)) for r in base}
    by_name = {a.name: a for a in attacks}
    # attacks with no result are "not executed" in every verdict; attacks with a result
    # were executed, even when an earlier rule decides the verdict
    missing = [n for n in expected_attacks if n not in by_name or by_name[n].result is None]

    # 1. gates of the base reproduction
    for name in BASE_GATES:
        gate = checked.get(name)
        if gate is None:
            return ClaimVerdict(
                PaperVerdict.INCONCLUSIVE,
                f"base gate '{name}' missing",
                attacks_not_executed=missing,
                incomplete_coverage=True,
            )
        if gate.status is not TestStatus.PASS:
            verdict = _gate_failure_verdict(name, gate, failures.get(name))
            verdict.attacks_not_executed = missing
            return verdict

    # 2. valid fatal failure
    fatal_failed = [n for n in fatal if n in checked and checked[n].status is TestStatus.FAIL]
    if fatal_failed:
        return ClaimVerdict(
            PaperVerdict.NOT_REPRODUCED,
            "fatal failure in: " + ", ".join(fatal_failed),
            attacks_not_executed=missing,
        )

    # 3. incomplete base reproduction
    incomplete = [n for n in fatal if n not in checked or checked[n].status is not TestStatus.PASS]
    if incomplete:
        return ClaimVerdict(
            PaperVerdict.INCONCLUSIVE,
            "base reproduction incomplete: " + ", ".join(incomplete),
            attacks_not_executed=missing,
            incomplete_coverage=True,
        )

    # the base reproduction is obtained from here on
    failed, inconclusive, partial = [], [], []
    for name in expected_attacks:
        if name in missing:
            continue
        attack = by_name[name]
        prerequisites = [
            None if p is None else apply_minimum_coverage(p, minimums.get(p.name))
            for p in (attack.run, attack.metric)
        ]
        if any(p is None or p.status is not TestStatus.PASS for p in prerequisites):
            inconclusive.append(name)
            continue
        result = apply_minimum_coverage(attack.result, minimums.get(name))
        if _is_incomplete(result):
            partial.append(name)
        if result.status is TestStatus.FAIL:
            failed.append(name)
        elif result.status is TestStatus.INCONCLUSIVE or name in partial:
            # a PASS below the attack's own expected coverage is not a pass
            inconclusive.append(name)

    # 4. valid robustness failure
    if failed:
        return ClaimVerdict(
            PaperVerdict.FRAGILE,
            "valid failure in: " + ", ".join(failed),
            basic_reproduction_obtained=True,
            attacks_not_executed=missing,
            attacks_incomplete=partial,
            incomplete_coverage=bool(missing or inconclusive or partial),
        )
    # 5. robustness incomplete
    if missing or inconclusive:
        parts = []
        if missing:
            parts.append("not executed: " + ", ".join(missing))
        if inconclusive:
            parts.append("inconclusive: " + ", ".join(inconclusive))
        return ClaimVerdict(
            PaperVerdict.INCONCLUSIVE,
            "; ".join(parts),
            status=ROBUSTNESS_INCONCLUSIVE,
            basic_reproduction_obtained=True,
            attacks_not_executed=missing,
            attacks_incomplete=partial,
            incomplete_coverage=True,
        )
    # 6.
    return ClaimVerdict(
        PaperVerdict.REPRODUCED, "every check passed", basic_reproduction_obtained=True
    )


@dataclass
class PaperProfile:
    claims: list[tuple[str, PaperVerdict]]
    counts: dict[str, int]
    total: int
    headline: str
    has_negative: bool


def paper_profile(claims: Sequence[tuple[str, PaperVerdict]]) -> PaperProfile:
    """The result of a paper: the profile of its claims, in the drawn order.

    A headline appears only when every claim has the same verdict; otherwise it is
    "Mixed results: see the claims". INCONCLUSIVE stays in the denominator.
    """
    ordered = [(key, PaperVerdict(v)) for key, v in claims]
    if not ordered:
        raise ValueError("a paper result needs at least one claim")
    _unique([key for key, _ in ordered], "claim")
    counts = {v.value: 0 for v in PaperVerdict}
    for _, verdict in ordered:
        counts[verdict.value] += 1
    total = len(ordered)
    distinct = {v for _, v in ordered}
    if len(distinct) == 1:
        (only,) = distinct
        headline = f"{total} of {total} drawn claims: {only.value}"
    else:
        headline = "Mixed results: see the claims"
    return PaperProfile(
        claims=ordered,
        counts=counts,
        total=total,
        headline=headline,
        has_negative=any(v in NEGATIVE for _, v in ordered),
    )


def attack_result(name: str, status: TestStatus, coverage: int, message: str = "") -> TestResult:
    """Convenience constructor for an attack's own result (severity warning)."""
    return TestResult(
        name, status, Severity.WARNING, message, coverage=coverage, coverage_unit="runs"
    )


def _runs_attack(
    name: str,
    runs: Sequence[bool | None],
    expected_runs: int,
    failures_for_fragile: int,
    rule: str,
    extra_fail: bool = False,
    extra_pending: bool = False,
) -> TestResult:
    if len(runs) != expected_runs:
        raise ValueError(f"{name} expects {expected_runs} run slots, got {len(runs)}")
    valid = [r for r in runs if r is not None]
    failed = sum(1 for r in valid if r is False)
    summary = f"{failed} valid failures in {len(valid)} valid runs of {expected_runs}; {rule}"

    def out(status: TestStatus) -> TestResult:
        result = attack_result(name, status, len(valid), summary)
        result.metrics = {
            EXPECTED_COVERAGE: expected_runs,
            "valid_runs": len(valid),
            "valid_failures": failed,
        }
        return result

    if failed >= failures_for_fragile:
        return out(TestStatus.FAIL)
    if len(valid) < expected_runs:
        return out(TestStatus.INCONCLUSIVE)
    if extra_fail:
        return out(TestStatus.FAIL)
    if extra_pending:
        return out(TestStatus.INCONCLUSIVE)
    return out(TestStatus.PASS)


def seeds_attack(runs: Sequence[bool | None], mean_holds: bool | None) -> TestResult:
    """The ``seeds`` attack (plan section 6.3): 5 extra seeds.

    ``runs`` has one slot per seed: True when the run is valid and the claim's
    predicate holds, False for a valid failure, None for a missing, interrupted or
    invalid run (never a failure). Two valid failures establish the failure. With all
    5 runs valid, at most one failure, and the predicate on the mean of the 5 runs
    holding, the attack passes; the predicate failing on the mean is a failure.
    Otherwise it is INCONCLUSIVE.
    """
    return _runs_attack(
        "seeds",
        runs,
        expected_runs=5,
        failures_for_fragile=2,
        rule="the predicate must hold in at least 4 of 5 runs and on their mean",
        extra_fail=mean_holds is False,
        extra_pending=mean_holds is None,
    )


def data_split_attack(runs: Sequence[bool | None]) -> TestResult:
    """The ``data_split`` attack (plan section 6.3, decision V-3): 3 re-splits; the
    predicate must hold in 3 of 3. One valid failure establishes the failure; a
    missing or invalid run is never a failure."""
    return _runs_attack(
        "data_split",
        runs,
        expected_runs=3,
        failures_for_fragile=1,
        rule="the predicate must hold in 3 of 3 splits",
    )
