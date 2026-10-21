# Acceptance record: the instrumentation of the calibration record (stage 1, item D)

The maintainer's decision of 2026-10-21, item D: the next technical step. This record is committed
**before** its tests and its code (ROADMAP, v0.2.1 exit criterion 1). It changes **no decision** of
the engine. It does not recover what the old records lack, and it does not show that `e_pred` is
inflated: that hypothesis needs its own experiment afterwards (experiment plan, X2), with its cost
approved. Revision 2, after Codex's review (its points applied: the field sources, the stage
matrices, the source checks and the sabotages).

## 1. What is added, and where each value comes from

**In the calibration record** (`holdout.calibration_measurement`, the `calibration_only` records):

| Field | Meaning | Source in the code (value copied, never recomputed differently) |
|---|---|---|
| `n_pred` | predicted transit windows inside a hidden sector span | `count_n_pred` in `_round_corrected` (`cap["n_pred"]`) |
| `grid_dp` | the `dP` grid, in days | `period_grid` in `_round_corrected` (`cap["grid"]`) |
| `train_var_rep` | the train replicas' variance at each `dP`, in grid order | `train_replica_stats` (`cap["train_var_rep"]`) |
| `hidden_var_rep` | the hidden replicas' variance at each `dP`, in grid order | `record_hidden` (`cap["hidden_var_rep"]`) |
| `e_pred_1`, `e_pred_2` | the predicted errors decisions 1 and 2 used | `cap["e_pred_1"]`, `cap["e_pred_2"]` |
| `m_beta` | the margin of `e_pred_1` | the plan's `corrections.m_beta` (`cap["m_beta"]`) |
| `d_c` | `d_train − CAPACITY_K · e_train` | `cap["d_c"]` |
| `train_ephemeris` | `Ephemeris.to_dict()` | the ephemeris of the round (`prepared.ephemeris`; at a timing stop, the one in the stop's `RoundResult`) |
| `train_duration_days` | the train candidate's duration | the train candidate of the round |
| `max_timing_sigma_days` | the largest `σ_T` of the predicted transit windows | `plan_round`'s `max_sigma_t` |
| `n_transit_times` | the train transit times accepted | `plan_round`'s `len(times)` |

**One structural addition, still with no decision changed:** today `plan_round` does not return
the train candidate (nor its duration) on some early stops, for example `train_noise_undetermined`,
although the candidate exists then. To record `train_duration_days` "as soon as the candidate
exists", `plan_round`'s returned plan carries the candidate (and `n_transit_times`,
`max_timing_sigma_days`) in its diagnostics whenever they exist. AC5 protects every existing output
from this change.

A field not known at a round's stopping point is present with `None` (never absent, never guessed).

**On the evaluator's side only** (`rmin_study.record_target` or its successor): each case's injected
parameters (`period`, `t0`, `duration`, `depth`, `impact`, `ingress_fraction`, and the scenario's
`s`), under a key `truth` of the target record, added **after** the engine's calls. The engine never
receives them.

**Not changed:** every decision, threshold, message and status of `run_holdout` and of
`calibration_measurement`; the existing fields; the configuration's format; any verdict.

## 2. The expected fields at each stopping point

Two matrices, because the calibration measurement does **not** stop at decisions 1 and 2
(`_round_corrected(enforce=False)`: a failed decision is recorded and the computation goes on),
while the enforced path (`run_holdout`) stops there. "set" means the value of the source above;
"None" means present and `None`.

**(a) Calibration records** (what `calibration_measurement` returns):

| Stopping point | ephemeris, duration, σ_T, n_transit_times | n_pred, grid_dp, d_c, m_beta | train_var_rep | e_pred_1 | hidden_var_rep, e_pred_2 |
|---|---|---|---|---|---|
| no train data | all None | None | None | None | None |
| no train candidate | all None | None | None | None | None |
| train candidate rejected before its transit times (`train_snr_below_gate` and the like) | duration set, the others None | None | None | None | None |
| `train_noise_undetermined` | duration set (the structural addition), the others as they exist at that point | None | None | None | None |
| too few train transit times (`only N train transit times`) | duration and n_transit_times set, ephemeris and σ_T None | None | None | None | None |
| timing stop | all set | None | None | None | None |
| train validity rejected after the windows are predicted (for example the predicted-window fraction) | all set (the ephemeris and `σ_T` exist by then) | None | None | None | None |
| `no_predicted_window` | all set | `n_pred` = 0, the others set | None | None | None |
| train replicas below `r_min` | all set | set | set | None | None |
| decision 1 failed (recorded, not stopping) | all set | set | set | set | as the later stages give |
| hidden noise stop (`stage == "hidden_noise"`) | all set | set | set | set | `hidden_var_rep` as computed (may be partial), `e_pred_2` None |
| decision 2 failed (recorded, not stopping) | all set | set | set | set | set |
| measurement stop | all set | set | set | set | set |
| measured (PASS, FAIL, INCONCLUSIVE by the FAIL rule) | all set | set | set | set | set |

**(b) The enforced path** (`run_holdout`): it produces no calibration record; AC5 checks that its
outputs are byte-identical before and after the change. The matrix (a) is the contract of the new
fields.

