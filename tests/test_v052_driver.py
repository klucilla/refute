"""The stage-2 batch driver (#216, the maintainer's items 8 and 10): resume, atomic shards, the
worker rule, the cap and the pause. Offline, with synthetic shards."""

from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
STAGE2 = ROOT / "docs/validation/v0.5.2/stage2"
sys.path.insert(0, str(STAGE2))
import driver  # noqa: E402

# the placement rule is the maintainer's machine's; a CI runner has no processors 8 to 31
PLACED = (os.cpu_count() or 0) >= 32
SHARDS = [(f"s{i:03d}", i) for i in range(24)]


def job(i: int) -> bytes:
    """A deterministic result that depends on its seed only; shard 5 records an error outcome."""
    if i == 5:
        return json.dumps({"shard": i, "status": "ERROR"}, sort_keys=True).encode() + b"\n"
    rng = np.random.default_rng([20261108, i])
    total = 0.0
    for _ in range(60):
        total += float(np.linalg.norm(rng.normal(size=(150, 150))))
    return json.dumps({"shard": i, "value": total}, sort_keys=True).encode() + b"\n"


def spin(seconds: float) -> bytes:
    """Burn processor time for about the given seconds."""
    end = time.process_time() + seconds
    while time.process_time() < end:
        pass
    return b"spun\n"


def nap(seconds: float) -> bytes:
    time.sleep(seconds)
    return b"slept\n"


def boom(i: int) -> bytes:
    if i == 1:
        raise ValueError("an unexpected failure of a shard")
    return b"fine\n"


SCRIPT = """
import sys
from pathlib import Path
sys.path.insert(0, {tests!r})
sys.path.insert(0, {stage2!r})
import driver
from test_v052_driver import PLACED, SHARDS, job, sunday

if __name__ == "__main__":
    run = driver.Run(
        Path({out!r}), job, SHARDS, "fp", 10.0, {workers}, clock=sunday, check_placement=PLACED
    )
    print(run.execute())
"""


def sunday() -> dt.datetime:
    return dt.datetime(2026, 11, 8, 22, 0, tzinfo=driver.BRT)


def _launch(tmp_path, out, workers=2):
    script = tmp_path / f"launch{workers}.py"
    script.write_text(
        SCRIPT.format(tests=str(ROOT / "tests"), stage2=str(STAGE2), out=str(out), workers=workers),
        "utf-8",
    )
    return subprocess.Popen([sys.executable, str(script)], stdout=subprocess.DEVNULL)


def _run(out, shards=SHARDS, **kw):
    kw.setdefault("cap_hours", 10.0)
    kw.setdefault("workers", 2)
    return driver.Run(out, job, shards, "fp", clock=sunday, check_placement=PLACED, **kw)


def _pids_on_file(charge) -> bool:
    """The charge file's worker identities; the driver replaces it atomically, and on Windows a
    read during the replacement is refused (CI run 42817682415): that read is retried."""
    try:
        return bool(json.loads(charge.read_text("utf-8"))["pids"])
    except (PermissionError, FileNotFoundError, json.JSONDecodeError):
        return False


def _kill_after(proc, sidecars, count):
    deadline = time.monotonic() + 200
    charge = sidecars.parent / "charges" / "b00000.json"
    while time.monotonic() < deadline:
        if sidecars.exists() and len(list(sidecars.glob("*.json"))) >= count:
            # on Windows, the workers' identities are on file before the controller dies
            if sys.platform != "win32" or _pids_on_file(charge):
                break
        time.sleep(0.02)
    proc.kill()
    proc.wait(timeout=60)
    time.sleep(3.0)  # the killed run's workers end when their pipe closes


def _workers_gone(run):
    """After a kill, wait for the workers to end, as the restart will require."""
    deadline = time.monotonic() + 60
    while run.workers_still_running() and time.monotonic() < deadline:
        time.sleep(0.5)
    assert run.workers_still_running() == []


def test_a_killed_run_resumes_to_the_same_bytes_with_another_worker_count(tmp_path):
    """Interrupt midway by killing the process, resume, compare with an uninterrupted run."""
    whole = tmp_path / "whole"
    proc = _launch(tmp_path, whole, workers=2)
    assert proc.wait(timeout=240) == 0
    reference = _run(whole).assemble()

    cut = tmp_path / "cut"
    _kill_after(_launch(tmp_path, cut, workers=2), cut / "sidecars", 6)
    done = len(list((cut / "sidecars").glob("*.json")))
    assert 6 <= done < len(SHARDS)
    # the crash is charged: every worker of the batch that was not closed, for a whole shard
    assert _run(cut).spent_seconds() >= 2 * driver.MAX_SHARD_SECONDS
    _workers_gone(_run(cut))
    proc = _launch(tmp_path, cut, workers=3)
    assert proc.wait(timeout=240) == 0
    assert _run(cut).assemble() == reference


