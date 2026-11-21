"""v0.5.5: the ledger step that raises T2a-E stage 2's allocation before its first start
(``docs/validation/v0.5.5/r1_allocation_step.py``; the maintainer's decisions of 2026-11-21,
10:00, item 1). Offline, on a temporary ledger."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[2] / "docs/validation/v0.5.5"
STAGE2 = Path(__file__).resolve().parents[2] / "docs/validation/v0.5.2/stage2"
for p in (str(HERE), str(STAGE2)):
    if p not in sys.path:
        sys.path.insert(0, p)
import budgeted  # noqa: E402  (v0.5.2's, unbound: importing it changes nothing)

BOUND = ("LEDGER", "LINES", "HARD_MAXIMUM", "SPENT_BEFORE", "save")
st = lv = None  # set by the ``step`` fixture
SECTION = "v055"


@pytest.fixture(autouse=True)
def step(monkeypatch):
    """Loaded inside a test, never at collection: importing it binds ``budgeted`` to v0.5.5's
    ledger; the bound attributes are restored after each test."""
    global st, lv
    for name in BOUND:
        monkeypatch.setattr(budgeted, name, getattr(budgeted, name))
    if st is None:
        spec = importlib.util.spec_from_file_location(
            "r1_allocation_step_under_test", HERE / "r1_allocation_step.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        st = module
    lv = st.lv
    lv.bind()
    return st


@pytest.fixture
def ledger(tmp_path, monkeypatch):
    monkeypatch.setattr(budgeted, "LEDGER", tmp_path / "ledger.json")
    monkeypatch.setattr(budgeted, "LINES", {SECTION: 63.5})
    monkeypatch.setattr(budgeted, "HARD_MAXIMUM", 64.0)
    monkeypatch.setattr(budgeted, "SPENT_BEFORE", 0.0)
    monkeypatch.setattr(budgeted, "save", lv._atomic_save)
    monkeypatch.setattr(lv, "HERE", tmp_path)
    monkeypatch.setattr(lv, "LOCK", tmp_path / "ledger.lock")
    budgeted.declare(SECTION, {"r1_t2ae_2": 3.1, "r1_t2ae_1c": 1.5, "r1_reserve": 20.3})
    book = budgeted.load()
    book["sections"][SECTION]["parts"]["r1_t2ae_2"]["margin_checks"] = [{"fits": False}]
    budgeted.save(book)
    return tmp_path


def _parts() -> dict:
    return budgeted.load()["sections"][SECTION]["parts"]


def test_the_step_raises_stage_2_once_in_one_write(ledger, monkeypatch):
    saves = []
    save = lv._atomic_save

    def counted(book):
        saves.append(1)
        save(book)

    monkeypatch.setattr(lv, "_atomic_save", counted)  # assert_bound compares the two
    monkeypatch.setattr(budgeted, "save", counted)
    record = st.apply("t2ae2")
    assert len(saves) == 1
    parts = _parts()
    assert parts["r1_t2ae_2"]["allocation_hours"] == 3.55
    assert parts["r1_reserve"]["allocation_hours"] == pytest.approx(19.85)
    assert parts["r1_t2ae_2"]["margin_checks"] == [{"fits": False}]  # the refusal stays
    assert record["from"] == {"r1_reserve": 0.45}
    assert record["allocation_hours"] == {"before": 3.1, "after": 3.55}
    assert record["script_sha256"] == st.own_sha256()
    assert st.apply("t2ae2") == record  # again: unchanged
    assert len(saves) == 1 and len(budgeted.load()["transfers"]) == 1


def test_the_new_allocation_fits_the_runner_s_margin():
    # the runner's own formula (r1_fixed_cap.protected_cap) with 4 workers and 600 s
    cap = (3.55 - 4 * (600 + 20) / 3600 - 4 * 0.5 / 3600) / 1.10
    assert cap >= 1.3 * 1.9871831597222223
    minimum = 1.3 * 1.9871831597222223 * 1.10 + 4 * 620 / 3600 + 4 * 0.5 / 3600
    assert 3.5311 < minimum < 3.5312 < 3.55  # the report's 3.5311 is this minimum, rounded


def test_a_part_that_started_is_never_raised(ledger):
    book = budgeted.load()
    book.setdefault("starts", {})["r1_t2ae_2"] = [{"identity": "x", "utc": "t", "resume": False}]
    budgeted.save(book)
    with pytest.raises(SystemExit, match="ran or started"):
        st.apply("t2ae2")
    assert _parts()["r1_t2ae_2"]["allocation_hours"] == 3.1


@pytest.mark.parametrize(
    "change, match",
    [
        (("r1_t2ae_2", "identity", "x"), "ran or started"),
        (("r1_t2ae_2", "spent_hours", 0.1), "ran or started"),
        (("r1_t2ae_2", "allocation_hours", 3.0), "not the declared allocation"),
        (("r1_reserve", "allocation_hours", 0.4), "cannot fund"),
    ],
)
def test_refusals(ledger, change, match):
    part, key, value = change
    book = budgeted.load()
    book["sections"][SECTION]["parts"][part][key] = value
    budgeted.save(book)
    with pytest.raises(SystemExit, match=match):
        st.apply("t2ae2")
    assert "transfers" not in budgeted.load()


def test_the_line_is_checked(ledger):
    book = budgeted.load()
    book["sections"][SECTION]["parts"]["big"] = {"allocation_hours": 40.0}
    budgeted.save(book)
    with pytest.raises(SystemExit, match="line"):
        st.apply("t2ae2")


def _restore_reserve(book):
    book["sections"][SECTION]["parts"]["r1_reserve"]["allocation_hours"] += 0.45


def _tamper_record(book):
    book["transfers"][0]["from"] = {"r1_reserve": 0.40}


def _tamper_reserve_record(book):
    book["transfers"][0]["reserve_hours"]["after"] = 20.3


def _duplicate(book):
    book["transfers"].append(dict(book["transfers"][0]))


def _pass_the_line(book):
    book["sections"][SECTION]["parts"]["big"] = {"allocation_hours": 40.0}


def _target_back(book):
    book["sections"][SECTION]["parts"]["r1_t2ae_2"]["allocation_hours"] = 3.1


def _extra_field(book):
    book["transfers"][0]["note"] = "x"


@pytest.mark.parametrize(
    "edit",
    [_restore_reserve, _tamper_record, _tamper_reserve_record, _duplicate, _pass_the_line,
     _target_back, _extra_field],
)  # fmt: skip
def test_a_step_on_file_that_no_longer_matches_is_a_stop_with_no_write(ledger, edit):
    # Codex, t2s round 1: the target kept at 3.55 (but for _target_back), the repeat refuses
    st.apply("t2ae2")
    book = budgeted.load()
    edit(book)
    budgeted.save(book)
    before = (ledger / "ledger.json").read_bytes()
    with pytest.raises(SystemExit, match="does not match"):
        st.apply("t2ae2")
    assert (ledger / "ledger.json").read_bytes() == before


def test_an_intact_repeat_writes_nothing(ledger, monkeypatch):
    first = st.apply("t2ae2")
    assert first["reserve_hours"] == {"before": 20.3, "after": 19.85}
    before = (ledger / "ledger.json").read_bytes()
    assert st.apply("t2ae2") == first
    assert (ledger / "ledger.json").read_bytes() == before


def test_a_later_transfer_from_the_reserve_is_accounted_on_repeat(ledger):
    # a later demonstrable transfer (as D2-F's funding records it) takes 2.1 from the reserve
    first = st.apply("t2ae2")
    book = budgeted.load()
    book["sections"][SECTION]["parts"]["r1_reserve"]["allocation_hours"] = 17.75
    book["transfers"].append({"to": "r1_d2f_a", "from": {"r1_d1p_b": 14.2, "r1_reserve": 2.1}})
    budgeted.save(book)
    assert st.apply("t2ae2") == first
    book = budgeted.load()
    book["sections"][SECTION]["parts"]["r1_reserve"]["allocation_hours"] = 18.0
    budgeted.save(book)
    with pytest.raises(SystemExit, match="does not match"):
        st.apply("t2ae2")


def test_an_archived_attempt_is_refused(ledger):
    book = budgeted.load()
    book["sections"][SECTION]["parts"]["r1_t2ae_2"]["attempts"] = [{"spent_hours": 0.0}]
    budgeted.save(book)
    with pytest.raises(SystemExit, match="ran or started"):
        st.apply("t2ae2")
    assert "transfers" not in budgeted.load()
