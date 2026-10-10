# v0.2.1 H7 (signal identity): acceptance criteria

Status: **criteria fixed before any validation runs.** This file is committed on its
own, before the tests and the code it describes. Written 2026-10-10 on branch
`claude/v0-2-1-gauntlet-fixes-13f5e7` (from `main` at `3dec26f`).

## Problem

In the v0.2 calibration a known false positive counts as *flagged* when its signal
verdict (without `flag_excluded_tests`) is `REFUTED`. The definition never asks
whether the analyzed signal is the catalogued one. The v0.2 post-mortem
(`calibration/v0.2/POSTMORTEM.md`, `main` at `3dec26f`) records one flagged false
positive, TOI-1481.01, whose search found a period with a relative error of 0.23
from the catalogued period (not an alias). That target was counted as flagged
without its catalogued signal being analyzed.

H7 corrects **the measure, not the engine**: a known false positive counts as
flagged only if the analyzed signal is the catalogued one. The search, the gauntlet,
the holdout, the per-target verdict and the per-target report do not change. The goal
is to measure correctly; if the honest count of flagged false positives drops, that
is a result, not a debt.

## Definition

Two new, opt-in fields in the calibration `pass_criteria`:

- `flag_requires_signal_recovery: bool`, default `false`.
- `flag_signal_period_factors: list[float]`, default `[1.0, 2.0, 0.5]` (P, 2P, P/2).
  Every factor must be `> 0`. Used only when the first field is `true`.

A false positive's signal is *recovered* when, for some factor `f` in
`flag_signal_period_factors`,

    |P_found - f * P_pub| / (f * P_pub) <= period_tolerance

where `P_pub` is `period_comparison.published_period_days` and `P_found` is
`period_comparison.found_period_days` of the target's `verdict.json`, and
`period_tolerance` is the claim's existing tolerance. **No new threshold.** The
boundary is inclusive, as for *recovered* planets. A missing period (analysis error,
no candidate, no published period) means *not recovered*.

With `flag_requires_signal_recovery: true`, a false positive is *flagged* only if its
signal is recovered **and** its signal verdict is `REFUTED`. The denominator stays
**every** false positive: "signal not recovered" stays in the count. Planets
(*recovered*, *refuted planets*) are computed by the same code as before.

With the field absent or `false`, every claim evaluates exactly as before.

## Acceptance criteria

H7 is accepted when every case below holds on the development seeds, the full
existing test suite passes unchanged, and `ruff check` / `ruff format --check` pass.

### A. Unit cases on fabricated results (`tests/test_calibration_signal_identity.py`)

Counted as **flagged** (flag on):

- A1. FP `REFUTED`, found period equal to the published period (error 0).
- A2. FP `REFUTED`, found at 2P and at P/2, within tolerance.
- A3. FP `REFUTED`, relative error exactly equal to the tolerance, for P, 2P and P/2
  (inclusive boundary; values exactly representable in binary floating point, so the
  check is not decided by rounding).

Counted as **not flagged, signal not recovered** (flag on):

- A4. FP `REFUTED`, found period at 0.23 relative error from the published period
  (fabricated values of the TOI-1481.01 type).
- A5. FP `REFUTED`, found at 3P or at P/3 (outside the decided factors).
- A6. FP `REFUTED`, error just above the tolerance.
- A7. FP with `status: ERROR`, or without a found period, or without a published
  period.

Counted as **not flagged, signal recovered**:

- A8. FP with the signal recovered but signal verdict other than `REFUTED`. H7 never
  creates a flag.

Unchanged (regression):

- A9. With the field absent or `false`: the results of `tests/test_calibration_v02.py`
  and `tests/test_calibration_eval.py` do not change (those files are not edited), and
  the criterion name stays exactly as before.
- A10. Planets: `recovered planets` and `refuted planets` are identical with the flag
  on and off, for the same results.
- A11. Monotonicity property: for randomly generated result sets (development seeds),
  `flagged with H7 ⊆ flagged without H7`, and the denominator is the same.
- A12. Reporting: the criterion is named
  `flagged false positives (signal recovered)`, or
  `flagged false positives (signal recovered; without <tests>)` with exclusions.
  `information` carries `false_positives_signal_not_recovered` (targets and count) and
  `flagged_without_signal_identity` (the count under the v0.2 definition). Every
  `targets` row carries `signal_recovered` (FP: bool; planet: `None`).
  `summary_markdown` has a "Signal recovered" column and a sentence stating the
  definition change since v0.2, the factors, how many false positives were not
  recovered and how many would count as flagged under the v0.2 definition.
