"""Execution of one paper in phases, with the WP2 accountant (WP3 design D-S4).

docs/validation/v0.3/wp3-acceptance.md, section 1.0.1, D-S4: a paper runs as one job
that goes through the setup, the base reproduction of every claim in the drawn order,
and only then the attacks, with the shared reserves of the WP2 accountant
(src/refute/core/budget.py; plan section 7.3). Parallelism exists only inside one step
of one claim: the containers of such a step start together, each with its own grant.
The setup runs one container at a time.

For every container the orchestrator asks the accountant for a grant (R = F + M,
W2.10a) before the start, builds the run with the threshold F, runs it on the backend,
and gives the accountant its final usage, read once when it ends (W2.10). It decides no
verdict: it records how each step ended, and the gates, predicates and attacks of
WP2/WP3 read those records.

How a step ends (``Outcome``):

- ``completed``: every container exited with code 0;
- ``failed``: a container exited with another code (the gates decide later whether the
  cause is the artifact's or Refute's);
- ``budget_exhausted``: the grant was refused, or a container reached its threshold F;
- ``operational_guard``: a container was stopped by the stage's active time limit or by
  the no-progress guard;
- ``refute_error``: the backend failed, a container was not started after its grant, a
  record was rejected, an unknown stop reason was returned, or the accounting became
  invalid (a breach);
- ``not_executed``: the step did not run, with the reason.

A Refute error stops the paper: any error inside the orchestrator, including one raised
by a callback or by the reading of the parent cgroup, is recorded and never escapes;
every step without a record is then ``not_executed`` and the accounting is invalid, so
every claim without a valid conclusion is ``INCONCLUSIVE``.

Inside a claim's base reproduction, a step runs only when the previous one completed
(no base run without a build). Attacks are independent of each other: each applicable
attack runs whatever the previous attack gave. Budget exhaustion and operational guards
are never causes of the artifact (WP2 W2.3).
"""

from __future__ import annotations

import enum
from collections.abc import Callable, Sequence
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Protocol

from refute.core import budget as bg
from refute.packs.ml.sandbox import (
    STOP_ACTIVE_TIME,
    STOP_NO_PROGRESS,
    STOP_THRESHOLD,
    RunResult,
    RunSpec,
    TimingMaxima,
    timing_alerts,
)


class Outcome(enum.StrEnum):
    COMPLETED = "completed"
    FAILED = "failed"
    BUDGET_EXHAUSTED = "budget_exhausted"
    OPERATIONAL_GUARD = "operational_guard"
    REFUTE_ERROR = "refute_error"
    NOT_EXECUTED = "not_executed"


COMPLETENESS_NOT_APPLICABLE = "not_applicable"  # no parent cgroup (subprocess backend)
COMPLETENESS_COMPLETE = "complete"
COMPLETENESS_INVALID = "invalid"

SETUP, BASE, ATTACKS = "setup", "base", "attacks"
_KNOWN_STOPS = frozenset({STOP_THRESHOLD, STOP_ACTIVE_TIME, STOP_NO_PROGRESS})


class Backend(Protocol):
    name: str

    def run(self, spec: RunSpec) -> RunResult: ...


@dataclass(frozen=True)
class Container:
    """One container of a step. ``make_spec`` builds its run from the threshold F of its
    grant; the run must carry exactly that threshold."""

    container_id: str
    make_spec: Callable[[int], RunSpec]


@dataclass(frozen=True)
class Step:
    """Containers that start together, inside one claim (the setup takes one)."""

    name: str
    containers: Sequence[Container]

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("a step needs a name")
        ids = [c.container_id for c in self.containers]
        if not ids or len(set(ids)) != len(ids):
            raise ValueError(f"step {self.name}: container ids must be given, without duplicates")


@dataclass(frozen=True)
class ContainerRecord:
    container_id: str
    account: str
    threshold_usec: int
    reservation_usec: int
    result: RunResult | None  # None when the container did not run to a result
    error: str = ""


@dataclass(frozen=True)
class StepRecord:
    phase: str  # "setup", "base" or "attacks"
    claim: str | None
    step: str
    outcome: Outcome
    reason: str = ""
    containers: tuple[ContainerRecord, ...] = ()


@dataclass(frozen=True)
class ClaimPlan:
    """One claim, in the drawn order. ``attack_steps`` holds one step per applicable
    attack, in the effective order fixed before the lock (plan section 7.4).
    ``base_obtained`` decides, from the records of the claim's base steps, whether the
    base reproduction was obtained (its gates and predicate, WP2/WP3); it is asked only
    when every base step completed."""

    key: str
    base_steps: Sequence[Step]
    attack_steps: Sequence[Step]
    base_obtained: Callable[[Sequence[StepRecord]], bool]


