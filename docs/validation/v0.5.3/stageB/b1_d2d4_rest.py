"""v0.5.3 stage B: B1.4's D2/D4 part completed after its cap stop (#217; the maintainer's decision
of 2026-11-12, item 1). **A forecast; it decides nothing.** ``method_status: not_validated``.

The part ``b1_forecast_d2d4`` stopped at its cap (1.5 times the 10-curve checkpoint's projection,
7.01 CPU-h) at 7.09 CPU-h, with 181 of its 200 curves done and no error. The maintainer approved
reconciling that stop and running the 19 missing curves with the same code, the same fingerprint
and the same rows, at most 1.5 CPU-h more, taken from ``b1_unallocated``. The stop at the cap
stays on file as a fact (``budgeted.reconcile`` keeps it under ``reconciled``).

As stage A's amendment 1 (``a0_refusals.run_rest``): ``b1_b14.py`` and its outputs are not
edited; the missing rows run as a new part, in a folder of their own, under the first part's
fingerprint (checked equal to the folder it wrote, ``5bb3277e4a908c18``) and with
``b1_b14.shard``. If that part stops again by the driver's mechanics (its cap or projection rules,
``MECHANICS``), the maintainer pre-approved one rerun within the same 1.5 CPU-h: ``run 2``
reconciles that stop and runs the rows still missing as a second part, or, if every row finished,
runs nothing. Any other stop goes to the maintainer.

**The 1.5 CPU-h.** Attempt ``k``'s allocation is what is left of the 1.5 CPU-h, over 1.5, and its
cap is at most what is left over ``MARGIN`` (1.2: the driver's 10 % overshoot and room for its
watchdog's polling), so every attempt together stays within 1.5 CPU-h. The rest parts' consumption
is checked against 1.5 CPU-h before an attempt and again at ``summarize`` (a STOP above). Every
check runs before anything is reconciled, so that a refusal leaves the state as it was.

``summarize`` writes ``b1-forecast-d2d4-complete.json``: the 200 records (the first part's 181 and
the rest, each shard checked by its sidecar: fingerprint, argument and SHA-256), every row exactly
once, and D2 and D4 by ``b1_b14.d2d4_summary``'s frozen rules, with the stop disclosed. Its
blocker list counts diagnostics as blockers (the maintainer's item 2), so it is left out here; the
decisive blockers are in ``b1-blockers-decisive.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import b1_b14  # noqa: E402,I001
from b1_b14 import bf, budgeted, ledger_b  # noqa: E402

import driver  # noqa: E402  (v0.5.2's, on the path set by ledger_b)

MAIN_PART = "b1_forecast_d2d4"
MAIN_FP = "5bb3277e4a908c18"
REST_PARTS = ("b1_forecast_d2d4_rest", "b1_forecast_d2d4_rest2")  # the run and its one rerun
EXTRA_HOURS = 1.5  # the maintainer's ceiling over every rest attempt
# the stops of the driver's mechanics that the pre-approved rerun may follow (``budgeted`` and
# ``driver``'s cap and projection rules); any other stop goes to the maintainer
MECHANICS = (
    "stopped: the cap is reached",
    "stopped: the cap was passed by the end of the run",
    "over the cap: the workers were ended",
    "stopped: the projection",
)
# the cap's divisor: the driver's 10 % overshoot and room for its watchdog, which polls every half
# second and ends the workers only after the limit is passed (Codex's round 1)
MARGIN = 1.2
OUT = b1_b14.OUT
OUT_FILE = HERE / "b1-forecast-d2d4-complete.json"
RECONCILE = (
    "The maintainer's decision of 2026-11-12, item 1 (#217): the part stopped at its cap (1.5 "
    "times the 10-curve checkpoint's projection of 4.67 CPU-h, so 7.01) at 7.09 CPU-h with 181 of "
    "200 curves done and no error. The stop stays recorded as a fact. The 19 missing curves run "
    "with the same code, fingerprint and rows as part b1_forecast_d2d4_rest (and, if it stops "
    "again by the driver's mechanics, one pre-approved rerun as b1_forecast_d2d4_rest2), within "
    "1.5 CPU-h more taken from b1_unallocated (b1_d2d4_rest.py)."
)


def _schedule() -> tuple[list, str]:
    rws = b1_b14.rows("d2d4")
    fp = b1_b14.fingerprint("d2d4", rws)
    if fp != MAIN_FP:
        raise SystemExit(f"the fingerprint is {fp}, not the first part's {MAIN_FP}: refused")
    return rws, fp


def _driver(part: str, rws: list, fp: str) -> driver.Run:
    """A read-only handle on a part's folder (the full schedule: a rest part's rows are a subset,
    with the same arguments)."""
    return driver.Run(
        OUT / part / fp, b1_b14.shard, rws, fp, 1.0, 1, pin=bf.PIN,
        max_shard_seconds=bf.MAX_SHARD_SECONDS,
    )  # fmt: skip


def _done(part: str, rws: list, fp: str) -> dict:
    """A part's finished shards, each checked by its sidecar (``driver.Run._done``)."""
    run = _driver(part, rws, fp)
    return {sid: run._paths(sid)[0].read_bytes() for sid in run._done()}


