# v0.2.1 correlated noise for the changes already made: acceptance criteria

Status: **criteria fixed before the generator, the reference and the tests.** This file is
committed on its own, before the tests and the code it describes. Written 2026-10-17 on
branch `claude/v0-2-1-reopen` (Phase I). Design reviewed with Codex (read-only, logical
processors 0 to 7) on 2026-10-17; its objections are incorporated below.

## Why, and what this file is not

The first exit criterion of v0.2.1 (ROADMAP.md, "v0.2.1 Gauntlet fixes", Exit criteria)
reads: "Every change has acceptance criteria, metrics and regression cases committed before
its tests and code, and synthetic cases that must pass and must fail, including correlated
noise." The audit of the reopening (`audit-criteria-1-4-5.md`) found that **none** of the
acceptance records of the changes already made has a correlated-noise case, and that the
generator of the test suite (`make_lightcurve` in `src/refute/packs/tess/synthetic.py`) makes
white noise only. Correlated noise exists only in the population harness
(`../population/population_v2.py`, `_noise`) and in the H3 measurement
(`../H3/measure.py`).

This file is a **prospective extension of coverage**. It does not make the correlated-noise
criteria retroactively earlier than the code of those changes: the historical absence is
recorded here and in the audit. Whether this regularization satisfies the historical reading
of the criterion is the maintainer's decision.

The synthetic scenes are idealized (ROADMAP.md, v0.2.1, Scope): the AR(1) model below is a
synthetic scenario comparable with the population study, not a model validated on TESS data.

## Changes covered

| Change | Record | Correlated cases | Why |
|---|---|---|---|
| H7 (signal identity) | `../H7-acceptance.md` | yes (section H7) | |
| H4 (train validity) | `../H4-acceptance.md` | yes (section H4) | |
| H9(a) (own-TIC catalog match) | `../H9a-acceptance.md` | yes (section H9) | |
| workers equivalence | `../workers-equivalence-acceptance.md` | yes (section W) | |
| CI option D | `../ci-time-option-d-acceptance.md` | yes (section D), after commit 3b | |
| #23 (report wording) | `issue-23-acceptance.md` | yes (section R) | |
| #32 (`init_worker` environment) | issue #32, `tests/test_runner.py` | **no** | its contract is that the environment is restored, also after an exception; it decides nothing about data, so the noise model does not reach it |
| H3 (timing floor) | `../H3-acceptance.md` | **no** | option A was abandoned; no implementation was accepted; its measurement already had red-noise cells |
| the generator itself | this file | section G | |

## G. The generator

### Definition

- `make_lightcurve` gains two keyword parameters: `red_noise_ppm: float = 0.0` and
  `red_tau_days: float = 1/24`.
- With `red_noise_ppm == 0` **nothing changes**: no new generator is created and the current
  arithmetic path is kept, so every existing scenario is byte-identical.
- With `red_noise_ppm > 0`: a second generator `np.random.default_rng([seed, 1])`, created
  once per call, gives, for each sector in order, a stationary AR(1) series with standard
  deviation `a = red_noise_ppm * 1e-6`: `x[0] ~ N(0, a)`, `x[i] = phi[i] x[i-1] +
  a sqrt(1 - phi[i]^2) e[i]`, `phi[i] = exp(-(t[i] - t[i-1]) / red_tau_days)` with the real
  time differences of that sector (orbit gaps included), the state started again in each
  sector. It is the model of the population harness (`_noise` in `population_v2.py`). The
  series is added to the flux after the white noise. The white noise draws of
  `np.random.default_rng(seed)` are unchanged, so a correlated light curve is the white one of
  the same seed plus the AR(1) series.
- `flux_err` stays the white sigma: the pipeline is not told about the red component.
- `make_blend` gains the same two parameters and passes them to its `make_lightcurve` call;
  the target series it renders into the pixels is that light curve, so the light curve, the
  pixels and the auxiliary columns stay coherent.
