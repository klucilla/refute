# v0.5.2 stage 2: the forecast's results and the maintainer's three paths (a STOP)

The maintainer's decision of 2026-11-10, second set (#216): with development seeds and data only, at most 25 CPU-h
for the whole forecast, (a) the T2a part, (b) the `odd_even` diagnosis, (c) the ratio of the box's error to the
Cramer-Rao bound split between A0 and the estimator; then a STOP with the results and the paths (i) to (iii), each
with its cost and risks. **Everything here is a forecast or a what-if on development data; it decides nothing.**
`method_status: not_validated`. The `planet_forecast` gate is failed in the ledger for D2 and now for T2a, and it
blocks the acceptance. Codex reviewed this record (forecast round 2, `WEAKENED`, 9 findings, all applied below).

## 1. Results

**Use.** The forecast used 13.7 CPU-h of its 25: D2/D4 4.85, the diagnosis 1.41, T2a 6.63 and its failed first
attempt 0.01, and three charged smokes 0.77 (one curve each for D2/D4 and the diagnosis, one injection above 20
sectors). Stage 2 has spent 176.8 CPU-h (`budgeted.spent`).

**D2 and D4** ([`forecast-v4.json`](forecast-v4.json), 112 eligible development planets): D2 kept v0.4 0.964,
version 3 0.839, version 4 **0.723** against the minimum 0.864 (FAIL); D4 INCONCLUSIVE 0.122 (PASS, at most 0.30).

**T2a** ([`forecast-t2a.json`](forecast-t2a.json)): 80 of the 615 recovered injections (40 in hosts of 2 to 4
sectors, 40 of 5 to 20), 0 errors, v0.4 reproduced on all 80 (no compatibility problem). The 56 injections above
20 sectors were not run: one takes 39 minutes, over the 30-minute batch, which an end-to-end timing smoke showed
before the main run (`4769684`). A and B lose them by the refusal rule, so for them they are known losses; v0.4
keeps them in its record; version 3 and C are unknown. Minimum: v0.4's exact 613/615 in the population minus 0.10 =
0.897.

| Battery | 2 to 4 kept | 5 to 20 kept | Estimate | Interval | Forecast |
|---|---|---|---|---|---|
| v0.4 (weighted sample; the population's 613/615 is the reference) | 39/40 | 40/40 | 0.988 | 0.876 to 0.998 | |
| Version 3 | 13/40 | 22/40 | 0.389 to 0.480 | 0.239 to 0.642 | FAIL |
| Version 4 A, as built | 11/40 | 0/40 | 0.135 | 0.067 to 0.276 | FAIL |
| Version 4 B, selector certified | 11/40 | 17/40 | 0.313 | 0.174 to 0.488 | FAIL |
| Version 4 C, B and the refusal lifted | 11/40 | 17/40 | 0.313 to 0.404 | 0.174 to 0.571 | FAIL |

For version 3 and C the estimate is partially identified: `forecast_t2a.py`'s summary prints the pessimistic end
(the unknown stratum lost) as its point, and the upper end counts it kept. The intervals are the stratified
hypergeometric ones (alpha 0.05 over the three strata) and already let every unknown outcome be kept; every one
ends below 0.897, so the FAIL does not depend on the stratum that was not run. The summary's rule "FAIL if the point
is below the minimum" could misclassify a case with missing outcomes in general; here it does not.

**What blocks T2a** ([`forecast_t2a_paths.py`](forecast_t2a_paths.py), [`forecast-t2a-paths.json`](forecast-t2a-paths.json)).
The main blocker is not `odd_even`: it is **`systematics` INCONCLUSIVE**, in version 3 as in version 4. Of version 4
B's 51 losses against v0.4, 48 carry it (23 of the class `insufficient_sensitivity`, 19 `not_enough_data` and 6
`outside_domain`, A0's comb refusal); it is the only blocker of 25 of them. `odd_even` INCONCLUSIVE is on 16 (never
alone), the sinusoid's on 15 (alone on 2). Version 3: 44 losses, 42 with `systematics` (20
`insufficient_sensitivity`, 22 `not_enough_data`), the only blocker of 28.

