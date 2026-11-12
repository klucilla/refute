"""v0.5.4, I4's second completion step (#217; the maintainer's decision of 2026-11-12, 18:05,
items 1 and 2). ``method_status: not_validated``. A new record: ``i4_bound.py`` and ``i4_rest.py``
are not edited (I4's fingerprint covers ``i4_bound.py``; ``i4_rest.py`` is reviewed and committed).

``h1_i4_rest`` stopped at its checkpoint (14 of 280 planets): its projection, 7.3 CPU-h, passed the
part's hard cap, 7.1, the first half's room after a 12-worker in-flight reserve. By the decision:

- ``run 2``: that stop is reconciled as a fact (nothing deleted). About 7 CPU-h, 5.6 left in
  ``h1_i4_rest`` and 1.4 of ``h1_reserve``, go to a new part ``h1_i4_rest2`` in one atomic save,
  with the history. Then the rows not yet done (266) run there with ``i4_bound.shard``, the same
  fingerprint and rows, **6 workers**, in their own folder, draining at 2026-11-18 19:30.
- ``run 3``, **the one pre-approved reserve:** only if ``h1_i4_rest2`` stopped by the part's cap or
  the first half's (``CAP_STOPS``). That stop is reconciled as a fact, and the first half's CPU
  sub-cap is raised from 25 to 30 CPU-h, recorded in the ledger (the phase's 50 unchanged). What is
  left of ``h1_i4_rest2`` and ``h1_reserve``, plus 5 CPU-h of ``h2_unallocated`` (the raised
  sub-cap's room), goes to ``h1_i4_rest3`` in one atomic save. The rows still not done then run
  there, again with 6 workers. Its procedure is posted on #217 before it runs.

Any other stop, an error, a rerun that does not reproduce its record, or L ≥ 23 (a draft
infeasibility) comes back to the maintainer. ``summarize`` reads every part's verified shards
(each row exactly once) through ``i4_bound.summarize``'s frozen computation, planet 3129 excluded
from L as decided before any I4 result was read.
"""

from __future__ import annotations

import json
import math
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import i4_rest as r1  # noqa: E402,I001  (it imports i4_bound, stage A's and B's modules, ledger_i)
from i4_rest import budgeted, driver, i4, ledger_i  # noqa: E402

MAIN_PART, REST_PART, REST2, REST3 = r1.MAIN_PART, r1.REST_PART, "h1_i4_rest2", "h1_i4_rest3"
OUTS = {
    MAIN_PART: i4.OUT,
    REST_PART: r1.OUT_REST,
    REST2: ledger_i.ROOT / ".cache/v054/i4-rest2",
    REST3: ledger_i.ROOT / ".cache/v054/i4-rest3",
}
WORKERS = 6  # the maintainer's decision: half the in-flight reserve
REST_STOP = "stopped: the projection 7.3 CPU-h passes the part's hard cap, 7.1"
FROM_REST, FROM_RESERVE = 5.6, 1.4  # about 7 CPU-h for h1_i4_rest2
FROM_H2 = 5.0  # the raised first-half sub-cap's room, for h1_i4_rest3 only
H1_RAISED = 30.0
# the stops of the part's cap or the first half's (``budgeted`` and ``driver``); any other stop,
# such as the phase's total, the CPU accounting or a slow shard, goes to the maintainer
CAP_STOPS = (
    "stopped: the cap is reached",
    "stopped: the cap was passed by the end of the run",
    "over the cap: the workers were ended",
    "stopped: the projection",
)
REASON2 = (
    "The maintainer's decision of 2026-11-12, 18:05, item 1 (#217): h1_i4_rest stopped at its "
    "checkpoint (projection 7.3 CPU-h against the part's hard cap 7.1, the first half's room after "
    "a 12-worker in-flight reserve); the stop is a fact; the 266 remaining planets run as "
    "h1_i4_rest2 with the same code, fingerprint and rows and 6 workers (i4_rest2.py)."
)
REASON3 = (
    "The maintainer's decision of 2026-11-12, 18:05, item 2 (#217), the one pre-approved reserve: "
    "h1_i4_rest2 stopped by the part's or the first half's cap; the stop is a fact; the first "
    "half's CPU sub-cap is raised from 25 to 30 CPU-h (the phase's 50 unchanged); what is left "
    "runs as h1_i4_rest3 with the same code, fingerprint and rows and 6 workers (i4_rest2.py)."
)