def test_a_shard_is_not_computed_twice(tmp_path):
    out = tmp_path / "r"
    run = _run(out, SHARDS[:3])
    assert run.execute() == "complete"
    before = {p.name: p.stat().st_mtime_ns for p in (out / "shards").iterdir()}
    assert run.execute() == "complete"
    assert before == {p.name: p.stat().st_mtime_ns for p in (out / "shards").iterdir()}


@pytest.mark.parametrize("damage", ["truncated", "corrupt", "missing"])
def test_a_damaged_shard_stops_the_run(tmp_path, damage):
    out = tmp_path / "r"
    run = _run(out, SHARDS[:2])
    run.execute()
    path = out / "shards" / "s000.bin"
    if damage == "truncated":
        path.write_bytes(path.read_bytes()[:3])
    elif damage == "corrupt":
        path.write_bytes(b"x" * path.stat().st_size)
    else:
        path.unlink()
    with pytest.raises(SystemExit, match="does not match"):
        run.execute()


def test_stale_records_are_refused(tmp_path):
    out = tmp_path / "r"
    _run(out, SHARDS[:2]).execute()
    with pytest.raises(SystemExit, match="another fingerprint"):
        driver.Run(
            out, job, SHARDS[:2], "other", 10.0, 1, clock=sunday, check_placement=PLACED
        ).execute()
    with pytest.raises(SystemExit, match="another argument"):
        _run(out, [("s000", 99), ("s001", 1)]).execute()
    with pytest.raises(SystemExit, match="not in this schedule"):
        _run(out, SHARDS[1:2]).execute()


def test_a_duplicated_identity_is_refused(tmp_path):
    with pytest.raises(SystemExit, match="share an identity"):
        _run(tmp_path, [("a", 1), ("a", 2)])


def test_a_result_without_its_sidecar_is_computed_again(tmp_path):
    """The crash between publishing the result and writing its sidecar."""
    out = tmp_path / "r"
    run = _run(out, SHARDS[:2])
    run.execute()
    expected = (out / "shards" / "s001.bin").read_bytes()
    (out / "sidecars" / "s001.json").unlink()
    (out / "shards" / "s001.bin").write_bytes(b"partial")
    assert run.execute() == "complete"
    assert (out / "shards" / "s001.bin").read_bytes() == expected


def test_a_leftover_temporary_file_is_harmless(tmp_path):
    """The crash during the temporary file's writing."""
    out = tmp_path / "r"
    (out / "shards").mkdir(parents=True)
    (out / "shards" / "s000.bin.tmp").write_bytes(b"half")
    run = _run(out, SHARDS[:1])
    assert run.execute() == "complete"
    assert json.loads(run.assemble())["shard"] == 0
    assert not (out / "shards" / "s000.bin.tmp").exists()


def test_error_outcomes_are_kept_in_the_bytes(tmp_path):
    out = tmp_path / "r"
    run = _run(out, SHARDS[4:7])
    run.execute()
    assert b'"ERROR"' in run.assemble()


@pytest.mark.parametrize(
    ("moment", "configured", "expected"),
    [
        (dt.datetime(2026, 11, 9, 8, 0, tzinfo=driver.BRT), 22, 10),  # Monday, at the opening
        (dt.datetime(2026, 11, 9, 17, 59, tzinfo=driver.BRT), 22, 10),
        (dt.datetime(2026, 11, 9, 18, 0, tzinfo=driver.BRT), 22, 22),  # at the closing
        (dt.datetime(2026, 11, 9, 7, 59, tzinfo=driver.BRT), 22, 22),
        (dt.datetime(2026, 11, 8, 12, 0, tzinfo=driver.BRT), 22, 22),  # a Sunday
        (dt.datetime(2026, 11, 9, 12, 0, tzinfo=driver.BRT), 8, 8),  # never above the configured
        (dt.datetime(2026, 11, 8, 12, 0, tzinfo=driver.BRT), 40, 22),  # never above 22
        (dt.datetime(2026, 11, 9, 11, 0, tzinfo=dt.UTC), 22, 10),  # 08:00 in Brasilia
    ],
)
def test_the_worker_rule(moment, configured, expected):
    assert driver.workers_for(moment, configured) == expected


