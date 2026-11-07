# v0.5.1 WP1: the feasibility forecast (2026-11-06)

**A diagnostic forecast** ([plan](../../../plans/v0.5.1-plan.md), section 4): it settles no target,
it is never an infeasibility record by itself, and every failed target's correction route is
built whatever it says. Development data only. It is optimistic by construction (the oracle knows
the true noise, the true shape and the generator's parameters).

- Script: [forecast.py](forecast.py); output: [forecast.json](forecast.json). Run on 2026-11-06 on
  logical processors 8 to 31 (`scripts/launch_affinity.ps1`): 1,200 development curves (400 each
  of EB1, EB2 and P; seeds `refute-v051-feas:<family>:<i>`), 5 generation failures; task CPU
  5.03 processor-hours (`forecast.json`, `task_cpu_processor_hours`, from the per-task log
  `.cache/v051/feasibility/cost.jsonl`): **above WP1's allocation of 4**
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

**Where the binaries' information is** (`forecast.json`, `EB1_near_equal_folded` and
`EB2_near_equal_folded`). For every near-equal folded binary (depth ratio at least 0.8, found at
half the true period: 66 in EB1, 79 in EB2), the nearest planet at the found period
needs the largest stellar radius the fit allowed (1.15 R_sun, 3 sigma above the generator's
star): the eclipse lasts longer than a planet's transit at the found period can around that star.
The five closest in each family have Mahalanobis distances 0.9 to 1.83. This
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

## The duration warning on development data (amendment 3, item 2 (b), 2026-11-06)

Script: [duration_measurement.py](duration_measurement.py); output:
[duration-measurement.json](duration-measurement.json). Development data only: 200 planets of each
of the C1 families P and PG (190 generated in PG), and 100 binaries folded at half their period per
case (depth ratio 1.0, 0.9, 0.7 x target SNR 10, 20, 30; the C1 EB1 geometry, impact parameter 0 to
0.8); the TIC star of the generator (radius and mass errors 5 %); the choices the acceptance text
does not fix yet are stated in the script's docstring; 2.31 processor-hours. It decides nothing.

| Group | Not detectable (Wilson 95 %) | Warning, all | Warning among detectable |
|---|---|---|---|
| P | 0.71 (0.64 to 0.77); 0.61 at target SNR >= 15 | 0.005 (1 of 200) | 0.0 |
| PG | 0.83 (0.77 to 0.88) | 0.0 (0 of 190) | 0.0 |
| binaries, SNR 10 | 0.95 to 0.98 | 0.25 to 0.35 | 0.2 to 0.8 (few detectable) |
| binaries, SNR 20 | 0.67 to 0.75 | 0.44 to 0.51 | 0.48 to 0.68 |
| binaries, SNR 30 | 0.53 to 0.71 | 0.44 to 0.52 | 0.52 to 0.62 |

By impact parameter (all binary cases at SNR 20 and 30): a warning on 92 to 100 % of the binaries
with b below 0.3, 17 to 32 % with b from 0.3 to 0.6, none with b from 0.6 to 0.8. Median
`sigma_Tmax / T_max` 5.3 % (the TIC errors), median `sigma_T / T_max` 1.1 to 5.8 % (by SNR). Under
the per-geometry effect (each binary's own duration minus `T_max(P)`, reported only, never used to
retune), 0 to 8 % detectable, the effect negative for 16 to 26 % of the binaries.

**Reading.** The warning has power as a measurement (about half the folded binaries at SNR 20 and
above, nearly all of the central ones, with one false warning in 390 planets), but as a decisive
warning test the sensitivity rule refuses its PASS on most planets (71 % of P), because the TIC's
5 % radius and mass errors alone almost fill the margin the alternative leaves; D2 allows a loss of
about 13 %. By amendment 3, item 2 (c) and (d), this goes to the maintainer with Claude's and
Codex's recommendation.

## The duration measurement with the adopted estimator (amendment 9, item 1, 2026-11-07)