## 3. The acceptance criteria (each with its test, written before the code)

**Coherence and source equality**
- **AC1, the formulas, piecewise** (following `predicted_error` and the `s_pred = d_c / e_pred if
  e_pred > 0 else NaN` lines of `_round_corrected`):
  - not computed at the stopping point (matrix (a)): `e_pred` and `s_pred` are `None`;
  - computed with an invalid input (an empty grid's variances, `n_pred ≤ 0`, a non-finite or a
    negative variance): `e_pred` is `NaN` and `s_pred` is `NaN`, as today;
  - computed with every variance zero: `e_pred` = 0 and `s_pred` is `NaN`;
  - otherwise (a non-empty grid, valid variances, a positive computed `e_pred`): the formulas
    `s_pred_1 = d_c / (m_beta · √(max(train_var_rep) / n_pred))` and
    `s_pred_2 = d_c / √(max(hidden_var_rep) / n_pred)` hold to 1e-12 relative.
  Each branch has its fixture.
- **AC2, source equality for every new field**, against an independent capture of the value the
  round used (a test spy on the source function, not a recomputation by the same formula):
  `e_pred_1`, `e_pred_2`, `grid_dp` (element by element), `train_var_rep` and `hidden_var_rep`
  (element by element, paired with `grid_dp[i]`, on fixtures whose variances differ across `dP`),
  `n_pred`, `d_c`, `m_beta`, `train_duration_days`, `n_transit_times`, `max_timing_sigma_days`,
  `train_ephemeris`.
- **AC3, the decisions:** decisions 1 and 2 recomputed from the new fields and the record's
  `threshold` equal the recorded decisions, including fixtures with `S_pred` exactly at the
  threshold and at its adjacent representable values (`math.nextafter` up and down).
- **AC4, the lengths:** `len(train_n_rep) = len(hidden_n_rep) = len(train_var_rep) =
  len(hidden_var_rep) = len(grid_dp)` whenever present; and `max_timing_sigma_days · 24`, rounded to
  two decimals, equals the number printed in a timing stop's reason.
- **AC5, nothing else changes:** on a fixed set of synthetic cases (white and AR(1), two and three
  years, every stopping point of matrix (a)), every pre-existing key of the calibration record and
  the whole `run_holdout` outcome (status, reasons, messages, metrics, windows, access log) are
  identical before and after; the record differs only by the added keys. The "before" is a snapshot
  made with the code before the change, committed with the tests. AC5 protects behaviour; it does
  not validate the new fields (AC1 to AC4 do).

**Boundary**
- **AB1** no predicted window: `n_pred` = 0 recorded, the variance and error fields `None`, the stop
  unchanged.
- **AB2** an empty `dP` grid, by an injected fixture (`period_grid` ordinarily gives a non-empty
  grid): the train counts are empty, `replicas_enough` fails first, the stop is
  `train_replicas_below_r_min`, `grid_dp` and `train_var_rep` are empty lists and `e_pred_1` is
  `None` (not computed).
- **AB3** every stopping point of matrix (a), each of its rows (the train-data, candidate,
  transit-time, timing and post-window validity stops included): its row exactly; AC5's fixture set
  covers the same rows.
- **AB4** a hidden year of one sector, and one with fewer replicas than `r_min`: recorded as
  computed.

**No leak**
- **AL1** no engine function receives a case parameter or the scenario: the signatures of
  `run_holdout` and `calibration_measurement` unchanged, and `truth` attached after the calls.
- **AL2** a read witness: the evaluator's `truth` is a guarded mapping that raises if it is read
  while an engine call is in progress (a flag set around the calls); the lot's code path runs with
  it and no read occurs.
- **AL3** changing the `truth` values changes no engine output (the records' engine fields byte for
  byte).

## 4. Sabotages planned (each must make a test fail)

| # | Sabotage | Caught by |
|---|---|---|
| S1 | `m_beta` dropped from the recorded `e_pred_1` | AC1, AC2 |
| S2 | `hidden_var_rep` permuted across `dP` (same maximum, same length) | AC2's element-wise pairing on unequal variances |
| S3 | a field absent instead of `None` at an early stop | AB3 |
| S4 | the ephemeris of another round | AC2 |
| S5 | the decision comparator changed from `>=` to `>` | AC3's fixture exactly at the threshold |
| S6 | the engine reads `truth` | AL2 |
| S7 | an existing field's value changed | AC5 |
| S8 | `train_duration_days` left `None` at `train_noise_undetermined` | AB3 |

A sabotage that no test catches is reported, and the gap closed before the code is accepted.

## 5. What it costs and what it touches

Code: `src/refute/packs/tess/holdout.py` (the record and `plan_round`'s diagnostics only) and the
evaluator (`docs/validation/v0.2.1/population/rmin_study.py` or its successor). Tests: a new test
file and the snapshot. No lot; CI only. On `main` (the maintainer's decision of 2026-10-20), never in
`.cache/wt-v021` (frozen at `2e4ff99`). The v0.3 locks are already `TAMPERED` in their code on `main`
by design (`calibration/v0.3/main/lock-verification/`); this change adds nothing to that. Every lot
that relies on these fields (X2, X3, X5) needs this record's tests accepted first.
