"""v0.5.5, R1, D2-F set A: a **fixed-cap adapter** for ``d2f_floor.py`` (#218; the maintainer's
decisions of 2026-11-21 at G1, item 2). ``method_status: not_validated``.

**Status: not released.** Codex reviews it (conversation ``d2fa``, up to three rounds) before any
dispatch; without a release after three rounds D2-F does not run, recorded.

**What the decision authorizes:** 2.1 CPU-h from the reserve, besides the 14.2 CPU-h transferred
from D1-P's set B (refused by set A's futility rule, ``d1p-A.json``), for D2-F's set A with 4
workers: 16.3 CPU-h of allocation against the 16.228111 Codex computed (``d2f-not-run.md``). No
``budgeted_v3``: no checkpoint and no projection rule. The revised design
(``docs/plans/v0.5.5-r1-designs-revision-1.md``, section 2) stays as it is, with its futility
rule. **Set B is not run by this adapter:** if set A is not futile, set B needs money beyond what
is authorized, and the adapter STOPs with that request.

**The protections of the T2a-E runner** (``r1_fixed_cap.py``, Codex's g1 rounds 1 to 3), here for
D2-F. The code is repeated, not imported: D2-F's frozen-list guard (``rc.require_frozen``) refuses
a process that loaded a project module outside D2-F's list, so this adapter is run as
``__main__`` (which the guard skips, as its docstring says), imports only ``d2f_floor`` and its
frozen closure, and is never imported by a check.
- **The protected cap:** ``(allocation - crash reserve - poll margin) / 1.10``, where the crash
  reserve is what one more batch left open by a crash is charged, ``workers x (shard limit +
  20 s)``; "the factor 1.10 defines the watchdog's threshold, not an exact physical limit"; the
  dispatch is refused when the reserve does not fit.
- **The effective cap:** the smaller of the protected cap, the line's cumulative cap
  (``lv.hard_cap``) and, on a resume, the cap recorded before (never raised); checked under the
  ledger's lock **before the start is recorded** against 1.3 times the projection, with the
  projection, its basis and the effective cap written to the ledger first; the driver gets that
  same cap (``expected_cap``), or the run is a STOP.
- **The operational identity:** this adapter's SHA-256, D2-F's fingerprint, the part, the
  allocation, the rows, the workers and the shard limit, frozen in the ledger before the first
  dispatch and checked on the resume and at the summary. The scientific modules and their
  frozen files are unchanged (``d2f_floor.py``'s fingerprint is its own).
- **An accounted completion:** a completion marker after ``budgeted.finish`` ends without a stop;
  the summary needs it, the identities, the driver's own completion, every charge closed and the
  ledger equal to the driver.
- **The closing receipt:** the summary's attempt is recorded under the lock with D2-F's summary
  charges already on file; afterwards a receipt binds the attempt, its one new charge, the
  record's SHA-256 and the operational identity. Counting charges by a prefix proves nothing; a
  missing or uncertain binding is a STOP; no historical charge is removed.
- **The wrapper's charge** in ``finally``, under the lock, on every path, deducting only the
  attempt's new inner charge.
- **The operational closing** (Codex, d2fa round 1; the runner's final record has the same
  place): ``d2f-A-closing.json``, written once and only after the wrapper's charge succeeded,
  binds the record's SHA-256, the attempt, the identity, the receipt and the wrapper's charge,
  with the summary's state (``final``, or ``stopped`` when ``d2f_floor`` ended in a STOP after
  writing its record). The operational acceptance (``check_closed``, the ``accept`` command)
  requires it with the state ``final``; its absence or inconsistency is a STOP.

**The projection** for the margin: 10.4 CPU-h, the designs' price (about 0.052 CPU-h per planet,
200 planets; "the pilot timed one D2-F planet but its line was cut from the output"), an
estimate without an auditable measurement. With 4 workers and the 1,200-second shard limit the
protected cap of 16.3 CPU-h is about 13.585 CPU-h, at least 1.3 x 10.4 = 13.52.

Usage (from the project root, through ``launch_detached.py``):
``.venv/Scripts/python.exe -B docs/validation/v0.5.5/d2f_fixed_cap.py run`` then ``summarize``;
``check`` is read only (the fingerprint through the frozen-list guard, the caps, the ledger);
``accept`` is read only (the operational acceptance of set A's record).
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import d2f_floor as d2f  # noqa: E402,I001  (its imports end binding budgeted to v0.5.5's ledger)
from d2f_floor import budgeted, lv, rc  # noqa: E402
import driver  # noqa: E402  (v0.5.2's, in D2-F's frozen list)

lv.bind()  # again, after every import (an earlier stage's module rebinds budgeted on import)

MARK = "fixed-cap"
SET = "A"
PART = d2f.part(SET)  # r1_d2f_a
SOURCE = "r1_d1p_b"  # D1-P's set B, refused by set A's futility rule
TRANSFER = 14.2  # the maintainer's decision of 2026-11-20 (21:00), item 2
FROM_RESERVE = 2.1  # the maintainer's decisions of 2026-11-21, item 2
ALLOCATION = round(TRANSFER + FROM_RESERVE, 6)  # 16.3
WORKERS = 4  # the decisions of 2026-11-21: at most 4 workers in D2-F
SHARD_LIMIT = rc.MAX_SHARD_SECONDS  # 1,200 s, the design's
CAP_MARGIN = 1.3  # the night decision: a part's cap at least 1.3 times its projection
POLL_SECONDS = 0.5  # the watchdog's interval (driver.py), per worker, as a margin
PROJECTION = {
    "basis": "the designs' price: about 0.052 CPU-h per planet times 200 planets "
    "(docs/plans/v0.5.5-r1-designs-revision-1.md, section 2); an estimate without an auditable "
    "measurement",
    "projection_hours": 10.4,
}
RECORD = HERE / f"d2f-{SET}.json"  # written by d2f_floor's own summary
CLOSING = HERE / f"d2f-{SET}-closing.json"  # the operational closing, after every charge
D1P_A = HERE / "d1p-A.json"
SUMMARY_CHARGE_PREFIX = f"d2f_summarize_{SET}_"  # d2f_floor.summarize's charge
WRAPPER_CHARGE_PREFIX = f"d2f_fixed_summary_{SET}_"  # this wrapper's own charge
ATTEMPTS = "summary_attempts"
RECEIPTS = "closing_receipts"
DECISION = "the maintainer's decisions of 2026-11-21 at G1, item 2 (#218)"


def own_sha256() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


# --- the caps ---------------------------------------------------------------------------------


def crash_reserve(workers: int, shard_limit: float) -> float:
    """CPU-h one more batch left open by a crash would be charged (``driver.Run._crash_charge``)."""
    return workers * (shard_limit + driver.CHARGE_SECONDS) / 3600.0


def protected_cap(allocation: float, workers: int, shard_limit: float) -> float:
    """The cap given to the driver, so that its watchdog threshold (1.10 times it), one more
    crash charge and the poll margin stay within the allocation. Refused (a STOP) if they do
    not fit."""
    room = allocation - crash_reserve(workers, shard_limit) - workers * POLL_SECONDS / 3600.0
    cap = room / driver.OVER_CAP_FACTOR
    if cap <= 0:
        raise SystemExit(
            f"the crash reserve for {workers} workers does not fit the allocation {allocation}: "
            "the dispatch is refused"
        )
    return cap


def effective_cap(row: dict, workers: int, shard_limit: float, line_cap: float | None) -> float:
    """The cap given to the driver, after every restriction: the allocation's protected cap, the
    line's cumulative cap and, on a resume, the cap recorded before (never raised)."""
    cap = protected_cap(row["allocation_hours"], workers, shard_limit)
    if line_cap is not None:
        cap = min(cap, line_cap)
    if "cap_hours" in row:  # a resume never raises the cap recorded before
        cap = min(cap, row["cap_hours"])
    if cap <= 0:
        raise SystemExit("no room under the caps: a STOP")
    return cap