**`not_enough_data` is not established as a limit of the data.** In `battery_v51_diff.py` (`not_run_class`) it
gathers every sub-check that could not run for a reason other than a missing input or an unmeasurable error: too few
transits for the momentum-dump check (`min_events_for_dumps`), and "no transit measured" in the SAP or background
series, which A0's depth function (`a0_v4.py`) also returns when an empirical error is unavailable, a contributing
sector is outside the grid, or a group variance cannot be computed (version 3 conflates the same causes). The
records keep the class, not the message, so the split among these reasons is not known: part of it may be A0, not
the data.

T2a's kept fraction if sets of INCONCLUSIVE blockers were removed. A warning FAIL gives WEAKENED, which is kept; the
range sets the stratum above 20 all lost, then all kept (for B, all kept is a counterfactual extension: B loses
them by its rule). The ranges bound that stratum only; they carry no sampling uncertainty, and they are removals,
not estimators.

| Removed | Version 4 B | Version 3 |
|---|---|---|
| Nothing (as run) | 0.313 to 0.404 | 0.389 to 0.480 |
| `odd_even` | 0.313 to 0.404 | 0.389 to 0.480 |
| `odd_even` and the sinusoid | 0.334 to 0.425 | 0.389 to 0.480 |
| `systematics` of the class `insufficient_sensitivity` | 0.500 to 0.591 | 0.622 to 0.713 |
| `odd_even`, the sinusoid and `systematics`'s `insufficient_sensitivity` | 0.610 to 0.701 | 0.634 to 0.726 |
| Every INCONCLUSIVE of the class `insufficient_sensitivity` | 0.622 to 0.713 | 0.647 to 0.738 |
| `odd_even`, the sinusoid and all of `systematics` | 0.884 to 0.975 | 0.874 to 0.965 |
| Every INCONCLUSIVE | 0.909 to 1.000 | 0.899 to 0.990 |

Removing `outside_domain` (in the last two rows) is an oracle: it would need a prospective, validated extension of
A0's domain, not an estimator. In the row of `odd_even`, the sinusoid and all of `systematics`, reaching 0.897
needs about 14 % of the stratum above 20 kept for version 4 and 25 % for version 3, so the refusal above 20 would
have to be lifted. Codex's check (round 2, finding 2): even with `systematics`'s `not_enough_data` kept as it is, an
optimistic removal of every other INCONCLUSIVE gives version 4 an upper end of about 0.902, above the minimum. **So
the current battery is forecast to fail T2a, and `systematics`'s unresolved measurements need diagnosis; these 80
injections do not establish that T2a is out of reach.**

**The `odd_even` diagnosis** ([`forecast-v4-diagnosis.json`](forecast-v4-diagnosis.json),
[`forecast-v4-paths.json`](forecast-v4-paths.json), `289b491`): on the 17 planets turned from PASS to INCONCLUSIVE
by the sensitivity rule, version 4's A0 error over the Cramer-Rao bound is 1.49 (median; 1.25 to 1.90). Split by
the conditional linear-box error under the generator's covariance (`sigma_box_true`: the observed weights, events
and preprocessing held fixed, the generator's original covariance applied; detrending and the randomness of those
choices left out), A0 over it is 1.10 (1.00 to 1.41) and it over the bound 1.33 (1.18 to 1.53); passing controls
1.33, 1.08 and 1.21. These ratios are diagnostic comparisons: they mix the estimator's weights, the selection, the
preprocessing and the knowledge of nuisance parameters, and do not attribute exactly 10 % to A0 and 33 % to the
estimator. The Cramer-Rao error uses the true template and the full original data. The power reaches the rule's
threshold on 0 of 17 with A0's error, 7 with `sigma_box_true`, 16 with the Cramer-Rao error.

