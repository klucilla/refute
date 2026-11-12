"""v0.5.4, I4's completion after the interruption (#217; the maintainer's decision of 2026-11-12,
15:46, items 1 and 2). ``method_status: not_validated``.

The part ``h1_i4`` (``i4_bound.py``, fingerprint ``161851db746b905b``) was ended at 10 of its 290
planets when the desktop app restarted at about 15:40; no worker survived, and its running batch's
charge file stayed open. As the D2/D4 completion and stage A's amendment 1 did, and without editing
``i4_bound.py`` (it is in its own fingerprint):

1. ``run``: the interruption is reconciled as a fact. The driver's own crash rule closes the open
   batch with its charge (``driver.Run._reconcile_crashes``), the part's consumption is set from
   the driver's charges (``budgeted.finish``), and the interruption is recorded as a stop and at
   once reconciled with the maintainer's decision as its reason. Nothing is deleted. Then the 280
   rows the part did not finish run as a new part ``h1_i4_rest`` (6 CPU-h transferred from
   ``h1_reserve``), with ``i4_bound.shard``, the same fingerprint and the same rows, in their own
   folder. A stop of the new part comes back to the maintainer; no other rerun is pre-approved.
2. ``summarize``: the 290 records, the first part's 10 and the rest's 280, every row exactly once
   and each shard checked by its sidecar, go through ``i4_bound.summarize``'s own computation (its
   reader pointed at these records), which writes ``i4-bound.json``. **Planet 3129**, unresolved in
   I1 (a raw and enforced ``odd_even`` FAIL, not a sensitivity case), is excluded from L by the
   maintainer's decision, taken before any I4 result was read; its record is reported apart.

Every run passes ``pause_at`` = 2026-11-18 19:30 (the maintainer's drain: no batch opens and no
shard is dispatched after it, and the batch in flight finishes).
"""

from __future__ import annotations

import datetime as dt
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import i4_bound as i4  # noqa: E402,I001  (it imports stage A's and B's modules, then ledger_i)
from i4_bound import budgeted, ledger_i  # noqa: E402

import driver  # noqa: E402  (v0.5.2's, on the path set by ledger_i)

MAIN_PART, REST_PART = i4.PART, "h1_i4_rest"
MAIN_FP = "161851db746b905b"
OUT_REST = ledger_i.ROOT / ".cache/v054/i4-rest"
REST_HOURS = 6.0
EXCLUDED = 3129  # unresolved in I1: excluded from L by the maintainer's decision (item 2)
PAUSE_AT = dt.datetime(2026, 11, 18, 19, 30, tzinfo=driver.BRT)
INTERRUPTION_STOP = "interrupted: the desktop app restarted"
LOCK_STALE = ledger_i.ROOT / ".cache/v054/ledger.lock"
INTERRUPTION = (
    "Interrupted at about 15:40 on 2026-11-12, when the desktop app restarted, at 10 of 290 "
    "planets; no worker survived (each recorded PID checked). The maintainer's decision of "
    "2026-11-12, 15:46, item 1 (#217): the open batch is closed by the driver's crash charge "
    "and recorded as a fact; the 280 remaining planets run as part h1_i4_rest with the same "
    "code, fingerprint and rows (i4_rest.py)."
)


def _main_run(rws: list) -> driver.Run:
    return driver.Run(i4.OUT / MAIN_FP, i4.shard, rws, MAIN_FP, 1.0, 1, pin=i4.PIN,
                      max_shard_seconds=i4.MAX_SHARD_SECONDS)  # fmt: skip


def _schedule() -> tuple[list, str]:
    rws = i4.schedule()
    fp = i4.fingerprint(rws)
    if fp != MAIN_FP:
        raise SystemExit(f"the fingerprint is {fp}, not the first part's {MAIN_FP}: refused")
    return rws, fp


