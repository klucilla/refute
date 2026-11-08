"""Print the pytest arguments of one CI shard.

The test suite is split into shards that run as parallel CI jobs, on every OS and
Python of the matrix, so that each test still runs once per matrix entry while the
wall-clock time of a run falls (the end-to-end fixtures below take most of it).

- ``heavy-a`` to ``heavy-f``: fixed lists of slow test files;
- ``rest``: every other test, with ``--ignore`` for each listed file.

Every listed file must exist (a renamed file fails the run instead of silently moving
to ``rest`` and running twice), and the lists may not overlap. ``check`` prints nothing
and exits 0 when the shards are consistent.

Limits to review if the configuration changes (issue #59; Codex review of PR #73):
``rest`` passes ``tests`` explicitly, so a new directory in ``testpaths`` of
``pyproject.toml`` would not be run by it; positional paths added to ``addopts`` would
also run in the heavy shards; and the CI splits the printed arguments on spaces, so a
test path with spaces or glob characters would need structured arguments.

Usage: uv run python scripts/ci_shard.py heavy-a|...|heavy-f|rest|check
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
    # v0.5.1 (#210): run 42279642640 reached 29.5 min after the v0.5.1 tests entered rest;
    # test_v051_wp2 (196 s locally) joins the lightest heavy shard (heavy-a, 138 s)
    # v0.5.1 WP5 row 5.4 (#210): the packaging rehearsal (about 300 s locally with parallel
    # workers) joins heavy-a, the lightest shard (about 334 s locally)
    "heavy-a": [
        "tests/test_ebcatalog_own_tic_e2e.py",
        "tests/test_v051_wp2.py",
        "tests/test_v051_rehearsal.py",
    ],
    # stage 1, X1b (2026-10-21): the 32 engine controls of spec B pushed heavy-a to 15.6 and
    # 22.3 min on windows-2025 (run 39696817920, from 11.9 before); they now run in parallel
    # workers and in a shard of their own
    # v0.5.1 WP4 and WP5 (#210): their analyzer runs and byte fixtures (about 140 s and 400 s
    # locally) join heavy-d, the lightest shard of run 42344929297 (4.1 to 7.0 min)
    "heavy-d": [
        "tests/test_spec_b.py",
        "tests/test_x2.py",
        "tests/test_v051_wp4.py",
        "tests/test_v051_wp5.py",
    ],
    "heavy-b": [
        "tests/test_holdout_train_validity_e2e.py",
        "tests/test_holdout_blindness.py",
        # v0.5.1 amendment 9 (#210): the duration_excess tests (about 90 s locally, one full
        # version-3 analysis) join heavy-b, among the lightest shards of run 42401264680
        "tests/test_v051_duration.py",
        # v0.5.2 (#210, the maintainer's decision of 2026-11-08 on #216): the WP3 (b) proof (373 s
        # locally) leaves rest, which reached 37 min after it entered
        "tests/test_v051_accept_wp3b_series.py",
    ],
    "heavy-c": [
        "tests/test_workers_equivalence.py",
        "tests/test_calibration_signal_identity_e2e.py",
        "tests/test_wp4_papers.py",
        # stage 1, item D (2026-10-21): its fixtures took 150 s in rest (run 39627687323), and
        # heavy-c was the lightest shard (5 to 7 min)
        "tests/test_instrumentation.py",
        # v0.5.2 (#210, the maintainer's decision of 2026-11-08 on #216): 167 s locally
        "tests/test_population_v3_identity.py",
    ],
    # v0.5.1 WP6 (#210): CI run 42213700298 (job times read from the GitHub API on 2026-11-06,
    # https://github.com/klucilla/refute/actions/runs/42213700298) took up to 60 min for rest
    # (windows-2025, Python
    # 3.13); its slowest files move to two new shards, balanced by the local times per file of
    # the final v0.5 suite's JUnit XML (rest about 2385 s before; about 750, 810 and 826 s after)
    "heavy-e": [
        "tests/test_rmin_derivation.py",
        "tests/test_rednoise_propagation.py",
        "tests/test_capacity_plan.py",
        "tests/test_v05_paired.py",
    ],
    "heavy-f": [
        "tests/test_v04_discover_run.py",
        "tests/test_prewhiten.py",
        "tests/test_holdout_capacity.py",
        "tests/test_v05_centroid.py",
        "tests/test_v05_battery.py",
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