def operational_identity(part, fingerprint, rows, allocation, workers, shard_limit) -> dict:
    rows_text = json.dumps(rows, sort_keys=True)
    return {
        "adapter_sha256": own_sha256(),
        "fingerprint": fingerprint,
        "part": part,
        "allocation_hours": allocation,
        "rows_sha256": hashlib.sha256(rows_text.encode()).hexdigest(),
        "workers": workers,
        "shard_limit_seconds": shard_limit,
    }


def check_margin(part: str, cap: float, projection: dict) -> None:
    """Under the caller's lock and before the start is recorded: the effective cap at least 1.3
    times the projection; the projection, its basis and the effective cap written first."""
    need = CAP_MARGIN * projection["projection_hours"]
    book = budgeted.load()
    row = budgeted._row(book, lv.SECTION, part)
    row.setdefault("margin_checks", []).append(
        {
            "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "basis": projection["basis"],
            "projection_hours": projection["projection_hours"],
            "effective_cap_hours": cap,
            "margin_needed_hours": need,
            "fits": cap >= need,
        }
    )
    budgeted.save(book)
    if cap < need:
        raise SystemExit(
            f"{part}: the effective cap {cap:.6f} is below {CAP_MARGIN} times the projection "
            f"({need:.6f}): a STOP"
        )