def _consumed() -> float:
    """The rest attempts' consumption, refused above the 1.5 CPU-h (a STOP for the maintainer)."""
    used = sum(ledger_b.part_consumption(p) for p in REST_PARTS)
    if used > EXTRA_HOURS + 1e-9:
        raise SystemExit(f"the rest parts consumed {used:.4f} CPU-h, above 1.5: a STOP")
    return used


def _authorized(row: dict) -> bool:
    """The first rest attempt's stop was reconciled by this step, for a stop of the driver's
    mechanics: the one rerun is authorized (persisted, so a resume never authorizes another)."""
    return any(
        r.get("reason") == RECONCILE and str(r.get("stop", "")).startswith(MECHANICS)
        for r in row.get("reconciled", [])
    )


def run(attempt: int) -> None:
    """Every check runs before anything is reconciled, so that a refusal leaves the state as it
    was and the step can be tried again (Codex's round 1); a part already started resumes under
    its identity."""
    if attempt not in (1, 2):
        raise SystemExit("usage: run 1, or run 2 (the one pre-approved rerun)")
    part = REST_PARTS[attempt - 1]
    before = ledger_b.v052_ledger_sha256()
    try:
        ledger_b.check_caps(f"b1 d2d4 rest {attempt}", reserve_days=0.1, reserve_tokens=0,
                            in_b0=False)  # fmt: skip
        rws, fp = _schedule()
        book = ledger_b._rows()
        if attempt == 1:
            if REST_PARTS[1] in book:
                raise SystemExit("the rerun's part exists already: refused")
            cause = MAIN_PART
            earlier = [MAIN_PART]
        else:
            first = book.get(REST_PARTS[0])
            if first is None:
                raise SystemExit("the rerun runs only after the first rest attempt: refused")
            stop = first.get("unresolved_stop")
            if stop is None and not _authorized(first):
                raise SystemExit("the rerun runs only after the first rest attempt stopped")
            if stop is not None and not stop.startswith(MECHANICS):
                raise SystemExit(f"not a stop of the driver's mechanics: {stop}: brought to "
                                 "the maintainer")  # fmt: skip
            cause = REST_PARTS[0]
            earlier = [MAIN_PART, REST_PARTS[0]]
        if attempt == 2 and "unresolved_stop" in book[MAIN_PART]:
            raise SystemExit("the first part's stop is not reconciled: refused")
        # the cause's stop, in the ledger and in the driver's folder: pending, or already
        # reconciled by an earlier call of this step (Codex's round 2: a resume between the
        # reconciliation and the part's creation stays possible, without authorizing another try)
        ledger_pending = "unresolved_stop" in book[cause]
        handle = _driver(cause, rws, fp)
        driver_stop = handle.unresolved_stop()
        if driver_stop is not None and not driver_stop.startswith(MECHANICS):
            raise SystemExit(f"{cause}: the driver's stop is not of its mechanics: {driver_stop}: "
                             "brought to the maintainer")  # fmt: skip
        done: set = set()
        for p in earlier:
            done |= set(_done(p, rws, fp))  # every sidecar checked before any change
        rest = [(sid, a) for sid, a in rws if sid not in done]
        left = EXTRA_HOURS - _consumed()
        if rest:  # the refusals that can be foreseen, before anything changes
            if left <= 0.0:
                raise SystemExit("the 1.5 CPU-h are used: a STOP")
            bf.disk_check(len(rest))
            if part in book:
                ledger_b.refuse_new_identity(part, fp, rest)
            elif book["b1_unallocated"]["allocation_hours"] < left / budgeted.STOP_FACTOR:
                raise SystemExit("b1_unallocated cannot give the allocation: refused")
            if budgeted._open_gates(budgeted.load(), ledger_b.SECTION, part):
                raise SystemExit("a failed gate blocks the part: refused")
        elif attempt == 1:
            raise SystemExit("no row is missing: nothing to run")
        # every check passed: only now is the cause's stop reconciled (each stop stays on file:
        # ``reconciled`` in the ledger, ``stop-reconciled-*.json`` in the driver's folder)
        if ledger_pending:
            budgeted.reconcile(ledger_b.SECTION, cause, RECONCILE)
        if driver_stop is not None:
            handle.reconcile(RECONCILE)
        if not rest:
            # a stop after every row finished (the cap passed by the end of the run): the rerun
            # only reconciles it and runs nothing (declared on #217 before the run)
            print("no row is missing: the stop is reconciled and nothing runs", flush=True)
            return
        if part not in ledger_b._rows():
            ledger_b.transfer("b1_unallocated", part, round(left / budgeted.STOP_FACTOR, 6),
                              RECONCILE)  # fmt: skip
        ledger_b.declare()
        ledger_b.refuse_new_identity(part, fp, rest)
        cap = ledger_b.hard_cap(part, bf.WORKERS, bf.MAX_SHARD_SECONDS)
        cap = min(cap, left / MARGIN)
        print(len(rest), "rows; hard cap", round(cap, 3), "CPU-h; fingerprint", fp, flush=True)
        state = budgeted.execute(
            ledger_b.SECTION, part, OUT / part / fp, b1_b14.shard, rest, fp, bf.WORKERS,
            pin=bf.PIN, max_shard_seconds=bf.MAX_SHARD_SECONDS, hard_cap_hours=cap,
        )  # fmt: skip
        print(state, flush=True)
        print("disk used by B1 so far:", bf.disk_after(), "bytes", flush=True)
    finally:
        if ledger_b.v052_ledger_sha256() != before:
            raise SystemExit("the v0.5.2 ledger changed: refused")
    if state != "complete":
        raise SystemExit(state)


