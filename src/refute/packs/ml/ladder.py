"""Build ladder and allowed patches of the ML pack (WP3 W3.9).

Plan section 6.1 (docs/plans/v0.3-plan.md, lines 393-403), fixed before the lock with
no free-form fixes:

1. ``own_environment``: the repository's own Dockerfile or ``environment.yml`` / lock
   file, as is;
2. ``requirements_compiled``: its ``requirements.txt`` resolved with
   ``uv pip compile --exclude-newer <date of the pinned commit>``, with the base Python
   (the first of ``build.python_ladder``);
3. ``requirements_compiled_next_python``: step 2 with the next Python version of the
   ladder.

"The first rung that builds is used; all attempts are logged." A rung whose input does
not exist in the repository is recorded as not applicable (WP3 design 1.0.2).

**Attribution of the ``environment_build`` gate** (plan section 8.2, lines 668-679):
``NOT_REPRODUCIBLE`` needs "every rung of the build ladder ran to its end and failed with
an error of the procedure itself". This module reads it literally: the cause
``artifact_build_ladder`` is recorded with ``attempts_required`` equal to the three rungs
of the ladder and ``attempts_completed`` equal to the rungs that ran to their end and
failed with an error of the procedure. A rung that was not applicable is not an attempt,
so the WP2 core gives ``INCONCLUSIVE`` (incomplete attempts) unless all three rungs ran
and failed. Whether a failure is an error of the procedure itself is decided by the
caller that ran the build (``RungResult.cause``); anything else, or nothing, is never an
artifact cause. This denominator (three rungs, not only the applicable ones) was a
provisional decision of 2026-10-16, taken under the maintainer's night delegation as the
more conservative reading (#94); ratified by the maintainer on 2026-10-16, preserving the
validation conditions and the documented concessions. The alternative (only the
applicable rungs) would change the verdict criterion.

The ladder stops at the first rung that builds, and also at the first rung that ends for
a reason on Refute's side (budget, operational guard, Refute error, a transient network
failure, an undetermined cause): an interrupted rung is not known to fail, so the next
rung is not tried in its place, and the gate is ``INCONCLUSIVE`` with that cause.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from refute.core.paper import FailureCause, GateFailure
from refute.core.verdict import Severity, TestResult, TestStatus
from refute.packs.ml.orchestrate import Outcome

RUNGS = ("own_environment", "requirements_compiled", "requirements_compiled_next_python")
GATE = "environment_build"

# How a rung that did not build stops the ladder, by the outcome of its build step.
_STOP_CAUSES = {
    Outcome.BUDGET_EXHAUSTED: FailureCause.BUDGET_EXHAUSTED,
    Outcome.OPERATIONAL_GUARD: FailureCause.OPERATIONAL_GUARD,
    Outcome.REFUTE_ERROR: FailureCause.REFUTE_ERROR,
    Outcome.NOT_EXECUTED: FailureCause.INTERRUPTED,
}
# The causes a failed rung may carry besides an error of the procedure itself.
_FAILED_STOP_CAUSES = frozenset(
    {
        FailureCause.TRANSIENT_NETWORK,
        FailureCause.REFUTE_ERROR,
        FailureCause.INTERRUPTED,
        FailureCause.UNDETERMINED,
    }
)


@dataclass(frozen=True)
class Rung:
    name: str
    applicable: bool
    reason: str  # the input found, or why the rung does not apply
    python: str | None = None  # the Python version of rungs 2 and 3


@dataclass(frozen=True)
class RungResult:
    """How the build of one rung ended. ``cause`` is required for a ``failed`` build: the
    caller's classification of the failure (``artifact_build_ladder`` only for an error
    of the procedure itself). It is ignored for any other outcome."""

    outcome: Outcome
    cause: FailureCause | None = None
    detail: str = ""


@dataclass(frozen=True)
class Attempt:
    rung: str
    applicable: bool
    reason: str
    result: RungResult | None  # None when the rung was not applicable or not reached
    reached: bool


@dataclass(frozen=True)
class LadderResult:
    built_with: str | None
    attempts: tuple[Attempt, ...]
    gate: TestResult  # the environment_build gate
    failure: GateFailure | None  # its recorded cause when it did not pass


def ladder_rungs(
    own_environment: str | None, requirements: str | None, python_ladder: Sequence[str]
) -> list[Rung]:
    """The three rungs, from the inputs found in the repository at the pinned commit:
    ``own_environment`` names the Dockerfile, environment file or lock file found (or
    None), ``requirements`` the requirements file found (or None)."""
    versions = list(python_ladder)
    if not versions or any(not isinstance(v, str) or not v for v in versions):
        raise ValueError("python_ladder is a non-empty list of versions")
    base, following = versions[0], versions[1] if len(versions) > 1 else None
    rungs = [
        Rung(
            RUNGS[0],
            own_environment is not None,
            f"found {own_environment}" if own_environment else "no own environment file",
        ),
        Rung(
            RUNGS[1],
            requirements is not None,
            f"found {requirements}" if requirements else "no requirements file",
            base,
        ),
    ]
    if requirements is None:
        rungs.append(Rung(RUNGS[2], False, "no requirements file", following))
    elif following is None:
        rungs.append(Rung(RUNGS[2], False, "no next Python version in the ladder"))
    else:
        rungs.append(Rung(RUNGS[2], True, f"found {requirements}", following))
    return rungs


def run_ladder(rungs: Sequence[Rung], build: Callable[[Rung], RungResult]) -> LadderResult:
    """Tries the applicable rungs in order and returns the ``environment_build`` gate."""
    if [r.name for r in rungs] != list(RUNGS):
        raise ValueError(f"the ladder is fixed: {RUNGS}, in this order")
    python = {r.name: r.python for r in rungs}
    attempts: list[Attempt] = []
    built_with: str | None = None
    stop_cause: FailureCause | None = None
    stop_detail = ""
    procedure_failures = 0
    for rung in rungs:
        if built_with is not None or stop_cause is not None:
            attempts.append(Attempt(rung.name, rung.applicable, rung.reason, None, False))
            continue
        if not rung.applicable:
            attempts.append(Attempt(rung.name, False, rung.reason, None, True))
            continue
        try:
            result = build(rung)
            if not isinstance(result, RungResult) or not isinstance(result.outcome, Outcome):
                raise TypeError("the build of a rung returned no RungResult")
        except Exception as exc:  # a Refute error: recorded, the ladder stops
            result = RungResult(Outcome.REFUTE_ERROR, None, f"{type(exc).__name__}: {exc}")
        attempts.append(Attempt(rung.name, True, rung.reason, result, True))
        if result.outcome is Outcome.COMPLETED:
            built_with = rung.name
        elif result.outcome is Outcome.FAILED:
            if result.cause is FailureCause.BUILD_LADDER:
                procedure_failures += 1  # an error of the procedure: try the next rung
            else:
                # no cause, or any cause that is not an error of the procedure itself,
                # stops the ladder and is never an artifact cause
                given = result.cause
                stop_cause = given if given in _FAILED_STOP_CAUSES else FailureCause.UNDETERMINED
                stop_detail = result.detail
        else:
            stop_cause = _STOP_CAUSES[result.outcome]
            stop_detail = result.detail

    log = [
        {
            "rung": a.rung,
            "applicable": a.applicable,
            "reason": a.reason,
            "reached": a.reached,
            "python": python[a.rung],
            "outcome": None if a.result is None else str(a.result.outcome),
            "cause": None if a.result is None or a.result.cause is None else str(a.result.cause),
            "detail": "" if a.result is None else a.result.detail,
        }
        for a in attempts
    ]
    common = {"metrics": {"attempts": log}, "coverage_unit": "build ladder rungs"}
    if built_with is not None:
        gate = TestResult(
            GATE,
            TestStatus.PASS,
            Severity.GATE,
            f"built with the rung {built_with}",
            coverage=1,
            **common,
        )
        return LadderResult(built_with, tuple(attempts), gate, None)
    if stop_cause is not None:
        gate = TestResult(
            GATE,
            TestStatus.INCONCLUSIVE,
            Severity.GATE,
            f"the ladder stopped ({stop_cause.value}): {stop_detail}".rstrip(": "),
            coverage=procedure_failures,
            **common,
        )
        return LadderResult(None, tuple(attempts), gate, GateFailure(stop_cause))
    if procedure_failures == 0:
        gate = TestResult(
            GATE,
            TestStatus.INCONCLUSIVE,
            Severity.GATE,
            "no rung of the build ladder applies to this repository",
            coverage=0,
            **common,
        )
        return LadderResult(None, tuple(attempts), gate, GateFailure(FailureCause.UNDETERMINED))
    gate = TestResult(
        GATE,
        TestStatus.FAIL,
        Severity.GATE,
        f"{procedure_failures} of {len(RUNGS)} rungs ran to their end and failed with an error "
        "of the procedure",
        coverage=procedure_failures,
        **common,
    )
    failure = GateFailure(FailureCause.BUILD_LADDER, procedure_failures, len(RUNGS))
    return LadderResult(None, tuple(attempts), gate, failure)


# ---- allowed patches (plan lines 401-403) ----------------------------------------------------


@dataclass(frozen=True)
class AllowedPatch:
    """One patch of ``build.allowed_patches``: the attachment path and its SHA-256, both
    covered by the lock."""

    attachment: str
    sha256: str


class PatchRefusedError(ValueError):
    """A patch that is not in the list fixed before the lock, or whose bytes differ."""


def check_patch(attachment: str, data: bytes, allowed: Sequence[AllowedPatch]) -> str:
    """Returns the SHA-256 of a patch that may be applied; refuses any other. Every patch
    applied is recorded as a diff in the dossier by the caller."""
    listed = [p for p in allowed if p.attachment == attachment]
    if len(listed) != 1:
        raise PatchRefusedError(
            f"patch {attachment!r} is not in the allowed list fixed before the lock"
        )
    digest = hashlib.sha256(data).hexdigest()
    if digest != listed[0].sha256:
        raise PatchRefusedError(f"patch {attachment!r} differs from its locked SHA-256")
    return digest