@dataclass(frozen=True)
class PaperPlan:
    setup_steps: Sequence[Step]
    claims: Sequence[ClaimPlan]

    def __post_init__(self) -> None:
        keys = [c.key for c in self.claims]
        if not keys or len(set(keys)) != len(keys):
            raise ValueError("a paper needs claims with unique keys")
        for step in self.setup_steps:
            if len(step.containers) != 1:
                raise ValueError(
                    f"setup step {step.name}: the setup runs one container at a time (D-S4)"
                )
        ids = [c.container_id for _, _, step in self.steps() for c in step.containers]
        if len(set(ids)) != len(ids):
            raise ValueError("container ids must be unique in a paper")
        names = [(phase, claim, step.name) for phase, claim, step in self.steps()]
        if len(set(names)) != len(names):
            raise ValueError("step names must be unique within the setup and within each claim")

    def steps(self) -> list[tuple[str, str | None, Step]]:
        """Every step with its phase and claim, in the order of execution."""
        out: list[tuple[str, str | None, Step]] = [(SETUP, None, s) for s in self.setup_steps]
        for claim in self.claims:
            out += [(BASE, claim.key, s) for s in claim.base_steps]
        for claim in self.claims:
            out += [(ATTACKS, claim.key, s) for s in claim.attack_steps]
        return out


@dataclass
class PaperRun:
    steps: list[StepRecord] = field(default_factory=list)
    setup_exhausted: bool = False
    base_obtained: dict[str, bool] = field(default_factory=dict)
    attack_claims: list[str] = field(default_factory=list)
    no_distribution: bool = False
    stopped: str = ""  # why the paper stopped early (a Refute error), or ""
    accounting_valid: bool = False  # set at the end; never True before the paper ends
    invalid_reasons: list[str] = field(default_factory=list)
    completeness: str = COMPLETENESS_NOT_APPLICABLE
    accountant_log: list[str] = field(default_factory=list)
    # a measured D or S above its V22 maximum, per container (1.4a; decided by the
    # maintainer on 2026-10-16): recorded for the maintainer, with no other effect
    timing_alerts: list[str] = field(default_factory=list)

    def of(self, phase: str, claim: str | None) -> list[StepRecord]:
        return [s for s in self.steps if s.phase == phase and s.claim == claim]


def _outcome(records: Sequence[ContainerRecord]) -> tuple[Outcome, str]:
    """How a step ended, from its containers; the most serious cause wins."""
    errors = [r for r in records if r.result is None]
    if errors:
        return Outcome.REFUTE_ERROR, "; ".join(f"{r.container_id}: {r.error}" for r in errors)
    stopped = {r.container_id: r.result.stopped for r in records if r.result.stopped}
    unknown = {k: v for k, v in stopped.items() if v not in _KNOWN_STOPS}
    if unknown:  # never masked by a known reason of another container
        return Outcome.REFUTE_ERROR, "unknown stop reason: " + repr(dict(sorted(unknown.items())))
    if STOP_THRESHOLD in stopped.values():
        names = sorted(k for k, v in stopped.items() if v == STOP_THRESHOLD)
        return Outcome.BUDGET_EXHAUSTED, "threshold reached: " + ", ".join(names)
    if stopped:
        return Outcome.OPERATIONAL_GUARD, "; ".join(f"{k}: {v}" for k, v in sorted(stopped.items()))
    failed = [r for r in records if r.result.exit_code != 0]
    if failed:
        return Outcome.FAILED, "; ".join(
            f"{r.container_id}: exit code {r.result.exit_code}" for r in failed
        )
    return Outcome.COMPLETED, ""


def _error(exc: BaseException) -> str:
    return f"{type(exc).__name__}: {exc}"


