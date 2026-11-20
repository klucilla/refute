"""v0.5.5: the ledger's one pre-approved resume, counted by recorded starts, its cumulative cap,
and its lock (``docs/validation/v0.5.5/ledger_v055.py``), on a temporary ledger and a temporary
lock; the real ones are not touched, and ``budgeted``'s module constants are restored after the
test."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT / "docs/validation/v0.5.2/stage2", ROOT / "docs/validation/v0.5.5"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import budgeted  # noqa: E402


@pytest.fixture
def lv(tmp_path, monkeypatch):
    for name in ("LEDGER", "LINES", "HARD_MAXIMUM", "SPENT_BEFORE", "save"):
        monkeypatch.setattr(budgeted, name, getattr(budgeted, name))  # restored at teardown
    import ledger_v055

    monkeypatch.setattr(ledger_v055, "HERE", tmp_path)
    monkeypatch.setattr(ledger_v055, "LOCK", tmp_path / "ledger.lock")
    monkeypatch.setattr(budgeted, "LEDGER", tmp_path / "ledger.json")
    monkeypatch.setattr(budgeted, "LINES", {"v055": ledger_v055.LINE_HOURS - 0.5})
    monkeypatch.setattr(budgeted, "HARD_MAXIMUM", ledger_v055.LINE_HOURS)
    monkeypatch.setattr(budgeted, "SPENT_BEFORE", 0.0)
    monkeypatch.setattr(budgeted, "save", ledger_v055._atomic_save)
    ledger_v055.declare()
    return ledger_v055


def test_the_lock_is_the_temporary_one(lv, tmp_path):
    with lv.Exclusive("probe") as ex:
        assert ex.path == tmp_path / "ledger.lock" and ex.path.exists()
    assert not (tmp_path / "ledger.lock").exists()


def test_the_allocations_fill_the_64_cpu_hour_line(lv):
    assert sum(lv.ALLOCATIONS.values()) + lv.CHARGES_ROOM == pytest.approx(lv.LINE_HOURS)
    assert lv.LINE_HOURS == pytest.approx(0.8 * lv.CAP_HOURS)


def test_one_resume_only_counted_by_starts(lv):
    rows = [("a", {"i": 0})]
    with lv.Exclusive("test"):
        assert lv.check_run("r1_t2ae_1", "fp1", rows) == 0
        assert lv.record_start("r1_t2ae_1", "fp1", rows) == 0  # a first run
        # an interruption before any consumption is still a start: the next run is the resume
        assert lv.record_start("r1_t2ae_1", "fp1", rows) == 1
        with pytest.raises(SystemExit, match="one pre-approved resume"):
            lv.check_run("r1_t2ae_1", "fp1", rows)
        with pytest.raises(SystemExit, match="another identity"):
            lv.check_run("r1_t2ae_1", "fp2", rows)


def test_the_cap_is_cumulative_over_the_identity(lv):
    book = budgeted.load()
    book["sections"][lv.SECTION]["parts"]["r1_t2ae_1"]["spent_hours"] = 2.0
    budgeted.save(book)
    # the allocation less archived attempts (none): the driver compares it with the
    # identity's whole consumption, so the 2.0 already spent is not subtracted again
    want = lv.ALLOCATIONS["r1_t2ae_1"] / lv.OVERSHOOT
    assert lv.hard_cap("r1_t2ae_1", 10, 1200.0) == pytest.approx(want)


def _lock_text(pid: int, stamp: str) -> str:
    return f"pid {pid}; a step; {stamp}\n"


@pytest.mark.skipif(sys.platform != "win32", reason="the process check uses the Windows API")
def test_a_stale_lock_is_removed_and_recorded(lv, tmp_path, monkeypatch):
    import os

    monkeypatch.setattr(lv, "STALE_LOG", tmp_path / "stale.jsonl")
    lock = tmp_path / "ledger.lock"
    # a PID no process has (Windows PIDs are multiples of 4, so this one never exists)
    lock.write_text(_lock_text(4_294_967, "2026-11-20T00:00:00Z"), "utf-8")
    with lv.Exclusive("test") as ex:
        assert ex.path == lock and lock.read_text("utf-8").startswith(f"pid {os.getpid()};")
    assert not lock.exists()
    assert "4294967" in (tmp_path / "stale.jsonl").read_text("utf-8")


@pytest.mark.skipif(sys.platform != "win32", reason="the process check uses the Windows API")
def test_a_live_lock_is_kept(lv, tmp_path, monkeypatch):
    import os

    monkeypatch.setattr(lv, "STALE_LOG", tmp_path / "stale.jsonl")
    lock = tmp_path / "ledger.lock"
    # this process, which started before a lock stamped now: alive, so the lock is kept
    lock.write_text(_lock_text(os.getpid(), "2099-01-01T00:00:00Z"), "utf-8")
    with pytest.raises(SystemExit, match="is held"):
        with lv.Exclusive("test"):
            pass
    assert lock.exists() and not (tmp_path / "stale.jsonl").exists()
    # the same PID with a stamp before this process started: a reused PID, so the lock is stale
    lock.write_text(_lock_text(os.getpid(), "2000-01-01T00:00:00Z"), "utf-8")
    assert lv.release_stale(lock) and not lock.exists()


def test_an_unreadable_lock_is_kept(lv, tmp_path, monkeypatch):
    monkeypatch.setattr(lv, "STALE_LOG", tmp_path / "stale.jsonl")
    lock = tmp_path / "ledger.lock"
    lock.write_text("something else\n", "utf-8")
    assert not lv.release_stale(lock) and lock.exists()


def test_the_guard_excludes_a_concurrent_acquisition_during_recovery(lv, tmp_path, monkeypatch):
    """During the recovery, a second, independent opening of the guard file, in the same process,
    cannot take the guard already held. This test does not run two processes concurrently (Codex,
    night round 2): the exclusion between processes rests on the operating system's primitive."""
    import os

    monkeypatch.setattr(lv, "STALE_LOG", tmp_path / "stale.jsonl")
    lock = tmp_path / "ledger.lock"
    lock.write_text(_lock_text(1, "2026-11-20T00:00:00Z"), "utf-8")
    seen = {}

    def dead(pid, stamp):
        fd = os.open(lock.with_name(lock.name + ".guard"), os.O_RDWR)
        try:
            seen["second_took_the_guard"] = lv._try_lock(fd)
        finally:
            os.close(fd)
        return False

    monkeypatch.setattr(lv, "_process_started_before", dead)
    assert lv.release_stale(lock)
    assert seen["second_took_the_guard"] is False
    assert not lock.exists()
    assert '"removed": true' in (tmp_path / "stale.jsonl").read_text("utf-8")


