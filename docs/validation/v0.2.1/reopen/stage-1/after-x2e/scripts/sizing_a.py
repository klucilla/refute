"""Option A, executable version (the maintainer's decisions of 2026-10-22 on the delivery 0abc6de,
item 2): for each regime, the cases planned within what the prefix holds (one prefix: 300 two-year
cases per noise, 100 three_years, 100 variability_some_years), and the probability of reaching 40
and 15 contributing cases:

- plug-in: a binomial at each observed rate (X2e alone; pooled X2 and X2e, or X2 for the
  variability cells), which ignores the rates' own uncertainty;
- with that uncertainty: the beta-binomial predictive under a Jeffreys prior (Beta(k + 1/2,
  n - k + 1/2)) and under a uniform prior (Beta(k + 1, n - k + 1)), from the pooled counts;
- the binomial at the one-sided 95% Clopper-Pearson lower bound of the pooled rate (a pessimistic
  rate).

The cases per regime follow one sizing rule, fixed here: the smallest number with a Jeffreys
predictive probability of at least 0.95 of reaching 40 contributing cases, or every case the prefix
holds if none reaches it. The earlier proposal's numbers (44, 131, 334) are reported beside them.

The counts are development data used for planning only; nothing here is a criterion. The costs use
the unit costs of X2e and X2 (sizing.py).

  python sizing_a.py <regimes.json> <out.json>
"""

import json
import sys
from pathlib import Path

from scipy import stats

AVAILABLE = {"2 years": 300, "3+ years no variability": 100, "3+ years variability": 100}
REALIZATIONS = 100
UNIT_NOVAR = 0.92 * 3600 * 22 / 4000
UNIT_VAR = (4.03 * 3600 * 22 - 4000 * UNIT_NOVAR) / 4000
# (cell, regime, the earlier proposal's cases, sub-lot)
PLAN = (
    ("AR(1), no variability", "3+ years", 44, "S1"),
    ("white, no variability", "3+ years", 44, "S1"),
    ("AR(1), variability", "3+ years", 44, "S2"),
    ("white, variability", "3+ years", 44, "S2"),
    ("AR(1), no variability", "2 years", 131, "S3"),
    ("white, no variability", "2 years", 334, "S3"),
)
TARGETS = (40, 15)
SIZING_PROBABILITY = 0.95


def counts(regimes: dict, source: str, cell: str, reg: str) -> tuple[int, int] | None:
    e = regimes.get(source, {}).get(cell, {}).get(reg)
    return None if e is None else (e["contributing_cases"], e["cases"])


def at_least(n: int, m: int, *, p: float | None = None, a: float = 0, b: float = 0) -> float:
    if p is not None:
        return float(stats.binom.sf(m - 1, n, p))
    return float(stats.betabinom.sf(m - 1, n, a, b))


def main() -> int:
    regimes = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    out = {"note": __doc__.split("\n\n")[0], "regimes": [], "sub_lots": {}}
    for cell, reg, earlier, sub in PLAN:
        variability = "variability" in cell and "no variability" not in cell
        cap = AVAILABLE[
            "2 years"
            if reg == "2 years"
            else f"3+ years {'variability' if variability else 'no variability'}"
        ]
        alone = counts(regimes, "eligibility_c6_x2e_alone", cell, reg)
        pooled = counts(regimes, "pooled_x2_x2e_no_variability", cell, reg) or counts(
            regimes, "x2_variability", cell, reg
        )
        k, m = pooled
        n = next(
            (
                c
                for c in range(40, cap + 1)
                if at_least(c, 40, a=k + 0.5, b=m - k + 0.5) >= SIZING_PROBABILITY
            ),
            cap,
        )
        lower = float(stats.beta.ppf(0.05, k, m - k + 1)) if k > 0 else 0.0
        entry = {
            "cell": cell,
            "regime": reg,
            "sub_lot": sub,
            "cases": n,
            "earlier_proposal_cases": earlier,
            "capped_by_prefix": n == cap
            and at_least(cap, 40, a=k + 0.5, b=m - k + 0.5) < SIZING_PROBABILITY,
            "available_in_prefix": cap,
            "x2e_alone": alone,
            "pooled_or_x2": pooled,
            "expected_contributing_pooled_rate": n * k / m,
        }
        for t in TARGETS:
            entry[f"p{t}"] = {
                "plug_in_x2e_alone": None
                if alone is None
                else at_least(n, t, p=alone[0] / alone[1]),
                "plug_in_pooled": at_least(n, t, p=k / m),
                "jeffreys_predictive": at_least(n, t, a=k + 0.5, b=m - k + 0.5),
                "uniform_predictive": at_least(n, t, a=k + 1, b=m - k + 1),
                "clopper_pearson_lower_95": at_least(n, t, p=lower),
            }
        entry["clopper_pearson_lower_95_rate"] = lower
        # the same probabilities for other numbers of cases within the prefix (sensitivity)
        entry["by_cases"] = {
            str(c): {
                "jeffreys_predictive_40": at_least(c, 40, a=k + 0.5, b=m - k + 0.5),
                "clopper_pearson_lower_95_40": at_least(c, 40, p=lower),
            }
            for c in sorted({n, *range(40, cap + 1, 10), cap})
            if c >= 40
        }
        unit = UNIT_VAR if variability else UNIT_NOVAR
        entry["curves"] = n * REALIZATIONS
        entry["lp_hours"] = n * REALIZATIONS * unit / 3600
        out["regimes"].append(entry)
        s = out["sub_lots"].setdefault(sub, {"cases": 0, "curves": 0, "lp_hours": 0.0})
        s["cases"] += n
        s["curves"] += n * REALIZATIONS
        s["lp_hours"] += entry["lp_hours"]
    for s in out["sub_lots"].values():
        s["wall_hours_22_workers"] = s["lp_hours"] / 22
        s["ceiling_hours_1_5x"] = 1.5 * s["wall_hours_22_workers"]
    total = {
        k: sum(s[k] for s in out["sub_lots"].values()) for k in ("cases", "curves", "lp_hours")
    }
    total["wall_hours_22_workers"] = total["lp_hours"] / 22
    out["total"] = total
    out["unit_lp_seconds_per_curve"] = {"no_variability": UNIT_NOVAR, "variability": UNIT_VAR}
    for e in out["regimes"]:
        print(
            f"{e['sub_lot']} {e['cell']} | {e['regime']}: "
            f"{e['cases']} of {e['available_in_prefix']}; "
            f"pooled {e['pooled_or_x2']}, expected {e['expected_contributing_pooled_rate']:.1f}; "
            + "; ".join(
                f"P(>={t}) plug-in {e[f'p{t}']['plug_in_pooled']:.3f} "
                f"Jeffreys {e[f'p{t}']['jeffreys_predictive']:.3f} "
                f"uniform {e[f'p{t}']['uniform_predictive']:.3f} "
                f"CP-low {e[f'p{t}']['clopper_pearson_lower_95']:.3f}"
                for t in TARGETS
            )
        )
    for name, s in out["sub_lots"].items():
        print(name, {k: round(v, 3) for k, v in s.items()})
    print("total", {k: round(v, 3) for k, v in total.items()})
    Path(sys.argv[2]).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
