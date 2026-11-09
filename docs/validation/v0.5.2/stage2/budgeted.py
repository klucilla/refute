"""v0.5.2 stage 2: a section of the budget through the batch driver, under the maintainer's decision
of 2026-11-09 (#216, item 1; ``budget.md``).

A section runs an evenly spaced 5 % of its shards first and projects its whole cost from what they
spent. It **stops if that projection passes 1.5 times the section's budget line**, or if the total
over every section (what is spent, or the best projection of what is not) passes the hard maximum
of 3,100 CPU-h. The rest runs only then, under a cap of 1.5 times the line. The ledger is kept in
``ledger.json`` next to this file; each stop is the driver's, and binds the same way.
``method_status: not_validated``.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from pathlib import Path

import driver

HERE = Path(__file__).resolve().parent
LEDGER = HERE / "ledger.json"
HARD_MAXIMUM = 3100.0
SPENT_BEFORE = 70.0  # budget.md: spent in stage 2 before the maintainer's decision
STOP_FACTOR = 1.5
PROBE_EVERY = 20  # one shard in twenty

LINES = {  # budget.md, CPU-h
    "a0": 1048.0,
    "known_answer": 820.0,
    "adequacy": 95.0,
    "sinusoid": 120.0,
    "selector": 135.0,
    "sabotages": 30.0,
    "remaining_work_packages": 81.0,
    "comb_reference_check": 40.0,
}


def load() -> dict:
    if LEDGER.exists():
        return json.loads(LEDGER.read_text("utf-8"))
    return {}


def save(ledger: dict) -> None:
    LEDGER.write_text(json.dumps(ledger, indent=1, sort_keys=True) + "\n", "utf-8", newline="\n")


def total_projection(ledger: dict) -> float:
    total = SPENT_BEFORE
    for section, line in LINES.items():
        row = ledger.get(section, {})
        total += max(row.get("spent_hours", 0.0), row.get("projection_hours", line))
    return total


def execute(
    section: str,
    part: str,
    out: Path,
    fn: Callable,
    shards: Sequence[tuple[str, object]],
    fingerprint: str,
    line_hours: float,
    workers: int,
    **kwargs,
) -> str:
    """Run one part of a section; ``line_hours`` is the part's share of the budget line. Returns the
    driver's state, or a sentence starting with ``stopped:``."""
    if section not in LINES:
        raise SystemExit(f"{section}: not a line of the budget")
    ledger = load()
    row = ledger.setdefault(section, {}).setdefault("parts", {}).setdefault(part, {})
    row["line_hours"] = line_hours
    row["shards"] = len(shards)
    cap = STOP_FACTOR * line_hours
    parts = ledger[section]["parts"]

    def guard(spent: float) -> str | None:
        """The shared limit, read before each batch; ``spent`` is this part's."""
        row["spent_hours"] = spent
        ledger[section]["spent_hours"] = sum(p.get("spent_hours", 0.0) for p in parts.values())
        save(ledger)
        if total_projection(ledger) > HARD_MAXIMUM:
            return f"stopped: the total projection passes {HARD_MAXIMUM:.0f} CPU-h"
        return None

    kwargs["guard"] = guard
    probe = list(shards)[::PROBE_EVERY]
    if "projection_hours" not in row:  # the checkpoint is frozen once written
        run = driver.Run(out, fn, probe, fingerprint, cap, workers, **kwargs)
        state = run.execute()
        if state != "complete":
            save(ledger)
            return state
        row["projection_hours"] = run.spent_seconds() / 3600.0 / len(probe) * len(shards)
        row["first_5_percent_shards"] = len(probe)
    projection = row["projection_hours"]
    ledger[section]["projection_hours"] = max(
        LINES[section], sum(p.get("projection_hours", p["line_hours"]) for p in parts.values())
    )
    save(ledger)
    if projection > cap:
        return f"stopped: the projection {projection:.1f} CPU-h passes 1.5 times {line_hours:.1f}"
    if total_projection(ledger) > HARD_MAXIMUM:
        return f"stopped: the total projection passes {HARD_MAXIMUM:.0f} CPU-h"
    run = driver.Run(out, fn, shards, fingerprint, cap, workers, **kwargs)
    state = run.execute()
    row["spent_hours"] = run.spent_seconds() / 3600.0
    ledger[section]["spent_hours"] = sum(p.get("spent_hours", 0.0) for p in parts.values())
    save(ledger)
    return state


def assembled(out: Path, fn, shards, fingerprint: str, workers: int, **kwargs) -> bytes:
    """The bytes of a run that has completed; refused otherwise, by the driver."""
    return driver.Run(out, fn, shards, fingerprint, 1.0, workers, **kwargs).assemble()
