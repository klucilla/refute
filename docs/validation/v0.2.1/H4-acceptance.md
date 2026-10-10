# v0.2.1 H4 (wrong training period in the blind holdout): acceptance criteria

Status: **criteria fixed before any validation runs.** This file is committed on its
own, before the tests and the code it describes. Written 2026-10-10 on branch
`claude/v0-2-1-gauntlet-fixes-13f5e7`.

## Problem

Each round of `holdout_by_year` hides one observing year, searches the other years
(the train data) and predicts transit windows in the hidden year from the train-only
candidate. Today the round uses that candidate whatever it is: it does not have to
pass the SNR gate, its box can be a large fraction of its period, and its windows can
cover most of the hidden year. A round trained on something other than a transit
can then FAIL (or PASS) without saying anything about the signal.

On the development scenarios the current code already shows the mechanism: in
`sinusoid` and `fp_variability_dominates` every round PASSES (20 of 20 on seeds
0-9) with a train box of duration/period 0.357 whose windows cover 100% of the
hidden year, so there is no "elsewhere" where the prediction could fail.

**Known targets.** The v0.2 post-mortem reports Kepler-447 b, whose 2024 round
trained on 0.518 d with a 10.4 h box and a train SNR of 7.05 (below the 7.1 gate),
with windows covering the hidden year. These numbers are cited **only as
motivation**. No threshold in this document was chosen, tuned or checked on
Kepler-447 b or on any other known target, and no known target is used to validate
H4.

## Scope

**General mode only:** the rules use only the train data of the round, the claim's
parameters and the hidden sectors' time spans (metadata, already used today to
predict windows). They never compare with the full-data analysis (which contains the
hidden year) nor with other rounds (whose train data contain this round's hidden
year).

**Out of scope, open item:** the *directed* mode of the v0.2.1 plan (requiring the
train candidate to match a published period and epoch). It would pass target
information into `run_holdout`, which changes the isolation contract.

## Definition

New fields in `test_plan.gauntlet.holdout_by_year`:

- `require_valid_train: bool`, default `true`. With `false` the rules below are
  still computed and reported, but never change a round (used for before/after
  studies and to verify test premises).
- `max_train_duration_period_ratio: float`, default `0.2`, in (0, 1].
- `max_hidden_window_fraction: float`, default `0.5`, in (0, 1].

A round's train candidate is **invalid** when any of these holds:

- **(a) gate:** its SNR is below `gauntlet.snr.min_snr` (7.1, the same gate as the
  full analysis, applied with the same function). No new threshold. A train SNR
  exactly equal to the gate is valid.
- **(b) duration:** its duration / period is above `max_train_duration_period_ratio`.
  Exactly equal is valid.
- **(c) windows:** the fraction of the hidden year covered by its transit windows is
  above `max_hidden_window_fraction`. Exactly equal is valid. The fraction is the
  length of the union of the transit windows `[t_pred - half_width, t_pred +
  half_width]`, clipped to the hidden sectors' spans `[t_start, t_end]`, divided by
  the total length of those spans. It uses the sector metadata only, never the hidden
  cadences.

