"""v0.5.3 stage B: the budget ledger and the other caps (#217; the maintainer's decision of
2026-11-11, `docs/plans/v0.5.3-stageB0-design.md`). ``method_status: not_validated``.

Like stage A's ``ledger_a.py``, it imports v0.5.2's ``budgeted.py`` and ``driver.py`` unchanged
(T2a's fingerprint does not move) and points their module constants at a ledger of its own: one
line, ``stage_b``, of 150 CPU-h, with nothing spent before. B0 is a sub-line of 30 CPU-h: its
parts are the ones named ``b0_*``. ``budgeted``'s stop rules apply unchanged. Import this module
before any use of ``budgeted`` in a stage B script.

**The other caps** (``caps.json``): review tokens and agent-days.

- **Review tokens** follow the maintainer's rule of 2026-11-11, which applies to stage B only and
  replaces there the decision of 2026-11-09. The count is each Codex conversation's uncached input
  plus its output, and every independent review session. A Codex conversation's figure is its
  last turn's ``input_tokens - cached_input_tokens + output_tokens``: the Codex CLI's
  ``turn.completed`` usage is cumulative over the conversation (#217, comment 6799452280).
- **Caps:** B0 1.5 M, stage B 4.5 M. A stop at 80 % of either.
- **Agent-days:** Claude's session transcripts since the stage began, as wall clock over 8-hour
  days (an upper bound), with the active time also recorded. Caps: B0 2, stage B 8."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
V052 = ROOT / "docs/validation/v0.5.2/stage2"
for p in (str(ROOT / "src"), str(V052)):
    if p not in sys.path:
        sys.path.insert(0, p)

import budgeted  # noqa: E402

SECTION = "stage_b"
CAP_HOURS = 150.0
B0_CAP_HOURS = 30.0
ALLOCATIONS = {  # declared before any dispatch; B1's 120 CPU-h stay unallocated until approved
    "b0_bound": 4.0,
    "b0_reserve": 25.9,  # 0.1 CPU-h of B0 left unallocated for its charges (smoke, summaries)
    "b1_unallocated": 120.0,
}  # 149.9 allocated, the whole line: the charges must fit in CHARGES_ROOM
V052_LEDGER = V052 / "ledger.json"
CAPS = HERE / "caps.json"
CODEX_EVENTS = ROOT / ".cache/v053/stageB/codex"
AGENT_TIME = ROOT / ".cache/v052/tools/agent_time.py"
TRANSCRIPTS = Path.home() / ".claude/projects/C--Projetos-refute"
STAGE_START = "2026-11-11T14:45:00"
OVERSHOOT = 1.10  # the driver may pass a part's cap by up to 10 %
TOKEN_CAPS = {"b0": 1_500_000, "stage_b": 4_500_000}
DAY_CAPS = {"b0": 2.0, "stage_b": 8.0}
TOKEN_STOP = 0.80  # the maintainer: stop at 80 % of a cap

CHARGES_ROOM = 0.1  # kept outside the line for the charges (smoke, summaries)

budgeted.LEDGER = HERE / "ledger.json"
# ``budgeted.total_projection`` counts the charges plus the whole line (Codex's round 1): the line
# is the cap less the charges' room, so that the projection stays within 150 CPU-h
budgeted.LINES = {SECTION: CAP_HOURS - CHARGES_ROOM}
budgeted.HARD_MAXIMUM = CAP_HOURS
budgeted.SPENT_BEFORE = 0.0


def _atomic_save(ledger: dict) -> None:
    """``budgeted.save``'s bytes, written atomically (a temporary file replaced)."""
    tmp = budgeted.LEDGER.with_name(budgeted.LEDGER.name + ".tmp")
    tmp.write_text(json.dumps(ledger, indent=1, sort_keys=True) + "\n", "utf-8", newline="\n")
    tmp.replace(budgeted.LEDGER)


budgeted.save = _atomic_save


def _rows() -> dict:
    return budgeted.load().get("sections", {}).get(SECTION, {}).get("parts", {})


def _charges(prefix: str = "") -> float:
    charges = budgeted.load().get("charges", [])
    return sum(c["hours"] for c in charges if c["name"].startswith(prefix))


