"""v0.5.5: the fixed, protected cap for R1's remaining parts
(``docs/validation/v0.5.5/r1_fixed_cap.py``; the maintainer's decision of 2026-11-20, 21:00,
items 1 and 3; Codex, g1 round 1). Offline, with synthetic shards, a temporary ledger and a
deterministic batch (each shard charged its own seconds, closed). **These deterministic batches
check the synthetic flow; they do not validate the real watchdog nor show a strict physical
limit.**"""

from __future__ import annotations

import datetime as dt
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[2] / "docs/validation/v0.5.5"
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

spec = importlib.util.spec_from_file_location("r1_fixed_cap_under_test", HERE / "r1_fixed_cap.py")
fc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fc)
budgeted, driver, lv, te = fc.budgeted, fc.driver, fc.lv, fc.te

SECTION = "v055"
# heterogeneous shards: the first three cheap, the rest dear (the case a checkpoint misjudges)
COST = {f"s{i:03d}": (1.0 if i < 3 else 30.0) for i in range(20)}
SHARDS = [(sid, int(sid[1:])) for sid in COST]
LIMIT = 1.0  # the shard limit of the synthetic runs (the crash reserve: workers x 21 s)


def quick(i: int) -> bytes:
    rec = {
        "index": i,
        "status": "OK",
        "freed": i % 2 == 0,
        "power_placebo": 0.9,
        "white": {"status": "OK", "power": 0.99},
    }
    return json.dumps(rec).encode() + b"\n"


class Exact(driver.Run):
    """Each shard is charged exactly its ``COST`` seconds; the batch takes every shard left until
    the cap would be passed, and closes its charge."""

    caps: list[float] = []

    def execute(self) -> str:
        Exact.caps.append(self.cap_hours)
        return super().execute()

    def _batch(self, todo, workers, spent_hours):
        name = f"b{len(list(self.charge_dir.glob('b*.json'))):05d}.json"
        spent, n = spent_hours * 3600.0, 0.0
        for sid, arg in todo:
            if spent + n >= self.cap_hours * 3600.0:
                break
            self._store(sid, arg, self.fn(arg), COST[sid], workers)
            n += COST[sid]
        self._write_charge(name, n, n, workers, True, {})
        return None


def sunday() -> dt.datetime:
    return dt.datetime(2026, 11, 8, 22, 0, tzinfo=driver.BRT)


KW = dict(clock=sunday, check_placement=False, batch_seconds=30.0)
KWX = dict(KW, max_shard_seconds=LIMIT)  # for a driver.Run built by a test


@pytest.fixture
def ledger(tmp_path, monkeypatch):
    monkeypatch.setattr(budgeted, "LEDGER", tmp_path / "ledger.json")
    monkeypatch.setattr(budgeted, "LINES", {SECTION: 63.5})
    monkeypatch.setattr(budgeted, "HARD_MAXIMUM", 64.0)
    monkeypatch.setattr(budgeted, "SPENT_BEFORE", 0.0)
    monkeypatch.setattr(budgeted, "save", lv._atomic_save)
    monkeypatch.setattr(lv, "HERE", tmp_path)
    monkeypatch.setattr(lv, "LOCK", tmp_path / "ledger.lock")
    monkeypatch.setattr(driver, "Run", Exact)
    monkeypatch.setattr(driver, "set_below_normal", lambda: None)
    Exact.caps = []
    budgeted.declare(SECTION, {"p": 0.2, "small": 0.05, "old": 0.2, "r1_reserve": 10.0})
    return tmp_path


def _row(part="p") -> dict:
    return budgeted.load()["sections"][SECTION]["parts"][part]


def _run(out, part="p", shards=SHARDS, workers=2):
    return fc.execute_fixed(SECTION, part, out, quick, shards, "fp", workers, LIMIT, **KW)


def test_the_protected_cap():
    # one crash charge (workers x (limit + 20 s)), the poll margin and the watchdog's 1.10
    cap = fc.protected_cap(1.5, 3, 600.0)
    assert cap * driver.OVER_CAP_FACTOR + fc.crash_reserve(3, 600.0) < 1.5
    assert cap == pytest.approx((1.5 - 3 * 620 / 3600 - 3 * 0.5 / 3600) / 1.10)
    # ten workers' crash charge with a 600 s limit (1.72 CPU-h) does not fit 1.5: refused
    with pytest.raises(SystemExit, match="does not fit"):
        fc.protected_cap(1.5, 10, 600.0)
    # the planned parts fit
    assert fc.protected_cap(fc.COMPLETION_ALLOCATION, fc.WORKERS[fc.COMPLETION_PART], 600.0) > 0.8
    assert fc.protected_cap(3.1, fc.WORKERS["r1_t2ae_2"], 600.0) > 2.1


