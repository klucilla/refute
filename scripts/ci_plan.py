"""Which CI matrix a workflow run gets (the two-level CI; the maintainer's decision of 2026-11-24,
#218 comment 7133936093, item 2, with the blocking items of Codex's round applied:
docs/plans/ci-two-level-consensus/). Standard library only: it runs in the workflow's ``plan``
job, which has no trigger-level path filter, so this script is the only path classifier.

Levels:
- ``full``: the four pairs (ubuntu-24.04 and windows-2025, each with Python 3.12.15 and 3.13.16),
  every shard. For a scheduled (nightly) run, a manual run (``workflow_dispatch``), the creation
  of a tag (``create``), a push that is not a fast-forward, and a push or pull request in which
  any commit touches a path of the full matrix (``FULL_PREFIXES``, ``FULL_FILES``).
- ``fast``: two pairs, ubuntu-24.04 with Python 3.12.15 and windows-2025 with Python 3.13.16,
  every shard; plus the recorded-value tests (``RECORDED_VALUE_TESTS``) on the two other pairs,
  because docs/validation/v0.3/wp3-acceptance.md (line 393) requires them on every CI job.
- ``docs``: no test job, when every touched path is documentation that no test, lint step or
  build reads (``DOCS_ONLY``, the former ``paths-ignore`` list). The run still exists.
- ``record-only``: no test job, for a push to main whose head commit message has the trailer line
  ``ORDER_PROOF`` exactly, which adds one non-merge commit by fast-forward, and touches no code
  path (``CODE_PREFIXES``, ``CODE_FILES``, ``*.py``) and no path of the full matrix. The run exists
  only so that the push has a run of ``ci.yml`` whose ``created_at`` proves when it was pushed
  (``refute.selection.publication``, ``refute.packs.tess.discover.pilot.push_run_created_at``).
  GitHub's own ``[skip ci]`` is not used for those pushes: it creates no run at all.
- ``none``: no test job, for the creation of a branch.

Anything this script cannot decide (no previous commit, a git error, an unknown event) gives
``full``.

Usage (in the workflow): ``python3 scripts/ci_plan.py``, with the environment variables EVENT,
REF_TYPE, SHA, BEFORE, PR_BASE, PR_HEAD and MESSAGE. It writes ``level``, ``reason``, ``pairs``
and ``extra_pairs`` to $GITHUB_OUTPUT when it is set, and prints them.
"""

from __future__ import annotations

import fnmatch
import json
import os
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass

FULL_PAIRS = (
    ("ubuntu-24.04", "3.12.15"),
    ("ubuntu-24.04", "3.13.16"),
    ("windows-2025", "3.12.15"),
    ("windows-2025", "3.13.16"),
)
FAST_PAIRS = (("ubuntu-24.04", "3.12.15"), ("windows-2025", "3.13.16"))
FAST_EXTRA_PAIRS = tuple(p for p in FULL_PAIRS if p not in FAST_PAIRS)
# the tests whose recorded values every CI job must reproduce (wp3-acceptance.md, line 393;
# tests/test_ml_schema.py, test_recorded_derived_values_are_exact; tests/test_ml_papers.py)
RECORDED_VALUE_TESTS = (
    "tests/test_ml_schema.py",
    "tests/test_ml_papers.py",
    "tests/test_ml_data_sources.py",
)
FULL_PREFIXES = ("src/", "calibration/", ".github/workflows/")
FULL_FILES = ("pyproject.toml", "uv.lock")
CODE_PREFIXES = ("src/", "scripts/", "tests/", "calibration/", ".github/")
CODE_FILES = ("pyproject.toml", "uv.lock", ".python-version", ".gitattributes")
DOCS_ONLY = (
    "docs/**/*.md",
    "docs/*.md",
    "docs/assets/*.svg",
    "docs/assets/*.png",
    "CLAUDE.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "PROMPT-v0.1.md",
    "ROADMAP.md",
    "SECURITY.md",
    # v0.5.13's data records (#218, the maintainer's decision J3, comment 7222879969): no test,
    # lint step or build reads a .json or .jsonl file of this folder (checked by a search of
    # tests/ and scripts/ on 2026-11-27); its tools/*.py stay code. A test that starts reading one
    # of these files must remove the pattern first.
    "docs/validation/v0.5.13/*.json",
    "docs/validation/v0.5.13/*.jsonl",
)
ORDER_PROOF = "CI: order-proof"


@dataclass(frozen=True)
class Plan:
    level: str
    reason: str

    @property
    def pairs(self) -> list[dict[str, str]]:
        chosen = {"full": FULL_PAIRS, "fast": FAST_PAIRS}.get(self.level, ())
        return [{"os": o, "python": p} for o, p in chosen]

    @property
    def extra_pairs(self) -> list[dict[str, str]]:
        chosen = FAST_EXTRA_PAIRS if self.level == "fast" else ()
        return [{"os": o, "python": p} for o, p in chosen]


