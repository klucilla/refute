"""v0.5.4's projection correction for future parts (``budgeted_v3``; #217, the maintainer's decision
of 2026-11-12, 15:46, item 4; a finding for #59): an interruption before the checkpoint no longer
makes the resume impossible, the crash charge still counts in the consumption and in every cap, and
a part that ran under v0.5.2's rule is refused. Offline, with synthetic shards and a temporary
ledger.

Two kinds of run:
- the real driver, with a real pool, interrupted by an exception that escapes the batch the way a
  killed controller leaves it: the shards stored with their sidecars, the batch's charge left open
  with the workers' identities, the ledger already marked;
- a deterministic batch (``Exact``: each shard is charged exactly one second, closed), so that
  v0.5.2 and v3 can be compared to the last digit and the crash charge set against the caps
  exactly.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
STAGE2 = ROOT / "docs/validation/v0.5.2/stage2"
V054 = ROOT / "docs/validation/v0.5.4"
for p in (str(STAGE2), str(V054)):
    if p not in sys.path:
        sys.path.insert(0, p)
import budgeted  # noqa: E402
import budgeted_v3  # noqa: E402
import driver  # noqa: E402

PLACED = (os.cpu_count() or 0) >= 32
SHARDS = [(f"s{i:03d}", i) for i in range(20)]
SHARDS60 = [(f"s{i:03d}", i) for i in range(60)]  # a checkpoint of three shards
SECTION, PART = "test", "p"
ALLOCATION = 0.05
CRASH = driver.CHARGE_SECONDS  # with max_shard_seconds=1.0, a crash costs 21 s per worker


def job(i: int) -> bytes:
    """About 0.3 s of processor time per shard, so the pool's start-up does not dominate the
    projection (a near-free shard would make any checkpoint projection meaningless)."""
    end = time.process_time() + 0.3
    while time.process_time() < end:
        pass
    return json.dumps({"shard": i}).encode() + b"\n"


def sunday() -> dt.datetime:
    return dt.datetime(2026, 11, 8, 22, 0, tzinfo=driver.BRT)


KW = dict(clock=sunday, check_placement=PLACED, max_shard_seconds=1.0, batch_seconds=30.0)


@pytest.fixture
def ledger(tmp_path, monkeypatch):
    monkeypatch.setattr(budgeted, "LEDGER", tmp_path / "ledger.json")
    monkeypatch.setattr(budgeted, "LINES", {SECTION: 10.0})
    monkeypatch.setattr(budgeted, "HARD_MAXIMUM", 10.0)
    monkeypatch.setattr(budgeted, "SPENT_BEFORE", 0.0)
    budgeted.declare(SECTION, {PART: ALLOCATION})
    return tmp_path


def _row() -> dict:
    return budgeted.load()["sections"][SECTION]["parts"][PART]


def _no_live_worker(out: Path) -> None:
    """No worker any batch ever recorded is still alive (no leftovers)."""
    for path in sorted((out / "charges").glob("b*.json")):
        doc = json.loads(path.read_text("utf-8"))
        for pid, created in doc["pids"].items():
            assert not driver.still_running(int(pid), created), (path.name, pid)


def _charge(out: Path, name: str, **doc) -> None:
    (out / "charges").mkdir(parents=True, exist_ok=True)
    full = {"seconds": 0.0, "committed": 0.0, "workers": 1, "closed": True, "pids": {}, **doc}
    (out / "charges" / name).write_text(json.dumps(full), "utf-8")


# --- a real interruption of the real driver ---------------------------------------------------


class Killed(BaseException):
    """Escapes the driver's ``except Exception`` like a killed controller: the batch's closing
    charge is never written."""


@pytest.fixture
def killed_after_one_shard(monkeypatch):
    """The next real batch stores one shard, then the controller 'dies': the batch's charge stays
    open with its workers' identities, as the watchdog last wrote it."""
    state = {"armed": True, "dying": False}
    store, write = driver.Run._store, driver.Run._write_charge

    def _store(self, *a, **k):
        store(self, *a, **k)
        if state["armed"]:
            state["armed"], state["dying"] = False, True
            raise Killed

    def _write_charge(self, name, seconds, committed, workers, closed, pids):
        if closed and state["dying"]:
            return  # the closing write never happens
        write(self, name, seconds, committed, workers, closed, pids)

    monkeypatch.setattr(driver.Run, "_store", _store)
    monkeypatch.setattr(driver.Run, "_write_charge", _write_charge)
    return state


