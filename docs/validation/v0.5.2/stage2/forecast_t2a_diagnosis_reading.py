"""v0.5.2 stage 2: a reading of the diagnosis of T2a's losses (``forecast-t2a-diagnosis.json``,
#216). **A what-if on development data; it decides nothing.** ``method_status: not_validated``.
It runs nothing: it reads the diagnosis's records (``budgeted.assembled``) and the forecast's
population.

**Two corrections of reading, stated, not hidden** (the frozen classification of
``forecast_t2a_diagnosis.py`` stands as it came out in its file):
1. A FAIL of severity warning gives WEAKENED, which T2a counts as kept (``core.verdict.aggregate``,
   rule 4): the 15 warning FAILs the classification listed as (e) do not block a loss and are left
   out of the blockers here.
2. ``odd_even``'s "no calibrated error for the odd/even difference" (class (u) by the frozen rule)
   is ``battery_v52.check_odd_even`` finding that ``a0.group_variance`` returned none (a
   procedural refusal; which of its branches, a lag correlation below ``MIN_PAIRS`` window pairs,
   a covariance that is not positive semi-definite or a variance that is not positive, was not
   diagnosed), so class (d) here. Revised after the independent review of the closing record,
   which found that an earlier version named ``MIN_PAIRS`` as the cause; the numbers are unchanged.

**The scenarios** remove blockers by class and count a loss kept when nothing decisive is left; the
stratum above 20 sectors (not run) is given all lost and all kept, as in
``forecast_t2a_paths.py``, with the forecast's stratified upper sampling bound. Removals are not
estimators: they say what a battery would have to resolve, not that one can.
"""

from __future__ import annotations

import json
import statistics
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import budgeted  # noqa: E402
import forecast_t2a as t  # noqa: E402
import forecast_t2a_diagnosis as d  # noqa: E402

MEASURED = t.MEASURED_STRATA


def blockers(rec: dict) -> list[dict]:
    """The decisive blockers of a loss, with the two corrections of reading."""
    out = []
    for b in d.classify(rec):
        if b["status"] == "FAIL" and b["severity"] == "warning":
            continue
        if b["test"] == "odd_even" and b["message"].startswith("no calibrated error"):
            b = {
                **b,
                "cls": "d",
                "evidence": "a0.group_variance returned none (branch undiagnosed)",
            }
        out.append(b)
    return out


def _key(b: dict) -> str:
    sub = ""
    if b["test"] == "systematics" and b["cls"] == "b":
        sub = " background sensitivity"
    return f"{b['test']}{sub}: {b['cls']}"


SCENARIOS = {
    "as run": lambda b: False,
    "every (d), A0's and the selection's refusals": lambda b: b["cls"] == "d",
    "systematics' background sensitivity (b)": lambda b: (
        b["test"] == "systematics" and b["cls"] == "b"
    ),
    "every (d) and systematics' background sensitivity": lambda b: (
        b["cls"] == "d" or (b["test"] == "systematics" and b["cls"] == "b")
    ),
    "every (b)": lambda b: b["cls"] == "b",
    "every blocker": lambda b: True,
}


