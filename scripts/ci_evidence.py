"""Test evidence of CI for one exact commit (Codex's blocking item 4 of the two-level CI round,
docs/plans/ci-two-level-consensus/). A run's green status alone is never evidence: a ``docs``,
``record-only`` or branch-creation run is green with no test job.

The evidence holds when one completed run of ``.github/workflows/ci.yml`` for the exact SHA has
every expected test job with conclusion ``success``:
- ``full``: the jobs ``<os> / Python <version> / <shard>`` of the four pairs and every shard of
  ``scripts/ci_shard.py`` (32 jobs with its eight shards since 2026-11-27; 28 with seven before);
- ``fast``: the jobs of the fast matrix (16 since 2026-11-27; 14 before) and the recorded-value
  jobs of the two other pairs.
Where a rule names a four-pair gate (a lock, a tag, a release, a dependency change, an acceptance
that names four green jobs), the level is ``full``, and the run must be on that commit before the
gated step: a run after a tag never satisfies a gate before the tag.

Usage: python scripts/ci_evidence.py <sha> --level full|fast [--repo owner/name]
It reads the GitHub API through ``gh api`` (network), prints the run it found and every missing
or failed job, and exits 0 only when the evidence holds.
"""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ".github/workflows/ci.yml"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def expected_jobs(level: str) -> set[str]:
    plan = _load("ci_plan")
    shards = [*_load("ci_shard").HEAVY, "rest"]
    if level == "full":
        pairs, extra = plan.FULL_PAIRS, ()
    elif level == "fast":
        pairs, extra = plan.FAST_PAIRS, plan.FAST_EXTRA_PAIRS
    else:
        raise ValueError(f"unknown level {level!r}")
    names = {f"{o} / Python {p} / {s}" for o, p in pairs for s in shards}
    names |= {f"{o} / Python {p} / recorded-values" for o, p in extra}
    return names


def evaluate(
    sha: str, runs: list[Mapping[str, Any]], jobs: Callable[[int], list[Mapping[str, Any]]], level
) -> tuple[bool, list[str]]:
    """``runs``: the workflow runs listed for the SHA; ``jobs(run_id)``: that run's jobs."""
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        return False, ["the SHA must be 40 lowercase hex digits"]
    want = expected_jobs(level)
    notes = []
    for run in sorted(runs, key=lambda r: str(r.get("created_at", ""))):
        if run.get("head_sha") != sha or run.get("path") != WORKFLOW_PATH:
            continue
        if run.get("status") != "completed":
            notes.append(f"run {run.get('id')}: not completed")
            continue
        got = {j.get("name"): j.get("conclusion") for j in jobs(int(run["id"]))}
        missing = sorted(want - set(got))
        failed = sorted(n for n in want & set(got) if got[n] != "success")
        if not missing and not failed:
            return True, [f"run {run['id']} ({run.get('event')}): {len(want)} jobs, all success"]
        notes.append(
            f"run {run.get('id')} ({run.get('event')}): {len(missing)} missing, "
            f"{len(failed)} not success" + (f", e.g. {(missing or failed)[0]}")
        )
    return False, notes or [f"no run of {WORKFLOW_PATH} for {sha}"]


def _gh(path: str) -> Any:
    return json.loads(subprocess.run(["gh", "api", path], capture_output=True, check=True).stdout)


def main(argv: list[str]) -> int:
    if len(argv) < 3 or argv[1] != "--level":
        print(__doc__)
        return 2
    sha, level = argv[0], argv[2]
    repo = argv[argv.index("--repo") + 1] if "--repo" in argv else "klucilla/refute"
    data = _gh(f"repos/{repo}/actions/workflows/ci.yml/runs?head_sha={sha}&per_page=100")
    runs = data.get("workflow_runs", [])

    def jobs(run_id: int) -> list[Mapping[str, Any]]:
        out, page = [], 1
        while True:
            batch = _gh(f"repos/{repo}/actions/runs/{run_id}/jobs?per_page=100&page={page}")
            out += batch.get("jobs", [])
            if len(out) >= batch.get("total_count", 0) or not batch.get("jobs"):
                return out
            page += 1

    ok, notes = evaluate(sha, runs, jobs, level)
    print("\n".join(notes))
    print("evidence holds" if ok else "NO EVIDENCE")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
