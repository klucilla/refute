"""The joint power of the charter's full AND rule, after Codex's round 1 (blocking item 4).

Deterministic binomial enumeration (terms below 1e-15 are dropped; no simulation, no data).
Planning model (Codex's round 1, item 4): two expected-SNR bands; planets 85 and 86, FPs 153 and
154; every case is assessed with probability 0.85, independently; an assessed planet is retained
with probability 0.90 and an assessed FP survives with probability 0.15. The rules, all applied to
the same counts:
- pooled safety: Wilson upper bound (one-sided 95 %) of survivors / assessed FPs <= 0.25;
- pooled sensitivity: Wilson lower bound of retained / assessed planets >= 0.80;
- pooled coverage, per arm: Wilson lower bound of assessed / all frozen cases >= 0.70;
- per band: safety <= 0.40, sensitivity >= 0.65, coverage per arm >= 0.60;
- symmetry: the signed two-sided 90 % Newcombe (method 10) interval [L, U] of planet minus FP
  abstention (both buckets, all frozen cases) has L >= -0.15 and U <= 0.15.
An empty band (no assessed case) cannot pass. Output: power-v2.json next to this file.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
Z1 = 1.6448536269514722  # one-sided 95 %, and the two-sided 90 % interval
EPS = 1e-15
PL_BANDS, FP_BANDS = (85, 86), (153, 154)
P_ASSESS, P_RETAIN, P_SURVIVE = 0.85, 0.90, 0.15
X, Y, Z, D = 0.25, 0.80, 0.70, 0.15
XB, YB, ZB = 0.40, 0.65, 0.60


def wilson(k: int, n: int) -> tuple[float, float]:
    if n == 0:
        return 0.0, 1.0
    p = k / n
    den = 1 + Z1 * Z1 / n
    mid = (p + Z1 * Z1 / (2 * n)) / den
    half = Z1 * math.sqrt(p * (1 - p) / n + Z1 * Z1 / (4 * n * n)) / den
    return max(0.0, mid - half), min(1.0, mid + half)


def pmf(n: int, p: float) -> list[float]:
    lp, lq = math.log(p), math.log1p(-p)
    return [
        math.exp(
            math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1) + k * lp + (n - k) * lq
        )
        for k in range(n + 1)
    ]


def min_k_lower(n: int, y: float) -> int:
    """The smallest k with Wilson lower bound >= y (n + 1 if none)."""
    return next((k for k in range(n + 1) if n and wilson(k, n)[0] >= y), n + 1)


def max_k_upper(n: int, x: float) -> int:
    """The largest k with Wilson upper bound <= x (-1 if none)."""
    ok = [k for k in range(n + 1) if n and wilson(k, n)[1] <= x]
    return max(ok) if ok else -1


def arm_distribution(bands: tuple[int, int], p_good: float, planets: bool) -> dict[int, float]:
    """P(every rule of the arm passes, and the arm's total assessed count = A), by A.

    For planets, "good" is retained and the rules are lower bounds; for FPs, the counted event is
    survival (probability p_good here is the survival probability) and the rules are upper bounds.
    """
    n1, n2 = bands
    w1, w2 = pmf(n1, P_ASSESS), pmf(n2, P_ASSESS)
    out: dict[int, float] = {}
    for a1, q1 in enumerate(w1):
        if q1 < EPS or wilson(a1, n1)[0] < ZB or a1 == 0:
            continue
        for a2, q2 in enumerate(w2):
            if q2 < EPS or wilson(a2, n2)[0] < ZB or a2 == 0:
                continue
            a = a1 + a2
            if wilson(a, n1 + n2)[0] < Z:
                continue
            k1p, k2p = pmf(a1, p_good), pmf(a2, p_good)
            if planets:  # k = retained; need k1 >= t1, k2 >= t2, k1 + k2 >= tp
                t1, t2, tp = min_k_lower(a1, YB), min_k_lower(a2, YB), min_k_lower(a, Y)
                tail2 = [0.0] * (a2 + 2)  # tail2[j] = P(k2 >= j)
                for j in range(a2, -1, -1):
                    tail2[j] = tail2[j + 1] + k2p[j]
                s = sum(
                    k1p[k1] * tail2[min(a2 + 1, max(t2, tp - k1, 0))] for k1 in range(t1, a1 + 1)
                )
            else:  # k = survivors; need k1 <= t1, k2 <= t2, k1 + k2 <= tp
                t1, t2, tp = max_k_upper(a1, XB), max_k_upper(a2, XB), max_k_upper(a, X)
                head2 = [0.0] * (a2 + 1)  # head2[j] = P(k2 <= j)
                acc = 0.0
                for j in range(a2 + 1):
                    acc += k2p[j]
                    head2[j] = acc
                s = 0.0
                for k1 in range(0, t1 + 1):
                    lim = min(t2, tp - k1)
                    if lim >= 0:
                        s += k1p[k1] * head2[lim]
            if s > 0:
                out[a] = out.get(a, 0.0) + q1 * q2 * s
    return out


def symmetry_ok(abst_pl: int, n_pl: int, abst_fp: int, n_fp: int) -> bool:
    p1, p2 = abst_pl / n_pl, abst_fp / n_fp
    l1, u1 = wilson(abst_pl, n_pl)
    l2, u2 = wilson(abst_fp, n_fp)
    d = p1 - p2
    lower = d - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2)
    upper = d + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)
    return lower >= -D and upper <= D


def main() -> int:
    n_pl, n_fp = sum(PL_BANDS), sum(FP_BANDS)
    pl = arm_distribution(PL_BANDS, P_RETAIN, planets=True)
    fp = arm_distribution(FP_BANDS, P_SURVIVE, planets=False)
    joint = sum(
        qp * qf
        for ap, qp in pl.items()
        for af, qf in fp.items()
        if symmetry_ok(n_pl - ap, n_pl, n_fp - af, n_fp)
    )
    out = {
        "schema": "refute-v0513-power-2",
        "mode": "exploratory",
        "method_status": "not_validated",
        "model": {
            "planet_bands": PL_BANDS,
            "fp_bands": FP_BANDS,
            "p_assess": P_ASSESS,
            "p_retain": P_RETAIN,
            "p_survive": P_SURVIVE,
        },  # fmt: skip
        "rules": {"X": X, "Y": Y, "Z": Z, "D": D, "band_X": XB, "band_Y": YB, "band_Z": ZB},
        "planet_arm_pass": round(sum(pl.values()), 6),
        "fp_arm_pass": round(sum(fp.values()), 6),
        "joint_pass_full_and_rule": round(joint, 6),
        "codex_round_1_value": 0.9459,
    }
    (HERE / "power-v2.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