class PaperRunner:
    """Runs one ``PaperPlan`` on a backend with an accountant.

    ``parent_usage`` and ``tolerance_usec`` are given only by a backend with a parent
    cgroup per paper (docker, on the VM): the completeness check of W2.10 then runs at
    the end. Without them it is recorded as not applicable.

    ``timing_maxima`` are the V22 maxima of D and S: a container whose measured value
    exceeds one gets an alert in ``PaperRun.timing_alerts``. The alert changes nothing
    else: not the margin M, the tolerance T, a threshold, a limit or an outcome."""

    def __init__(
        self,
        plan: PaperPlan,
        backend: Backend,
        accountant: bg.Accountant,
        *,
        parent_usage: Callable[[], int] | None = None,
        tolerance_usec: int | None = None,
        timing_maxima: TimingMaxima | None = None,
    ) -> None:
        if [c.key for c in plan.claims] != list(accountant.claims):
            raise ValueError("the accountant's claims must be the plan's, in the drawn order")
        if accountant.phase is not bg.Phase.SETUP or accountant.charged or accountant.running:
            raise ValueError("the accountant must be new")
        if (parent_usage is None) != (tolerance_usec is None):
            raise ValueError("parent_usage and tolerance_usec are given together")
        if tolerance_usec is not None and (type(tolerance_usec) is not int or tolerance_usec < 0):
            raise ValueError("tolerance_usec must be a non-negative integer of microseconds")
        self.plan = plan
        self.backend = backend
        self.accountant = accountant
        if timing_maxima is not None and not isinstance(timing_maxima, TimingMaxima):
            raise ValueError("timing_maxima is a TimingMaxima")
        self.parent_usage = parent_usage
        self.tolerance_usec = tolerance_usec
        self.timing_maxima = timing_maxima
        self.run_record = PaperRun()

    # -- one container, one step -------------------------------------------------------

    def _run_container(self, container: Container, grant: bg.Grant) -> ContainerRecord:
        try:
            spec = container.make_spec(grant.threshold_usec)
            if not isinstance(spec, RunSpec) or spec.threshold_usec != grant.threshold_usec:
                raise ValueError("the run does not carry the threshold of its grant")
            result = self.backend.run(spec)
            if not isinstance(result, RunResult):
                raise TypeError("the backend returned no RunResult")
        except Exception as exc:  # recorded; the paper stops (Refute error)
            return self._no_result(container, grant, _error(exc))
        return ContainerRecord(
            container.container_id,
            str(grant.account),
            grant.threshold_usec,
            grant.reservation_usec,
            result,
        )

    @staticmethod
    def _no_result(container: Container, grant: bg.Grant, error: str) -> ContainerRecord:
        return ContainerRecord(
            container.container_id,
            str(grant.account),
            grant.threshold_usec,
            grant.reservation_usec,
            None,
            error,
        )

    def _run_together(
        self, containers: Sequence[Container], grants: Sequence[bg.Grant]
    ) -> tuple[ContainerRecord, ...]:
        """Runs the containers of one step at the same time. A container that could not be
        submitted gets no result; the ones already submitted are waited for."""
        submitted: dict[str, Future] = {}
        error = ""
        try:
            with ThreadPoolExecutor(max_workers=len(grants)) as pool:
                for c, g in zip(containers, grants, strict=True):
                    submitted[c.container_id] = pool.submit(self._run_container, c, g)
        except Exception as exc:  # leaving the block waited for every submitted run
            error = _error(exc)
        records = []
        for c, g in zip(containers, grants, strict=True):
            future = submitted.get(c.container_id)
            if future is None:
                records.append(self._no_result(c, g, "not started: " + (error or "unknown")))
                continue
            try:
                records.append(future.result())
            except Exception as exc:
                records.append(self._no_result(c, g, _error(exc)))
        return tuple(records)  # in the plan's order

    def _run_step(self, phase: str, claim: str | None, account: bg.Account, step: Step):
        ids = [c.container_id for c in step.containers]
        try:
            grants = self.accountant.grant(account, ids)
        except bg.BudgetRefusedError as exc:
            d = exc.decision
            if d.reason == bg.BUDGET_EXHAUSTED:
                outcome, reason = Outcome.BUDGET_EXHAUSTED, f"{d.reason} ({d.pool})"
            else:
                outcome, reason = Outcome.REFUTE_ERROR, d.reason
            return self._add(StepRecord(phase, claim, step.name, outcome, reason))
        records = self._run_together(step.containers, grants)
        problems = []
        for record in records:
            if record.result is None:
                continue  # no final usage: the container stays without a record
            if self.timing_maxima is not None:
                for alert in timing_alerts(record.result, self.timing_maxima):
                    self.run_record.timing_alerts.append(f"{record.container_id}: {alert}")
            try:
                self.accountant.finish(record.container_id, account, record.result.usage_usec)
            except (bg.RecordRejectedError, ValueError) as exc:
                problems.append(f"{record.container_id}: record rejected: {exc}")
        outcome, reason = _outcome(records)
        if problems or not self.accountant.accounting_valid:
            outcome = Outcome.REFUTE_ERROR
            reason = "; ".join(
                [r for r in [reason] if r] + problems + self.accountant.invalid_reasons
            )
        return self._add(StepRecord(phase, claim, step.name, outcome, reason, records))

    def _add(self, record: StepRecord) -> StepRecord:
        self.run_record.steps.append(record)
        if record.outcome is Outcome.REFUTE_ERROR:
            where = " ".join(p for p in (record.phase, record.claim or "", record.step) if p)
            self._stop(f"{where}: {record.reason or 'Refute error'}")
        return record

    def _stop(self, reason: str) -> None:
        if not self.run_record.stopped:
            self.run_record.stopped = reason

    def _skip(self, phase: str, claim: str | None, steps: Sequence[Step], reason: str) -> None:
        for step in steps:
            self.run_record.steps.append(
                StepRecord(phase, claim, step.name, Outcome.NOT_EXECUTED, reason)
            )

    def _run_sequence(
        self, phase: str, claim: str | None, account: bg.Account, steps: Sequence[Step]
    ) -> bool:
        """A step runs only when the previous one completed. Returns whether every step
        completed. After a Refute error it returns at once; the final sweep records the
        steps that did not run."""
        for i, step in enumerate(steps):
            record = self._run_step(phase, claim, account, step)
            if self.run_record.stopped:
                return False
            if record.outcome is not Outcome.COMPLETED:
                reason = f"step {step.name} did not complete ({record.outcome})"
                self._skip(phase, claim, steps[i + 1 :], reason)
                return False
        return True

    def _base_obtained(self, claim: ClaimPlan) -> bool:
        try:
            return bool(claim.base_obtained(self.run_record.of(BASE, claim.key)))
        except Exception as exc:
            self._add(
                StepRecord(
                    BASE,
                    claim.key,
                    "base_obtained",
                    Outcome.REFUTE_ERROR,
                    "the base evaluation failed: " + _error(exc),
                )
            )
            return False

    # -- the paper ---------------------------------------------------------------------

    def run(self) -> PaperRun:
        try:
            self._phases()
        except Exception as exc:  # an unexpected Refute error is recorded, never raised
            self._stop("unexpected error: " + _error(exc))
        self._sweep()
        self._close()
        return self.run_record

    def _phases(self) -> None:
        out, acc, plan = self.run_record, self.accountant, self.plan

        setup_ok = self._run_sequence(SETUP, None, bg.SETUP, plan.setup_steps)
        if out.stopped:
            return
        acc.end_setup()
        out.setup_exhausted = acc.setup_exhausted

        for claim in plan.claims:
            if not setup_ok:
                self._skip(BASE, claim.key, claim.base_steps, "the setup did not complete")
                obtained = False
            elif out.setup_exhausted:
                reason = f"{bg.BUDGET_EXHAUSTED} ({bg.Pool.SETUP})"
                self._skip(BASE, claim.key, claim.base_steps, reason)
                obtained = False
            else:
                done = self._run_sequence(BASE, claim.key, bg.base(claim.key), claim.base_steps)
                if out.stopped:
                    return
                obtained = done and self._base_obtained(claim)
                if out.stopped:
                    return
            out.base_obtained[claim.key] = obtained
            acc.close_base(claim.key)

        acc.freeze_attacks(
            {c.key: out.base_obtained[c.key] and bool(c.attack_steps) for c in plan.claims}
        )
        out.no_distribution = acc.no_distribution
        out.attack_claims = list(acc.attacks.claims) if acc.attacks is not None else []

        for claim in plan.claims:
            if claim.key not in out.attack_claims:
                reason = "not eligible for attacks (base not obtained or no applicable attack)"
                self._skip(ATTACKS, claim.key, claim.attack_steps, reason)
                continue
            for step in claim.attack_steps:
                self._run_step(ATTACKS, claim.key, bg.attack(claim.key), step)
                if out.stopped:
                    return
            acc.close_attack(claim.key)

    def _sweep(self) -> None:
        """Every step of the plan without a record is recorded as not executed, and every
        claim without a base result as not obtained."""
        out = self.run_record
        done = {(s.phase, s.claim, s.step) for s in out.steps}
        reason = "the paper stopped: " + out.stopped if out.stopped else "not reached"
        for phase, claim, step in self.plan.steps():
            if (phase, claim, step.name) not in done:
                out.steps.append(StepRecord(phase, claim, step.name, Outcome.NOT_EXECUTED, reason))
        for claim in self.plan.claims:
            out.base_obtained.setdefault(claim.key, False)

    def _close(self) -> None:
        out, acc = self.run_record, self.accountant
        if self.parent_usage is not None:
            complete = False
            if not out.stopped:
                try:
                    complete = acc.check_completeness(self.parent_usage(), self.tolerance_usec)
                except Exception as exc:
                    self._stop("the completeness check failed: " + _error(exc))
            out.completeness = COMPLETENESS_COMPLETE if complete else COMPLETENESS_INVALID
        out.accounting_valid = acc.accounting_valid and not out.stopped
        out.invalid_reasons = list(acc.invalid_reasons)
        if out.stopped and out.stopped not in out.invalid_reasons:
            out.invalid_reasons.append(out.stopped)
        out.accountant_log = list(acc.log)