@dataclass(frozen=True)
class Change:
    """What a push or pull request changes: every path touched by any of its commits (so an edit
    reverted within the batch still counts), whether it is a fast-forward, how many commits it
    adds, and whether its head is a merge."""

    paths: tuple[str, ...]
    fast_forward: bool = True
    commits: int = 1
    head_is_merge: bool = False


def touches_full(paths) -> list[str]:
    return [f for f in paths if f in FULL_FILES or f.startswith(FULL_PREFIXES)]


def touches_code(paths) -> list[str]:
    return [f for f in paths if f in CODE_FILES or f.startswith(CODE_PREFIXES) or f.endswith(".py")]


def docs_only(paths) -> bool:
    def doc(f: str) -> bool:
        return any(fnmatch.fnmatchcase(f, pat) for pat in DOCS_ONLY) and not f.startswith(
            CODE_PREFIXES
        )

    return bool(paths) and all(doc(f) for f in paths)


def has_order_proof(message: str) -> bool:
    return any(line.strip() == ORDER_PROOF for line in (message or "").splitlines())


def _unknown(sha: str | None) -> bool:
    return not sha or set(sha) == {"0"}


def plan(
    event: str,
    ref_type: str,
    sha: str,
    before: str,
    pr_base: str,
    pr_head: str,
    message: str,
    read: Callable[[str, str, bool], Change],
) -> Plan:
    """``read(a, b, merge_base)``: the change from a to b (for a pull request, from their merge
    base). It may raise; an error gives ``full``."""
    if event == "schedule":
        return Plan("full", "the nightly run")
    if event == "workflow_dispatch":
        return Plan("full", "a manual run")
    if event == "create":
        if ref_type == "tag":
            return Plan("full", "a tag was created")
        return Plan("none", "a branch was created")
    if event not in ("push", "pull_request"):
        return Plan("full", f"event {event!r}")
    a, b = (before, sha) if event == "push" else (pr_base, pr_head)
    if _unknown(a) or _unknown(b):
        return Plan("full", "no previous commit to compare with")
    try:
        change = read(a, b, event == "pull_request")
    except Exception as exc:  # noqa: BLE001 - any failure means: test everything
        return Plan("full", f"the change could not be read ({type(exc).__name__})")
    if event == "push" and not change.fast_forward:
        return Plan("full", "the push is not a fast-forward")
    full = touches_full(change.paths)
    if event == "push" and has_order_proof(message):
        code = full or touches_code(change.paths)
        if code:
            level = "full" if full else "fast"
            return Plan(level, f"order-proof trailer ignored: it touches {code[0]}")
        if change.commits != 1 or change.head_is_merge:
            return Plan("fast", "order-proof trailer ignored: not one non-merge commit")
        return Plan("record-only", "an order-proof push: the run records the push time")
    if full:
        return Plan("full", f"a commit touches {full[0]}")
    if docs_only(change.paths):
        return Plan("docs", "every touched path is documentation that no test reads")
    return Plan("fast", "no path of the full matrix is touched")


def _split(out: bytes) -> list[str]:
    return [p.decode("utf-8", errors="surrogateescape") for p in out.split(b"\0") if p]


def git_change(a: str, b: str, merge_base: bool, cwd: str | None = None) -> Change:
    """Read the change from a to b with git (NUL-separated paths, no renames)."""

    def git(*args: str) -> bytes:
        return subprocess.run(["git", *args], capture_output=True, check=True, cwd=cwd).stdout

    start = git("merge-base", a, b).decode().strip() if merge_base else a
    fast_forward = (
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", a, b], capture_output=True, cwd=cwd
        ).returncode
        == 0
    )
    if not fast_forward and not merge_base:
        return Change((), fast_forward=False)
    paths = set(_split(git("diff", "--name-only", "--no-renames", "-z", start, b)))
    paths |= set(
        _split(git("log", "--format=", "--name-only", "--no-renames", "-m", "-z", f"{start}..{b}"))
    )
    commits = int(git("rev-list", "--count", f"{start}..{b}").decode().strip())
    parents = git("rev-list", "--parents", "-n", "1", b).decode().split()
    return Change(tuple(sorted(paths)), fast_forward, commits, len(parents) > 2)


def main() -> None:
    env = os.environ
    p = plan(
        env.get("EVENT", ""),
        env.get("REF_TYPE", ""),
        env.get("SHA", ""),
        env.get("BEFORE", ""),
        env.get("PR_BASE", ""),
        env.get("PR_HEAD", ""),
        env.get("MESSAGE", ""),
        git_change,
    )
    lines = [
        f"level={p.level}",
        f"reason={p.reason}",
        f"pairs={json.dumps(p.pairs)}",
        f"extra_pairs={json.dumps(p.extra_pairs)}",
    ]
    print("\n".join(lines))
    out = env.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    sys.exit(main())
