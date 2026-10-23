"""Proposal B's planning arithmetic (scope-b/README.md; the maintainer's direction of 2026-10-23):
for each design of the restricted population (curves with at least three observing years), every
approved criterion's acceptance count recomputed at its set size (one-sided 95% exact
Clopper-Pearson, as population-study.md) and its chance of passing at the protocol's reference
rates (design assumptions, not measurements); the per-regime counts of G1 and G2; the necessary
condition of C1 and C3 on the holdout; and the budget's known steps under R1. Nothing here is a
criterion or a decision.

  python sizing_b.py <out.json>
"""

import json
import sys
from pathlib import Path

from scipy.stats import beta, binom

LEVEL = 0.05
# the approved limits and the protocol's reference rates (population-study.md, sections 1 and 2)
C1, C2, C3, C4W, C4C = 0.10, 0.60, 0.20, 0.01, 0.05
REF = {"C1": 0.05, "C2": 0.70, "C3": 0.10, "C4 white": 0.005, "C4 correlated": 0.025}
G1, G2 = 0.60, 0.10
# the new per-regime objectives have no approved reference rate: these are assumptions for the
# sizing only (G2 at C1's reference; G1 at an assumed delivery), to be fixed by the maintainer
ASSUMED = {"G1 delivery": 0.70, "G2 refuted": 0.05}
TARGET_CHANCE = 0.80  # the protocol's sizing rule, per criterion
DESIGNS = {
    # per noise model and band: planets without and with variability; measurable false positives;
    # no-transit curves per noise model; every class with three or more observing years
    "B1 (a new population: 250 planets per band, 125 + 125)": {
        "planets": (125, 125),
        "false_positives": 250,
        "no_transit": {"white": 2200, "correlated": 600},
    },
    "B2 (a new population: 360 planets per band, 180 + 180, for the per-regime objectives)": {
        "planets": (180, 180),
        "false_positives": 250,
        "no_transit": {"white": 2200, "correlated": 600},
    },
    "B0 (hypothetical: today's three-year planet quotas, 50 + 50 per band, with new three-year "
    "controls; today's population filtered to three years would have no false positive and no "
    "curve without a transit)": {
        "planets": (50, 50),
        "false_positives": 250,
        "no_transit": {"white": 2200, "correlated": 600},
    },
}


def upper(k: int, n: int) -> float:
    return 1.0 if k >= n else float(beta.ppf(1 - LEVEL, k + 1, n - k))


def lower(k: int, n: int) -> float:
    return 0.0 if k <= 0 else float(beta.ppf(LEVEL, k, n - k + 1))


def max_pass(n: int, limit: float) -> int:
    """The largest count whose upper bound is at most the limit (-1 if none)."""
    k = -1
    while k + 1 <= n and upper(k + 1, n) <= limit:
        k += 1
    return k


def min_pass(n: int, limit: float) -> int | None:
    return next((k for k in range(n + 1) if lower(k, n) >= limit), None)


def power_upper(n: int, c: int, p: float) -> float:
    return float(binom.cdf(c, n, p)) if c >= 0 else 0.0


def power_lower(n: int, c: int | None, p: float) -> float:
    return 0.0 if c is None else float(binom.sf(c - 1, n, p))


