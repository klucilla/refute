# X2: geometry and identity (X2-A), and the calibration of the uncertainties (X2-B)

**Revision 2**, 2026-10-21, before any realization exists (the maintainer's decision after X0c and
X1b, item 3). Revision 1 (`5a657fb`, with the corrections of `acc9dda`) asked only X2-B's question.
**Not authorized to run:** the execution package ([x2-execution-package.md](x2-execution-package.md))
goes to the maintainer, and the lot runs only after that authorization. Once this revision is
committed, its metrics, rules and criteria do not change; anything else computed is written apart,
as exploratory. Development evidence, not validation: X2 validates no `R_min`, no specification and
no configuration.

## 1. The questions

**X2-A, geometry and identity.** X0c found the constant scenario's false FAIL dominated by the train
against the windows measured (`Z_train`), with the twin's depth far below the train's, and
identified no cause. X2-A separates, round by round, four causes: **a wrong candidate**, **an
imprecise extrapolation** of the ephemeris into the hidden year, **an attenuation in the
processing** (the twin keeps the model's variability and trend, is measured with the trend fitted
to the noisy curve, and depends on the masks, the detrending and the fit), and **an inflated train
depth**; and it measures how often each happens across noise realizations of the same case.

**X2-B, the calibration of the uncertainties** (the original question). Is the predicted error
`e_pred` (`e_pred,1` from the train's replicas with the margin `m_beta`, `e_pred,2` from the hidden
year's) **correctly conservative** (above the true scatter by no more than its design), **really
overestimated**, or **underestimated** (the unsafe direction), against the scatter of the hidden
depth over repeated noise realizations, decided by the standard deviation?

## 2. The information contract

- The synthetic truth (the injected period, epoch, duration, depth, impact, ingress fraction) is the
  **evaluator's only**: made before the engine's calls, held in a guarded mapping that refuses every
  read during them (`rmin_study.EvaluatorTruth`, X1), and attached to the record after them. The
  engine receives the light curve and its metadata, as in every lot.
- **No identity gate is implemented and no new reference is given to the engine** (the maintainer's
  decision, item 4). X2-A **diagnoses** identity on the evaluator's side only. The train candidate
  is never compared with the global search's candidate (that search may have used the hidden year;
  the holdout's tests require independence from the global candidate). A truly independent external
  ephemeris would be another information contract, close to the directed mode, with its own
  specification and validation; it is not part of X2.
- No threshold or gate changes because of X2's answer alone; a change is proposed with its own
  specification, tests and review (section 8).

## 3. The design

- **Cells:** four, disjoint: white without variability, white with, AR(1) without, AR(1) with.
- **Cases:** from the new prefix `refute-v0.2.1-x2-1` (never used), the planets of the bands near and
  measurable; per group, the cases ordered by band (near, then measurable) and index, every
  `n // 20`-th, the first 20. In the groups without variability this gives, per band, 5 `two_years`,
  3 `three_years`, 2 `few_train`; in the groups with variability, 20 `variability_some_years`. No
  case is replaced after its realizations are seen.
- **Realizations:** 100 per case, `j = 0 … 99`: the case exactly as the population harness builds
  it (its parameters, sampling, model and auxiliary data), its noise drawn again, sector by sector
  in time order exactly as the harness draws it, from the realization's seed. With the case's own
  noise seed the realization is the case byte for byte (tested).
- **Seeds:** realization `j` of case `c` in group `g`: the first 8 bytes, big-endian, of the SHA-256
  of `refute/v0.2.1/stage-1/X2/<g>/<c>/<j>`; the 8000 seeds are listed in the execution package and
  checked there against the seeds of the earlier lots.
- **Rounds:** every observing year of every realization, by `calibration_measurement` on the study's
  M4 configuration (`m4-configurations/rmin-study.json`: `r_min` 8, the capacity decisions recorded,
  not enforced, so every round is measured where it can be), with the noiseless twin and X1's fields.
- **Nothing is discarded:** every realization and every round stays in the records and in the
  denominators; a round with a wrong candidate, an unmeasured round or a twin unavailable is counted
  in its class.

## 4. The record (one file per realization)

The case, the group, the mechanism, the band, `j`, the seed, the observing years, the sectors
(number, year, start, end), the configuration's identity, every round's calibration record (with X1's
fields: `train_ephemeris`, `train_duration_days`, `max_timing_sigma_days`, `n_transit_times`,
`n_pred`, `grid_dp`, `d_c`, `m_beta`, `train_var_rep`, `e_pred_1`, `hidden_var_rep`, `e_pred_2`), the
**registered windows** of each round, and the evaluator's truth attached after the engine's calls.
The registered windows (each transit and control window and its replicas: kind, epoch, predicted
time, half-width, the inner and outer edges of its baseline band) are what the engine registers for
the hidden year: its masks, bands and boxes. They are recomputed on the evaluator's side, after the
engine's calls, with the engine's own functions (`plan_round`, `register_replicas`) from the train
data and the hidden sectors' spans only, and the round's recorded train ephemeris must equal the
recomputed one exactly, or the record is refused; `None` for a round that stops before its windows
exist. (Added before any realization, after Codex's review of the package: the calibration record
alone does not let the per-epoch widths and the replicas be rebuilt.)

## 5. X2-A: the metrics and the rules (fixed now)

Computed by the evaluator, per round with a train ephemeris (`train_ephemeris` present), from the
record, the truth and the case's cadences (rebuilt from the case's layout, without noise). Notation:
`P`, `t_ref`, `n_ref` the train ephemeris; `D` the train duration; `dP` the period correction the
measurement chose (0 when the round was not measured); `P*`, `t0*`, `D*`, `δ*` the injected period,
epoch, duration and depth; `span` the curve's time span (last sector's end minus first sector's
start); the hidden spans, the hidden year's sectors.

