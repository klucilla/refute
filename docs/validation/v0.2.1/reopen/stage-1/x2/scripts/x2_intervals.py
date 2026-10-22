"""X2-B's cell intervals, recomputed from the evaluation's own output with the committed functions
of x2_evaluate (code 8b54384), because ``x2_evaluate.evaluate`` stored each ratio as
``{**intervals, **cell_verdict(...)}`` and the verdict's keys ``sd`` and ``mad`` overwrote the
intervals' (the verdicts were computed from the intervals before; only the stored intervals were
lost). The per-case values are taken from the stored ``case_year_stats`` exactly as ``evaluate``
takes them (the non-excluded case-years' finite values, by case); ``cell_interval`` and
``cell_verdict`` are the committed ones; every recomputed verdict must equal the stored one.

  python x2_intervals.py <x2-evaluation.json> <out x2-intervals.json>
"""

import json
import math
import sys
from collections import defaultdict
from pathlib import Path

POP = Path(__file__).resolve().parents[4] / "population"
sys.path.insert(0, str(POP))
import x2_evaluate as ev  # noqa: E402


def main() -> int:
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    out, mismatches = {}, []
    m_beta = None
    for cell, entry in data["x2b"].items():
        stats = entry["case_year_stats"]
        out[cell] = {}
        for name, _ in ev.RATIOS:
            design = entry["ratios"][name]["design"]
            if name == "rho_1":
                m_beta = design
            ivs = {}
            for scale in ("sd", "mad"):
                per_case = defaultdict(list)
                for key, s in stats.items():
                    case = key.split(" | ")[0]
                    v = s.get(f"{name}_{scale}")
                    if not s.get("excluded") and isinstance(v, (int, float)) and math.isfinite(v):
                        per_case[case].append(v)
                ivs[scale] = ev.cell_interval(dict(per_case))
            verdict = ev.cell_verdict(ivs["sd"], ivs["mad"], design)
            stored = entry["ratios"][name]
            for k in ("sd", "mad", "verdict"):
                if stored[k] != verdict[k]:
                    mismatches.append(
                        f"{cell} {name} {k}: stored {stored[k]} recomputed {verdict[k]}"
                    )
            out[cell][name] = {
                "design": design,
                "sd_interval": ivs["sd"],
                "mad_interval": ivs["mad"],
                "sd_verdict": verdict["sd"],
                "mad_verdict": verdict["mad"],
                "verdict": verdict["verdict"],
            }
    payload = {"m_beta": m_beta, "mismatches": mismatches, "cells": out}
    Path(sys.argv[2]).write_text(
        json.dumps(payload, indent=1) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps({"mismatches": mismatches}))
    return 1 if mismatches else 0


if __name__ == "__main__":
    sys.exit(main())
