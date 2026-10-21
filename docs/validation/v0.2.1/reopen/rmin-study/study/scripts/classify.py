"""Classify, from study-evaluation-summary.json, why each criterion failed at each R and group,
keeping apart (the maintainer's decision of 2026-10-21, item 4): "minimum not reached" (n below
the minimum, which is not waived after the result), "statistical bound not met" (the one-sided
Clopper-Pearson bound beyond its limit), "observed rate beyond the limit" (the point estimate
itself beyond it), for coverage "observed value outside its band", and for weakening its
incompatibility. Prints a Markdown table and writes failure-classes.json.

Usage: python classify.py <summary.json> <out.json>"""

import json
import sys
from pathlib import Path

MIN = {"false_fail": 866, "disappearance": 83, "weakening": 101}
FF_MAX, DIS_MIN, WEAK_MIN = 0.02, 0.80, 0.50
COV1, COV2, MED = (0.60, 0.76), (0.92, 0.98), 0.2


def classes(name: str, c: dict, r: str) -> list[str]:
    if c["passed"]:
        return []
    out = []
    if name == "false_fail":
        if c["n"] < MIN[name]:
            out.append(f"minimum not reached ({c['n']} < 866)")
        if c["upper"] > FF_MAX:
            out.append(f"bound not met (upper {c['upper']:.4f} > 0.02)")
        if c["n"] and c["fails"] / c["n"] > FF_MAX:
            out.append(f"observed rate beyond (FAILs {c['fails']}/{c['n']})")
    elif name == "disappearance":
        if c["n"] < MIN[name]:
            out.append(f"minimum not reached ({c['n']} < 83)")
        if c["lower"] < DIS_MIN:
            out.append(f"bound not met (lower {c['lower']:.3f} < 0.80)")
        if c["n"] and c["fails"] / c["n"] < DIS_MIN:
            out.append(f"observed rate beyond ({c['fails']}/{c['n']})")
    elif name == "coverage":
        bad = []
        if not COV1[0] <= c["within_1"] <= COV1[1]:
            bad.append(f"within 1 = {c['within_1']:.3f}")
        if not COV2[0] <= c["within_2"] <= COV2[1]:
            bad.append(f"within 2 = {c['within_2']:.3f}")
        if abs(c["median"]) > MED:
            bad.append(f"median {c['median']:+.3f}")
        out.append("observed value outside its band (" + ", ".join(bad) + ")")
    elif name == "weakening":
        if r in ("8", "10", "12", "15"):
            out.append("incompatible by construction (n = 0)")
        else:
            out.append("only the window 9.89 to 10 of two-year curves; no target (n = 0)")
    return out


def main() -> int:
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    table = {}
    print("| R | group | false FAIL | coverage | disappearance | weakening |")
    print("|---|---|---|---|---|---|")
    for r, rows in data["by_r"].items():
        table[r] = {}
        for g, c in rows.items():
            cells = {
                k: classes(k, c[k], r)
                for k in ("false_fail", "coverage", "disappearance", "weakening")
            }
            table[r][g] = cells
            print(
                f"| {r} | {g} | " + " | ".join("; ".join(v) or "met" for v in cells.values()) + " |"
            )
    Path(sys.argv[2]).write_text(json.dumps(table, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
