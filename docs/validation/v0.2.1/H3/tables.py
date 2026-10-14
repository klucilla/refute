"""Markdown tables of the H3 part 1 measurement from its JSON results.

Usage (from the repository root):

    uv run python docs/validation/v0.2.1/H3/tables.py docs/validation/v0.2.1/H3/results.json

Rates are per trial (one seed, one round). The bound is the one-sided exact
(Clopper-Pearson) upper bound at 95%. The criterion and the decision rule are in
docs/validation/v0.2.1/H3-acceptance.md.
"""

from __future__ import annotations

import collections
import json
import math
import sys

X, ALPHA = 0.05, 0.05
NS = (3, 4, 5, 6, 7, 8)
PERIODIC = ("planet", "false_positive")
NOISES = ("white", "red")


def binom_cdf(k: int, n: int, p: float) -> float:
    return sum(math.comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(k + 1))


def upper(k: int, n: int) -> float:
    """One-sided exact (Clopper-Pearson) upper bound at 1 - ALPHA, by bisection."""
    if n == 0 or k >= n:
        return 1.0
    lo, hi = k / n, 1.0
    for _ in range(100):
        mid = (lo + hi) / 2
        if binom_cdf(k, n, mid) > ALPHA:
            lo = mid
        else:
            hi = mid
    return hi


def row(*cells: object) -> str:
    return "| " + " | ".join(str(c) for c in cells) + " |"


def header(*names: str) -> list[str]:
    return [row(*names), "|" + "---|" * len(names)]


def main() -> None:
    with open(sys.argv[1], encoding="utf-8") as fh:
        results = json.load(fh)
    cells = collections.defaultdict(list)
    for r in results:
        cells[(r["signal"], r["noise"], r["n"], r["floor"])].append(r)

    out = ["## Table 1. Calibration without the floor (periodic signals, 60 trials per cell)", ""]
    out += header(
        "Signal",
        "Noise",
        "N",
        "Orbit (d)",
        "Measured N",
        "Other signal",
        "Trials with ephemeris",
        "Trials with a 3-sigma deviation",
        "Transits > 3 sigma / total",
        "Trials that read",
        "Trials with a window loss",
        "95% upper bound",
        "< 5%?",
    )
    criterion = {}
    for signal in PERIODIC:
        for noise in NOISES:
            for n in NS:
                cell = cells[(signal, noise, n, False)]
                assert len(cell) == 60
                with_eph = [r for r in cell if r["ephemeris"]]
                pulls = [p for r in with_eph for p in r["pulls"]]
                losses = sum(r["losses"] > 0 for r in cell)
                bound = upper(losses, len(cell))
                criterion[(signal, noise, n)] = bound < X
                counts = [r["n_times"] for r in cell if r["n_times"] is not None]
                out.append(
                    row(
                        signal,
                        noise,
                        n,
                        cell[0]["orbit"],
                        f"{min(counts)}-{max(counts)}" if counts else "n/a",
                        sum(r["other"] for r in cell),
                        len(with_eph),
                        sum(r["dev3"] > 0 for r in with_eph),
                        f"{sum(p > 3 for p in pulls)} / {len(pulls)}",
                        sum(r["status"] in ("PASS", "FAIL") for r in cell),
                        losses,
                        f"{bound:.1%}",
                        "yes" if bound < X else "no",
                    )
                )

    out += ["", "## Criterion by N (the four periodic cells, without the floor)", ""]
    out += header("N", "planet white", "planet red", "FP white", "FP red", "N satisfies")
    satisfied = {}
    for n in NS:
        values = [criterion[(s, z, n)] for s in PERIODIC for z in NOISES]
        satisfied[n] = all(values)
        marks = ["yes" if v else "no" for v in values]
        out.append(row(n, *marks, "yes" if satisfied[n] else "no"))
    qualifying = [n for n in NS if all(satisfied[m] for m in NS if m >= n)]
    smallest = str(min(qualifying)) if qualifying else "none: no limit sustained"
    out += ["", f"Smallest N that satisfies it with every larger measured N: {smallest}", ""]

    out += ["## Table 2. Outcomes without / with the floor (applied at every N, 60 trials)", ""]
    out += header(
        "Signal",
        "Noise",
        "N",
        "PASS",
        "FAIL",
        "INCONCLUSIVE",
        "FAIL increase with the floor?",
        "Trials with a window loss",
    )
    for signal in (*PERIODIC, "vanishing"):
        for noise in NOISES:
            for n in NS:
                off, on = cells[(signal, noise, n, False)], cells[(signal, noise, n, True)]
                c_off = collections.Counter(r["status"] for r in off)
                c_on = collections.Counter(r["status"] for r in on)
                s_off = {r["seed"]: r["status"] for r in off}
                s_on = {r["seed"]: r["status"] for r in on}
                new = sum(1 for k in s_off if s_on[k] == "FAIL" and s_off[k] != "FAIL")
                lost = sum(1 for k in s_off if s_off[k] == "FAIL" and s_on[k] != "FAIL")
                loss_off = sum(r["losses"] > 0 for r in off)
                loss_on = sum(r["losses"] > 0 for r in on)
                out.append(
                    row(
                        signal,
                        noise,
                        n,
                        f"{c_off['PASS']} / {c_on['PASS']}",
                        f"{c_off['FAIL']} / {c_on['FAIL']}",
                        f"{c_off['INCONCLUSIVE']} / {c_on['INCONCLUSIVE']}",
                        f"{'yes' if c_on['FAIL'] > c_off['FAIL'] else 'no'} (+{new}, -{lost})",
                        f"{loss_off} / {loss_on}" if signal != "vanishing" else "n/a",
                    )
                )
    print("\n".join(out))


if __name__ == "__main__":
    main()