def test_no_shard_starts_at_the_pause(tmp_path):
    out = tmp_path / "r"
    late = dt.datetime(2026, 11, 18, 20, 0, tzinfo=driver.BRT)
    run = driver.Run(
        out, job, SHARDS[:2], "fp", 10.0, 1, clock=lambda: late, check_placement=PLACED
    )
    assert run.execute().startswith("paused")
    assert not list((out / "shards").iterdir())


def test_the_cap_stops_the_dispatch(tmp_path):
    """Spent time beyond a tiny cap: the next invocation dispatches nothing."""
    out = tmp_path / "r"
    run = _run(out, SHARDS[:2], cap_hours=10.0, workers=1)
    run.execute()
    more = _run(out, SHARDS[:2] + SHARDS[2:4], cap_hours=1e-9, workers=1)
    assert more.execute().startswith("stopped")
    assert len(list((out / "shards").iterdir())) == 2


def test_crossing_the_cap_at_the_end_binds(tmp_path, monkeypatch):
    """Codex's end-of-round review, finding 4: the last shard can carry consumption past the cap
    without reaching the watchdog; a completed run must not be assembled without a reason."""
    out = tmp_path / "r"
    run = _run(out, SHARDS[:2], cap_hours=10.0, workers=1)
    run.execute()
    late = _run(out, SHARDS[:2], cap_hours=1.5, workers=1)
    monkeypatch.setattr(late, "spent_seconds", lambda: 1.6 * 3600.0)
    assert late.execute().startswith("stopped")
    assert late.unresolved_stop() is not None
    with pytest.raises(SystemExit):
        late.assemble()


def test_a_guard_stops_the_dispatch_and_binds(tmp_path):
    out = tmp_path / "r"
    run = _run(out, SHARDS[:2], cap_hours=10.0, workers=1, guard=lambda spent: "stopped: a guard")
    assert run.execute() == "stopped: a guard"
    assert not list((out / "shards").iterdir())
    assert run.unresolved_stop() == "stopped: a guard"


@pytest.fixture
def ledger(tmp_path, monkeypatch):
    import budgeted

    monkeypatch.setattr(budgeted, "LEDGER", tmp_path / "ledger.json")
    return budgeted


def test_a_part_stops_above_one_and_a_half_times_its_allocation(tmp_path, ledger):
    ledger.declare("adequacy", {"p": 4.0 / 3600.0})
    state = ledger.execute(
        "adequacy", "p", tmp_path / "r", spin, [(f"s{i:03d}", 0.5) for i in range(40)], "fp",
        1, clock=sunday, check_placement=PLACED,
    )  # fmt: skip
    assert state.startswith("stopped")
    assert len(list((tmp_path / "r" / "shards").iterdir())) <= 2


def test_a_part_must_be_declared(tmp_path, ledger):
    with pytest.raises(SystemExit):
        ledger.execute("adequacy", "p", tmp_path / "r", job, SHARDS[:2], "fp", 1)


def test_a_stop_binds_under_other_code_until_it_is_reconciled(tmp_path, ledger):
    ledger.declare("adequacy", {"p": 4.0 / 3600.0})
    shards = [(f"s{i:03d}", 0.5) for i in range(40)]
    args = {"clock": sunday, "check_placement": PLACED}
    assert ledger.execute(
        "adequacy", "p", tmp_path / "r", spin, shards, "fp", 1, **args
    ).startswith("stopped")
    with pytest.raises(SystemExit):
        ledger.execute("adequacy", "p", tmp_path / "r2", spin, shards, "other", 1, **args)
    with pytest.raises(SystemExit):
        ledger.assembled("adequacy", "p", tmp_path / "r", spin, shards, "fp", 1)
    ledger.reconcile("adequacy", "p", "a recorded reason")
    assert "unresolved_stop" not in ledger.load()["sections"]["adequacy"]["parts"]["p"]


