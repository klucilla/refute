"""Part B's two strata, described: the TOI depth and period of the drawn TOIs (descriptive only).

The maintainer's decision of 2026-11-23 (08:30, #218), item 1 (c), asks the public report to say
that the two strata are different populations. This script reads the committed draw
(`calibration/v0.5.6/part-b-draw.json`, the `chosen` entries of each stratum, whose depth and
period are the NASA Exoplanet Archive TOI table's, copied from the frozen frame) and writes the
median and quartiles of each stratum to `part-b-strata.json`. It reads no light curve and decides
nothing: it is a description of the drawn sample, never of the TOI population.

Usage (from the project root):
    .venv/Scripts/python.exe -B docs/validation/v0.5.6/part_b_strata.py
"""

from __future__ import annotations

import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DRAW = ROOT / "calibration/v0.5.6/part-b-draw.json"
OUT = Path(__file__).resolve().parent / "part-b-strata.json"
LABEL = "WEAKENED; does not meet D1, D2, D4, T2a"
FIELDS = (("depth_ppm", "TOI depth (ppm)"), ("period_days", "TOI period (d)"))


def describe(values: list[float]) -> dict:
    q1, q2, q3 = statistics.quantiles(values, n=4, method="inclusive")
    return {"n": len(values), "median": q2, "q1": q1, "q3": q3}


def main() -> None:
    data = DRAW.read_bytes()
    draw = json.loads(data)
    strata = {}
    for stratum, arm in draw["arms"].items():
        strata[stratum] = {
            field: describe([float(c[field]) for c in arm["chosen"]]) for field, _ in FIELDS
        }
    doc = {
        "schema": "refute-v056-part-b-strata-1",
        "role": "descriptive only: the drawn sample, never the TOI population",
        "limits_label": LABEL,
        "method_status": "not_validated",
        "source": {
            "draw": DRAW.relative_to(ROOT).as_posix(),
            "draw_sha256": hashlib.sha256(data).hexdigest(),
            "values": "the chosen entries' depth_ppm and period_days (NASA Exoplanet Archive TOI "
            "table, copied from the frozen frame)",
            "quartiles": "statistics.quantiles(n=4, method='inclusive')",
        },
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "strata": strata,
    }
    OUT.write_text(json.dumps(doc, indent=1) + "\n", "utf-8", newline="\n")
    for stratum, fields in strata.items():
        for field, name in FIELDS:
            d = fields[field]
            print(f"{stratum}: {name}: n {d['n']}, median {d['median']:.4g}, "
                  f"quartiles {d['q1']:.4g} to {d['q3']:.4g}")  # fmt: skip


if __name__ == "__main__":
    main()
