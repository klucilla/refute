# v0.5.1 WP1: the feasibility forecast (2026-11-06)

**A diagnostic forecast** ([plan](../../../plans/v0.5.1-plan.md), section 4): it settles no target,
it is never an infeasibility record by itself, and every failed target's correction route is
built whatever it says. Development data only. It is optimistic by construction (the oracle knows
the true noise, the true shape and the generator's parameters).

- Script: [forecast.py](forecast.py); output: [forecast.json](forecast.json). Run on 2026-11-06 on
  logical processors 8 to 31 (`scripts/launch_affinity.ps1`): 1,200 development curves (400 each
  of EB1, EB2 and P; seeds `refute-v051-feas:<family>:<i>`), 5 generation failures; task CPU
  5.03 processor-hours (`.cache/v051/feasibility/cost.jsonl`): **above WP1's allocation of 4**
  (1.26 times; the stop rule acts at 1.5 times), taken from the development reserve; the smoke
  run had shown 9 s per curve, the parallel run about 15 s.
- Generator, search and plans: the frozen v0.5 code (`calib05.c1.generate`, the v0.5 candidate
  generation, `calib05.plans.pair` on the v0.4 claim's test plan); nothing changed.

## What it says

| Target | Forecast | Reference |
|---|---|---|
| D1 EB1 | 388 eligible; optimistic survival 0.024; at C1' size (about 194 eligible) about 4.6 expected survivors against at most 11; the D1 count met in almost every bootstrap replicate | v0.5: 35 of 190 |
| D1 EB2 | 372 eligible; optimistic survival 0.042; about 7.9 expected survivors against at most 10; met in 87 % of replicates (median) | v0.5: 40 of 186 |
| D2, D4 (rule floor) | 356 eligible planets: `odd_even` against the full depth not detectable at the Cramer-Rao error for 4 (1.1 %); the secondary against the primary depth for none; in the SNR 15 subset, none | D2 needs kept at least about 0.868; D4 INCONCLUSIVE at most 0.30 |
| T2a (indication) | 615 recovered gate-passing injections into original-gate-negative hosts (v0.5 C2): 3 (0.5 %) with search SNR below 9.29 | T2a needs survival at least about 0.897 |

**Reading.** No target is forecast out of reach under the stated rules: the information that
separates the binaries from planets is in the light curves, and the pre-data rule with #185's
alternatives leaves almost every planet decidable at the Cramer-Rao error. v0.5's planet loss
therefore comes from the estimators and their errors (section 2 of the plan), not from the
rule's floor.

**Where the binaries' information is.** For every near-equal folded binary (depth ratio at least
0.8, found at half the true period: 66 in EB1, 79 in EB2), the nearest planet at the found period
needs the largest stellar radius the fit allowed (1.15 R_sun, 3 sigma above the generator's
star): the eclipse lasts longer than a planet's transit at the found period can around that star.
The closest cases (Mahalanobis distance 0.9 to 1.8) are the shorter, higher-impact eclipses. This
supports the route of the plan's section 3a, (ii): the duration warning against the
circular-orbit maximum with the star's uncertainty, and says that its power, not a new kind of
test, decides D1. A real estimator of the duration has an error the oracle does not have, so the
real survivors will be more than forecast.

## Limits

- Eligibility is approximated by the search candidate's SNR at the gate's `min_snr` (the final
  candidate and its gate test were not run); the binaries are folded as the search found them.
- The nearest planet is fitted in white weights near the events, and the distance computed under
  the full covariance: a fit that misses the minimum overstates the distance (optimistic).
- The bootstrap gives an upper quantile of a forecast, not a confidence statement.
- **Deviation from the plan's wording (T2a):** the plan says "each curve's white error"; the v0.5
  C2 light curves are not cached, so each injection's search SNR stands for it (white noise only:
  `odd_even` against the full depth needs SNR at least `2 (3 + 1.645) = 9.29`).

`method_status: not_validated`.