def summarize() -> None:
    recs, per_part, used, fp = complete_records()
    d2d4 = b1_b14.d2d4_summary(recs)
    d2d4.pop("v5_blockers")  # diagnostics counted as blockers: see b1-blockers-decisive.json
    d2d4["part_state"] = (
        "complete after a reconciled cap stop: the first part stopped at its cap (7.01 CPU-h) "
        f"at 7.09 CPU-h with 181 of 200 records; records per part {per_part}"
    )
    d2d4["smoke_index_disclosed"] = sorted(b1_b14.SMOKE_INDICES)
    d2d4["cpu_hours"] = {p: round(ledger_b.part_consumption(p), 4) for p in (MAIN_PART, *used)}
    out = {
        "label": "B1.4's D2 and D4 development forecast with the candidate version 5, the part "
        "completed after its cap stop (decides nothing)",
        "method_status": "not_validated",
        "decision": "the maintainer's decision of 2026-11-12, item 1 (#217)",
        "fingerprint": fp,
        "d2_d4": d2d4,
        "blockers": "left out: b1_b14.d2d4_summary counts diagnostics as blockers; the decisive "
        "blockers are in b1-blockers-decisive.json",
    }  # fmt: skip
    OUT_FILE.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", "utf-8", newline="\n")
    print(json.dumps(out, indent=1, sort_keys=True))


def complete_records() -> tuple[list, dict, list, str]:
    """The 200 records in schedule order, every row exactly once, each shard checked by its
    sidecar; refused unless the last rest attempt completed and no stop is unresolved. Returns the
    records, the records per part, the rest parts used and the fingerprint."""
    rws, fp = _schedule()
    book = ledger_b._rows()
    used = [p for p in REST_PARTS if p in book]
    if not used or "unresolved_stop" in book[used[-1]]:
        raise SystemExit("the rest has not completed: refused")
    if any("unresolved_stop" in book[p] for p in (MAIN_PART, *used)):
        raise SystemExit("an unresolved stop: refused")
    ledger = budgeted.load()
    for p in (MAIN_PART, *used):  # the driver's own stop file and the gates (Codex's round 1)
        if _driver(p, rws, fp).unresolved_stop() is not None:
            raise SystemExit(f"{p}: an unresolved stop in the driver's folder: refused")
        if budgeted._open_gates(ledger, ledger_b.SECTION, p):
            raise SystemExit(f"{p}: a failed gate: refused")
    _consumed()  # the 1.5 CPU-h over every rest attempt (a STOP above)
    found: dict = {}
    origin: dict = {}
    for part in (MAIN_PART, *used):
        for sid, data in _done(part, rws, fp).items():
            if sid in found:
                raise SystemExit(f"{sid}: done in two parts: refused")
            found[sid], origin[sid] = data, part
    missing = [sid for sid, _ in rws if sid not in found]
    if missing:
        raise SystemExit(f"{len(missing)} rows are missing: refused")
    recs = [
        json.loads(x) for sid, _ in rws for x in found[sid].decode().splitlines() if x.strip()
    ]  # fmt: skip
    if len(recs) != len(rws):
        raise SystemExit(f"{len(recs)} records for {len(rws)} rows: refused")
    per_part = {p: sum(o == p for o in origin.values()) for p in (MAIN_PART, *used)}
    return recs, per_part, used, fp


if __name__ == "__main__":
    with ledger_b.Exclusive(f"b1_d2d4_rest {' '.join(sys.argv[1:])}"):
        if sys.argv[1] == "run":
            run(int(sys.argv[2]))
        elif sys.argv[1] == "summarize":
            summarize()
        else:
            raise SystemExit("usage: run 1|2, or summarize")
