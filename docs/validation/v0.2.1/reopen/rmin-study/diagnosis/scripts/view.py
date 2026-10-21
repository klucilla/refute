"""Compact view of the diagnosis outputs (read only)."""

import json
import sys
from collections import Counter
from pathlib import Path

d = Path(sys.argv[1])
gates = json.loads((d / "gates.json").read_text("utf-8"))
cap = json.loads((d / "capacity.json").read_text("utf-8"))
su = json.loads((d / "safety-utility.json").read_text("utf-8"))
bs = json.loads((d / "bs.json").read_text("utf-8"))
inter = json.loads((d / "interruptions.json").read_text("utf-8"))

print("== Q1: share of rounds stopped at each gate (of the population), per R and cell")
for r in ("8", "20"):
    for cell, v in gates[r].items():
        row = {g: round(x["stopped_of_population"]["fraction"], 3) for g, x in v["gates"].items()}
        print(r, cell, row, "unclassified", v["unclassified_rounds"])
print("\n== Q1: G0 subcategories at R=8 (constant)")
for cell, v in gates["8"].items():
    if cell.endswith("constant"):
        print(cell, v["gates"]["G0"]["subcategories"])
print("\n== Q1: G3 cross tables at R=8, R=20")
for r in ("8", "20"):
    for cell, v in gates[r].items():
        if cell.endswith("constant"):
            print(r, cell, v["g3_cross_table"], v["gates"]["G3"]["subcategories"])
print("\n== Q3 pooled per R: categories of G2/G4 rounds")
for r, v in cap.items():
    tot = Counter()
    for _cut, e in v["by_group_band_mechanism"].items():
        for g, x in e.items():
            for k in (
                "rounds",
                "undefined",
                "below_min_snr",
                "in_margin_min_snr_to_threshold",
                "not_in_any_category",
            ):
                tot[f"{g}.{k}"] += x[k]
    print(
        r,
        dict(tot),
        "threshold parts",
        {n: round(p["threshold"], 2) for n, p in v["threshold_parts"].items()},
    )
print(
    "\n== Q3 at R=8, G2 by group|band|mechanism: below / margin / rounds, median S_pred, "
    "e_pred/e_train median"
)
for cut, e in cap["8"]["by_group_band_mechanism"].items():
    x = e["G2"]
    if x["rounds"]:
        print(
            cut,
            x["below_min_snr"],
            x["in_margin_min_snr_to_threshold"],
            x["rounds"],
            round(x["s_pred_quantiles"].get("q50", float("nan")), 2),
            round(x["e_pred_over_e_train"].get("q50", float("nan")), 2),
            round(x["d_c_over_d_train"].get("q50", float("nan")), 2),
        )
print("\n== Q5")
for r, v in bs.items():
    print(
        r,
        {
            k: v[k]
            for k in (
                "rounds",
                "targets",
                "targets_with_two_rounds",
                "median_b",
                "s",
                "sd",
                "iqr",
                "beyond_3s",
            )
        },
        "icc",
        v["anova"].get("icc"),
        "corr",
        v["two_round_correlation"],
        "B1",
        v["bootstrap_B1_selected_targets"],
        "B2",
        v["bootstrap_B2_all_targets"],
    )
print("\n== Q5 regimes at R=8")
print(bs["8"]["regimes"])
print("\n== Q8 at R=8 and R=20")
for r in ("8", "20"):
    for cell, e in su[r].items():
        keys = ("total", "eligible", "decided", "PASS", "FAIL", "INCONCLUSIVE")
        extra = {
            k: (e[k]["fraction"] if isinstance(e.get(k), dict) else e.get(k))
            for k in (
                "decided_over_total",
                "error_over_eligible",
                "error_over_decided",
                "error_over_total",
                "error_upper_over_decided",
            )
            if k in e
        }
        print(r, cell, {k: e[k] for k in keys}, extra)
print("\n== Q2 timing ratio bins at R=8")
for cell, v in inter["8"]["timing_rounds_by_rounded_ratio"].items():
    print(cell, v)
print("\n== Q2 train SNR bins at R=8 (INCONCLUSIVE rounds)")
for cell, v in inter["8"]["inconclusive_rounds_by_train_snr"].items():
    print(cell, v)