def main() -> None:
    fp = d.fingerprint()
    shards, _ = d.preflight()
    data = budgeted.assembled(
        d.SECTION, d.PART, d.OUT / fp, d.shard, shards, fp, t.WORKERS, pin=t.PIN,
        max_shard_seconds=t.MAX_SHARD_SECONDS,
    )  # fmt: skip
    recs = [json.loads(x) for x in data.decode().splitlines() if x.strip()]
    rows = t.population()
    pop = Counter(r["stratum"] for r in rows)
    minimum = sum(r["v04_stage"] in t.KEPT for r in rows) / len(rows) - 0.10
    losses = {
        (r["key"], r["slot"]): blockers(r)
        for r in recs
        if r["v04"]["stage_verdict"] in t.KEPT and r["v4"]["stage_verdict"] not in t.KEPT
    }
    by_test, sole_sets, label = Counter(), Counter(), Counter()
    for bl in losses.values():
        for b in bl:
            by_test[_key(b)] += 1
            if b.get("label_defect"):
                label[f"systematics: {b['label']} -> {b['label_from_causes']}"] += 1
            if b["test"] == "odd_even" and b["message"].startswith("no calibrated error"):
                label[f"odd_even: {b['label']} -> outside_domain"] += 1
        sole_sets[" + ".join(sorted({_key(b) for b in bl}))] += 1
    out: dict = {
        "label": "a reading of the diagnosis of T2a's losses; a what-if, it decides nothing",
        "method_status": "not_validated",
        "corrections_of_reading": [
            "a warning FAIL gives WEAKENED (kept): not a blocker",
            "odd_even 'no calibrated error' is a0.group_variance refused: class (d)",
        ],
        "losses": len(losses),
        "minimum": minimum,
        "blockers_by_test_and_class": dict(sorted(by_test.items())),
        "losses_by_set_of_blockers": dict(sorted(sole_sets.items(), key=lambda x: -x[1])),
        "labels_that_do_not_name_the_cause": dict(label),
        "scenarios": {},
    }
    for name, rm in SCENARIOS.items():
        per, upper = {}, 0
        for s in MEASURED:
            mine = [r for r in recs if r["stratum"] == s]
            k = 0
            for r in mine:
                if r["v4"]["stage_verdict"] in t.KEPT:
                    k += 1
                elif (r["key"], r["slot"]) in losses or r["v4"]["stage_verdict"] == "INCONCLUSIVE":
                    k += not [b for b in blockers(r) if not rm(b)]
            per[s] = round(k / len(mine), 4)
            upper += t._hypergeometric(k, len(mine), pop[s], t.ALPHA / len(t.STRATA))[1]
        low = sum(pop[s] * per[s] for s in MEASURED) / len(rows)
        high = low + pop["above_20"] / len(rows)
        out["scenarios"][name] = {
            "per_stratum": per,
            "kept_above_20_all_lost": round(low, 4),
            "kept_above_20_all_kept": round(high, 4),
            "upper_sampling_bound_above_20_all_kept": round(
                (upper + pop["above_20"]) / len(rows), 4
            ),
            "meets_minimum": "yes" if low >= minimum else "no" if high < minimum else
            f"only if {(minimum - low) * len(rows) / pop['above_20']:.0%} of the stratum above 20 "
            "is kept",
        }  # fmt: skip
    # the background sub-check's power: A0's error on the background rise against the depth
    power = []
    for r in recs:
        bl = losses.get((r["key"], r["slot"]), [])
        if not any(b["test"] == "systematics" and b["cls"] == "b" for b in bl):
            continue
        m = r["v4"]["tests"]["systematics"]["final"]["metrics"]
        block = r["v4"]["tests"]["systematics"]["final"]["sensitivity"]["background"]
        sap = m.get("depth_sap_ppm")
        err = m.get("background_rise_err")
        power.append({
            "injection": f"{r['key']}/{r['slot']}",
            "injected_depth_ppm": r["injection"]["depth_ppm"],
            "candidate_snr": r["final_candidate"]["snr"],
            "probability": block.get("probability"),
            "background_error_over_sap_depth": err / (sap / 1e6) if sap and err else None,
        })  # fmt: skip
    ratios = [
        p["background_error_over_sap_depth"] for p in power if p["background_error_over_sap_depth"]
    ]
    probs = [p["probability"] for p in power]
    out["background_power"] = {
        "alternative": "a background rise of 0.8 of the depth, detected with probability 0.95",
        "fail_rule": "rise at least 3 errors and at least 0.5 of the depth (params.py); power 0.95 "
        "at 0.8 of the depth needs about error <= 0.8 / (3 + 1.645) = 0.17 of the depth",
        "losses": len(power),
        "probability_median": statistics.median(probs) if probs else None,
        "probability_range": [min(probs), max(probs)] if probs else None,
        "error_over_depth_median": statistics.median(ratios) if ratios else None,
        "error_over_depth_range": [min(ratios), max(ratios)] if ratios else None,
        "per_injection": sorted(power, key=lambda p: p["probability"]),
    }  # fmt: skip
    (HERE / "forecast-t2a-diagnosis-reading.json").write_text(
        json.dumps(out, indent=1, sort_keys=True) + "\n", "utf-8"
    )
    print(json.dumps({k: v for k, v in out.items() if k != "background_power"}, indent=1))
    print(json.dumps({k: v for k, v in out["background_power"].items() if k != "per_injection"},
                     indent=1))  # fmt: skip


if __name__ == "__main__":
    main()
