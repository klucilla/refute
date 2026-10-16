"""ML pack runner, part 1: metric extraction (W3.11, W3.12) and the subprocess backend
(W3.8 to W3.10), offline. Every run of the backend is the cataloged synthetic fixture
``sandbox-probe`` (tests/fixtures/sandbox/probe.py), written by the harness and run by this
interpreter (the project's virtual environment); the backend refuses anything else."""

import json
import os
import sys
import time
from decimal import Decimal

import pytest

from refute.packs.ml import extract as ex
from refute.packs.ml import sandbox as sb
from synthetic_harness import fixture

# ---- extraction ----------------------------------------------------------------------------


def regex(pattern, group=1):
    return {"from": "log", "regex": {"pattern": pattern, "group": group}}


def test_regex_on_the_log_keeps_the_token_text(tmp_path):
    got = ex.extract(regex(r"acc=([0-9.]+)"), tmp_path, "epoch 3\nacc=91.20\n", None)
    assert (got.token, got.value, got.source) == ("91.20", Decimal("91.20"), "log")
    named = ex.extract(regex(r"acc=(?P<v>[0-9.]+)", "v"), tmp_path, "acc=0.5", None)
    assert named.token == "0.5"


@pytest.mark.parametrize(
    ("log", "reason"),
    [
        ("no metric here", "matched 0 times"),
        ("acc=1.0\nacc=2.0\n", "matched 2 times"),
        ("acc=nan", "matched 0 times"),
    ],
)
def test_regex_must_match_exactly_once(tmp_path, log, reason):
    with pytest.raises(ex.ExtractionError, match=reason):
        ex.extract(regex(r"acc=([0-9.]+)"), tmp_path, log, None)


def test_regex_group_must_exist_and_hold_a_number(tmp_path):
    with pytest.raises(ex.ExtractionError, match="no group"):
        ex.extract(regex(r"acc=([0-9.]+)", 2), tmp_path, "acc=1.0", None)
    with pytest.raises(ex.ExtractionError, match="not a finite decimal"):
        ex.extract(regex(r"acc=(\S+)"), tmp_path, "acc=inf", None)


def test_json_path_on_a_file_with_the_seed(tmp_path):
    (tmp_path / "out").mkdir()
    (tmp_path / "out" / "m-7.json").write_text('{"test": {"acc": 91.20, "runs": [0.5, 0.25]}}')
    spec = {"from": "file", "file": "out/m-{seed}.json", "json_path": "$.test.acc"}
    got = ex.extract(spec, tmp_path, "", 7)
    assert got.token == "91.20" and got.source == "file:out/m-7.json"
    spec["json_path"] = "$.test.runs[1]"
    assert ex.extract(spec, tmp_path, "", 7).token == "0.25"


@pytest.mark.parametrize(
    ("document", "path", "reason"),
    [
        ('{"a": 1}', "$.b", "no key"),
        ('{"a": [1]}', "$.a[3]", "no index"),
        ('{"a": "91.2"}', "$.a", "not a number"),
        ('{"a": true}', "$.a", "not a number"),
        ('{"a": NaN}', "$.a", "not valid JSON"),
        ('{"a": 1}', "$..a", "unsupported step"),
        ('{"a": 1}', "$", "whole document"),
        ('{"a": 1}', "a", "must start with"),
    ],
)
def test_json_path_failures(tmp_path, document, path, reason):
    (tmp_path / "m.json").write_text(document)
    with pytest.raises(ex.ExtractionError, match=reason):
        ex.extract({"from": "file", "file": "m.json", "json_path": path}, tmp_path, "", None)


def test_csv_column_of_the_single_matching_row(tmp_path):
    (tmp_path / "r.csv").write_text("split,acc\ntrain,99.0\ntest,91.2\n")
    spec = {
        "from": "file",
        "file": "r.csv",
        "csv": {"column": "acc", "row": {"column": "split", "equals": "test"}},
    }
    assert ex.extract(spec, tmp_path, "", None).token == "91.2"
    (tmp_path / "r.csv").write_text("split,acc\ntest,91.2\ntest,90.0\n")
    with pytest.raises(ex.ExtractionError, match="2 rows"):
        ex.extract(spec, tmp_path, "", None)
    spec["csv"]["column"] = "f1"
    with pytest.raises(ex.ExtractionError, match="no column"):
        ex.extract(spec, tmp_path, "", None)


def test_ambiguous_documents_are_refused(tmp_path):
    """Codex review: a repeated JSON key or CSV column would let a parser choose."""
    (tmp_path / "m.json").write_text('{"a": 1, "a": 2}')
    with pytest.raises(ex.ExtractionError, match="repeated"):
        ex.extract({"from": "file", "file": "m.json", "json_path": "$.a"}, tmp_path, "", None)
    (tmp_path / "r.csv").write_text("split,acc,acc\ntest,1,2\n")
    spec = {
        "from": "file",
        "file": "r.csv",
        "csv": {"column": "acc", "row": {"column": "split", "equals": "test"}},
    }
    with pytest.raises(ex.ExtractionError, match="repeats the columns"):
        ex.extract(spec, tmp_path, "", None)
    (tmp_path / "r.csv").write_text("split,acc\ntest\n")
    with pytest.raises(ex.ExtractionError, match="fields"):
        ex.extract(spec, tmp_path, "", None)


def test_the_json_token_is_kept_literally(tmp_path):
    (tmp_path / "m.json").write_text('{"a": 1e-2, "b": 91.20, "c": 7}')
    for path, token in (("$.a", "1e-2"), ("$.b", "91.20"), ("$.c", "7")):
        spec = {"from": "file", "file": "m.json", "json_path": path}
        assert ex.extract(spec, tmp_path, "", None).token == token