def _interrupt(out: Path, killed: dict, execute) -> None:
    with pytest.raises(Killed):
        execute(SECTION, PART, out, job, SHARDS60, "fp", 1, **KW)
    killed["dying"] = False
    docs = [json.loads(p.read_text("utf-8")) for p in sorted((out / "charges").glob("b*.json"))]
    assert [d["closed"] for d in docs] == [False]  # one batch, left open
    assert len(list((out / "sidecars").glob("*.json"))) == 1  # a partial checkpoint (1 of 3)
    assert "projection_hours" not in _row()


def test_a_real_interruption_before_the_checkpoint_resumes_under_v3(ledger, killed_after_one_shard):
    out = ledger / "run"
    _interrupt(out, killed_after_one_shard, budgeted_v3.execute)
    assert _row()["driver"] == "v3"  # marked at its first dispatch, before the interruption
    state = budgeted_v3.execute(SECTION, PART, out, job, SHARDS60, "fp", 2, **KW)
    assert state == "complete"
    row = _row()
    run = driver.Run(out, job, SHARDS60, "fp", 1.0, 1, **KW)
    assert len(run._done()) == len(SHARDS60)
    assert budgeted_v3.crash_seconds(run) == pytest.approx(1 * (1.0 + CRASH))
    # the crash charge is consumed: in the row, and so in the line and every caller's cap
    assert row["spent_hours"] * 3600.0 == pytest.approx(run.spent_seconds())
    assert row["spent_hours"] * 3600.0 >= 1.0 + CRASH
    assert row["projection_hours"] < budgeted.STOP_FACTOR * ALLOCATION
    _no_live_worker(out)


def test_the_same_interruption_stops_under_v052(ledger, killed_after_one_shard):
    """v0.5.2's ``budgeted.execute`` on the same interruption: its projection rule stops it, the
    projection being the checkpoint's charge, crash included, over its share."""
    out = ledger / "run"
    _interrupt(out, killed_after_one_shard, budgeted.execute)
    state = budgeted.execute(SECTION, PART, out, job, SHARDS60, "fp", 2, **KW)
    row = _row()
    share = row["checkpoint_shards"] / len(SHARDS60)
    assert row["projection_hours"] == pytest.approx(row["spent_hours"] / share)
    assert row["spent_hours"] * 3600.0 >= 1.0 + CRASH
    allowed = budgeted.STOP_FACTOR * ALLOCATION
    assert row["projection_hours"] > allowed
    assert state == (
        f"stopped: the projection {row['projection_hours']:.1f} CPU-h passes "
        f"1.5 times the allocation, {allowed:.1f}"
    )
    assert row["unresolved_stop"] == state
    _no_live_worker(out)


def test_an_uninterrupted_real_part_projects_its_whole_charge(ledger):
    out = ledger / "run"
    assert budgeted_v3.execute(SECTION, PART, out, job, SHARDS, "fp", 2, **KW) == "complete"
    run = driver.Run(out, job, SHARDS, "fp", 1.0, 1, **KW)
    assert budgeted_v3.crash_seconds(run) == 0.0
    assert budgeted_v3.measured_seconds(run) == pytest.approx(run.spent_seconds())
    _no_live_worker(out)


# --- the deterministic batch -----------------------------------------------------------------


class Exact(driver.Run):
    """Each shard is charged exactly one second and stored with its sidecar; with ``crash_after``
    set, the batch stores that many shards, leaves its charge open and 'dies'."""

    crash_after: int | None = None
    tracked: float | None = None  # what the interrupted batch's charge tracked, if not its shards
    caps: list[float] = []  # the cap each driver run was given, in order

    def execute(self) -> str:
        Exact.caps.append(self.cap_hours)
        return super().execute()

    def _batch(self, todo, workers, spent_hours):
        name = f"b{len(list(self.charge_dir.glob('b*.json'))):05d}.json"
        take = todo if Exact.crash_after is None else todo[: Exact.crash_after]
        for sid, arg in take:
            self._store(sid, arg, self.fn(arg), 1.0, workers)
        n = float(len(take))
        if Exact.crash_after is not None:
            Exact.crash_after = None
            seconds = n if Exact.tracked is None else Exact.tracked
            Exact.tracked = None
            self._write_charge(name, seconds, n, workers, False, {})
            raise Killed
        self._write_charge(name, n, n, workers, True, {})
        return None


