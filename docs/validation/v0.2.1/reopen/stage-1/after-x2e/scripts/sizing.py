"""Planning arithmetic for the prospective package (the maintainer's decisions after X2e, item 5):
for each regime's case contribution rate (from regimes.json, development data only), the smallest
number of new independent cases that reaches a required number of contributing cases with a given
probability under a binomial model; and the cost of the curves at the measured unit costs. Nothing
here is a criterion; the rates are estimates from few cases, so the sizes are planning values.

  python sizing.py <regimes.json> <out.json>
"""

import json
import math
import sys
from pathlib import Path

PROBABILITY = 0.90
REALIZATIONS = 100  # curves per case, as X2 and X2e
# logical-processor seconds per curve, measured: X2e (no variability) 0.92 h x 22 / 4000; X2's
# variability cells, X2's total less its two no-variability cells at X2e's unit cost
UNIT_NOVAR = 0.92 * 3600 * 22 / 4000
UNIT_VAR = (4.03 * 3600 * 22 - 4000 * UNIT_NOVAR) / 4000


def p_at_least(n: int, p: float, k: int) -> float:
    return sum(math.comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(k, n + 1))


def smallest_n(p: float, k: int) -> int:
    n = k
    while p_at_least(n, p, k) < PROBABILITY:
        n += 1
    return n


def main() -> int:
    regimes = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    rates = {}
    for source in ("eligibility_c6_x2e_alone", "pooled_x2_x2e_no_variability", "x2_variability"):
        for cell, by_regime in regimes[source].items():
            for reg, e in by_regime.items():
                rates.setdefault(f"{cell} | {reg}", {})[source] = e["case_contribution_rate"]
    out = {
        "probability": PROBABILITY,
        "realizations_per_case": REALIZATIONS,
        "unit_lp_seconds_per_curve": {"no_variability": UNIT_NOVAR, "variability": UNIT_VAR},
        "regimes": {},
    }
    for key, by_source in sorted(rates.items()):
        p = min(by_source.values())  # the lower observed rate, the conservative one
        unit = UNIT_VAR if "variability" in key and "no variability" not in key else UNIT_NOVAR
        entry = {"rates": by_source, "rate_used": p}
        for k in (15, 40):
            n = smallest_n(p, k) if p > 0 else None
            entry[f"cases_for_{k}"] = n
            entry[f"lp_hours_for_{k}"] = None if n is None else n * REALIZATIONS * unit / 3600
        out["regimes"][key] = entry
        print(
            f"{key}: rate {p:.2f}; 15 contributing: {entry['cases_for_15']} cases "
            f"({entry['lp_hours_for_15']:.1f} LP-h); 40: {entry['cases_for_40']} cases "
            f"({entry['lp_hours_for_40']:.1f} LP-h)"
        )
    print(f"unit cost: no variability {UNIT_NOVAR:.1f} LP-s/curve, variability {UNIT_VAR:.1f}")
    Path(sys.argv[2]).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
