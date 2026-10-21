# X1b: specification B's experimental implementation, under its acceptance record

Authorized by the maintainer on 2026-10-21 (decisions after X0 and X1, item 2). The acceptance
record ([x1b-acceptance.md](x1b-acceptance.md)) and B6's revision were committed and pushed in
`5a657fb`, before the tests and the code. **Implementation, not adoption:** the legacy rule stays the
default everywhere; no verdict, study result or dossier uses B.

## The order

1. **The controls' preconditions, on the engine as it was** (the rounds do not depend on the
   aggregation; `probe.json`, `probe2.json`, `probe3.json`, kept in the working folder, never
   committed because they name the machine's paths): 31 of 32 met theirs at once. The disappearing
   planet in AR(1) with three years FAILed also in its rounds hiding 2018 and 2019 with its first
   seed (4103), so C3 could not have its other rounds PASS; twelve seeds were tried in order from
   4200 and the first that met the precondition, 4207, was taken (recorded in `tests/spec_b_cases.py`
   and in the acceptance record before it was committed). **A development observation, outside
   X1b:** a round hiding a year *with* the signal FAILed in 11 of the 12 seeds (16 of their 24 such
   rounds; corrected after Codex's review, which recounted `probe2.json`; the acceptance record's
   "10 of the 12", committed in `5a657fb`, is wrong and stays as committed) (the train holds
   the year without the signal); at the target level the FAIL is right (the planet did disappear),
   but a FAIL in a year that has the signal points at the predicted windows, as X0c's false FAIL do.
2. **The tests before the code:** `tests/test_spec_b.py` (T1 to T9) on `tests/spec_b_cases.py`; run
   against the unchanged code: **78 tests, 45 failures, 33 errors, 0 passed** (JUnit).
3. **The code:** `holdout.spec_b_outcome`, `holdout.SpecBCompletenessError`,
   `holdout.AGGREGATION_LEGACY` and `AGGREGATION_SPEC_B`; `run_holdout(..., *, aggregation)` and
   `_spec_b_holdout`; `rmin_evaluate.target_outcomes(..., *, aggregation)`, which calls the engine's
   function. The legacy path's code is unchanged.
4. **Two corrections of the tests after their first run against the code**, both of the expected
   undecided years, not of an outcome (every control had the status the record expects):
   - **C3 in two years:** the other round trains on the year without the signal and is undecided too,
     so the undecided years are both years (the probe had shown it; the test had listed only the last).
   - **C7b in two years:** the first year's round trains on the year without the signal and stops
     before its windows are predicted, so the no-window replacement is never reached there; a year
     without a window beside a FAIL exists only in three years. The test checks C7b's FAIL in all four
     variants and its `no_predicted_window` year in the two three-year variants (and in T1's row).
   And one test of X1's (`test_the_engine_signatures_are_unchanged`) was updated, as X1b's change
   requires: `run_holdout`'s parameters are the three positional ones and the keyword-only
   `aggregation`, whose default is the legacy rule.
5. **The tests after the code:** `test_spec_b.py`, `test_rmin_evaluate.py` and
   `test_instrumentation.py` with AC5's exact comparison on the snapshot's machine
   (`REFUTE_AC5_EXACT=1`): **301 tests, 1 failure** (the signature test, updated as above), 3
   skipped (JUnit); AC5's exact comparisons all passed, so the legacy `run_holdout` outcome is
   byte-identical to the snapshot made before X1.
6. **The full suite:** 3760 tests, 1 failure, 0 errors, 88 skipped (JUnit). The failure was a second
   signature test, `tests/test_holdout_isolation.py::test_run_holdout_rejects_a_candidate_argument`
   (`run_holdout` never receives a candidate), updated the same way: the three data parameters,
   the keyword-only `aggregation`, and a candidate given as `aggregation` refused (`ValueError`); it
   and X1's signature test then ran alone: 2 tests, 0 failures. Nothing else changed after the suite.
7. **The sabotages** (the acceptance record, section 4): results below.

## Codex's review of the round (OBJECAO on `9933eb1`, all points applied)

- **The evaluator keyed the rounds by year before the shared check**, so a duplicated year's FAIL
  could vanish (2018 FAIL, 2018 PASS, 2020 PASS gave PASS; the other order FAIL). Every round, as
  recorded, now goes to `spec_b_outcome` before it is keyed; tested in both orders (refused).
- **One necessary year with a FAIL gave FAIL**, against the acceptance record (1.1: fewer than two
  years is INCONCLUSIVE, the rounds complete). The guard now comes first; tested with the three
  statuses.
- Tests before the fix: 5, 3 failing (the FAIL year and the two orders); after it,
  `test_spec_b.py` and `test_rmin_evaluate.py`: 103 tests, 0 failures; the full suite: **3764 tests,
  0 failures, 0 errors, 88 skipped** (JUnit). Codex's second round: ACORDO. CI on `9933eb1` was
  green.
- The record's corrections (X0c's README and exploratory note, X2's deciding scale, X3's `R` and
  bootstrap, a count here and a rounding in X0c) are in those files, each marked.

## The controls' outcomes

| Control | white, 2 years | white, 3 years | AR(1), 2 years | AR(1), 3 years | today's rule (same rounds) |
|---|---|---|---|---|---|
| C1 constant | PASS | PASS | PASS | PASS | PASS |
| C2 disappearing | FAIL | FAIL | FAIL | FAIL | FAIL |
| C3 disappearing, last-year decision 2 stopped | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE in 2 years, **PASS in 3** |
| C4 constant, last-year decision 2 stopped | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | **PASS** |
| C5 no transit | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE |
| C5r train candidate rejected | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE |
| C7a constant, no window in the last year | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | **PASS** |
| C7b disappearing, no window in the first year | FAIL | FAIL | FAIL | FAIL | FAIL |

## The sabotages

Each applied to the staged code, `tests/test_spec_b.py` run, the file restored from the index (the
diff empty after each). All seven caught:

| # | Sabotage | Tests failing |
|---|---|---|
| S1 | PASS when any round PASSes | 17 (T1, T6, T7: C3 in three years, C4, C7a; T9) |
| S2 | FAIL's precedence dropped | 12 (T1, T7: C2 in two years, C7b; T9) |
| S3 | a missing necessary year accepted | 1 (T3) |
| S4 | a duplicated year accepted | 2 (T3) |
| S5 | B reached with the corrections switch off | 1 (T5) |
| S6 | `run_holdout`'s default changed to B | 2 (T6, T8) |
| S7 | the evaluator using its own copy of the aggregation | 1 (T8) |
