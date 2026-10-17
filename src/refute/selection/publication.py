"""Proof that the claim inventories were published before the claim round (WP5 W5.11).

Git dates are not evidence: author and committer dates are set by whoever makes the
commit (https://git-scm.com/docs/git-commit#_commit_information, accessed 2026-10-14).
The evidence is a server-side GitHub timestamp tied to the commit SHA: the
``created_at`` of the GitHub Actions run started by the push of that commit, read from
the GitHub API. The inventories live in a path that the CI ``paths-ignore`` list does
not skip, so that the push starts a run.

The proof holds only when that run exists, is for that exact SHA, was started by a
push, belongs to the expected repository and workflow file, and was created before the
claim round's publication time by at least the margin fixed in the protocol; and when
the working tree was clean and every inventory file in that commit has the published
hash. Anything else makes the round unusable for those inventories: the draw is refused
and the maintainer decides.

**Re-runs.** A re-run of a workflow keeps the run's ``id`` and ``created_at`` and raises
its ``run_attempt``; ``run_started_at`` changes (observed on this repository's run
38896912610 on 2026-10-17: ``created_at`` 2026-10-16T11:54:40Z, ``run_attempt`` 2,
``run_started_at`` 2026-10-16T12:31:11Z). So the proof uses ``created_at`` only, records
the attempt, and a re-run is never a new publication (#59, Codex review of #82).

**Paging.** The runs are listed with ``per_page=100`` and every page is read until the
API's ``total_count`` is reached; a short or inconsistent listing is refused.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Collection, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

PER_PAGE = 100
REPOSITORY = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
WORKFLOW_PATH = re.compile(r"\.github/workflows/[A-Za-z0-9_.-]+\.ya?ml")


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
    repository: str
    workflow_path: str
    run_attempt: int
    # the published SHA-256 of each required inventory, sorted by name
    inventory_hashes: tuple[tuple[str, str], ...] = ()


def _full_name(value: Any) -> str | None:
    return value.get("full_name") if isinstance(value, Mapping) else None


def _check_identity(run: Mapping[str, Any], repository: str, workflow_path: str) -> None:
    """A run counts only for the expected repository (its own and its head repository,
    so a fork's run is never evidence) and the expected workflow file."""
    if _full_name(run.get("repository")) != repository:
        raise PublicationError(f"run {run.get('id')}: not a run of {repository}")
    if _full_name(run.get("head_repository")) != repository:
        raise PublicationError(f"run {run.get('id')}: its head repository is not {repository}")
    if run.get("path") != workflow_path:
        raise PublicationError(f"run {run.get('id')}: not a run of the workflow {workflow_path}")
    attempt = run.get("run_attempt")
    if not isinstance(attempt, int) or isinstance(attempt, bool) or attempt < 1:
        raise PublicationError(f"run {run.get('id')}: run_attempt must be a positive integer")


def check_publication(
    commit_sha: str,
    runs: list[Mapping[str, Any]],
    round_published_at: datetime,
    margin: timedelta,
    tree_clean: bool,
    files_in_commit: Mapping[str, str],
    published_hashes: Mapping[str, str],
    required_inventories: Collection[str],
    *,
    repository: str,
    workflow_path: str,
) -> PublicationProof:
    """``runs``: the GitHub API ``workflow_runs`` for ``head_sha = commit_sha``
    (``fetch_push_runs``). ``files_in_commit``: SHA-256 of each inventory file as stored
    in that commit; ``published_hashes``: the hashes published with the inventories, one
    per required inventory (never empty: every inventory the draw needs must be covered).
    ``repository`` (``owner/name``) and ``workflow_path`` (for example
    ``.github/workflows/ci.yml``) are fixed in the protocol: a run of another repository,
    of a fork or of another workflow is never evidence."""
    if not re.fullmatch(r"[0-9a-f]{40}", commit_sha):
        raise PublicationError("the commit SHA must be 40 lowercase hex digits")
    if not REPOSITORY.fullmatch(repository):
        raise PublicationError("repository must be owner/name")
    if not WORKFLOW_PATH.fullmatch(workflow_path):
        raise PublicationError("workflow_path must be .github/workflows/<file>.yml")
    if round_published_at.tzinfo is None:
        raise PublicationError("the round time must be timezone-aware (UTC)")
    if margin < timedelta(0):
        raise PublicationError("the margin cannot be negative")
    if not tree_clean:
        raise PublicationError("the working tree is not clean")
    if not published_hashes:
        raise PublicationError("no published inventory hashes: nothing is shown to be published")
    required = set(required_inventories)
    if not required:
        raise PublicationError("the set of required inventories is empty")
    if set(published_hashes) != required:
        missing = sorted(required - set(published_hashes))
        extra = sorted(set(published_hashes) - required)
        raise PublicationError(
            f"the published hashes do not cover exactly the required inventories "
            f"(missing: {missing}, not required: {extra})"
        )
    for name, digest in published_hashes.items():
        if not re.fullmatch(r"[0-9a-f]{64}", str(digest)):
            raise PublicationError(f"inventory {name}: the published hash is not a SHA-256")
        if name not in files_in_commit:
            raise PublicationError(f"inventory {name} is not in the commit of the evidence")
        if files_in_commit[name] != digest:
            raise PublicationError(f"inventory {name} differs from its published hash")
    if any(r.get("head_sha") != commit_sha for r in runs):
        raise PublicationError("evidence for another SHA")
    pushes = [r for r in runs if r.get("event") == "push"]
    if not pushes:
        raise PublicationError("no GitHub Actions run started by the push of that commit")
    ids = [r.get("id") for r in pushes]
    if len(set(ids)) != len(ids):
        raise PublicationError("the listing repeats a run")
    for r in pushes:
        _check_identity(r, repository, workflow_path)
    # the earliest creation among the push runs of this SHA and workflow; created_at, never
    # run_started_at, so a re-run (same id, a higher run_attempt) never moves the time
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
        repository,
        workflow_path,
        int(first["run_attempt"]),
        tuple(sorted((name, str(digest)) for name, digest in published_hashes.items())),
    )


def fetch_push_runs(
    repository: str, commit_sha: str, get_json: Callable[[str], Mapping[str, Any]]
) -> list[Mapping[str, Any]]:
    """Every workflow run of ``commit_sha`` started by a push, from the GitHub API (network
    through ``get_json``, so tests run offline), reading every page. Errors propagate:
    missing evidence is never assumed."""
    if not REPOSITORY.fullmatch(repository):
        raise PublicationError("repository must be owner/name")
    if not re.fullmatch(r"[0-9a-f]{40}", commit_sha):
        raise PublicationError("the commit SHA must be 40 lowercase hex digits")
    runs: list[Mapping[str, Any]] = []
    total: int | None = None
    page = 1
    while True:
        data = get_json(
            f"https://api.github.com/repos/{repository}/actions/runs"
            f"?head_sha={commit_sha}&event=push&per_page={PER_PAGE}&page={page}"
        )
        batch = data.get("workflow_runs")
        count = data.get("total_count")
        if not isinstance(batch, list):
            raise PublicationError("the API answer has no workflow_runs")
        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            raise PublicationError("the API answer has no total_count")
        if total is None:
            total = count
        elif count != total:
            raise PublicationError("total_count changed while the pages were read")
        runs.extend(batch)
        if len(runs) >= total or not batch:
            break
        page += 1
    if len(runs) != total:
        raise PublicationError(f"read {len(runs)} runs, the API counts {total}")
    return runs