- A13. Schema: a factor `<= 0` (and an empty factor list) is rejected; a v0.2 claim
  without the new fields loads with the defaults.

### B. End to end on synthetic data (`tests/test_calibration_signal_identity_e2e.py`)

Synthetic scenario data, full analysis with the fast test plan, `build_result`, then
`TessCalibrator.evaluate`. Every case **first checks its premise** (which period the
search found). If the premise does not hold, the test **fails**; it is never skipped.

- B1. **Not recovered.** New scenario `fp_variability_dominates`: a weak eclipse
  (P = 2.9 d, 1000 ppm) plus a stronger sinusoid (4000 ppm) at a period that is not
  commensurate with the eclipse, inside the fast search range; published period = the
  eclipse period. Premise: the search found a period that is not P, 2P or P/2 of the
  eclipse. Expected: `signal_recovered` is false and the target is not flagged, even if
  its verdict is `REFUTED`.
- B2. **Not recovered.** `eb_secondary` with a deliberately wrong published period
  (not P, 2P or P/2 of the injected period). Expected: same verdict as with the right
  period, signal not recovered, not flagged.
- B3. **Counted as before.** `eb_secondary` and `eb_odd_even` with the correct
  published period. Premise: the found period matches the injected period. Expected:
  `REFUTED` and flagged, with the flag on and off.
- B4. **Alias.** `eb_equal` (equal eclipses), published period = injected P.
  Premise: the found period matches P or P/2. Expected: signal recovered.
- B5. **Planets unchanged.** `planet` and `planet_three_years`: `recovered` and
  `refuted planets` identical with the flag on and off.

## Seeds

- **Development set: seeds 0 to 9.** Unit and property tests may use all of them.
  The end-to-end tests use seeds 0, 1 and 2 of that set (each scenario runs a full
  analysis, so the subset keeps the suite fast).
- **Confirmation set: not generated and not used now.** Per rule 5 of the v0.2.1
  plan it is reserved, derived later from a future drand round and run once, with the
  code frozen. Nothing in H7 depends on it.

No known target (real data) is used to validate H7 or to choose any value.

## Effect on the v0.2 lock (expected, not a regression)

On this branch `refute verify calibration/v0.2/self_claim.yaml` reports `TAMPERED`,
for two components:

- **code**: any change under `src/`, `pyproject.toml` or `uv.lock` changes the code
  hash. This holds for every v0.2.1 change, not only H7.
- **claim**: the lock hashes the *resolved* claim (`LoadedClaim.canonical()` in
  `src/refute/core/claim.py`), and `resolve_pass_criteria` fills every default of
  `CalibrationCriteria`. Adding the two fields above therefore changes the resolved
  `claim_sha256` of older claims. The same happened to the v0.1 claim when v0.2 added
  `flag_excluded_tests`.

The lock files, the claim file and the evaluation of the v0.2 claim (the new field
defaults to `false`) are unchanged. The v0.2 calibration is verified at its locked
commit `cc9d104` ("calibration v0.2: lock the self-claim"; code hash `2cd8b5c1…`),
which becomes the protected tag `v0.2.0-calibration-lock` at release. (`e176ac3`, the
commit recorded inside the lock, has the same code but not the lock file, so
`verify` there reports FAIL.) No test runs `verify` on `calibration/v0.2/`. Keeping
the canonicalization stable when the claim schema gains optional fields is recorded
as a future-phase item (milestone v1.0); nothing is implemented now.

## Risks and open items

- **Planets**: no change in code paths; A10 and B5 check it.
- **Flagged false positives**: can only fall or stay equal (A11). This is intended.
  The "at least N flagged" criterion becomes harder; that is not compensated in any
  other hypothesis.
- **Factors P, 2P, P/2**: a different signal could, by chance, land on one of these
  multiples within the tolerance and count as the same signal. Unlikely at the
  tolerance used (0.001), not impossible. A future mitigation is to check the epoch
  as well; **open item, out of scope for H7.**
- **Imprecise catalogue period**: a false positive whose catalogued period is off by
  more than the tolerance is "not recovered" even with the right signal. It stays
  visible in the report (list of not-recovered targets) and never becomes a flag.
  **Open item.**
- **Coverage**: "signal not recovered" stays in the denominator; `signal_recovered`
  is available for the coverage requirement defined later in v0.2.1.

## Out of scope

H4, H3, H1, H9(a), H2, the report sentence (#23) and the coverage requirement each
get their own plan and approval.