1. **Identity of the candidate.** `q = P / P*`; the tolerance `ε = D* / (2·span)` (the period error
   that moves a transit by half a duration over the whole curve). The class: `same` if
   `|q − 1| ≤ ε`; `alias ×k` if `|q / k − 1| ≤ ε` for `k` in 2, 3, 1/2, 1/3 (in that order);
   `other` otherwise.
2. **The windows in the hidden year**, the registered ones (section 4): the transit windows' epochs
   `m` and predicted times `t_pred`; the measurement's centers `t_pred + (m − n_ref)·dP`; the box
   half-width `D / 2`; the masks of **every** registered window (transit, control and replica) out to
   the inner edge of its baseline band; the transit windows' baseline bands. A round whose windows
   were not registered keeps 5.1, 5.3 and 5.5 (its centers from the ephemeris, `t_ref + m·(P + dP)`)
   and has no overlap (5.4).
3. **Offsets:** for each measurement center, the signed offset to the nearest injected transit center
   `t0* + n·P*` inside the hidden spans; reported as the largest absolute offset and the mean offset,
   in units of `D*` and of `σ_T,max` (the round's `max_timing_sigma_days`).
4. **Overlap with the injected transits,** on the hidden year's cadences (rebuilt from the case's
   layout, without noise) inside the injected transits (`|t − (t0* + n·P*)| ≤ D*/2`): the fraction
   inside a measurement box; inside a transit window's baseline band; and **outside every registered
   mask** (an injected transit the detrending fits as baseline).
5. **Depths against the injected one,** never only against each other: `d_train / δ*`, `d_twin / δ*`,
   `d_hidden / δ*`; and the box references from the injected signal model without noise, trend or
   variability (`1 − signal_model`): `b_true`, its mean in boxes of half-width `D / 2` centered on
   the injected transits of the hidden year; `b_pred`, its mean in the boxes actually measured
   (the predicted centers). Then `d_twin / d_train` splits exactly into three factors:
   `(b_true / d_train) · (b_pred / b_true) · (d_twin / b_pred)`: **the train's inflation**
   `I = d_train / b_true`, **the placement** `L = b_pred / b_true`, **the processing** `A = d_twin / b_pred`.
