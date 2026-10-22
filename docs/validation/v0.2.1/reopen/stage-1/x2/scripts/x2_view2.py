"""Readings of X2's declared outputs (the per-round rows and the case-year statistics): FAIL per
case-year, FAIL over measured rounds per cell, the excluded case-years by mechanism."""

import json
import sys
from collections import Counter
from pathlib import Path

d = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
rows = d["rows"]
mech = {r["case_id"]: r["mechanism"] for r in rows}
fail_cy = Counter((r["group"], r["case_id"], r["year"]) for r in rows if r.get("fail"))
print("FAIL case-years:", len(fail_cy), "top:")
for k, v in fail_cy.most_common(12):
    print("  ", k, v)
for g in sorted({r["group"] for r in rows}):
    rr = [r for r in rows if r["group"] == g]
    m = sum(1 for r in rr if r.get("measured"))
    f = sum(1 for r in rr if r.get("fail"))
    cases = Counter(r["case_id"] for r in rr if r.get("fail"))
    print(
        f"{g}: FAIL {f} / measured {m} / rounds {len(rr)}; cases with a FAIL {len(cases)}; "
        f"largest case share {max(cases.values()) if cases else 0}"
    )
for g, e in d["x2b"].items():
    ex = Counter(
        mech[k.split(" | ")[0]] for k, s in e["case_year_stats"].items() if s.get("excluded")
    )
    inc = Counter(
        mech[k.split(" | ")[0]] for k, s in e["case_year_stats"].items() if not s.get("excluded")
    )
    print(f"{g}: excluded by mechanism {dict(ex)}; included {dict(inc)}")