# --- the funding --------------------------------------------------------------------------------


def _never_ran(book: dict, part: str) -> bool:
    row = budgeted._row(book, lv.SECTION, part)
    return (
        "identity" not in row
        and row.get("spent_hours", 0.0) == 0.0
        and not row.get("attempts")
        and not lv._starts(book, part)
    )


def fund() -> None:
    """Under the ledger's lock: D1-P set B's 14.2 CPU-h and 2.1 from the reserve to D2-F's set A,
    once. Refused unless D1-P's set A record holds its futility rule (set B refused), neither
    part ever ran, and the allocations with the charges' room stay inside the 64 CPU-h line. A
    repeated call with the transfer already made changes nothing. **One atomic write** holds the
    new allocations and the transfer's record (Codex, d2fa round 1): neither part ever ran, so
    no attempt is archived. **After the funding, ``lv.declare()``, its command line and the
    earlier scripts that call it (``i4_diagnosis.py``, ``pilot_costs.py``, ``t2ae_geometry.py``)
    are not run**: they would restore the earlier table; a ledger found otherwise is reconciled
    by the maintainer, never restored automatically."""
    lv.assert_bound()
    with lv.Exclusive("d2f funding"):
        book = budgeted.load()
        rows = book.get("sections", {}).get(lv.SECTION, {}).get("parts", {})
        if PART not in rows or SOURCE not in rows or "r1_reserve" not in rows:
            raise SystemExit("v0.5.5's parts are not declared: refused")
        done = [t for t in book.get("transfers", []) if t.get("to") == PART]
        if done:
            if rows[PART]["allocation_hours"] != ALLOCATION or rows[SOURCE]["allocation_hours"]:
                raise SystemExit("the transfer on file does not match the ledger: a STOP")
            return
        if json.loads(D1P_A.read_text("utf-8")).get("futile_after_A") is not True:
            raise SystemExit("D1-P's set A does not hold its futility rule: no transfer")
        for part in (SOURCE, PART):
            if not _never_ran(book, part):
                raise SystemExit(f"{part} ran or started: the transfer is refused")
        if rows[SOURCE]["allocation_hours"] != TRANSFER or rows[PART]["allocation_hours"] != 0.0:
            raise SystemExit("the allocations are not the declared ones: refused")
        merged = {p: r["allocation_hours"] for p, r in rows.items()}
        merged[SOURCE] = 0.0
        merged[PART] = ALLOCATION
        merged["r1_reserve"] = round(merged["r1_reserve"] - FROM_RESERVE, 6)
        if merged["r1_reserve"] < 0:
            raise SystemExit("the reserve cannot fund the part: the maintainer's")
        if sum(merged.values()) + max(lv._charges(), lv.CHARGES_ROOM) > lv.LINE_HOURS + 1e-9:
            raise SystemExit("the allocations and the charges' room pass the 64 CPU-h line")
        if sum(merged.values()) > budgeted.LINES[lv.SECTION] + 1e-9:  # budgeted.declare's check
            raise SystemExit(f"{lv.SECTION}: the allocations pass the budget line")
        for part in (SOURCE, PART, "r1_reserve"):  # none ran: nothing to archive
            rows[part]["allocation_hours"] = merged[part]
        book.setdefault("transfers", []).append(
            {
                "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "to": PART,
                "from": {SOURCE: TRANSFER, "r1_reserve": FROM_RESERVE},
                "allocation_hours": ALLOCATION,
                "decision": DECISION,
                "adapter_sha256": own_sha256(),
            }
        )
        budgeted.save(book)