def quick(i: int) -> bytes:
    return f"{i}\n".encode()


@pytest.fixture
def exact(monkeypatch):
    monkeypatch.setattr(driver, "Run", Exact)
    monkeypatch.setattr(driver, "set_below_normal", lambda: None)
    Exact.crash_after = Exact.tracked = None
    Exact.caps = []
    yield Exact
    Exact.crash_after = Exact.tracked = None


EKW = dict(clock=sunday, check_placement=False, max_shard_seconds=1.0, batch_seconds=30.0)


def _exact_run(execute, out, workers=2, **extra) -> str:
    return execute(SECTION, PART, out, quick, SHARDS60, "fp", workers, **EKW, **extra)


def test_without_an_interruption_v3_matches_v052_exactly(ledger, exact):
    first = _exact_run(budgeted.execute, ledger / "a")
    old = {k: v for k, v in _row().items() if k != "identity"}
    book = budgeted.load()
    book["sections"][SECTION]["parts"][PART] = {"allocation_hours": ALLOCATION}
    budgeted.save(book)
    second = _exact_run(budgeted_v3.execute, ledger / "b")
    new = {k: v for k, v in _row().items() if k != "identity"}
    assert first == second == "complete"
    assert new.pop("driver") == "v3"
    assert new.pop("projection_basis").startswith("measured CPU")
    assert new == old  # the same projection, consumption and checkpoint, to the last digit
    assert old["projection_hours"] == pytest.approx(3.0 / (3 / 60) / 3600.0)


def test_an_exact_interruption_v052_stops_and_v3_completes(ledger, exact):
    crash = 2 * (1.0 + CRASH)  # two workers
    exact.crash_after = 1
    with pytest.raises(Killed):
        _exact_run(budgeted.execute, ledger / "a")
    state = _exact_run(budgeted.execute, ledger / "a")
    spent = 1.0 + crash + 2.0  # the shard before the crash, its charge, the checkpoint's other two
    assert _row()["projection_hours"] == pytest.approx(spent / (3 / 60) / 3600.0)
    projection = _row()["projection_hours"]
    assert state == (
        f"stopped: the projection {projection:.1f} CPU-h passes 1.5 times the allocation, "
        f"{budgeted.STOP_FACTOR * ALLOCATION:.1f}"
    )
    book = budgeted.load()
    book["sections"][SECTION]["parts"][PART] = {"allocation_hours": ALLOCATION}
    budgeted.save(book)
    exact.crash_after = 1
    with pytest.raises(Killed):
        _exact_run(budgeted_v3.execute, ledger / "b")
    assert _exact_run(budgeted_v3.execute, ledger / "b") == "complete"
    row = _row()
    assert row["projection_hours"] == pytest.approx(3.0 / (3 / 60) / 3600.0)
    assert row["spent_hours"] == pytest.approx((60.0 + crash) / 3600.0)  # the crash consumed


def test_a_larger_measured_projection_raises_the_part_cap(ledger, exact):
    """Codex's round-2 example, documented in ``budgeted_v3``: the interrupted batch tracked 5 s
    with 1 s committed; the projection keeps the 5 s (140 s, not 60 s with only the committed),
    and the part's own cap after the checkpoint rises with it (1.5 x 140 + 42 = 252 s)."""
    exact.crash_after, exact.tracked = 1, 5.0
    with pytest.raises(Killed):
        _exact_run(budgeted_v3.execute, ledger / "run")
    assert _exact_run(budgeted_v3.execute, ledger / "run") == "complete"
    crash = 2 * (1.0 + CRASH)
    assert _row()["projection_hours"] == pytest.approx((5.0 + 2.0) / (3 / 60) / 3600.0)
    state = json.loads((ledger / "run" / "state.json").read_text("utf-8"))
    assert state["cap_hours"] == pytest.approx((1.5 * 140.0 + crash) / 3600.0)
    assert state["spent_hours"] == pytest.approx((5.0 + crash + 2.0 + 57.0) / 3600.0)


