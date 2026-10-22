# X2e: results (development evidence, not validation)

Run as authorized by the maintainer on 2026-10-22, exactly as in
[../../x2e-execution-package.md](../../x2e-execution-package.md), under
[../../x2e-declaration.md](../../x2e-declaration.md) (code `d1929fe`), with the resumption
pre-approved in [klucilla/refute#166](https://github.com/klucilla/refute/issues/166) (not used: the lot
ran once, without interruption). Nothing here validates an error model, `R_min` or a configuration;
nothing is adopted; no threshold or gate changes.

## The lot

- **4000 curves, 9200 rounds**, in **0.92 h** on 22 workers (processors 8 to 31), started 2026-10-22
  19:01 UTC; no failure, no temporary file left, the ceiling (3 h) not reached; the check clean.
- [lot-run-report-20261022T190121451603Z.json](lot-run-report-20261022T190121451603Z.json),
  [lot-manifest.json](lot-manifest.json) (lot `x2e`), [lot-record-digests.json](lot-record-digests.json)
  (SHA-256 `64febf24e4307e80816824b1666d6993bd0834c29c25c6c8c1912e6b365ace1f`).
- **The evaluations, as declared:** X2e alone, [x2e-evaluation.json](x2e-evaluation.json) (SHA-256
  `70552eed9aa1e96db057b456427b472112381d7070d3c185276a09e8dd001d9b`), and **pooled with X2's stored
  rows** of the same cells, [x2e-pooled-evaluation.json](x2e-pooled-evaluation.json) (SHA-256
  `27b5a23af95574db51cf6ea604b33ea375b16464044d6adace1be3ef19916ee1`), both with the corrected
  evaluator (intervals and verdicts stored apart); the lot's identity check passed.

## X2-B, pooled (40 cases per cell; the deciding analysis)

| cell | case-years (excluded) | cases contributing | `ρ_1` (design 1.2) | `ρ_2` (design 1) | `ρ_h` (design 1) |
|---|---|---|---|---|---|
| AR(1), no variability | 92 (36) | 24 of 40 | 1.25 [1.21, 1.28]: SD calibrated as designed, MAD [1.22, 1.38] not determined → **not determined** | 1.26 [1.13, 1.45], MAD [1.21, 1.43] → **overestimated** | 1.08 [1.06, 1.12] → **not determined** |
| white, no variability | 92 (49) | 17 of 40 | 1.34 [1.29, 1.38] → **not determined** | 1.25 [1.17, 1.36], MAD [1.20, 1.38] → **overestimated** | 1.04 [0.97, 1.08], MAD [1.00, 1.09] → **calibrated** |

- **No cell is `underestimated`.**
- **`e_pred,2` is overestimated in these two cells too**, as in the two variability cells of X2
  (1.25 and 1.21): with X2e, **`ρ_2` is overestimated in all four cells**, between 1.21 and 1.26, both
  scales agreeing. The excess is not specific to a regime.
- `e_hidden` is calibrated in `white, no variability`; elsewhere not determined.
- **Which case-years decide:** the contributing case-years are mostly `three_years` (36 of 56 in
  AR(1), 36 of 43 in white); `two_years` contribute 18 and 5, `few_train` 2 and 2. Of the excluded
  ones, 20 of 36 (AR(1)) and 24 of 49 (white) had no measured realization. These verdicts therefore
  rest mainly on the three-year layout.
- **X2e alone** (not deciding): 11 and 8 contributing cases of 20, so every ratio is not determined;
  the new cases contribute at about X2's rate (13 and 9 of 20).
- The subset `same` with `L ≥ 0.8` (not deciding) gives values within the intervals above.

## X2-A, pooled

| cell | FAIL / rounds measured | the FAIL's causes |
|---|---|---|
| AR(1), no variability | 19 / 5190 | none 11, imprecise extrapolation 3, wrong candidate 2, attenuation 2, inflated 1 |
| white, no variability | 94 / 3894 | **wrong candidate 72**, inflated train depth 11, none 7, imprecise extrapolation 3, attenuation 1 |

The rounds with `Z_train ≥ 3`: AR(1) 219 (none 114, imprecise extrapolation 60, wrong candidate 40);
white 335 (wrong candidate 148, none 107, imprecise extrapolation 68). The pattern of X2 holds without
variability: a wrong candidate and an imprecise extrapolation dominate; the attenuation in the
processing is rare there (it dominated with variability). X2e alone: FAIL 10 (AR(1)) and 57 (white, 49
of them a wrong candidate).

## Section 7 (descriptive, pooled; no claim)

| cell | decision 1: refused by capacity / would pass with `σ_meas` | decision 2: refused / would pass | structural | measured |
|---|---|---|---|---|
| AR(1), no variability | 1662 / 803 | 1222 / 643 | 44 | 5190 / 9200 |
| white, no variability | 1443 / 958 | 1195 / 773 | 15 | 3894 / 9200 |

## What follows

- **Specification C** ([../../spec-c-error-model.md](../../spec-c-error-model.md)) now has, in the
  cells without variability, data never used before (X2e) and, pooled with X2, determined cells. The
  excess of `ρ_2` in all four cells argues for a cause in the decision-2 model as a whole rather than
  in one regime; whether one of spec C's candidates removes it is spec C's own analysis (its own
  authorization), on X2e's records for these cells, and on a replicate with new seeds for the cells
  with variability (spec C, C6). Not done here.
- X3 still waits for the correction of the error model.

## Scripts

[../scripts/x2e_view.py](../scripts/x2e_view.py) (the tables above), with the package's scripts.

## The archive

The records are archived on the maintainer's Drive, folder `arquivo-v0.2.1-x2e-lot`: one zip
(`x2e-lot-20261022T190119Z-d1929fe.zip`, SHA-256
`9b598df737d330d2e23d9958e1a349791ef8bd4a6cb4144aa178f356097776de`, 4003 members: the run folder and the
run's log), checked against the committed record digests before and read back from the Drive after;
the manifest [archive-MANIFEST.sha256](archive-MANIFEST.sha256) and the script
[../scripts/archive_x2e_lot.py](../scripts/archive_x2e_lot.py). The run folder was then removed from
`.cache`.