# --- the driver with the fixed cap --------------------------------------------------------------


def execute_fixed(
    section, part, out, fn, shards, fingerprint, workers, shard_limit, line_cap=None,
    expected_cap=None, **kwargs,
) -> str:  # fmt: skip
    """v0.5.2's driver with the effective cap for the whole part: no checkpoint and no
    projection. Every charge, crash charges included, counts in the part, the line and the
    total. A cap different from the one checked before the start is a STOP."""
    ledger = budgeted.load()
    gates = budgeted._open_gates(ledger, section, part)
    if gates:
        raise SystemExit(f"a failed gate blocks this work: {gates}")
    row = budgeted._row(ledger, section, part)
    if "unresolved_stop" in row:
        raise SystemExit(f"{section}/{part}: an unresolved stop: {row['unresolved_stop']}")
    if row.get("completed_fixed"):
        raise SystemExit(f"{section}/{part}: already completed")
    ran = "identity" in row or row.get("spent_hours", 0.0) > 0 or row.get("attempts")
    if ran and row.get("driver") != MARK:
        raise SystemExit(f"{section}/{part}: it ran under another driver: refused")
    if row.get("attempts"):
        raise SystemExit(f"{section}/{part}: archived attempts: the maintainer's")
    identity = budgeted._identity(fingerprint, shards, row["allocation_hours"])
    if row.get("identity") not in (None, identity):
        raise SystemExit(f"{section}/{part}: another identity: a rerun is the maintainer's")
    op = operational_identity(
        part, fingerprint, shards, row["allocation_hours"], workers, shard_limit
    )
    if row.get("operational_identity") not in (None, op):
        raise SystemExit(f"{section}/{part}: the adapter or its settings changed: refused")
    cap = effective_cap(row, workers, shard_limit, line_cap)
    if expected_cap is not None and abs(cap - expected_cap) > 1e-12:
        raise SystemExit(
            f"{section}/{part}: the effective cap {cap} differs from the one checked before the "
            f"start ({expected_cap}): a STOP"
        )
    row.update(identity=identity, driver=MARK, operational_identity=op, cap_hours=cap)
    row["cap_basis"] = (
        "fixed by the allocation, protected for one crash charge, the poll margin and the "
        "watchdog's 1.10; no checkpoint or projection rule (" + DECISION + ")"
    )
    budgeted.save(ledger)

    def guard(spent: float) -> str | None:
        row["spent_hours"] = spent
        budgeted.save(ledger)
        if budgeted.total_projection(ledger) > budgeted.HARD_MAXIMUM:
            return f"stopped: the total projection passes {budgeted.HARD_MAXIMUM:.0f} CPU-h"
        return None

    kwargs["guard"] = guard
    run = driver.Run(
        out, fn, shards, fingerprint, cap, workers, max_shard_seconds=shard_limit, **kwargs
    )
    stopped = run.unresolved_stop()
    if stopped is not None:
        raise SystemExit(f"an unresolved stop ({stopped}): reconcile it first")
    state = run.execute()
    if state != "complete":
        row["spent_hours"] = run.spent_seconds() / 3600.0
        return budgeted._ended(ledger, row, state)
    ended = budgeted.finish(ledger, section, part, run.spent_seconds() / 3600.0)
    if ended:
        return ended
    row["completed_fixed"] = {
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "spent_hours": row["spent_hours"],
    }
    budgeted.save(ledger)
    return state