def _transfer_atomic(reason: str) -> None:
    """``ledger_i.transfer``'s effect in one atomic save: the debit, the credit and the history
    together (Codex's round 1; ``ledger_i.py`` is in I1's and I4's fingerprints, so it is not
    edited)."""
    book = budgeted.load()
    parts = book["sections"][ledger_i.SECTION]["parts"]
    src = parts["h1_reserve"]
    if src["allocation_hours"] - REST_HOURS < src.get("spent_hours", 0.0):
        raise SystemExit("h1_reserve cannot give back hours it has spent: refused")
    src["allocation_hours"] -= REST_HOURS
    parts[REST_PART] = {"allocation_hours": REST_HOURS}
    total = sum(r["allocation_hours"] for r in parts.values())
    if total > budgeted.LINES[ledger_i.SECTION] + 1e-9:
        raise SystemExit("the allocations would pass the line: refused")
    book.setdefault("transfers", []).append(
        {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "from": "h1_reserve",
         "to": REST_PART, "hours": REST_HOURS, "reason": reason}
    )  # fmt: skip
    budgeted.save(book)


def _attempts_path(fp: str) -> Path:
    return OUT_REST / fp / "run-attempts.jsonl"


def _attempt(fp: str, what: str, state: str | None = None) -> None:
    """A durable record of each run's start and end (Codex's round 2): a start without an end is an
    interruption, and a later run refuses it."""
    path = _attempts_path(fp)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "event": what,
            "pid": os.getpid(), "state": state}  # fmt: skip
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(line, sort_keys=True) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def _open_attempts(fp: str) -> list:
    path = _attempts_path(fp)
    if not path.exists():
        return []
    events = [json.loads(x) for x in path.read_text("utf-8").splitlines() if x.strip()]
    starts = [e for e in events if e["event"] == "start"]
    ends = [e for e in events if e["event"] == "end"]
    return starts[len(ends) :] if len(starts) > len(ends) else []


def _check_attempts(fp: str) -> None:
    open_ = _open_attempts(fp)
    if open_:
        raise SystemExit(f"{REST_PART}: a run started at {open_[0]['utc']} never ended (another "
                         "interruption): a STOP for the maintainer")  # fmt: skip


