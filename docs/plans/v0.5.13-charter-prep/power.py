"""Power calculation for the v0.5.13 charter's targets (#218, comment 7203695669, item B1 b).

Deterministic and exact (binomial sums, no simulation, no data). It sizes the three axes and
the symmetry lock on the v0.6 sample of route (d1): 171 planets found from the ground and 307
KELT false positives, the usable counts of v0.5.10's census (limits label: 'closed with declared
limits (gate REFUTED); does not meet criteria 1, 2, 3, 4, 5, 7, 8, 9, 10').

The rules (all one-sided, 95 %, Wilson score bounds):
- safety:      Wilson upper bound of (FPs that survive / FPs assessed)          <= X
- sensitivity: Wilson lower bound of (planets retained / planets assessed)      >= Y
- coverage:    Wilson lower bound of (assessed / not unassessed_data), per arm  >= Z
- symmetry:    the upper bound of the 90 % Newcombe (method 10) interval of
               |abstention rate on planets - abstention rate on FPs|            <= D

For each rule and sample size, it gives the true rate at which the rule passes with
probability 0.80 and 0.90 (the "design alternative"), and the joint probability of passing all
four (AND rule) at stated true rates; the axes are treated as independent, which the charter
names as a limit. Output: power.json and power.md next to this file.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
Z95 = 1.6448536269514722  # one-sided 95 %
Z90_TWO = 1.6448536269514722  # two-sided 90 % interval for the difference
N_PLANETS, N_FPS = 171, 307


def wilson(k: int, n: int, z: float = Z95) -> tuple[float, float]:
    if n == 0:
        return 0.0, 1.0
    p = k / n
    den = 1 + z * z / n
    mid = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0.0, mid - half), min(1.0, mid + half)


def binom_pmf(n: int, p: float) -> list[float]:
    if p <= 0:
        return [1.0] + [0.0] * n
    if p >= 1:
        return [0.0] * n + [1.0]
    lp, lq = math.log(p), math.log1p(-p)
    out = []
    for k in range(n + 1):
        lc = math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)
        out.append(math.exp(lc + k * lp + (n - k) * lq))
    return out


def power_upper(n: int, x: float, p: float) -> float:
    """P(Wilson upper bound of k/n <= x) when k ~ Bin(n, p)."""
    return sum(w for k, w in enumerate(binom_pmf(n, p)) if wilson(k, n)[1] <= x)


def power_lower(n: int, y: float, p: float) -> float:
    """P(Wilson lower bound of k/n >= y) when k ~ Bin(n, p)."""
    return sum(w for k, w in enumerate(binom_pmf(n, p)) if wilson(k, n)[0] >= y)


def solve(f, target: float, lo: float, hi: float, increasing: bool) -> float:
    for _ in range(60):
        mid = (lo + hi) / 2
        v = f(mid)
        if (v < target) == increasing:
            lo = mid
        else:
            hi = mid
    return round((lo + hi) / 2, 4)


def newcombe_upper_abs(k1: int, n1: int, k2: int, n2: int) -> float:
    """Upper end of the 90 % Newcombe (method 10) interval of |p1 - p2|."""
    p1, p2 = k1 / n1, k2 / n2
    l1, u1 = wilson(k1, n1, Z90_TWO)
    l2, u2 = wilson(k2, n2, Z90_TWO)
    d = p1 - p2
    lower = d - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2)
    upper = d + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)
    return max(abs(lower), abs(upper))


def power_symmetry(n1: int, n2: int, a1: float, a2: float, dmax: float) -> float:
    w1, w2 = binom_pmf(n1, a1), binom_pmf(n2, a2)
    total = 0.0
    for k1, p1 in enumerate(w1):
        if p1 < 1e-12:
            continue
        for k2, p2 in enumerate(w2):
            if p2 < 1e-12:
                continue
            if newcombe_upper_abs(k1, n1, k2, n2) <= dmax:
                total += p1 * p2
    return total


def main() -> int:
    out: dict = {
        "schema": "refute-v0513-power-1",
        "mode": "exploratory",
        "method_status": "not_validated",
        "sample": {"planets": N_PLANETS, "fps": N_FPS, "source": "v0.5.10 census (d1)"},
        "rules": "one-sided 95 % Wilson bounds; symmetry: 90 % Newcombe method 10 on |difference|",
        "design_alternatives": [],
        "proposal": {},
    }
    rows = []

    def row(axis: str, cov, n: int, thr: float, tgt: float, upper: bool) -> None:
        if upper:  # the rule passes when the true rate is low enough
            p = solve(lambda q: power_upper(n, thr, q), tgt, 0.0, thr, increasing=False)
        else:  # the rule passes when the true rate is high enough
            p = solve(lambda q: power_lower(n, thr, q), tgt, thr, 1.0, increasing=True)
        rows.append(
            {"axis": axis, "coverage": cov, "n": n, "threshold": thr, "power": tgt,
             "true_rate_at_power": p}
        )  # fmt: skip

    # Design alternatives: for each axis, candidate threshold and assessed n
    for cov in (1.0, 0.8, 0.7):
        for thr in (0.20, 0.25, 0.30):
            for tgt in (0.8, 0.9):
                row("safety", cov, round(N_FPS * cov), thr, tgt, upper=True)
        for thr in (0.75, 0.80, 0.85):
            for tgt in (0.8, 0.9):
                row("sensitivity", cov, round(N_PLANETS * cov), thr, tgt, upper=False)
    for n, arm in ((N_PLANETS, "planets"), (N_FPS, "fps")):
        for thr in (0.60, 0.70, 0.80):
            for tgt in (0.8, 0.9):
                row(f"coverage_{arm}", None, n, thr, tgt, upper=False)
    # Strata: 3 equal bands (of SNR or depth), 80 % assessed; floors looser than the pooled
    for thr in (0.35, 0.40):
        row("stratum_safety", 0.8, round(N_FPS // 3 * 0.8), thr, 0.8, upper=True)
    for thr in (0.65, 0.70):
        row("stratum_sensitivity", 0.8, round(N_PLANETS // 3 * 0.8), thr, 0.8, upper=False)
    out["design_alternatives"] = rows
    # Symmetry lock: power when both arms abstain at the same rate
    sym = []
    for a in (0.10, 0.20, 0.30):
        for dmax in (0.10, 0.15):
            pw = round(power_symmetry(N_PLANETS, N_FPS, a, a, dmax), 4)
            sym.append({"abstention_both_arms": a, "D": dmax, "power": pw})
    out["symmetry"] = sym
    # The proposed values and the joint (AND) power at a stated scenario
    x_cap, y_floor, z_floor, d_cap = 0.25, 0.80, 0.70, 0.15
    scen = {"fp_survival": 0.15, "planet_retention": 0.90, "assessed_share": 0.85,
            "abstention_both_arms": 0.15}  # fmt: skip
    n_fp, n_pl = round(N_FPS * scen["assessed_share"]), round(N_PLANETS * scen["assessed_share"])
    abst = scen["abstention_both_arms"]
    parts = {
        "safety": power_upper(n_fp, x_cap, scen["fp_survival"]),
        "sensitivity": power_lower(n_pl, y_floor, scen["planet_retention"]),
        "coverage_planets": power_lower(N_PLANETS, z_floor, scen["assessed_share"]),
        "coverage_fps": power_lower(N_FPS, z_floor, scen["assessed_share"]),
        "symmetry": power_symmetry(N_PLANETS, N_FPS, abst, abst, d_cap),
    }
    joint = math.prod(parts.values())
    out["proposal"] = {
        "X": x_cap,
        "Y": y_floor,
        "Z": z_floor,
        "D": d_cap,
        "scenario": scen,
        "power_by_part": {k: round(v, 4) for k, v in parts.items()},
        "joint_power_AND_independent": round(joint, 4),
    }
    (HERE / "power.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    lines = ["| axis | n | threshold | power | true rate at that power |", "|---|---|---|---|---|"]
    for r in rows:
        lines.append(
            f"| {r['axis']} (coverage {r['coverage']}) | {r['n']} | {r['threshold']} | "
            f"{r['power']} | {r['true_rate_at_power']} |"
        )
    lines += ["", "| abstention (both arms) | D | power |", "|---|---|---|"]
    lines += [f"| {s['abstention_both_arms']} | {s['D']} | {s['power']} |" for s in sym]
    lines += ["", "Proposal: " + json.dumps(out["proposal"])]
    (HERE / "power.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(out["proposal"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
