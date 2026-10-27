"""A descriptive breakdown of the check's result, read from result.json and the MAST rows it
recorded (no query): per class, how many TICs have each number of distinct years and of sectors,
and, for those failing D5, their separations. Nothing here changes a classification.
python breakdown.py <result.json> <mast-rows.json> <out.json>"""

import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("rcc", HERE / "real_controls_check.py")
rcc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rcc)

result = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
rows = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
ps = (rcc.CACHE / "pscomppars.csv").read_text(encoding="utf-8-sig")
toi = (rcc.CACHE / "exofop_toi.csv").read_text(encoding="utf-8-sig")
pooled = rcc.pools(ps, toi, set(result["exclusions"]["union"]))
out = {}
for name in ("planets", "false_positives"):
    years, sectors, d5, reasons = Counter(), Counter(), [], Counter()
    for tic in pooled[name]:
        failed, summary = rcc.screen(rows[str(tic)])
        reasons[failed or "inside"] += 1
        years[len(set(summary["years"]))] += 1
        sectors[len(summary["sectors"])] += 1
        if failed == "D5":
            d5.append(summary["separations_days"])
    out[name] = {
        "reasons_recomputed": dict(sorted(reasons.items())),
        "tics_by_distinct_years": dict(sorted(years.items())),
        "tics_by_sectors": dict(sorted(sectors.items())),
        "three_years_and_three_sectors": sum(
            1
            for tic in pooled[name]
            if len(set(rcc.screen(rows[str(tic)])[1]["years"])) == 3
            and len(rcc.screen(rows[str(tic)])[1]["sectors"]) == 3
        ),
        "d5_failures_separations_days": sorted(d5),
    }
Path(sys.argv[3]).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({n: {k: v for k, v in o.items() if k != "d5_failures_separations_days"}
                  for n, o in out.items()}, indent=1))  # fmt: skip
