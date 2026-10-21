# X1: the instrumentation, implemented under its acceptance record

Authorized by the maintainer on 2026-10-21 (no lot). The acceptance record:
[instrumentation-acceptance.md](instrumentation-acceptance.md) (revision 2, committed in `c5d1287`
before the tests and the code). **No decision of the engine changed.**

## The order

1. **The snapshot first**, with the code before the change (`98ebc9f`):
   `tests/make_instrumentation_snapshot.py` wrote `tests/fixtures/instrumentation_snapshot.json`,
   the calibration record and the `run_holdout` outcome of 15 synthetic cases, one per row of matrix
   (a) (two for "measured", white and AR(1); the cases in `tests/instrumentation_cases.py`). One
   case was corrected before the snapshot was kept: the AR(1) "measured" case first hid a year too
   far from the train and stopped at the timing rule, so it was moved to a hidden year next to the
   train (THREE_BY_ONE, 2019); the first snapshot was discarded.
2. **The tests before the code:** `tests/test_instrumentation.py`, 100 tests; run against the
   unchanged code: **77 failures** (the 23 that passed are those that must hold before and after:
   the old record and `run_holdout` against the snapshot, the signatures).
3. **The code:** `src/refute/packs/tess/holdout.py` (`RoundPlan.diagnostics`, set at each return of
   `plan_round`; `INSTRUMENT_FIELDS` and `_instrument_fields`; the fields copied into the
   calibration record where the round computes them) and
   `docs/validation/v0.2.1/population/rmin_study.py` (`truth_of`, `EvaluatorTruth`, `engine_call`,
   `engine_call_active`; `record_target` adds `truth` after the engine's calls).
4. **One test corrected after its first run against the code:** the spy of the train candidate's
   duration read `finalize_candidate`'s first call, which is `search_period`'s, not the round's
   refit; it now reads the last call (the refit), and the duration is still checked against the
   round's `train_candidate` where the metrics have it. The acceptance criterion did not change.
5. **The tests after the code:** 100 tests, 0 failures (JUnit).
6. **The sabotages** (the acceptance record, section 4), each applied to the staged code, the tests
   run, the file restored from the index (the diff empty after each):

| # | Sabotage | Tests failing |
|---|---|---|
| S1 | `m_beta` dropped from the recorded `e_pred_1` | 9 (AC2, AC1) |
| S2 | `hidden_var_rep` permuted across `dP` | 6 (AC2, element-wise) |
| S3 | the fields absent at an early stop | 23 (AB3, AC2, AC4) |
| S4 | the ephemeris of another round | 10 (AC2) |
| S5 | the decision-1 comparator `>=` changed to `>` | 1 (AC3, exactly at the threshold) |
| S6 | the engine reads the truth | 2 (AL2) |
| S7 | an existing field's value changed | 16 (AC5, AC2) |
| S8 | `train_duration_days` left `None` at `train_noise_undetermined` | 2 (AB3) |

All eight caught.

## After Codex's review of the round (OBJECAO, all points applied)

Codex found no change of any engine decision or output and no wrong field source, but gaps in the
tests and a weak guard. Applied in the same round:
- **The guard:** `EvaluatorTruth` is now a mapping by composition, not a `dict` subclass (so
  `dict.__getitem__` and `dict`'s own methods do not reach its values); every route of its interface
  raises during an engine call: item access, `get`, iteration, length, membership, `dict(...)`,
  `{**...}`, `repr`, `str`, `copy`, `deepcopy`, `pickle`, and views taken **before** the call and
  consumed during it. Its limit, stated in its docstring: deliberate access to its private attribute
  is not prevented; the witness covers the mapping's interface.
- **New tests:** each of those routes (16); an engine that obtains the truth object and reads it is
  caught and the target not recorded; AL3 with the **real** `calibration_measurement`, not a stub;
  the hidden-variance branches of AC1 (NaN, negative, infinite, all zero); `max_timing_sigma_days`
  against plan_round's predicted windows in every row that has it; decision 2 exactly at its
  threshold and at the adjacent representable values; and **AC5 exactly** (byte for byte, as JSON)
  in the snapshot's own environment (Windows, CPython 3.13.16), the tolerant comparison kept for the
  other platforms.
- **The generator** of the snapshot now refuses uncommitted changes under `src/` and records the
  engine file's SHA-256 and the environment (the snapshot already committed was made with the code of
  `98ebc9f`, before the change, with `holdout.py` identical to `c5d1287`'s; its environment is now
  recorded in the tests, as the generator did not record it then).
- **Four more sabotages:** S9 `repr` unguarded (2 tests failing); S10 decision 2's comparator `>=`
  changed to `>` (1, exactly at the threshold); S11 the views guarded only when taken (**escaped at
  first**: the test consumed the view with `list(...)`, which calls the guarded `__len__` first,
  while a bare `for` loop does not; the test now consumes by bare iteration, and S11 is caught, 3
  tests failing); S12 the guard switched off (17). All four caught.

## CI on `46e3d95` (the first push of X1): red, and why

Run 39627687323: the four `rest` jobs failed on two tests of AC5's tolerant comparison
(`decision_1_failed` and `measurement_stop`): on Ubuntu and on Windows with Python 3.12 the engine's
own floats differ from the snapshot's far more than 1e-9 (a train period at about 2e-6 relative, a
BLS SNR at about 2e-4), with every status, reason, key and length identical. No behaviour changed;
the 1e-9 tolerance was wrong for a snapshot made on one platform. Fixed forward: the comparison
outside the snapshot's environment checks the structure, the keys, the list lengths and every
non-float value exactly, and each float only for its kind (finite, NaN, infinite); the values
themselves are compared exactly, as JSON, in the snapshot's environment, where they were found
byte-identical. The same run showed `rest` at 34 to 38 minutes; it was already 16 to 46 minutes on
`5b86736` (run 39369145960), over the 15-minute target before X1; `tests/test_instrumentation.py`
(150 s of fixtures) moves to `heavy-c`, the lightest shard; the older breach of `rest` stays open,
to be rebalanced apart.

## Two notes

- **AC5's comparison** checks equal structure and values, floats to 1e-9 relative: the snapshot was
  made on one platform (Windows, CPython 3.13.16) and CI runs on Ubuntu and Windows, 3.12 and 3.13,
  where the last bits of a float can differ (as found before in this phase). Strings, integers,
  `None` and keys are compared exactly.
- **What it does not do:** it does not recover the fields the R_min study's records lack, and it
  does not test whether `e_pred` is inflated (experiment X2, its own authorization).
