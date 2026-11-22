"""The review-token count of Codex conversations (``docs/validation/v0.5.6/codex_tokens.py``; the
maintainer's decisions of 2026-11-21, 21:00, item 3, and 22:30, item 1). Offline, on synthetic
event files. ``docs/validation/v0.5.5/ledger_v055.py`` keeps its anchored bytes."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
V056 = ROOT / "docs/validation/v0.5.6"
if str(V056) not in sys.path:
    sys.path.insert(0, str(V056))
import codex_tokens as ct  # noqa: E402


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


def test_a_resumed_thread_counts_by_its_last_round(tmp_path):
    # one thread resumed: usage is cumulative, the last round holds it all
    _round(tmp_path, "g1", 1, ["t-1"], 1000, 400, 50)  # 650
    _round(tmp_path, "g1", 2, ["t-1"], 2500, 1500, 80)  # 1080, cumulative
    assert ct.count(tmp_path) == {"conversations": {"g1": 1080}, "phase": 1080}


def test_rounds_run_as_new_sessions_are_summed(tmp_path):
    # the "pause" case: every round a new session (its own thread), usage per round
    _round(tmp_path, "pause", 1, ["t-a"], 582_961, 499_328, 9_422)  # 93,055
    _round(tmp_path, "pause", 2, ["t-b"], 370_332, 327_168, 4_222)  # 47,386
    _round(tmp_path, "pause", 3, ["t-c"], 429_766, 382_848, 5_400)  # 52,318
    assert ct.count(tmp_path)["conversations"] == {"pause": 192_759}
    # the count before the fix took round 3 alone: the undercount this test reproduces
    assert _last_round_only(tmp_path) == 52_318


def test_mixed_threads_and_round_numbers_past_nine(tmp_path):
    _round(tmp_path, "c", 1, ["t-1"], 100, 0, 10)  # 110
    _round(tmp_path, "c", 2, ["t-1"], 300, 100, 20)  # 220, resumes t-1
    _round(tmp_path, "c", 10, ["t-1"], 500, 150, 30)  # 380, r10 comes after r2
    _round(tmp_path, "c", 3, ["t-2"], 50, 0, 5)  # 55, a new session
    _round(tmp_path, "d", 1, [], 10, 0, 1)  # 11, one round without thread id: it counts
    assert ct.count(tmp_path) == {"conversations": {"c": 435, "d": 11}, "phase": 446}


def test_a_round_of_several_without_thread_id_is_refused(tmp_path):
    _round(tmp_path, "e", 1, ["t-1"], 100, 0, 10)
    _round(tmp_path, "e", 2, [], 300, 100, 20)  # a resumed round that lost its id
    with pytest.raises(SystemExit, match="no thread id"):
        ct.count(tmp_path)


def test_conflicting_thread_ids_in_one_file_are_refused(tmp_path):
    _round(tmp_path, "f", 1, ["t-1", "t-2"], 100, 0, 10)
    with pytest.raises(SystemExit, match="conflicting"):
        ct.count(tmp_path)


def test_conflicting_thread_ids_are_refused_even_without_usage(tmp_path):
    events = [{"type": "thread.started", "thread_id": t} for t in ("t-1", "t-2")]
    (tmp_path / "g-r1-events.jsonl").write_text(
        "\n".join(json.dumps(e) for e in events) + "\n", "utf-8"
    )
    with pytest.raises(SystemExit, match="conflicting"):
        ct.count(tmp_path)


def test_the_v055_ledger_keeps_its_anchored_bytes():
    # the decision of 2026-11-21 (22:30), item 1: the SHA-256 R1's records anchor
    data = (ROOT / "docs/validation/v0.5.5/ledger_v055.py").read_bytes()
    assert (
        hashlib.sha256(data).hexdigest()
        == "65e65400357b5866f27cc83c8a7858fb404ee9af39cb9460737d24cf7fcd0a17"
    )
