"""Read only: a compact view of x0a.json and x0b.json."""

import json
import sys
from pathlib import Path

d = Path(sys.argv[1])
a = json.loads((d / "x0a.json").read_text("utf-8"))
b = json.loads((d / "x0b.json").read_text("utf-8"))
for r in ("8", "20"):
    print(f"== X0a R={r}")
    for g, v in a[r].items():
        print(
            g,
            "PASS",
            v["pass_targets"],
            "of decided",
            v["decided_disappearing_targets"],
            "last gate",
            v["last_round_gate"],
            "passing pos",
            v["passing_year_position"],
            "smeas",
            {
                k: round(x, 2) if isinstance(x, float) else x
                for k, x in v["s_meas_of_pass_rounds"].items()
            },
            "years pass",
            v["observing_years_of_pass_targets"],
            "years decided",
            v["observing_years_of_decided_targets"],
        )
for r in ("8", "20"):
    print(f"== X0b R={r}")
    for cell, v in b[r].items():
        extra = {k: v[k] for k in v if k.startswith(("false_", "turned_with", "b_inconclusive"))}
        print(
            cell,
            "today",
            v["today"],
            "B",
            v["spec_b"],
            "dec/total",
            round(v["decided_over_total"]["today"]["fraction"], 4),
            "->",
            round(v["decided_over_total"]["spec_b"]["fraction"], 4),
            "P->I",
            v["turned_pass_to_inconclusive"],
            extra,
        )
        print(
            "   turned undecided by gate",
            dict(list(v["turned_undecided_years_by_gate"].items())[:6]),
        )
