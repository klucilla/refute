"""The viability check of 2026-10-23, items 1b, 1e and 1f (arithmetic on holdout-reading.json, read
only). The final aggregation (`refute/core/verdict.py`, `aggregate`) makes a planet SURVIVED or
WEAKENED only if its holdout PASSES (the holdout is a fatal test: FAIL gives REFUTED,
INCONCLUSIVE gives INCONCLUSIVE unless another fatal test FAILS), so the holdout's PASS fraction
bounds the delivered fraction (G1) from above, and the holdout's non-PASS planets all end REFUTED
or INCONCLUSIVE.

- C1 and C3 together (the measurable band, 250 planets per noise model in the population study's
  design: 150 two-year, 50 three-year, 50 with variability; C1 passes with at most 16 REFUTED of
  250, C3 with at most 39 INCONCLUSIVE of 250) need at least 250 - 16 - 39 = 195 holdout PASS;
- G1 (a lower bound of at least 0.60 per regime) needs at least k PASS of n per regime;
- the expected holdout PASS of each noise model at those quotas, from the per-regime rates read on
  the R_min records (M4-rmin-study, R = 8), under the legacy aggregation and specification B, as
  read and under the optimistic hypothesis (capacity-INCONCLUSIVE rounds counted as PASS);
- item 1f, a quantification only: if a holdout INCONCLUSIVE counted as WEAKENED in the final
  aggregation, the upper bound on G1 would be the holdout's non-FAIL fraction.

  python bounds.py <holdout-reading.json> <out.json>
"""

import json
import sys
from pathlib import Path

from scipy.stats import beta

QUOTAS = {"2 years": 150, "3+ years": 50, "3+ years, variability": 50}
C1_MAX, C3_MAX, N_BAND = 16, 39, 250
G1_LOWER = 0.60


def cp_lower(k: int, n: int) -> float:
    return 0.0 if k <= 0 else float(beta.ppf(0.05, k, n - k + 1))


def min_k(n: int, lower: float) -> int:
    return next(k for k in range(n + 1) if cp_lower(k, n) >= lower)


def main() -> int:
    reading = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))["measurable"]
    out = {
        "c1_c3_holdout_pass_needed": {"of": N_BAND, "at_least": N_BAND - C1_MAX - C3_MAX},
        "g1_pass_needed": {str(n): min_k(n, G1_LOWER) for n in sorted(set(QUOTAS.values()))},
        "regimes": {},
        "expected_at_quotas": {},
    }
    readings = (
        "legacy_status",
        "legacy_optimistic_status",
        "spec_b_status",
        "spec_b_optimistic_status",
    )
    for key, cell in reading.items():
        n = cell["targets"]
        out["regimes"][key] = {
            r: {
                "pass": cell[r].get("PASS", 0) / n,
                "fail": cell[r].get("FAIL", 0) / n,
                "inconclusive": cell[r].get("INCONCLUSIVE", 0) / n,
            }
            for r in readings
        } | {"targets": n}
    for noise in ("white", "AR(1)"):
        e = {}
        for r in readings:
            passes = sum(
                q * out["regimes"][f"{noise} | {reg}"][r]["pass"] for reg, q in QUOTAS.items()
            )
            non_fail = sum(
                q * (1 - out["regimes"][f"{noise} | {reg}"][r]["fail"]) for reg, q in QUOTAS.items()
            )
            e[r] = {
                "holdout_pass_expected_of_250": passes,
                "meets_the_c1_c3_necessary_condition": passes >= N_BAND - C1_MAX - C3_MAX,
                "if_inconclusive_counted_weakened_upper_of_250": non_fail,
            }
        out["expected_at_quotas"][noise] = e
    Path(sys.argv[2]).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: out[k] for k in ("c1_c3_holdout_pass_needed", "g1_pass_needed")}))
    for key, v in out["regimes"].items():
        print(key, {r: round(v[r]["pass"], 3) for r in readings})
    for noise, e in out["expected_at_quotas"].items():
        print(noise, {r: round(x["holdout_pass_expected_of_250"], 1) for r, x in e.items()})
        print(
            "   if INCONCLUSIVE counted WEAKENED:",
            {r: round(x["if_inconclusive_counted_weakened_upper_of_250"], 1) for r, x in e.items()},
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
