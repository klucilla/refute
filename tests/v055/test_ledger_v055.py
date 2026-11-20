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
    # the allocation (2.5) less archived attempts (none): the driver compares it with the
    # identity's whole consumption, so the 2.0 already spent is not subtracted again
    assert lv.hard_cap("r1_t2ae_1", 10, 1200.0) == pytest.approx(2.5 / lv.OVERSHOOT)