D2 if blockers were removed ([`forecast_v4_paths_r2.py`](forecast_v4_paths_r2.py),
[`forecast-v4-paths-r2.json`](forecast-v4-paths-r2.json), a new derived record; reading warning FAILs as kept changes
none of these):

| Removed | D2 kept (minimum 0.864) |
|---|---|
| Nothing (as forecast) | 0.723 (81/112) |
| `odd_even`'s sensitivity INCONCLUSIVE, bound-supported or all | 0.8125 (91/112) |
| The sinusoid's INCONCLUSIVE | 0.741 (83/112) |
| `odd_even` where the bound supports it, and the sinusoid | **0.884 (99/112), margin 0.020** |
| `odd_even` everywhere, and the sinusoid | 0.893 (100/112) |
| Every A0-dependent or sinusoid INCONCLUSIVE | 0.991 (111/112) |

## 2. The paths

The wall clock uses the rate measured in `budget.md`: about 9.8 CPU-h per hour over a week (12 workers off business
hours, 10 in them). The pause of 18 November at 20:00 is about 196 hours from 2026-11-10 16:00 BRT; the date of the
resume after it is the maintainer's, so no end date is given.

### (i) A design amendment inside v0.5.2: a calibrated, efficient `odd_even` estimator

**Options in the literature** ([sources](../../../plans/sources/v0.5.2-odd-even-estimators-2026-11-10.md), read
2026-11-10): a transit model fitted to odd and even transits separately (Kepler DV, Twicken et al. 2018; Li et al.
2019); LEO-Vetter's trapezoid or transit model with only the depth and T0 free and the shape fixed at the overall
fit (Kunimoto et al. 2025, which also reports fits whose uncertainties are unavailable); a correlated-noise
likelihood, wavelet (Carter and Winn 2009, with simulation evidence of better uncertainties under their assumed
noise processes) or Gaussian process (Aigrain and Foreman-Mackey 2023). These are candidates for investigation:
none supplies the calibration evidence Refute requires, and none validates Refute's odd/even statistic.

**What E2 already rejected** ([stage 1](../stage1/README.md), E2): `built`, `built_masked`, `candidate_shape`,
`crossfit`, `pseudo_ephemeris` and `box`. They fail the null cells (9 or 10 of 24 for `box`, `built_masked` and
`candidate_shape`, nearly all of the 0.20 d shape) and the power (7 or 8 of 12 alternative cells below 0.80);
`pseudo_ephemeris`'s scatter is 1.43 to 1.58 in correlated noise. E2 already tried fixed candidate templates, so a
fixed shape is not new by itself; what E2 did not try is a **joint correlated-noise likelihood** with the shape, the
timing, the estimation of the covariance and the covariance between odd and even depths treated explicitly.

**Predicted effect.** On D2, `odd_even` alone gives 0.8125 (FAIL); with the sinusoid's INCONCLUSIVE also gone,
0.884 where the bound supports it (margin 0.020), and the sinusoid's INCONCLUSIVE has not been diagnosed. On T2a,
`odd_even` and the sinusoid give 0.334 to 0.425 and adding `systematics`'s `insufficient_sensitivity` 0.610 to 0.701:
fails, unless `systematics`'s `not_enough_data` also resolves, whose causes are not known. These are optimistic
blocker removals, not the performance of a built estimator.

