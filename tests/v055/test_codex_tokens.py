"""v0.5.5: the review-token count of Codex conversations (``ledger_v055.codex_tokens``; the
maintainer's decision of 2026-11-21, 21:00, item 3). Offline, on synthetic event files."""

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


@pytest.fixture
def lv(monkeypatch):
    """``ledger_v055``, loaded afresh, with ``budgeted``'s attributes restored after the test
    (loading it binds ``budgeted`` to v0.5.5's ledger)."""
    for name in BOUND:
        monkeypatch.setattr(budgeted, name, getattr(budgeted, name))
    spec = importlib.util.spec_from_file_location("ledger_v055_under_test", HERE / "ledger_v055.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _round(folder: Path, conv: str, rnd: int, threads: list[str], inp: int, cached: int, out: int):
    folder.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps({"type": "thread.started", "thread_id": t}) for t in threads]
    usage = {"input_tokens": inp, "cached_input_tokens": cached, "output_tokens": out}
    lines.append(json.dumps({"type": "turn.completed", "usage": usage}))
    (folder / f"{conv}-r{rnd}-events.jsonl").write_text("\n".join(lines) + "\n", "utf-8")


def _last_round_only(folder: Path) -> int:
    """The count before the fix: each conversation's last round alone."""
    last: dict[str, tuple[int, int]] = {}
    for path in folder.glob("*-events.jsonl"):
        conv, rnd = path.name.rsplit("-r", 1)[0], int(path.name.rsplit("-r", 1)[1].split("-")[0])
        usage = json.loads(path.read_text("utf-8").splitlines()[-1])["usage"]
        n = usage["input_tokens"] - usage["cached_input_tokens"] + usage["output_tokens"]
        if conv not in last or rnd > last[conv][0]:
            last[conv] = (rnd, n)
    return sum(n for _, n in last.values())


def test_a_resumed_thread_counts_by_its_last_round(lv, tmp_path, monkeypatch):
    # one thread resumed: usage is cumulative, the last round holds it all
    _round(tmp_path, "g1", 1, ["t-1"], 1000, 400, 50)  # 650
    _round(tmp_path, "g1", 2, ["t-1"], 2500, 1500, 80)  # 1080, cumulative
    monkeypatch.setattr(lv, "CODEX_EVENTS", tmp_path)
    assert lv.codex_tokens() == {"conversations": {"g1": 1080}, "phase": 1080}


def test_rounds_run_as_new_sessions_are_summed(lv, tmp_path, monkeypatch):
    # the "pause" case: every round a new session (its own thread), usage per round
    _round(tmp_path, "pause", 1, ["t-a"], 582_961, 499_328, 9_422)  # 93,055
    _round(tmp_path, "pause", 2, ["t-b"], 370_332, 327_168, 4_222)  # 47,386
    _round(tmp_path, "pause", 3, ["t-c"], 429_766, 382_848, 5_400)  # 52,318
    monkeypatch.setattr(lv, "CODEX_EVENTS", tmp_path)
    assert lv.codex_tokens()["conversations"] == {"pause": 192_759}
    # the count before the fix took round 3 alone: the undercount this test reproduces
    assert _last_round_only(tmp_path) == 52_318


def test_mixed_threads_and_round_numbers_past_nine(lv, tmp_path, monkeypatch):
    _round(tmp_path, "c", 1, ["t-1"], 100, 0, 10)  # 110
    _round(tmp_path, "c", 2, ["t-1"], 300, 100, 20)  # 220, resumes t-1
    _round(tmp_path, "c", 10, ["t-1"], 500, 150, 30)  # 380, r10 comes after r2
    _round(tmp_path, "c", 3, ["t-2"], 50, 0, 5)  # 55, a new session
    _round(tmp_path, "d", 1, [], 10, 0, 1)  # 11, one round without thread id: it counts
    monkeypatch.setattr(lv, "CODEX_EVENTS", tmp_path)
    assert lv.codex_tokens() == {"conversations": {"c": 435, "d": 11}, "phase": 446}


def test_a_round_of_several_without_thread_id_is_refused(lv, tmp_path, monkeypatch):
    _round(tmp_path, "e", 1, ["t-1"], 100, 0, 10)
    _round(tmp_path, "e", 2, [], 300, 100, 20)  # a resumed round that lost its id
    monkeypatch.setattr(lv, "CODEX_EVENTS", tmp_path)
    with pytest.raises(SystemExit, match="no thread id"):
        lv.codex_tokens()


def test_conflicting_thread_ids_in_one_file_are_refused(lv, tmp_path, monkeypatch):
    _round(tmp_path, "f", 1, ["t-1", "t-2"], 100, 0, 10)
    monkeypatch.setattr(lv, "CODEX_EVENTS", tmp_path)
    with pytest.raises(SystemExit, match="conflicting"):
        lv.codex_tokens()


def test_conflicting_thread_ids_are_refused_even_without_usage(lv, tmp_path, monkeypatch):
    tmp_path.mkdir(parents=True, exist_ok=True)
    events = [{"type": "thread.started", "thread_id": t} for t in ("t-1", "t-2")]
    (tmp_path / "g-r1-events.jsonl").write_text(
        "\n".join(json.dumps(e) for e in events) + "\n", "utf-8"
    )
    monkeypatch.setattr(lv, "CODEX_EVENTS", tmp_path)
    with pytest.raises(SystemExit, match="conflicting"):
        lv.codex_tokens()
