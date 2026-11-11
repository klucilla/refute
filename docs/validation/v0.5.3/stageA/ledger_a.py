"""v0.5.3 stage A: the budget ledger (#217; `docs/plans/v0.5.3-stageA-design.md`). It imports
v0.5.2's ``budgeted.py`` and ``driver.py`` unchanged (so T2a's fingerprint does not move) and
points their module constants at a ledger of its own: one line, ``stage_a``, of 50 CPU-h, the
maintainer's cap of 2026-11-11, with nothing spent before. ``budgeted``'s functions read these
constants when they are called, so every stop rule of v0.5.2 applies here unchanged. Import this
module before any use of ``budgeted`` in a stage A script. ``method_status: not_validated``."""

from __future__ import annotations

import hashlib
import json
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

SECTION = "stage_a"
CAP_HOURS = 50.0
ALLOCATIONS = {  # the design's initial allocations, declared before any dispatch
    "a_refusals": 4.0,
    "b_d2_bound": 8.0,
    "c1_background_audit": 2.0,
    "c2_t2a_bound": 4.0,
    "c3_above_20": 18.0,
    "d_geometry": 6.0,
    "reserve": 8.0,
}
V052_LEDGER = V052 / "ledger.json"
CAPS = HERE / "caps.json"
AGENT_TIME = ROOT / ".cache/v052/tools/agent_time.py"
TRANSCRIPTS = Path.home() / ".claude/projects/C--Projetos-refute"
STAGE_START = "2026-11-11T05:55:00"
OVERSHOOT = 1.10  # the driver may pass a part's cap by up to 10 %

budgeted.LEDGER = HERE / "ledger.json"
budgeted.LINES = {SECTION: CAP_HOURS}
budgeted.HARD_MAXIMUM = CAP_HOURS
budgeted.SPENT_BEFORE = 0.0


def _rows() -> dict:
    return budgeted.load().get("sections", {}).get(SECTION, {}).get("parts", {})


def declare() -> None:
    """Initialize the missing allocations only: persisted ones, transfers included, are kept."""
    current = {p: r["allocation_hours"] for p, r in _rows().items()}
    merged = {**ALLOCATIONS, **current}
    if abs(sum(merged.values()) - CAP_HOURS) > 1e-9:
        raise SystemExit("the allocations do not add up to the 50 CPU-h cap")
    budgeted.declare(SECTION, merged)


def transfer(source: str, target: str, hours: float, reason: str) -> None:
    """A prospective transfer between parts, recorded in the ledger before the target runs; the
    source's spent attempts stay counted (``budgeted.declare`` archives a changed row)."""
    rows = _rows()
    alloc = {p: r["allocation_hours"] for p, r in rows.items()}
    spent_source = rows.get(source, {}).get("spent_hours", 0.0)
    if alloc[source] - hours < spent_source:
        raise SystemExit(f"{source}: cannot give back hours it has spent")
    alloc[source] -= hours
    alloc[target] = alloc.get(target, 0.0) + hours  # a new part may be created by a transfer
    budgeted.declare(SECTION, alloc)
    book = budgeted.load()
    book.setdefault("transfers", []).append(
        {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "from": source,
         "to": target, "hours": hours, "reason": reason}
    )  # fmt: skip
    budgeted.save(book)


def spent() -> float:
    return budgeted.spent(budgeted.load())


def hard_cap(part: str, workers: int, max_shard_seconds: float) -> float:
    """The part's strict cap (the design's "Accounting"): what is left of the 50 CPU-h minus the
    in-flight reserve of one batch (workers times the shard limit), over the driver's 10 %
    overshoot, and at most 1.5 times the part's current allocation in the ledger. This attempt's
    own spending is not added back: a resumed part keeps counting what it spent."""
    rows = _rows()
    if part not in rows:
        raise SystemExit(f"{part}: not declared")
    reserve = workers * max_shard_seconds / 3600.0
    left = CAP_HOURS - spent() - reserve
    cap = min(left, 1.5 * rows[part]["allocation_hours"]) / OVERSHOOT
    if cap <= 0:
        raise SystemExit(f"{part}: no room under the 50 CPU-h cap: a STOP")
    return cap


def agent_days() -> tuple[float, float]:
    """Claude's agent-days since stage A began: (wall clock, active), by the transcripts."""
    out = subprocess.run(
        [sys.executable, str(AGENT_TIME), str(TRANSCRIPTS), STAGE_START],
        capture_output=True, text=True, check=True,
    ).stdout  # fmt: skip
    wall = float(out.split("wall ")[1].split(" h")[0]) / 8.0
    active = float(out.split("= ")[1].split(" agent-days")[0])
    return wall, active


def check_caps(reserve_days: float, reserve_tokens: int) -> None:
    """Before a step: the review tokens and the agent-days, with the step's reservation, must stay
    under their caps; the check is recorded in ``caps.json``. Refused otherwise (a STOP)."""
    doc = json.loads(CAPS.read_text("utf-8"))
    tokens = max(e["review_tokens"] for e in doc["entries"])
    wall, active = agent_days()
    entry = {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "step": "check",
             "review_tokens": tokens, "agent_days_wall": round(wall, 2),
             "agent_days_active": round(active, 2),
             "reserved": {"agent_days": reserve_days, "review_tokens": reserve_tokens}}  # fmt: skip
    doc["entries"].append(entry)
    CAPS.write_text(json.dumps(doc, indent=1) + "\n", "utf-8", newline="\n")
    if tokens + reserve_tokens > doc["caps"]["review_tokens"]:
        raise SystemExit("the review-token cap would be passed: a STOP")
    if wall + reserve_days > doc["caps"]["agent_days"]:
        raise SystemExit("the agent-day cap (wall-clock bound) would be passed: a STOP")


def v052_ledger_sha256() -> str:
    return hashlib.sha256(V052_LEDGER.read_bytes()).hexdigest()


if __name__ == "__main__":
    declare()
    print("declared; spent", round(spent(), 3), "CPU-h of", CAP_HOURS)