def test_a_stop_issued_by_the_driver_binds_in_the_ledger(tmp_path, ledger):
    """Codex, end of round 5: a cap, accounting or shard-limit stop of the driver itself is
    written to the ledger, so other code cannot run the part until it is reconciled."""
    ledger.declare("adequacy", {"p": 1.0})
    shards = [(f"s{i:03d}", 0.3) for i in range(6)]
    book = ledger.load()
    row = book["sections"]["adequacy"]["parts"]["p"]
    row["identity"] = ledger._identity("fp", shards, 1.0)
    row["projection_hours"] = 1e-6  # a frozen projection whose cap the first batch passes
    ledger.save(book)
    args = {"clock": sunday, "check_placement": PLACED}
    state = ledger.execute("adequacy", "p", tmp_path / "r", spin, shards, "fp", 1, **args)
    assert state != "complete" and not state.startswith("paused")  # the cap, by either path
    assert ledger.load()["sections"]["adequacy"]["parts"]["p"]["unresolved_stop"] == state
    with pytest.raises(SystemExit):
        ledger.execute("adequacy", "p", tmp_path / "r2", spin, shards, "other", 1, **args)


def test_a_frozen_checkpoint_is_not_measured_again_under_the_same_code(tmp_path, ledger):
    ledger.declare("adequacy", {"p": 1.0})
    args = {"clock": sunday, "check_placement": PLACED}
    # enough work for the checkpoint's projection to exceed a new batch's worker start
    shards = [(f"s{i:03d}", 0.3) for i in range(20)]
    assert ledger.execute("adequacy", "p", tmp_path / "r", spin, shards, "fp", 1, **args) == (
        "complete"
    )
    first = ledger.load()["sections"]["adequacy"]["parts"]["p"]["projection_hours"]
    ledger.execute("adequacy", "p", tmp_path / "r", spin, shards, "fp", 1, **args)
    assert ledger.load()["sections"]["adequacy"]["parts"]["p"]["projection_hours"] == first


def test_other_code_is_a_new_attempt_and_keeps_the_consumption(tmp_path, ledger):
    ledger.declare("adequacy", {"p": 1.0})
    args = {"clock": sunday, "check_placement": PLACED}
    # a frozen projection with room, so that the first run completes: a one-shard checkpoint of
    # four tiny shards projects less than a new batch's worker start, and its cap would now bind
    book = ledger.load()
    row = book["sections"]["adequacy"]["parts"]["p"]
    row["identity"] = ledger._identity("fp", SHARDS[:4], 1.0)
    row["projection_hours"] = 1.0
    ledger.save(book)
    assert ledger.execute("adequacy", "p", tmp_path / "r", job, SHARDS[:4], "fp", 1, **args) == (
        "complete"
    )
    ledger.execute("adequacy", "p", tmp_path / "r2", job, SHARDS[:4], "other", 1, **args)
    row = ledger.load()["sections"]["adequacy"]["parts"]["p"]
    assert len(row["attempts"]) == 1 and row["attempts"][0]["spent_hours"] > 0.0


def test_a_part_not_reached_keeps_its_reservation():
    import budgeted

    book = {"sections": {"adequacy": {"parts": {
        "a": {"allocation_hours": 25.0, "projection_hours": 30.0},
        "b": {"allocation_hours": 70.0},
    }}}}  # fmt: skip
    base = budgeted.SPENT_BEFORE + sum(v for k, v in budgeted.LINES.items() if k != "adequacy")
    assert budgeted.total_projection(book) == pytest.approx(base + 100.0)
    # a line with no part declared stays reserved whole
    assert budgeted.total_projection({}) == pytest.approx(
        budgeted.SPENT_BEFORE + sum(budgeted.LINES.values())
    )


def test_a_charge_counts_once_in_the_total_and_in_what_is_spent(ledger):
    before = ledger.total_projection(ledger.load())
    ledger.charge("a probe", 2.5, "measured")
    book = ledger.load()
    assert ledger.total_projection(book) == pytest.approx(before + 2.5)
    assert ledger.spent(book) == pytest.approx(ledger.SPENT_BEFORE + 2.5)
    with pytest.raises(SystemExit):
        ledger.charge("a probe", 1.0, "again")


def test_the_cap_follows_the_frozen_projection():
    import budgeted

    assert budgeted.cap_of({"allocation_hours": 95.0}) == pytest.approx(142.5)
    assert budgeted.cap_of({"allocation_hours": 95.0, "projection_hours": 50.0}) == pytest.approx(
        75.0
    )


