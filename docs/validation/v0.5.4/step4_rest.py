"""v0.5.4 step 4's completion part, after the driver stopped ``h2_step4`` by its mechanics (#217;
the maintainer's decision of 2026-11-12, night, item 7c: one pre-approved completion part per
step, with the same code and rows, reviewed by Codex as a diff, its procedure on #217 first).
``method_status: not_validated``.

**The stop, as a fact.** ``h2_step4``'s checkpoint (4 of 77 shards) projected 0.795 CPU-h. Its
own rule (1.5 times the projection, plus no crash charge) set the cap at 1.193 CPU-h, and the run
stopped there: 62 of 77 shards done, 1.308 CPU-h spent ("stopped: the cap is reached").

``run``:
1. **Checks.** The stop must be exactly that one in the ledger. The driver writes no
   ``stop.json`` for it (its loop's own break); one, if present, must be the same. No
   worker of the part may be alive, and no batch may be open. The fingerprint must be step 4's.
2. **The stop as a fact.** It is reconciled with this decision's reason. The part is closed: its
   projection becomes its consumption, and the frozen projection is kept as
   ``projection_at_stop`` and in ``allocation_closures``. Nothing is deleted.
3. **The allocation.** What ``h2_step4`` has left, rounded down, moves to ``h2_step4_rest``.
4. **The run.** The rows not done run through ``budgeted_v3`` with step 4's own ``shard``,
   fingerprint and rows.

``summarize`` runs step 4's own summary, unchanged, on all 77 shards. The shards come from both
parts, each row exactly once, every sidecar verified. Its consumption is both parts'.

A further stop of this part is a STOP for the maintainer: only one completion is pre-approved.

Usage (from the project root): ``run`` through ``launch_detached.py``, then ``summarize``.
"""

from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import step4_b0_errors as s4  # noqa: E402,I001  (i4_bound's imports, ledger_i last)
import budgeted  # noqa: E402
import budgeted_v3  # noqa: E402
import driver  # noqa: E402
import ledger_i  # noqa: E402

MAIN = s4.PART
REST = "h2_step4_rest"
OUT_REST = s4.ROOT / ".cache/v054/step4-rest"
EXPECTED_STOP = "stopped: the cap is reached"
EXPECTED_FP = "4e080d7b0c162001"  # h2_step4's run (its state.json)
REASON = ("the maintainer's decision of 2026-11-12 (night), item 7c (#217): h2_step4 stopped by "
          "the driver's mechanics (its checkpoint's projection, 0.795 CPU-h, set the part's cap at "
          "1.193; 62 of 77 shards done); the stop is a fact, the part is closed, and the rows not "
          "done run as h2_step4_rest with the same code and rows")  # fmt: skip


def _handle(part_out: Path, rows: list, fp: str) -> driver.Run:
    return driver.Run(part_out / fp, s4.shard, rows, fp, 1.0, 1, pin=s4.PIN,
                      max_shard_seconds=s4.MAX_SHARD_SECONDS)  # fmt: skip


def _schedule() -> tuple[list, str]:
    rows = s4.schedule(s4.b0_records())
    return rows, s4.fingerprint(rows)


def _close(part: str) -> None:
    """i4_rest2's closure: the projection becomes the consumption; nothing is deleted."""
    book = budgeted.load()
    row = book["sections"][ledger_i.SECTION]["parts"][part]
    if "projection_at_stop" in row:
        return
    consumed = row.get("spent_hours", 0.0)
    row["projection_at_stop"] = row.get("projection_hours")
    row["projection_hours"] = consumed
    book.setdefault("allocation_closures", []).append(
        {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "part": part,
         "consumed": consumed, "projection_at_stop": row["projection_at_stop"],
         "reason": "a stopped part closed after its reconciliation (step4_rest.py)"}
    )  # fmt: skip
    budgeted.save(book)


def _transfer_atomic(hours: float) -> None:
    """i4_rest2's atomic transfer (the debit, the credit and the history in one save), never
    through ``declare``, which would archive the closed part (Codex, h2-step4rest round 1)."""
    book = budgeted.load()
    parts = book["sections"][ledger_i.SECTION]["parts"]
    row = parts[MAIN]
    if row["allocation_hours"] - hours < row.get("spent_hours", 0.0) - 1e-9:
        raise SystemExit(f"{MAIN} cannot give back hours it has spent: refused")
    row["allocation_hours"] -= hours
    parts[REST] = {"allocation_hours": round(hours, 6)}
    if sum(r["allocation_hours"] for r in parts.values()) > budgeted.LINES[ledger_i.SECTION] + 1e-9:
        raise SystemExit("the allocations would pass the line: refused")
    book.setdefault("transfers", []).append(
        {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "from": MAIN, "to": REST,
         "hours": hours, "reason": REASON}
    )  # fmt: skip
    budgeted.save(book)


def _check_fp(rows: list, fp: str) -> None:
    state = json.loads((s4.OUT / fp / "state.json").read_text("utf-8")) if (
        s4.OUT / fp / "state.json").exists() else {}  # fmt: skip
    if fp != EXPECTED_FP or state.get("fingerprint") != fp or state.get("shards") != len(rows):
        raise SystemExit(f"the fingerprint {fp} is not h2_step4's run: refused")