def declare() -> None:
    """Declare the allocations. A part that has spent nothing (no attempt either) takes the
    design's value; a part that has spent keeps its persisted allocation (transfers included).
    The allocations plus the charges must stay within 150 CPU-h, and B0's within 30 (Codex's
    round 1: ``budgeted``'s projection counts the charges)."""
    merged = dict(ALLOCATIONS)
    transferred = bool(budgeted.load().get("transfers"))  # after a transfer, persisted rows rule
    for p, r in _rows().items():
        if transferred or r.get("spent_hours", 0.0) > 0 or r.get("attempts"):
            merged[p] = r["allocation_hours"]
    if sum(merged.values()) + _charges() > CAP_HOURS + 1e-9:
        raise SystemExit("the allocations and charges pass the 150 CPU-h cap")
    if _charges() > CHARGES_ROOM + 1e-9:
        raise SystemExit("the charges pass their 0.1 CPU-h room: a STOP")
    b0 = sum(v for k, v in merged.items() if k.startswith("b0_")) + _charges("b0_")
    if b0 > B0_CAP_HOURS + 1e-9:
        raise SystemExit("B0's allocations and charges pass its 30 CPU-h sub-cap")
    budgeted.declare(SECTION, merged)


def transfer(source: str, target: str, hours: float, reason: str) -> None:
    """A prospective transfer between parts, recorded before the target runs; B0's parts may only
    trade among themselves (its sub-cap)."""
    if source.startswith("b0_") != target.startswith("b0_"):
        raise SystemExit("a transfer across B0's sub-cap is refused")
    rows = _rows()
    alloc = {p: r["allocation_hours"] for p, r in rows.items()}
    if alloc[source] - hours < rows.get(source, {}).get("spent_hours", 0.0):
        raise SystemExit(f"{source}: cannot give back hours it has spent")
    alloc[source] -= hours
    alloc[target] = alloc.get(target, 0.0) + hours
    budgeted.declare(SECTION, alloc)
    book = budgeted.load()
    book.setdefault("transfers", []).append(
        {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "from": source,
         "to": target, "hours": hours, "reason": reason}
    )  # fmt: skip
    budgeted.save(book)


def spent() -> float:
    return budgeted.spent(budgeted.load())


def b0_spent() -> float:
    """B0's parts (their attempts included) and the charges named ``b0_*`` (probes, smokes)."""
    book = budgeted.load()
    total = sum(c["hours"] for c in book.get("charges", []) if c["name"].startswith("b0_"))
    for p, r in _rows().items():
        if p.startswith("b0_"):
            total += r.get("spent_hours", 0.0)
            total += sum(a["spent_hours"] for a in r.get("attempts", []))
    return total


def charges_left() -> float:
    return CHARGES_ROOM - _charges()


def charge(name: str, hours: float, basis: str) -> None:
    """``budgeted.charge``: consumption outside a part (a smoke, a summary), charged once by name.
    The consumption happened, so it is always recorded; a STOP follows if the charges pass their
    room (Codex's round 2)."""
    budgeted.charge(name, hours, basis)
    if _charges() > CHARGES_ROOM + 1e-12:
        raise SystemExit("the charges passed their 0.1 CPU-h room: a STOP")


def hard_cap(part: str, workers: int, max_shard_seconds: float) -> float:
    """The part's strict cap: what is left of the 150 CPU-h (and, for a B0 part, of B0's 30)
    minus one batch's in-flight reserve, over the driver's 10 % overshoot, and at most 1.5 times
    the part's allocation."""
    rows = _rows()
    if part not in rows:
        raise SystemExit(f"{part}: not declared")
    reserve = workers * max_shard_seconds / 3600.0
    left = CAP_HOURS - spent() - reserve
    if part.startswith("b0_"):
        left = min(left, B0_CAP_HOURS - b0_spent() - reserve)
    cap = min(left, 1.5 * rows[part]["allocation_hours"]) / OVERSHOOT
    if cap <= 0:
        raise SystemExit(f"{part}: no room under the caps: a STOP")
    return cap


