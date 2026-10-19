"""Sizing of the ``R_min`` study (docs/validation/v0.2.1/reopen/m4-implementation-map.md,
Amendment 19, with the readings of Amendment 26), committed before any lot of the study is
generated.

Read-only; writes rmin-sizing.json next to this file (never replaced).
Usage: uv run python docs/validation/v0.2.1/reopen/calc/rmin_sizing.py

It computes, from **declared reference rates** (design assumptions of Amendment 19, never
measurements):

1. The eligible-count minima of the three binomial criteria, each read with a one-sided
   Clopper-Pearson bound at ``1 - 0.05 / 5`` = 0.99 (Bonferroni over the five values of ``R``):
   ``n1 >= m1 = 725`` for the false FAIL (upper bound <= 0.02 at a true rate of 0.005), ``m4`` for
   the disappearance (lower bound >= 0.80 at a true rate of 0.95) and ``m5`` for the incompatible
   weakening (lower bound >= 0.50 at a true rate of 0.70). The pass probability of a binomial
   criterion is not monotone in the count (the steps of the bound), and the realized count is any
   count at or above the minimum, so (Amendment 26, reading 2) each minimum is the smallest count
   **from which** the pass probability at the reference rate stays at least 0.95 for every count up
   to the realized group size; the pointwise smallest count is reported beside it.
2. The number of generated targets per group (four groups: white or AR(1) noise, with or without
   variability) for which the probability that every minimum is reached is at least 0.999, at the
   declared eligible fraction 0.15 in each scenario (the weakening filter included). The three
   scenarios use the same targets, so they are dependent: their failure probabilities are combined
   by the union bound, never multiplied.
3. The realized size (Amendment 26, reading 1): each group takes its cases of each prefix
   ``refute-v0.2.1-rmin-study-<k>`` whole (400 per prefix without variability, 100 with), so its
   size is the minimum of 2 rounded up to whole blocks.

The compute it implies is computed apart, from the study's timing lot (Amendment 26, 6), before any
lot is generated, and brought to the maintainer with the 397 h ceiling.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from scipy.stats import beta, binom

HERE = Path(__file__).resolve().parent
OUT = HERE / "rmin-sizing.json"

# --- declared design assumptions (Amendment 19) -----------------------------------------------
R_VALUES = (8, 10, 12, 15, 20)
LEVEL = 1.0 - 0.05 / len(R_VALUES)  # one-sided, per bound
PASS_TARGET = 0.95  # each binomial criterion at its reference rate
ALL_MINIMA_TARGET = 0.999  # every minimum reached, per group
ELIGIBLE_FRACTION = 0.15  # in each scenario, the weakening filter included
M1 = 725  # the T1 minimum of revision 4, 2
SCENARIOS = ("constant", "disappearing", "weakened")
CRITERIA = {
    "false_fail": {"kind": "upper", "threshold": 0.02, "rate": 0.005, "start": M1},
    "disappearance": {"kind": "lower", "threshold": 0.80, "rate": 0.95, "start": 1},
    "weakening": {"kind": "lower", "threshold": 0.50, "rate": 0.70, "start": 1},
}
SCENARIO_OF = {"false_fail": "constant", "disappearance": "disappearing", "weakening": "weakened"}
# --- the lots (Amendment 26, reading 1): cases of a group per prefix, per noise model ----------
BLOCK = {
    "white, no variability": 400,
    "white, variability": 100,
    "AR(1), no variability": 400,
    "AR(1), variability": 100,
}


def cp_upper(x: int, n: int) -> float:
    return 1.0 if x >= n else float(beta.ppf(LEVEL, x + 1, n - x))


def cp_lower(x: int, n: int) -> float:
    return 0.0 if x <= 0 else float(beta.ppf(1.0 - LEVEL, x, n - x + 1))


def pass_probability(name: str, n: int) -> float:
    """P(the criterion passes) with ``n`` eligible targets at the reference rate."""
    c = CRITERIA[name]
    if c["kind"] == "upper":
        # passes when the FAIL count x has cp_upper(x, n) <= threshold; the bound increases with
        # x, so the passing counts are 0..xmax (found by bisection)
        if cp_upper(0, n) > c["threshold"]:
            return 0.0
        lo, hi = 0, n  # cp_upper(lo) passes; find the last passing x
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if cp_upper(mid, n) <= c["threshold"]:
                lo = mid
            else:
                hi = mid - 1
        return float(binom.cdf(lo, n, c["rate"]))
    # lower: passes when cp_lower(x, n) >= threshold; the bound increases with x, so the passing
    # counts are xmin..n (found by bisection)
    if cp_lower(n, n) < c["threshold"]:
        return 0.0
    lo, hi = 0, n  # cp_lower(hi) passes; find the first passing x
    while lo < hi:
        mid = (lo + hi) // 2
        if cp_lower(mid, n) >= c["threshold"]:
            hi = mid
        else:
            lo = mid + 1
    return float(binom.sf(lo - 1, n, c["rate"]))


def pointwise_minimum(name: str) -> int:
    n = CRITERIA[name]["start"]
    while pass_probability(name, n) < PASS_TARGET:
        n += 1
    return n


def uniform_minimum(name: str, upto: int) -> dict:
    """The smallest count from which the pass probability stays >= PASS_TARGET up to ``upto``."""
    probs = {k: pass_probability(name, k) for k in range(CRITERIA[name]["start"], upto + 1)}
    n = upto + 1
    for k in range(upto, CRITERIA[name]["start"] - 1, -1):
        if probs[k] < PASS_TARGET:
            break
        n = k
    if n > upto:
        raise SystemExit(f"{name}: no count up to {upto} passes")
    return {
        "minimum": n,
        "pointwise_smallest": pointwise_minimum(name),
        "pass_probability_at_minimum": probs[n],
        "lowest_pass_probability_from_minimum": min(probs[k] for k in range(n, upto + 1)),
        "checked_up_to": upto,
    }


def miss(n: int, minima: dict[str, int]) -> float:
    return sum(float(binom.cdf(m - 1, n, ELIGIBLE_FRACTION)) for m in minima.values())


def probabilistic_size(minima: dict[str, int]) -> int:
    n = max(minima.values())
    while miss(n, minima) > 1.0 - ALL_MINIMA_TARGET:
        n += 1
    return n


def main() -> None:
    if OUT.exists():
        raise SystemExit(f"{OUT.name} exists; not replaced")
    # The realized size depends on the minima and the minima on the range checked: iterate to a
    # fixed point (the range starts at the pointwise minima's size).
    minima = {name: pointwise_minimum(name) for name in CRITERIA}
    for _ in range(20):
        size = probabilistic_size(minima)
        realized = {g: math.ceil(size / b) * b for g, b in BLOCK.items()}
        upto = max(realized.values())
        criteria = {name: uniform_minimum(name, upto) for name in CRITERIA}
        new = {name: criteria[name]["minimum"] for name in CRITERIA}
        if new == minima:
            break
        minima = new
    else:
        raise SystemExit("the sizing did not reach a fixed point")
    per_group = {
        g: {
            "block_per_prefix": BLOCK[g],
            "prefixes": realized[g] // BLOCK[g],
            "targets": realized[g],
            "union_bound_on_missing": miss(realized[g], minima),
        }
        for g in BLOCK
    }
    targets = sum(realized.values())
    out = {
        "assumptions": {
            "R_values": list(R_VALUES),
            "one_sided_level_per_bound": LEVEL,
            "pass_target": PASS_TARGET,
            "all_minima_target": ALL_MINIMA_TARGET,
            "eligible_fraction_each_scenario": ELIGIBLE_FRACTION,
            "m1": M1,
            "criteria": CRITERIA,
            "note": (
                "declared reference rates, design assumptions of Amendment 19; not measurements"
            ),
        },
        "criteria": criteria,
        "probabilistic_size_per_group": size,
        "union_bound_at_probabilistic_size": miss(size, minima),
        "per_group": per_group,
        "targets": targets,
        "light_curves_study": targets * len(SCENARIOS),
        "light_curves_reserve": targets * len(SCENARIOS),
        "scenarios": list(SCENARIOS),
    }
    OUT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