def test_the_total_is_checked_after_the_last_batch(ledger, monkeypatch):
    monkeypatch.setattr(ledger, "HARD_MAXIMUM", 3099.0)
    ledger.declare("adequacy", {"p": 1.0})
    book = ledger.load()
    book["sections"]["adequacy"]["parts"]["p"]["identity"] = "x"
    assert ledger.finish(book, "adequacy", "p", 5000.0).startswith("stopped")
    assert "unresolved_stop" in ledger.load()["sections"]["adequacy"]["parts"]["p"]


def test_a_failed_gate_blocks_everything_and_stays_on_file(tmp_path, ledger):
    ledger.declare("adequacy", {"p": 1.0})
    ledger.fail_gate("adequacy", {"certified": 3})
    with pytest.raises(SystemExit):
        ledger.execute("adequacy", "p", tmp_path / "r", job, SHARDS[:2], "fp", 1)
    ledger.resolve_gate("adequacy", "a prospective redesign")
    book = ledger.load()
    assert not book["gates"] and book["gate_history"][0]["detail"] == {"certified": 3}


def test_the_checkpoint_is_an_evenly_spaced_twentieth():
    import budgeted

    assert len(budgeted.checkpoint(list(range(17)))) == 1
    picked = budgeted.checkpoint(list(range(100)))
    assert len(picked) == 5 and picked[0] == 0 and picked[-1] == 99


def _events(out):
    return [json.loads(x) for x in (out / "progress.jsonl").read_text("utf-8").splitlines()]


def test_the_batch_time_limit_stops_dispatch_and_the_next_batch_finishes(tmp_path):
    """Expiry itself: dispatch closes half a second in, and a shard takes a second."""
    out = tmp_path / "r"
    shards = [(f"s{i}", 1.0) for i in range(3)]
    run = driver.Run(
        out,
        spin,
        shards,
        "fp",
        10.0,
        1,
        clock=sunday,
        check_placement=PLACED,
        batch_seconds=30.0,
        max_shard_seconds=29.5,
    )
    assert run.execute() == "complete"
    batches = [e for e in _events(out) if e["event"] == "batch"]
    assert len(batches) >= 2 and batches[0]["workers"] == 1


def test_a_shard_limit_must_leave_room_inside_the_batch(tmp_path):
    with pytest.raises(SystemExit, match="room inside the batch"):
        _run(tmp_path, SHARDS[:1], batch_seconds=10.0, max_shard_seconds=10.0)


def test_a_shard_beyond_its_limit_is_kept_and_stops_the_run(tmp_path):
    out = tmp_path / "r"
    shards = [("a", 1.5), ("b", 0.0)]
    run = driver.Run(
        out,
        nap,
        shards,
        "fp",
        10.0,
        1,
        clock=sunday,
        check_placement=PLACED,
        batch_seconds=60.0,
        max_shard_seconds=0.5,
    )
    assert run.execute().startswith("stopped: shard a")
    assert (out / "shards" / "a.bin").read_bytes() == b"slept\n"
    assert not (out / "shards" / "b.bin").exists()
    assert any(e["event"] == "shard_over_limit" for e in _events(out))


def test_complete_bytes_cannot_pass_an_unresolved_stop(tmp_path):
    """The last shard overruns: every shard exists, and the run still may not be used."""
    out = tmp_path / "r"
    run = driver.Run(
        out,
        nap,
        [("a", 1.5)],
        "fp",
        10.0,
        1,
        clock=sunday,
        check_placement=PLACED,
        batch_seconds=60.0,
        max_shard_seconds=0.5,
    )
    assert run.execute().startswith("stopped: shard a")
    assert len(run._done()) == 1 and not run.completed()
    with pytest.raises(SystemExit, match="unresolved stop"):
        run.assemble()
    with pytest.raises(SystemExit, match="unresolved stop"):
        run.execute()
    run.reconcile("a test: the limit was declared too small")
    assert run.execute() == "complete"
    assert run.completed() and run.assemble() == b"slept\n"
    assert list(out.glob("stop-reconciled-*.json"))


@pytest.mark.skipif(sys.platform != "win32", reason="process identities are Windows handles")
def test_a_restart_is_refused_while_a_crashed_batch_has_live_workers(tmp_path):
    out = tmp_path / "r"
    run = _run(out, SHARDS[:1])
    (out / "charges").mkdir(parents=True)
    tracker = driver.CpuTracker()
    tracker.observe([os.getpid()])
    pids = tracker.identities()
    tracker.close()
    doc = {"seconds": 1.0, "committed": 0.0, "workers": 2, "closed": False, "pids": pids}
    (out / "charges" / "b00000.json").write_text(json.dumps(doc), "utf-8")
    with pytest.raises(SystemExit, match="still running"):
        run.execute()