def check_completed(section, part, run, fingerprint, shards) -> dict:
    """The part ended complete under this adapter: the completion marker, the identities, the
    driver's own completion, every charge closed, the ledger's consumption equal to the
    driver's, and no failed gate. Returns the row."""
    ledger = budgeted.load()
    row = budgeted._row(ledger, section, part)
    if budgeted._open_gates(ledger, section, part):
        raise SystemExit(f"{section}/{part}: a failed gate: refused")
    if "unresolved_stop" in row or row.get("driver") != MARK or not row.get("completed_fixed"):
        raise SystemExit(f"{section}/{part}: not completed under the fixed cap: refused")
    if row.get("identity") != budgeted._identity(fingerprint, shards, row["allocation_hours"]):
        raise SystemExit(f"{section}/{part}: another identity: refused")
    if (row.get("operational_identity") or {}).get("adapter_sha256") != own_sha256():
        raise SystemExit(f"{section}/{part}: the adapter changed since its run: refused")
    if not run.completed():
        raise SystemExit(f"{section}/{part}: the driver's run is not complete: refused")
    for path in sorted(run.charge_dir.glob("b*.json")):
        if not json.loads(path.read_text("utf-8"))["closed"]:
            raise SystemExit(f"{section}/{part}: an open charge ({path.name}): refused")
    if abs(row["spent_hours"] - run.spent_seconds() / 3600.0) > 1e-9:
        raise SystemExit(f"{section}/{part}: the ledger and the driver disagree: refused")
    return row


# --- set A --------------------------------------------------------------------------------------


def _set_a() -> tuple[list, str, Path]:
    rows = d2f.schedule(SET)
    fp = d2f.fingerprint(rows)  # D2-F's complete code identity, its frozen-list guard included
    return rows, fp, d2f.OUT / fp


def run() -> None:
    """D2-F's set A with the fixed cap: the funding, then one lock over the identity and resume
    checks, the caps, the effective cap and its margin, the start's record and the driver."""
    lv.assert_bound()
    if WORKERS > rc.workers_now(dt.datetime.now(rc.BRT)):
        raise SystemExit("more workers than R1 allows: refused")
    rows, fp, out = _set_a()
    step = f"d2f run {SET} (fixed cap)"
    with lv.Exclusive(step):
        fund()
        if budgeted._row(budgeted.load(), lv.SECTION, PART).get("completed_fixed"):
            raise SystemExit(f"{PART}: already completed")  # before any start is recorded
        lv.check_run(PART, fp, rows)
        lv.check_caps(step, 0.5, 300_000, len(rows) * 60_000 + 50_000_000)
        line_cap = lv.hard_cap(PART, WORKERS, SHARD_LIMIT)  # a STOP if no room is left
        cap = effective_cap(budgeted._row(budgeted.load(), lv.SECTION, PART), WORKERS,
                            SHARD_LIMIT, line_cap)  # fmt: skip
        check_margin(PART, cap, PROJECTION)
        earlier = lv.record_start(PART, fp, rows)
        kind = "the pre-approved resume" if earlier else "a first run"
        print(f"{PART}: {len(rows)} shards; {WORKERS} workers; cap {cap:.4f} CPU-h; {kind}",
              flush=True)  # fmt: skip
        state = execute_fixed(
            lv.SECTION, PART, out, d2f.shard, rows, fp, WORKERS, SHARD_LIMIT,
            line_cap=line_cap, expected_cap=cap, pin=rc.pin()[:WORKERS], pause_at=rc.NO_PAUSE,
        )  # fmt: skip
    print(state, flush=True)
    lv.check_caps(f"d2f after the run {SET}", 0.0, 0)
    if state != "complete":
        raise SystemExit(f"STOP for the maintainer: {state}")