Order: (a) and (b) are evaluated together right after the train search; if either
holds, the round stops there. Otherwise transit times, the train ephemeris and the
windows are computed as today; the existing timing-uncertainty rule (issue #2) is
applied unchanged, then (c).

An invalid round is **INCONCLUSIVE, never FAIL**, and is decided **before the hidden
year is read**: no `HiddenYear` is built and its access log is empty. Each round
reports `train_validity` (the three values, the thresholds, whether the rules were
applied, and the list of reasons).

### Thresholds (derived from the window geometry, not from data)

- **(b) 0.2.** A transit window's baseline band extends to
  `duration/2 + baseline_outer_durations * duration` from the predicted time (with no
  timing slack). It reaches the phase-0.5 control box when
  `duration * (1 + baseline_outer_durations) > period / 2`, that is, with the default
  `baseline_outer_durations = 1.5`, when duration/period > 1 / (2 * 2.5) = 0.2. Above
  that, the transit and control measurements are no longer independent.
- **(c) 0.5.** If the transit windows cover more than half of the observed hidden
  time, they overlap the phase-0.5 control windows: there is no part of the year
  outside the prediction, so a non-detection or a detection is not a test of it.

## Baseline on the development set (current code, before H4)

Measured on seeds 0-9 of every existing scenario plus `fp_variability_dominates`,
with the fast test plan (200 rounds). This is the "before" measurement; it was not
used to choose any threshold (they follow from the geometry above).

| Scenario | Round statuses today | Min train SNR | Max D/P | Max window fraction |
|---|---|---|---|---|
| planet, no_radius | 17 PASS, 3 INCONCLUSIVE (each) | 53.3 | 0.024 | 0.155 |
| planet_three_years | 30 PASS | 76.4 | 0.024 | 0.026 |
| eb_secondary, eb_odd_even, eb_equal, blend | 20 PASS (each) | 171 | 0.055 | 0.164 |
| noise | 20 INCONCLUSIVE | 3.8 | 0.342 | n/a |
| vanishing | 9 FAIL, 11 INCONCLUSIVE | 4.2 | 0.191 | 0.148 |
| sinusoid, fp_variability_dominates | 20 PASS (each) | 81.0 | 0.357 | 1.000 |
| single_year | no rounds | - | - | - |

### Scenario tried and discarded: `weak_planet`

A weak planet was meant to show rule (a) alone turning a FAIL into INCONCLUSIVE. It
was prototyped on development seeds and **discarded because it is not robust**:

- Depths 400 to 800 ppm (seeds 0-4): train SNR 9.2 to 24.0, never below 7.1.
- Depths 200, 230 and 260 ppm (seeds 0-9): train SNR 3.8 to 9.5, but **all 60 rounds
  are already INCONCLUSIVE today** through the existing timing-uncertainty rule, so H4
  would change only the reason, never a FAIL. At 200 ppm, 3 of 20 rounds also trained
  on a different period (5.06 d, 1.85 d, and 0.513 d with duration/period 0.487,
  which also triggers (b)), and at 230 ppm the train SNR crosses 7.1 depending on the
  seed.

Rule (a) is therefore covered by the unit cases, by a declared test double (B2) and
by the reasons in `noise` and `vanishing` (B3).

## Acceptance criteria

H4 is accepted when every case below holds, the full existing test suite passes
unchanged, and `ruff check` / `ruff format --check` pass.

### A. Unit cases (`tests/test_holdout_train_validity.py`)

The rule evaluation on fabricated train candidates, ephemerides and sector spans:

- A1. (a): train SNR 7.09 is invalid; 7.1 is valid.
- A2. (b): duration/period above 0.2 is invalid; exactly 0.2 is valid. The boundary
  uses duration 0.125 d and period 0.625 d (both exact in binary; their correctly
  rounded quotient is the same double as the literal 0.2), and the case just above
  uses the next double below 0.625 for the period.
- A3. (c) alone: duration/period 0.15 (valid for (b)) with timing slack whose windows
  cover more than half of the hidden spans is invalid; the same with windows covering
  exactly half is valid; windows that overlap each other or cross a sector edge are
  counted once and clipped.
- A4. Several reasons at once are all reported.
- A5. An invalid round is INCONCLUSIVE, never FAIL, for every combination of reasons.
- A6. `require_valid_train: false`: the values and reasons are reported, the round is
  not changed.
- A7. Schema: `max_train_duration_period_ratio` and `max_hidden_window_fraction`
  outside (0, 1] are rejected; a claim without the fields loads with the defaults.

### B. End to end on synthetic data (`tests/test_holdout_train_validity_e2e.py`)

Every case first checks its premise. A premise that does not hold fails the test; it
is never skipped. Premises about today's behavior are checked in the test itself with
`require_valid_train: false`.

- B1. **INCONCLUSIVE, today FAIL.** New scenario `variability_train_only`: the
  `planet_three_years` transit plus a 4000 ppm sinusoid at 0.7 d present in 2018 and
  2019 and absent in 2020. Round hiding 2020. Premise (guard off): the train candidate
  is at 0.7 d (not the planet) and the round is FAIL. Expected (guard on):
  INCONCLUSIVE with reason (b) only; (c) does not trigger (window fraction below 0.5);
  the hidden year is not read. The other rounds of this scenario fail with a *valid*
  train (the sinusoid in their hidden year lowers the SNR); that is outside H4 and
  they must stay FAIL. Seeds 0-4.
- B2. **(a) alone turns a FAIL into INCONCLUSIVE (declared test double).** Scenario
  `vanishing`, round hiding 2020 (train 2018 holds the real signal). Inside the test
  only, the train search of that round (`refute.packs.tess.holdout.search_period`) is
  replaced by a double that runs the real search and returns the same candidate with
  its SNR set to 6.9. Premise (guard off, with the double): the round is FAIL.
  Expected (guard on, with the double): INCONCLUSIVE with reason (a) only. Seeds 0-3:
  on seed 4 this round is already INCONCLUSIVE today (measured on the development
  set before this file was written: the 2020 round is FAIL on seeds 0-3 and 5-9,
  INCONCLUSIVE on seed 4), so seed 4 is excluded here and in B6.
- B3. **Reason only.** `noise` (every round) and `vanishing` (rounds hiding 2018) are
  INCONCLUSIVE today and stay INCONCLUSIVE; premise: train SNR below 7.1; expected:
  reason (a) present. Seeds 0-9.
- B4. **INCONCLUSIVE, today PASS.** `sinusoid` and `fp_variability_dominates`, every
  round: premise (guard off) PASS with duration/period above 0.2; expected (guard on)
  INCONCLUSIVE with reason (b). Seeds 0-4.
- B5. **Still passing.** `planet` and `planet_three_years`: no reason in any round,
  and every round status identical with the guard on and off. Seeds 0-4.
- B6. **Still failing.** `vanishing`, round hiding 2020 without any double. Premise
  (guard off): FAIL. Expected (guard on): FAIL, no reason. Seeds 0-3 (see B2).

### C. Blindness (`tests/test_holdout_blindness.py`)

- C1. For each round of `planet`, `vanishing`, `variability_train_only` and
  `sinusoid` (seeds 0-2), the hidden year's flux is replaced, keeping its times and
  sectors, by (i) white noise only, (ii) a different signal (a deep eclipse at another
  period), (iii) nothing (constant flux). Everything decided before the hidden windows
  are read must be byte-identical (canonical form) to the original: the train
  candidate, the transit times, the train ephemeris, the transit and control windows,
  `train_validity`, the timing-uncertainty decision and the hidden-year detrending
  window. For rounds decided before the read (any INCONCLUSIVE from the train side),
  the whole round result must be identical and its access log empty.
- C2. Structural: the pre-read step receives no hidden-year flux (its signature takes
  the train data and the hidden sectors' spans only), and a round with an invalid
  train never constructs `HiddenYear` (checked by replacing the class with one that
  raises).

### D. Property and regression (in `tests/test_holdout_train_validity_e2e.py`)

For every existing scenario plus `fp_variability_dominates` and
`variability_train_only`, seeds 0-9, with the guard on and off:

- D1. Per round, the status with the guard is either the status without it or
  INCONCLUSIVE.
- D2. `holdout_by_year` FAIL with the guard implies FAIL without it.
- D3. Only `noise`, `vanishing`, `sinusoid`, `fp_variability_dominates` and
  `variability_train_only` may have reasons; in `noise` and `vanishing` only on rounds
  that are INCONCLUSIVE without the guard.

## Seeds

- **Development set: seeds 0 to 9** (the same set as H7). Cases use the subsets
  stated above to keep the suite fast.
- **Confirmation set: not generated and not used now.** It is reserved per rule 5 of
  the v0.2.1 plan.

## Planned sabotages (run after the code passes, never committed)

Each one is run against the H4 tests only and reverted with an empty `git diff`
before the next. Each must be caught by the cases listed.

| Sabotage | Must be caught by |
|---|---|
| S1. The guard always reports a valid train | A1-A5, B1, B2, B4, D3 |
| S2. Rule (a) uses an SNR measured on train plus hidden data (a leak) | C1 |
| S3. An invalid train gives FAIL instead of INCONCLUSIVE | A5, B1, B2, B4, D1 |
| S4a. Rule (a) removed | A1, B2, B3 |
| S4b. Rule (b) removed | A2, B1, B4 |
| S4c. Rule (c) removed | A3 |
| S5. Rule (c) computed from the hidden cadence times instead of the sector metadata | C1 if variant (iii) changes the result; otherwise recorded as not detectable by flux replacement |

## Effect on locks

The new fields have defaults, so the resolved `test_plan` (and the claim hash) of
older claims changes, as for H7 (issue #30). The v0.2 calibration is verified at its
locked commit `cc9d104`.

## Risks

- **Refuted planets:** can only fall or stay equal: the guard never creates a FAIL
  (D1, D2). A planet with every round invalid gets an INCONCLUSIVE holdout and an
  INCONCLUSIVE verdict instead of SURVIVED; this counts against the coverage
  requirement defined later (R7) and is reported.
- **Flagged false positives:** can fall when a flag depended on a round with an
  invalid train. Intended (R4); not compensated by any other hypothesis.
- **Recovered planets:** unchanged (full-data analysis).
- **Power against noise:** the blind test stays the defense against signals that do
  not repeat. The guard only removes rounds whose train is not a valid basis for a
  prediction; nothing becomes PASS that was not PASS (D1).
- **Geometric thresholds:** a real contact binary with duration/period above 0.2 gets
  an INCONCLUSIVE holdout. The blind holdout is not the eclipsing-binary test.
- **Variability in the hidden year** (the other rounds of B1) still lowers the hidden
  SNR with a valid train; that is outside H4 (closer to H6).

## Out of scope

The directed mode (open item), H3, H1, H9(a), H2, the report sentence (#23) and the
coverage requirement.
