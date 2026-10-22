"""Print X2e's tables (X2e alone and pooled with X2): python x2e_view.py <evaluation.json> ..."""

# ruff: noqa: E501  (the printed lines are kept as run)

import json
import sys
from collections import Counter
from pathlib import Path


def f(x, p=3):
    return "-" if x is None else (f"{x:.{p}g}" if isinstance(x, float) else str(x))


for path in sys.argv[1:]:
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    print(f"\n######## {Path(path).name}: rounds {d['rounds']}")
    mech = {r["case_id"]: r["mechanism"] for r in d["rows"]}
    for g, e in d["x2b"].items():
        print(f"\n{g}: case-years {e['case_years']}, excluded {e['excluded']}")
        for name, r in e["ratios"].items():
            sd, mad = r["sd_interval"], r["mad_interval"]
            sub = e["subset_same_and_placed"][name]
            print(
                f"  {name} (D={f(r['design'])}): SD {f(sd['value'])} [{f(sd['lo'])}, {f(sd['hi'])}] n={sd['cases']} -> {r['sd_verdict']}; "
                f"MAD {f(mad['value'])} [{f(mad['lo'])}, {f(mad['hi'])}] -> {r['mad_verdict']}; FINAL {r['verdict']} | subset {f(sub['value'])} [{f(sub['lo'])}, {f(sub['hi'])}] n={sub['cases']}"
            )
        ex = Counter(
            mech[k.split(" | ")[0]] for k, s in e["case_year_stats"].items() if s.get("excluded")
        )
        inc = Counter(
            mech[k.split(" | ")[0]]
            for k, s in e["case_year_stats"].items()
            if not s.get("excluded")
        )
        zero = sum(
            1 for s in e["case_year_stats"].values() if s.get("excluded") and s.get("measured") == 0
        )
        print(
            f"  excluded by mechanism {dict(ex)} (of which no measurement {zero}); included {dict(inc)}"
        )
    for g, c in d["x2a"]["by_cell"].items():
        print(f"\n{g}")
        for k in ("all", "z_train_ge_3", "fail"):
            print(f"  {k}: n={c[k]['n']} {json.dumps(c[k]['counts'])}")
    for g, c in d["descriptive"].items():
        print(
            f"\n  descriptive {g}: refused/would pass {json.dumps(c['stopped_that_would_pass'])} structural {json.dumps(c['structural_impediments'])} measured {json.dumps(c['measured'])}"
        )
    print("\nfindings:", json.dumps(d["findings"]))
