"""The viability check of 2026-10-23, item 1c (read only): the final verdicts of the measurable
planets in the v0.2.1 development campaign 1 (`population/campaigns/dev-campaign-1/`, its committed
metrics), per noise model and mechanism, at each of its points M0 to M3. That campaign ran the whole
analysis (search, gauntlet, holdout, aggregation) on the configurations of 2026-10-13, **before the
M4 corrections**; it is not the configuration of the R_min study or of the final engine, and is
read only for what the M4 records cannot give: the final verdicts.

  python dev_campaign_reading.py <metrics-dev-campaign-1.json> <out.json>
"""

import json
import sys
from pathlib import Path

REGIME = {
    "two_years": "2 years",
    "few_train": "2 years",
    "three_years": "3+ years",
    "variability_some_years": "3+ years, variability",
}


def main() -> int:
    metrics = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    out = {"note": __doc__.split("\n\n")[0], "points": {}}
    for point in metrics["points"]:
        by = point["metrics"]["by_mechanism"]
        condition = sorted(by)[0]
        rows = {}
        for key, e in by[condition].items():
            cls, band, noise, mechanism = key.split("|")
            if cls != "planet" or band != "measurable":
                continue
            cell = rows.setdefault(
                f"{'white' if noise == 'white' else 'AR(1)'} | {REGIME[mechanism]}",
                {"n": 0, "refuted": 0, "inconclusive": 0, "mechanisms": []},
            )
            cell["n"] += e["n"]
            cell["refuted"] += e["refuted"]
            cell["inconclusive"] += e["inconclusive"]
            cell["mechanisms"].append(mechanism)
        for cell in rows.values():
            cell["survived_or_weakened"] = cell["n"] - cell["refuted"] - cell["inconclusive"]
        out["points"][point["point"]] = {"catalog_condition": condition, "measurable": rows}
        print(point["point"], condition)
        for k, v in sorted(rows.items()):
            print(
                f"  {k}: n {v['n']}, SURVIVED or WEAKENED {v['survived_or_weakened']}, "
                f"REFUTED {v['refuted']}, INCONCLUSIVE {v['inconclusive']}"
            )
    Path(sys.argv[2]).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