def run() -> None:
    ledger_i.assert_bound()
    before = ledger_i.v052_ledger_sha256()
    try:
        rws, fp = _schedule()
        main = _main_run(rws)
        alive = main.workers_still_running()
        if alive:
            raise SystemExit(f"workers of the interrupted batch are alive: {alive}: refused")
        done = main._done()  # every finished shard checked by its sidecar
        rest = [(sid, a) for sid, a in rws if sid not in done]
        if len(done) + len(rest) != 290 or not rest:
            raise SystemExit(f"{len(done)} done and {len(rest)} left: refused")
        book = ledger_i._rows()
        row = book[MAIN_PART]
        reconciled = any(r.get("reason") == INTERRUPTION for r in row.get("reconciled", []))
        pending = row.get("unresolved_stop")
        # a pending stop is checked whatever the history (Codex's round 2): only this step's own
        # intermediate state, before its reconciliation, may be resumed
        if pending is not None and (reconciled or pending != INTERRUPTION_STOP):
            raise SystemExit(f"{MAIN_PART}: an unexpected stop: {pending}")
        if main.unresolved_stop() is not None:
            raise SystemExit(f"{MAIN_PART}: a stop in the driver's folder: refused")
        if not reconciled and REST_PART in book:
            raise SystemExit(f"{REST_PART} exists before the reconciliation: refused")
        _check_attempts(fp)
        if REST_PART in book:
            transfers = budgeted.load().get("transfers", [])
            if not any(t.get("to") == REST_PART and t.get("reason") == INTERRUPTION
                       for t in transfers):  # fmt: skip
                raise SystemExit(f"{REST_PART} exists without its transfer record: refused")
            rest_run = driver.Run(OUT_REST / fp, i4.shard, rest, fp, 1.0, 1, pin=i4.PIN,
                                  max_shard_seconds=i4.MAX_SHARD_SECONDS)  # fmt: skip
            if rest_run.charge_dir.exists() and any(
                not json.loads(f.read_text("utf-8"))["closed"]
                for f in rest_run.charge_dir.glob("b*.json")
            ):
                raise SystemExit(f"{REST_PART}: an open batch (another interruption): a STOP "
                                 "for the maintainer")  # fmt: skip
        reserve = len(rest) * i4.MAX_RECORD_BYTES + i4.RUN_OVERHEAD_BYTES
        ledger_i.check_caps("i4 rest run", reserve_days=0.3, reserve_tokens=0,
                            reserve_bytes=reserve)  # fmt: skip
        if not reconciled:
            # the interruption as a fact: the driver's crash charge, then the stop, reconciled
            main._reconcile_crashes()
            charged = main.spent_seconds() / 3600.0
            if pending is None:
                ledger = budgeted.load()
                stop = budgeted.finish(ledger, ledger_i.SECTION, MAIN_PART, charged)
                if stop is not None:  # a real budget stop is kept, never overwritten
                    raise SystemExit(f"STOP for the maintainer: {stop}")
                ledger = budgeted.load()
                budgeted._stop(ledger, ledger["sections"][ledger_i.SECTION]["parts"][MAIN_PART],
                               INTERRUPTION_STOP)  # fmt: skip
            budgeted.reconcile(ledger_i.SECTION, MAIN_PART, INTERRUPTION)
            print(f"{MAIN_PART}: the interruption reconciled; charged {charged:.4f} CPU-h",
                  flush=True)  # fmt: skip
        if REST_PART not in ledger_i._rows():
            with ledger_i.Exclusive("transfer"):  # re-entrant: the run holds the lock already
                _transfer_atomic(INTERRUPTION)
        ledger_i.declare()
        ledger_i.refuse_new_identity(REST_PART, fp, rest)
        cap = ledger_i.hard_cap(REST_PART, i4.WORKERS, i4.MAX_SHARD_SECONDS)
        print(len(rest), "rows; hard cap", round(cap, 3), "CPU-h; fingerprint", fp, flush=True)
        _attempt(fp, "start")
        state = budgeted.execute(
            ledger_i.SECTION, REST_PART, OUT_REST / fp, i4.shard, rest, fp, i4.WORKERS,
            pin=i4.PIN, max_shard_seconds=i4.MAX_SHARD_SECONDS, hard_cap_hours=cap,
            pause_at=PAUSE_AT,
        )  # fmt: skip
        _attempt(fp, "end", state)  # only a run that returned records its end
        print(state, flush=True)
        ledger_i.check_caps("i4 rest after the run", 0.0, 0)
    finally:
        if ledger_i.v052_ledger_sha256() != before:
            raise SystemExit("the v0.5.2 ledger changed: refused")
    if state != "complete":
        raise SystemExit(f"STOP for the maintainer: {state}")


def _records(rws: list, fp: str) -> tuple[list, str | None]:
    """The 290 records: the first part's verified shards and the rest's, every row exactly once;
    a refusal text if the rest did not complete (its verified shards are still read)."""
    found: dict = {}
    main = _main_run(rws)
    for sid in main._done():
        found[sid] = main._paths(sid)[0].read_bytes()
    rest_rows = [(sid, a) for sid, a in rws if sid not in found]
    refusal = None
    rest_run = driver.Run(OUT_REST / fp, i4.shard, rest_rows, fp, 1.0, 1, pin=i4.PIN,
                          max_shard_seconds=i4.MAX_SHARD_SECONDS)  # fmt: skip
    book = ledger_i._rows()
    ledger = budgeted.load()
    for part, handle in ((MAIN_PART, main), (REST_PART, rest_run)):
        if "unresolved_stop" in book.get(part, {}) or handle.unresolved_stop():
            refusal = f"{part}: an unresolved stop"
        if budgeted._open_gates(ledger, ledger_i.SECTION, part):
            refusal = f"{part}: a failed gate"
    for sid in rest_run._done():
        if sid in found:
            raise SystemExit(f"{sid}: done in both parts: refused")
        found[sid] = rest_run._paths(sid)[0].read_bytes()
    if _open_attempts(fp):
        refusal = f"{REST_PART}: a run that never ended (an interruption)"
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
    return recs, refusal