def _handle(part: str, rows: list, fp: str) -> driver.Run:
    return driver.Run(OUTS[part] / fp, i4.shard, rows, fp, 1.0, 1, pin=i4.PIN,
                      max_shard_seconds=i4.MAX_SHARD_SECONDS)  # fmt: skip


def _attempts(part: str, fp: str) -> Path:
    return OUTS[part] / fp / "run-attempts.jsonl"


def _attempt(part: str, fp: str, what: str, state: str | None = None) -> None:
    """A durable start and end of each run (as ``i4_rest``): a start without an end is a STOP."""
    path = _attempts(part, fp)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "event": what,
            "pid": os.getpid(), "state": state}  # fmt: skip
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(line, sort_keys=True) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def _open_attempts(part: str, fp: str) -> bool:
    path = _attempts(part, fp)
    if not path.exists():
        return False
    events = [json.loads(x) for x in path.read_text("utf-8").splitlines() if x.strip()]
    return sum(e["event"] == "start" for e in events) > sum(e["event"] == "end" for e in events)


def _open_batch(handle: driver.Run) -> bool:
    return handle.charge_dir.exists() and any(
        not json.loads(f.read_text("utf-8"))["closed"] for f in handle.charge_dir.glob("b*.json")
    )


def _raised() -> bool:
    return any(c.get("reason") == REASON3 for c in budgeted.load().get("sub_cap_changes", []))


def _bind_sub_cap() -> None:
    """The first half's sub-cap as the ledger records it: 30 once the raise is on file."""
    ledger_i.H1_CAP_HOURS = H1_RAISED if _raised() else 25.0


def _done_before(part: str, rws: list, fp: str) -> set:
    """The rows finished by every part before ``part``, each checked by its sidecar."""
    order = [MAIN_PART, REST_PART, REST2, REST3]
    done: set = set()
    for p in order[: order.index(part)]:
        if p in ledger_i._rows():
            done |= set(_handle(p, rws, fp)._done())
    return done


def _transfer_atomic(debits: dict, target: str, extra: dict | None = None) -> None:
    """Debits, the credit, the history (and the sub-cap's raise) in one atomic save."""
    book = budgeted.load()
    parts = book["sections"][ledger_i.SECTION]["parts"]
    total = 0.0
    utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    reason = REASON3 if extra else REASON2
    for src, hours in debits.items():
        if hours <= 0.0:  # a donor with nothing left gives nothing (Codex's round 1)
            continue
        row = parts[src]
        if row["allocation_hours"] - hours < row.get("spent_hours", 0.0) - 1e-9:
            raise SystemExit(f"{src} cannot give back hours it has spent: refused")
        row["allocation_hours"] -= hours
        total += hours
        book.setdefault("transfers", []).append(
            {"utc": utc, "from": src, "to": target, "hours": hours, "reason": reason}
        )
    parts[target] = {"allocation_hours": round(total, 6)}
    if sum(r["allocation_hours"] for r in parts.values()) > budgeted.LINES[ledger_i.SECTION] + 1e-9:
        raise SystemExit("the allocations would pass the line: refused")
    if extra:
        book.setdefault("sub_cap_changes", []).append({"utc": utc, **extra, "reason": reason})
    budgeted.save(book)


def _close(part: str) -> None:
    """A stopped part, once its stop is reconciled, is closed: its projection becomes its
    consumption, so that ``budgeted.total_projection`` (each part counts the larger of its
    consumption and its projection, plus the line's unallocated rest) stops counting work the part
    will never do.
    The frozen projection is kept in the row (``projection_at_stop``) and in the ledger's
    ``allocation_closures``; the identity, the consumption and the allocation do not change, and
    nothing is deleted (Codex's rounds 1 and 2: archiving the attempt, or reducing the allocation,
    would count the consumption twice through the line's unallocated rest)."""
    book = budgeted.load()
    row = book["sections"][ledger_i.SECTION]["parts"][part]
    if "projection_at_stop" in row:
        return  # closed already
    consumed = row.get("spent_hours", 0.0)
    row["projection_at_stop"] = row.get("projection_hours")
    row["projection_hours"] = consumed
    book.setdefault("allocation_closures", []).append(
        {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "part": part,
         "consumed": consumed, "projection_at_stop": row["projection_at_stop"],
         "reason": "a stopped part closed after its reconciliation (i4_rest2.py)"}
    )  # fmt: skip
    budgeted.save(book)