def test_the_line_s_cap_applies_when_smaller_and_a_resume_never_raises_it(ledger):
    line = 0.01  # 36 s: smaller than the protected cap of the allocation
    state = fc.execute_fixed(SECTION, "p", ledger / "a", quick, SHARDS, "fp", 2, LIMIT,
                             line_cap=line, **KW)  # fmt: skip
    assert Exact.caps == [pytest.approx(line)]
    assert state.startswith("stopped")
    assert _row()["cap_hours"] == pytest.approx(line)


def test_a_fixed_cap_runs_heterogeneous_shards_with_no_checkpoint(ledger):
    # 3 x 1 s + 17 x 30 s = 513 s; budgeted_v3's checkpoint of the first shards would have
    # projected 60 s and capped the part at 90 s
    assert _run(ledger / "a") == "complete"
    assert len(Exact.caps) == 1  # one driver run, no checkpoint run
    assert Exact.caps[0] == pytest.approx(fc.protected_cap(0.2, 2, LIMIT))
    row = _row()
    assert row["driver"] == fc.MARK and "projection_hours" not in row
    assert row["spent_hours"] == pytest.approx(513 / 3600)
    assert row["completed_fixed"]["spent_hours"] == pytest.approx(513 / 3600)
    assert row["operational_identity"]["runner_sha256"] == fc.own_sha256()
    run = Exact(ledger / "a", quick, SHARDS, "fp", 1.0, 2, **KWX)
    assert fc.check_completed(SECTION, "p", run, "fp", SHARDS)["driver"] == fc.MARK
    with pytest.raises(SystemExit, match="already completed"):
        _run(ledger / "a")


def test_the_cap_stops_binds_and_never_completes(ledger):
    state = _run(ledger / "a", part="small")  # a cap of about 124 s
    assert state.startswith("stopped")
    row = _row("small")
    assert "unresolved_stop" in row and "completed_fixed" not in row
    assert row["spent_hours"] < 0.05  # within the allocation, the crash reserve left
    with pytest.raises(SystemExit, match="unresolved stop"):
        _run(ledger / "a", part="small")
    run = Exact(ledger / "a", quick, SHARDS, "fp", 1.0, 2, **KWX)
    with pytest.raises(SystemExit, match="not completed"):
        fc.check_completed(SECTION, "small", run, "fp", SHARDS)


def test_refusals(ledger):
    book = budgeted.load()
    book["sections"][SECTION]["parts"]["old"].update(driver="v3", spent_hours=0.1, identity="x")
    budgeted.save(book)
    with pytest.raises(SystemExit, match="another driver"):
        _run(ledger / "b", part="old")
    # the runner or its settings changed between runs of the same part
    book = budgeted.load()
    book["sections"][SECTION]["parts"]["p"]["operational_identity"] = {"runner_sha256": "other"}
    budgeted.save(book)
    with pytest.raises(SystemExit, match="the runner or its settings changed"):
        _run(ledger / "a")
    book = budgeted.load()
    book["sections"][SECTION]["parts"]["p"].pop("operational_identity")
    budgeted.save(book)
    assert _run(ledger / "a") == "complete"
    with pytest.raises(SystemExit, match="already completed"):
        _run(ledger / "a", shards=SHARDS[:5])


def test_shards_without_an_accounted_completion_are_refused(ledger):
    assert _run(ledger / "a") == "complete"
    run = Exact(ledger / "a", quick, SHARDS, "fp", 1.0, 2, **KWX)
    book = budgeted.load()
    book["sections"][SECTION]["parts"]["p"].pop("completed_fixed")
    budgeted.save(book)
    with pytest.raises(SystemExit, match="not completed"):
        fc.check_completed(SECTION, "p", run, "fp", SHARDS)
    book["sections"][SECTION]["parts"]["p"]["completed_fixed"] = {"utc": "x", "spent_hours": 0}
    book["sections"][SECTION]["parts"]["p"]["spent_hours"] = 0.0
    budgeted.save(book)
    with pytest.raises(SystemExit, match="disagree"):
        fc.check_completed(SECTION, "p", run, "fp", SHARDS)
    # an open charge
    (ledger / "a" / "charges" / "b00009.json").write_text(
        json.dumps({"seconds": 0, "committed": 0, "workers": 1, "closed": False, "pids": {}}),
        "utf-8",
    )
    with pytest.raises(SystemExit, match="open charge|not complete"):
        fc.check_completed(SECTION, "p", run, "fp", SHARDS)
    budgeted.fail_gate("g", {})
    with pytest.raises(SystemExit, match="failed gate"):
        fc.check_completed(SECTION, "p", run, "fp", SHARDS)


