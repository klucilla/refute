"""v0.5.4's candidate detached launcher (``launch_detached``; #217), offline: its pure checks and
its start sequence (claim the prefix, start the child suspended, record its identity, resume it;
on a failure after the start, end that child by its own handle), with a fake process. The real
start is observed by the restart probe, which writes only under ``.cache``."""

from __future__ import annotations

import sys
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
V054 = ROOT / "docs/validation/v0.5.4"
if str(V054) not in sys.path:
    sys.path.insert(0, str(V054))
import launch_detached  # noqa: E402


def test_the_mask_of_8_to_31():
    assert launch_detached._mask("8-31") == 0xFFFFFF00


@pytest.mark.parametrize("bad", ["31-8", "0-64", "-1-3"])
def test_a_bad_range_is_refused(bad):
    with pytest.raises((SystemExit, ValueError)):
        launch_detached._mask(bad)


def test_a_log_outside_the_project_is_refused(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    assert launch_detached._inside(root, ".cache/x/log") == (root / ".cache/x/log").resolve()
    for outside in ("../elsewhere/log", str(tmp_path / "elsewhere" / "log")):
        with pytest.raises(SystemExit, match="inside the project"):
            launch_detached._inside(root, outside)


def test_the_child_starts_suspended_and_broken_away():
    flags = launch_detached.FLAGS
    assert flags & 0x00000004  # CREATE_SUSPENDED: nothing runs before its identity is on file
    assert flags & 0x01000000  # CREATE_BREAKAWAY_FROM_JOB
    assert flags & 0x00000008 and flags & 0x00000200  # DETACHED_PROCESS, CREATE_NEW_PROCESS_GROUP


def test_the_record_is_written_atomically(tmp_path):
    path = tmp_path / "log.pid.json"
    launch_detached._write_atomic(path, '{"pid": 1}\n')
    assert path.read_text("utf-8") == '{"pid": 1}\n'
    assert not (tmp_path / "log.pid.json.tmp").exists()


class Child:
    """A fake process: records what happened to it."""

    started: list[Child] = []

    def __init__(self, argv, **kwargs):
        self.pid, self.argv, self.kwargs = 4242 + len(Child.started), argv, kwargs
        self.killed = self.waited = self.resumed = False
        Child.started.append(self)

    def kill(self):
        self.killed = True

    def wait(self, timeout=None):
        self.waited = True
        return 1


@pytest.fixture
def fake():
    Child.started = []
    return Child


def _start(log: Path, **over):
    def resume(pid):
        next(c for c in Child.started if c.pid == pid).resumed = True

    kw = dict(popen=Child, creation_time=lambda pid: 133_000_000_000_000_000 + pid, resume=resume)
    kw.update(over)
    return launch_detached.start(log, ["python", "probe.py"], {"script": "probe.py"}, **kw)


def test_the_identity_is_on_file_before_the_child_is_resumed(tmp_path, fake):
    log = tmp_path / "launch"
    seen = {}

    def resume(pid):
        seen["record"] = (tmp_path / "launch.pid.json").read_text("utf-8")
        fake.started[0].resumed = True

    record = _start(log, resume=resume)
    child = fake.started[0]
    assert child.kwargs["creationflags"] == launch_detached.FLAGS
    assert child.resumed and not child.killed
    assert f'"pid": {child.pid}' in seen["record"] and '"created": ' in seen["record"]
    assert record["pid"] == child.pid and record["created"] > 0
    assert (tmp_path / "launch.claim").exists()


@pytest.mark.parametrize("step", ["creation", "write", "resume"])
def test_a_failure_after_the_start_ends_the_child(tmp_path, fake, step):
    def boom(*a):
        raise OSError(f"{step} failed")

    over = {
        "creation": {"creation_time": boom},
        "write": {"write": boom},
        "resume": {"resume": boom},
    }[step]
    with pytest.raises(SystemExit, match="could not be secured"):
        _start(tmp_path / "launch", **over)
    child = fake.started[0]
    assert child.killed and child.waited and not child.resumed


def test_a_refused_breakaway_starts_nothing(tmp_path, fake):
    def refuse(*a, **k):
        raise PermissionError("access denied")

    with pytest.raises(SystemExit, match="breakaway was refused"):
        _start(tmp_path / "launch", popen=refuse)
    assert fake.started == []


def test_a_log_is_never_reused(tmp_path, fake):
    _start(tmp_path / "launch")
    with pytest.raises(SystemExit, match="never reused"):
        _start(tmp_path / "launch")
    assert len(fake.started) == 1


def test_two_concurrent_launchers_on_one_log_start_one_child(tmp_path, fake):
    barrier = threading.Barrier(2)
    results = []

    def one():
        barrier.wait()
        try:
            results.append(_start(tmp_path / "launch")["pid"])
        except SystemExit as exc:
            results.append(str(exc))

    threads = [threading.Thread(target=one) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(fake.started) == 1
    assert sorted(type(r).__name__ for r in results) == ["int", "str"]
    assert any("never reused" in str(r) for r in results)