**Cost.** Developing and evaluating the estimator, frozen before evaluation like E2, and diagnosing the sinusoid's
INCONCLUSIVE and `systematics`'s: an unmeasured estimate of 20 to 60 CPU-h. A new estimator is a new family member,
so the null calibration, the known-answer gate and the adequacy check would be repriced from the prospective
estimator and its validation workload, not by a generic factor. As a scale only: the 2,979 CPU-h remaining in
`budget.md` plus 10 to 30 % gives **3,297 to 3,933 additional CPU-h, 3,474 to 4,110 in total** with the 176.8
spent, above the 3,100 maximum (the budget decision is open); the overlapping allocations would have to be
reconciled before a final total. Wall clock: about **14 to 17 days of compute**, plus development, plus the pause.
Agent-days: Claude's wall-clock bound since the delegation of 2026-11-08 is 6.1 of 12 (49.1 hours of the session
transcripts' wall clock over 8-hour days; active time with gaps capped at 10 minutes 1.8); Codex's time is not
counted in it.

**Risks.** The battery is forecast to fail T2a unless `systematics`'s unresolved measurements are fixed too; D2
passes only if the sinusoid's INCONCLUSIVE is resolved as well, by 0.020 on 112 development planets. A new estimator
may fail the 0.20 d null cells like E2's. The acceptance would end after the pause, on an open budget. v0.5.2 is
round 2 of 3: a failed acceptance leaves one round.

### (ii) Close v0.5.2 as not approved (round 2 of 3)

**Cost.** No further experiment CPU. About one day for the closing record, the ROADMAP tick and the independent
review the phase rule requires (a planning estimate; a reviewer session needs the maintainer's approval, and its
tokens and agent time count against their limits).

**Risks.** One round left. The 177 CPU-h of stage 2 are spent, but the results stand as records: version 4's A0
and its adequacy failure, the `odd_even` diagnosis, the T2a measurement, both failed gates. Round 3 is worth running
only if it starts from what blocks the targets: `systematics`'s unresolved measurements, the sinusoid's
INCONCLUSIVE and an efficient, calibrated `odd_even`, with T2a's target and the coverage requirement kept.

### (iii) An infeasibility record for D2

**The diagnosis does not establish an information limit, and does not support a D2 infeasibility finding.** At
the Cramer-Rao error, 16 of the 17 planets would reach the sensitivity rule's threshold; WP1's 98.9 % (v0.5.1) is
another information forecast of the same kind. Neither shows that an attainable estimator, with an estimated
covariance, a fitted ephemeris and nuisance parameters, and a valid uncertainty, would reach it.

**What would be missing.** A bound on the attainable testing performance under stated assumptions, mapped to
enough of D2's population to force its failure: for `odd_even`, and for the sinusoid's INCONCLUSIVE, which D2 also
needs removed and which no work has measured. An optimistic Cramer-Rao variance in a Gaussian power is not, alone,
a proof either way. A first sinusoid diagnostic would cost about 2 to 5 CPU-h and one or two days (an estimate);
the complete record is unpriced. An infeasibility record is the maintainer's (a non-delegated stop).

## 3. Recommendations

**Claude's: path (ii).** Path (i) as scoped is forecast to fail D2 (0.8125) and T2a (0.31 to 0.43); widened to the
sinusoid and `systematics`'s sensitivity it still fails T2a, at more than 3,100 CPU-h and weeks of wall clock, with
no integrated, calibrated estimator yet. Path (iii) has no evidence of a real limit. Closing records the findings;
round 3 should start by diagnosing `systematics`'s `not_enough_data` causes and the sinusoid's INCONCLUSIVE, then an
efficient, calibrated `odd_even`.

**Codex's: path (ii)** ([answer](../../../plans/v0.5.2-consensus/forecast-t2a-round-2-answer.md)): close as not
approved, without declaring D2 or T2a infeasible; path (i) lacks an integrated, calibrated solution and an approved
budget, path (iii) the impossibility evidence; before the remaining round, diagnose the unresolved `systematics`
causes, keeping the target and the coverage requirement.

## What this does not establish

These are forecasts on development data with small samples (112 planets, 80 injections), and the what-ifs remove
blockers without designing anything: a real estimator would remove fewer. Costs marked as estimates have no
measurement behind them. Nothing here says that version 4, or any battery, is calibrated.