def test_file_errors(tmp_path):
    spec = {"from": "file", "file": "missing.json", "json_path": "$.a"}
    with pytest.raises(ex.ExtractionError, match="cannot read"):
        ex.extract(spec, tmp_path, "", None)
    with pytest.raises(ex.ExtractionError, match="without '..'"):
        ex.extract(dict(spec, file="../x.json"), tmp_path, "", None)
    with pytest.raises(ex.ExtractionError, match="has no seed"):
        ex.extract(dict(spec, file="m-{seed}.json"), tmp_path, "", None)
    with pytest.raises(ex.ExtractionError, match="exactly one"):
        ex.extract(
            {"from": "log", "json_path": "$.a", "regex": {"pattern": "x", "group": 0}},
            tmp_path,
            "",
            None,
        )


# ---- subprocess backend ----------------------------------------------------------------------


@pytest.fixture
def probe(tmp_path):
    """The cataloged fixture ``sandbox-probe`` in its own folder, and a backend that runs
    only it."""
    auth = fixture("sandbox-probe", tmp_path / "fixture")
    return auth, sb.SubprocessBackend([auth])


def probe_argv(*args):
    return [sys.executable, "-I", "probe.py", *args]


def spec(auth, argv, **kw):
    values = dict(
        argv=argv,
        workdir=auth.root,
        env=dict(os.environ),
        log_path=auth.root.parent / "logs" / "run.log",
        threshold_usec=None,
        active_time_limit_s=60.0,
        no_progress_s=30.0,
        poll_s=0.05,
    )
    values.update(kw)
    return sb.RunSpec(**values)


def test_a_run_writes_its_log_and_exit_code(probe):
    auth, backend = probe
    result = backend.run(spec(auth, probe_argv("exit", "3")))
    assert result.exit_code == 3 and result.stopped is None
    assert "acc=91.2" in result.log_path.read_text()
    assert type(result.usage_usec) is int and result.usage_usec >= 0


def test_the_cpu_of_children_and_grandchildren_is_counted(probe):
    auth, backend = probe
    # a child that starts a busy grandchild, then a second busy child
    result = backend.run(spec(auth, probe_argv("tree", "0.6")))
    assert result.exit_code == 0 and result.stopped is None
    assert result.usage_usec >= 1_000_000  # at least the two busy descendants


def test_the_threshold_stops_the_whole_run(probe):
    auth, backend = probe
    result = backend.run(spec(auth, probe_argv("wait", "busy", "30"), threshold_usec=400_000))
    assert result.stopped == sb.STOP_THRESHOLD and result.exit_code is None
    assert 400_000 <= result.usage_usec < 10_000_000
    assert result.elapsed_s < 20


def test_no_process_of_the_run_survives_the_stop(probe):
    """Codex review: the stop and the final reading cover every descendant."""
    auth, backend = probe
    beat = auth.root / "out" / "beat.txt"
    beat.parent.mkdir()
    argv = probe_argv("wait", "beat", "out/beat.txt", "30")
    result = backend.run(spec(auth, argv, threshold_usec=300_000))
    assert result.stopped == sb.STOP_THRESHOLD
    size = beat.stat().st_size
    time.sleep(1.0)
    assert beat.stat().st_size == size  # the grandchild no longer writes


def test_a_finished_run_leaves_no_descendant(probe):
    auth, backend = probe
    beat = auth.root / "out" / "tick.txt"
    beat.parent.mkdir()
    # the first process starts a child and exits at once, leaving it behind
    result = backend.run(spec(auth, probe_argv("detach", "tick", "out/tick.txt")))
    assert result.exit_code == 0
    size = beat.stat().st_size if beat.exists() else 0
    time.sleep(1.0)
    assert (beat.stat().st_size if beat.exists() else 0) == size


def test_no_progress_stops_a_silent_idle_run(probe):
    auth, backend = probe
    result = backend.run(spec(auth, probe_argv("idle", "30"), no_progress_s=1.0))
    assert result.stopped == sb.STOP_NO_PROGRESS and result.elapsed_s < 15


def test_the_active_time_limit_stops_a_run_that_keeps_printing(probe):
    auth, backend = probe
    result = backend.run(
        spec(auth, probe_argv("chatty"), active_time_limit_s=1.5, no_progress_s=1.0)
    )
    assert result.stopped == sb.STOP_ACTIVE_TIME and result.elapsed_s < 15


@pytest.mark.parametrize(
    "bad",
    [
        dict(argv=[]),
        dict(argv="python x.py"),
        dict(threshold_usec=0),
        dict(threshold_usec=1.5),
        dict(active_time_limit_s=0),
        dict(active_time_limit_s=float("inf")),
        dict(no_progress_s=float("nan")),
    ],
)
def test_invalid_specs(tmp_path, bad):
    values = {"argv": ["x"], **bad}
    argv = values.pop("argv")
    defaults = dict(
        workdir=tmp_path,
        env={},
        log_path=tmp_path / "run.log",
        threshold_usec=None,
        active_time_limit_s=60.0,
        no_progress_s=30.0,
    )
    with pytest.raises(ValueError):
        sb.RunSpec(argv=argv, **{**defaults, **values})


def test_extraction_from_a_real_run(probe):
    auth, backend = probe
    result = backend.run(spec(auth, probe_argv("train", "4")))
    assert result.exit_code == 0
    log = result.log_path.read_text()
    by_log = ex.extract(regex(r"final acc=([0-9.]+)"), auth.root, log, 4)
    by_file = ex.extract(
        {"from": "file", "file": "out/m-{seed}.json", "json_path": "$.test.acc"},
        auth.root,
        log,
        4,
    )
    assert by_log.value == by_file.value == Decimal("91.25")
    assert json.loads((auth.root / "out" / "m-4.json").read_text())["test"]["acc"] == 91.25
