"""v0.5.3 stage A, item (a): which branch of A0 refuses, in every refusal of T2a's and D2's losses
(#217; `docs/plans/v0.5.3-stageA-design.md`, section (a)). **A diagnosis on development data; it
decides nothing.** ``method_status: not_validated``. No change to ``src/``, to any rule or to T2a's
fingerprint: v0.5.2's scripts are imported, never edited, and none of their writing entry points is
called; historical records are read through ``driver.Run(...).assemble()`` only.

**What runs.** T2a: the 51 development injections that version 4 B loses against v0.4 in the v0.5.2
diagnosis, rebuilt by ``forecast_t2a_diagnosis.one`` (the v0.4 battery and version 4 C, with its
trace of every ``a0_v4.a0_depth`` return). D2: the 28 development planets that version 4 loses
against v0.4 in ``forecast-v4.json``, rebuilt as ``forecast_v4.one`` does (C1's generator and
development seed; the v0.4 battery and version 4 at stage 2; version 3 not run), with the same trace
of ``a0_v4.a0_depth``. In version 4, every call of these is traced, the original's result returned
unchanged:

- ``a0.group_variance``: on a none, ``_gv_branch`` (a step-by-step copy, run only on a none) names
  the first refusing branch: a lag correlation with fewer than ``MIN_PAIRS`` window pairs; enough
  pairs but a degenerate (zero-variance) Pearson correlation; a covariance that is not positive
  semi-definite; a variance that is not positive. Every correlation it used is kept.
- ``a0_v4.empirical_events``: the epochs in and out, and for each dropped event its reason (no
  coverage stratum; or its sector and stratum's empirical error refused, with ``n``, ``n_eff`` and
  the lag correlations).

Calls made by the diagnostic copy ``forecast_t2a_diagnosis._why_none`` (a replay on an A0 none) are
tagged ``replay`` and never counted as the battery's. A record is quarantined, not classified, if
any trace failed or a copy disagreed, or if it does not reproduce its v0.5.2 record: for T2a the
candidate, every version 4 test's status and message and the stage verdict; for D2 both verdicts
and every version 4 test's status and class.

Usage: ``run`` through ``scripts/launch_affinity.ps1``, then ``summarize`` (``a0-refusals.json``).
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ledger_a  # noqa: E402,I001  (before budgeted: it points the ledger at stage A's)
import budgeted  # noqa: E402
import driver  # noqa: E402
import forecast_t2a as t  # noqa: E402
import forecast_t2a_diagnosis as td  # noqa: E402
import forecast_v4 as fv  # noqa: E402

PART = "a_refusals"
OUT = ledger_a.ROOT / ".cache/v053/stageA/a0-refusals"
# Amendment 1 (2026-11-11, #217): the first attempt stopped by the frozen-projection rule (1.5 times
# the 5 % checkpoint's 1.34 CPU-h) at 2.20 CPU-h, within its 4 CPU-h allocation, with 72 of the 79
# records done; the stop is reconciled with that reason and the 7 missing records run as their own
# part, from 0.5 CPU-h transferred from the reserve; the summary joins both, each shard checked by
# its sidecar.
MAIN_FP = "c24c94200bee49dd"  # the first attempt's fingerprint: this script and ledger_a.py at
# commit adc3f95 (recomputed from those committed files); the amendment only adds code
REST_FP = "d8e3e9b34e0c7aa0"  # the rest part's fingerprint when it ran (this script before the
# summary's fix for D2 records; the code that builds a record did not change)
PART_REST = "a_refusals_rest"
OUT_REST = ledger_a.ROOT / ".cache/v053/stageA/a0-refusals-rest"
REST_HOURS = 0.5
RECONCILE = (
    "The 5 % checkpoint (4 of 79 records) projected 1.34 CPU-h, below the records' real cost (T2a "
    "median 96 CPU-seconds with the traces); the part spent 2.20 of its 4.0 CPU-h allocation and "
    "did 72 of 79 records. The 7 missing ones run as part a_refusals_rest (0.5 CPU-h from the "
    "reserve, prospective; #217), and this attempt's consumption stays counted."
)
WORKERS = 12
PIN = tuple(range(8, 32, 2))
MAX_SHARD_SECONDS = 1200.0
KEPT = ("SURVIVED", "WEAKENED")
_STATE = {"replay": 0}


# --- the v0.5.2 records, read without any ledger ----------------------------------------------


def _assemble(out: Path, fn, shards, fp, **kwargs) -> list[dict]:
    data = driver.Run(out / fp, fn, shards, fp, 1.0, 1, **kwargs).assemble()
    return [json.loads(x) for x in data.decode().splitlines() if x.strip()]


def t2a_old() -> dict:
    recs = _assemble(td.OUT, td.shard, t.shards(), td.fingerprint(), pin=t.PIN,
                     max_shard_seconds=t.MAX_SHARD_SECONDS)  # fmt: skip
    return {(r["key"], r["slot"]): r for r in recs}


def d2_old() -> dict:
    recs = _assemble(fv.OUT, fv.shard, fv.shards(), fv.fingerprint(), pin=fv.PIN,
                     max_shard_seconds=fv.MAX_SHARD_SECONDS)  # fmt: skip
    return {r["index"]: r for r in recs}


def schedule() -> list:
    t_old = t2a_old()
    rows = [
        (f"t-{k}-{s:02d}", {"kind": "t2a", "key": k, "slot": s, "stratum": r["stratum"]})
        for (k, s), r in sorted(t_old.items())
        if r.get("status") == "OK" and r["v04"]["stage_verdict"] in KEPT
        and r["v4"]["stage_verdict"] not in KEPT
    ]  # fmt: skip
    d_old = d2_old()
    rows += [
        (f"d-{i:05d}", {"kind": "d2", "index": i})
        for i, r in sorted(d_old.items())
        if r.get("status") == "OK" and r["gate_passed"] and r["identity"]
        and r["v04"] in KEPT and r["v4"] not in KEPT
    ]  # fmt: skip
    counts = (sum(a["kind"] == "t2a" for _, a in rows), sum(a["kind"] == "d2" for _, a in rows))
    if counts != (51, 28):
        raise SystemExit(f"the schedule is not the 51 T2a and 28 D2 losses: {counts}")
    return rows


# --- the traces -------------------------------------------------------------------------------


def _gv_branch(weights, sigmas, events, windows, h, pooled) -> dict:
    """Why ``a0.group_variance`` returned None: its steps, in its order (``a0.py``)."""
    from refute.packs.tess import a0

    n = len(weights)
    cov = np.zeros((n, n))
    cache: dict = {}

    def used() -> list:
        return [
            {"key": [k[0], k[1], k[2], k[3]], "r": None if v[0] is None else float(v[0]),
             "pairs": int(v[1])} for k, v in cache.items()
        ]  # fmt: skip

    for i in range(n):
        cov[i, i] = sigmas[i] ** 2
        for j in range(i + 1, n):
            ei, ej = events[i], events[j]
            if ei.centre > ej.centre:
                ei, ej = ej, ei
            if ei.sector != ej.sector or ei.segment != ej.segment:
                continue
            k = int(round(abs(ej.centre - ei.centre) / (2.0 * h)))
            if k < 1 or k > a0.MAX_LAG:
                continue
            sub = [w for w in windows if w.sector == ei.sector]
            key = (ei.sector, k, None, None) if pooled.get(ei.sector) else (
                ei.sector, k, ei.stratum, ej.stratum)  # fmt: skip
            if key not in cache:
                cache[key] = a0.lag_correlation(sub, k, key[2], key[3])
            r, pairs = cache[key]
            if r is None:
                return {
                    "branch": "lag correlation below MIN_PAIRS" if pairs < a0.MIN_PAIRS
                    else "degenerate lag correlation (enough pairs, zero variance)",
                    "sector": int(ei.sector), "segment": int(ei.segment), "lag": k,
                    "strata": [key[2], key[3]], "pooled": bool(pooled.get(ei.sector)),
                    "pairs": int(pairs), "min_pairs": a0.MIN_PAIRS,
                    "windows_in_sector": len(sub),
                    "windows_by_stratum": dict(Counter(w.stratum for w in sub)),
                    "correlations_used": used(),
                }  # fmt: skip
            cov[i, j] = cov[j, i] = sigmas[i] * sigmas[j] * r
    eig = np.linalg.eigvalsh(cov)
    if eig.min() < -1e-12 * max(eig.max(), 0.0):
        return {
            "branch": "covariance not positive semi-definite",
            "min_eigenvalue": float(eig.min()),
            "max_eigenvalue": float(eig.max()),
            "correlations_used": used(),
        }
    w = np.asarray(weights, dtype=float)
    var = float(w @ cov @ w)
    if not var > 0:
        return {"branch": "variance not positive", "variance": var, "correlations_used": used()}
    return {"branch": "COPY DISAGREES"}


def _traced_gv(original, calls: list):
    def group_variance(weights, sigmas, events, windows, h, pooled):
        got = original(weights, sigmas, events, windows, h, pooled)
        row = {
            "caller": sys._getframe(1).f_code.co_name,
            "replay": _STATE["replay"] > 0,
            "events": len(weights),
            "event_sectors": sorted({int(e.sector) for e in events}),
            "event_strata": dict(Counter(e.stratum for e in events)),
            "refused": got is None,
        }
        if got is None:
            try:
                row.update(_gv_branch(weights, sigmas, events, windows, h, pooled))
            except Exception as exc:  # noqa: BLE001 - recorded apart; the result stands
                row["instrumentation_error"] = repr(exc)
        calls.append(row)
        return got

    return group_variance


def _traced_events(original, calls: list):
    def empirical_events(flat, candidate, events, event_params, cadence_days, measure,
                         exclude_phase_half=False):  # fmt: skip
        got = original(flat, candidate, events, event_params, cadence_days, measure,
                       exclude_phase_half)  # fmt: skip
        try:
            from refute.packs.tess import a0

            out, _, details = got
            kept = {int(e) for e in out.epochs}
            expected_in = candidate.duration / cadence_days
            dropped = []
            for i, centre in enumerate(events.centers):
                epoch = int(events.epochs[i])
                if epoch in kept:
                    continue
                st = a0.stratum(events.n_in[i] / expected_in, event_params.min_coverage)
                sec = int(a0.sector_of(flat.time, flat.sector, centre))
                reason = "no coverage stratum" if st is None else "empirical error refused"
                info = details.get(f"{sec}:{st}") if st is not None else None
                dropped.append({"epoch": epoch, "sector": sec, "stratum": st, "reason": reason,
                                "n": (info or {}).get("n"), "n_eff": (info or {}).get("n_eff"),
                                "r_k": (info or {}).get("r_k")})  # fmt: skip
            calls.append({
                "caller": sys._getframe(1).f_code.co_name, "replay": _STATE["replay"] > 0,
                "epochs_in": [int(e) for e in events.epochs], "epochs_out": sorted(kept),
                "dropped": dropped,
            })  # fmt: skip
        except Exception as exc:  # noqa: BLE001 - recorded apart; the result stands
            calls.append({"instrumentation_error": repr(exc), "replay": _STATE["replay"] > 0})
        return got

    return empirical_events


def _replay_tagged(original):
    def why_none(*args, **kwargs):
        _STATE["replay"] += 1
        try:
            return original(*args, **kwargs)
        finally:
            _STATE["replay"] -= 1

    return why_none


def _with_trace(fn, depth_calls: list | None = None):
    """Run ``fn`` with the traces installed; ``depth_calls``, when given, also traces
    ``a0_v4.a0_depth`` with ``forecast_t2a_diagnosis``'s tracer (D2; T2a's ``one`` traces it)."""
    from refute.packs.tess import a0, a0_v4

    calls: list = []
    events: list = []
    saved = (a0.group_variance, a0_v4.empirical_events, td._why_none, a0_v4.a0_depth)
    a0.group_variance = _traced_gv(saved[0], calls)
    a0_v4.empirical_events = _traced_events(saved[1], events)
    td._why_none = _replay_tagged(saved[2])
    if depth_calls is not None:
        a0_v4.a0_depth = td._tracer(saved[3], depth_calls)
    try:
        out = fn()
    finally:
        a0.group_variance, a0_v4.empirical_events, td._why_none, a0_v4.a0_depth = saved
    return out, calls, events


# --- one record -----------------------------------------------------------------------------


def _d2_one(i: int, rec: dict) -> None:
    """``forecast_v4.one`` without version 3, with version 4 traced."""
    from refute.packs.tess.calib05 import c1
    from refute.packs.tess.detrend import detrend
    from refute.packs.tess.discover.paired import _outcome as paired_outcome
    from refute.packs.tess.pipeline import attack_candidate, global_prewhitening
    from refute.packs.tess.search import search_period

    data, truth = c1.generate("P", c1.development_seed("P", i))
    p04, _, p4 = fv.plans()
    flat = detrend(data.lc, p04.detrend)
    pw, searched = global_prewhitening(data, p04, flat)
    cand = search_period(searched, p04.search).candidate
    v04 = paired_outcome(data, cand, p04, 2, None, None, pw)
    rec["v04"] = v04["verdict"]
    rec["a0_depth_calls"] = []
    g, calls, events = _with_trace(
        lambda: attack_candidate(data, cand, p4, None, None, pw), rec["a0_depth_calls"]
    )
    rec["group_variance_calls"], rec["empirical_events_calls"] = calls, events
    rec["v4"], rec["v4_tests"] = fv._verdict(g.tests, p4)
    rec["selection"] = next(
        ({k: sel.get(k) for k in ("original", "eligible_events", "chosen", "contributing",
                                  "refused")}
         for tr in g.tests if (sel := tr.metrics.get("sector_selection"))), None)  # fmt: skip
    rec["messages"] = {tr.name: tr.message for tr in g.tests}


def shard(arg: dict) -> bytes:
    started = time.process_time()
    rec: dict = dict(arg)
    try:
        if arg["kind"] == "t2a":
            inner: dict = {}
            try:
                _, calls, events = _with_trace(lambda: td.one(arg, inner))
            finally:
                rec.update(inner)
            rec["group_variance_calls"], rec["empirical_events_calls"] = calls, events
        else:
            _d2_one(arg["index"], rec)
        rec["status"] = "OK"
    except Exception as exc:  # noqa: BLE001 - recorded, never dropped
        rec["status"], rec["reason"] = "ERROR", repr(exc)
    rec["cpu_seconds"] = time.process_time() - started
    return json.dumps(rec, sort_keys=True, default=str).encode() + b"\n"


def fingerprint() -> str:
    from refute.core.codehash import compute_code_hash

    h = hashlib.sha256(compute_code_hash().sha256.encode())
    for path in (
        Path(__file__),
        HERE / "ledger_a.py",
        td.HERE / "forecast_t2a_diagnosis.py",
        td.HERE / "forecast_t2a.py",
        td.HERE / "forecast_v4.py",
        td.HERE / "t2a-fetch.json",
        td.HERE / "budgeted.py",
        td.HERE / "driver.py",
    ):
        h.update(hashlib.sha256(path.read_bytes()).digest())
    return h.hexdigest()[:16]


def run() -> None:
    before = ledger_a.v052_ledger_sha256()
    try:
        ledger_a.check_caps(reserve_days=0.3, reserve_tokens=0)
        ledger_a.declare()
        fp = fingerprint()
        rows = schedule()
        cap = ledger_a.hard_cap(PART, WORKERS, MAX_SHARD_SECONDS)
        print("hard cap", round(cap, 2), "CPU-h", flush=True)
        state = budgeted.execute(
            ledger_a.SECTION, PART, OUT / fp, shard, rows, fp, WORKERS, pin=PIN,
            max_shard_seconds=MAX_SHARD_SECONDS, hard_cap_hours=cap,
        )  # fmt: skip
        print(state, flush=True)
    finally:
        if ledger_a.v052_ledger_sha256() != before:
            raise SystemExit("the v0.5.2 ledger changed: refused")
    if state != "complete":
        raise SystemExit(state)


def _main_done(rows: list) -> dict:
    """The first attempt's finished records, each checked by its sidecar (``driver.Run._done``:
    the fingerprint, the argument and the bytes)."""
    r = driver.Run(OUT / MAIN_FP, shard, rows, MAIN_FP, 1.0, 1, pin=PIN,
                   max_shard_seconds=MAX_SHARD_SECONDS)  # fmt: skip
    return {sid: r._paths(sid)[0].read_bytes() for sid in r._done()}


def run_rest() -> None:
    """Amendment 1: reconcile the first attempt's stop and run its missing records."""
    before = ledger_a.v052_ledger_sha256()
    try:
        ledger_a.check_caps(reserve_days=0.1, reserve_tokens=0)
        rows_book = ledger_a._rows()
        if "unresolved_stop" in rows_book.get(PART, {}):
            budgeted.reconcile(ledger_a.SECTION, PART, RECONCILE)
        if PART_REST not in ledger_a._rows():
            ledger_a.transfer("reserve", PART_REST, REST_HOURS, RECONCILE)
        fp = fingerprint()
        rows = schedule()
        done = _main_done(rows)
        rest = [(sid, a) for sid, a in rows if sid not in done]
        cap = ledger_a.hard_cap(PART_REST, WORKERS, MAX_SHARD_SECONDS)
        print(len(rest), "records; hard cap", round(cap, 2), "CPU-h", flush=True)
        state = budgeted.execute(
            ledger_a.SECTION, PART_REST, OUT_REST / fp, shard, rest, fp, WORKERS, pin=PIN,
            max_shard_seconds=MAX_SHARD_SECONDS, hard_cap_hours=cap,
        )  # fmt: skip
        print(state, flush=True)
    finally:
        if ledger_a.v052_ledger_sha256() != before:
            raise SystemExit("the v0.5.2 ledger changed: refused")
    if state != "complete":
        raise SystemExit(state)