def codex_tokens() -> dict:
    """Per Codex conversation (``<b0|b1>-<name>-r<round>-events.jsonl``), the last round's
    cumulative uncached input plus output; totals for B0 and stage B."""
    last: dict[str, tuple[int, int]] = {}
    for path in sorted(CODEX_EVENTS.glob("*-events.jsonl")):
        m = re.fullmatch(r"(.+)-r(\d+)-events\.jsonl", path.name)
        if not m:
            continue
        usage = None
        for line in path.read_text("utf-8-sig", errors="replace").splitlines():
            line = line.strip().lstrip("﻿")
            if not line.startswith("{"):
                continue
            try:
                event = json.loads(line)
            except ValueError:
                continue
            # the event's own type, not the text (a command's output may quote it)
            if event.get("type") == "turn.completed" and "usage" in event:
                usage = event["usage"]
        if usage is None:
            continue
        count = usage["input_tokens"] - usage["cached_input_tokens"] + usage["output_tokens"]
        conv, rnd = m.group(1), int(m.group(2))
        if conv not in last or rnd > last[conv][0]:
            last[conv] = (rnd, count)
    per = {conv: c for conv, (_, c) in last.items()}
    return {
        "conversations": per,
        "b0": sum(c for k, c in per.items() if k.startswith("b0")),
        "stage_b": sum(per.values()),
    }


def independent_review_tokens() -> int:
    doc = json.loads(CAPS.read_text("utf-8"))
    return int(doc.get("independent_review_tokens", 0))


def agent_days() -> tuple[float, float]:
    """Claude's agent-days since stage B began: (wall clock, active), by the transcripts."""
    out = subprocess.run(
        [sys.executable, str(AGENT_TIME), str(TRANSCRIPTS), STAGE_START],
        capture_output=True, text=True, check=True,
    ).stdout  # fmt: skip
    wall = float(out.split("wall ")[1].split(" h")[0]) / 8.0
    active = float(out.split("= ")[1].split(" agent-days")[0])
    return wall, active


def check_caps(step: str, reserve_days: float, reserve_tokens: int, in_b0: bool = True) -> dict:
    """Before a step: tokens (with the step's reservation) under 80 % of their caps, and the
    agent-days (with the reservation) under theirs; recorded in ``caps.json``. A STOP otherwise."""
    doc = json.loads(CAPS.read_text("utf-8"))
    codex = codex_tokens()
    review = independent_review_tokens()
    wall, active = agent_days()
    tokens = {"b0": codex["b0"] + (review if in_b0 else 0), "stage_b": codex["stage_b"] + review}
    entry = {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "step": step,
             "codex_tokens": codex, "independent_review_tokens": review,
             "agent_days_wall": round(wall, 2), "agent_days_active": round(active, 2),
             "cpu_hours": {"stage_b": round(spent(), 3), "b0": round(b0_spent(), 3)},
             "reserved": {"agent_days": reserve_days, "review_tokens": reserve_tokens}}  # fmt: skip
    doc["entries"].append(entry)
    CAPS.write_text(json.dumps(doc, indent=1) + "\n", "utf-8", newline="\n")
    scopes = ("b0", "stage_b") if in_b0 else ("stage_b",)
    for scope in scopes:
        if tokens[scope] + reserve_tokens >= TOKEN_STOP * TOKEN_CAPS[scope]:
            raise SystemExit(f"{scope}: review tokens would reach 80 % of the cap: a STOP")
        if wall + reserve_days >= DAY_CAPS[scope]:
            raise SystemExit(f"{scope}: the agent-day cap (wall-clock bound) is reached: a STOP")
    return entry


def v052_ledger_sha256() -> str:
    return hashlib.sha256(V052_LEDGER.read_bytes()).hexdigest()


if __name__ == "__main__":
    if sys.argv[1:] == ["declare"]:
        declare()
        print("declared; spent", round(spent(), 3), "CPU-h of", CAP_HOURS)
    elif sys.argv[1:2] == ["check"]:
        print(json.dumps(check_caps(sys.argv[2], float(sys.argv[3]), int(sys.argv[4])), indent=1))
    else:
        print(json.dumps(codex_tokens(), indent=1))
