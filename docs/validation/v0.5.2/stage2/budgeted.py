"""v0.5.2 stage 2: a section of the budget through the batch driver, under the maintainer's
decision of 2026-11-09 (#216, item 1; ``budget.md``). ``method_status: not_validated``.

- **Every part of a section is declared, with its allocation, before anything is dispatched**,
  so a part not yet reached keeps its reservation in the total.
- **The checkpoint.** A part first runs an evenly spaced 5 % of its shards (the caller shuffles
  its constructions into the shards, so that the sample is representative) and projects its
  whole cost by scheduled units. The projection is frozen, bound to the fingerprint, the schedule
  and the allocation; other code or another schedule is a new attempt, and the earlier attempts'
  consumption stays in the ledger.
- **The stops.** The part stops if its projection passes 1.5 times its allocation, if its
  consumption passes 1.5 times its frozen projection, or if the total over every section (what
  is spent, or the projection of what is not) passes the hard maximum of 3,100 CPU-h: before each
  batch and again after the last one. A stop is written to the ledger and binds across attempts,
  until ``reconcile`` records a reason; assembly is refused meanwhile.
- **A failed gate** (``fail_gate``) blocks every later part of every section, until
  ``resolve_gate`` records the prospective redesign. The failure stays on file. Only the
  maintainer's explicit decision can let one named part run meanwhile (``exempt``, recorded).
"""

from __future__ import annotations

import hashlib
import json
import math
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


def declare(section: str, allocations: dict[str, float]) -> None:
    """Register every part of a section; the allocations may not pass the budget line."""
    if section not in LINES:
        raise SystemExit(f"{section}: not a line of the budget")
    if sum(allocations.values()) > LINES[section] + 1e-9:
        raise SystemExit(f"{section}: the allocations pass the budget line")
    ledger = load()
    parts = ledger.setdefault("sections", {}).setdefault(section, {"parts": {}})["parts"]
    for part, hours in allocations.items():
        row = parts.setdefault(part, {"allocation_hours": hours})
        if row["allocation_hours"] != hours:
            _archive(row)
            row["allocation_hours"] = hours
    save(ledger)


def _archive(row: dict) -> None:
    """Close the current attempt; its consumption stays counted."""
    if "identity" in row or row.get("spent_hours", 0.0) > 0.0:
        row.setdefault("attempts", []).append(
            {
                "identity": row.get("identity"),
                "spent_hours": row.get("spent_hours", 0.0),
                "projection_hours": row.get("projection_hours"),
            }
        )
    for key in ("identity", "spent_hours", "projection_hours", "checkpoint_shards"):
        row.pop(key, None)


def _part_total(row: dict) -> float:
    earlier = sum(a["spent_hours"] for a in row.get("attempts", []))
    expected = row["projection_hours"] if "projection_hours" in row else row["allocation_hours"]
    return earlier + max(row.get("spent_hours", 0.0), expected)


def charge(name: str, hours: float, basis: str) -> None:
    """Consumption that ran outside a section (a probe), charged once by name; it counts in the
    total like anything spent (Codex, end of round 5)."""
    ledger = load()
    charges = ledger.setdefault("charges", [])
    if any(c["name"] == name for c in charges):
        raise SystemExit(f"{name}: already charged")
    charges.append({"name": name, "hours": hours, "basis": basis})
    save(ledger)


def spent(ledger: dict) -> float:
    """Everything consumed so far: before the decision, the charges, and every part's attempts."""
    total = SPENT_BEFORE + sum(c["hours"] for c in ledger.get("charges", []))
    for section in ledger.get("sections", {}).values():
        for row in section["parts"].values():
            total += row.get("spent_hours", 0.0)
            total += sum(a["spent_hours"] for a in row.get("attempts", []))
    return total


