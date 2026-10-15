"""The walk of the shuffled frame (WP5 W5.6 to W5.8; plan sections 4.3 and 4.4).

Each candidate gets one decision with one reason from the closed list, and its
evidence. Queries to arXiv, GitHub and Hugging Face retry transient errors a fixed
number of times with a fixed backoff (both written in the protocol, #22). Transient
errors are logged apart from rule-based rejections, with every attempt. A candidate
still unchecked after the retries **stops the walk** for the maintainer: it is never
rejected silently. Nothing here chooses a source of randomness: the order comes in
already shuffled (``refute.drand.shuffled``).
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

# Plan section 4.4, closed list of rejection reasons.
REJECTION_REASONS = (
    "out_of_scope",
    "no_license",
    "data_requires_registration_or_terms",
    "data_license_incompatible",
    "weights_license_incompatible",
    "outside_v03_experimental_scope",
    "data_not_public",
    "needs_paid_api_or_credentials",
    "stated_compute_over_budget",
    "requires_gpu",
    "dataset_over_budget",
    "pretrained_download_over_budget",
    "ambiguous_repository",
    "repository_unavailable",
    "no_reproduction_instructions",
    "category_outside_list",
)
ACCEPTED = "accepted"
REJECTED = "rejected"
STOPPED = "stopped_transient"


class WalkError(Exception):
    """A triage result or a retry policy is not valid."""


class TransientError(Exception):
    """A query failed for a reason that may pass (timeout, HTTP 5xx, connection error)."""


@dataclass(frozen=True)
class RetryPolicy:
    """Fixed in the protocol before its drand round (W5.7)."""

    attempts: int
    backoff_seconds: float

    def __post_init__(self) -> None:
        if self.attempts < 1 or self.backoff_seconds < 0:
            raise WalkError("a retry policy needs at least 1 attempt and a non-negative backoff")


@dataclass
class Attempt:
    utc: str
    error: str


class RetriesExhaustedError(Exception):
    def __init__(self, attempts: list[Attempt]):
        super().__init__(f"transient errors on all {len(attempts)} attempts")
        self.attempts = attempts


def with_retries(
    query: Callable[[], Any],
    policy: RetryPolicy,
    sleep: Callable[[float], None],
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> tuple[Any, list[Attempt]]:
    """Runs ``query``; a ``TransientError`` is retried up to the policy, sleeping the fixed
    backoff between attempts. Returns the result and the failed attempts before it.
    Any other exception propagates at once (it is not transient)."""
    failures: list[Attempt] = []
    for attempt in range(policy.attempts):
        try:
            return query(), failures
        except TransientError as exc:
            failures.append(Attempt(now().strftime("%Y-%m-%dT%H:%M:%SZ"), str(exc)))
            if attempt + 1 < policy.attempts:
                sleep(policy.backoff_seconds)
    raise RetriesExhaustedError(failures)


@dataclass(frozen=True)
class TriageResult:
    decision: str  # ACCEPTED or REJECTED
    reason: str  # ACCEPTED, or one reason of REJECTION_REASONS
    evidence: str

    def __post_init__(self) -> None:
        if self.decision == ACCEPTED:
            if self.reason != ACCEPTED:
                raise WalkError("an acceptance has the reason 'accepted'")
        elif self.decision == REJECTED:
            if self.reason not in REJECTION_REASONS:
                raise WalkError(f"rejection reason not in the closed list: {self.reason!r}")
        else:
            raise WalkError(f"unknown decision {self.decision!r}")
        if not self.evidence.strip():
            raise WalkError("every decision needs its evidence")


@dataclass
class WalkEntry:
    position: int
    arxiv_id: str
    decision: str
    reason: str
    evidence: str
    transient_attempts: list[Attempt] = field(default_factory=list)


@dataclass
class WalkLog:
    entries: list[WalkEntry]
    accepted: list[str]
    stopped: bool

    @property
    def complete(self) -> bool:
        return not self.stopped


def walk(
    ordered_ids: Iterable[str],
    triage: Callable[[str], TriageResult],
    needed: int,
    policy: RetryPolicy,
    sleep: Callable[[float], None],
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> WalkLog:
    """Walks the candidates in the given order until ``needed`` are accepted. ``triage``
    may raise ``TransientError``; after the policy's retries the walk stops at that
    candidate (decision ``stopped_transient``), for the maintainer."""
    if needed < 1:
        raise WalkError("needed must be at least 1")
    entries: list[WalkEntry] = []
    accepted: list[str] = []
    for position, arxiv_id in enumerate(ordered_ids, start=1):
        try:
            result, failures = with_retries(lambda a=arxiv_id: triage(a), policy, sleep, now)
        except RetriesExhaustedError as exc:
            entries.append(
                WalkEntry(
                    position,
                    arxiv_id,
                    STOPPED,
                    "transient errors after the retries",
                    "",
                    exc.attempts,
                )
            )
            return WalkLog(entries, accepted, stopped=True)
        if not isinstance(result, TriageResult):
            raise WalkError("triage must return a TriageResult")
        entries.append(
            WalkEntry(position, arxiv_id, result.decision, result.reason, result.evidence, failures)
        )
        if result.decision == ACCEPTED:
            accepted.append(arxiv_id)
            if len(accepted) == needed:
                return WalkLog(entries, accepted, stopped=False)
    return WalkLog(entries, accepted, stopped=False)


def rejection_profile(log: WalkLog) -> dict[str, int]:
    """Rejections counted by reason (plan section 4.4: the profile is itself a result)."""
    counts = {reason: 0 for reason in REJECTION_REASONS}
    for entry in log.entries:
        if entry.decision == REJECTED:
            counts[entry.reason] += 1
    return counts


def log_markdown(log: WalkLog, labels: Sequence[str] = ()) -> str:
    """The walk as a Markdown table for the selection log."""
    lines = [
        "| Position | arXiv | Decision | Reason | Evidence | Transient attempts |",
        "|---|---|---|---|---|---|",
    ]
    for e in log.entries:
        attempts = "; ".join(f"{a.utc} {a.error}" for a in e.transient_attempts) or "-"
        cells = [str(e.position), e.arxiv_id, e.decision, e.reason, e.evidence or "-", attempts]
        lines.append("| " + " | ".join(cells) + " |")
    if log.stopped:
        lines.append("")
        lines.append(
            "The walk stopped on transient errors; the maintainer decides how to continue."
        )
    return "\n".join([*labels, *lines]) + "\n"
