# X0c: the constant scenario's false FAIL, read only, declared before it runs

Authorized by the maintainer on 2026-10-21 (decisions after X0 and X1, item 3): the next priority of
safety. Under specification B the false FAIL's count is unchanged but its fraction among the decided
rises (`AR(1), variability`: 2/476 → 2/36), so more PASS would lower it without correcting any
error; the FAIL themselves must be understood. **Development evidence, not validation.** From the
recorded fields only: no light curve is built, the engine is not run, no lot. This declaration is
committed and pushed before the analysis runs; only what it declares is computed; anything else is
written apart in `exploratory.md`, never run.

## Data, code, conventions

As X0 ([../x0/DECLARATION.md](../x0/DECLARATION.md)): the 76 800 records of the R_min study checked
against their committed digests (a mismatch stops the analysis); the study's code at `2e4ff99`
(`.cache/wt-v021`, read only, no bytecode written); `derive_round` and `target_outcomes` with
bs-choice's committed pair at each R; the gates G0 to G6 and the reason kinds of the diagnosis's
script (`diagnosis.py`, imported, as X0 did); the completeness check (one round per observing year)
first.

**The cases:** every constant-scenario target whose aggregated outcome is FAIL at **R = 8** or at
**R = 20** (X0b counted 8 at R = 8: 2 in `AR(1), variability`, 6 in `white, no variability`; and 6 at
R = 20: 5 and 1 in `white, variability`). A FAIL target's count is the same under today's rule and
under B (B2, the precedence of a valid FAIL).

## What is reported, per case (`x0c.json`)

1. The target, its group, its observing years, its case labels from the diagnosis (`labels`: band,
   noise, index, mechanism and, for `few_train`, its train transits and distance), and at which of
   R = 8 and R = 20 it is FAIL.
2. **Every round** of the target, at each of R = 8 and R = 20: its hidden year, status, reason, gate
   and reason kind, decisions 1 and 2, and `S_meas` when measured.
3. **Each FAIL round**, from its record: `S_meas`; `Z`, recomputed by the study's `fail_rule` from
   the recorded `d_train`, `e_train`, `d_hidden`, `e_hidden` (and checked to give FAIL); those four;
   `d_twin` and `twin_status`; `dP`; `S_pred,1`, `S_pred,2` and the capacity threshold at that R
   (`capacity_threshold(min_snr, b_R, s_R, n_years)`); `n_years`; the smallest train and hidden
   replica counts; `hidden_noise_undetermined`; `measurement_status`; `stage`; `reason`.
4. **Derived, by algebraic identities of the recorded fields only** (stated with each value):
   - `d_c = d_train − K·e_train` with the engine's `CAPACITY_K` at `2e4ff99`;
   - `e_pred,1 = d_c / S_pred,1` and `e_pred,2 = d_c / S_pred,2` (when `S_pred` is finite and not
     zero), and the ratios `e_hidden / e_pred,2` and `e_hidden / e_train`;
   - `σ = sqrt(e_train² + e_hidden²)` and the split of `Z` into two parts that add up to it:
     `Z_train = (d_train − d_twin) / σ` (the train depth against the noiseless twin's depth at the
     predicted windows and the chosen `dP`) and `Z_hidden = (d_twin − d_hidden) / σ` (the hidden
     measurement against that twin depth);
   - `d_hidden / d_train`, `d_twin / d_train`, `(d_twin − d_hidden) / e_hidden`.
5. **The cause class, by rules fixed here** (on the FAIL round; computed only when `twin_status` is
   ok and `d_twin` finite, otherwise `twin unavailable`):
   - `hidden measurement` if `Z_hidden ≥ 3` and `Z_train < 3`;
   - `train or windows` if `Z_train ≥ 3` and `Z_hidden < 3`;
   - `both` if both are `≥ 3`;
   - `sum only` if neither reaches 3 (the FAIL comes from the two parts together).

   `hidden measurement` means the noise of the hidden year's measurement (or an error `e_hidden`
   too small) moved `d_hidden` far below the signal really present at those windows; `train or
   windows` means the windows measured carry less signal than the train depth says, either because
   the train depth is above the truth or because the predicted windows or `dP` missed part of the
   transits.

## The context distributions (per group, at R = 8 and R = 20)

Over every constant-scenario round of the group whose derived status at that R is PASS, FAIL or
INCONCLUSIVE `not_detected_not_inconsistent` (the eligible rounds) and whose twin is ok: the count,
the quantiles (1, 5, 25, 50, 75, 95, 99%) of `(d_twin − d_hidden) / e_hidden`, of `Z_train` and of
`Z_hidden`; the 1.4826 MAD of `(d_twin − d_hidden) / e_hidden`; and the fraction of rounds with
`Z_hidden ≥ 3` and with `Z_train ≥ 3`. Where each FAIL round falls in its group's distributions is
reported as its rank. **No inferential claim**: these show whether a case is in a tail, not whether
`e_hidden` is calibrated (that is X2's question, with repeated noise realizations).

## The limitations, declared now

- The records hold no injected parameter (they were never written there before X1) and no light
  curve is built here, so the train depth cannot be compared with the **injected** depth: `train or
  windows` does not separate a train depth above the truth from windows that missed the transits
  (the train ephemeris, the predicted windows and their `σ_T` are not recorded at `2e4ff99`).
- The records hold no per-window value, no replica variance and no noise realization, so a FAIL
  classed `hidden measurement` cannot be split into a noise excursion and an underestimated
  `e_hidden`; the ratio `e_hidden / e_pred,2` is reported, not interpreted as a cause.
- Where a case has `twin unavailable`, or where the parts are both below 3, the cause is reported as
  not identified from the records.
- Eight and six cases are not a sample for any rate.

## The outputs

`x0c.json` (the cases, the context distributions, the counts by class), a README with the tables,
and the script (`scripts/x0c.py`) with its SHA-256 as run and as committed, as X0 did.
