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

## The D1 route search for the folded binaries (amendment 10, item 3, 2026-11-07)

Script: [d1_routes.py](d1_routes.py) (commits `82574e6`, `4b058f8`); output:
[d1-routes.json](d1-routes.json). Development data only (the WP1 forecast's records and seeds,
new seeds `refute-v051-dev:route-<family>:<i>`). **12.04 processor-hours, above the 10 approved
(1.2 times; under the 1.5-times stop).** It decides nothing. Codex's two rounds:
`docs/plans/v0.5.1-consensus/d1-routes-round-*-answer.md`.

**(a) Where the separation is.** The WP1 oracle (the nearest planet at the found period; survival
`1 - Phi(d - 1.645)` from the Mahalanobis distance of noiseless curves: an optimistic proxy, not a
measured count), repeated with the star's parameters known or free within 3 sigma, scaled to C1'
(194 EB1 and 186 EB2 eligible):

| The star | EB1 | EB2 |
|---|---|---|
| radius known | 2.0 | 4.1 |
| radius 2.5 % | 2.9 | 6.0 |
| radius 5 % (the WP1 forecast; the mass held fixed) | 4.6 | 7.9 |
| radius known, mass 5 % | 2.7 | 5.5 |
| radius 2.5 %, mass 2.5 % | 3.4 | 6.6 |
| **radius 5 %, mass 5 % (the generator's TIC errors)** | **7.6** | **12.3** |
| radius 10 %, mass 10 % | 9.1 | 15.2 |

The separation is the transit duration and geometry against the star's density, and the TIC's
radius and mass errors remove much of it: under this oracle proxy, with both errors, EB2's
forecast is above D1's allowance (about 10 at 186 eligible). The WP1 forecast was optimistic: it
held the mass fixed. This is a forecast under the oracle proxy, not a proof; D1 is decided by
C1'.

**(b) Routes unavailable on C1** (the frozen generator, `calib05.c1.generate`): ellipsoidal
variation, Doppler beaming and reflection are not generated (BEER, Faigler and Mazeh 2011,
https://arxiv.org/abs/1106.2713, read 2026-11-07, applies to real data only); both eclipses share
their duration and ingress fraction, so no eclipse-shape asymmetry exists; the catalog star is
fixed in the generator (radius and mass 1.0 +- 0.05), so better stellar parameters (Gaia DR3) cannot
move D1 on C1 (on real data they would bring a third-party input: its licence, a DATA_LICENSE and a
sources record).

**(c) The transit-geometry consistency with a real estimator** (a physical planet at the found
period with the TIC radius and mass under Gaussian priors, against a free trapezoid, both fitted
in white weights; `dchi2`, and `dchi2_cov` the same residuals **re-scored** under the generator's
covariance, not fitted with it; Seager and Mallen-Ornelas 2003, https://arxiv.org/abs/astro-ph/0206228,
read 2026-11-07). Flag fractions among the eligible curves; both thresholds exploratory (9 has no
calibrated meaning; the planets' pooled 99.73 % quantile rests on about one tail observation):

| Group | At `dchi2 >= 9` | At the planets' 99.73 % quantile |
|---|---|---|
| EB1 (white / correlated) | 0.37 / 0.56 | 0 / 0 |
| EB2 | 0.48 / 0.79 | 0 / 1 of 75 |
| P (planets) | 0.016 / 0.027 | 0 / 1 of 73 |
| PG (grazing planets) | **0.305** / 0.057 | 0 / 0 (`dchi2_cov`: 1 of 59 white) |

The grazing planets' tail (white PG, 90th percentile 64) is unexplained (the records keep neither
the true impact parameter nor fit diagnostics); the C1 planets share the generator's model, so even
these rates are optimistic for real planets (limb darkening, eccentricity: Dawson and Johnson 2012,
https://arxiv.org/abs/1203.5537, read 2026-11-07, cited by Codex).

**Reading (Claude and Codex).** No new decisive test can be justified in v0.5.1 from this
evidence; D1 for EB1 and EB2 stays measured in C1' and reported; if it fails, the joint
infeasibility path with D2 (amendment 4, item 2) may cite (a) as supporting forecast evidence, not
proof. The geometry consistency is a candidate for a later round (Codex: as a non-fatal diagnostic
pending calibration; Claude: recorded only, since a new diagnostic needs the maintainer's
approval), with its prerequisites: the grazing tail explained, covariance-aware fitting and a
full-chain calibration with enough tail evidence, limb-darkening and eccentricity stress cases, a
real-planet false-flag check. No other route is measured in this round (the budget is spent).

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
