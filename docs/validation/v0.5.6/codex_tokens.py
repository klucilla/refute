"""Review tokens of Codex conversations, counted from their event files.

The maintainer's decisions of 2026-11-21 (21:00, item 3, and 22:30, item 1; #218): a conversation
whose rounds were run as new Codex sessions (the conversation "pause") was undercounted by the
v0.5.5 ledger's rule, which took each conversation's last round. The fix lives here, in a new
module, so that ``docs/validation/v0.5.5/ledger_v055.py`` keeps the bytes R1's records anchor.
The figures already recorded keep their bytes; the correction is
``docs/validation/v0.5.5/pause-tokens-correction.md``.

**The rule:** sum the last completed round's net usage (``input_tokens - cached_input_tokens +
output_tokens``) for each distinct thread. Rounds that resume one Codex thread (the same
``thread.started`` id; ``codex_affinity.ps1 -Thread``) report cumulative usage, so a thread counts
by its last round; rounds run as new sessions each start a thread of their own and are summed.

**The contract:**
- a conversation of one counted round counts even without a thread id;
- in a conversation of several counted rounds, every counted round must name its thread;
- a file that names two different thread ids is refused, with or without a usage event;
- rounds are ordered by their number (``r10`` after ``r2``).

Event files are named ``<conversation>-r<round>-events.jsonl``.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

NAME = re.compile(r"(.+)-r(\d+)-events\.jsonl")


def _read(path: Path) -> tuple[set[str], dict | None]:
    """The thread ids a file names and its last ``turn.completed`` usage."""
    usage, ids = None, set()
    for line in path.read_text("utf-8-sig", errors="replace").splitlines():
        line = line.strip().lstrip("﻿")
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get("type") == "thread.started" and event.get("thread_id"):
            ids.add(event["thread_id"])
        if event.get("type") == "turn.completed" and "usage" in event:
            usage = event["usage"]
    return ids, usage


def count(folder: Path) -> dict:
    """Per conversation in ``folder``, its review tokens, and the folder's total, as
    ``{"conversations": {...}, "phase": total}`` (the shape of ``ledger_v055.codex_tokens``)."""
    rounds: dict[str, list[tuple[int, str | None, int]]] = {}
    for path in sorted(Path(folder).glob("*-events.jsonl")):
        m = NAME.fullmatch(path.name)
        if not m:
            continue
        ids, usage = _read(path)
        if len(ids) > 1:
            raise SystemExit(f"{path.name}: conflicting thread ids; refused")
        if usage is None:
            continue
        net = usage["input_tokens"] - usage["cached_input_tokens"] + usage["output_tokens"]
        rounds.setdefault(m.group(1), []).append((int(m.group(2)), next(iter(ids), None), net))
    per = {}
    for conv, items in rounds.items():
        if len(items) > 1 and any(thread is None for _, thread, _ in items):
            raise SystemExit(f"{conv}: a round of several has no thread id; refused")
        last: dict[str | None, tuple[int, int]] = {}
        for rnd, thread, net in items:
            if thread not in last or rnd > last[thread][0]:
                last[thread] = (rnd, net)
        per[conv] = sum(n for _, n in last.values())
    return {"conversations": per, "phase": sum(per.values())}
