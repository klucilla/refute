"""v0.5.4: a correction of the budgeted driver's projection, for future parts only (#217; the
maintainer's decision of 2026-11-12, 15:46, item 4; a finding for #59). ``method_status:
not_validated``.

**The finding.** In v0.5.2's ``budgeted.execute``, a part's projection is the consumption of its
checkpoint over the checkpoint's share of the work. ``driver.Run.spent_seconds`` includes the crash
charge of a batch left open (every worker for a whole shard and an interval). So an interruption
before the checkpoint completes makes the projection explode, and the projection rule stops the
part: a resume becomes impossible without a new part (I4 on 2026-11-12: about 5.08 CPU-h charged for
about 0.2 used, a projection of about 100 against 12).

**The correction.** The crash charge still counts in the part's consumption and so in the line, the
sub-caps and the hard maximum: the guard, the consumption and the total all use ``spent_seconds``,
unchanged, and a caller's hard cap (``ledger_i.hard_cap``) is computed from them. **The
projection** uses the measured CPU, ``measured_seconds``: the larger of
- every batch's charge without its crash charge (``crash_seconds``: a batch closed by the crash
  rule, or still open, adds ``workers * (max_shard_seconds + 20 s)``; what was tracked before the
  interruption stays), and
- the CPU the finished shards' sidecars record (a floor: a shard finished after the last write of
  an interrupted batch's charge is still counted).

Without an interruption the first term is ``spent_seconds`` and is never below the second (each
batch's committed seconds are its shards' CPU), so the projection is exactly v0.5.2's.

**The part's own rule** (1.5 times the allocation before the checkpoint, 1.5 times the projection
after it) is applied to the measured CPU too. The driver compares it with ``spent_seconds``, so the
crash charges on file are added to it: ``cap = rule + crash``. Otherwise one interruption would stop
the resumed part at once. The caller's hard cap still bounds it, and it counts the crash charges.
The driver's watchdog keeps its 10 % over that cap, crash charges included.

**Not uniformly more conservative** (Codex, h1-driverv3 round 2). Against a measure of only the
committed seconds, keeping what was tracked before an interruption, and the sidecar floor, can only
raise the projection. That makes the stop against 1.5 times the allocation, and the stop against a
caller's hard cap, earlier or the same; but the part's own cap after the checkpoint, 1.5 times the
projection, rises with it, so a stop by the part's own consumption can come later (a checkpoint of
3/60, an interrupted batch with 5 s tracked and 1 s committed, a crash charge of 42 s and two more
shards of 1 s: a projection of 140 s against 60, a cap of 252 s against 132 with the crash charge
of 42 s alone added, or 136 under round 1's measure, which added the 46 s of spent less measured).
This is v0.5.2's own rule applied to a larger measured projection; the caller's hard cap and the
total still bound it, and both count every crash charge. Before the checkpoint, the cap is 1.5
times the allocation plus the crash charges only, never more.

``execute`` is v0.5.2's ``budgeted.execute`` with that one change, plus two checks before it: a
driver stop on file (``stop.json``) is refused before anything is reconciled, in the driver's own
order, and an interrupted batch is closed by the driver's own crash rule (refused while one of its
workers is alive) before any cap is set. It marks the part's row ``"driver": "v3"`` at its first
dispatch, and **refuses any part that ran under the earlier rule** (a row with an identity, a
consumption or attempts and no mark). So it is never applied to reconcile a past stop.
``budgeted.py`` and ``driver.py`` are imported unchanged; nothing in them is edited.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from pathlib import Path

import budgeted
import driver

MARK = "v3"


def crash_seconds(run: driver.Run) -> float:
    """The crash charges on file: every batch closed by the crash rule, or still open."""
    total = 0.0
    if run.charge_dir.exists():
        for path in sorted(run.charge_dir.glob("b*.json")):
            doc = json.loads(path.read_text("utf-8"))
            if doc.get("reconciled_after_a_crash") or not doc["closed"]:
                total += run._crash_charge(doc["workers"])
    return total


def measured_seconds(run: driver.Run) -> float:
    """The CPU the part measured, with no crash charge (the module's docstring)."""
    tracked = run.spent_seconds() - crash_seconds(run)
    shards = sum(side["cpu_seconds"] for side in run._done().values())
    return max(tracked, shards)


def _check_mark(row: dict) -> None:
    ran = "identity" in row or row.get("spent_hours", 0.0) > 0 or row.get("attempts")
    if ran and row.get("driver") != MARK:
        raise SystemExit("this part ran under v0.5.2's projection rule: v3 is never applied to it")


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
    """``budgeted.execute`` with the projection on measured CPU (the module's docstring)."""
    ledger = budgeted.load()
    gates = budgeted._open_gates(ledger, section, part)
    if gates:
        raise SystemExit(f"a failed gate blocks this work: {gates}")
    row = budgeted._row(ledger, section, part)
    _check_mark(row)
    if "unresolved_stop" in row:
        raise SystemExit(f"{section}/{part}: an unresolved stop: {row['unresolved_stop']}")
    identity = budgeted._identity(fingerprint, shards, row["allocation_hours"])
    if row.get("identity") not in (None, identity):
        budgeted._archive(row)
    row["identity"] = identity
    row["driver"] = MARK
    budgeted.save(ledger)

    def guard(spent: float) -> str | None:
        row["spent_hours"] = spent
        budgeted.save(ledger)
        if budgeted.total_projection(ledger) > budgeted.HARD_MAXIMUM:
            return f"stopped: the total projection passes {budgeted.HARD_MAXIMUM:.0f} CPU-h"
        return None

    kwargs["guard"] = guard
    reconciler = driver.Run(out, fn, shards, fingerprint, 1.0, workers, **kwargs)
    # the driver's order: an unresolved driver stop is refused before anything is reconciled
    stopped = reconciler.unresolved_stop()
    if stopped is not None:
        raise SystemExit(f"an unresolved stop ({stopped}): reconcile it first")
    # an interrupted batch is closed by the driver's own crash rule before any cap is set (it
    # refuses while a worker of that batch is alive), so its charge is known
    if reconciler.charge_dir.exists():
        reconciler._reconcile_crashes()
    crash = crash_seconds(reconciler) / 3600.0

    def cap() -> float:
        rule = budgeted.cap_of(row) + crash
        return rule if hard_cap_hours is None else min(rule, hard_cap_hours)

    if "projection_hours" not in row:
        probe = budgeted.checkpoint(shards)
        run = driver.Run(out, fn, probe, fingerprint, cap(), workers, **kwargs)
        state = run.execute()
        row["spent_hours"] = run.spent_seconds() / 3600.0  # every charge counts in the cap
        if state != "complete":
            return budgeted._ended(ledger, row, state)
        share = sum(units(a) for _, a in probe) / sum(units(a) for _, a in shards)
        row["projection_hours"] = measured_seconds(run) / 3600.0 / share  # measured CPU only
        row["projection_basis"] = "measured CPU of the checkpoint (budgeted_v3)"
        row["checkpoint_shards"] = len(probe)
        budgeted.save(ledger)
        allowed = budgeted.STOP_FACTOR * row["allocation_hours"]
        if row["projection_hours"] > allowed:
            return budgeted._stop(
                ledger,
                row,
                f"stopped: the projection {row['projection_hours']:.1f} CPU-h passes "
                f"1.5 times the allocation, {allowed:.1f}",
            )
        if budgeted.total_projection(ledger) > budgeted.HARD_MAXIMUM:
            return budgeted._stop(
                ledger, row, f"stopped: the total passes {budgeted.HARD_MAXIMUM:.0f} CPU-h"
            )
    if hard_cap_hours is not None and row["projection_hours"] > hard_cap_hours:
        return budgeted._stop(
            ledger,
            row,
            f"stopped: the projection {row['projection_hours']:.1f} CPU-h passes the part's hard "
            f"cap, {hard_cap_hours:.1f}",
        )
    run = driver.Run(out, fn, shards, fingerprint, cap(), workers, **kwargs)
    state = run.execute()
    if state != "complete":
        row["spent_hours"] = run.spent_seconds() / 3600.0
        return budgeted._ended(ledger, row, state)
    return budgeted.finish(ledger, section, part, run.spent_seconds() / 3600.0) or state
