"""v0.5.3 stage A, item (c3): the sample of T2a's stratum above 20 sectors, with version 4 C only
(#217; `docs/plans/v0.5.3-stageA-design.md`, section (c3), amendment 2). **A measurement on
development data; it decides nothing.** ``method_status: not_validated``. No change to ``src/``, to
any rule or to T2a's fingerprint; v0.5.2's scripts are imported, never edited.

**The controller** (v0.5.2's driver checks an overlong shard only after it completes, so (c3) has
its own, with these guarantees):

- **Containment.** Before creating any child, the controller assigns *itself* to a Windows Job
  Object with ``KILL_ON_JOB_CLOSE`` and the 8-to-31 affinity limit; every child is created inside
  the job (a child of a job's process belongs to it from creation), so none can outlive the
  controller and none can run on processors 0 to 7. Each child pins itself to its one processor
  before importing anything heavy, runs at BelowNormal (creation flag) with one thread per numeric
  library (``OMP_NUM_THREADS``, ``MKL_NUM_THREADS``, ``OPENBLAS_NUM_THREADS`` = 1).
- **Accounting, durable and conservative.** Before a launch, an attempt file (its id, the
  injection, the reservation) is written atomically. After the child exits, its processor time
  through its own handle is charged to the stage A ledger exactly once (``budgeted.charge`` named
  by the attempt id), and the attempt is closed. If the measurement fails, or if an attempt is found
  open at start (a controller crash), the attempt's full reservation is charged instead, a binding
  stop is written, and the injection stays unknown. Every created handle is cleaned up in a
  ``finally``.
- **Deadlines.** An independent watchdog thread, its clock started before each launch, ends a child
  (by its own handle) at 1,500 seconds of wall time or at the batch's deadline (28 minutes after the
  batch starts), whichever comes first; a batch therefore never passes 30 minutes. Before each
  batch, the part's cap (1.5 times its allocation) and stage A's 50 CPU-h must hold with the
  batch's own size times 1,500 CPU-seconds plus 60 seconds of overhead reserved, else a binding
  stop.
- **Outcomes.** A child writes ``<id>.part``; the controller publishes it as the injection's record
  only after a clean exit and its charge. A timeout or an interruption is authoritative: its marker
  is written atomically and the injection stays unknown even if a ``.part`` exists. A record whose
  traces failed (``forecast_t2a_diagnosis``'s instrumentation errors or copy disagreements) or whose
  final candidate differs from its C2 v0.4 record's is unknown too.
- **Gates.** The smoke (the injection whose host has the most light-curve files; a runtime proxy)
  runs alone first; its acceptance (a clean exit within 1,200 seconds) is written with the
  fingerprint, and ``run`` refuses without it. Then a checkpoint of the first ceil(n / 20)
  injections projects the part's cost by injection; past 1.5 times the allocation, a binding stop.
  A binding stop (``stop.json``) refuses every later batch until reconciled with a reason. No batch
  starts after 20:00 on 18 November.

**Each injection** (``one``): rebuilt as ``forecast_t2a_diagnosis.one`` does, then version 4 C only
(the selector treated as certified and the refusal above 20 lifted, as the forecast did; no v0.4,
version 3 or A battery), with ``forecast_t2a_diagnosis._battery``'s traces; its final gauntlet
candidate compared with its C2 v0.4 record's.

Usage: ``smoke``, then ``run``, both through ``scripts/launch_affinity.ps1``; ``summarize``
(``above20.json``). Each child is ``one <key> <slot> <part file> <processor>``.
"""

from __future__ import annotations

import sys

if __name__ == "__main__" and len(sys.argv) == 6 and sys.argv[1] == "one":
    # a child pins itself to its processor before any other import (NumPy included); the job's
    # SUBSET_AFFINITY flag lets it narrow to one processor of 8 to 31
    import ctypes

    _k = ctypes.windll.kernel32
    _k.GetCurrentProcess.restype = ctypes.c_void_p
    _k.SetProcessAffinityMask.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
    if not _k.SetProcessAffinityMask(_k.GetCurrentProcess(), 1 << int(sys.argv[5])):
        raise SystemExit(f"could not pin this child to processor {sys.argv[5]}")

