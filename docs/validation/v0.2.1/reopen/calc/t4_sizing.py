"""Sizing and compute of the T4 study of the timing rule (map Amendment 28, the maintainer's choice
of 2026-10-19: T4 with a PASS threshold calibrated on a lot of its own), for the maintainer's
decision before any lot. Read-only; writes t4-sizing.json next to this file (never replaced).

Declared reference rates (design assumptions, never measurements), from the geometric lot already
examined (``calc/timing-diagnosis.json``) where it gives them, assumed otherwise (marked). The lots'
composition: the planets of the bands near and measurable of the two-year layouts ``two_years`` and
``few_train`` (2 : 1), 600 targets per prefix (300 per noise model), taken in whole prefixes.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from scipy.stats import beta, binom

HERE = Path(__file__).resolve().parent
OUT = HERE / "t4-sizing.json"

# --- declared reference rates ----------------------------------------------------------------
COMPOSITION = {"two_years": 2 / 3, "few_train": 1 / 3}
Y_LAST = {"two_years": 13 / 40, "few_train": 12 / 20}  # geometric lot
Y_ANY = {"two_years": 15 / 40, "few_train": 14 / 20}  # geometric lot
M_SHARE = {"(12,24]": 22 / 35, "(24,36]": 13 / 35}  # geometric lot
GATES = 0.60  # assumed: an admitted round passes the gates of a PASS (R_min, hidden noise, finite)
E3_RATE = 0.15  # assumed: a constant target INCONCLUSIVE under T0 and PASS under T4
ELIGIBLE = 0.15  # assumed (as Amendment 19): T0's eligible fraction, each scenario
FALSE_PASS_TRUE = 0.01
FALSE_FAIL_TRUE = 0.005
DISAPPEARANCE_TRUE = 0.95
WEAKENING_TRUE = 0.70
COVERAGE_TRUE = 0.002
NOISES = ("white", "correlated")
BLOCK_PER_NOISE = 300
BLOCK = 600
# --- the calibration ---------------------------------------------------------------------------
N_CAL = 1000
INDEX = 996
# --- the evaluation: 16 limits ---------------------------------------------------------------
LIMITS = 16
ALPHA = 0.05 / LIMITS
PASS_TARGET = 0.95
ALL_MINIMA = 0.999
# --- the cost (the R_min timing lot, the code of 7e2eb87) --------------------------------------
SECONDS_PER_CURVE = 1.25 * 19.0
T4_FACTOR = 1.5  # declared, unmeasured: replaced by the T4 timing lot before the lots
LOT_OVERHEAD = 1.2
WORKERS = 6
TIMING_TARGETS = 40  # 20 per noise model, three scenarios


def mix(rates: dict) -> float:
    return sum(COMPOSITION[k] * rates[k] for k in COMPOSITION)


def cp_upper(x: int, n: int) -> float:
    return 1.0 if x >= n else float(beta.ppf(1 - ALPHA, x + 1, n - x))


def cp_lower(x: int, n: int) -> float:
    return 0.0 if x <= 0 else float(beta.ppf(ALPHA, x, n - x + 1))


def pass_upper(n: int, limit: float, rate: float) -> float:
    if cp_upper(0, n) > limit:
        return 0.0
    lo, hi = 0, n
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if cp_upper(mid, n) <= limit:
            lo = mid
        else:
            hi = mid - 1
    return float(binom.cdf(lo, n, rate))


def pass_lower(n: int, limit: float, rate: float) -> float:
    if cp_lower(n, n) < limit:
        return 0.0
    lo, hi = 0, n
    while lo < hi:
        mid = (lo + hi) // 2
        if cp_lower(mid, n) >= limit:
            hi = mid
        else:
            lo = mid + 1
    return float(binom.sf(lo - 1, n, rate))


def minimum(fn, limit: float, rate: float) -> int:
    """The smallest n from which the pass probability stays >= PASS_TARGET up to 4n (every n)."""
    n = 5
    while fn(n, limit, rate) < PASS_TARGET:
        n = int(n * 1.05) + 1
    while True:
        bad = next((k for k in range(n, 4 * n + 1) if fn(k, limit, rate) < PASS_TARGET), None)
        if bad is None:
            return n
        n = bad + 1


def joint_targets(
    minima: dict, yields: dict, block: int, budget: float = 1.0 - ALL_MINIMA
) -> tuple[int, float]:
    """The smallest whole-block number of targets for which the union bound on missing any
    minimum is at most ``budget`` (a share of the study's total failure budget)."""
    n = block
    while True:
        miss = sum(float(binom.cdf(minima[k] - 1, n, yields[k])) for k in minima)
        if miss <= budget:
            return n, miss
        n += block


def main() -> None:
    if OUT.exists():
        raise SystemExit(f"{OUT.name} exists; not replaced")
    y_last, y_any = mix(Y_LAST), mix(Y_ANY)
    # the calibration lot (the noises pooled): 1000 null maxima in each class
    cal_yields = {c: y_last * GATES * s for c, s in M_SHARE.items()}
    # the study's failure budget 1 - ALL_MINIMA, split before the sizes: 1/7 to the calibration,
    # 1/7 to each of the three scenarios in each of the two noise models
    share = (1.0 - ALL_MINIMA) / 7
    cal_targets, cal_miss = joint_targets(
        {c: N_CAL for c in M_SHARE}, cal_yields, BLOCK, budget=share
    )
    confidence = float(binom.cdf(INDEX - 1, N_CAL, 0.99))
    # the evaluation lot, per noise model and scenario (each scenario's targets are the first ones
    # of the lot's order: the scenarios use nested sets of the same targets)
    global ALPHA

    def criteria_for(limits: int, pooled: bool) -> dict:
        global ALPHA
        ALPHA = 0.05 / limits
        e1 = minimum(pass_upper, 0.02, FALSE_PASS_TRUE)
        out = {
            "E1b": (minimum(pass_upper, 0.02, FALSE_PASS_TRUE), y_any, "disappearing"),
            "E2": (minimum(pass_upper, 0.02, FALSE_FAIL_TRUE), ELIGIBLE, "constant"),
            "E3": (minimum(pass_lower, 0.10, E3_RATE), 1.0, "constant"),
            "E4 disappearance": (
                minimum(pass_lower, 0.80, DISAPPEARANCE_TRUE),
                ELIGIBLE,
                "disappearing",
            ),
            "E4 weakening": (minimum(pass_lower, 0.50, WEAKENING_TRUE), ELIGIBLE, "weakened"),
            "E5": (minimum(pass_upper, 0.01, COVERAGE_TRUE), y_any, "constant"),
        }
        if pooled:
            out["E1"] = (e1, y_last * GATES, "disappearing")
        else:
            for c, share in M_SHARE.items():
                out[f"E1 {c}"] = (e1, y_last * GATES * share, "disappearing")
        return out

    variants = {
        "A, E1 per noise and class (16 limits)": criteria_for(16, pooled=False),
        "B, E1 per noise, the classes pooled (14 limits)": criteria_for(14, pooled=True),
    }
    sec = SECONDS_PER_CURVE * T4_FACTOR * LOT_OVERHEAD
    cal_h = cal_targets * 1 * sec / WORKERS / 3600
    timing_h = TIMING_TARGETS * 3 * sec / WORKERS / 3600
    evaluation = {}
    for name, crit in variants.items():
        per_scenario = {}
        for sc in ("constant", "disappearing", "weakened"):
            sel = {k: v for k, v in crit.items() if v[2] == sc}
            n, miss = joint_targets(
                {k: v[0] for k, v in sel.items()},
                {k: v[1] for k, v in sel.items()},
                BLOCK_PER_NOISE,
                budget=share,
            )
            per_scenario[sc] = {"targets_per_noise": n, "union_bound_on_missing": miss}
        curves = sum(v["targets_per_noise"] for v in per_scenario.values()) * len(NOISES)
        hours = curves * sec / WORKERS / 3600
        total = timing_h + cal_h + hours
        evaluation[name] = {
            "minima_per_noise": {k: v[0] for k, v in crit.items()},
            "yields_per_target": {k: v[1] for k, v in crit.items()},
            "per_scenario": per_scenario,
            "targets": max(v["targets_per_noise"] for v in per_scenario.values()) * len(NOISES),
            "light_curves": curves,
            "evaluation_hours": hours,
            "total_hours_with_timing_and_calibration": total,
            "proposed_ceiling_hours": math.ceil(1.25 * total),
        }
    hours = {"timing_lot": timing_h, "calibration": cal_h}
    out = {
        "reference_rates": {
            "composition": COMPOSITION,
            "admitted_last_year_per_target": y_last,
            "admitted_any_per_target": y_any,
            "M_class_shares": M_SHARE,
            "gates_of_a_pass (assumed)": GATES,
            "E3 exact event per constant target (assumed)": E3_RATE,
            "T0 eligible fraction per scenario (assumed)": ELIGIBLE,
            "false_pass": FALSE_PASS_TRUE,
            "false_fail": FALSE_FAIL_TRUE,
            "disappearance_fail": DISAPPEARANCE_TRUE,
            "weakening_fail": WEAKENING_TRUE,
            "coverage_adverse": COVERAGE_TRUE,
        },
        "calibration": {
            "null_maxima_per_class": N_CAL,
            "order_statistic": INDEX,
            "confidence_of_the_bound": confidence,
            "yields_per_target": cal_yields,
            "targets": cal_targets,
            "union_bound_on_missing": cal_miss,
        },
        "evaluation": {"alpha_per_limit": "0.05/16 (A) or 0.05/14 (B)", "variants": evaluation},
        "failure_budget": {"total": 1.0 - ALL_MINIMA, "per_part": share, "parts": 7},
        "cost_machine_hours": hours,
        "cost_assumptions": {
            "seconds_per_curve": SECONDS_PER_CURVE,
            "t4_factor (unmeasured)": T4_FACTOR,
            "lot_overhead": LOT_OVERHEAD,
            "workers": WORKERS,
            "scenarios": {"timing": 3, "calibration": 1, "evaluation": 3},
        },
    }
    OUT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