# --- the summary -----------------------------------------------------------------------------


def _trace_failures(rec: dict) -> list[str]:
    why = []
    v4 = rec.get("v4")
    depth = rec.get("a0_depth_calls") or (v4.get("a0_depth_calls") if isinstance(v4, dict) else [])
    depth = depth or []
    for c in rec.get("group_variance_calls") or []:
        if "instrumentation_error" in c or c.get("branch") == "COPY DISAGREES":
            why.append("group variance trace")
    for c in rec.get("empirical_events_calls") or []:
        if "instrumentation_error" in c:
            why.append("empirical events trace")
    for c in depth:
        if "instrumentation_error" in c or "COPY DISAGREES" in (c.get("why") or ""):
            why.append("a0_depth trace")
    return sorted(set(why))


def _quarantine_t2a(rec: dict, old: dict) -> list[str]:
    why = []
    if rec.get("compat_problems"):
        why.append("the v0.4 record does not reproduce")
    if old["v4"].get("candidate") != rec["v4"].get("candidate"):
        why.append("the candidate differs from the v0.5.2 diagnosis record")
    for field in ("status", "message"):
        o = {k: v["final"][field] for k, v in old["v4"]["tests"].items() if "final" in v}
        n = {k: v["final"][field] for k, v in rec["v4"]["tests"].items() if "final" in v}
        if o != n:
            why.append(f"a test {field} differs from the v0.5.2 diagnosis record")
    if old["v4"]["stage_verdict"] != rec["v4"]["stage_verdict"]:
        why.append("the stage verdict differs from the v0.5.2 diagnosis record")
    return why