def total_projection(ledger: dict) -> float:
    """Spent before, the charges, each section's parts and whatever of its line no part has
    declared."""
    sections = ledger.get("sections", {})
    total = SPENT_BEFORE + sum(c["hours"] for c in ledger.get("charges", []))
    for section, line in LINES.items():
        parts = sections.get(section, {"parts": {}})["parts"]
        allocated = sum(p["allocation_hours"] for p in parts.values())
        total += max(0.0, line - allocated) + sum(_part_total(p) for p in parts.values())
    return total


def cap_of(row: dict) -> float:
    """1.5 times the frozen projection once there is one, before that 1.5 times the allocation."""
    return STOP_FACTOR * row.get("projection_hours", row["allocation_hours"])


def _stop(ledger: dict, row: dict, message: str) -> str:
    row["unresolved_stop"] = message
    save(ledger)
    return message


def finish(ledger: dict, section: str, part: str, spent: float) -> str | None:
    """Final accounting of a part: a total above the maximum is a stop written to the ledger."""
    row = ledger["sections"][section]["parts"][part]
    row["spent_hours"] = spent
    save(ledger)
    if total_projection(ledger) > HARD_MAXIMUM:
        return _stop(ledger, row, f"stopped: the total projection passes {HARD_MAXIMUM:.0f} CPU-h")
    return None


def _open_gates(ledger: dict, section: str | None = None, part: str | None = None) -> list[str]:
    """The failed gates that block this part: all of them, unless the maintainer exempted this
    very part (``exempt``)."""
    failed = [k for k, v in ledger.get("gates", {}).items() if v.get("state") == "failed"]
    exempt_parts = {(e["section"], e["part"], e["gate"]) for e in ledger.get("gate_exemptions", [])}
    return [g for g in failed if (section, part, g) not in exempt_parts]


def exempt(gate: str, section: str, part: str, decision: str) -> None:
    """The maintainer's explicit permission for one part to run while a gate is failed; the
    failure stays on file and keeps blocking every other part."""
    ledger = load()
    if ledger.get("gates", {}).get(gate, {}).get("state") != "failed":
        raise SystemExit(f"{gate}: not a failed gate")
    ledger.setdefault("gate_exemptions", []).append(
        {"gate": gate, "section": section, "part": part, "decision": decision}
    )
    save(ledger)


def fail_gate(name: str, detail: dict) -> None:
    ledger = load()
    ledger.setdefault("gates", {})[name] = {"state": "failed", "detail": detail}
    save(ledger)


def pass_gate(name: str, detail: dict) -> None:
    ledger = load()
    ledger.setdefault("gates", {})[name] = {"state": "passed", "detail": detail}
    save(ledger)


def resolve_gate(name: str, reason: str) -> None:
    """A prospective redesign is recorded; the failed assessment stays on file."""
    ledger = load()
    gate = ledger["gates"][name]
    ledger.setdefault("gate_history", []).append({"gate": name, **gate, "resolved_by": reason})
    del ledger["gates"][name]
    save(ledger)


def reconcile(section: str, part: str, reason: str) -> None:
    ledger = load()
    row = ledger["sections"][section]["parts"][part]
    row.setdefault("reconciled", []).append({"stop": row.pop("unresolved_stop"), "reason": reason})
    save(ledger)


def _row(ledger: dict, section: str, part: str) -> dict:
    try:
        return ledger["sections"][section]["parts"][part]
    except KeyError:
        raise SystemExit(f"{section}/{part}: not declared") from None


def _identity(fingerprint: str, shards: Sequence, allocation: float) -> str:
    text = json.dumps([[s, repr(a)] for s, a in shards]) + f"{fingerprint}:{allocation}"
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def checkpoint(shards: Sequence) -> list:
    """An evenly spaced twentieth of the shards, rounded up."""
    n, k = len(shards), math.ceil(len(shards) / PROBE_EVERY)
    return [shards[i] for i in sorted({round(j * (n - 1) / max(k - 1, 1)) for j in range(k)})]


