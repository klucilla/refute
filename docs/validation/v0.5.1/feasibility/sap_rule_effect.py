"""Amendment 6, item 1 (b): the development measurement of the SAP applicability rule's effect on
D2 and D4 (docs/plans/v0.5.1-acceptance.md, WP3 (a)). Development data only; decides nothing.

C1's generator, family P, development seeds ``c1.development_seed("P", i)`` for ``i`` in 0 to 99;
the v0.4 compatibility battery and the version-3 battery on the shared candidate (as
``discover.paired.paired_chain``, stage 2, no catalogs), C1's matching and eligibility. The
version-3 battery runs once; its ``systematics`` is computed under both rules on the same
candidate, inputs and seeds (the affine rule of the code; the written constant-factor rule by
replacing ``battery_v51_diff.sap_applicability`` in this process), every other test unchanged;
then the coverage rule, the sensitivity rule, the stage deferral and the aggregation apply to each
set. Reported per rule: D2 and D4; paired: the 4 x 4 verdict tables over the eligible planets and
over the D4 subset, with denominators; the systematics status transitions; the stop condition.

Run (heavy; from the project root):
``scripts/launch_affinity.ps1 -Script docs/validation/v0.5.1/feasibility/sap_rule_effect.py``;
writes ``sap-rule-effect.json`` next to this script.
"""

from __future__ import annotations

import json
import sys
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
N = 100
VERDICTS = ("SURVIVED", "WEAKENED", "REFUTED", "INCONCLUSIVE")


def written_rule(a):
    """The acceptance's written rule before amendment 6: not applicable only when SAP and
    PDCSAP are identical up to a constant factor."""
    from refute.packs.tess import battery_v51_diff as v51d

    sap, pdc = v51d._normalized(a.sap_flux), v51d._normalized(a.pdcsap_flux)
    both = np.isfinite(sap) & np.isfinite(pdc)
    if both.any() and np.max(np.abs(sap[both] - pdc[both])) <= v51d.AFFINE_TOLERANCE:
        return False, "SAP and PDCSAP identical up to a constant factor", None
    return True, "", None


def plans():
    import copy

    from refute.packs.tess.calib05.plans import v05_plan
    from refute.packs.tess.calib05.steps import v04_test_plan
    from refute.packs.tess.params import TessTestPlan

    v04 = v04_test_plan(ROOT)
    p3 = copy.deepcopy(v05_plan(v04))
    p3["discovery"]["version"] = 3
    p3["v051"] = {}
    return TessTestPlan.model_validate(v04), TessTestPlan.model_validate(p3)


def outcome(tests, plan):
    from refute.core.sensitivity import enforce_sensitivity
    from refute.core.verdict import aggregate, defer_tests, enforce_coverage
    from refute.packs.tess.pipeline import expected_by_role
    from refute.packs.tess.power import registry_for

    tests = enforce_sensitivity(enforce_coverage(tests), registry_for(plan))
    tests, _ = defer_tests(tests, dict(plan.discovery.stages), 2)
    decisive, _ = expected_by_role(plan, False)
    verdict, _ = aggregate([t for t in tests if t.name in decisive], expected=decisive)
    sysm = next(t for t in tests if t.name == "systematics")
    return verdict.value, sysm.status.value


