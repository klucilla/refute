"""Proof that the claim inventories were published before the claim round (WP5 W5.11).

Git dates are not evidence: author and committer dates are set by whoever makes the
commit (https://git-scm.com/docs/git-commit#_commit_information, accessed 2026-10-14).
The evidence is a server-side GitHub timestamp tied to the commit SHA: the
``created_at`` of the GitHub Actions run started by the push of that commit, read from
the GitHub API. The inventories live in a path that the CI ``paths-ignore`` list does
not skip, so that the push starts a run.

The proof holds only when that run exists, is for that exact SHA, was started by a
push, and was created before the claim round's publication time by at least the margin
fixed in the protocol; and when the working tree was clean and every inventory file in
that commit has the published hash. Anything else makes the round unusable for those
inventories: the draw is refused and the maintainer decides.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any


class PublicationError(Exception):
    """The inventories cannot be shown to be published before the round."""


def _utc(text: str) -> datetime:
    if not isinstance(text, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", text):
        raise PublicationError(f"not a UTC timestamp: {text!r}")
    return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)


@dataclass(frozen=True)
class PublicationProof:
    commit_sha: str
    run_id: int
    run_created_at: str
    round_published_at: str  # converted to UTC
    margin_seconds: float


def check_publication(
    commit_sha: str,
    runs: list[Mapping[str, Any]],
    round_published_at: datetime,
    margin: timedelta,
    tree_clean: bool,
    files_in_commit: Mapping[str, str],
    published_hashes: Mapping[str, str],
) -> PublicationProof:
    """``runs``: the GitHub API ``workflow_runs`` for ``head_sha = commit_sha``.
    ``files_in_commit``: SHA-256 of each inventory file as stored in that commit;
    ``published_hashes``: the hashes published with the inventories, one per required
    inventory (never empty: every inventory the draw needs must be covered)."""
    if not re.fullmatch(r"[0-9a-f]{40}", commit_sha):
        raise PublicationError("the commit SHA must be 40 lowercase hex digits")
    if round_published_at.tzinfo is None:
        raise PublicationError("the round time must be timezone-aware (UTC)")
    if margin < timedelta(0):
        raise PublicationError("the margin cannot be negative")
    if not tree_clean:
        raise PublicationError("the working tree is not clean")
    if not published_hashes:
        raise PublicationError("no published inventory hashes: nothing is shown to be published")
    for name, digest in published_hashes.items():
        if not re.fullmatch(r"[0-9a-f]{64}", str(digest)):
            raise PublicationError(f"inventory {name}: the published hash is not a SHA-256")
        if name not in files_in_commit:
            raise PublicationError(f"inventory {name} is not in the commit of the evidence")
        if files_in_commit[name] != digest:
            raise PublicationError(f"inventory {name} differs from its published hash")
    pushes = [r for r in runs if r.get("event") == "push" and r.get("head_sha") == commit_sha]
    if any(r.get("head_sha") != commit_sha for r in runs):
        raise PublicationError("evidence for another SHA")
    if not pushes:
        raise PublicationError("no GitHub Actions run started by the push of that commit")
    first = min(pushes, key=lambda r: _utc(r.get("created_at", "")))
    created = _utc(first["created_at"])
    if created + margin > round_published_at:
        raise PublicationError(
            f"the push run was created at {first['created_at']}, not at least {margin} "
            f"before the round ({round_published_at.isoformat()})"
        )
    return PublicationProof(
        commit_sha,
        int(first["id"]),
        first["created_at"],
        round_published_at.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        margin.total_seconds(),
    )


def fetch_push_runs(
    repository: str, commit_sha: str, get_json: Callable[[str], Mapping[str, Any]]
) -> list[Mapping[str, Any]]:
    """The workflow runs of ``commit_sha`` from the GitHub API (network through
    ``get_json``, so tests run offline). Errors propagate: missing evidence is never
    assumed."""
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise PublicationError("repository must be owner/name")
    data = get_json(
        f"https://api.github.com/repos/{repository}/actions/runs?head_sha={commit_sha}&event=push"
    )
    runs = data.get("workflow_runs")
    if not isinstance(runs, list):
        raise PublicationError("the API answer has no workflow_runs")
    return runs