def execute(
    section: str,
    part: str,
    out: Path,
    fn: Callable,
    shards: Sequence[tuple[str, object]],
    fingerprint: str,
    workers: int,
    units: Callable[[object], int] = lambda arg: 1,
    hard_cap_hours: float | None = None,
    **kwargs,
) -> str:
    """Run one declared part; returns the driver's state, or a sentence starting ``stopped``.
    ``hard_cap_hours``, when given, bounds the part's cap below the 1.5 rule (a cap the
    maintainer fixed for this work, such as the forecast's 20 CPU-h)."""
    ledger = load()
    gates = _open_gates(ledger, section, part)
    if gates:
        raise SystemExit(f"a failed gate blocks this work: {gates}")
    row = _row(ledger, section, part)
    if "unresolved_stop" in row:
        raise SystemExit(f"{section}/{part}: an unresolved stop: {row['unresolved_stop']}")
    identity = _identity(fingerprint, shards, row["allocation_hours"])
    if row.get("identity") not in (None, identity):
        _archive(row)
    row["identity"] = identity
    save(ledger)

    def guard(spent: float) -> str | None:
        row["spent_hours"] = spent
        save(ledger)
        if total_projection(ledger) > HARD_MAXIMUM:
            return f"stopped: the total projection passes {HARD_MAXIMUM:.0f} CPU-h"
        return None

    kwargs["guard"] = guard

    def cap() -> float:
        rule = cap_of(row)
        return rule if hard_cap_hours is None else min(rule, hard_cap_hours)

    if "projection_hours" not in row:
        probe = checkpoint(shards)
        run = driver.Run(out, fn, probe, fingerprint, cap(), workers, **kwargs)
        state = run.execute()
        row["spent_hours"] = run.spent_seconds() / 3600.0
        if state != "complete":
            return _ended(ledger, row, state)
        share = sum(units(a) for _, a in probe) / sum(units(a) for _, a in shards)
        row["projection_hours"] = row["spent_hours"] / share
        row["checkpoint_shards"] = len(probe)
        save(ledger)
        allowed = STOP_FACTOR * row["allocation_hours"]
        if row["projection_hours"] > allowed:
            return _stop(
                ledger,
                row,
                f"stopped: the projection {row['projection_hours']:.1f} CPU-h passes "
                f"1.5 times the allocation, {allowed:.1f}",
            )
        if total_projection(ledger) > HARD_MAXIMUM:
            return _stop(ledger, row, f"stopped: the total passes {HARD_MAXIMUM:.0f} CPU-h")
    if hard_cap_hours is not None and row["projection_hours"] > hard_cap_hours:
        return _stop(
            ledger,
            row,
            f"stopped: the projection {row['projection_hours']:.1f} CPU-h passes the part's hard "
            f"cap, {hard_cap_hours:.1f}",
        )
    run = driver.Run(out, fn, shards, fingerprint, cap(), workers, **kwargs)
    state = run.execute()
    if state != "complete":
        row["spent_hours"] = run.spent_seconds() / 3600.0
        return _ended(ledger, row, state)
    return finish(ledger, section, part, run.spent_seconds() / 3600.0) or state


def _ended(ledger: dict, row: dict, state: str) -> str:
    """A driver run that did not complete: a stop of any kind (cap, accounting, shard limit, the
    guard) binds across attempts in the ledger; a pause stays resumable (Codex, end of round 5)."""
    if state.startswith("paused"):
        save(ledger)
        return state
    return _stop(ledger, row, state)


def assembled(
    section: str, part: str, out: Path, fn, shards, fingerprint: str, workers: int, **kwargs
) -> bytes:
    """The bytes of a completed part; refused under a stop or a failed gate."""
    ledger = load()
    row = _row(ledger, section, part)
    if "unresolved_stop" in row or _open_gates(ledger, section, part):
        raise SystemExit(f"{section}/{part}: refused under a stop or a failed gate")
    return driver.Run(out, fn, shards, fingerprint, 1.0, workers, **kwargs).assemble()