def _partial_l(rws: list, fp: str) -> tuple[int, int]:
    """L so far over the finished fresh planets (3129 excluded), and their invalid count."""
    low = invalid = 0
    for part in (MAIN_PART, REST_PART, REST2, REST3):
        if part not in ledger_i._rows():
            continue
        handle = _handle(part, rws, fp)
        for sid in handle._done():
            for line in handle._paths(sid)[0].read_text("utf-8").splitlines():
                if not line.strip():
                    continue
                rec = json.loads(line)
                if rec.get("set") != "fresh" or rec.get("index") == r1.EXCLUDED:
                    continue
                nb = rec.get("nuisance") or {}
                if rec.get("status") != "OK" or rec.get("mismatch") or nb.get("invalid"):
                    invalid += 1
                elif "power_nuisance" not in rec:
                    invalid += 1
                elif rec["power_nuisance"] < i4.REQUIRED:
                    low += 1
    return low, invalid


def _science_checks(rws: list, fp: str) -> None:
    """Before any reconciliation or transfer (Codex's round 1): no binding stop of I4 (an error, an
    oversized record, a rerun that does not reproduce), and L so far below 23."""
    if i4.STOP_FILE.exists():
        raise SystemExit("I4's binding stop exists: a STOP for the maintainer")
    low, _ = _partial_l(rws, fp)
    if low >= i4.NEEDED_LOSSES:
        raise SystemExit(f"L is already {low} >= 23 (a draft infeasibility): a STOP for the "
                         "maintainer")  # fmt: skip


def _common_checks(rws: list, fp: str, cause_stop: tuple[str, str] | None = None) -> None:
    """Before anything changes: no live worker, no open batch, no run left open, and no driver stop
    file, in any part, except the cause's own cap stop in run 3 when it agrees with the ledger
    (``cause_stop``); the first part's interruption already reconciled."""
    for part in (MAIN_PART, REST_PART, REST2, REST3):
        if part not in ledger_i._rows():
            continue
        handle = _handle(part, rws, fp)
        if handle.workers_still_running():
            raise SystemExit(f"{part}: workers still alive: refused")
        if _open_batch(handle):
            raise SystemExit(f"{part}: an open batch (an interruption): a STOP for the maintainer")
        if part != MAIN_PART and _open_attempts(part, fp):
            raise SystemExit(f"{part}: a run that never ended: a STOP for the maintainer")
        driver_stop = handle.unresolved_stop()
        if driver_stop is not None and not (
            cause_stop and part == cause_stop[0] and driver_stop == cause_stop[1]
        ):
            raise SystemExit(f"{part}: a stop in the driver's folder: refused")
    main = ledger_i._rows()[MAIN_PART]
    if "unresolved_stop" in main or not any(
        x.get("reason") == r1.INTERRUPTION for x in main.get("reconciled", [])
    ):
        raise SystemExit(f"{MAIN_PART}: not in its reconciled state: refused")