def test_the_caps_each_driver_run_was_given(ledger, exact):
    """Before the checkpoint: 1.5 x allocation, plus the crash charges on file and nothing else
    (not the 4 s tracked above the committed); after it: 1.5 x projection plus the crash."""
    exact.crash_after, exact.tracked = 1, 5.0
    with pytest.raises(Killed):
        _exact_run(budgeted_v3.execute, ledger / "run")
    _exact_run(budgeted_v3.execute, ledger / "run")
    crash = 2 * (1.0 + CRASH)
    rule = budgeted.STOP_FACTOR * ALLOCATION
    assert exact.caps == pytest.approx(
        [rule, rule + crash / 3600.0, (1.5 * 140.0 + crash) / 3600.0]
    )


def test_the_crash_charge_counts_against_the_hard_cap(ledger, exact):
    exact.crash_after = 1
    with pytest.raises(Killed):
        _exact_run(budgeted_v3.execute, ledger / "run")
    crash = 2 * (1.0 + CRASH)
    hard = (crash + 0.5) / 3600.0  # passed by the crash charge and the shard before it
    state = _exact_run(budgeted_v3.execute, ledger / "run", hard_cap_hours=hard)
    assert state == "stopped: the cap is reached"
    row = _row()
    assert row["unresolved_stop"] == state
    assert row["spent_hours"] == pytest.approx((1.0 + crash) / 3600.0)


def test_the_crash_charge_counts_in_the_total(ledger, exact, monkeypatch):
    monkeypatch.setattr(budgeted, "LINES", {SECTION: ALLOCATION})
    monkeypatch.setattr(budgeted, "HARD_MAXIMUM", 0.06)
    exact.crash_after = 1
    with pytest.raises(Killed):
        _exact_run(budgeted_v3.execute, ledger / "run", workers=12)
    crash = 12 * (1.0 + CRASH)  # 0.07 CPU-h: the total passes 0.06 by the crash charge alone
    state = _exact_run(budgeted_v3.execute, ledger / "run", workers=12)
    assert state.startswith("stopped: the total projection passes")
    assert _row()["spent_hours"] == pytest.approx((1.0 + crash) / 3600.0)


def test_the_three_kinds_of_batch_are_measured(tmp_path):
    out = tmp_path / "run"
    # closed: the larger, 2.0; crash-reconciled: 3.0 tracked before it; open: 1.0
    _charge(out, "b00000.json", seconds=2.0, committed=1.5)
    reconciled = dict(seconds=3.0 + 2 * (1.0 + CRASH), committed=1.0, workers=2)
    _charge(out, "b00001.json", **reconciled, reconciled_after_a_crash=True)
    _charge(out, "b00002.json", seconds=1.0, committed=0.5, workers=4, closed=False)
    run = driver.Run(out, quick, SHARDS, "fp", 1.0, 1, check_placement=False, max_shard_seconds=1.0)
    assert budgeted_v3.crash_seconds(run) == pytest.approx(6 * (1.0 + CRASH))
    assert budgeted_v3.measured_seconds(run) == pytest.approx(2.0 + 3.0 + 1.0)
    run.data_dir.mkdir(parents=True)
    run.side_dir.mkdir(parents=True)
    for sid, arg in SHARDS[:4]:  # sidecars above what the charges tracked: the floor applies
        run._store(sid, arg, quick(arg), 2.5, 1)
    assert budgeted_v3.measured_seconds(run) == pytest.approx(10.0)


def test_a_driver_stop_is_refused_before_any_reconciliation(ledger):
    out = ledger / "run"
    _charge(out, "b00000.json", seconds=1.0, committed=0.5, workers=4, closed=False)
    (out / "stop.json").write_text(json.dumps({"state": "stopped: x", "at": "t"}), "utf-8")
    with pytest.raises(SystemExit, match="unresolved stop"):
        budgeted_v3.execute(SECTION, PART, out, job, SHARDS, "fp", 2, **KW)
    doc = json.loads((out / "charges" / "b00000.json").read_text("utf-8"))
    assert doc["closed"] is False and "reconciled_after_a_crash" not in doc


@pytest.mark.parametrize(
    "earlier", [{"identity": "x"}, {"spent_hours": 0.01}, {"attempts": [{"spent_hours": 0.01}]}]
)
def test_a_part_of_the_earlier_rule_is_refused(ledger, earlier):
    book = budgeted.load()
    book["sections"][SECTION]["parts"][PART].update(earlier)
    budgeted.save(book)
    with pytest.raises(SystemExit, match="never applied"):
        budgeted_v3.execute(SECTION, PART, ledger / "run", job, SHARDS, "fp", 2, **KW)
    assert "driver" not in _row()
