"""v0.5.5: the fixed-cap adapter for D2-F's set A (``docs/validation/v0.5.5/d2f_fixed_cap.py``;
the maintainer's decisions of 2026-11-21 at G1, item 2). Offline, with synthetic shards, a
temporary ledger, a deterministic batch and a stand-in for ``d2f_floor``'s summary. **These
deterministic batches check the synthetic flow; they do not validate the real watchdog nor show
a strict physical limit.**"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[2] / "docs/validation/v0.5.5"
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
STAGE2 = Path(__file__).resolve().parents[2] / "docs/validation/v0.5.2/stage2"
if str(STAGE2) not in sys.path:
    sys.path.insert(0, str(STAGE2))
import budgeted  # noqa: E402  (v0.5.2's, unbound: importing it changes nothing)
import driver  # noqa: E402

BOUND = ("LEDGER", "LINES", "HARD_MAXIMUM", "SPENT_BEFORE", "save")
ad = lv = d2f = None  # set by the ``adapter`` fixture


@pytest.fixture(autouse=True)
def adapter(monkeypatch):
    """The adapter is loaded inside a test, never at collection: importing it binds ``budgeted``
    to v0.5.5's ledger, which other test files must not see; the bound attributes are restored
    after each test."""
    global ad, lv, d2f
    for name in BOUND:
        monkeypatch.setattr(budgeted, name, getattr(budgeted, name))
    if ad is None:
        spec = importlib.util.spec_from_file_location(
            "d2f_fixed_cap_under_test", HERE / "d2f_fixed_cap.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        ad = module
    assert ad.budgeted is budgeted and ad.driver is driver
    lv, d2f = ad.lv, ad.d2f
    return ad


SECTION = "v055"
COST = {f"A-P-{i:04d}": (1.0 if i < 3 else 30.0) for i in range(20)}  # heterogeneous
SHARDS = [(sid, {"set": "A", "indices": [int(sid[-4:])]}) for sid in COST]
LIMIT = 1.0
HISTORICAL = "d2f_summarize_A_19990101T000000Z"


def quick(arg) -> bytes:
    return json.dumps({"index": arg["indices"][0], "status": "OK"}).encode() + b"\n"


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


class Crash(Exact):
    crashed = False

    def _batch(self, todo, workers, spent_hours):
        if Crash.crashed:
            return super()._batch(todo, workers, spent_hours)
        Crash.crashed = True
        for sid, arg in todo[:2]:
            self._store(sid, arg, self.fn(arg), COST[sid], workers)
        self._write_charge("b00000.json", 2.0, 2.0, workers, False, {})
        raise RuntimeError("the controller died")


@pytest.fixture
def ledger(tmp_path, monkeypatch):
    monkeypatch.setattr(budgeted, "LEDGER", tmp_path / "ledger.json")
    monkeypatch.setattr(budgeted, "LINES", {SECTION: 63.5})
    monkeypatch.setattr(budgeted, "HARD_MAXIMUM", 64.0)
    monkeypatch.setattr(budgeted, "SPENT_BEFORE", 0.0)
    monkeypatch.setattr(budgeted, "save", lv._atomic_save)
    monkeypatch.setattr(lv, "HERE", tmp_path)
    monkeypatch.setattr(lv, "LOCK", tmp_path / "ledger.lock")
    monkeypatch.setattr(lv, "check_caps", lambda *a, **k: {})
    monkeypatch.setattr(driver, "Run", Exact)
    monkeypatch.setattr(driver, "set_below_normal", lambda: None)
    monkeypatch.setattr(driver, "check_controller_placement", lambda: None)
    monkeypatch.setattr(d2f, "schedule", lambda s: list(SHARDS))
    monkeypatch.setattr(d2f, "fingerprint", lambda rows: "fp")
    monkeypatch.setattr(d2f, "OUT", tmp_path / "d2f")
    monkeypatch.setattr(d2f, "shard", quick)
    monkeypatch.setattr(ad, "WORKERS", 2)
    monkeypatch.setattr(ad, "SHARD_LIMIT", LIMIT)
    monkeypatch.setattr(ad, "PROJECTION", {"basis": "synthetic", "projection_hours": 0.1})
    monkeypatch.setattr(ad, "RECORD", tmp_path / "d2f-A.json")
    monkeypatch.setattr(ad, "CLOSING", tmp_path / "d2f-A-closing.json")
    monkeypatch.setattr(ad, "D1P_A", tmp_path / "d1p-A.json")
    (tmp_path / "d1p-A.json").write_text(json.dumps({"futile_after_A": True}), "utf-8")
    Exact.caps = []
    budgeted.declare(
        SECTION,
        {"r1_d1p_a": 14.2, "r1_d1p_b": 14.2, "r1_d2f_a": 0.0, "r1_d2f_b": 0.0, "r1_reserve": 21.8},
    )
    return tmp_path


def _parts() -> dict:
    return budgeted.load()["sections"][SECTION]["parts"]


def _wrapper_charges() -> list:
    return [c for c in budgeted.load()["charges"] if c["name"].startswith(ad.WRAPPER_CHARGE_PREFIX)]


# --- the caps -----------------------------------------------------------------------------------


def test_the_authorized_funding_fits_four_workers_and_not_ten():
    # Codex's figures (d2f-not-run.md): 16.228111 CPU-h are needed with 4 workers and a 1,200 s
    # shard limit for a cap of 1.3 x 10.4 = 13.52; the authorized 16.3 fits, ten workers do not
    assert ad.ALLOCATION == pytest.approx(16.3)
    cap = ad.protected_cap(16.3, 4, 1200.0)
    assert cap >= 1.3 * 10.4
    assert cap * driver.OVER_CAP_FACTOR + ad.crash_reserve(4, 1200.0) < 16.3
    assert ad.protected_cap(16.228111, 4, 1200.0) == pytest.approx(13.52, abs=1e-5)
    assert ad.protected_cap(16.3, 10, 1200.0) < 1.3 * 10.4
    assert ad.SHARD_LIMIT == ad.rc.MAX_SHARD_SECONDS == 1200.0 and ad.WORKERS == 4


# --- the funding --------------------------------------------------------------------------------


def test_the_funding_moves_d1p_b_and_the_reserve_once(ledger, monkeypatch):
    saves = []
    save = lv._atomic_save

    def counted(book):
        saves.append(1)
        save(book)

    monkeypatch.setattr(lv, "_atomic_save", counted)  # assert_bound compares the two
    monkeypatch.setattr(budgeted, "save", counted)
    ad.fund()
    assert len(saves) == 1  # the allocations and the transfer's record in one write
    parts = _parts()
    assert parts["r1_d2f_a"]["allocation_hours"] == pytest.approx(16.3)
    assert parts["r1_d1p_b"]["allocation_hours"] == 0.0
    assert parts["r1_reserve"]["allocation_hours"] == pytest.approx(19.7)
    (t,) = budgeted.load()["transfers"]
    assert t["to"] == "r1_d2f_a" and t["from"] == {"r1_d1p_b": 14.2, "r1_reserve": 2.1}
    ad.fund()  # again: unchanged
    assert len(budgeted.load()["transfers"]) == 1
    assert _parts()["r1_reserve"]["allocation_hours"] == pytest.approx(19.7)


def test_the_funding_is_refused_without_its_conditions(ledger):
    (ledger / "d1p-A.json").write_text(json.dumps({"futile_after_A": False}), "utf-8")
    with pytest.raises(SystemExit, match="futility"):
        ad.fund()
    (ledger / "d1p-A.json").write_text(json.dumps({"futile_after_A": True}), "utf-8")
    book = budgeted.load()
    book.setdefault("starts", {})["r1_d1p_b"] = [{"identity": "x", "utc": "t", "resume": False}]
    budgeted.save(book)
    with pytest.raises(SystemExit, match="r1_d1p_b ran or started"):
        ad.fund()
    book = budgeted.load()
    book["starts"] = {}
    book["sections"][SECTION]["parts"]["r1_reserve"]["allocation_hours"] = 1.0
    budgeted.save(book)
    with pytest.raises(SystemExit, match="cannot fund"):
        ad.fund()
    assert "transfers" not in budgeted.load()


# --- the run ------------------------------------------------------------------------------------


def test_set_a_runs_with_the_effective_cap_it_checked(ledger):
    ad.run()
    row = _parts()["r1_d2f_a"]
    protected = ad.protected_cap(16.3, 2, LIMIT)
    assert Exact.caps == [pytest.approx(protected)]  # one driver run, no checkpoint
    check = row["margin_checks"][-1]
    assert check["fits"] and check["effective_cap_hours"] == pytest.approx(protected)
    assert row["driver"] == ad.MARK and row["completed_fixed"]
    assert "projection_hours" not in row and "checkpoint_shards" not in row
    assert row["operational_identity"]["adapter_sha256"] == ad.own_sha256()
    assert row["spent_hours"] == pytest.approx(513 / 3600)
    assert len(budgeted.load()["starts"]["r1_d2f_a"]) == 1
    with pytest.raises(SystemExit, match="already completed|resume was used"):
        ad.run()


def test_set_a_is_refused_when_only_the_protected_cap_fits_the_margin(ledger, monkeypatch):
    monkeypatch.setattr(lv, "hard_cap", lambda *a: 0.1)  # the line allows less than 1.3 x 0.1
    with pytest.raises(SystemExit, match="below 1.3 times the projection"):
        ad.run()
    book = budgeted.load()
    row = book["sections"][SECTION]["parts"]["r1_d2f_a"]
    assert row["margin_checks"][-1]["fits"] is False
    assert "r1_d2f_a" not in book.get("starts", {}) and Exact.caps == []


def test_the_cap_stops_binds_and_never_completes(ledger, monkeypatch):
    monkeypatch.setattr(ad, "PROJECTION", {"basis": "synthetic", "projection_hours": 0.01})
    monkeypatch.setattr(lv, "hard_cap", lambda *a: 0.02)  # 72 s against 513 s of work
    with pytest.raises(SystemExit, match="STOP for the maintainer"):
        ad.run()
    row = _parts()["r1_d2f_a"]
    assert "unresolved_stop" in row and "completed_fixed" not in row
    with pytest.raises(SystemExit, match="not completed"):
        ad.summarize()
    assert not (ledger / "d2f-A.json").exists()


def test_a_real_resume_never_raises_the_cap(ledger, monkeypatch):
    monkeypatch.setattr(driver, "Run", Crash)
    Crash.crashed = False
    monkeypatch.setattr(ad, "PROJECTION", {"basis": "synthetic", "projection_hours": 0.01})
    monkeypatch.setattr(lv, "hard_cap", lambda *a: 0.05)
    with pytest.raises(RuntimeError, match="died"):
        ad.run()
    assert _parts()["r1_d2f_a"]["cap_hours"] == pytest.approx(0.05)
    monkeypatch.setattr(lv, "hard_cap", lambda *a: 1.0)  # the line allows more now
    with pytest.raises(SystemExit, match="STOP for the maintainer"):
        ad.run()  # the pre-approved resume: the cap recorded before stays
    assert Exact.caps == [pytest.approx(0.05), pytest.approx(0.05)]
    assert budgeted.load()["starts"]["r1_d2f_a"][-1]["resume"] is True
    # the open batch was closed by the reconciliation with exactly one crash charge added, the
    # earlier consumption kept (Codex, d2fa round 1)
    charge = json.loads((ledger / "d2f" / "fp" / "charges" / "b00000.json").read_text("utf-8"))
    assert charge["closed"] and charge["reconciled_after_a_crash"]
    assert charge["seconds"] == pytest.approx(2.0 + 2 * (LIMIT + driver.CHARGE_SECONDS))


def test_a_changed_adapter_is_refused(ledger, monkeypatch):
    monkeypatch.setattr(driver, "Run", Crash)
    Crash.crashed = False
    with pytest.raises(RuntimeError):
        ad.run()
    book = budgeted.load()
    book["sections"][SECTION]["parts"]["r1_d2f_a"]["operational_identity"]["adapter_sha256"] = "x"
    budgeted.save(book)
    with pytest.raises(SystemExit, match="the adapter or its settings changed"):
        ad.run()


# --- the summary --------------------------------------------------------------------------------


def _inner(ledger, futile=True, fail=None, hours=0.001, name="inner"):
    """A stand-in for d2f_floor.summarize: its record (written once), its own charge, then
    ``fail`` (as its stops are raised after the record)."""

    def summarize(set_name):
        assert set_name == "A"
        (ledger / "d2f-A.json").write_text(json.dumps({"futile_after_A": futile}), "utf-8")
        budgeted.charge(f"{ad.SUMMARY_CHARGE_PREFIX}{name}", hours, "the frozen summary")
        if fail is not None:
            raise SystemExit(fail)

    return summarize


def test_the_summary_binds_its_charge_and_charges_the_wrapper(ledger, monkeypatch):
    ad.run()
    budgeted.charge(HISTORICAL, 0.001, "an earlier summary")
    monkeypatch.setattr(d2f, "summarize", _inner(ledger))
    ad.summarize()
    receipt = ad.check_receipt()
    assert receipt["charge_name"] == f"{ad.SUMMARY_CHARGE_PREFIX}inner"
    want = hashlib.sha256((ledger / "d2f-A.json").read_bytes()).hexdigest()
    assert receipt["summary_sha256"] == want
    book = budgeted.load()
    assert book[ad.ATTEMPTS][-1]["prior_summary_charges"] == [HISTORICAL]
    assert any(c["name"] == HISTORICAL for c in book["charges"])  # never removed
    assert len(_wrapper_charges()) == 1
    closing = ad.check_closed()
    assert closing["state"] == "final" and closing["receipt"] == receipt
    assert closing["wrapper_charge"] == {
        "name": _wrapper_charges()[0]["name"],
        "hours": _wrapper_charges()[0]["hours"],
    }
    ad.accept()
    with pytest.raises(SystemExit, match="written once"):
        ad.summarize()
    assert len(_wrapper_charges()) == 2  # the refusal's work is charged too
    assert ad.check_closed() == closing


def test_a_failed_wrapper_charge_leaves_no_closing(ledger, monkeypatch):
    # Codex, d2fa round 1: the record, its charge and the receipt are saved, then the wrapper's
    # charge fails before it persists: a STOP, no valid closing, and the operational entry refuses
    ad.run()
    monkeypatch.setattr(d2f, "summarize", _inner(ledger))
    charge = lv.charge

    def fails(name, hours, basis):
        if name.startswith(ad.WRAPPER_CHARGE_PREFIX):
            raise SystemExit("the wrapper's charge failed")
        return charge(name, hours, basis)

    monkeypatch.setattr(lv, "charge", fails)
    with pytest.raises(SystemExit, match="the wrapper's charge failed"):
        ad.summarize()
    assert not (ledger / "d2f-A-closing.json").exists()
    assert ad.check_receipt()["charge_name"].endswith("inner")  # the evidence is kept
    assert _wrapper_charges() == []
    with pytest.raises(SystemExit, match="is missing"):
        ad.check_closed()
    with pytest.raises(SystemExit, match="is missing"):
        ad.accept()
    monkeypatch.setattr(lv, "charge", charge)
    with pytest.raises(SystemExit, match="written once"):
        ad.summarize()  # no automatic repair: the maintainer's reconciliation


def test_a_closing_that_does_not_bind_its_charges_is_refused(ledger, monkeypatch):
    ad.run()
    monkeypatch.setattr(d2f, "summarize", _inner(ledger))
    ad.summarize()
    closing = json.loads((ledger / "d2f-A-closing.json").read_text("utf-8"))
    closing["wrapper_charge"]["hours"] += 1.0
    (ledger / "d2f-A-closing.json").write_text(json.dumps(closing), "utf-8")
    with pytest.raises(SystemExit, match="does not bind"):
        ad.check_closed()


def test_a_set_a_that_is_not_futile_stops_with_the_request(ledger, monkeypatch):
    ad.run()
    monkeypatch.setattr(d2f, "summarize", _inner(ledger, futile=False))
    with pytest.raises(SystemExit, match="set B needs .* beyond what is authorized"):
        ad.summarize()
    assert ad.check_receipt()["charge_name"].endswith("inner")
    assert ad.check_closed()["state"] == "final"  # the record is closed; set B is the STOP


def test_a_stop_after_the_record_still_binds_it_and_propagates(ledger, monkeypatch):
    ad.run()
    monkeypatch.setattr(d2f, "summarize", _inner(ledger, fail="STOP for the maintainer: x"))
    with pytest.raises(SystemExit, match="STOP for the maintainer: x"):
        ad.summarize()
    assert ad.check_receipt()["charge_name"].endswith("inner")
    assert len(_wrapper_charges()) == 1
    closing = json.loads((ledger / "d2f-A-closing.json").read_text("utf-8"))
    assert closing["state"] == "stopped" and "STOP for the maintainer: x" in closing["stop"]
    with pytest.raises(SystemExit, match="closed in a STOP"):
        ad.check_closed()  # never a success


def test_an_exception_before_the_record_charges_the_wrapper_only(ledger, monkeypatch):
    ad.run()

    def fails(set_name):
        budgeted.charge(f"{ad.SUMMARY_CHARGE_PREFIX}inner", 0.001, "the frozen summary")
        raise SystemExit("an inner STOP before the record")

    monkeypatch.setattr(d2f, "summarize", fails)
    clock = iter([100.0])  # a deterministic process clock: 10 s for the wrapper's whole call
    monkeypatch.setattr(ad.time, "process_time", lambda: next(clock, 110.0))
    with pytest.raises(SystemExit, match="an inner STOP"):
        ad.summarize()
    assert not (ledger / "d2f-A.json").exists()
    assert not (ledger / "d2f-A-closing.json").exists()
    assert ad.RECEIPTS not in budgeted.load()
    assert _wrapper_charges()[0]["hours"] == pytest.approx((10.0 - 3.6) / 3600.0)


def test_a_record_without_a_bound_receipt_is_not_proven(ledger, monkeypatch):
    ad.run()
    budgeted.charge(HISTORICAL, 0.001, "an earlier summary")
    (ledger / "d2f-A.json").write_text(json.dumps({"futile_after_A": True}), "utf-8")
    with pytest.raises(SystemExit, match="not proven"):
        ad.check_receipt()
    with pytest.raises(SystemExit, match="written once"):
        ad.summarize()


def test_two_new_charges_in_one_attempt_are_a_stop(ledger, monkeypatch):
    ad.run()

    def twice(set_name):
        _inner(ledger)(set_name)
        budgeted.charge(f"{ad.SUMMARY_CHARGE_PREFIX}again", 0.001, "a second charge")

    monkeypatch.setattr(d2f, "summarize", twice)
    with pytest.raises(SystemExit, match="binding is uncertain"):
        ad.summarize()
    assert ad.RECEIPTS not in budgeted.load()