import datetime as dt
import hashlib
import json
import math
import os
import subprocess
import threading
import time
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ledger_a  # noqa: E402,I001  (before budgeted: it points the ledger at stage A's)
import budgeted  # noqa: E402
import driver  # noqa: E402
import forecast_t2a as t  # noqa: E402
import forecast_t2a_diagnosis as td  # noqa: E402

PART = "c3_above_20"
OUT = ledger_a.ROOT / ".cache/v053/stageA/above20"
CHILD_SECONDS = 1500.0
SMOKE_SECONDS = 1200.0
BATCH_SECONDS = 28 * 60.0
OVERHEAD_SECONDS = 60.0
KEPT = ("SURVIVED", "WEAKENED")
CPUS = tuple(range(8, 32, 2))


def schedule() -> list[dict]:
    rows = [r for r in t.sample(t.population()) if r["stratum"] == "above_20"]
    if len(rows) != 30:
        raise SystemExit(f"not the forecast's 30 injections above 20 sectors: {len(rows)}")
    return [{"key": r["key"], "slot": r["slot"]} for r in rows]


def fingerprint() -> str:
    from refute.core.codehash import compute_code_hash

    h = hashlib.sha256(compute_code_hash().sha256.encode())
    for path in (
        Path(__file__),
        HERE / "ledger_a.py",
        td.HERE / "forecast_t2a_diagnosis.py",
        td.HERE / "forecast_t2a.py",
        td.HERE / "t2a-fetch.json",
        td.HERE / "budgeted.py",
        td.HERE / "driver.py",
    ):
        h.update(hashlib.sha256(path.read_bytes()).digest())
    return h.hexdigest()[:16]


def _atomic(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, "utf-8")
    tmp.replace(path)


def _name(item: dict) -> str:
    return f"{item['key']}-{item['slot']:02d}"


# --- one injection (the child) ---------------------------------------------------------------


def _c2_candidate(key: str, slot: int) -> dict | None:
    for line in t.C2_RECORDS.read_text("utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("kind") == "injection" and r["target_key"] == key and int(r["slot"]) == slot:
            return r["chain"]["v04"]["candidate"]
    return None


def one(key: str, slot: int, output: Path, cpu: int) -> None:
    if driver._own_mask() != 1 << cpu:  # pinned at the top of this module, before any import
        raise SystemExit(f"this child is not pinned to processor {cpu}")
    from refute.packs.tess import battery_v52

    started = time.process_time()
    rec: dict = {"key": key, "slot": slot, "processor": cpu}
    battery_v52.MAX_ORIGINAL_SECTORS = 10**6  # version 4 C: the refusal above 20 lifted
    try:
        _rebuild_and_attack(key, slot, rec)
        expected = _c2_candidate(key, slot)
        rec["c2_v04_candidate"] = expected
        rec["candidate_matches_c2"] = expected == rec["v4"]["candidate"]
        rec["status"] = "OK"
    except Exception as exc:  # noqa: BLE001 - recorded with what was filled, never dropped
        rec["status"], rec["reason"] = "ERROR", repr(exc)
    rec["cpu_seconds"] = time.process_time() - started
    _atomic(output, json.dumps(rec, sort_keys=True, default=str) + "\n")


def _rebuild_and_attack(key: str, slot: int, rec: dict) -> None:
    """``forecast_t2a_diagnosis.one`` with version 4 C only (no v0.4 battery); ``rec`` is filled
    as it goes, so an error keeps what was collected."""
    import numpy as np

    from refute.packs.tess.adapter import TessAdapter
    from refute.packs.tess.calib05 import c2
    from refute.packs.tess.detrend import detrend
    from refute.packs.tess.discover import injection as inj
    from refute.packs.tess.discover.measure import load_catalogs
    from refute.packs.tess.pipeline import global_prewhitening
    from refute.packs.tess.search import search_period

    target = t.targets()[key]
    raw, staged, plans = t._plans()
    randomness = json.loads((t.V04_STEP / "runs" / "r_inj.json").read_text("utf-8"))["beacon"][
        "randomness"
    ]
    catalog = ((t.V04_STEP / "eb_catalog.csv").as_posix(),)
    scan_path = (t.V04_STEP / "eb_catalog_scan.json").as_posix()
    tasks = c2.tasks_for(target, raw, t.CACHE, randomness, catalog, scan_path)
    task = next(x for x in tasks if x.kind == "injection" and x.slot == slot)
    base = TessAdapter().load(target, staged, t.CACHE)
    star = base.star
    drawn = inj.draw_injections(
        task.seed,
        task.k,
        inj.first_time(base),
        star.radius_rsun if star else None,
        star.logg_cgs if star else None,
    )[task.slot]
    data = inj.inject(base, drawn)
    rec["sectors"] = int(np.unique(data.lc.sector).size)
    rec["injection"] = drawn.to_dict()
    catalogs, scan = load_catalogs(catalog, scan_path, t.CACHE)
    p04 = plans["v04"]
    flat = detrend(data.lc, p04.detrend)
    pw, searched = global_prewhitening(data, p04, flat)
    cand = search_period(searched, p04.search).candidate
    rec["v4"] = {"a0_depth_calls": [], "tests": {}}
    out, _ = td._battery(data, cand, plans["v4C"], catalogs, scan, pw, rec["v4"])
    rec["v4"].update(
        candidate=out["candidate"],
        stage_verdict=out["stage_verdict"],
        stage_verdict_reason=out["stage_verdict_reason"],
        deferred=out["deferred"],
        stage_tests=out["stage_tests"],
    )


# --- the controller --------------------------------------------------------------------------


def _k32():
    import ctypes
    from ctypes import wintypes

    k = ctypes.windll.kernel32
    k.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    k.CreateJobObjectW.restype = wintypes.HANDLE
    k.SetInformationJobObject.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
    ]
    k.SetInformationJobObject.restype = wintypes.BOOL
    k.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    k.AssignProcessToJobObject.restype = wintypes.BOOL
    k.GetCurrentProcess.argtypes = []
    k.GetCurrentProcess.restype = wintypes.HANDLE
    return k


