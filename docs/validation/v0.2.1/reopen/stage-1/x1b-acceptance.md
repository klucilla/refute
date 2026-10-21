# X1b: the acceptance record of specification B's experimental implementation

Authorized by the maintainer on 2026-10-21 (decisions after X0 and X1, item 2), as an
**experimental** implementation of [spec-b-target-pass.md](spec-b-target-pass.md) (B6 revised first,
in the same commit as this record). This record is committed before the tests and the code; the
tests are run against the code as it is first (they must fail where B is asked for), then the code is
written. **Implementation is not adoption:** no verdict, no study result and no dossier uses B.

## 1. What is implemented

1. **One function, in the engine:** `refute.packs.tess.holdout.spec_b_outcome(rounds,
   necessary_years)`. `rounds` is a sequence of `(hidden_year, status, reason)` with status
   `"PASS"`, `"FAIL"` or `"INCONCLUSIVE"`; `necessary_years` the observing years of the curve (B1).
   It returns `{"rule": "spec_b_experimental", "status", "reason", "fail_years", "pass_years",
   "undecided"}` (`undecided`: each INCONCLUSIVE necessary year with its round's reason), by B2:
   any FAIL gives FAIL (reason `prediction_failed`); otherwise PASS when every necessary year's round
   is PASS; otherwise INCONCLUSIVE `necessary_years_undecided`. Fewer than two necessary years (with
   their rounds complete): INCONCLUSIVE `fewer_than_two_observing_years`. The outcome does not depend
   on the order of the rounds.
2. **Completeness, refused as an error** (`SpecBCompletenessError`, a `ValueError`), never an
   outcome: an empty list of rounds; a round of a year not among the necessary years; two rounds of
   one year; a necessary year without its round; a duplicated necessary year; a status other than
   the three.
3. **The engine:** `run_holdout(raw, sectors, plan, *, aggregation="legacy")`. `"legacy"` (the
   default) is today's code, unchanged. `"spec_b_experimental"` is accepted only when the plan's
   corrections switch is on (the M4 path); otherwise `ValueError` before any round. Any other value:
   `ValueError`. With B, the rounds are made as today; the target's status and message come from
   `spec_b_outcome` with `raw.years` as the necessary years; the metrics keep today's summary and add
   `"aggregation": "spec_b_experimental"` and `"spec_b"` (the function's return); the coverage is
   B2's (the windows measured in the conclusive rounds, which for a PASS under B are all the rounds).
   The guard of fewer than two observing years (INCONCLUSIVE before any round) is unchanged for both.
4. **The evaluator:** `rmin_evaluate.target_outcomes(rec, r_min, b, s, min_snr, *,
   aggregation="legacy")`; with `"spec_b_experimental"` the status is `spec_b_outcome`'s over the
   derived rounds with `rec["years"]` as the necessary years, and the return adds `"spec_b"`. The
   default and `aggregate` are unchanged.
5. **Nothing else changes:** no caller passes the new argument (the gauntlet, the CLI, the studies'
   runners, the population harness); no configuration file can select B; the frozen records (the
   R_min study, the diagnosis, X0, the v0.3 dossiers) keep their bytes and their reading. X0's own
   `aggregate_b` (a committed analysis script) is not touched.

## 2. The tests, written before the code

| # | Test | Expected |
|---|---|---|
| T1 | `spec_b_outcome` on every row of B3 (including the two `no_predicted_window` rows) | the row's outcome under B, its reason, its years |
| T2 | every permutation of each row's rounds | the same outcome |
| T3 | each completeness refusal of 1.2 | `SpecBCompletenessError` |
| T4 | one necessary year, its round complete | INCONCLUSIVE `fewer_than_two_observing_years` |
| T5 | `run_holdout` with B and the corrections switch off; with an unknown aggregation | `ValueError`, before any round |
| T6 | `run_holdout`'s legacy outcome | unchanged: the existing holdout tests and X1's AC5 (structure everywhere, exact on the snapshot's machine) |
| T7 | the engine controls of B4 (section 3), with B | the expected target status; the legacy status recomputed from the same rounds for the contrast |
| T8 | `run_holdout` with B calls `spec_b_outcome` once, with `raw.years`; `target_outcomes` with B calls it once with `rec["years"]` | one implementation |
| T9 | `target_outcomes` with B on synthetic records (each B3 row as derived rounds) | `spec_b_outcome`'s status; the default unchanged |
| C6 | the existing blindness property (`tests/test_holdout_blindness.py`) | kept and run |

## 3. The engine controls (B4), fixed before the code

Synthetic curves (`tests/spec_b_cases.py`): the planet `synthetic.PLANET` (depth 0.002), two
sectors per observing year, two layouts (2018 and 2020; 2018, 2019 and 2020), white noise and AR(1)
(red 600 ppm), one seed per layout and noise. Where one round alone must stop, a **declared
replacement** of one engine function does it, as X1's cases did:
- the decision-2 stop: `predicted_error`, when called for decision 2 in the named year's round,
  returns infinity (`S_pred,2 = 0`, the round stops with `insufficient_capacity_hidden_noise` before
  its measurement);
- the year without a predicted window: `count_n_pred` returns 0 for the named year's round (the round
  stops with `no_predicted_window`).

| Control | Curve | Replacement | Under B |
|---|---|---|---|
| C1 | constant planet | none | PASS |
| C2 | disappearing planet (no signal in the last year) | none | FAIL |
| C3 | disappearing planet | decision 2 stops the last year's round | INCONCLUSIVE, the last year undecided |
| C4 | constant planet | decision 2 stops the last year's round | INCONCLUSIVE, the last year undecided (an abstention, not an error) |
| C5 | no transit at all | none | never PASS |
| C5r | constant planet, the train candidate rejected before the capacity rule (`max_train_duration_period_ratio` 1e-6) | none | never PASS |
| C7a | constant planet | no predicted window in the last year | INCONCLUSIVE, the last year undecided (`no_predicted_window`) |
| C7b | disappearing planet | no predicted window in the first year | FAIL (a valid FAIL keeps its precedence) |

Each in the four variants (white and AR(1), two and three years): 32 runs. **The rounds' statuses do
not depend on the aggregation**, so each control's precondition (C1 every round PASS; C2 and C7b the
last round FAIL; C3, C4 and C7a the named round stopped as intended; C3 in three years the other
rounds PASS) was checked on the engine as it is before the code (`probe.json`, `probe2.json`,
`probe3.json`, kept in the working folder); a control whose precondition failed was changed before
this record was committed, never after. One was: the disappearing planet in AR(1) with three years
FAILed also in the rounds hiding 2018 and 2019 with its first seed, so its seed was replaced by the
first of twelve tried in order (4207) that meets the precondition; the twelve are kept, and that
those rounds FAIL in 10 of the 12 seeds is recorded as a development observation, outside X1b's
scope. **The legacy contrast, asserted:** today PASS for C4 and C7a (both layouts) and for C3 in
three years; today INCONCLUSIVE for C3 in two years (its other round trains on the year without the
signal); today FAIL for C2 and C7b.

## 4. Acceptance

All the tests of section 2 pass; the full suite passes; ruff exits 0; the sabotages below are each
caught by at least one test; Codex's review of the implementation finds nothing open.

| Sabotage | Caught by |
|---|---|
| S1 PASS when any round PASSes (today's rule inside `spec_b_outcome`) | T1, T7 |
| S2 FAIL's precedence dropped (an undecided year before a FAIL gives INCONCLUSIVE) | T1, T7 |
| S3 a missing necessary year accepted | T3 |
| S4 a duplicated year accepted | T3 |
| S5 B reached with the corrections switch off | T5 |
| S6 `run_holdout`'s default changed to B | T6, T8 |
| S7 the evaluator using its own aggregation instead of the shared function | T8 |