- `scenario_data(name, seed, noise="white")` gains `noise`: `"white"` (default, unchanged) or
  `"correlated"`, the **correlated profile**: 600 ppm white (the scenarios' value) plus 600 ppm
  AR(1) with `tau` = 1 hour, applied to every scenario, `blend` and `sinusoid` included.
  The noise-only replacement of `replace_year_flux` (blindness tests) is not changed.
- The analysis helpers carry the mode: `analyze_scenario_seed` accepts `(name, seed)` as
  today or `(name, seed, noise)`; `analyze_scenario_with_catalog` reads `task["noise"]`
  (default `"white"`).

### Reference of the old generator

After this file is committed and **before** the generator is changed, a script
(`correlated/white_reference.py`) computes, with the current code, a SHA-256 digest of every
array of `scenario_data(name, seed)` (light curve, sectors, star, pixels and auxiliary
columns, in a fixed order) for every scenario of `SCENARIOS` plus `fp_variability_dominates`
and `variability_train_only`, seeds 0, 1 and 2, and writes `correlated/white-reference.json`.
That file is committed on its own. Comparing the two modes of the new code alone would not
catch a regression common to both.

### Cases (`tests/test_synthetic_correlated_noise.py`)

- G1. With the default mode, every digest equals `white-reference.json` (13 scenarios x 3
  seeds).
- G2. For `planet`, seeds 0 to 2: the correlated flux minus the white flux of the same seed
  equals, to 1e-12, an AR(1) series computed in the test by its own implementation of the
  definition above (from `np.random.default_rng([seed, 1])`, sector by sector, state started
  again in each sector); the times and sectors are those of the white curve.
- G2b (sanity). Over the cadences of each case of G2, the sample standard deviation of that
  difference is within 10% of 600 ppm, and its lag-one sample autocorrelation over consecutive
  cadences of the same orbit is within 0.02 of `exp(-120 s / 1 h)` (0.9672); the series differ
  between seeds.
- G3. `flux_err` is identical in the two modes.
- G4. `blend`, correlated, seed 0: the light curve equals the crowding-corrected aperture
  photometry recomputed from its own pixels (as `make_blend` defines it), to 1e-12.
- G5. `make_lightcurve` with `red_noise_ppm=0` does not call `np.random.default_rng` a second
  time (checked by wrapping it).

## Seeds and the confirmation set

The correlated cases use the development seeds of the suite (0 to 9, with the subsets below),
with the separate stream `[seed, 1]`. They are distinct from the population seeds (prefix
`refute-v0.2.1-population-dev`) and from the confirmation set, which is not generated and not
used. No known target and no real data are used.

## Two kinds of case

- **Mechanism cases** test the change itself and must pass in any noise model (invariants,
  and outcomes the change decides). A failure is a defect of the change.
- **Expectation cases** depend on what the rest of the engine does with correlated noise (a
  premise such as "the search finds the injected period", or a verdict). Each expectation has
  its own test function, separate from the mechanism test that uses it.

Every mechanism case is conditional on its premise where it needs one: it is evaluated on the
seeds where the premise holds, and it must be **non-empty** (the premise holds on at least one
of its seeds), so that it cannot pass by never looking.

**If an expectation case fails:** the case, its numbers and its expectation are kept; the
failure is recorded in an amendment of this file with the numbers; the correlated acceptance
of that change is **pending** (criterion 1 is not met for it) until it is resolved. A cause
is attributed to the TESS corrections (M4, M5) only with evidence; until then the record says
"suspected association". To keep CI green, only that expectation function may be marked
`xfail(strict=True, raises=AssertionError)`, after the amendment and citing it; never a
mechanism case, never a whole module. A mechanism case that fails is fixed in the code of the
change, or the change is reopened.

## H7. Signal identity (in `tests/test_calibration_signal_identity_e2e.py`)

Correlated profile, fast test plan, `build_result`, then `TessCalibrator.evaluate`, flag on
and off, seeds 0 to 2 (as the white end-to-end cases).

- H7-M1 (mechanism, B5 in correlated noise). `planet` and `planet_three_years`: `recovered`
  and `refuted planets` identical with the flag on and off.
- H7-M2 (mechanism, A11 on real analyses). Over the results of every case of this section:
  flagged with H7 equals flagged without H7 minus the false positives whose signal is not
  recovered, and the denominator is the same.
- H7-M3 (mechanism, B1). `fp_variability_dominates`: on the seeds where the search found a
  period that is not P, 2P or P/2 of the eclipse (premise), `signal_recovered` is false and
  the target is not flagged, whatever its verdict. Non-empty.
- H7-M4 (mechanism, B3). `eb_secondary` and `eb_odd_even` with the correct published period:
  on the seeds where the found period matches the injected one (premise), the flag on and the
  flag off give the same flagged status. Non-empty.
- H7-E1 (expectation). The premise of H7-M3 holds on every seed.
- H7-E2 (expectation). The premise of H7-M4 holds on every seed, and those targets are
  `REFUTED` and flagged.

## H4. Train validity (in `tests/test_holdout_train_validity_e2e.py`)

Correlated profile, guard on and off (`require_valid_train`).

- H4-M1 (mechanism, D1 and D2). Every existing scenario plus `fp_variability_dominates` and
  `variability_train_only`, seeds 0 to 4: per round, the status with the guard is the status
  without it or INCONCLUSIVE; `holdout_by_year` FAIL with the guard implies FAIL without it.
- H4-M2 (mechanism, B1). `variability_train_only`, round hiding 2020, seeds 0 to 4: on the
  seeds where, with the guard off, the train candidate is at 0.7 d (within 1%) (premise), the
  guard-on round is INCONCLUSIVE with reason (b) among its reasons, decided before the hidden
  year is read (empty access log). Non-empty.
- H4-M3 (mechanism, B4). `sinusoid` and `fp_variability_dominates`, seeds 0 to 4: every round
  whose guard-off train has duration/period above 0.2 is INCONCLUSIVE with reason (b) with the
  guard on, with an empty access log. Non-empty in each scenario.
- H4-M4 (mechanism, B6, the negative control). `vanishing`, round hiding 2020, seeds 0 to 9:
  every round that FAILs with the guard off and has no train-validity reason stays FAIL, with
  no reason, with the guard on. Non-empty.
- H4-M5 (mechanism, C1 blindness). `planet` and `vanishing`, seeds 0 to 2, each round: with
  the hidden year's flux replaced by the three variants of `replace_year_flux`, everything
  decided before the hidden windows are read is byte-identical to the original (as C1 of the
  H4 record), and rounds decided before the read are identical with an empty access log.
- H4-E1 (expectation, B5). `planet` and `planet_three_years`, seeds 0 to 4: no reason in any
  round, and every round status identical with the guard on and off.
- H4-E2 (expectation, D3). Over H4-M1: reasons appear only in `noise`, `vanishing`,
  `sinusoid`, `fp_variability_dominates` and `variability_train_only`; in `noise` and
  `vanishing` only on rounds that are INCONCLUSIVE without the guard.
- H4-E3 (expectation). The premises of H4-M2 and H4-M4 hold on every seed listed.

## H9. Own-TIC catalog match (in `tests/test_ebcatalog_own_tic_e2e.py`)

Correlated profile, a synthetic catalog as in the H9(a) record, switch on (default) and off
(`same_photometry_catalogs: []`). After option D is complete (section D), the switch-off
analyses come from the shared path, with complete controls on seeds 0 and 1.

- H9-M1 (mechanism, D1 and D2). Every scenario of the H9(a) module, seeds 0 to 4, with a
  TESS-EB row under the target's TIC at the scenario's period: REFUTED with the default implies
  REFUTED with the switch off; the two test lists are identical except, possibly, the severity
  of `eb_catalog` (fatal to warning); the verdict changes only when `eb_catalog` was the only
  fatal failure, and then it is never SURVIVED.
- H9-M2 (mechanism, B1). `planet` with the own-TIC row at 3.7 d, seeds 0 to 4: on the seeds
  where, with the switch off, the verdict is REFUTED with `eb_catalog` the only fatal failure
  (premise), the default gives a verdict other than REFUTED and SURVIVED, `eb_catalog` FAIL with
  severity warning and `downgraded: true`, and the report holds the downgrade sentence.
  Non-empty.
- H9-M3 (mechanism, B3, the negative control). `blend` with a TESS-EB row under the
  neighbor's TIC at the neighbor's period (2.3 d), seeds 0 to 4: on the seeds where the found
  period matches 2.3 d (premise), `eb_catalog` is a fatal FAIL with the default and the verdict
  is REFUTED. Non-empty.
- H9-E1 (expectation). The premises of H9-M2 and H9-M3 hold on every seed.
- H9-E2 (expectation, B2). `eb_secondary` and `eb_odd_even` with the own-TIC row at their
  period, seeds 0 to 4: REFUTED with the switch on and off.

## W. Workers equivalence (in `tests/test_workers_equivalence.py`)

- W-M1 (mechanism). A fourth target, `TIC-14`, scenario `planet` in the correlated profile,
  seed 0, role planet, joins the claim of the test (four targets; `--workers 4` for O). Level
  (a) of the workers record holds for it as for the other three (F, F4 and R14 against O), and
  the full-run summaries of F and F4 equal O's. The premises of the record (E0) are checked
  per target key, not by unpacking a fixed number of targets.
- W-E1 (expectation). In O, `TIC-14`'s blind holdout has at least one round that read the
  hidden year (a non-empty access log), so that the equivalence covers a round that reads.

## D. CI option D, after commit 3b (in `tests/test_ebcatalog_own_tic_e2e.py`)

- D-M1 (mechanism, E1). For `planet` and `eb_secondary` in the correlated profile, seeds 0 and
  1, the derived switch-off analysis equals the complete switch-off analysis, byte for byte, as
  E1 of the option D record (the verdict record and the gauntlet test lists).
- D-E1 (expectation, the E1 premise). `planet`, correlated, seeds 0 and 1: the derived
  switch-off verdict differs from the default one (switch off REFUTED with `eb_catalog` fatal;
  default WEAKENED with `eb_catalog` a warning).

## R. Report wording, #23 (in `tests/test_holdout_report_wording.py`)

- R-M1 (mechanism). B1 of the #23 record on the 2020 year of `planet` in the correlated
  profile, seed 2: every hidden cadence reaches the detrending, the mask covers only the
  registered windows, and the access log is empty after construction.

## Planned sabotages (after the code passes; never committed)

| Sabotage | Must be caught by |
|---|---|
| SG1. The AR(1) series drawn from the white generator (the white stream shifts in the correlated mode) | G2 |
| SG2. The AR(1) state not restarted per sector | G2 |
| SG3. `scenario_data` ignores `noise` for `blend` | G4 |
| SG4. `red_noise_ppm=0` still creates the second generator | G5 |
| SH4. The guard of H4 always reports a valid train (S1 of the H4 record) | H4-M2, H4-M3 |
| SH9. Own-TIC rows stay fatal (S1 of the H9(a) record) | H9-M2 |
| SH7. H7 ignores the flag | H7-M2 |

## Cost and CI

The correlated cases add complete analyses: H7 about 30, H4 about 2 x 13 x 5 plus the
blindness replacements, H9 about 13 x 5 (plus controls), W four executions of one more target,
D 4 complete controls. They are placed in the heavy shards of `scripts/ci_shard.py`; a new
shard is added only if the measured job time of a CI run exceeds 15 minutes. The time is
measured and recorded, never assumed.

## Effect on locks

The generator and the helpers are under `src/`, so the code hash changes, as for every v0.2.1
change. No locked claim uses the synthetic generator; the v0.2 calibration is verified at its
locked tag `v0.2.0-calibration-lock`.

## Amendment 1 (2026-10-17): the generator, its sabotages and one wording correction

**Order.** This file `b8371d6`; the reference of the old generator `ff5d7d4` (two runs, identical
digests); the tests `9922198` (before the code: 52 tests, 11 failures, every case that needs the
new mode); the code `0cc8063` (52 passed, 0 failures, from the JUnit file).

**Sabotages SG1 to SG4**, against `tests/test_synthetic_correlated_noise.py` only, the
implementation staged, each file restored from the index with an empty `git diff`; nothing
committed:

| Sabotage | Failing cases | Planned and caught |
|---|---|---|
| SG1. The AR(1) series drawn from the white generator | G2 (3 seeds), G2b (3 seeds), G5 correlated | yes |
| SG2. The AR(1) state not restarted per sector (the last value of a sector carried into the next) | G2 (3 seeds) | yes |
| SG3. `scenario_data` ignores the noise mode for `blend` | G4 | yes |
| SG4. The white mode creates the second generator | G5 white | yes |

**Wording correction (no criterion changes).** The definition said the correlated profile is
"600 ppm white (the scenarios' value) plus 600 ppm AR(1)". The white noise is each scenario's
own value, unchanged: 600 ppm for every scenario except `blend`, whose `make_blend` uses
300 ppm (as before). The profile adds the 600 ppm AR(1) to that white noise; the code
(`CORRELATED_PROFILE` in `synthetic.py`) and G4 follow this, and nothing else was assumed.

## Amendment 2 (2026-10-17, before the tests of the changes): the maintainer's decision, and two definitions

**The maintainer's decision (2026-10-17).** Exit criterion 1 is **accepted as a prospective
regularization, with an explicit historical exception**. On the record:

- (a) **The historical absence.** The changes H7, H4, H9(a), workers equivalence and CI option D
  were accepted (their records, tests and code, 2026-10-10 and 2026-10-11) **without** any
  correlated-noise case; these cases were added on 2026-10-17, by this file.
- (b) **The decision.** The maintainer accepts this prospective regularization as the way to meet
  criterion 1 for those changes.
- (c) **The order.** The criteria of this file were committed (`b8371d6`, this amendment) before the
  respective tests and code; the git history shows it.
- (d) **The results**, complete, including every expectation that keeps failing, are recorded in a
  later amendment, with the numbers. An `xfail` keeps a pending item visible; it **does not**
  satisfy the acceptance: a change whose correlated expectation fails stays pending under
  criterion 1.

The AR(1) component is a **synthetic scenario of correlated noise**, comparable with the population
study; it is never presented as a validated reproduction of the real noise of TESS data.

**Two definitions made before the tests.**

1. **The holdout helper carries the mode too.** `holdout_scenario_seed` (the helper of the H4 and
   blindness tests, which runs the blind holdout alone) reads `task["noise"]` (default `"white"`),
   like the two analysis helpers named in section G. Without it the H4 cases could not run in the
   correlated profile.
2. **Where H4-M5 lives.** H4-M5 (blindness in the correlated profile) is placed in
   `tests/test_holdout_blindness.py`, beside C1 of the H4 record whose helpers it uses, not in
   `tests/test_holdout_train_validity_e2e.py`. Its definition does not change.