def run() -> None:
    ledger_i.assert_bound()
    rows, fp = _schedule()
    _check_fp(rows, fp)
    main = _handle(s4.OUT, rows, fp)
    book = ledger_i._rows()
    if REST in book:
        raise SystemExit(f"{REST} exists already: a STOP for the maintainer")
    pending = book[MAIN].get("unresolved_stop")
    # the driver writes no stop.json for this stop (its loop's own break); the ledger holds it
    if pending != EXPECTED_STOP or main.unresolved_stop() not in (None, EXPECTED_STOP):
        raise SystemExit(f"{MAIN}: not the expected stop ({pending}): a STOP for the maintainer")
    if main.workers_still_running():
        raise SystemExit(f"{MAIN}: workers are still alive: refused")
    for path in sorted(main.charge_dir.glob("b*.json")):
        if not json.loads(path.read_text("utf-8"))["closed"]:
            raise SystemExit(f"{MAIN}: an open batch ({path.name}): refused")
    done = set(main._done())
    rest = [(sid, a) for sid, a in rows if sid not in done]
    if not rest:
        raise SystemExit("no row is left: refused")
    ledger_i.check_caps("step4 rest run", reserve_days=0.2, reserve_tokens=s4.RESERVE_TOKENS,
                        in_h1=False, reserve_bytes=len(rest) * 20_000 + 50_000_000)  # fmt: skip
    with ledger_i.Exclusive("step4 rest transition"):
        budgeted.reconcile(ledger_i.SECTION, MAIN, REASON)
        if main.unresolved_stop() is not None:
            main.reconcile(REASON)
        _close(MAIN)
        row = ledger_i._rows()[MAIN]
        left = row["allocation_hours"] - ledger_i.part_consumption(MAIN)
        hours = math.floor(max(left, 0.0) * 1e6) / 1e6  # rounded down
        _transfer_atomic(hours)
    ledger_i.refuse_new_identity(REST, fp, rest)
    cap = ledger_i.hard_cap(REST, s4.WORKERS, s4.MAX_SHARD_SECONDS)
    print(f"{REST}: {len(rest)} shards; hard cap {cap:.3f} CPU-h; fp {fp}", flush=True)
    with ledger_i.Exclusive("step4 rest run"):
        state = budgeted_v3.execute(
            ledger_i.SECTION, REST, OUT_REST / fp, s4.shard, rest, fp, s4.WORKERS, pin=s4.PIN,
            max_shard_seconds=s4.MAX_SHARD_SECONDS, hard_cap_hours=cap, pause_at=s4.r1.PAUSE_AT,
            units=lambda arg: len(arg["items"]),
        )  # fmt: skip
    print(state, flush=True)
    ledger_i.check_caps("step4 rest after the run", 0.0, 0, in_h1=False)
    if state != "complete":
        raise SystemExit(f"STOP for the maintainer (no further completion): {state}")


def summarize() -> None:
    """Step 4's own summary, unchanged, on the 77 shards of both parts."""
    ledger_i.assert_bound()
    rows, fp = _schedule()
    _check_fp(rows, fp)
    book = ledger_i._rows()
    ledger = budgeted.load()
    for part, out in ((MAIN, s4.OUT), (REST, OUT_REST)):
        if part not in book or "unresolved_stop" in book[part]:
            raise SystemExit(f"{part}: missing or an unresolved stop: refused")
        if _handle(out, rows, fp).unresolved_stop() is not None:
            raise SystemExit(f"{part}: a driver stop: refused")
        if budgeted._open_gates(ledger, ledger_i.SECTION, part):
            raise SystemExit(f"{part}: a failed gate: refused")
    found: dict = {}
    for out in (s4.OUT, OUT_REST):
        handle = _handle(out, rows, fp)
        for sid in handle._done():
            if sid in found:
                raise SystemExit(f"{sid}: done in two parts: refused")
            found[sid] = handle._paths(sid)[0].read_bytes()
    missing = [sid for sid, _ in rows if sid not in found]
    if missing:
        raise SystemExit(f"{len(missing)} shards are not done: refused")
    data = b"".join(found[sid] for sid, _ in rows)

    original = s4.budgeted.assembled

    def assembled(section, part, out, fn, rws, fpx, workers, **kwargs):
        if part == MAIN and section == ledger_i.SECTION:
            if (fpx, rws) != (fp, rows):
                raise SystemExit("an unexpected read of step 4: refused")
            return data
        return original(section, part, out, fn, rws, fpx, workers, **kwargs)  # B0's reader

    consumption = ledger_i.part_consumption

    def both(part):
        return consumption(MAIN) + consumption(REST) if part == MAIN else consumption(part)

    saved = (s4.budgeted.assembled, s4.ledger_i.part_consumption)
    s4.budgeted.assembled, s4.ledger_i.part_consumption = assembled, both
    try:
        s4.summarize()
    finally:
        s4.budgeted.assembled, s4.ledger_i.part_consumption = saved


if __name__ == "__main__":
    if budgeted.LEDGER != ledger_i.HERE / "ledger.json":
        raise SystemExit("budgeted is not pointed at v0.5.4's ledger: refused")
    {"run": run, "summarize": summarize}[sys.argv[1]]()
