"""Item 3 (b) of the maintainer's decision of 2026-11-08 (#208): a **development forecast** of D2,
D4 and T2a with the acceptance's rule applied. It decides nothing. Development data only.
``method_status: not_validated``.

**D2, D4.** C1's generator, family P, development seeds ``c1.development_seed("P", i)`` for ``i``
in 0 to 99 (the seeds of ``sap_rule_effect.py``); the v0.4 compatibility battery and the
version-3 battery on the shared candidate, as ``discover.paired.paired_chain`` (stage 2, no
catalogs), the plans of ``calib051.plans.pair``. The chain runs once per curve. Then each reading
of the rule is applied to the tests that rely on A0's errors, with the run-time cells of
``strata.json`` (coverage stratum; for a group statistic, the lowest coverage stratum of the
measured events and the number of sectors holding them, as A0's rows define the group stratum):

- ``as_built``: no rule (the battery as it stands);
- ``strict``, ``ignoring_nd``, ``white_only``: the three readings of ``strata.py`` (the third
  supposes the noise model known and white); a decisive test whose cell is not accepted becomes
  INCONCLUSIVE, whatever it returned (acceptance, A0: "never decisive on an uncalibrated error");
- ``a0_tests_outside``: the decisive tests relying on A0 are left out of the verdict altogether
  (not the acceptance's reading: it shows what the rest of the battery does).

A0's errors at the decisive level: ``odd_even`` (``matched_diff``), ``aperture_depth``
(``large_minus_core``), ``systematics`` (``sap_minus_expected``). ``single_event`` and
``event_consistency`` are diagnostic in the plan until WP2 is accepted. A0's cell for
``aperture_depth`` and ``systematics`` is taken from the flattened target's events (their own
series have the same cadences).

**T2a.** The v0.5 C2 records (development); the curves are not cached. Where the rule leaves no
accepted cell for a statistic the value is fixed by the rule whatever the curves are; elsewhere
only an upper bound comes from the v0.5 statuses of the tests outside A0 (not the version-3
ones), and it is labelled so.

Usage (heavy; from the project root): ``scripts/launch_affinity.ps1 -Script
docs/validation/v0.5.1/feasibility/strategy/forecast_rule.py -Arguments 'run[,<max units>]'
-Log .cache/v051/item3/forecast``; then ``.venv/Scripts/python.exe <this file> summarize``
writes ``forecast-rule.json``.
"""

from __future__ import annotations

import json
import sys
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
OUT = ROOT / ".cache/v051/item3/forecast"
RECORDS = OUT / "records.jsonl"
C2_RECORDS = ROOT / ".cache/v05/calibration/c2/records.jsonl"
N = 100
SCENARIOS = ("as_built", "strict", "ignoring_nd", "white_only", "a0_tests_outside")
CELL_READING = {
    "strict": "strict",
    "ignoring_nd": "ignoring_nd",
    "white_only": "white_only_ignoring_nd",
}
STAT = {
    "odd_even": "matched_diff",
    "aperture_depth": "large_minus_core",
    "systematics": "sap_minus_expected",
}
A0_DIAGNOSTIC = ("single_event", "event_consistency")
ORDER = ("full", "partial", "minimal")
VERDICTS = ("SURVIVED", "WEAKENED", "REFUTED", "INCONCLUSIVE")


def _cells():
    doc = json.loads((HERE / "strata.json").read_text("utf-8"))
    return doc["runtime_cells"]


def _group_accepted(cells, stat, lowest, n_sectors, reading):
    if lowest is None or n_sectors not in (2, 3, 4):
        return False
    return bool(cells[f"{stat}|{lowest}|{n_sectors}"][reading])


def _outcome(tests, plan, cells, scenario, strata):
    from refute.core.sensitivity import enforce_sensitivity
    from refute.core.verdict import TestStatus, aggregate, defer_tests, enforce_coverage
    from refute.packs.tess.pipeline import expected_by_role
    from refute.packs.tess.power import registry_for

    tests = enforce_sensitivity(enforce_coverage(tests), registry_for(plan))
    out, status = [], {}
    for t in tests:
        if scenario in CELL_READING and t.name in STAT:
            ok = _group_accepted(
                cells, STAT[t.name], strata["lowest"], strata["n_sectors"], CELL_READING[scenario]
            )
            if not ok:
                t = replace(t, status=TestStatus.INCONCLUSIVE)
        out.append(t)
        status[t.name] = t.status.value
    out, _ = defer_tests(out, dict(plan.discovery.stages), 2)
    decisive, _ = expected_by_role(plan, False)
    if scenario == "a0_tests_outside":
        decisive = [n for n in decisive if n not in STAT]
    verdict, _ = aggregate([t for t in out if t.name in decisive], expected=decisive)
    return verdict.value, status


