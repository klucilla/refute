"""v0.5.5: R2's own line of caps (``docs/validation/v0.5.5/r2_line.py``; the maintainer's
decisions of 2026-11-21, 13:30, item 1). Offline, on a temporary ledger."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[2] / "docs/validation/v0.5.5"
STAGE2 = Path(__file__).resolve().parents[2] / "docs/validation/v0.5.2/stage2"
for p in (str(HERE), str(STAGE2)):
    if p not in sys.path:
        sys.path.insert(0, p)
import budgeted  # noqa: E402

BOUND = ("LEDGER", "LINES", "HARD_MAXIMUM", "SPENT_BEFORE", "save")
r2 = lv = None


@pytest.fixture(autouse=True)
def module(monkeypatch):
    global r2, lv
    for name in BOUND:
        monkeypatch.setattr(budgeted, name, getattr(budgeted, name))
    if r2 is None:
        spec = importlib.util.spec_from_file_location("r2_line_under_test", HERE / "r2_line.py")
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        r2 = m
    lv = r2.lv
    lv.bind()
    return r2


@pytest.fixture
def ledger(tmp_path, monkeypatch):
    monkeypatch.setattr(budgeted, "LEDGER", tmp_path / "ledger.json")
    monkeypatch.setattr(budgeted, "save", lv._atomic_save)
    monkeypatch.setattr(lv, "HERE", tmp_path)
    monkeypatch.setattr(lv, "LOCK", tmp_path / "ledger.lock")
    monkeypatch.setattr(lv, "CAPS_LOCK", tmp_path / "caps.lock")
    monkeypatch.setattr(r2, "RECORD", tmp_path / "r2-caps.json")
    monkeypatch.setattr(lv, "check_caps", lambda *a, **k: {})
    budgeted.declare("v055", {"r1_reserve": 1.0})
    return tmp_path


def test_the_line_opens_once_with_its_caps(ledger):
    line = r2.open_line()
    assert line["caps"] == {
        "review_tokens": 1_000_000,
        "agent_days": 5.0,
        "cpu_hours_new_version": 0.0,
    }
    assert line["stop_fraction"] == 0.80
    before = (ledger / "ledger.json").read_bytes()
    assert r2.open_line() == line
    assert (ledger / "ledger.json").read_bytes() == before
    book = budgeted.load()
    book["r2_line"]["caps"]["review_tokens"] = 2_000_000
    budgeted.save(book)
    with pytest.raises(SystemExit, match="differs"):
        r2.open_line()


def test_no_check_before_the_line(ledger):
    with pytest.raises(SystemExit, match="not open"):
        r2.check("x", 0.0, 0)


def test_only_r2_conversations_count(ledger, monkeypatch):
    monkeypatch.setattr(
        lv, "codex_tokens", lambda: {"conversations": {"g1": 900_000, "r2args": 100, "r2x": 20}}
    )
    assert r2.tokens() == {"conversations": {"r2args": 100, "r2x": 20}, "r2": 120}


def _events(folder, name, inp, cached, out):
    folder.mkdir(parents=True, exist_ok=True)
    usage = {"input_tokens": inp, "cached_input_tokens": cached, "output_tokens": out}
    (folder / f"{name}-r1-events.jsonl").write_text(
        json.dumps({"type": "turn.completed", "usage": usage}) + "\n", "utf-8"
    )


def test_r2_conversations_count_only_on_r2_s_line(tmp_path, monkeypatch):
    # the maintainer's decisions of 2026-11-21 (15:20), item 4: R2's events live apart
    v055, r2dir = tmp_path / "codex", tmp_path / "r2codex"
    _events(v055, "g1", 1000, 400, 50)  # 650
    _events(r2dir, "r2args", 300, 100, 20)  # 220
    monkeypatch.setattr(lv, "CODEX_EVENTS", v055)
    monkeypatch.setattr(r2, "CODEX_EVENTS", r2dir)
    assert r2.tokens() == {"conversations": {"r2args": 220}, "r2": 220}
    assert lv.codex_tokens()["phase"] == 650
    assert r2.both_lines() == {"v055_without_r2": 650, "r2": 220, "v055_with_r2": 870}
    assert lv.CODEX_EVENTS == v055  # restored after the count


@pytest.mark.parametrize(
    "tokens, wall, reserve_days, reserve_tokens, match",
    [
        (799_999, 0.0, 0.0, 1, "tokens"),
        (700_000, 0.0, 0.0, 100_000, "tokens"),
        (0, 3.9, 0.1, 0, "agent-days"),
        (0, 4.0, 0.0, 0, "agent-days"),
    ],
)
def test_the_80_percent_stops(ledger, monkeypatch, tokens, wall, reserve_days, reserve_tokens,
                              match):  # fmt: skip
    r2.open_line()
    monkeypatch.setattr(r2, "tokens", lambda: {"conversations": {}, "r2": tokens})
    monkeypatch.setattr(r2, "agent_days", lambda since: (wall, 0.1))
    with pytest.raises(SystemExit, match=match):
        r2.check("s", reserve_days, reserve_tokens)
    entries = json.loads((ledger / "r2-caps.json").read_text("utf-8"))["entries"]
    assert entries[-1]["step"] == "s"  # recorded before the STOP


def test_a_check_under_the_caps_passes_and_checks_v055_too(ledger, monkeypatch):
    r2.open_line()
    seen = []
    monkeypatch.setattr(lv, "check_caps", lambda step, d, t: seen.append((step, d, t)) or {})
    monkeypatch.setattr(r2, "tokens", lambda: {"conversations": {}, "r2": 100_000})
    monkeypatch.setattr(r2, "agent_days", lambda since: (1.0, 0.5))
    entry = r2.check("args", 0.5, 200_000)
    assert entry["cpu_hours_new_version"] == 0.0
    assert seen == [("r2: args", 0.5, 200_000)]
