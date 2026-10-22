# X2e: the extension of X2's cells without variability (declaration, not run)

The maintainer's decision after X2 (2026-10-22, item 2): X2-B left the cells without variability
`not determined` for too few contributing cases (13 and 9 of 20). X2e extends them, **before** any
code of a correction of the error model, to separate coincidence from cause
([spec-c-error-model.md](spec-c-error-model.md)). Written before X2e's lot exists; its rules do not
change after. Development evidence, not validation.

## 1. What is added

- **Cells:** white without variability, AR(1) without variability (the two that were not determined).
- **Cases:** from a new prefix, `refute-v0.2.1-x2-2` (never used), **20 per cell by X2's own rule**
  (the planets of the bands near and measurable, ordered by band and index, every `n // 20`-th, the
  first 20): per band 5 `two_years`, 3 `three_years`, 2 `few_train`, as X2. The maintainer's estimate
  was about 24 (AR(1)) and 34 (white) cases in all; X2's rule in whole blocks of 20 keeps X2's
  composition and gives 40 per cell, the nearest whole block above both estimates.
- **Realizations:** 100 per case, as X2; the realization's seed: the first 8 bytes, big-endian, of the
  SHA-256 of `refute/v0.2.1/stage-1/X2e/refute-v0.2.1-x2-2/<group>/<case>/<j>` (the prefix is in the
  seed because case ids repeat across prefixes).
- **Rounds, records, information contract:** X2's, unchanged (x2-declaration.md, sections 2 to 4),
  with the record's format `refute-v0.2.1-x2e-record/1` and its target under the new prefix.

## 2. The analysis (fixed now)

- **Pooled:** X2-A and X2-B (x2-declaration.md, sections 5 to 7), exactly as declared there, over
  **X2's committed rows of these two cells** (`x2/x2-evaluation.json`, read as stored, never
  recomputed) **and X2e's rows**, each case named by its prefix: 40 cases per cell. X2-B's rule needs at
  least 15 contributing cases per cell, as in X2.
- **X2e alone:** the same analysis on X2e's 20 cases per cell, reported beside, not deciding (it
  shows whether the new cases behave as X2's).
- **For specification C:** X2e's records carry every candidate's inputs (`train_var_rep`,
  `hidden_var_rep`, `grid_dp`, `n_pred`, `m_beta`); the candidates are judged on X2e's data in these
  two cells as spec C declares (its section C6), by its own analysis, after its own authorization.
- No threshold or gate changes; X3 waits.