def _quarantine_d2(rec: dict, old: dict) -> list[str]:
    why = []
    if old["v04"] != rec["v04"] or old["v4"] != rec["v4"]:
        why.append("a verdict differs from forecast-v4's record")
    for field in ("status", "class"):
        o = {k: v.get(field) for k, v in old["v4_tests"].items()}
        n = {k: v.get(field) for k, v in rec["v4_tests"].items()}
        if o != n:
            why.append(f"a test {field} differs from forecast-v4's record")
    return why


def summarize() -> None:
    fp = fingerprint()
    rows = schedule()
    done = _main_done(rows)
    rest = [(sid, a) for sid, a in rows if sid not in done]
    data = b"".join(done.values())
    if rest:
        data += budgeted.assembled(
            ledger_a.SECTION, PART_REST, OUT_REST / REST_FP, shard, rest, REST_FP, WORKERS,
            pin=PIN, max_shard_seconds=MAX_SHARD_SECONDS,
        )  # fmt: skip
    recs = [json.loads(x) for x in data.decode().splitlines() if x.strip()]
    if len(recs) != len(rows):
        raise SystemExit(f"{len(recs)} records assembled of {len(rows)}")
    t_old, d_old = t2a_old(), d2_old()
    out: dict = {
        "label": "which branch of A0 refuses in T2a's and D2's losses; a diagnosis, decides "
        "nothing (#217, stage A (a))",
        "method_status": "not_validated",
        "fingerprint": fp,
        "records": len(recs),
        "errors": [f"{r.get('key', r.get('index'))}: {r.get('reason')}" for r in recs
                   if r["status"] != "OK"],
        "quarantined": {},
    }  # fmt: skip
    branches: Counter = Counter()
    drops: Counter = Counter()
    per_record = []
    for r in recs:
        if r["status"] != "OK":
            continue
        rid = f"{r['key']}/{r['slot']}" if r["kind"] == "t2a" else f"D2 {r['index']}"
        old = t_old[(r["key"], r["slot"])] if r["kind"] == "t2a" else d_old[r["index"]]
        q = (_quarantine_t2a if r["kind"] == "t2a" else _quarantine_d2)(r, old)
        q += _trace_failures(r)
        if q:
            out["quarantined"][rid] = q
            continue
        refusals = [c for c in r["group_variance_calls"] if c["refused"] and not c["replay"]]
        for c in refusals:
            branches[f"{r['kind']}: {c['caller']}: {c['branch']}"] += 1
        for c in r["empirical_events_calls"]:
            if not c.get("replay"):
                for d in c.get("dropped", []):
                    drops[f"{r['kind']}: {c['caller']}: {d['reason']}"] += 1
        if r["kind"] == "t2a":
            sel = next((((v.get("final") or {}).get("metrics") or {}).get("sector_selection")
                        for v in r["v4"]["tests"].values()
                        if ((v.get("final") or {}).get("metrics") or {}).get("sector_selection")),
                       None)  # fmt: skip
            msgs = {k: v["final"]["message"] for k, v in r["v4"]["tests"].items()
                    if (v.get("final") or {}).get("status") == "INCONCLUSIVE"}  # fmt: skip
            depth = r["v4"].get("a0_depth_calls", [])
        else:
            sel = r.get("selection")
            msgs = {k: r["messages"].get(k) for k, v in r["v4_tests"].items()
                    if v["status"] == "INCONCLUSIVE"}  # fmt: skip
            depth = r.get("a0_depth_calls", [])
        per_record.append({
            "record": rid, "selection": sel, "inconclusive_messages": msgs,
            "group_variance_refusals": refusals,
            "a0_depth_nones": [{k: c.get(k) for k in ("caller", "series", "why", "sectors")}
                               for c in depth if c.get("result") is None],
            "dropped_events": [d for c in r["empirical_events_calls"] if not c.get("replay")
                               for d in c.get("dropped", [])],
        })  # fmt: skip
    out["group_variance_branches"] = dict(sorted(branches.items()))
    out["dropped_event_reasons"] = dict(sorted(drops.items()))
    out["per_record"] = per_record
    out["cpu_hours"] = round(sum(float(r.get("cpu_seconds", 0)) for r in recs) / 3600, 3)
    (HERE / "a0-refusals.json").write_text(
        json.dumps(out, indent=1, sort_keys=True, default=str) + "\n", "utf-8"
    )
    print(json.dumps({k: v for k, v in out.items() if k != "per_record"}, indent=1))


if __name__ == "__main__":
    {"run": run, "run_rest": run_rest, "summarize": summarize}[sys.argv[1]]()
