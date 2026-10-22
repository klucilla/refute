"""Readings after X2e (the maintainer's decisions after X2e, items 1, 2 and 4), from the committed
evaluations only (no record, no light curve, no run):

1. spec C's eligibility with the data C6 allows for a decision (X2e alone), per cell and regime;
2. X2-B per regime (two observing years; three or more) for X2e alone, the pooled X2+X2e cells and
   X2's cells with variability: contributing cases, case-years, exclusions, coverage, and each
   ratio's median and cluster-bootstrap interval where at least 15 cases contribute (a reading, not
   a declared decision);
3. the contribution rates per regime (for sizing a new lot);
4. the measurement FAIL rounds and how many passed both capacity decisions as recorded.

  python regimes.py <x2-evaluation.json> <x2e-evaluation.json> <x2e-pooled-evaluation.json> <out>
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

POP = Path(__file__).resolve().parents[4] / "population"
sys.path.insert(0, str(POP))
import x2_evaluate as ev  # noqa: E402

TWO = {"two_years", "few_train"}
RATIOS = ("rho_1", "rho_2", "rho_h")


def regime(mechanism: str) -> str:
    return "2 years" if mechanism in TWO else "3+ years"


def ratio_entry(ratio: dict) -> dict:
    """A ratio's stored intervals, whichever key layout the evaluation has (X2's own output kept the
    verdict under `sd`/`mad`; it is read through x2-intervals.json elsewhere)."""
    return ratio


def per_regime(evaluation: dict, cells: list[str]) -> dict:
    mech = {r["case_id"]: r["mechanism"] for r in evaluation["rows"]}
    out = {}
    for g in cells:
        stats = evaluation["x2b"][g]["case_year_stats"]
        by_regime = defaultdict(
            lambda: {
                "case_years": 0,
                "excluded": 0,
                "no_measurement": 0,
                "cases": set(),
                "contributing": set(),
                "values": {n: defaultdict(list) for n in RATIOS},
            }
        )
        for key, s in stats.items():
            case = key.split(" | ")[0]
            reg = regime(mech[case])
            b = by_regime[reg]
            b["case_years"] += 1
            b["cases"].add(case)
            if s.get("excluded"):
                b["excluded"] += 1
                b["no_measurement"] += int(s.get("measured") == 0)
                continue
            b["contributing"].add(case)
            for n in RATIOS:
                v = s.get(f"{n}_sd")
                if isinstance(v, (int, float)):
                    b["values"][n][case].append(v)
        cell = {}
        for reg, b in sorted(by_regime.items()):
            entry = {
                "cases": len(b["cases"]),
                "contributing_cases": len(b["contributing"]),
                "case_years": b["case_years"],
                "excluded_case_years": b["excluded"],
                "excluded_with_no_measurement": b["no_measurement"],
                "eligible": len(b["contributing"]) >= ev.MIN_CASES,
                "case_contribution_rate": len(b["contributing"]) / len(b["cases"]),
                "case_year_contribution_rate": (b["case_years"] - b["excluded"]) / b["case_years"],
            }
            for n in RATIOS:
                entry[n] = ev.cell_interval(dict(b["values"][n]))
                flat = [v for vs in b["values"][n].values() for v in vs]
                # descriptive only: the median of the contributing case-years, with no interval and
                # no verdict where fewer than 15 cases contribute
                entry[f"{n}_median_descriptive"] = float(np.median(flat)) if flat else None
            cell[reg] = entry
        out[g] = cell
    return out


def fail_reading(evaluation: dict, cells: list[str]) -> dict:
    out = {}
    for g in cells:
        rows = [r for r in evaluation["rows"] if r["group"] == g and r.get("fail")]
        both = [r for r in rows if r.get("decision_1") == "pass" and r.get("decision_2") == "pass"]
        out[g] = {
            "measurement_fail_rounds": len(rows),
            "of_which_both_recorded_capacity_decisions_pass": len(both),
            "wrong_candidate": sum(1 for r in rows if r["cause"] == "wrong candidate"),
            "wrong_candidate_passing_both": sum(1 for r in both if r["cause"] == "wrong candidate"),
        }
    return out


def main() -> int:
    x2, x2e, pooled = (json.loads(Path(p).read_text(encoding="utf-8")) for p in sys.argv[1:4])
    novar = ["AR(1), no variability", "white, no variability"]
    var = ["AR(1), variability", "white, variability"]
    result = {
        "note": (
            "a reading of the committed evaluations; the per-regime intervals are not a declared "
            "decision; a median where fewer than 15 cases contribute is descriptive, not validated"
        ),
        "eligibility_c6_x2e_alone": per_regime(x2e, novar),
        "pooled_x2_x2e_no_variability": per_regime(pooled, novar),
        "x2_variability": per_regime(x2, var),
        "fail_x2e_pooled": fail_reading(pooled, novar),
        "fail_x2_variability": fail_reading(x2, var),
    }
    Path(sys.argv[4]).write_text(
        json.dumps(result, indent=1) + "\n", encoding="utf-8", newline="\n"
    )
    for k, v in result.items():
        if k == "note":
            continue
        print(f"\n== {k}")
        for g, cell in v.items():
            if "measurement_fail_rounds" in cell:
                print(f"  {g}: {cell}")
                continue
            for reg, e in cell.items():
                rho = " ".join(
                    f"{n} {e[n]['value']:.3g} [{e[n]['lo']:.3g}, {e[n]['hi']:.3g}]"
                    if e[n]["value"] is not None
                    else f"{n} (median {e[n + '_median_descriptive']:.3g}, not validated)"
                    if e[n + "_median_descriptive"] is not None
                    else f"{n} -"
                    for n in RATIOS
                )
                print(
                    f"  {g} | {reg}: cases {e['cases']}, contributing {e['contributing_cases']} "
                    f"(rate {e['case_contribution_rate']:.2f}), case-years {e['case_years']}, "
                    f"excluded {e['excluded_case_years']} "
                    f"(none measured {e['excluded_with_no_measurement']}), "
                    f"eligible {e['eligible']} | {rho}"
                )
    return 0


if __name__ == "__main__":
    sys.exit(main())
