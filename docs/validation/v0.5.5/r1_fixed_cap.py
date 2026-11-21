"""v0.5.5, R1: the remaining parts with a **fixed, protected cap by their allocation** (#218; the
maintainer's decision of 2026-11-20, 21:00, items 1 and 3). ``method_status: not_validated``.

**Status: not released.** Codex's three rounds (``docs/plans/v0.5.5-consensus/``, conversation
``g1``) left three items pending: the proof that a recovered summary's charge belongs to that
attempt, the wrapper's charge on an exception, and stage 2's margin against the effective cap.
By the most conservative option, nothing ran through this runner. At G1 (2026-11-21) the
maintainer's adviser chose path A: the three items are applied here in Codex's text (the closing
receipt, ``_check_receipt``; the wrapper's charge in ``finally``; ``check_margin`` against the
effective cap), with round 3's tests 4 to 6, for a new Codex review (conversation ``g1r``, up to
three rounds). Nothing runs through this runner before Codex releases it.

**Why.** v0.5.4's ``budgeted_v3`` projects a part from a checkpoint of its first shards and then
caps it at 1.5 times that projection. On heterogeneous shards a checkpoint of a few shards
underestimates (v0.5.4's step 4; T2a-E's stage 1 on 2026-11-20: 3 shards projected 0.93 CPU-h,
the cap became 1.39, and 37 of 51 injections had used 1.53 when the driver ended its workers).
**The lesson, recorded:** R1's remaining parts run with a fixed cap by their allocation, with no
checkpoint and no projection rule.

**What this script is.** The scientific modules and their frozen files stay unchanged
(``t2ae_census.py``, ``ledger_v055.py``, ``budgeted_v3.py``, ``budgeted.py``, ``driver.py``), so
the checks' scientific fingerprints stay as they ran. **This operational runner is new and has an
identity of its own** (its SHA-256, the fingerprint, the part, the allocation, the rows, the
workers and the shard limit), frozen in the ledger under the lock before the first dispatch and
checked on the resume and at the summary. This exception is not a closure of the dependencies by
the FROZEN guard (which skips ``__main__``). It is run as ``__main__`` and never imported by
a check.

**The protected cap** (Codex, g1 round 1): the driver's watchdog ends the workers only above 1.10
times the cap, a threshold rather than an exact physical limit, and a batch left open by a crash
is charged ``workers × (max_shard_seconds + 20 s)``. So the cap given to the driver is
``(allocation − crash reserve − poll margin) / 1.10``, with every crash charge on file counted in
the consumption; **the dispatch is refused when that reserve does not fit**. "The factor 1.10
defines the watchdog's threshold, not an exact physical limit. Every crash charge enters the
allocation. The dispatch is refused when the necessary reserve does not fit."

**What it runs:**
- ``execute_fixed``: v0.5.2's driver (``driver.Run``, unchanged) with that cap for the whole part,
  no checkpoint; the ledger's guard, the stop rules and the final accounting are ``budgeted``'s.
  A part with a stop, of another identity or run by another driver is refused. A completion
  marker is written only after ``budgeted.finish`` ends without a stop.
- **T2a-E's stage-1 completion** (item 1): a new part, ``r1_t2ae_1c``, allocation **1.5 CPU-h**
  (from the reserve), the same rows and fingerprint as stage 1, running only the injections the
  stopped run had not finished, in a folder of its own. The stopped part keeps its stop on file,
  as a fact. "Complete shard coverage is not an accounted completion: without closed charges, a
  persisted completion and the matching identity in the ledger, the summary is refused." The
  summary assembles both folders' shards (each checked against its sidecar), in schedule order,
  and hands them to ``t2ae_census``'s own summary through the declared combined reader; the
  completion record names each part's injections and consumption and the stage's total.
- **T2a-E's stage 2**: ``r1_t2ae_2`` (3.1 CPU-h, 4 workers), after stage 1's record, the
  finished completion record bound to it by SHA-256, the scientific identity and the futility
  rule; its projection is revised on measured data before it runs (the mean CPU of stage 1's 51
  injections times 51, ``stage2_projection``, superseding the planning 2.1 CPU-h), and the run is
  refused unless the **effective** cap (the one given to the driver, after every restriction) is
  at least 1.3 times it, checked under the lock before the start and written to the ledger.

Usage (from the project root, through ``launch_detached.py`` for a run):
``r1_fixed_cap.py t2ae-1c run`` then ``t2ae-1c summarize``; ``t2ae-2 run`` then
``t2ae-2 summarize``.
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
import t2ae_census as te  # noqa: E402,I001  (it binds budgeted to v0.5.5's ledger last)
import r1_common as rc  # noqa: E402
import ledger_v055 as lv  # noqa: E402
import budgeted  # noqa: E402
import driver  # noqa: E402

MARK = "fixed-cap"
COMPLETION_PART = "r1_t2ae_1c"
COMPLETION_ALLOCATION = 1.5  # the maintainer's decision of 2026-11-20 (21:00), item 1
STOPPED_PART = "r1_t2ae_1"
COMPLETION_RECORD = HERE / "t2ae-1-completion.json"
# the operational limit is 600 seconds elapsed since the dispatch (the driver's default); the
# 215 CPU-s observed in stage 1 are a reference of cost and do not show that elapsed limit; passing
# it is still a STOP (Codex, g1 round 2)
SHARD_LIMIT = 600.0
WORKERS = {COMPLETION_PART: 3, "r1_t2ae_2": 4}  # sized so that the crash reserve fits
CAP_MARGIN = 1.3  # the night decision: a part's cap at least 1.3 times its projection
POLL_SECONDS = 0.5  # the watchdog's interval (driver.py), per worker, as a margin


def own_sha256() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


# --- the protected cap ----------------------------------------------------------------------------


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


def operational_identity(part, fingerprint, rows, allocation, workers, shard_limit) -> dict:
    rows_text = json.dumps([[s, repr(a)] for s, a in rows])
    return {
        "runner_sha256": own_sha256(),
        "fingerprint": fingerprint,
        "part": part,
        "allocation_hours": allocation,
        "rows_sha256": hashlib.sha256(rows_text.encode()).hexdigest(),
        "workers": workers,
        "shard_limit_seconds": shard_limit,
    }


def effective_cap(row: dict, workers: int, shard_limit: float, line_cap: float | None) -> float:
    """The cap given to the driver, after every restriction: the allocation's protected cap, the
    line's cumulative cap (``line_cap``) and, on a resume, the cap recorded before (never
    raised). No room is a STOP."""
    cap = protected_cap(row["allocation_hours"], workers, shard_limit)
    if line_cap is not None:
        cap = min(cap, line_cap)
    if "cap_hours" in row:  # a resume never raises the cap recorded before
        cap = min(cap, row["cap_hours"])
    if cap <= 0:
        raise SystemExit("no room under the caps: a STOP")
    return cap


# --- the driver with the fixed cap ----------------------------------------------------------------


def execute_fixed(
    section: str,
    part: str,
    out: Path,
    fn,
    shards,
    fingerprint: str,
    workers: int,
    shard_limit: float,
    line_cap: float | None = None,
    expected_cap: float | None = None,
    **kwargs,
) -> str:
    """v0.5.2's driver with a protected cap fixed by the allocation, for the whole part: no
    checkpoint and no projection. "The effective cap is the smaller of the allocation's protected
    cap and the cumulative cap the line allows (``line_cap``, from ``lv.hard_cap``). A resume
    never raises the cap recorded before" (Codex, g1 round 2). Every charge, crash charges
    included, counts in the part, the line and the total. ``expected_cap``: the effective cap a
    caller checked before recording the start (stage 2's margin); a different cap here is a
    STOP, so the cap checked is the cap given to the driver (Codex, g1 round 3)."""
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
        raise SystemExit(f"{section}/{part}: the runner or its settings changed: refused")
    cap = effective_cap(row, workers, shard_limit, line_cap)
    if expected_cap is not None and abs(cap - expected_cap) > 1e-12:
        raise SystemExit(
            f"{section}/{part}: the effective cap {cap} differs from the one checked before the "
            f"start ({expected_cap}): a STOP"
        )
    row.update(identity=identity, driver=MARK, operational_identity=op, cap_hours=cap)
    row["cap_basis"] = (
        "fixed by the allocation, protected for one crash charge, the poll margin and the "
        "watchdog's 1.10; no checkpoint or projection (the maintainer's decision of 2026-11-20, "
        "21:00, item 3)"
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


def check_completed(section: str, part: str, run: driver.Run, fingerprint: str, shards) -> dict:
    """The part ended complete under this runner: the completion marker, the identities, the
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
    if (row.get("operational_identity") or {}).get("runner_sha256") != own_sha256():
        raise SystemExit(f"{section}/{part}: the runner changed since its run: refused")
    if not run.completed():
        raise SystemExit(f"{section}/{part}: the driver's run is not complete: refused")
    for path in sorted(run.charge_dir.glob("b*.json")):
        if not json.loads(path.read_text("utf-8"))["closed"]:
            raise SystemExit(f"{section}/{part}: an open charge ({path.name}): refused")
    if abs(row["spent_hours"] - run.spent_seconds() / 3600.0) > 1e-9:
        raise SystemExit(f"{section}/{part}: the ledger and the driver disagree: refused")
    return row


# --- the ledger: a part from the reserve ----------------------------------------------------------


def declare_fixed(extra: dict[str, float]) -> None:
    """The ledger's current allocations, with ``extra`` parts added and taken from the reserve
    (``lv.declare`` would restore the earlier table, so these runs never call it). A part already
    declared keeps its allocation."""
    lv.assert_bound()
    with lv.Exclusive("declare_fixed"):
        rows = lv._rows()
        if not rows:
            raise SystemExit("v0.5.5's parts are not declared: refused")
        merged = {p: r["allocation_hours"] for p, r in rows.items()}
        for part, hours in extra.items():
            if part in merged:
                if merged[part] != hours:
                    raise SystemExit(f"{part}: declared with another allocation: refused")
                continue
            merged[part] = hours
            merged["r1_reserve"] = round(merged["r1_reserve"] - hours, 6)
        if merged["r1_reserve"] < 0:
            raise SystemExit("the reserve cannot fund the part: the maintainer's")
        if sum(merged.values()) + max(lv._charges(), lv.CHARGES_ROOM) > lv.LINE_HOURS + 1e-9:
            raise SystemExit("the allocations and the charges' room pass the 64 CPU-h line")
        budgeted.declare(lv.SECTION, merged)


def check_margin(part: str, cap: float, projection: dict) -> None:
    """Under the caller's lock and before the start is recorded (Codex, g1 round 3): "The
    projection is a planning extrapolation based on the CPU of stage 1's 51 finished shards,
    with no guarantee of representativeness or of future cost. The dispatch requires an
    effective cap, after every restriction, of at least 1.3 times that projection." The
    projection, its basis and the effective cap are written to the ledger before the dispatch.
    This is not the 1.5-times-projection stop rule, which is not reintroduced."""
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


def guarded_fixed(
    part: str,
    out: Path,
    rows: list,
    fp: str,
    step: str,
    reserve_bytes: int,
    projection: dict | None = None,
) -> str:
    """One lock over the whole run: the identity and resume checks, the caps, the effective cap
    (and, with ``projection``, its margin), the start's record and the driver (as
    ``lv.guarded_run``, without its declaration)."""
    lv.assert_bound()
    workers = WORKERS[part]
    if workers > rc.workers_now(dt.datetime.now(rc.BRT)):
        raise SystemExit("more workers than R1 allows: refused")
    with lv.Exclusive(step):
        lv.check_run(part, fp, rows)
        lv.check_caps(step, 0.5, 300_000, reserve_bytes)
        line_cap = lv.hard_cap(part, workers, SHARD_LIMIT)  # a STOP if no room is left
        row = budgeted._row(budgeted.load(), lv.SECTION, part)
        cap = effective_cap(row, workers, SHARD_LIMIT, line_cap)
        if projection is not None:
            check_margin(part, cap, projection)
        earlier = lv.record_start(part, fp, rows)
        kind = "the pre-approved resume" if earlier else "a first run"
        print(f"{part}: {len(rows)} shards; {workers} workers; {kind}", flush=True)
        return execute_fixed(
            lv.SECTION,
            part,
            out,
            te.shard,
            rows,
            fp,
            workers,
            SHARD_LIMIT,
            line_cap=line_cap,
            expected_cap=cap,
            pin=rc.pin()[:workers],
            pause_at=rc.NO_PAUSE,
        )


# --- T2a-E: stage 1's completion ------------------------------------------------------------------


def _stage1() -> tuple[list, str, Path]:
    rows = te.schedule("1")
    fp = te.fingerprint(rows)
    return rows, fp, te.OUT / fp


def _completion_out(out: Path) -> Path:
    return Path(str(out) + "-completion")


def stopped_done(rows: list, fp: str, out: Path) -> dict[str, dict]:
    """The stopped run's finished shards, each checked against its sidecar (fingerprint,
    argument and bytes), by ``driver.Run._done``, unchanged."""
    return driver.Run(out, te.shard, rows, fp, 1.0, 1)._done()


def completion_rows(rows: list, done: dict) -> list:
    return [(sid, arg) for sid, arg in rows if sid not in done]


def t2ae_1c_run() -> None:
    rows, fp, out = _stage1()
    if driver.Run(out, te.shard, rows, fp, 1.0, 1).unresolved_stop() is None:
        raise SystemExit("stage 1's run has no stop on file: a completion is not what it needs")
    todo = completion_rows(rows, stopped_done(rows, fp, out))
    print(f"stage 1: {len(rows) - len(todo)} finished in the stopped run; {len(todo)} to complete")
    if not todo:
        raise SystemExit("nothing to complete")
    declare_fixed({COMPLETION_PART: COMPLETION_ALLOCATION})
    state = guarded_fixed(
        COMPLETION_PART,
        _completion_out(out),
        todo,
        fp,
        "t2ae completion of stage 1",
        len(todo) * 400_000 + 50_000_000,
    )
    print(state, flush=True)
    lv.check_caps("t2ae after the completion of stage 1", 0.0, 0)
    if state != "complete":
        raise SystemExit(f"STOP for the maintainer: {state}")


def merged_stage1_records() -> tuple[list, dict]:
    """Stage 1's records in schedule order, from the stopped run's finished shards and the
    completed completion part's, each checked against its sidecar; refused unless the completion
    part passes ``check_completed`` and every injection is in exactly one of the two folders."""
    rows, fp, out = _stage1()
    done_a = stopped_done(rows, fp, out)
    todo = completion_rows(rows, done_a)
    comp = driver.Run(_completion_out(out), te.shard, todo, fp, 1.0, 1)
    check_completed(lv.SECTION, COMPLETION_PART, comp, fp, todo)
    data_b = comp.assemble()  # refused while a shard is missing or a stop is on file
    done_b = comp._done()
    if set(done_a) & set(done_b) or len(done_a) + len(done_b) != len(rows):
        raise SystemExit("the two runs do not cover stage 1 exactly once: refused")
    by_sid = {}
    for sid, _ in rows:
        folder = out if sid in done_a else _completion_out(out)
        by_sid[sid] = (folder / "shards" / f"{sid}.bin").read_bytes()
    if b"".join(by_sid[s] for s, _ in todo) != data_b:
        raise SystemExit("the completion's bytes differ from its assembly: refused")
    recs = [json.loads(x) for x in b"".join(by_sid[s] for s, _ in rows).decode().splitlines() if x]
    book = budgeted.load()
    a_cpu = lv.part_consumption(STOPPED_PART)
    b_cpu = lv.part_consumption(COMPLETION_PART)
    split = {
        "stopped_part": STOPPED_PART,
        "stopped_part_stop": budgeted._row(book, lv.SECTION, STOPPED_PART).get("unresolved_stop"),
        "stopped_part_shards": sorted(done_a),
        "stopped_part_cpu_hours": round(a_cpu, 4),
        "completion_part": COMPLETION_PART,
        "completion_part_shards": sorted(done_b),
        "completion_part_cpu_hours": round(b_cpu, 4),
        "total_stage_1_cpu_hours": round(a_cpu + b_cpu, 4),
        "completion_operational_identity": budgeted._row(book, lv.SECTION, COMPLETION_PART)[
            "operational_identity"
        ],
        "fingerprint": fp,
    }
    return recs, split


def _completion_doc(split: dict, recovered: bool, receipt: dict) -> dict:
    return {
        "label": "v0.5.5 R1, T2a-E: stage 1 completed in a new part with a fixed cap (the "
        "maintainer's decision of 2026-11-20, 21:00, item 1)",
        "method_status": "not_validated",
        "state": "final",
        "stage_1_record": "t2ae-1.json",
        "stage_1_record_sha256": hashlib.sha256((HERE / "t2ae-1.json").read_bytes()).hexdigest(),
        "runner": "docs/validation/v0.5.5/r1_fixed_cap.py",
        "runner_sha256": own_sha256(),
        "written_after_a_recovery": recovered,
        "closing_receipt": receipt,
        "note": "The scientific modules and their frozen files are unchanged; the operational "
        "runner is new and has an identity of its own; the summary used the declared combined "
        "reader. t2ae-1.json's cpu_hours counts the stopped part only; both parts and the total "
        "are here.",
        **split,
    }


SUMMARY_CHARGE_PREFIX = "t2ae_summarize_1_"  # t2ae_census.summarize's charge for stage 1
ATTEMPTS = "summary_attempts"  # the ledger's list of the completion summary's attempts
RECEIPTS = "closing_receipts"  # the ledger's list of their closing receipts
WRAPPER_CHARGE_PREFIX = "t2ae_completion_summary_"  # the wrapper's own charge


def _expected_stage1_fields(recs: list) -> dict:
    """The decisive fields ``t2ae_census._summarize("1")`` writes, recomputed with the frozen
    functions, for checking a recovered ``t2ae-1.json``."""
    counts = te._counts(recs)
    futile = rc.t2ae_futile_after_first(
        counts["freed"], counts["valid"], counts["unknown"], te.POPULATION - len(recs)
    )
    out = {"stage": "1", "counts": counts, "futile_after_1": futile}
    if futile:
        outcome = rc.t2ae_outcome(counts["freed"], counts["valid"], counts["unknown"])
        if counts["unknown"] <= rc.T2A_MAX_UNK:
            outcome = "unresolved (no completion could reach a decisive outcome)"
        out["outcome"] = outcome
    return out


def _summary_charges(book: dict) -> dict[str, float]:
    """The stage-1 summary's charges on file, by name. A historical one (an earlier, refused
    summary) is kept and never removed."""
    return {
        c["name"]: c["hours"]
        for c in book.get("charges", [])
        if c["name"].startswith(SUMMARY_CHARGE_PREFIX)
    }


def _open_attempt() -> dict:
    """Under the ledger's lock, before the inner summary runs: the attempt's record, with the
    stage-1 summary charges already on file and the completion part's operational identity."""
    book = budgeted.load()
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    attempt = {
        "attempt": f"t2ae-1c-summary-{stamp}-pid{os.getpid()}-{len(book.get(ATTEMPTS, []))}",
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "prior_summary_charges": sorted(_summary_charges(book)),
        "operational_identity": budgeted._row(book, lv.SECTION, COMPLETION_PART)[
            "operational_identity"
        ],
        "runner_sha256": own_sha256(),
    }
    book.setdefault(ATTEMPTS, []).append(attempt)
    budgeted.save(book)
    return attempt


def _new_summary_charges(attempt: dict) -> dict[str, float]:
    """The stage-1 summary charges that were not on file when the attempt opened. Under the
    ledger's lock no other process charges (``lv.charge`` takes the same lock), so these are the
    inner summary's."""
    now = _summary_charges(budgeted.load())
    return {n: h for n, h in now.items() if n not in attempt["prior_summary_charges"]}


def _write_receipt(attempt: dict, stage1: Path) -> dict:
    """The closing receipt (Codex, g1 round 3): the attempt, its specific charge, the summary's
    SHA-256 and the operational identity, persisted before the final record."""
    new = _new_summary_charges(attempt)
    if len(new) != 1:
        raise SystemExit(
            f"{len(new)} new charges of the stage-1 summary in this attempt: the binding is "
            "uncertain; a STOP for the maintainer's reconciliation"
        )
    if not stage1.exists():
        raise SystemExit("the inner summary ended without t2ae-1.json: a STOP")
    ((name, hours),) = new.items()
    receipt = {
        "attempt": attempt["attempt"],
        "charge_name": name,
        "charge_hours": hours,
        "summary_sha256": hashlib.sha256(stage1.read_bytes()).hexdigest(),
        "operational_identity": attempt["operational_identity"],
        "runner_sha256": own_sha256(),
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    book = budgeted.load()
    book.setdefault(RECEIPTS, []).append(receipt)
    budgeted.save(book)
    return receipt


def _check_receipt(stage1: Path) -> dict:
    """A recovery's proof (Codex, g1 round 3): "The recovery requires proof of the charge of the
    attempt that produced this summary, bound to its SHA-256 and to the operational identity.
    The number of charges with a prefix is not that proof. A missing or uncertain binding causes
    a STOP." Exactly one receipt bound to this summary's SHA-256; its attempt on file, opened
    before its charge; its charge on file with the same hours; the same operational identity
    and runner."""
    book = budgeted.load()
    digest = hashlib.sha256(stage1.read_bytes()).hexdigest()
    bound = [r for r in book.get(RECEIPTS, []) if r.get("summary_sha256") == digest]
    if len(bound) != 1:
        raise SystemExit(
            f"{len(bound)} closing receipts bound to t2ae-1.json's SHA-256: the charge of the "
            "attempt that produced it is not proven; a STOP for the maintainer's reconciliation"
        )
    receipt = bound[0]
    attempts = {a["attempt"]: a for a in book.get(ATTEMPTS, [])}
    attempt = attempts.get(receipt.get("attempt"))
    op = budgeted._row(book, lv.SECTION, COMPLETION_PART).get("operational_identity")
    charges = _summary_charges(book)
    name = receipt.get("charge_name")
    proven = (
        attempt is not None
        and receipt.get("operational_identity") == op == attempt["operational_identity"]
        and receipt.get("runner_sha256") == own_sha256() == attempt["runner_sha256"]
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


def t2ae_1c_summarize() -> None:
    """Under the ledger's lock (Codex, g1 round 2): "the final record's existence is checked
    under the same lock that guards its publication; a final record is never overwritten". The
    caps and the charges' room are checked on both paths.

    Without ``t2ae-1.json``: the attempt is recorded (with the summary charges already on file),
    the merged records go to ``t2ae_census``'s own summary (its caps, its charge) with the
    combined reader for that call only, and the closing receipt binds the attempt, its new
    charge, the summary's SHA-256 and the operational identity.

    With it (an interruption before the final record): the recovery needs that receipt
    (``_check_receipt``); counting charges by prefix proves nothing; a missing or uncertain
    binding is a STOP; the historical charge is never removed. The record's code identity and
    decisive fields must equal their recomputation.

    The wrapper's own work is charged in ``finally``, under the lock, on every path, refusals
    and exceptions included (Codex, g1 round 3): "The wrapper's additional work is accounted
    also in attempts refused or interrupted by an exception. Only consumption provably charged
    by the inner summary is deducted. Any STOP prevents the final publication." The completion
    record (``state: final``) is written only after a normal end and the wrapper's charge."""
    with lv.Exclusive("t2ae completion summary"):
        started = time.process_time()
        attempt = None
        try:
            if COMPLETION_RECORD.exists():
                raise SystemExit(f"{COMPLETION_RECORD.name} exists: the record is written once")
            lv.check_caps("t2ae completion summary", reserve_days=0.05, reserve_tokens=0)
            if lv.charges_left() < 0.02:
                raise SystemExit("too little of the charges' room left for the summary: a STOP")
            recs, split = merged_stage1_records()
            stage1 = HERE / "t2ae-1.json"
            recovered = stage1.exists()
            if recovered:
                receipt = _check_receipt(stage1)
                if lv.charges_left() < 0:
                    raise SystemExit("the charges passed their room: a STOP")
                first = json.loads(stage1.read_text("utf-8"))
                if first.get("code_identity", {}).get("digest") != te.code_identity()["digest"]:
                    raise SystemExit("t2ae-1.json holds another code identity: refused")
                want = _expected_stage1_fields(recs)
                got = {k: first.get(k) for k in want}
                if got != want or ("outcome" in first) != ("outcome" in want):
                    raise SystemExit("t2ae-1.json's decisive fields differ from the merged records")
            else:

                def merged_reader(stage: str) -> list:
                    if stage != "1":
                        raise SystemExit(f"the combined reader serves stage 1 only, not {stage}")
                    return recs

                attempt = _open_attempt()
                original = te._records
                te._records = merged_reader
                try:
                    te.summarize("1")  # its caps, its charge; a STOP propagates
                finally:
                    te._records = original
                receipt = _write_receipt(attempt, stage1)
            doc = _completion_doc(split, recovered, receipt)
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
            lv.charge(
                f"{WRAPPER_CHARGE_PREFIX}{stamp}_{n:03d}",  # unique under the lock
                used / 3600.0,
                f"r1_fixed_cap.t2ae_1c_summarize, apart from t2ae_census.summarize's own charge: "
                f"{used:.1f} s",
            )
        COMPLETION_RECORD.write_text(
            json.dumps(doc, indent=1, sort_keys=True) + "\n", "utf-8", newline="\n"
        )
    print(json.dumps({k: v for k, v in doc.items() if not k.endswith("_shards")}, indent=1))


# --- T2a-E: stage 2 -------------------------------------------------------------------------------


def check_stage1_published() -> dict:
    """Stage 2 requires the stage-1 summary and the finished completion record, bound by
    SHA-256, with the same runner, besides the scientific identity and the futility rule."""
    first = te._first_stage()  # stage 1's record, under the same complete code identity
    if not COMPLETION_RECORD.exists():
        raise SystemExit("stage 1's completion record is missing: stage 2 refused")
    comp = json.loads(COMPLETION_RECORD.read_text("utf-8"))
    if comp.get("state") != "final" or comp.get("stage_1_record_sha256") != first["_sha256"]:
        raise SystemExit("the completion record is not bound to t2ae-1.json: stage 2 refused")
    if comp.get("runner_sha256") != own_sha256():
        raise SystemExit("the runner changed since stage 1's completion: stage 2 refused")
    return first


def stage2_projection(rows: list) -> dict:
    """Stage 2's projection, revised on measured data and recorded before stage 2 runs (Codex,
    g1 round 2): the mean CPU of stage 1's 51 finished injections (their sidecars, in both
    folders) times stage 2's injections. The earlier planning projection (2.1 CPU-h, from step 6's
    replay) is superseded by this measured one. The margin is checked against the **effective**
    cap under the lock, before the start (``check_margin``; Codex, g1 round 3)."""
    r1, fp1, out = _stage1()
    done_a = stopped_done(r1, fp1, out)
    todo = completion_rows(r1, done_a)
    done_b = driver.Run(_completion_out(out), te.shard, todo, fp1, 1.0, 1)._done()
    cpu = [d["cpu_seconds"] for d in (*done_a.values(), *done_b.values())]
    if len(cpu) != len(r1):
        raise SystemExit("stage 1's measured costs are incomplete: stage 2 refused")
    mean = sum(cpu) / len(cpu)
    return {
        "basis": f"the mean CPU of stage 1's {len(cpu)} finished injections (their sidecars, "
        f"{mean:.3f} s) times stage 2's {len(rows)} injections; a planning extrapolation",
        "stage_1_mean_cpu_seconds": mean,
        "projection_hours": mean * len(rows) / 3600.0,
    }


def t2ae_2_run() -> None:
    first = check_stage1_published()
    if first.get("futile_after_1") is not False:
        raise SystemExit("stage 1's futility rule holds: stage 2 refused")
    rows = te.schedule("2")
    fp = te.fingerprint(rows)
    proj = stage2_projection(rows)
    print(json.dumps(proj, indent=1), flush=True)
    state = guarded_fixed(
        te.part("2"),
        te.OUT / fp,
        rows,
        fp,
        "t2ae run 2 (fixed cap)",
        len(rows) * 400_000 + 50_000_000,
        projection=proj,
    )
    print(state, flush=True)
    lv.check_caps("t2ae after the run 2", 0.0, 0)
    if state != "complete":
        raise SystemExit(f"STOP for the maintainer: {state}")


def t2ae_2_summarize() -> None:
    check_stage1_published()
    rows = te.schedule("2")
    fp = te.fingerprint(rows)
    run = driver.Run(te.OUT / fp, te.shard, rows, fp, 1.0, 1)
    with lv.Exclusive("t2ae stage 2 summary"):
        check_completed(lv.SECTION, te.part("2"), run, fp, rows)
        te.summarize("2")


COMMANDS = {
    ("t2ae-1c", "run"): t2ae_1c_run,
    ("t2ae-1c", "summarize"): t2ae_1c_summarize,
    ("t2ae-2", "run"): t2ae_2_run,
    ("t2ae-2", "summarize"): t2ae_2_summarize,
}


if __name__ == "__main__":
    if budgeted.LEDGER != lv.HERE / "ledger.json":
        raise SystemExit("budgeted is not pointed at v0.5.5's ledger: refused")
    COMMANDS[tuple(sys.argv[1:3])]()
