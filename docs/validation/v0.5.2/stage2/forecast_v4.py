"""v0.5.2 stage 2: a development forecast of D2 and D4 with battery version 4, paired with the v0.4
compatibility battery and version 3 on the same curves (the maintainer's decision of 2026-11-09,
#216, item 2). **A forecast; it decides nothing.** Development data only; ``method_status:
not_validated``.

**The curves.** C1's generator, family P, development seeds ``c1.development_seed("P", i)`` for
``i`` in ``FIRST`` to ``FIRST + N - 1`` (v0.5.1's forecast used 0 to 99, so these planets are
new). The candidate generation is shared (``paired.paired_chain`` of the v0.4 plan, stage 2, no
catalogs); each battery then attacks the same candidate: the v0.4 battery, version 3
(``calib051.plans.pair``) and version 4 (the version-3 plan with discovery version 4 and the
``v052`` section at its defaults: the sinusoid's FAIL allowed, the sector selector not
certified). Each record keeps every test's status and, for version 4, why an A0-dependent test
is undecided (the sector rule, the comb's measured events) and the sinusoid's own status, so
that the loss of measurable curves can be traced to its cause on planets.

**The targets' minimums** (``docs/plans/v0.5.1-plan.md``, unchanged): D2, kept (SURVIVED or
WEAKENED) over eligible at least the v0.4 value minus 0.10, REFUTED over eligible at most 0.05
with its upper bound at most 0.10; D4, INCONCLUSIVE over the subset of target SNR at least 15 at
most 0.30. Eligible: the gate passed and the candidate matches the truth (``c1.identity``).

T2a is not run here: its curves are real hosts (v0.5's C2), which are not cached; the summary
reads what the sector rule implies for them from the C2 records (``t2a_sector_reading``).

Usage: ``scripts/launch_affinity.ps1 -Script <this file> -Arguments run -Log
.cache/v052/s2/forecast-v4``; then ``.venv/Scripts/python.exe <this file> summarize`` writes
``forecast-v4.json``.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))
import budgeted  # noqa: E402

LABEL = "refute-v052-dev:forecast-v4"
OUT = ROOT / ".cache/v052/s2/forecast-v4"
FIRST = 1000
N = 200
PER_SHARD = 2
WORKERS = 12
PIN = tuple(range(8, 32, 2))
SECTION, PART = "remaining_work_packages", "forecast_d2_d4"
ALLOCATION_HOURS = 15.0
C2_RECORDS = ROOT / ".cache/v05/calibration/c2/records.jsonl"
A0_TESTS = ("odd_even", "aperture_depth", "systematics", "single_event", "event_consistency")
KEPT = ("SURVIVED", "WEAKENED")


def plans():
    from refute.packs.tess.calib05.steps import v04_test_plan
    from refute.packs.tess.calib051.plans import pair, v051_plan
    from refute.packs.tess.params import TessTestPlan

    raw = v04_test_plan(ROOT)
    p04, p3 = pair(raw)
    d4 = v051_plan(raw)
    d4["discovery"]["version"] = 4
    d4["v052"] = {}
    p4 = TessTestPlan.model_validate(d4)
    if not p4.is_v052:
        raise SystemExit("the version-4 plan is not version 4")
    return p04, p3, p4


def _verdict(tests, plan) -> tuple[str, dict]:
    from refute.core.sensitivity import enforce_sensitivity
    from refute.core.verdict import aggregate, defer_tests, enforce_coverage
    from refute.packs.tess.pipeline import expected_by_role
    from refute.packs.tess.power import registry_for

    tests = enforce_sensitivity(enforce_coverage(list(tests)), registry_for(plan))
    tests, _ = defer_tests(tests, dict(plan.discovery.stages), 2)
    decisive, _ = expected_by_role(plan, False)
    verdict, _ = aggregate([t for t in tests if t.name in decisive], expected=decisive)
    detail = {}
    for t in tests:
        row = {"status": t.status.value}
        cls = t.metrics.get("inconclusive_class")
        if cls:
            row["class"] = cls
        sel = t.metrics.get("sector_selection")
        if sel:
            row["refused"] = sel.get("refused")
            row["contributing"] = len(sel.get("contributing") or [])
        detail[t.name] = row
    return verdict.value, detail


def one(i: int) -> dict:
    from refute.packs.tess.calib05 import c1
    from refute.packs.tess.detrend import detrend
    from refute.packs.tess.discover.paired import _outcome as paired_outcome
    from refute.packs.tess.pipeline import attack_candidate, global_prewhitening
    from refute.packs.tess.search import search_period

    started = time.process_time()
    rec: dict = {"index": i}
    try:
        data, truth = c1.generate("P", c1.development_seed("P", i))
    except c1.GenerationFailedError as exc:
        return {**rec, "status": "GENERATION_FAILURE", "reason": str(exc)}
    rec["target_snr"] = truth["target_snr"]
    p04, p3, p4 = plans()
    flat = detrend(data.lc, p04.detrend)
    pw, searched = global_prewhitening(data, p04, flat)
    cand = search_period(searched, p04.search).candidate
    v04 = paired_outcome(data, cand, p04, 2, None, None, pw)
    rec["gate_passed"] = v04["gate_passed"]
    rec["identity"] = c1.identity(truth, v04["candidate"])
    rec["v04"] = v04["verdict"]
    rec["sectors"] = len(set(data.lc.sector.tolist()))
    for name, plan in (("v3", p3), ("v4", p4)):
        g = attack_candidate(data, cand, plan, None, None, pw)
        rec[name], rec[f"{name}_tests"] = _verdict(g.tests, plan)
    rec["status"] = "OK"
    rec["cpu_seconds"] = time.process_time() - started
    return rec


def shard(start: int) -> bytes:
    lines = []
    for i in range(start, start + PER_SHARD):
        try:
            rec = one(i)
        except Exception as exc:  # noqa: BLE001 - recorded, never dropped
            rec = {"index": i, "status": "ERROR", "reason": repr(exc)}
        lines.append(json.dumps(rec, sort_keys=True))
    return ("\n".join(lines) + "\n").encode()


def shards() -> list:
    return [(f"f{i:05d}", i) for i in range(FIRST, FIRST + N, PER_SHARD)]


def fingerprint() -> str:
    from refute.core.codehash import compute_code_hash

    h = hashlib.sha256(compute_code_hash().sha256.encode())
    h.update(hashlib.sha256(Path(__file__).read_bytes()).digest())
    return h.hexdigest()[:16]


def run() -> None:
    fp = fingerprint()
    budgeted.declare(SECTION, {PART: ALLOCATION_HOURS})
    state = budgeted.execute(
        SECTION, PART, OUT / fp, shard, shards(), fp, WORKERS, pin=PIN, max_shard_seconds=1800.0
    )
    print(state, flush=True)
    if state != "complete":
        raise SystemExit(state)


def _rate(k: int, n: int) -> dict:
    from scipy import stats

    high = float(stats.beta.ppf(0.95, k + 1, n - k)) if k < n else 1.0
    return {"count": k, "of": n, "fraction": k / n if n else None, "upper_95": high}


def t2a_sector_reading() -> dict:
    """What the sector rule implies for T2a's real hosts: with the selector not certified, a
    target whose measured events fall in five or more sectors is INCONCLUSIVE in every
    A0-dependent test. Read from the v0.5 C2 records (the sectors of each host's light curve)."""
    if not C2_RECORDS.exists():
        return {"state": "the v0.5 C2 records are not available"}
    counts: Counter = Counter()
    for line in C2_RECORDS.read_text("utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("kind") != "original":
            continue
        n = r.get("n_sectors") or len(r.get("sectors") or [])
        counts["5_or_more" if n >= 5 else "2_to_4" if n >= 2 else "unknown_or_1"] += 1
    return {"hosts_by_sector_count": dict(counts)}


def summarize() -> None:
    fp = fingerprint()
    data = budgeted.assembled(
        SECTION, PART, OUT / fp, shard, shards(), fp, WORKERS, pin=PIN, max_shard_seconds=1800.0
    )
    recs = [json.loads(x) for x in data.decode().splitlines() if x.strip()]
    ok = [r for r in recs if r.get("status") == "OK"]
    eligible = [r for r in ok if r["gate_passed"] and r["identity"]]
    subset = [r for r in eligible if r["target_snr"] >= 15.0]
    n, m = len(eligible), len(subset)
    out: dict = {
        "label": "forecast, decides nothing (#216, item 2): D2 and D4 with battery version 4",
        "method_status": "not_validated",
        "seeds": f"c1.development_seed('P', i), i = {FIRST} to {FIRST + N - 1}",
        "curves": len(recs),
        "errors": sum(r.get("status") == "ERROR" for r in recs),
        "generation_failures": sum(r.get("status") == "GENERATION_FAILURE" for r in recs),
        "eligible": n,
        "d4_subset": m,
        "sectors": dict(Counter(str(r["sectors"]) for r in eligible)),
        "batteries": {},
    }
    v04_kept = sum(r["v04"] in KEPT for r in eligible)
    for b in ("v04", "v3", "v4"):
        kept = sum(r[b] in KEPT for r in eligible)
        refuted = sum(r[b] == "REFUTED" for r in eligible)
        inconclusive = sum(r[b] == "INCONCLUSIVE" for r in subset)
        block = {
            "verdicts": dict(Counter(r[b] for r in eligible)),
            "D2_kept": _rate(kept, n),
            "D2_refuted": _rate(refuted, n),
            "D4_inconclusive": _rate(inconclusive, m),
        }
        if b != "v04":
            block["D2_kept_minimum"] = (v04_kept / n - 0.10) if n else None
            block["D2_kept_meets"] = bool(n) and kept / n >= v04_kept / n - 0.10
            block["D2_refuted_meets"] = (
                bool(n) and refuted / n <= 0.05 and (block["D2_refuted"]["upper_95"] <= 0.10)
            )
            block["D4_meets"] = bool(m) and inconclusive / m <= 0.30
            tests = {}
            for t in (*A0_TESTS, "sinusoid"):
                tests[t] = dict(Counter(r[f"{b}_tests"].get(t, {}).get("status") for r in eligible))
            block["tests"] = tests
        out["batteries"][b] = block
    # the loss of measurable curves on planets: why version 4 leaves an A0 test undecided
    why: Counter = Counter()
    for r in eligible:
        oe = r["v4_tests"].get("odd_even", {})
        if oe.get("status") != "INCONCLUSIVE":
            continue
        refused = oe.get("refused")
        if refused and "outside the grid" in refused:
            why["comb: measured events in a sector count outside 2 to 4"] += 1
        elif refused:
            why[f"sector selection: {refused}"] += 1
        else:
            why["odd_even undecided on its measured events"] += 1
    out["v4_odd_even_inconclusive_causes"] = dict(why)
    out["v4_sinusoid_inconclusive"] = sum(
        r["v4_tests"].get("sinusoid", {}).get("status") == "INCONCLUSIVE" for r in eligible
    )
    out["v4_verdict_changes_from_v3"] = dict(
        Counter(f"{r['v3']} -> {r['v4']}" for r in eligible if r["v3"] != r["v4"])
    )
    out["T2a"] = {
        "state": "not run: real hosts, not cached",
        "sector_rule_reading": t2a_sector_reading(),
    }
    out["cpu_hours"] = round(sum(float(r.get("cpu_seconds", 0.0)) for r in recs) / 3600.0, 3)
    (HERE / "forecast-v4.json").write_text(
        json.dumps(out, indent=1, sort_keys=True) + "\n", "utf-8"
    )
    print(json.dumps(out, indent=1, sort_keys=True))


if __name__ == "__main__":
    {"run": run, "summarize": summarize}[sys.argv[1]]()
