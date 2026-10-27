"""The C/D viability lot's report tables from its evaluation (no new computation: every number is
read from ``evaluation.json``; the rows' and barriers' counts are rounds, the R counts targets).

  python summarize.py <evaluation.json> <out.json>
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path


def main(argv: list[str]) -> int:
    out = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    table: dict = {"geometry_sha256": out["geometry_sha256"], "states": out["states"]}
    for alt, s in out["alternatives"].items():
        part: dict = {"outcome": s["outcome"], "rows": s["rows"], "barriers": s["barriers"]}
        part["by_regime"] = s["by_regime"]
        part["by_years"] = s["by_years"]
        part["rounds_pass_by_years"] = s["rounds_pass_by_years"]
        part["identity_flags"] = s["identity_flags"]
        part["not_identifiable_rounds"] = s["not_identifiable_rounds"]
        part["per_noise"] = {}
        for noise, x in s["per_noise"].items():
            part["per_noise"][noise] = {
                "n": x["n"],
                "missing": x["missing"],
                "R1_pass": x["pass"],
                "R1_fail": x["fail"],
                "R1_pass_L": x["R1_pass_bounds_worst"]["L"],
                "R1_fail_U": x["R1_fail_bounds_worst"]["U"],
                "legacy_pass": x["legacy_pass"],
                "R3_pass": x["R3_pass"],
                "R2": {
                    k: {
                        "pass": v["pass_bounds"]["without_missing"]["k"],
                        "fail": v["fail_bounds"]["without_missing"]["k"],
                        "pass_L": v["pass_bounds"]["without_missing"]["L"],
                        "pass_U": v["pass_bounds"]["without_missing"]["U"],
                        "reaches_benchmark": v["reaches_benchmark"],
                    }
                    for k, v in x["R2"].items()
                },
            }
        undecided = Counter()
        for r in out["readings"][alt]:
            if r["R1"] != "PASS":
                undecided[
                    tuple(sorted({rd["row"] for rd in r["rounds"] if rd["status"] != "PASS"}))
                ] += 1
        part["non_pass_targets_by_rows"] = {
            "+".join(map(str, k)): v for k, v in undecided.most_common()
        }
        step = out["steps"].get(alt)
        if step is not None and not step.get("closure"):
            best = sorted(
                step["pairs"].items(),
                key=lambda kv: -min(v["pass"] for v in kv[1]["noise"].values()),
            )
            part["step"] = {
                "succeeds": step["succeeds"],
                "cpu_seconds": step["cpu_seconds"],
                "wall_seconds": step["wall_seconds"],
                "pairs": {
                    name: {
                        n: {
                            "pass": v["pass"],
                            "fail": v["fail"],
                            "pass_L": v["pass_bounds"]["without_missing"]["L"],
                            "meets": v["meets"],
                        }
                        for n, v in p["noise"].items()
                    }
                    for name, p in best
                },
                "envelope_descriptive": step["envelope_descriptive"],
            }
        else:
            part["step"] = step
        table[alt] = part
    table["c_against_d"] = out["c_against_d"]
    table["destination"] = out["destination"]
    table["final"] = out["final"]
    with open(argv[1], "x", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(table, indent=1) + "\n")
    print(json.dumps(table, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