def run_one(i: int) -> dict:
    from refute.packs.tess import a0
    from refute.packs.tess.calib05 import c1
    from refute.packs.tess.calib05.steps import v04_test_plan
    from refute.packs.tess.calib051.plans import pair
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
    p04, p3 = pair(v04_test_plan(ROOT))
    flat = detrend(data.lc, p04.detrend)
    pw, searched = global_prewhitening(data, p04, flat)
    cand = search_period(searched, p04.search).candidate
    v04 = paired_outcome(data, cand, p04, 2, None, None, pw)
    rec["gate_passed"] = v04["gate_passed"]
    rec["identity"] = c1.identity(truth, v04["candidate"])
    rec["v04"] = v04["verdict"]

    captured = []
    original = a0.empirical_events

    def spy(flat_, candidate, events, params, cadence, exclude_phase_half=False):
        got = original(
            flat_, candidate, events, params, cadence, exclude_phase_half=exclude_phase_half
        )
        if not captured:  # the first call is the pipeline's, on the flattened target
            captured.append((flat_, candidate, got[0], params, cadence))
        return got

    a0.empirical_events = spy
    try:
        g = attack_candidate(data, cand, p3, None, None, pw)
    finally:
        a0.empirical_events = original
    strata = {"lowest": None, "n_sectors": 0, "events": {}}
    if captured:
        fl, c, measured, params, cadence = captured[0]
        expected_in = c.duration / cadence
        metas = [
            a0.event_meta(fl.time, fl.sector, ctr, n / expected_in, params.min_coverage)
            for ctr, n in zip(measured.centers.tolist(), measured.n_in.tolist(), strict=True)
        ]
        metas = [m for m in metas if m is not None]
        if metas:
            strata["lowest"] = max((m.stratum for m in metas), key=ORDER.index)
            strata["n_sectors"] = len({m.sector for m in metas})
            strata["events"] = dict(Counter(m.stratum for m in metas))
    rec["strata"] = strata
    cells = _cells()
    rec["verdicts"], rec["tests"] = {}, {}
    for scenario in SCENARIOS:
        rec["verdicts"][scenario], rec["tests"][scenario] = _outcome(
            list(g.tests), p3, cells, scenario, strata
        )
    rec["status"] = "OK"
    rec["cpu_seconds"] = time.process_time() - started
    return rec


def run(limit=None):
    from refute.core.runner import default_workers

    OUT.mkdir(parents=True, exist_ok=True)
    done = set()
    if RECORDS.exists():
        done = {json.loads(x)["index"] for x in RECORDS.read_text("utf-8").splitlines() if x}
    todo = [i for i in range(N) if i not in done]
    if limit is not None:
        todo = todo[:limit]
    with ProcessPoolExecutor(max_workers=default_workers()) as pool:
        futures = {pool.submit(run_one, i): i for i in todo}
        with RECORDS.open("a", encoding="utf-8") as fh:
            for fut in as_completed(futures):
                try:
                    rec = fut.result()
                except Exception as exc:  # noqa: BLE001 - recorded, never dropped
                    rec = {"index": futures[fut], "status": "ERROR", "reason": repr(exc)}
                fh.write(json.dumps(rec, sort_keys=True) + "\n")
                fh.flush()