# --- the summary, its receipt and the wrapper's charge ------------------------------------------


def _summary_charges(book: dict) -> dict[str, float]:
    return {
        c["name"]: c["hours"]
        for c in book.get("charges", [])
        if c["name"].startswith(SUMMARY_CHARGE_PREFIX)
    }


def _open_attempt() -> dict:
    book = budgeted.load()
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    attempt = {
        "attempt": f"d2f-{SET}-summary-{stamp}-pid{os.getpid()}-{len(book.get(ATTEMPTS, []))}",
        "part": PART,
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "prior_summary_charges": sorted(_summary_charges(book)),
        "operational_identity": budgeted._row(book, lv.SECTION, PART)["operational_identity"],
        "adapter_sha256": own_sha256(),
    }
    book.setdefault(ATTEMPTS, []).append(attempt)
    budgeted.save(book)
    return attempt


def _new_summary_charges(attempt: dict) -> dict[str, float]:
    """Under the ledger's lock no other process charges (``lv.charge`` takes the same lock), so
    a D2-F summary charge that was not on file when the attempt opened is the inner summary's."""
    now = _summary_charges(budgeted.load())
    return {n: h for n, h in now.items() if n not in attempt["prior_summary_charges"]}


def _write_receipt(attempt: dict) -> dict:
    new = _new_summary_charges(attempt)
    if len(new) != 1:
        raise SystemExit(
            f"{len(new)} new charges of D2-F's summary in this attempt: the binding is "
            "uncertain; a STOP for the maintainer's reconciliation"
        )
    ((name, hours),) = new.items()
    receipt = {
        "attempt": attempt["attempt"],
        "part": PART,
        "record": RECORD.name,
        "charge_name": name,
        "charge_hours": hours,
        "summary_sha256": hashlib.sha256(RECORD.read_bytes()).hexdigest(),
        "operational_identity": attempt["operational_identity"],
        "adapter_sha256": own_sha256(),
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    book = budgeted.load()
    book.setdefault(RECEIPTS, []).append(receipt)
    budgeted.save(book)
    return receipt


def check_receipt() -> dict:
    """The record's accounting proof: exactly one receipt bound to its SHA-256, its attempt on
    file, its charge on file with the same hours and absent before the attempt, and the same
    operational identity and adapter. A missing or uncertain binding is a STOP."""
    book = budgeted.load()
    digest = hashlib.sha256(RECORD.read_bytes()).hexdigest()
    bound = [r for r in book.get(RECEIPTS, []) if r.get("summary_sha256") == digest]
    if len(bound) != 1:
        raise SystemExit(
            f"{len(bound)} closing receipts bound to {RECORD.name}'s SHA-256: the charge of the "
            "attempt that produced it is not proven; a STOP for the maintainer's reconciliation"
        )
    receipt = bound[0]
    attempt = {a["attempt"]: a for a in book.get(ATTEMPTS, [])}.get(receipt.get("attempt"))
    op = budgeted._row(book, lv.SECTION, PART).get("operational_identity")
    charges = _summary_charges(book)
    name = receipt.get("charge_name")
    proven = (
        attempt is not None
        and receipt.get("operational_identity") == op == attempt["operational_identity"]
        and receipt.get("adapter_sha256") == own_sha256() == attempt["adapter_sha256"]
        and name in charges
        and charges[name] == receipt.get("charge_hours")
        and name not in attempt["prior_summary_charges"]
    )
    if not proven:
        raise SystemExit(
            "the closing receipt does not bind the attempt, its charge and the operational "
            "identity: a STOP for the maintainer's reconciliation"
        )
    return receipt


def summarize() -> None:
    """Under the ledger's lock: the accounted completion, then ``d2f_floor``'s own summary (its
    caps, its charge, its stops, its write-once record), then the internal receipt, then the
    wrapper's charge in ``finally`` (on every path), and **only after that charge succeeded** the
    operational closing (Codex, d2fa round 1): "Preserve d2f-A.json and the internal receipt as
    evidence. Persist a separate operational closing only after the wrapper's successful charge,
    binding the record's SHA, the attempt, the identity, the receipt and the wrapper's charge.
    Record the summary's state explicitly. The operational acceptance requires that closing; its
    absence or inconsistency causes a STOP. A scientific STOP stays recorded and propagated, with
    no publication of success."

    The receipt is written whenever the record now exists, also when ``d2f_floor`` ends in a STOP
    after writing it (its stops are facts of the record); the closing then has the state
    ``stopped``, never ``final``, and the STOP propagates. If set A is not futile, set B needs
    money beyond the authorized: a STOP with that request, after the closing."""
    lv.assert_bound()
    with lv.Exclusive(f"d2f summary {SET} (fixed cap)"):
        started = time.process_time()
        attempt = receipt = inner_exc = None
        try:
            if RECORD.exists() or CLOSING.exists():
                raise SystemExit(f"{RECORD.name} or {CLOSING.name} exists: written once")
            rows, fp, out = _set_a()
            run_ = driver.Run(out, d2f.shard, rows, fp, 1.0, 1, max_shard_seconds=SHARD_LIMIT)
            check_completed(lv.SECTION, PART, run_, fp, rows)
            attempt = _open_attempt()
            try:
                d2f.summarize(SET)
            except BaseException as exc:  # noqa: BLE001 - re-raised after the closing
                inner_exc = exc
            if RECORD.exists():
                receipt = _write_receipt(attempt)
        finally:
            inner = 0.0
            if attempt is not None:  # only what the inner summary provably charged
                inner = sum(_new_summary_charges(attempt).values()) * 3600.0
            used = max(0.0, time.process_time() - started - inner)
            n = sum(
                1
                for c in budgeted.load().get("charges", [])
                if c["name"].startswith(WRAPPER_CHARGE_PREFIX)
            )
            stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
            wrapper_name = f"{WRAPPER_CHARGE_PREFIX}{stamp}_{n:03d}"  # unique under the lock
            lv.charge(
                wrapper_name,
                used / 3600.0,
                f"d2f_fixed_cap.summarize, apart from d2f_floor.summarize's own charge: "
                f"{used:.1f} s",
            )
        # reached only after a normal end of the block above and the wrapper's charge
        if receipt is None:
            if inner_exc is not None:
                raise inner_exc  # no record: nothing to close
            raise SystemExit("d2f_floor's summary ended without its record: a STOP")
        closing = {
            "label": "v0.5.5 R1, D2-F set A: the operational closing of the fixed-cap summary",
            "method_status": "not_validated",
            "state": "final" if inner_exc is None else "stopped",
            "stop": None if inner_exc is None else str(inner_exc),
            "record": RECORD.name,
            "record_sha256": receipt["summary_sha256"],
            "attempt": attempt["attempt"],
            "operational_identity": attempt["operational_identity"],
            "adapter_sha256": own_sha256(),
            "receipt": receipt,
            "wrapper_charge": {"name": wrapper_name, "hours": used / 3600.0},
            "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        with CLOSING.open("x", encoding="utf-8", newline="\n") as fh:  # written once
            fh.write(json.dumps(closing, indent=1, sort_keys=True) + "\n")
    if inner_exc is not None:
        raise inner_exc
    if json.loads(RECORD.read_text("utf-8")).get("futile_after_A") is False:
        raise SystemExit(
            "set A is not futile: set B needs about "
            f"{ALLOCATION:.1f} CPU-h beyond what is authorized; STOP with the request"
        )


def check_closed() -> dict:
    """The operational acceptance of set A's record: the closing on file, bound to the record's
    SHA-256, to a receipt that ``check_receipt`` proves, to the same attempt and operational
    identity, to this adapter, and to the wrapper's charge on file with the same hours; its state
    ``final`` (a closing ``stopped`` is a recorded STOP, never a success). Any absence or
    inconsistency is a STOP for the maintainer's reconciliation."""
    if not CLOSING.exists():
        raise SystemExit(f"{CLOSING.name} is missing: the record is not closed; a STOP")
    closing = json.loads(CLOSING.read_text("utf-8"))
    receipt = check_receipt()
    book = budgeted.load()
    charges = {c["name"]: c["hours"] for c in book.get("charges", [])}
    wrapper = closing.get("wrapper_charge") or {}
    bound = (
        closing.get("record_sha256") == hashlib.sha256(RECORD.read_bytes()).hexdigest()
        and closing.get("receipt") == receipt
        and closing.get("attempt") == receipt["attempt"]
        and closing.get("operational_identity") == receipt["operational_identity"]
        and closing.get("adapter_sha256") == own_sha256()
        and wrapper.get("name") in charges
        and charges[wrapper["name"]] == wrapper.get("hours")
    )
    if not bound:
        raise SystemExit(f"{CLOSING.name} does not bind the record and its charges: a STOP")
    if closing.get("state") != "final":
        raise SystemExit(f"set A's summary is closed in a STOP ({closing.get('stop')}): a STOP")
    return closing


def accept() -> None:
    """The operational entry that accepts set A's record (read only): ``check_closed``, then the
    record's futility reading as it came out."""
    lv.assert_bound()
    closing = check_closed()
    doc = json.loads(RECORD.read_text("utf-8"))
    shown = {k: doc.get(k) for k in ("futile_after_A", "outcome_per_variant", "stops")}
    print(json.dumps({"closing": closing["utc"], **shown}, indent=1, sort_keys=True))


def check() -> None:
    """Read only (no ledger write, no lock): the fingerprint through D2-F's frozen-list guard in
    this process, the rows, the protected cap of the authorized allocation and the margin, the
    ledger's current allocations and D1-P set A's futility, for the procedure posted before the
    run."""
    lv.assert_bound()
    rows, fp, out = _set_a()
    parts = lv._rows()
    cap = protected_cap(ALLOCATION, WORKERS, SHARD_LIMIT)
    report = {
        "fingerprint": fp,
        "shards": len(rows),
        "planets": sum(len(a["indices"]) for _, a in rows),
        "out": out.relative_to(d2f.ROOT).as_posix(),
        "adapter_sha256": own_sha256(),
        "allocation_hours": ALLOCATION,
        "workers": WORKERS,
        "shard_limit_seconds": SHARD_LIMIT,
        "protected_cap_hours": cap,
        "margin_needed_hours": CAP_MARGIN * PROJECTION["projection_hours"],
        "fits": cap >= CAP_MARGIN * PROJECTION["projection_hours"],
        # what the line leaves now (lv.hard_cap's ``left``, the part having spent nothing)
        "line_left_cap_hours_now": (
            lv.LINE_HOURS - lv.CHARGES_ROOM - lv.spent() - WORKERS * SHARD_LIMIT / 3600.0
        )
        / lv.OVERSHOOT,
        "ledger_allocations": {p: r["allocation_hours"] for p, r in parts.items()},
        "d1p_a_futile": json.loads(D1P_A.read_text("utf-8")).get("futile_after_A"),
        "record_exists": RECORD.exists(),
        "closing_exists": CLOSING.exists(),
    }
    print(json.dumps(report, indent=1, sort_keys=True))


COMMANDS = {"run": run, "summarize": summarize, "check": check, "accept": accept}


if __name__ == "__main__":
    if budgeted.LEDGER != lv.HERE / "ledger.json":
        raise SystemExit("budgeted is not pointed at v0.5.5's ledger: refused")
    COMMANDS[sys.argv[1]]()
