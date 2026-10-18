"""Sizing of the calibration population of revision 4 of the corrections plan
(docs/validation/v0.2.1/reopen/corrections-plan-rev4.md, section 5 and Amendment 1), for the
maintainer's review before any calibration case is generated (decision of 2026-10-17, item 5).

Read-only; writes calibration-sizing-rev4.json next to this file (never replaced).
Usage: uv run python docs/validation/v0.2.1/reopen/calc/calibration_sizing_rev4.py

It computes, from **declared reference rates** (design assumptions, never measurements):

1. The 21 conditions (K1 to K8; T1a-w, T1a-r, T1b-w, T1b-r, T2a, T2b, T5, T5v at 0.02; T6w, T6r at
   0.01; L1; M1, M1v), the pass probability of each at its size, and the union lower bound on joint
   approval, ``1 - sum(P fail) - alpha_den - 11 x 0.001`` (section 5). The sizes start at
   revision 3's and the size of the condition with the largest failure probability is raised, step
   by step, until the bound reaches 0.80.
2. The simultaneous budget of the denominator bounds: ``S_total`` (configuration x condition x
   stratum, six configurations) and the per-bound level ``1 - alpha_den / (2 S_total)``.
3. The selection part: for each condition with a minimum ``m``, the group size for which the
   probability of at least ``m`` usable cases is at least 0.999 at the declared reference usable
   fraction (the reserves are sized later from the selection results, by the same rule with the
   Clopper-Pearson lower bounds; the function is here, and a worked example).
4. The worst case of machine time on logical processors 0 to 7 with 6 workers, with the declared
   seconds per case and the declared factor for the new methods, and a proposed ceiling.

The K conditions use a seeded multinomial simulation (as revision 3); M1 and M1v the exact
distribution-free interval of the median under the declared spread, by a seeded simulation.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from scipy.stats import beta, binom, norm

HERE = Path(__file__).resolve().parent
OUT = HERE / "calibration-sizing-rev4.json"
SEED = 20261017
SIMS = 200_000

# --- declared design assumptions (section 5 of revision 4; revision 3, section 8) -----------
JOINT_TARGET = 0.80
ALPHA_DEN = 0.01  # simultaneous budget of every denominator lower bound
DEN_MISS = 0.001  # P(missing denominator | bounds hold), per condition with a minimum
N_MIN_CONDITIONS = 11  # T1a-w, T1a-r, T1b-w, T1b-r, T2a, T2b, T5, T5v, L1, M1, M1v
CONFIGURATIONS = 6  # the budget of revision 3, 9.1
LOOKS = 2  # at most one enlargement of the selection part
T_DESIGN_FRACTION = 0.25  # true failure rate = alpha / 4 (revision 3)
L_DESIGN = 0.90
M_SPREAD = 0.05
# Strata per group (band x mechanism of the generation): planets without variability, near and
# measurable, mechanisms two_years, three_years, few_train; with variability, near and measurable,
# one mechanism; null, mechanisms pure_noise, trend, trend_variability.
STRATA = {
    "T1a-w": 6,
    "T1a-r": 6,
    "T1b-w": 2,
    "T1b-r": 2,
    "T2a": 12,
    "T2b": 4,
    "T5": 12,
    "T5v": 4,
    "L1": 2,
    "M1": 12,
    "M1v": 4,
}
# Reference usable fraction of each condition with a minimum (declared; the selection measures
# the real ones): conclusive rounds (T1), signal identity (T2), found without prewhitening (T5),
# candidate at the variability period (L1), found with and without prewhitening (M1).
F_REF = {
    "T1a-w": 0.5,
    "T1a-r": 0.5,
    "T1b-w": 0.4,
    "T1b-r": 0.4,
    "T2a": 0.85,
    "T2b": 0.6,
    "T5": 0.8,
    "T5v": 0.6,
    "L1": 0.6,
    "M1": 0.75,
    "M1v": 0.55,
}
SECONDS_PER_CASE_WORKER = 12.0  # campaign 1, internal time
NEW_METHODS_FACTOR = (
    2.0  # declared allowance for A1, replicas, prewhitening and timing (unmeasured)
)
LOT_OVERHEAD = 1.2  # campaign 1
WORKERS = 6
GENERATION_SECONDS_PER_CASE = 335.0 / 5200  # campaign 1, process wall, 24 workers
GENERATION_WORKERS_REF = 24


def cp_two(x: np.ndarray, n: int) -> tuple[np.ndarray, np.ndarray]:
    x = np.asarray(x)
    lo = np.where(x == 0, 0.0, beta.ppf(0.025, np.maximum(x, 1), n - x + 1))
    hi = np.where(x == n, 1.0, beta.ppf(0.975, x + 1, np.maximum(n - x, 1)))
    return lo, hi


def cp_upper(x: int, n: int) -> float:
    return 1.0 if x >= n else float(beta.ppf(0.95, x + 1, n - x))


def cp_lower(x: int, n: int, level: float = 0.95) -> float:
    return 0.0 if x <= 0 else float(beta.ppf(1.0 - level, x, n - x + 1))


def interval_pass_set(n: int, a: float, b: float) -> np.ndarray:
    x = np.arange(n + 1)
    lo, hi = cp_two(x, n)
    return x[(lo >= a) & (hi <= b)]


EDGES = [-2.0, -1.0, -0.2, 0.2, 1.0, 2.0]


def k_pass(n: int, sims: int = SIMS) -> float:
    rng = np.random.default_rng(SEED + n)
    cdf = [0.0, *[norm.cdf(e) for e in EDGES], 1.0]
    pr = np.diff(cdf)
    counts = rng.multinomial(n, pr, size=sims)
    in1 = counts[:, 2] + counts[:, 3] + counts[:, 4]
    in2 = in1 + counts[:, 1] + counts[:, 5]
    below = counts[:, 0] + counts[:, 1] + counts[:, 2]
    above = counts[:, 4] + counts[:, 5] + counts[:, 6]
    ok = (
        np.isin(in1, interval_pass_set(n, 0.60, 0.76))
        & np.isin(in2, interval_pass_set(n, 0.92, 0.98))
        & (below < n / 2)
        & (above < n / 2)
    )
    return float(np.mean(ok))


def t_pass(n: int, alpha: float) -> float:
    xmax = -1
    for x in range(n + 1):
        if cp_upper(x, n) <= alpha:
            xmax = x
        else:
            break
    return float(binom.cdf(xmax, n, alpha * T_DESIGN_FRACTION)) if xmax >= 0 else 0.0


def l_pass(n: int) -> float:
    for x in range(n + 1):
        if cp_lower(x, n) >= 0.80:
            return float(binom.sf(x - 1, n, L_DESIGN))
    return 0.0


def m_pass(n: int, sims: int = 100_000) -> float:
    """The distribution-free 95% interval of the median (order statistics), both ends inside
    [0.95, 1.05], when the paired ratios are N(1, M_SPREAD^2): by a seeded simulation."""
    lo_rank = int(binom.ppf(0.025, n, 0.5))
    hi_rank = n - lo_rank + 1
    rng = np.random.default_rng(SEED + 7 * n)
    x = np.sort(rng.normal(1.0, M_SPREAD, size=(sims, n)), axis=1)
    lo, hi = x[:, lo_rank - 1], x[:, hi_rank - 1]
    return float(np.mean((lo >= 0.95) & (hi <= 1.05)))


def kind(name: str) -> str:
    if name.startswith("K"):
        return "K"
    if name in ("T6w", "T6r"):
        return "T01"
    if name.startswith("T"):
        return "T02"
    if name == "L1":
        return "L"
    return "M"


CONDITIONS = [f"K{i}" for i in range(1, 9)] + [
    "T1a-w",
    "T1a-r",
    "T1b-w",
    "T1b-r",
    "T2a",
    "T2b",
    "T5",
    "T5v",
    "T6w",
    "T6r",
    "L1",
    "M1",
    "M1v",
]
START = {"K": 1000, "T02": 725, "T01": 1450, "L": 200, "M": 50}
STEP = {"K": 50, "T02": 25, "T01": 50, "L": 10, "M": 5}


def pass_prob(k: str, n: int) -> float:
    return {
        "K": lambda: k_pass(n),
        "T02": lambda: t_pass(n, 0.02),
        "T01": lambda: t_pass(n, 0.01),
        "L": lambda: l_pass(n),
        "M": lambda: m_pass(n),
    }[k]()


def size_conditions() -> dict:
    """Raise, by kind (every condition of a kind shares its size), the size of the kind whose
    conditions lose the most probability, until the union bound reaches the target."""
    sizes = dict(START)
    cache: dict[tuple[str, int], float] = {}

    def p(k: str, n: int) -> float:
        if (k, n) not in cache:
            cache[(k, n)] = pass_prob(k, n)
        return cache[(k, n)]

    counts = {k: sum(1 for c in CONDITIONS if kind(c) == k) for k in START}
    steps = []
    for _ in range(200):
        fail = {k: counts[k] * (1.0 - p(k, sizes[k])) for k in sizes}
        bound = 1.0 - sum(fail.values()) - ALPHA_DEN - N_MIN_CONDITIONS * DEN_MISS
        steps.append({"sizes": dict(sizes), "union_bound": bound})
        if bound >= JOINT_TARGET:
            break
        worst = max(fail, key=fail.get)
        sizes[worst] += STEP[worst]
    per_condition = {
        c: {"n": sizes[kind(c)], "pass": p(kind(c), sizes[kind(c)])} for c in CONDITIONS
    }
    return {"sizes_by_kind": sizes, "per_condition": per_condition, "steps": steps}


def min_group_for_minimum(m: int, f: float, target: float = 0.999) -> int:
    n = m
    while binom.sf(m - 1, n, f) < target:
        n += max(1, n // 200)
    return n


def main() -> None:
    if OUT.exists():
        raise SystemExit(f"{OUT.name} exists; not replaced")
    out: dict = {"seed": SEED, "simulations": SIMS}
    sizing = size_conditions()
    out["conditions"] = sizing
    final = sizing["steps"][-1]
    out["union_bound"] = {
        "value": final["union_bound"],
        "target": JOINT_TARGET,
        "alpha_den": ALPHA_DEN,
        "missing_denominators": N_MIN_CONDITIONS * DEN_MISS,
        "note": "a lower bound on joint approval conditional on the declared reference rates; "
        "not a measured power",
    }

    s_total = CONFIGURATIONS * sum(STRATA.values())
    out["simultaneous_budget"] = {
        "configurations": CONFIGURATIONS,
        "strata_per_condition": STRATA,
        "S_total": s_total,
        "looks": LOOKS,
        "level_per_bound": 1.0 - ALPHA_DEN / (LOOKS * s_total),
    }

    # The selection part: per condition with a minimum, the group size at the reference fraction.
    minima = {c: sizing["per_condition"][c]["n"] for c in F_REF}
    selection = {}
    for c, m in minima.items():
        selection[c] = {
            "minimum_usable": m,
            "reference_usable_fraction": F_REF[c],
            "group_size_at_0.999": min_group_for_minimum(m, F_REF[c]),
        }
    out["selection_part"] = selection

    # A worked example of the reserve rule: a stratum's lower bound at the Bonferroni level when
    # the selection shows the reference fraction on 1000 cases.
    level = out["simultaneous_budget"]["level_per_bound"]
    example_f_l = cp_lower(round(F_REF["T1a-w"] * 1000), 1000, level)
    out["reserve_rule_example"] = {
        "selection_cases": 1000,
        "observed_fraction": F_REF["T1a-w"],
        "f_L_at_level": example_f_l,
        "group_size_for_minimum": min_group_for_minimum(minima["T1a-w"], example_f_l),
        "cap_per_noise_model": 3000,
    }

    # Light curves per part: the largest group need of each family and noise model.
    k_n = sizing["sizes_by_kind"]["K"]
    no_var = max(
        k_n,
        selection["T1a-w"]["group_size_at_0.999"],
        selection["T2a"]["group_size_at_0.999"],
        selection["T5"]["group_size_at_0.999"],
        selection["M1"]["group_size_at_0.999"],
    )
    with_var = max(
        k_n,
        selection["T1b-w"]["group_size_at_0.999"],
        selection["T2b"]["group_size_at_0.999"],
        selection["T5v"]["group_size_at_0.999"],
        selection["M1v"]["group_size_at_0.999"],
    )
    null = max(sizing["sizes_by_kind"]["T01"], selection["L1"]["group_size_at_0.999"])
    per_part = 2 * no_var + 2 * with_var + 2 * null
    paired = 2 * no_var + 2 * with_var + 2 * null  # second run without prewhitening
    seconds = (per_part + paired) * SECONDS_PER_CASE_WORKER * NEW_METHODS_FACTOR * LOT_OVERHEAD
    eval_h = seconds / WORKERS / 3600
    gen_h = per_part * GENERATION_SECONDS_PER_CASE * GENERATION_WORKERS_REF / WORKERS / 3600
    worst = {
        "selection_generation": gen_h * 1.5,  # with the one enlargement block (at most 50%)
        "selection_evaluations": CONFIGURATIONS * eval_h * 1.5,
        "reserve_r4": gen_h + eval_h,
        "reserve_r5": gen_h + eval_h,
    }
    worst["total"] = sum(worst.values())
    out["parts"] = {
        "light_curves_per_noise_model": {
            "planets_without_variability": no_var,
            "planets_with_variability": with_var,
            "null": null,
        },
        "light_curves_per_part": per_part,
        "paired_second_runs_per_part": paired,
    }
    out["cost_hours_worst_case"] = worst
    out["cost_assumptions"] = {
        "seconds_per_case_and_worker": SECONDS_PER_CASE_WORKER,
        "new_methods_factor": NEW_METHODS_FACTOR,
        "lot_overhead": LOT_OVERHEAD,
        "workers": WORKERS,
        "affinity": "logical processors 0 to 7",
        "generation": "campaign 1 rate scaled from 24 to 6 workers",
        "enlargement": "the selection part at most 1.5 times its size (one block)",
    }
    out["proposed_ceiling_hours"] = math.ceil(1.25 * worst["total"])
    OUT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(
        json.dumps({k: out[k] for k in ("union_bound", "parts", "cost_hours_worst_case")}, indent=1)
    )
    print("ceiling:", out["proposed_ceiling_hours"], "h")


if __name__ == "__main__":
    main()