Script: [duration_measurement_v2.py](duration_measurement_v2.py); output:
[duration-measurement-v2.json](duration-measurement-v2.json). The same development cases and
seeds as the first measurement, measured by the production function
`battery_v51.check_duration_excess` (the phase-placement `sigma_T` with its validity rule);
2.27 processor-hours. It decides nothing.

| Group | Not detectable | Warning, all | Warning among detectable | Placements rejected |
|---|---|---|---|---|
| P (200) | 0.695 | 0.005 (1 of 200) | 0.0 | 16 of 4000 (at a bound) |
| PG (190 generated) | 0.816 | 0.0 | 0.0 | 5 of 3800 |
| binaries, SNR 10 | 0.95 to 0.97 | 0.25 to 0.34 | 0.4 to 0.67 | 3 to 5 per 2000 |
| binaries, SNR 20 | 0.67 to 0.77 | 0.45 to 0.51 | 0.52 to 0.72 | 1 to 6 per 2000 |
| binaries, SNR 30 | 0.54 to 0.67 | 0.43 to 0.53 | 0.51 to 0.59 | 3 to 10 per 2000 |

**Reading.** The adopted estimator reproduces the first measurement's picture (P not detectable
0.695 against 0.71; PG 0.816 against 0.83; the binaries' warning rates within a few points); the
validity rule rejects under 1 % of the placements and leaves no planet or binary INCONCLUSIVE.
Amendment 4's figures may be cited for the adopted estimator with these numbers.

## The cost of the acceptance run (2026-11-07)

Script: [acceptance_cost_probe.py](acceptance_cost_probe.py); output:
[acceptance-cost-probe.json](acceptance-cost-probe.json). Development seeds only. Mean processor
seconds per unit (small samples, run beside another job): one A0 per-event ephemeris 0.02; one A0
group ephemeris (the version-3 `odd_even`, with the shortcut's bootstrap) 0.74 (0.11 to 2.8); one
C1 curve through the paired chain of the v0.4 and version-3 batteries 89 (21 to 205), against 48
for the v0.5 battery's chain (`docs/validation/v0.5.1/wp5/reproduce-c1-prefix.json`).

## `period_alias` on the development control TIC-101395259 (#204, 2026-11-06)

**The data** ([fetch_dev_control.py](fetch_dev_control.py), [dev-control-fetch.json](dev-control-fetch.json)):
the maintainer's approval of 2026-11-06 (#208), light curves only, into `.cache/v051/dev/` (outside
git): 6 SPOC 120-s light-curve files (11491200 bytes), retrieved
2026-11-06T19:06:13Z from MAST through the frozen TESS adapter, no transient error; each file's URL
and SHA-256 are in the record, and all 6 are equal to the SHA-256 the v0.5 dossier
recorded (`TIC-101395259/data/manifest.json` in the Drive archive, read only).

**The diagnosis** ([alias_dev_control.py](alias_dev_control.py), [alias-dev-control.json](alias-dev-control.json)):
the v0.5 sensitivity simulation (50 sinusoids at the candidate's period, peak to trough equal to the
depth, the same seed) gives **43 of 50 failures as it is**, exactly the v0.5 dossier's value; with
the test's detrending replaced by the identity, **50 of 50**; with four harmonics in the Fourier
model instead of two, **50 of 50**; with the test's detrending window of one period instead of three,
**50 of 50**. So, on this control, the test prefers a box on a pure sinusoid because its own
detrending (a window of three periods, 22.7 days, longer than an orbit of 13 days) distorts a
large sinusoid (2,777 ppm semi-amplitude) into a shape that two harmonics do not absorb; it is not
a penalty for searched box parameters (amendment 1, item 3), and the synthetic check of 240 pure
sinusoids on two clean sectors did not show it. The acceptance section of WP3 (c) is written from
this (a design that absorbs the distortion, with both error sides accepted on the full chain).
