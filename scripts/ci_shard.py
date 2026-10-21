"""Print the pytest arguments of one CI shard.

The test suite is split into shards that run as parallel CI jobs, on every OS and
Python of the matrix, so that each test still runs once per matrix entry while the
wall-clock time of a run falls (the end-to-end fixtures below take most of it).

- ``heavy-a``, ``heavy-b``, ``heavy-c``: fixed lists of end-to-end test files;
- ``rest``: every other test, with ``--ignore`` for each listed file.

Every listed file must exist (a renamed file fails the run instead of silently moving
to ``rest`` and running twice), and the lists may not overlap. ``check`` prints nothing
and exits 0 when the shards are consistent.

Limits to review if the configuration changes (issue #59; Codex review of PR #73):
``rest`` passes ``tests`` explicitly, so a new directory in ``testpaths`` of
``pyproject.toml`` would not be run by it; positional paths added to ``addopts`` would
also run in the heavy shards; and the CI splits the printed arguments on spaces, so a
test path with spaces or glob characters would need structured arguments.

Usage: uv run python scripts/ci_shard.py heavy-a|heavy-b|heavy-c|rest|check
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Measured on the main run of 2026-10-15 (ubuntu-24.04, Python 3.12): the fixtures of
# these files took about 1390 of the 1557 seconds of the test step. v0.2.1 reopening
# (2026-10-18): the correlated-noise cases and the v0.3 tests pushed windows-2025 /
# Python 3.13 rest to 1015 s and heavy-b to 943 s (PR #157, run 39085740367), over the
# 15-minute target; a fourth shard, heavy-c, balances them by the local times per file.
HEAVY = {
    "heavy-a": ["tests/test_ebcatalog_own_tic_e2e.py"],
    "heavy-b": [
        "tests/test_holdout_train_validity_e2e.py",
        "tests/test_holdout_blindness.py",
    ],
    "heavy-c": [
        "tests/test_workers_equivalence.py",
        "tests/test_calibration_signal_identity_e2e.py",
        "tests/test_wp4_papers.py",
        # stage 1, item D (2026-10-21): its fixtures took 150 s in rest (run 39627687323), and
        # heavy-c was the lightest shard (5 to 7 min)
        "tests/test_instrumentation.py",
    ],
}


def check() -> None:
    listed = [f for files in HEAVY.values() for f in files]
    if len(listed) != len(set(listed)):
        raise SystemExit("a test file is listed in two shards")
    for f in listed:
        if not (ROOT / f).is_file():
            raise SystemExit(f"listed test file not found: {f}")


def args(shard: str) -> list[str]:
    check()
    if shard in HEAVY:
        return HEAVY[shard]
    if shard == "rest":
        return ["tests"] + [f"--ignore={f}" for files in HEAVY.values() for f in files]
    raise SystemExit(f"unknown shard {shard!r}")


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else ""
    if name == "check":
        check()
    else:
        print(" ".join(args(name)))
