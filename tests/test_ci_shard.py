"""The CI shards (scripts/ci_shard.py) cover every test file exactly once."""

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ci_shard", ROOT / "scripts" / "ci_shard.py")
shard = importlib.util.module_from_spec(spec)
sys.modules["ci_shard"] = shard
spec.loader.exec_module(shard)


def test_shards_are_consistent():
    shard.check()


def test_every_test_file_runs_in_exactly_one_shard():
    every = {p.relative_to(ROOT).as_posix() for p in (ROOT / "tests").glob("test_*.py")}
    heavy = [f for files in shard.HEAVY.values() for f in files]
    rest_args = shard.args("rest")
    ignored = {a.removeprefix("--ignore=") for a in rest_args if a.startswith("--ignore=")}
    assert rest_args[0] == "tests"
    assert ignored == set(heavy)
    assert set(heavy) <= every
    rest = every - ignored
    assert rest and not rest & set(heavy)
    assert sorted(heavy) == sorted(set(heavy))  # no file in two shards


def test_unknown_shard_is_refused():
    import pytest

    with pytest.raises(SystemExit):
        shard.args("nope")