def run(stage: int) -> None:
    if stage not in (2, 3):
        raise SystemExit("usage: run 2, or run 3 (the one pre-approved reserve)")
    ledger_i.assert_bound()
    _bind_sub_cap()
    before = ledger_i.v052_ledger_sha256()
    part, cause = (REST2, REST_PART) if stage == 2 else (REST3, REST2)
    try:
        rws, fp = r1._schedule()  # the fingerprint must be 161851db746b905b
        book = ledger_i._rows()
        pending0 = book.get(cause, {}).get("unresolved_stop")
        allowed = (cause, pending0) if stage == 3 and pending0 and pending0.startswith(
            CAP_STOPS) else None  # fmt: skip
        _common_checks(rws, fp, allowed)
        _science_checks(rws, fp)
        if cause not in book:
            raise SystemExit(f"{cause} does not exist: refused")
        if stage == 2 and (REST3 in book or "projection_at_stop" in book.get(REST2, {})):
            raise SystemExit(f"{REST2} is closed or {REST3} exists: run 2 refused, a STOP for "
                             "the maintainer")  # fmt: skip
        row = book[cause]
        reason = REASON2 if stage == 2 else REASON3
        pending = row.get("unresolved_stop")
        reconciled = any(x.get("reason") == reason for x in row.get("reconciled", []))
        if stage == 2 and pending is not None and pending != REST_STOP:
            raise SystemExit(f"{cause}: an unexpected stop: {pending}")
        if stage == 3 and pending is not None and not pending.startswith(CAP_STOPS):
            raise SystemExit(f"{cause}: not a stop of a cap: {pending}: brought to the maintainer")
        if pending is None and not reconciled:
            raise SystemExit(f"{cause} has no stop to follow: refused")
        if pending is not None and reconciled:
            raise SystemExit(f"{cause}: a new stop after its reconciliation: refused")
        done = _done_before(part, rws, fp)
        rest = [(sid, a) for sid, a in rws if sid not in done]
        if not rest:
            raise SystemExit("no row is left: refused")
        if part in book:
            # a closed part is never a target again (the tie-break of Codex's round 3: after any
            # failure in the transition to run 3, STOP for the maintainer, never resume by run 2)
            if "projection_at_stop" in book[part]:
                raise SystemExit(f"{part} is closed: a STOP for the maintainer")
            ledger_i.refuse_new_identity(part, fp, rest)
        reserve = len(rest) * i4.MAX_RECORD_BYTES + i4.RUN_OVERHEAD_BYTES
        ledger_i.check_caps(f"i4 rest{stage} run", reserve_days=0.3, reserve_tokens=0,
                            reserve_bytes=reserve)  # fmt: skip
        # every check passed: the cause's stop as a fact (in the ledger and, where the driver wrote
        # one, in its folder), the cause closed, then the atomic allocation
        if pending is not None:
            budgeted.reconcile(ledger_i.SECTION, cause, reason)
        cause_handle = _handle(cause, rws, fp)
        if cause_handle.unresolved_stop() is not None:
            cause_handle.reconcile(reason)
        _close(cause)
        if part not in ledger_i._rows():
            with ledger_i.Exclusive("transfer"):
                if stage == 2:
                    _transfer_atomic({REST_PART: FROM_REST, "h1_reserve": FROM_RESERVE}, REST2)
                else:
                    book = ledger_i._rows()
                    left2 = book[REST2]["allocation_hours"] - ledger_i.part_consumption(REST2)
                    reserve_left = book["h1_reserve"]["allocation_hours"]
                    _transfer_atomic(
                        {REST2: math.floor(max(left2, 0.0) * 1e6) / 1e6,  # rounded down
                         "h1_reserve": reserve_left,
                         "h2_unallocated": FROM_H2},
                        REST3, extra={"sub_cap": "h1", "from": 25.0, "to": H1_RAISED},
                    )  # fmt: skip
        _bind_sub_cap()
        ledger_i.declare()
        ledger_i.refuse_new_identity(part, fp, rest)
        cap = ledger_i.hard_cap(part, WORKERS, i4.MAX_SHARD_SECONDS)
        print(f"{part}: {len(rest)} rows; hard cap {cap:.3f} CPU-h; {WORKERS} workers; "
              f"first-half sub-cap {ledger_i.H1_CAP_HOURS}; fingerprint {fp}",
              flush=True)  # fmt: skip
        _attempt(part, fp, "start")
        state = budgeted.execute(
            ledger_i.SECTION, part, OUTS[part] / fp, i4.shard, rest, fp, WORKERS,
            pin=i4.PIN, max_shard_seconds=i4.MAX_SHARD_SECONDS, hard_cap_hours=cap,
            pause_at=r1.PAUSE_AT,
        )  # fmt: skip
        _attempt(part, fp, "end", state)
        print(state, flush=True)
        ledger_i.check_caps(f"i4 rest{stage} after the run", 0.0, 0)
    finally:
        if ledger_i.v052_ledger_sha256() != before:
            raise SystemExit("the v0.5.2 ledger changed: refused")
    if state != "complete":
        if stage == 2 and state.startswith(CAP_STOPS):
            raise SystemExit(f"STOP: {state}; the pre-approved reserve (run 3) applies, after its "
                             "review and its procedure on #217")  # fmt: skip
        raise SystemExit(f"STOP for the maintainer: {state}")