def test_a_lock_whose_identity_changed_is_kept(lv, tmp_path, monkeypatch):
    monkeypatch.setattr(lv, "STALE_LOG", tmp_path / "stale.jsonl")
    lock = tmp_path / "ledger.lock"
    lock.write_text(_lock_text(1, "2026-11-20T00:00:00Z"), "utf-8")

    def dead_but_replaced(pid, stamp):
        lock.write_text(_lock_text(2, "2026-11-20T00:00:01Z"), "utf-8")
        return False

    monkeypatch.setattr(lv, "_process_started_before", dead_but_replaced)
    assert not lv.release_stale(lock)
    assert lock.exists() and not (tmp_path / "stale.jsonl").exists()


def test_a_release_removes_only_its_own_instance(lv, tmp_path):
    lock = tmp_path / "ledger.lock"
    with pytest.raises(SystemExit, match="not this process's lock"):
        with lv.Exclusive("test"):
            lock.write_text(_lock_text(2, "2026-11-20T00:00:01Z"), "utf-8")
    assert lock.exists()
    lock.unlink()
    lv._held.pop(lock, None)


def test_a_live_process_keeps_its_lock_on_any_platform(lv, tmp_path, monkeypatch):
    monkeypatch.setattr(lv, "STALE_LOG", tmp_path / "stale.jsonl")
    lock = tmp_path / "ledger.lock"
    lock.write_text(_lock_text(1, "2026-11-20T00:00:00Z"), "utf-8")
    for answer in (True, None):
        monkeypatch.setattr(lv, "_process_started_before", lambda pid, stamp, a=answer: a)
        with pytest.raises(SystemExit, match="is held"):
            with lv.Exclusive("test"):
                pass
        assert lock.exists()
