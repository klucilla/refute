"""The CI shards (scripts/ci_shard.py) cover every collected test exactly once."""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ci_shard", ROOT / "scripts" / "ci_shard.py")
shard = importlib.util.module_from_spec(spec)
sys.modules["ci_shard"] = shard
spec.loader.exec_module(shard)


def _collected_files() -> set[str]:
    """Files of every test item pytest collects from the full suite (no shard)."""
    argv = ["-m", "pytest", "--collect-only", "-q", "-o", "addopts=", "-p", "no:cacheprovider"]
    out = subprocess.run(
        [sys.executable, *argv],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return {line.split("::", 1)[0] for line in out.splitlines() if "::" in line}


def test_shards_are_consistent():
    shard.check()


def test_heavy_shards_run_exactly_their_lists():
    for name, files in shard.HEAVY.items():
        assert shard.args(name) == files


def test_every_collected_test_runs_in_exactly_one_shard():
    collected = _collected_files()
    heavy = [f for files in shard.HEAVY.values() for f in files]
    assert sorted(heavy) == sorted(set(heavy))  # no file in two heavy shards
    assert set(heavy) <= collected  # every heavy file has collected tests

    rest_args = shard.args("rest")
    assert rest_args[0] == "tests"
    ignored = {a.removeprefix("--ignore=") for a in rest_args if a.startswith("--ignore=")}
    assert ignored == set(heavy)
    # Every collected file is under tests/ (so the rest shard reaches it) and runs in
    # exactly one shard: a heavy list, or rest when it is in no heavy list.
    for f in collected:
        assert f.startswith("tests/"), f
        assert sum(f in files for files in shard.HEAVY.values()) + (f not in ignored) == 1, f


def test_unknown_shard_is_refused():
    with pytest.raises(SystemExit):
        shard.args("nope")