6. **The cause of a round** (in this order, the first that holds; **every** round gets one):
   - `twin unavailable` if the round has no train ephemeris, was not measured, or the twin's
     measurement failed;
   - `wrong candidate` if the identity is not `same`;
   - otherwise the factor with the largest reduction of `d_twin / d_train`, among the train's
     inflation (`log I` if `I > 1`), the placement (`−log L` if `0 < L < 1`) and the processing
     (`−log A` if `0 < A < 1`), with `L ≤ 0` counted as the placement's complete loss and `A ≤ 0` as
     the processing's (if both are `≤ 0`, the placement); named `inflated train depth`, `imprecise
     extrapolation`, `attenuation in the processing`;
   - `none` if no factor reduces the ratio by more than 20% (`I ≤ 1.25`, `L ≥ 0.8`, `A ≥ 0.8`), or
     if the factors are undefined;
   - a tie between factors goes to the first in the order inflated, extrapolation, processing.
   Each factor and each flag (identity, offsets above `D*/2` and above `3·σ_T,max`, the overlap
   fractions) is reported on its own as well, never only the class.
7. **Reported, per cell and by layout** (mechanism, number of years): the classes over all rounds,
   over the rounds with `Z_train ≥ 3` (`Z_train = (d_train − d_twin) / sqrt(e_train² + e_hidden²)`,
   as X0c), and over the FAIL rounds (in the constant scenario a FAIL is false; a FAIL here is the
   FAIL rule, `holdout.fail_rule`, on the round's measurement with `min_snr` 5, **the capacity
   decisions not enforced**, as `calibration_measurement` records them), each with its denominator; per case-year, how often across the 100 realizations each class occurs, how often
   the identity differs from the case-year's most frequent one, and the scatter of the predicted
   centers (the standard deviation of the mean offset). No rate is claimed beyond these cells.

## 6. X2-B: the quantities and the criteria (fixed now)

Per case `c` and hidden year `y` (a case-year), over all its realizations whose measurement is ok,
**whatever their X2-A class** (the subset with `same` and `L ≥ 0.8` is reported apart, not deciding):

- **The measurement's scatter, separated from the signal's:** `σ_meas` = the standard deviation of
  `d_hidden − d_twin` (the hidden measurement against the noiseless signal at the same windows and
  `dP`), **deciding**; the 1.4826 MAD of the same, the check; `σ_tot` = the standard deviation of
  `d_hidden` and `σ_sig` = that of `d_twin` (the change of the signal actually measured, when the
  candidate or the windows move), reported. At least **30** measured realizations, otherwise the
  case-year is excluded and counted.
- `ρ_1 = median(e_pred,1) / σ_meas`, `ρ_2 = median(e_pred,2) / σ_meas`, `ρ_h = median(e_hidden) / σ_meas`.
- **The cell's value:** the median over its case-years; its 95% interval by a cluster bootstrap over
  the cases (all of a case's years resampled together), 2000 resamples, the seed the first 8 bytes of
  the SHA-256 of `refute/v0.2.1/stage-1/X2/bootstrap`. A cell needs at least 15 of its 20 cases
  contributing, otherwise its verdict is `not determined`.
- **The criteria,** with `τ = 0.10`, the design value `D` (`m_beta` for `ρ_1`, from the plan; 1 for
  `ρ_2` and `ρ_h`) and the interval `[lo, hi]`: `calibrated or conservative as designed` if
  `[lo, hi] ⊂ [1 − τ, (1 + τ)·D]`; `overestimated` if `lo > (1 + τ)·D`; `underestimated` if
  `hi < 1 − τ`; `not determined` otherwise. Each verdict is computed with the standard deviation
  (deciding) and with the MAD (the check); where the two differ, that ratio's verdict in that cell is
  `not determined`. `underestimated` in any cell is reported first, as a safety finding (the
  findings in the order underestimated, overestimated, not determined, calibrated; then by cell and
  ratio).

**The procedure** is `x2_evaluate.round_rows` and `x2_evaluate.evaluate`, run by
`x2_study.py evaluate` on a complete lot (the lot's check passes first), committed and tested before
any realization; its output is written once and never replaced.

## 7. Reported apart, descriptive only

The rounds refused by a capacity decision (`insufficient_capacity_train` at decision 1,
`insufficient_capacity_hidden_noise` at decision 2) that would pass with `σ_meas` in place of
`e_pred`, **without** any claim that this would be better (releasing a gate can bring new PASS and
new FAIL); the structural impediments (no predicted window, train replicas below `r_min`), which a
change of the error cannot remove, counted apart; `ρ` by layout
and by `n_pred`; the fraction of rounds measured per cell.

## 8. What follows (fixed now)

- X2-B `calibrated or conservative as designed` in every cell: the error model stays; X3 calibrates
  `b` and `s` with it. Otherwise a change of the error model is **proposed** (its own specification,
  tests and Codex review), and X3's definitive calibration uses the corrected model.
- X2-A: its classes say which of the four causes to study next; a change to the engine that follows
  from them (for example to the ephemeris extrapolation or the detrending) is proposed with its own
  specification, tests and validation, never applied because of X2 alone, and never by raising a
  threshold to remove the old cases.
- `not determined`: reported; the size needed is computed and requested, never extended without
  authorization.