def summarize() -> None:
    ledger_i.assert_bound()
    rws, fp = _schedule()
    recs, refusal = _records(rws, fp)
    excluded = [r for r in recs if r["set"] == "fresh" and r["index"] == EXCLUDED]
    kept = [r for r in recs if not (r["set"] == "fresh" and r["index"] == EXCLUDED)]
    i4._read = lambda rows, fp_: (kept, refusal)  # i4_bound.summarize's computation, these records
    try:
        i4.summarize()
    except SystemExit as exc:
        stop = str(exc)
    else:
        stop = None
    doc = json.loads(i4.OUT_FILE.read_text("utf-8"))
    doc["completion"] = {
        "decision": "the maintainer's decision of 2026-11-12, 15:46 (#217)",
        "parts": {MAIN_PART: "10 planets, then interrupted (reconciled)",
                  REST_PART: "the 280 remaining planets"},
        "cpu_hours": {p: round(ledger_i.part_consumption(p), 4) for p in (MAIN_PART, REST_PART)},
        "excluded_from_L": {
            "index": EXCLUDED,
            "why": "unresolved in I1: a raw and enforced odd_even FAIL, not a sensitivity case; "
            "excluded from L and from I2's population by the maintainer's decision (item 2), "
            "taken before any I4 result was read",
            "record": excluded,
        },
        "L_threshold_note": "L is counted over the 177 eligible fresh planets other than 3129; "
        "the threshold stays 23 (at most 155 kept against 156 needed)",
    }  # fmt: skip
    i4.OUT_FILE.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", "utf-8",
                           newline="\n")  # fmt: skip
    if stop:
        raise SystemExit(stop)


def _alive(pid: int) -> bool:
    """Is any process with this PID running (its exit code still STILL_ACTIVE)? Conservative: a
    reused PID also counts as alive, so the lock is then kept."""
    import ctypes
    from ctypes import wintypes

    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    k32.OpenProcess.restype = wintypes.HANDLE
    k32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    k32.GetExitCodeProcess.restype = wintypes.BOOL
    k32.CloseHandle.argtypes = [wintypes.HANDLE]
    k32.CloseHandle.restype = wintypes.BOOL
    handle = k32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not handle:
        # only "no such process" (ERROR_INVALID_PARAMETER) proves it gone; anything else is
        # treated as alive (Codex's round 2)
        return ctypes.get_last_error() != 87
    try:
        code = wintypes.DWORD()
        if not k32.GetExitCodeProcess(handle, ctypes.byref(code)):
            return True  # the query failed: undetermined, treated as alive
        return code.value == 259  # STILL_ACTIVE
    finally:
        k32.CloseHandle(handle)


def release_stale_lock() -> None:
    """The interrupted run left ``ledger.lock`` held by a process that no longer exists. The lock
    is not deleted: it is renamed beside itself, kept as a record, after checking its PID is not
    running (``driver.still_running``). Refused for a live holder or another file."""
    if not LOCK_STALE.exists():
        print("no lock left", flush=True)
        return
    text = LOCK_STALE.read_text("utf-8").strip()
    if not text.startswith("pid ") or "; i4 run;" not in text:
        raise SystemExit(f"the lock is not the interrupted I4 run's: {text}: refused")
    pid = int(text.split(";")[0].split()[1])
    if _alive(pid):
        raise SystemExit(f"the lock's holder {pid} is running: refused")
    kept = LOCK_STALE.with_name("ledger.lock.stale-i4-run-" + text.split("; ")[-1].replace(":", ""))
    LOCK_STALE.rename(kept)
    print(f"the stale lock is kept as {kept.name}", flush=True)


if __name__ == "__main__":
    ledger_i.assert_bound()
    if sys.argv[1] == "release-lock":
        release_stale_lock()
        sys.exit(0)
    with ledger_i.Exclusive(f"i4_rest {' '.join(sys.argv[1:])}"):
        {"run": run, "summarize": summarize}[sys.argv[1]]()
