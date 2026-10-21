"""Read only: Q3 (run 2) totals per R and scenario, and the e_pred/e_train medians per cut."""

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

cap = json.loads((Path(sys.argv[1]) / "capacity.json").read_text("utf-8"))
for r, v in cap.items():
    tot = defaultdict(Counter)
    for cut, e in v["by_group_scenario_band_mechanism"].items():
        sc = cut.split("|")[1]
        for g, x in e.items():
            for k in (
                "rounds",
                "below_min_snr",
                "in_margin_min_snr_to_threshold",
                "undefined",
                "not_in_any_category",
            ):
                tot[f"{sc}.{g}"][k] += x[k]
    print(r, {k: dict(c) for k, c in sorted(tot.items())})
meds = defaultdict(list)
for cut, e in cap["8"]["by_group_scenario_band_mechanism"].items():
    g, sc = cut.split("|")[:2]
    x = e["G2"]
    if x["rounds"] and "q50" in x["e_pred_over_e_train"]:
        meds[sc].append(x["e_pred_over_e_train"]["q50"])
print({sc: (round(min(v), 2), round(max(v), 2)) for sc, v in meds.items()})