def _contain_self():
    """Put this controller in a Job Object that kills its processes when the controller's handle
    closes, limited to processors 8 to 31; every later child is created inside it."""
    import ctypes
    from ctypes import wintypes

    class BASIC(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", ctypes.c_int64),
            ("PerJobUserTimeLimit", ctypes.c_int64),
            ("LimitFlags", wintypes.DWORD),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", wintypes.DWORD),
            ("Affinity", ctypes.c_size_t),
            ("PriorityClass", wintypes.DWORD),
            ("SchedulingClass", wintypes.DWORD),
        ]

    class IO(ctypes.Structure):
        _fields_ = [(n, ctypes.c_uint64) for n in ("r", "w", "o", "rb", "wb", "ob")]

    class EXTENDED(ctypes.Structure):
        _fields_ = [
            ("Basic", BASIC),
            ("Io", IO),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    k = _k32()
    job = k.CreateJobObjectW(None, None)
    if not job:
        raise OSError("CreateJobObjectW failed")
    info = EXTENDED()
    # KILL_ON_JOB_CLOSE | LIMIT_AFFINITY | SUBSET_AFFINITY (a process may narrow its own mask)
    info.Basic.LimitFlags = 0x2000 | 0x10 | 0x4000
    info.Basic.Affinity = sum(1 << c for c in range(8, 32))
    if not k.SetInformationJobObject(job, 9, ctypes.byref(info), ctypes.sizeof(info)):
        raise OSError("SetInformationJobObject failed")
    if not k.AssignProcessToJobObject(job, k.GetCurrentProcess()):
        raise OSError("AssignProcessToJobObject (the controller) failed")
    return k, job


def _stop_paths() -> list[Path]:
    """Every unreconciled binding stop of (c3), whatever its fingerprint."""
    return sorted(OUT.glob("*/stop.json"))


def _bind_stop(fp: str, why: str) -> str:
    (OUT / fp).mkdir(parents=True, exist_ok=True)
    utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    _atomic(OUT / fp / "stop.json", json.dumps({"stop": why, "utc": utc}))
    return f"stopped: {why}"


def _charge(attempt: str, hours: float, basis: str) -> None:
    """Charge an attempt exactly once (idempotent by its id)."""
    name = f"c3 attempt {attempt}"
    if not ledger_a.charged(name):
        budgeted.charge(name, hours, basis)


def _part_spent() -> float:
    charges = budgeted.load().get("charges", [])
    return sum(c["hours"] for c in charges if c["name"].startswith("c3 "))


def _recover() -> list[str]:
    """Attempts left open by an interrupted controller, under any fingerprint: each is charged its
    full reservation (once), its injection marked interrupted and a binding stop written, all
    before the open attempt is removed."""
    found = []
    for path in sorted(OUT.glob("*/attempts/*.open")):
        fp = path.parent.parent.name
        a = json.loads(path.read_text("utf-8"))
        _charge(
            a["id"],
            a["reserved_hours"],
            "an attempt left open (controller interrupted): its full reservation, conservatively",
        )
        marker = OUT / fp / f"{a['name']}.timeout"
        if not marker.exists():
            _atomic(marker, json.dumps({**a, "outcome": "interrupted"}))
        _bind_stop(fp, f"attempt {a['id']} ({a['name']}) left open by an interrupted controller")
        path.unlink()
        found.append(a["name"])
    return found


def _launch(fp: str, item: dict, cpu: int, reserved_h: float) -> dict:
    attempt = uuid.uuid4().hex[:12]
    name = _name(item)
    part = OUT / fp / f"{name}.{attempt}.part"
    open_path = OUT / fp / "attempts" / f"{attempt}.open"
    _atomic(open_path, json.dumps({"id": attempt, "name": name, "reserved_hours": reserved_h}))
    env = {
        **os.environ,
        "OMP_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
    }
    args = [sys.executable, str(Path(__file__)), "one", item["key"], str(item["slot"])]
    proc = subprocess.Popen(
        [*args, str(part), str(cpu)],
        creationflags=0x4000,  # BELOW_NORMAL_PRIORITY_CLASS
        cwd=str(ledger_a.ROOT),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return {
        "attempt": attempt,
        "item": item,
        "name": name,
        "part": part,
        "open": open_path,
        "proc": proc,
        "reserved_h": reserved_h,
        "timed_out": False,
    }


def _clean_result(e: dict) -> bool:
    """A child's result is accepted only if it exited cleanly in time and its record is valid."""
    if e["timed_out"] or e["proc"].returncode != 0 or not e["part"].exists():
        return False
    r = json.loads(e["part"].read_text("utf-8"))
    if r.get("status") != "OK" or not r.get("candidate_matches_c2"):
        return False
    return not any(
        "instrumentation_error" in c or "COPY DISAGREES" in (c.get("why") or "")
        for c in (r.get("v4") or {}).get("a0_depth_calls", [])
    )


def _settle(fp: str, e: dict) -> str | None:
    """Charge one child exactly once and publish or mark its outcome; a stop reason, if any."""
    stop = None
    cpu_s = driver._times(e["proc"]._handle)
    if cpu_s is None:
        _charge(
            e["attempt"],
            e["reserved_h"],
            "the processor time could not be measured: the full reservation, conservatively",
        )
        stop = f"{e['name']}: processor time not measurable"
    else:
        note = "; ended at its deadline" if e["timed_out"] else ""
        _charge(
            e["attempt"], cpu_s / 3600.0, "the child's processor time through its handle" + note
        )
    final, marker = OUT / fp / f"{e['name']}.json", OUT / fp / f"{e['name']}.timeout"
    if stop is None and not marker.exists() and _clean_result(e):
        e["part"].replace(final)
    elif not marker.exists():
        doc = {
            "name": e["name"],
            "attempt": e["attempt"],
            "timed_out": e["timed_out"],
            "returncode": e["proc"].returncode,
        }
        _atomic(marker, json.dumps(doc))
    e["open"].unlink(missing_ok=True)
    return stop


def _batch(fp: str, items: list[dict], child_limit: float) -> list[str]:
    """One batch. The watchdog runs before the first launch and until every child has exited; no
    child is launched at or after the batch's deadline; each child is settled on its own."""
    reserved_h = (child_limit + OVERHEAD_SECONDS) / 3600.0
    deadline = time.monotonic() + BATCH_SECONDS
    running: list[dict] = []
    stops: list[str] = []
    state = {"dispatching": True, "error": None}
    lock = threading.Lock()

    def watchdog() -> None:
        try:
            while True:
                with lock:
                    for e in running:
                        if e["proc"].poll() is None and time.monotonic() >= e["limit"]:
                            e["timed_out"] = True
                            e["proc"].kill()  # this controller's own child
                    done = not state["dispatching"] and all(
                        e["proc"].poll() is not None for e in running
                    )
                if done:
                    return
                time.sleep(1.0)
        except Exception as exc:  # noqa: BLE001 - a watchdog failure is a binding stop
            state["error"] = repr(exc)

    dog = threading.Thread(target=watchdog, daemon=True)
    dog.start()
    try:
        for cpu, item in zip(CPUS, items, strict=False):
            if time.monotonic() >= deadline:
                break
            limit = min(time.monotonic() + child_limit, deadline)  # the clock starts first
            entry = _launch(fp, item, cpu, reserved_h)
            entry["limit"] = limit
            with lock:
                running.append(entry)
    finally:
        with lock:
            state["dispatching"] = False
        dog.join()
        if state["error"]:
            stops.append(f"the watchdog failed: {state['error']}")
        for e in running:
            try:
                if e["proc"].poll() is None:
                    e["timed_out"] = True
                    e["proc"].kill()
                e["proc"].wait()
                why = _settle(fp, e)
            except Exception as exc:  # noqa: BLE001 - every child is settled; the error stops
                why = f"{e['name']}: settlement failed: {exc!r}"
            if why:
                stops.append(why)
                _bind_stop(fp, why)
    return stops


def _todo(fp: str, items: list[dict]) -> list[dict]:
    return [
        i
        for i in items
        if not (OUT / fp / f"{_name(i)}.json").exists()
        and not (OUT / fp / f"{_name(i)}.timeout").exists()
    ]


def _gate(fp: str, n: int, child_limit: float) -> str | None:
    if _stop_paths():
        return "refused: a binding stop of (c3) is unresolved"
    if dt.datetime.now(driver.BRT) >= driver.PAUSE_AT:
        return "paused: 18 November, 20:00"
    ledger_a.check_caps(reserve_days=0.1, reserve_tokens=0)
    reserve = n * (child_limit + OVERHEAD_SECONDS) / 3600.0
    alloc = ledger_a._rows()[PART]["allocation_hours"]
    if _part_spent() + reserve > 1.5 * alloc or ledger_a.spent() + reserve > ledger_a.CAP_HOURS:
        return _bind_stop(fp, "the next batch could pass the part's or stage A's cap")
    return None


def _controlled(fn) -> str:
    before = ledger_a.v052_ledger_sha256()
    driver.check_controller_placement()
    _contain_self()  # the job's handle stays open until this controller exits
    try:
        ledger_a.declare()
        if _recover():
            return "stopped: attempts left open by an interrupted controller (charged, marked)"
        return fn()
    finally:
        if ledger_a.v052_ledger_sha256() != before:
            raise SystemExit("the v0.5.2 ledger changed: refused")


def _smoke_item(items: list[dict]) -> dict:
    files = json.loads(t.C2_FETCH.read_text("utf-8"))["files"]
    return max(items, key=lambda i: (len(files.get(i["key"]) or []), -items.index(i)))


def smoke() -> None:
    fp = fingerprint()

    def body() -> str:
        (OUT / fp / "attempts").mkdir(parents=True, exist_ok=True)
        accept = OUT / fp / "smoke-acceptance.json"
        if accept.exists():
            return f"already decided: {accept.read_text('utf-8')}"
        worst = _smoke_item(schedule())
        if (OUT / fp / f"{_name(worst)}.timeout").exists():
            return _bind_stop(fp, "the smoke's injection is a terminal unknown")
        why = _gate(fp, 1, SMOKE_SECONDS)
        if why:
            return why
        started = time.monotonic()
        stops = _batch(fp, [worst], SMOKE_SECONDS)
        wall = time.monotonic() - started
        ok = (
            not stops
            and wall <= SMOKE_SECONDS
            and (OUT / fp / f"{_name(worst)}.json").exists()
            and not (OUT / fp / f"{_name(worst)}.timeout").exists()
        )
        doc = {"fingerprint": fp, "injection": worst, "wall_seconds": wall, "accepted": ok}
        _atomic(accept, json.dumps(doc))
        if not ok:
            return _bind_stop(fp, f"the smoke did not finish cleanly within {SMOKE_SECONDS:.0f} s")
        return f"smoke accepted: {worst} in {wall:.0f} s"

    print(_controlled(body), flush=True)


def _checkpoint(fp: str, items: list[dict], checkpoint: int) -> str | None:
    """The checkpoint's decision, persisted once its injections are settled; reconstructed on a
    restart that finds the checkpoint's injections done without it."""
    path = OUT / fp / "checkpoint.json"
    if path.exists():
        return None
    settled = len(items) - len(_todo(fp, items))
    if settled < checkpoint:
        return None
    projection = _part_spent() / settled * len(items)
    alloc = ledger_a._rows()[PART]["allocation_hours"]
    doc = {
        "settled": settled,
        "projection_hours": projection,
        "allocation_hours": alloc,
        "passes": projection <= 1.5 * alloc,
    }
    _atomic(path, json.dumps(doc))
    if not doc["passes"]:
        return _bind_stop(fp, f"the checkpoint projects {projection:.1f} CPU-h, past 1.5 x {alloc}")
    return None


def run() -> None:
    fp = fingerprint()

    def body() -> str:
        accept = OUT / fp / "smoke-acceptance.json"
        if not accept.exists() or not json.loads(accept.read_text("utf-8"))["accepted"]:
            return "refused: no accepted smoke of this fingerprint"
        items = schedule()
        checkpoint = math.ceil(len(items) / 20)
        while True:
            why = _checkpoint(fp, items, checkpoint)
            if why:
                return why
            todo = _todo(fp, items)
            if not todo:
                return "complete"
            settled = len(items) - len(todo)
            w = driver.workers_for(dt.datetime.now(driver.BRT), len(CPUS))
            batch = todo[:w] if settled >= checkpoint else todo[: checkpoint - settled]
            why = _gate(fp, len(batch), CHILD_SECONDS)
            if why:
                return why
            stops = _batch(fp, batch, CHILD_SECONDS)
            if stops:
                return f"stopped: {'; '.join(stops)}"

    print(_controlled(body), flush=True)


def summarize() -> None:
    from collections import Counter

    fp = fingerprint()
    items = schedule()
    recs, unknown = [], []
    for i in items:
        path, marker = OUT / fp / f"{_name(i)}.json", OUT / fp / f"{_name(i)}.timeout"
        if marker.exists() or not path.exists():
            unknown.append({**i, "why": "timeout, interruption or not run"})
            continue
        r = json.loads(path.read_text("utf-8"))
        problems = []
        if r["status"] != "OK":
            problems.append(f"error: {r.get('reason')}")
        elif not r["candidate_matches_c2"]:
            problems.append("the final candidate differs from its C2 v0.4 record's")
        for c in (r.get("v4") or {}).get("a0_depth_calls", []):
            if "instrumentation_error" in c or "COPY DISAGREES" in (c.get("why") or ""):
                problems.append("a trace failed")
                break
        if problems:
            unknown.append({**i, "why": "; ".join(problems)})
        else:
            recs.append(r)
    blockers: Counter = Counter()
    for r in recs:
        if r["v4"]["stage_verdict"] in KEPT:
            continue
        for n in r["v4"]["stage_tests"]:
            v = (r["v4"]["tests"].get(n) or {}).get("final") or {}
            if v.get("status") == "INCONCLUSIVE" or (
                v.get("status") == "FAIL" and v.get("severity") != "warning"
            ):
                blockers[f"{n} {v['status']}"] += 1
    out = {
        "label": "T2a's stratum above 20 sectors with version 4 C; a measurement, decides "
        "nothing (#217, (c3))",
        "method_status": "not_validated",
        "fingerprint": fp,
        "sample": len(items),
        "measured": len(recs),
        "unknown": unknown,
        "v4C_kept": sum(r["v4"]["stage_verdict"] in KEPT for r in recs),
        "verdicts": dict(Counter(r["v4"]["stage_verdict"] for r in recs)),
        "blockers": dict(blockers),
        "cpu_hours": round(_part_spent(), 3),
        "records": recs,
    }
    _atomic(HERE / "above20.json", json.dumps(out, indent=1, sort_keys=True, default=str) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "records"}, indent=1, default=str))


if __name__ == "__main__":
    if sys.argv[1] == "one":
        one(sys.argv[2], int(sys.argv[3]), Path(sys.argv[4]), int(sys.argv[5]))
    else:
        {"smoke": smoke, "run": run, "summarize": summarize}[sys.argv[1]]()