def test_declare_fixed_takes_from_the_reserve(ledger):
    fc.declare_fixed({"r1_t2ae_1c": 1.5})
    parts = budgeted.load()["sections"][SECTION]["parts"]
    assert parts["r1_t2ae_1c"]["allocation_hours"] == 1.5
    assert parts["r1_reserve"]["allocation_hours"] == pytest.approx(8.5)
    fc.declare_fixed({"r1_t2ae_1c": 1.5})  # the same declaration again: unchanged
    assert budgeted.load()["sections"][SECTION]["parts"]["r1_reserve"]["allocation_hours"] == (
        pytest.approx(8.5)
    )
    with pytest.raises(SystemExit, match="another allocation"):
        fc.declare_fixed({"r1_t2ae_1c": 2.0})
    with pytest.raises(SystemExit, match="cannot fund"):
        fc.declare_fixed({"big": 20.0})


# --- stage 1's completion: coverage, the summary and its recovery ---------------------------------


@pytest.fixture
def stage1(ledger, monkeypatch):
    rows = SHARDS[:10]
    out = ledger / "stage1"
    first = Exact(out, quick, rows, "fp", 1.0, 2, **KWX)
    (out / "shards").mkdir(parents=True)
    (out / "sidecars").mkdir(parents=True)
    for sid, arg in rows[:6]:
        first._store(sid, arg, quick(arg), 1.0, 2)
    first._record_stop("over the cap: the workers were ended")
    monkeypatch.setattr(fc, "_stage1", lambda: (rows, "fp", out))
    monkeypatch.setattr(fc.te, "shard", quick)
    monkeypatch.setattr(fc, "WORKERS", {fc.COMPLETION_PART: 2, "r1_t2ae_2": 2})
    budgeted.declare(
        SECTION, {"p": 0.2, "small": 0.05, "old": 0.2, fc.COMPLETION_PART: 0.2, "r1_reserve": 9.8}
    )
    book = budgeted.load()
    book["sections"][SECTION]["parts"][fc.STOPPED_PART] = {
        "allocation_hours": 0.0,
        "unresolved_stop": "over the cap",
    }
    budgeted.save(book)
    return rows, out


def _complete(rows, out):
    todo = fc.completion_rows(rows, fc.stopped_done(rows, "fp", out))
    state = fc.execute_fixed(
        SECTION, fc.COMPLETION_PART, fc._completion_out(out), quick, todo, "fp", 2, LIMIT, **KW
    )
    assert state == "complete"
    return todo


def test_the_completion_covers_the_stage_once_in_schedule_order(stage1):
    rows, out = stage1
    with pytest.raises(SystemExit, match="not completed"):
        fc.merged_stage1_records()
    todo = _complete(rows, out)
    assert [s for s, _ in todo] == [s for s, _ in rows[6:]]
    recs, split = fc.merged_stage1_records()
    assert [r["index"] for r in recs] == [arg for _, arg in rows]
    assert split["stopped_part_shards"] == sorted(s for s, _ in rows[:6])
    assert split["completion_part_shards"] == sorted(s for s, _ in rows[6:])
    assert split["stopped_part_stop"] == "over the cap"
    assert split["total_stage_1_cpu_hours"] == pytest.approx(
        split["stopped_part_cpu_hours"] + split["completion_part_cpu_hours"], abs=1e-4
    )
    # a shard in both folders is refused (the completion's identity, bound to its rows, or the
    # driver's own sidecar check refuses it first)
    extra = Exact(out, quick, rows, "fp", 1.0, 2, **KWX)
    extra._store(rows[6][0], rows[6][1], quick(rows[6][1]), 1.0, 2)
    with pytest.raises(SystemExit, match="exactly once|not in this schedule|another identity"):
        fc.merged_stage1_records()