def run(i: int) -> dict:
    from refute.core.verdict import TestStatus
    from refute.packs.tess import battery_v51_diff as v51d
    from refute.packs.tess import power
    from refute.packs.tess.calib05 import c1
    from refute.packs.tess.detrend import detrend
    from refute.packs.tess.discover.paired import _outcome
    from refute.packs.tess.pipeline import attack_candidate, global_prewhitening
    from refute.packs.tess.search import search_period

    started = time.process_time()
    rec: dict = {"index": i}
    try:
        data, truth = c1.generate("P", c1.development_seed("P", i))
    except c1.GenerationFailedError as exc:
        return {**rec, "status": "GENERATION_FAILURE", "reason": str(exc)}
    rec["target_snr"] = truth["target_snr"]
    p04, p3 = plans()
    flat = detrend(data.lc, p04.detrend)
    pw, searched = global_prewhitening(data, p04, flat)
    cand = search_period(searched, p04.search).candidate
    v04 = _outcome(data, cand, p04, 2, None, None, pw)
    rec["gate_passed"] = v04["gate_passed"]
    rec["identity"] = c1.identity(truth, v04["candidate"])
    rec["v04"] = v04["verdict"]
    g = attack_candidate(data, cand, p3, None, None, pw)
    tests = list(g.tests)
    rec["affine"], rec["affine_systematics"] = outcome(tests, p3)
    final = g.candidate
    if final is not None and data.aux is not None:
        secondary = next(t for t in tests if t.name == "secondary_eclipse")
        exclude = secondary.status is TestStatus.FAIL
        original = v51d.sap_applicability
        v51d.sap_applicability = written_rule
        try:
            sys_w = v51d.check_systematics(
                data.aux.sectors, final, p3, power.candidate_seed("systematics", final), exclude
            )
        finally:
            v51d.sap_applicability = original
        tests_w = [sys_w if t.name == "systematics" else t for t in tests]
    else:
        tests_w = tests
    rec["written"], rec["written_systematics"] = outcome(tests_w, p3)
    rec["status"] = "OK"
    rec["cpu_seconds"] = time.process_time() - started
    return rec


def table(pairs, labels=VERDICTS):
    n = len(pairs)
    counts = Counter(pairs)
    return {
        "denominator": n,
        "counts": {f"{a} -> {b}": counts[(a, b)] for a in labels for b in labels if counts[(a, b)]},
        "fractions": {
            f"{a} -> {b}": counts[(a, b)] / n for a in labels for b in labels if counts[(a, b)]
        },
        "changed": sum(v for (a, b), v in counts.items() if a != b),
        "changed_fraction": (sum(v for (a, b), v in counts.items() if a != b) / n) if n else None,
    }


def summarize(records):
    eligible = [r for r in records if r.get("status") == "OK" and r["gate_passed"]
                and r["identity"]]  # fmt: skip
    n = len(eligible)
    subset = [r for r in eligible if r["target_snr"] >= 15.0]
    out = {"curves": len(records), "eligible": n, "d4_subset": len(subset)}
    kept04 = sum(r["v04"] in ("SURVIVED", "WEAKENED") for r in eligible) / n if n else None
    for rule in ("written", "affine"):
        kept = sum(r[rule] in ("SURVIVED", "WEAKENED") for r in eligible) / n if n else None
        refuted = sum(r[rule] == "REFUTED" for r in eligible) / n if n else None
        inc = sum(r[rule] == "INCONCLUSIVE" for r in subset) / len(subset) if subset else None
        out[rule] = {
            "counts": dict(Counter(r[rule] for r in eligible)),
            "D2_kept": kept,
            "D2_v04_kept": kept04,
            "D2_refuted_fraction": refuted,
            "D4_inconclusive_fraction": inc,
        }
    out["paired_eligible"] = table([(r["written"], r["affine"]) for r in eligible])
    out["paired_d4_subset"] = table([(r["written"], r["affine"]) for r in subset])
    statuses = ("PASS", "FAIL", "INCONCLUSIVE")
    out["systematics_eligible"] = table(
        [(r["written_systematics"], r["affine_systematics"]) for r in eligible], statuses
    )
    out["systematics_d4_subset"] = table(
        [(r["written_systematics"], r["affine_systematics"]) for r in subset], statuses
    )
    w, a = out["written"], out["affine"]
    out["stop"] = bool(
        n
        and (
            a["D2_kept"] < w["D2_kept"]
            or a["D2_refuted_fraction"] > w["D2_refuted_fraction"]
            or (subset and a["D4_inconclusive_fraction"] > w["D4_inconclusive_fraction"])
        )
    )
    return out


def main() -> None:
    sys.path.insert(0, str(ROOT / "src"))
    import subprocess

    from refute.core.runner import default_workers

    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()
    with ProcessPoolExecutor(max_workers=default_workers()) as pool:
        records = list(pool.map(run, range(N)))
    result = {"commit": commit, "summary": summarize(records), "records": records}
    (HERE / "sap-rule-effect.json").write_text(json.dumps(result, indent=1) + "\n", "utf-8")
    print(json.dumps(result["summary"], indent=1))


if __name__ == "__main__":
    main()