def design(d: dict) -> dict:
    nv, v = d["planets"]
    n_band = nv + v
    c1, c3 = max_pass(n_band, C1), max_pass(n_band, C3)
    c2 = min_pass(d["false_positives"], C2)
    out = {
        "C1 refuted planets, per band and noise": {
            "n": n_band,
            "pass_with_at_most": c1,
            "chance_at_reference": power_upper(n_band, c1, REF["C1"]),
        },
        "C2 flagged false positives, measurable, per noise": {
            "n": d["false_positives"],
            "pass_with_at_least": c2,
            "chance_at_reference": power_lower(d["false_positives"], c2, REF["C2"]),
        },
        "C3 INCONCLUSIVE, planets, measurable, per noise": {
            "n": n_band,
            "pass_with_at_most": c3,
            "chance_at_reference": power_upper(n_band, c3, REF["C3"]),
        },
        "C3 INCONCLUSIVE, false positives, measurable, per noise": {
            "n": d["false_positives"],
            "pass_with_at_most": max_pass(d["false_positives"], C3),
            "chance_at_reference": power_upper(
                d["false_positives"], max_pass(d["false_positives"], C3), REF["C3"]
            ),
        },
        "necessary holdout PASS of the measurable planets (C1 and C3 together)": {
            "of": n_band,
            "at_least": n_band - c1 - c3,
        },
    }
    for noise, n in d["no_transit"].items():
        lim, ref = (C4W, REF["C4 white"]) if noise == "white" else (C4C, REF["C4 correlated"])
        c4 = max_pass(n, lim)
        out[f"C4 false alarms, {noise}"] = {
            "n": n,
            "pass_with_at_most": c4,
            "chance_at_reference": power_upper(n, c4, ref),
        }
    for name, n in (("no variability", nv), ("variability", v)):
        k1, k2 = min_pass(n, G1), max_pass(n, G2)
        out[f"G1 delivered, measurable, {name}"] = {
            "n": n,
            "pass_with_at_least": k1,
            "chance_at_assumed_0.70": power_lower(n, k1, ASSUMED["G1 delivery"]),
        }
        out[f"G2 refuted, measurable, {name}"] = {
            "n": n,
            "pass_with_at_most": k2,
            "chance_at_assumed_0.05": power_upper(n, k2, ASSUMED["G2 refuted"]),
        }
    return out


def n_for(kind: str, p: float) -> int:
    """The smallest regime size whose chance of passing at ``p`` is at least TARGET_CHANCE."""
    for n in range(10, 2001):
        c = min_pass(n, G1) if kind == "G1" else max_pass(n, G2)
        chance = power_lower(n, c, p) if kind == "G1" else power_upper(n, c, p)
        if chance >= TARGET_CHANCE:
            return n
    return -1


def budget() -> dict:
    """The known steps of proposal B, at their ceilings, in LP-h and wall time on 22 workers
    (X2f's S1 and S2 as declared; the confirmation as X2f; X3 restricted to three-year curves,
    about half of its 2600 planning curves, at the highest measured cost per curve, 61.6 LP-s, and
    a ceiling of 1.5 times)."""
    s1, s2 = 3.25 * 22, 10.50 * 22  # the ceilings of x2f-declaration.md
    x3 = 1300 * 61.6 * 1.5 / 3600
    consumed, suites = 386.2, 19.1
    known = consumed + suites + 2 * (s1 + s2) + x3
    wall_known = 51.2 + 2 * (3.25 + 10.50) + x3 / 22
    return {
        "x2f_s1_s2_estimate_lp_h": 47.6 + 153.9,
        "x2f_s1_s2_ceiling_lp_h": s1 + s2,
        "confirmation_ceiling_lp_h": s1 + s2,
        "x3_three_year_ceiling_lp_h": x3,
        "consumed_lots_lp_h": consumed,
        "suites_proxy_lp_h": suites,
        "known_steps_at_ceilings_lp_h": known,
        "known_steps_wall_h": wall_known,
        "remaining_lp_h_of_4000": 4000 - known,
        "remaining_wall_h_of_200": 200 - wall_known,
        "remaining_wall_as_lp_h_on_22": (200 - wall_known) * 22,
    }


def main() -> int:
    out = {
        "note": __doc__.split("\n\n")[0],
        "assumed_rates_for_the_new_objectives": ASSUMED,
        "designs": {k: design(v) for k, v in DESIGNS.items()},
        "regime_size_for_0.80": {
            "G1 at 0.70": n_for("G1", ASSUMED["G1 delivery"]),
            "G2 at 0.05": n_for("G2", ASSUMED["G2 refuted"]),
        },
        "budget": budget(),
    }
    Path(sys.argv[1]).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    for name, d in out["designs"].items():
        print(name)
        for k, v in d.items():
            print("  ", k, v)
    print(json.dumps(out["budget"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