@pytest.fixture
def pub(stage1, monkeypatch, tmp_path):
    rows, out = stage1
    _complete(rows, out)
    folder = tmp_path / "pub"
    folder.mkdir()
    monkeypatch.setattr(fc, "HERE", folder)
    monkeypatch.setattr(fc, "COMPLETION_RECORD", folder / "t2ae-1-completion.json")
    monkeypatch.setattr(fc.te, "code_identity", lambda: {"digest": "d"})
    monkeypatch.setattr(lv, "check_caps", lambda *a, **k: {})
    return folder


def _interrupted_summary(pub, charges=1, **change):
    """t2ae-1.json as the frozen summary writes it, then an interruption before the record."""
    recs, _ = fc.merged_stage1_records()
    doc = {"code_identity": {"digest": "d"}, **fc._expected_stage1_fields(recs), **change}
    (pub / "t2ae-1.json").write_text(json.dumps(doc), "utf-8")
    for k in range(charges):
        budgeted.charge(f"{fc.SUMMARY_CHARGE_PREFIX}{k}", 0.001, "the frozen summary")


def test_the_summary_publishes_and_recovers_once(pub, monkeypatch):
    _interrupted_summary(pub)
    fc.t2ae_1c_summarize()
    comp = json.loads((pub / "t2ae-1-completion.json").read_text("utf-8"))
    assert comp["written_after_a_recovery"] is True and comp["state"] == "final"
    assert any(c["name"].startswith("t2ae_completion_summary_") for c in budgeted.load()["charges"])
    want = hashlib.sha256((pub / "t2ae-1.json").read_bytes()).hexdigest()
    assert comp["stage_1_record_sha256"] == want
    with pytest.raises(SystemExit, match="written once"):
        fc.t2ae_1c_summarize()
    # stage 2 is bound to both records
    monkeypatch.setattr(fc.te, "_first_stage", lambda: {"_sha256": want, "futile_after_1": False})
    assert fc.check_stage1_published()["futile_after_1"] is False
    monkeypatch.setattr(fc.te, "_first_stage", lambda: {"_sha256": "x", "futile_after_1": False})
    with pytest.raises(SystemExit, match="not bound"):
        fc.check_stage1_published()


@pytest.mark.parametrize(
    "charges, change, match",
    [
        (0, {}, "accounting is uncertain"),
        (2, {}, "accounting is uncertain"),
        (1, {"counts": {"injections": 1}}, "decisive fields differ"),
        (1, {"futile_after_1": None}, "decisive fields differ"),
        (1, {"stage": "2"}, "decisive fields differ"),
    ],
)
def test_a_recovery_is_refused_without_certain_accounting_or_fields(pub, charges, change, match):
    _interrupted_summary(pub, charges=charges, **change)
    with pytest.raises(SystemExit, match=match):
        fc.t2ae_1c_summarize()
    assert not (pub / "t2ae-1-completion.json").exists()


def test_a_recovery_after_the_charges_passed_their_room_is_refused(pub):
    _interrupted_summary(pub)
    budgeted.charge("big", lv.CHARGES_ROOM, "a charge that passes the room")
    with pytest.raises(SystemExit, match="room"):
        fc.t2ae_1c_summarize()
    assert not (pub / "t2ae-1-completion.json").exists()


def test_a_record_that_appears_before_the_lock_is_never_overwritten(pub, monkeypatch):
    _interrupted_summary(pub)
    enter = lv.Exclusive.__enter__

    def appears(self):
        out = enter(self)
        if not (pub / "t2ae-1-completion.json").exists():
            (pub / "t2ae-1-completion.json").write_text("{}", "utf-8")  # another process
        return out

    monkeypatch.setattr(lv.Exclusive, "__enter__", appears)
    with pytest.raises(SystemExit, match="written once"):
        fc.t2ae_1c_summarize()
    assert (pub / "t2ae-1-completion.json").read_text("utf-8") == "{}"


def test_stage_2_needs_the_completion_record(ledger, monkeypatch, tmp_path):
    monkeypatch.setattr(fc, "COMPLETION_RECORD", tmp_path / "missing.json")
    monkeypatch.setattr(fc.te, "_first_stage", lambda: {"_sha256": "x", "futile_after_1": False})
    with pytest.raises(SystemExit, match="completion record is missing"):
        fc.check_stage1_published()
