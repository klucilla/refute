# X2: is the predicted error inflated? (declaration, not run)

Prepared on 2026-10-21 at the maintainer's request (decisions after X0 and X1, item 4). **Not
authorized to run.** Its execution comes back to the maintainer with its size, seeds, affinity,
workers, cost and ceiling (section 7), and runs only after that authorization; this declaration is
committed before any realization exists, and its criteria do not change after.

## 1. The question

The capacity decisions stop a round when `S_pred = d_c / e_pred` is below the threshold, with
`e_pred,1` (from the train's replicas, with the margin `m_beta`) and `e_pred,2` (from the hidden
year's replicas). If `e_pred` is **larger than the true scatter** of the hidden-year depth, rounds
are stopped that could be decided. X2 separates three answers, with criteria fixed here:
- **correctly conservative:** `e_pred` above the true scatter by no more than its declared design
  (`e_pred,1`: the margin `m_beta`; `e_pred,2`: none);
- **really overestimated:** above the true scatter by more than its design, beyond the tolerance;
- **underestimated:** below the true scatter beyond the tolerance (the unsafe direction: it makes
  `S_pred` and `S_meas` too optimistic, which the false FAIL and false PASS can follow).

External precedent, not a method adopted: correlated noise can raise a transit detection threshold
well above the white-noise value ([sources/pont-zucker-queloz-2006.md](sources/pont-zucker-queloz-2006.md)),
so the AR(1) cells are tested, never assumed.

## 2. The design

- **Cells:** four, disjoint: white without variability, white with, AR(1) without, AR(1) with (the
  population harness's groups).
- **Cases:** 20 per cell, the constant scenario, planets of the bands near and measurable, taken in
  index order from a new prefix never used (`x2-1`), the first 20 of each group; no case is replaced
  after its realizations are seen.
- **Realizations:** 100 per case: the case's signal, star and sampling fixed, only the noise
  generator's seed changed (white and AR(1) parts both). The code that makes a realization is part
  of X2's execution package, with its own tests (the signal and the sampling identical across
  realizations, the noise different), written and accepted before the run.
- **Rounds:** every round of every realization, by `calibration_measurement` (the capacity
  decisions recorded, not enforced, so every round is measured where it can be), with the fields of
  X1 (`e_pred_1`, `e_pred_2`, `train_var_rep`, `hidden_var_rep`, `m_beta`, `n_pred`, the timing
  fields). The R_min of the records is the study's 8; the replica counts are kept for every R.
- **Seeds:** realization `j` of case `c` in cell `g` has the seed derived from the SHA-256 of
  `refute/v0.2.1/stage-1/X2/<g>/<c>/<j>` (the first 8 bytes, big-endian); the list of seeds is
  committed with the execution package before the run, and checked to share nothing with any seed or
  prefix used before (the lists of the R_min study, bs-choice and the earlier lots).

## 3. The quantities

For each case `c` and hidden year `y` (a case-year), over its realizations whose measurement is ok:
- `σ_emp(c, y)`: the scatter of `d_hidden`, with at least **30** measured realizations (fewer: the
  case-year is excluded and counted). **The standard deviation decides** (it is the quantity a
  predicted error stands for); the 1.4826 MAD is computed beside it as a check (revised before any
  data after Codex's review of the round: the two scales can differ widely on heavy tails, and the
  criteria below read one interval);
- `ρ_1 = median(e_pred,1) / σ_emp`, `ρ_2 = median(e_pred,2) / σ_emp`, `ρ_h = median(e_hidden) / σ_emp`;
- the pull `(d_hidden − d_twin) / e_hidden` over the realizations: its standard deviation and 1.4826
  MAD (1 if `e_hidden` is calibrated).

The cell's value of each ratio is the median over its case-years; its 95% interval by a cluster
bootstrap over the **cases** (all of a case's years resampled together), 2000 resamples, seed fixed
in the execution package. A cell needs at least 15 of its 20 cases contributing, otherwise its
verdict is `not determined`.

## 4. The criteria (fixed now)

With tolerance `τ = 0.10`, the design value `D` (`m_beta` for `ρ_1`, read from the plan; 1 for `ρ_2`
and `ρ_h`) and the cell's 95% interval `[lo, hi]`:
- `calibrated or conservative as designed` if `[lo, hi] ⊂ [(1 − τ)·D_low, (1 + τ)·D]`, where
  `D_low = 1` (an error between the true scatter and its design is accepted as designed);
- `overestimated` if `lo > (1 + τ)·D`;
- `underestimated` if `hi < 1 − τ`;
- `not determined` otherwise (the interval straddles a limit).

Reported for each ratio and cell, never merged; `underestimated` in any cell is reported first, as
a safety finding. **The scale's disagreement:** each ratio's verdict is computed with the standard
deviation (deciding) and with the MAD (the check); where the two verdicts differ, the cell's verdict
for that ratio is `not determined`, both are reported, and that cell's ratio does not count as
`calibrated or conservative as designed` for section 6 or for X3.

## 5. Reported apart, descriptive only

- The rounds stopped by decision 1 or 2 that would pass with `σ_emp` in place of `e_pred` (per cell),
  **without** any claim that this would be better: releasing a gate can bring new PASS and new FAIL
  (the maintainer's qualification of 2026-10-21, item 5).
- `ρ` by the number of observing years and by `n_pred`.
- The fraction of realizations whose round is measured, per cell.

## 6. What follows from the answer (fixed now)

- `calibrated or conservative as designed` in every cell: the error model stays; X3 calibrates `b`
  and `s` with it.
- `overestimated` or `underestimated` in some cell: a change of the error model is **proposed** (its
  own specification, tests and Codex review), and the instrumentation and X3's definitive calibration
  use the corrected model (the maintainer's order: X2 before X3's definitive calibration).
- `not determined`: reported; the size needed for a decision is computed and requested, never
  extended without authorization.

## 7. To be given with the request to run

The size (4 × 20 × 100 = 8000 curves, planning), the seeds (section 2), the affinity (processors 8
to 31), the workers (the project's default for that affinity, measured on this lot), the estimated
cost (≈ 4.7 h at 6 workers from the R_min study's 12.7 worker-seconds per curve; the gain of more
workers measured, not assumed) and a ceiling (the run stops at 1.5 times its estimate, and reports
what it has). Nothing of this is a validation of `R_min`, of B or of a configuration.
