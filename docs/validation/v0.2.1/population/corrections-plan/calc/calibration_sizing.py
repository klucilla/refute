"""Sizing of the calibration population of m4-plan-rev3.md (section 8), by exact binomial
calculations (Clopper-Pearson intervals) and, for the joint conditions on one set of pulls, a
seeded multinomial simulation. Read-only; writes calibration-sizing.json next to this file
(never replaced). Usage: calibration_sizing.py

Conditions (one statistic per light curve; a light curve is the independent unit):
- coverage condition K (per pull statistic): the two-sided 95% Clopper-Pearson interval of the
  fraction of |pull| <= 1 lies inside [0.60, 0.76], that of |pull| <= 2 inside [0.92, 0.98],
  and fewer than n/2 pulls lie below -0.2 and fewer than n/2 above +0.2 (median within
  +-0.2);
- upper tail condition T(alpha): the one-sided 95% upper Clopper-Pearson bound of a failure
  fraction is at most alpha;
- lower condition L(r): the one-sided 95% lower Clopper-Pearson bound of a kept fraction is at
  least r;
- median-ratio condition M: the distribution-free two-sided 95% interval of the median of a
  paired ratio lies inside [0.95, 1.05].
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from scipy.stats import beta, binom, norm

HERE = Path(__file__).resolve().parent
# calibration-sizing.json is the first run (16 conditions, superseded); this run has the 17
# conditions of m4-plan-rev3.md section 8.3 (the holdout tail split by variability).
OUT = HERE / "calibration-sizing-rev3.json"
SEED = 20261014
SIMS = 200_000


def cp_two(x: np.ndarray, n: int) -> tuple[np.ndarray, np.ndarray]:
    x = np.asarray(x)
    lo = np.where(x == 0, 0.0, beta.ppf(0.025, np.maximum(x, 1), n - x + 1))
    hi = np.where(x == n, 1.0, beta.ppf(0.975, x + 1, np.maximum(n - x, 1)))
    return lo, hi


def cp_upper(x: int, n: int) -> float:
    return 1.0 if x >= n else float(beta.ppf(0.95, x + 1, n - x))


def cp_lower(x: int, n: int) -> float:
    return 0.0 if x <= 0 else float(beta.ppf(0.05, x, n - x + 1))


def interval_pass_set(n: int, a: float, b: float) -> np.ndarray:
    x = np.arange(n + 1)
    lo, hi = cp_two(x, n)
    return x[(lo >= a) & (hi <= b)]


def p_interval(n: int, p: float, a: float, b: float) -> float:
    ok = interval_pass_set(n, a, b)
    return float(binom.pmf(ok, n, p).sum()) if ok.size else 0.0


# Pull categories for the joint coverage simulation: (<-2), [-2,-1), [-1,-0.2), [-0.2,0.2],
# (0.2,1], (1,2], (>2).
EDGES = [-2.0, -1.0, -0.2, 0.2, 1.0, 2.0]


def cell_probs(shift: float = 0.0, scale: float = 1.0) -> np.ndarray:
    cdf = [0.0, *[norm.cdf((e - shift) / scale) for e in EDGES], 1.0]
    return np.diff(cdf)


def k_pass_prob(n: int, shift: float = 0.0, scale: float = 1.0, sims: int = SIMS) -> dict:
    """Probability that the coverage condition passes when the pulls are N(shift, scale^2),
    by a seeded multinomial simulation, and the exact single-part probabilities."""
    rng = np.random.default_rng(SEED)
    pr = cell_probs(shift, scale)
    counts = rng.multinomial(n, pr, size=sims)
    in1 = counts[:, 2] + counts[:, 3] + counts[:, 4]
    in2 = in1 + counts[:, 1] + counts[:, 5]
    below = counts[:, 0] + counts[:, 1] + counts[:, 2]
    above = counts[:, 4] + counts[:, 5] + counts[:, 6]
    ok1 = np.isin(in1, interval_pass_set(n, 0.60, 0.76))
    ok2 = np.isin(in2, interval_pass_set(n, 0.92, 0.98))
    okm = (below < n / 2) & (above < n / 2)
    p1 = float(pr[2] + pr[3] + pr[4])
    p2 = float(p1 + pr[1] + pr[5])
    return {
        "joint_simulated": float(np.mean(ok1 & ok2 & okm)),
        "one_sigma_exact": p_interval(n, p1, 0.60, 0.76),
        "two_sigma_exact": p_interval(n, p2, 0.92, 0.98),
        "median_simulated": float(np.mean(okm)),
        "true_one_sigma_coverage": p1,
        "true_two_sigma_coverage": p2,
    }


def t_pass_prob(n: int, alpha: float, p: float) -> tuple[float, int]:
    xmax = -1
    for x in range(n + 1):
        if cp_upper(x, n) <= alpha:
            xmax = x
        else:
            break
    return (float(binom.cdf(xmax, n, p)) if xmax >= 0 else 0.0), xmax


def l_pass_prob(n: int, r: float, p: float) -> tuple[float, int]:
    xmin = None
    for x in range(n + 1):
        if cp_lower(x, n) >= r:
            xmin = x
            break
    return (float(binom.sf(xmin - 1, n, p)) if xmin is not None else 0.0), (xmin if xmin is not None else -1)


def m_pass_prob(n: int, center: float, spread: float) -> float:
    """Distribution-free 95% interval of the median: order statistics l and u with binomial(n,
    1/2); pass if both lie in [0.95, 1.05]. Paired ratios ~ N(center, spread^2)."""
    lo_rank = int(binom.ppf(0.025, n, 0.5))  # X_(lo_rank) with 1-based rank lo_rank
    hi_rank = n - lo_rank + 1
    a = norm.cdf((0.95 - center) / spread)
    b = norm.cdf((1.05 - center) / spread)
    # P(X_(lo) >= 0.95) = P(#below 0.95 < lo_rank); P(X_(hi) <= 1.05) = P(#above 1.05 < n-hi+1)
    p_lo = float(binom.cdf(lo_rank - 1, n, a))
    p_hi = float(binom.cdf(n - hi_rank, n, 1 - b))
    return max(0.0, p_lo + p_hi - 1.0)


def min_n(fn, target: float, start: int, stop: int, step: int) -> int | None:
    for n in range(start, stop + 1, step):
        if fn(n) >= target:
            return n
    return None


def main() -> None:
    if OUT.exists():
        raise SystemExit(f"{OUT.name} exists; not replaced")
    out: dict = {"seed": SEED, "simulations": SIMS}

    # 1. The maintainer's checks of the two-sigma condition (interval inside [0.92, 0.98]).
    checks = {
        "no_count_passes": {
            str(n): {"passing_counts": interval_pass_set(n, 0.92, 0.98).tolist()} for n in (90, 120)
        },
        "pass_probability_at_nominal_0.9545": {
            str(n): p_interval(n, 0.9545, 0.92, 0.98) for n in (300, 530, 650, 800, 1000, 1200)
        },
        "pass_probability_at_true_0.90": {
            str(n): p_interval(n, 0.90, 0.92, 0.98) for n in (300, 530, 650, 1000)
        },
    }
    checks["eight_independent_cells_at_0.91"] = 0.91 ** 8
    out["maintainer_checks"] = checks

    # 2. Design: 17 conditions per reserve (K1-K8; T1a, T1b, T2a, T2b, T5 at 0.02; T6w, T6r at
    #    0.01; L1; M1); joint power target 0.80 with an independence approximation, so each
    #    condition is sized for at least 0.80 ** (1/17).
    n_conditions = 17
    target_each = 0.80 ** (1 / n_conditions)
    out["design"] = {"conditions_per_reserve": n_conditions, "joint_target": 0.80, "target_each": target_each}

    # Coverage conditions K1..K8 (nominal pulls N(0,1)).
    n_k = min_n(lambda n: k_pass_prob(n, sims=40_000)["joint_simulated"], target_each, 600, 2000, 50)
    k_nominal = k_pass_prob(n_k)
    k_false = {
        "true_two_sigma_0.90 (pull scale 1.2159)": k_pass_prob(n_k, scale=1.2159),
        "true_one_sigma_0.55 (pull scale 1.3238)": k_pass_prob(n_k, scale=1.3238),
        "pulls_too_narrow (scale 0.80)": k_pass_prob(n_k, scale=0.80),
        "bias_0.35": k_pass_prob(n_k, shift=0.35),
    }
    out["coverage_condition"] = {"n_per_condition": n_k, "nominal": k_nominal, "false_pass": k_false}

    # Upper-tail conditions: T1 (holdout false FAIL, alpha 0.02), T2 and T3 (alias FAIL among real
    # transits, 0.02), T5 (transits lost by the prewhitening, 0.02): designed true rate alpha/4.
    tail = {}
    for name, alpha in (("T_0.02", 0.02), ("T_0.01", 0.01)):
        p_design = alpha / 4
        n_t = min_n(lambda n, a=alpha, p=p_design: t_pass_prob(n, a, p)[0], target_each, 100, 5000, 25)
        power, xmax = t_pass_prob(n_t, alpha, p_design)
        tail[name] = {
            "alpha": alpha,
            "design_true_rate": p_design,
            "n": n_t,
            "max_failures_allowed": xmax,
            "power": power,
            "false_pass_at_2alpha": t_pass_prob(n_t, alpha, 2 * alpha)[0],
            "false_pass_at_1.5alpha": t_pass_prob(n_t, alpha, 1.5 * alpha)[0],
            "zero_failure_minimum_n": math.ceil(math.log(0.05) / math.log(1 - alpha)),
        }
    tail["zero_failure_reference"] = {
        str(a): math.ceil(math.log(0.05) / math.log(1 - a)) for a in (0.01, 0.02, 0.05)
    }
    out["tail_conditions"] = tail

    # Lower condition T4 (alias FAIL kept on variability-made dips, at least 0.80): design 0.90.
    n_l = min_n(lambda n: l_pass_prob(n, 0.80, 0.90)[0], target_each, 50, 2000, 10)
    pw, xmin = l_pass_prob(n_l, 0.80, 0.90)
    out["lower_condition"] = {
        "r": 0.80,
        "design_true_rate": 0.90,
        "n": n_l,
        "min_kept_required": xmin,
        "power": pw,
        "false_pass_at_0.75": l_pass_prob(n_l, 0.80, 0.75)[0],
        "false_pass_at_0.70": l_pass_prob(n_l, 0.80, 0.70)[0],
    }

    # Median-ratio condition T7 (prewhitening depth bias): ratios ~ N(1, 0.05) by assumption.
    n_m = min_n(lambda n: m_pass_prob(n, 1.0, 0.05), target_each, 50, 2000, 10)
    out["median_ratio_condition"] = {
        "n": n_m,
        "assumed_spread": 0.05,
        "power": m_pass_prob(n_m, 1.0, 0.05),
        "false_pass_at_median_0.94": m_pass_prob(n_m, 0.94, 0.05),
        "false_pass_at_median_0.96": m_pass_prob(n_m, 0.96, 0.05),
    }

    # 3. Joint power at the chosen sizes (independence approximation; 8 K, 5 T at 0.02, 2 T at
    #    0.01, 1 L, 1 M = 17 conditions).
    joint = (
        k_nominal["joint_simulated"] ** 8
        * tail["T_0.02"]["power"] ** 5
        * tail["T_0.01"]["power"] ** 2
        * out["lower_condition"]["power"]
        * out["median_ratio_condition"]["power"]
    )
    out["joint_power_independence_approximation"] = joint

    # 4. Cases per part and cost (section 8.4 of the plan). Per replica of the development
    #    structure and per noise model: multi-year planets without variability in near and
    #    measurable (two_years 100 + three_years 50 + few_train 50, two bands) = 400; planets
    #    with variability in near and measurable = 100; no-transit: 2200 white, 600 correlated.
    n_k_noise = n_k  # each K condition is per noise model
    t1_targets = tail["T_0.02"]["n"]  # conclusive targets needed in T1a and in T1b, each
    out["t1_minimum_conclusive_fraction"] = t1_targets / (2 * n_k_noise)
    groups = {
        "planets_no_variability_per_noise": n_k_noise,
        "planets_with_variability_per_noise": n_k_noise,
        "null_per_noise": tail["T_0.01"]["n"],
    }
    replicas = {
        "planets_no_variability": math.ceil(n_k_noise / 400),
        "planets_with_variability": math.ceil(n_k_noise / 100),
        "null_white": math.ceil(tail["T_0.01"]["n"] / 2200),
        "null_correlated": math.ceil(tail["T_0.01"]["n"] / 600),
    }
    cases_part = 2 * n_k_noise + 2 * n_k_noise + 2 * tail["T_0.01"]["n"]
    paired_extra = 2 * n_k_noise + 2 * tail["T_0.01"]["n"]  # second run without prewhitening
    seconds_per_case_worker = 12.0
    workers = 24
    analysis_h = cases_part * seconds_per_case_worker / workers / 3600
    paired_h = paired_extra * seconds_per_case_worker / workers / 3600
    generation_h = cases_part * (335.0 / 5200) / 3600
    out["parts"] = {
        "groups_per_part": groups,
        "t1_needs_conclusive_targets": t1_targets,
        "replicas_of_the_development_structure_per_part": replicas,
        "cases_per_part": cases_part,
        "paired_second_runs_per_part": paired_extra,
        "cost_per_evaluation_h": {
            "analysis": analysis_h,
            "paired_second_run": paired_h,
            "generation_once": generation_h,
            "total_per_configuration_evaluation": analysis_h + paired_h,
        },
        "assumptions": "12 s per light curve per worker, 24 workers, ideal division; generation at "
        "the campaign 1 rate (335 s per 5200 cases); the lot overhead of campaign 1 (about 20%) is "
        "not included",
    }
    budget_configs = 6
    out["total_cost_h"] = {
        "selection_part_all_configurations_worst_case": budget_configs * (analysis_h + paired_h),
        "reserve_r4_once": analysis_h + paired_h + generation_h,
        "reserve_r5_once": analysis_h + paired_h + generation_h,
        "selection_generation_once": generation_h,
        "configuration_budget": budget_configs,
    }
    OUT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