def _t2a(cells_doc):
    """The T2a denominator of the v0.5 C2 report and what the rule fixes or bounds there."""
    if not C2_RECORDS.exists():
        return {"state": "the v0.5 C2 records are not available"}
    recs = [json.loads(x) for x in C2_RECORDS.read_text("utf-8").splitlines() if x.strip()]
    own = {
        r["target_key"]
        for r in recs
        if r["kind"] == "original" and r.get("status") == "OK" and r["chain"]["v04"]["gate_passed"]
    }
    rows = []
    for r in recs:
        if r["kind"] != "injection" or r.get("status") != "OK" or r["target_key"] in own:
            continue
        if not (r.get("recovery") or {}).get("recovered"):  # the v0.5 C2 report's denominator
            continue
        rows.append(r)
    n = len(rows)
    surv = ("SURVIVED", "WEAKENED")
    s04 = sum(r["chain"]["v04"]["stage_verdict"] in surv for r in rows)
    s05 = sum(r["chain"]["v05"]["stage_verdict"] in surv for r in rows)
    # the rest of the battery at v0.5: no decisive test outside A0 failing fatally or undecided
    from refute.packs.tess.calib051.values import V051_DECISIVE

    outside = [t for t in V051_DECISIVE if t not in STAT]
    bound = 0
    for r in rows:
        tests = r["chain"]["v05"]["tests"]
        deferred = set(r["chain"]["v05"].get("deferred") or [])
        bad = False
        for name in outside:
            t = tests.get(name)
            if t is None or name in deferred:
                continue
            if t["status"] == "INCONCLUSIVE" or (
                t["status"] == "FAIL" and t["severity"] == "fatal"
            ):
                bad = True
        bound += not bad
    tests_doc = cells_doc["tests"]["odd_even (decisive statistic)"]
    return {
        "label": "development forecast; it decides nothing",
        "denominator": n,
        "v04_survival": s04 / n if n else None,
        "v05_survival": s05 / n if n else None,
        "target_reference": "at least the v0.4 value minus 0.10",
        "strict": {
            "value": 0.0 if tests_doc["accepted_cells_strict"] == 0 else None,
            "note": "odd_even has no accepted cell, so it is INCONCLUSIVE on every curve and no "
            "curve is kept; fixed by the rule, whatever the curves are",
        },
        "upper_bound_rest_of_battery_at_v05": bound / n if n else None,
        "upper_bound_note": "the fraction with no decisive test outside A0 failing fatally or "
        "undecided, from the v0.5 statuses (not version 3's): an upper bound for "
        "a0_tests_outside and for readings with accepted cells, never a measurement",
    }


def summarize():
    recs = [json.loads(x) for x in RECORDS.read_text("utf-8").splitlines() if x.strip()]
    ok = [r for r in recs if r.get("status") == "OK"]
    eligible = [r for r in ok if r["gate_passed"] and r["identity"]]
    subset = [r for r in eligible if r["target_snr"] >= 15.0]
    n, m = len(eligible), len(subset)
    out = {
        "label": "development forecast (item 3 (b), #208); it decides nothing",
        "method_status": "not_validated",
        "curves": len(recs),
        "generation_failures": sum(r.get("status") == "GENERATION_FAILURE" for r in recs),
        "errors": sum(r.get("status") == "ERROR" for r in recs),
        "eligible": n,
        "d4_subset": m,
        "v04_kept": sum(r["v04"] in ("SURVIVED", "WEAKENED") for r in eligible) / n if n else None,
        "group_strata": dict(Counter(str(r["strata"]["lowest"]) for r in eligible)),
        "n_sectors": dict(Counter(str(r["strata"]["n_sectors"]) for r in eligible)),
        "scenarios": {},
    }
    for sc in SCENARIOS:
        counts = Counter(r["verdicts"][sc] for r in eligible)
        block = {
            "counts": {v: counts[v] for v in VERDICTS},
            "D2_kept": sum(counts[v] for v in ("SURVIVED", "WEAKENED")) / n if n else None,
            "D2_refuted": counts["REFUTED"] / n if n else None,
            "D4_inconclusive": (
                sum(r["verdicts"][sc] == "INCONCLUSIVE" for r in subset) / m if m else None
            ),
            "tests_decided": {},
        }
        for t in STAT:
            sts = Counter(r["tests"][sc].get(t) for r in eligible)
            block["tests_decided"][t] = {
                "PASS": sts["PASS"],
                "FAIL": sts["FAIL"],
                "INCONCLUSIVE": sts["INCONCLUSIVE"],
            }
        out["scenarios"][sc] = block
    cells_doc = json.loads((HERE / "strata.json").read_text("utf-8"))
    out["T2a"] = _t2a(cells_doc)
    out["cpu_hours"] = round(sum(float(r.get("cpu_seconds", 0.0)) for r in recs) / 3600.0, 3)
    (HERE / "forecast-rule.json").write_text(
        json.dumps(out, indent=1, sort_keys=True) + "\n", "utf-8"
    )
    print(json.dumps(out, indent=1, sort_keys=True))


if __name__ == "__main__":
    if sys.argv[1:2] == ["run"]:
        run(int(sys.argv[2]) if len(sys.argv) > 2 else None)
    elif sys.argv[1:] == ["summarize"]:
        summarize()
    else:
        raise SystemExit("usage: forecast_rule.py run [max units] | summarize")