def _records(rws: list, fp: str) -> tuple[list, str | None, dict]:
    found: dict = {}
    origin: dict = {}
    refusal = None
    book = ledger_i._rows()
    ledger = budgeted.load()
    used = [p for p in (MAIN_PART, REST_PART, REST2, REST3) if p in book]
    for part in used:
        handle = _handle(part, rws, fp)
        if "unresolved_stop" in book[part] or handle.unresolved_stop():
            refusal = f"{part}: an unresolved stop"
        if budgeted._open_gates(ledger, ledger_i.SECTION, part):
            refusal = f"{part}: a failed gate"
        if part != MAIN_PART and _open_attempts(part, fp):
            refusal = f"{part}: a run that never ended"
        for sid in handle._done():
            if sid in found:
                raise SystemExit(f"{sid}: done in two parts: refused")
            found[sid] = handle._paths(sid)[0].read_bytes()
            origin[sid] = part
    missing = [sid for sid, _ in rws if sid not in found]
    if missing and refusal is None:
        refusal = f"{len(missing)} rows are missing"
    recs = [json.loads(x) for sid, _ in rws if sid in found
            for x in found[sid].decode().splitlines() if x.strip()]  # fmt: skip
    args = {(a["set"], a["index"]) for _, a in rws}
    keys = [(r["set"], r["index"]) for r in recs]
    if len(set(keys)) != len(keys) or not set(keys) <= args:
        raise SystemExit("records with duplicated or unknown keys: refused")
    if refusal is None and len(recs) != 290:
        refusal = f"{len(recs)} records, not 290"
    per_part = {p: sum(o == p for o in origin.values()) for p in used}
    return recs, refusal, per_part


def summarize() -> None:
    ledger_i.assert_bound()
    rws, fp = r1._schedule()
    recs, refusal, per_part = _records(rws, fp)
    excluded = [r for r in recs if r["set"] == "fresh" and r["index"] == r1.EXCLUDED]
    kept = [r for r in recs if not (r["set"] == "fresh" and r["index"] == r1.EXCLUDED)]
    i4._read = lambda rows, fp_: (kept, refusal)  # i4_bound.summarize's computation, these records
    try:
        i4.summarize()
    except SystemExit as exc:
        stop = str(exc)
    else:
        stop = None
    doc = json.loads(i4.OUT_FILE.read_text("utf-8"))
    used = list(per_part)
    charged = ledger_i.part_consumption(MAIN_PART)
    doc["completion"] = {
        "decisions": "the maintainer's decisions of 2026-11-12, 15:46 and 18:05 (#217)",
        "records_per_part": per_part,
        "cpu_hours": {p: round(ledger_i.part_consumption(p), 4) for p in used},
        "crash_charge_hours": round(charged, 4),
        "crash_charge_note": f"{MAIN_PART}'s consumption is the driver's crash charge of the "
        "interrupted batch; its measured CPU (its 10 shards' sidecars) is reported apart",
        "measured_cpu_hours_of_the_interrupted_part": round(sum(
            json.loads(p.read_text("utf-8"))["cpu_seconds"]
            for p in (OUTS[MAIN_PART] / fp / "sidecars").glob("*.json")) / 3600.0, 4),
        "first_half_sub_cap": H1_RAISED if _raised() else 25.0,
        "excluded_from_L": {
            "index": r1.EXCLUDED,
            "why": "unresolved in I1: a raw and enforced odd_even FAIL, not a sensitivity case; "
            "excluded from L and from I2's population by the maintainer's decision of 15:46 "
            "(item 2), taken before any I4 result was read",
            "record": excluded,
        },
        "L_threshold_note": "L is counted over the 177 eligible fresh planets other than 3129; "
        "the threshold stays 23 (at most 155 kept against 156 needed)",
    }  # fmt: skip
    i4.OUT_FILE.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", "utf-8",
                           newline="\n")  # fmt: skip
    if stop:
        raise SystemExit(stop)


if __name__ == "__main__":
    ledger_i.assert_bound()
    with ledger_i.Exclusive(f"i4_rest2 {' '.join(sys.argv[1:])}"):
        if sys.argv[1] == "run":
            run(int(sys.argv[2]))
        elif sys.argv[1] == "summarize":
            summarize()
        else:
            raise SystemExit("usage: run 2|3, or summarize")
