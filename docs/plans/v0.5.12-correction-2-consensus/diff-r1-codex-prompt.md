Same rules as before in this thread (read-only, no network, never any path on the K: drive, no run of M1, M2, the control, the tests or any phase unit, and none of the seeds already used). This is a NEW closed question, the review of the exact `src/` diff (round 1 of up to 3).

The maintainer ADOPTED correction 2 revision 1 (`docs/plans/v0.5.12-spec-correction-2-r1.md`, commit `38c02ae`, SHA-256 `c24e7fd936929d713f53755b53233cc453e3e65a043f887b2f9e1511869873db`). The tests were then pushed before any `src/` change (`98117ef`): `tests/test_v0512_223_cases.py` (#223's case record, `docs/validation/v0.5.12/step2/cases.json`) and `tests/test_v0512_correction2.py` (revision 1's section 7), with ten strict expected failures on the approval code (JUnit `docs/validation/v0.5.12/step2/junit-suites-before-src.xml`: 67 tests, 0 failures, 10 xfail).

The proposed diff, NOT committed, is `docs/validation/v0.5.12/step4/src-diff-proposed.patch` (16,649 bytes, SHA-256 `0d15040e30b73d257973d215e42fe0d412eba03ec4177ca5cc7d110cde23eb0b`). The working tree holds it. It changes `src/refute/packs/tess/screen_d5.py` (a new `_noise_f1`; `_f1_box`'s noise, per-parity variance, numerator and metrics; the record field `spec_correction_2_sha256`), removes the ten markers, and replaces four tests of `tests/test_v0511_screen.py` that asserted the frozen F1 values (revision 1, section 6, and B2) by tests against the independent oracle `tests/v0512_oracles.py`. With it: the three suites give 97 tests, 0 failures, 0 errors, 0 skipped.

## The one question of this round
Does the diff implement revision 1's section 4 exactly (the estimator, the positive prefix sum for C, the effective epoch count, the guards and reasons, the metrics and their keys, the record's hash field), change only version 5's F1 (F2, U1 and versions 1 to 4 untouched), and remove the markers and replace the frozen-value tests as section 6 and the order of steps allow? Check with path:line evidence. Do not reopen the adopted correction; a new finding outside this question is a recorded item.

## Answer (English, at most about 45 lines)
- OVERALL: SURVIVED / WEAKENED / REFUTED for committing this exact diff.
- Each blocking item with its exact fix (the replacement code or text).
- Recorded items, if any.