def test_a_crashed_batch_is_closed_with_its_charge_on_restart(tmp_path):
    out = tmp_path / "r"
    run = _run(out, SHARDS[:1], max_shard_seconds=100.0)
    (out / "charges").mkdir(parents=True)
    doc = {"seconds": 1.0, "committed": 0.0, "workers": 2, "closed": False, "pids": {}}
    (out / "charges" / "b00000.json").write_text(json.dumps(doc), "utf-8")
    assert run.execute() == "complete"
    closed = json.loads((out / "charges" / "b00000.json").read_text("utf-8"))
    expected = 1.0 + 2 * (100.0 + driver.CHARGE_SECONDS)
    assert closed["closed"] is True and closed["seconds"] == pytest.approx(expected)


@pytest.mark.skipif(sys.platform != "win32", reason="live times are read through Windows handles")
def test_a_failed_accounting_stops_dispatch_and_binds(tmp_path, monkeypatch):
    out = tmp_path / "r"
    monkeypatch.setattr(driver, "_times", lambda _handle: None)
    shards = [(f"s{i}", 2.0) for i in range(6)]
    run = driver.Run(out, spin, shards, "fp", 10.0, 1, clock=sunday, check_placement=PLACED)
    assert run.execute() == "stopped: the CPU accounting failed"
    assert len(run._done()) < len(shards)
    assert run.unresolved_stop() == "stopped: the CPU accounting failed"


def test_a_worker_exception_stops_the_run_and_closes_the_charge(tmp_path):
    out = tmp_path / "r"
    run = driver.Run(
        out,
        boom,
        [("a", 0), ("b", 1), ("c", 2)],
        "fp",
        10.0,
        2,
        clock=sunday,
        check_placement=PLACED,
    )
    with pytest.raises(ValueError, match="unexpected failure"):
        run.execute()
    doc = json.loads((out / "charges" / "b00000.json").read_text("utf-8"))
    assert doc["closed"] is True
    assert not (out / "shards" / "b.bin").exists()


def test_a_failed_time_query_keeps_the_last_value(monkeypatch):
    tracker = driver.CpuTracker()
    tracker.handles = {1: object(), 2: object()}
    answers = iter([5.0, 3.0, None, 4.0])
    monkeypatch.setattr(driver, "_times", lambda _handle: next(answers))
    assert tracker.total() == 8.0
    assert tracker.total() == 9.0  # the first worker's query failed: it keeps 5.0
    assert tracker.failed_queries == 1 and tracker.failing_since is not None
    tracker.handles = {}


@pytest.mark.skipif(sys.platform != "win32", reason="live times are read through Windows handles")
def test_the_live_cap_stops_dispatch_within_the_run(tmp_path):
    out = tmp_path / "r"
    shards = [(f"s{i:03d}", 0.2) for i in range(60)]
    run = driver.Run(out, spin, shards, "fp", 0.003, 1, clock=sunday, check_placement=PLACED)
    assert run.execute() == "stopped: the cap is reached"
    assert 0 < len(run._done()) < len(shards)
    spent = run.spent_seconds() / 3600.0
    assert 0.003 <= spent <= 0.003 * driver.OVER_CAP_FACTOR


@pytest.mark.skipif(sys.platform != "win32", reason="live times are read through Windows handles")
def test_the_watchdog_ends_the_workers_above_ten_percent(tmp_path):
    out = tmp_path / "r"
    started = time.monotonic()
    run = driver.Run(out, spin, [("a", 120.0)], "fp", 5e-4, 1, clock=sunday, check_placement=PLACED)
    assert run.execute().startswith("over the cap")
    assert time.monotonic() - started < 60.0
    assert not (out / "shards" / "a.bin").exists()
    assert any(e["event"] == "over_cap" for e in _events(out))


def test_a_pin_outside_the_allowed_processors_is_refused(tmp_path):
    with pytest.raises(SystemExit, match="outside 8 to 31"):
        driver.Run(tmp_path, job, SHARDS, "fp", 1.0, 1, pin=[2])


def test_assembly_refuses_a_missing_shard(tmp_path):
    with pytest.raises(SystemExit, match="not done"):
        _run(tmp_path, SHARDS[:1]).assemble()
