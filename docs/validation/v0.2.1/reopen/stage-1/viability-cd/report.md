# The C/D viability lot: the report (2026-10-27)

The declaration: [README.md](README.md) (as amended at 2ba9e4a); the code and its acceptance:
[../../../population/viability-cd-acceptance.md](../../../population/viability-cd-acceptance.md)
(amendments A and B; 41 tests, 25 of 25 sabotages, Codex agreed); the geometry list:
[geometry-list.json](geometry-list.json) (491c955); the lot's issue: #173. Run under the
maintainer's authorization 2 of 2026-10-27. Synthetic planets on geometries derived from real TESS
metadata: a screening of the holdout, not a discovery and not a verdict on any real target.

## 1. The outcome, by the rules fixed before the run

| | C (three years, every sector) | D (four or five years, no variability) |
| --- | --- | --- |
| Outcome (section 6) | **INDETERMINATE** | **INDETERMINATE** |
| Destination (section 9) | the step over C | the step over D |
| The step (specification C's twelve pairs) | **applies; no pair meets the PASS rule** | **applies; no pair meets the PASS rule** |
| Final reading | **ended** | **ended** |

**By the investment rule fixed before the lot (section 9), the current effort ends as not
approved**, the hypotheses recorded for future research (section 6 below). This is an investment
rule, **not a proof** that a corrected method, another capacity model or a domain with more years is
infeasible. No proposal is allowed by the table; the decision is the maintainer's.

## 2. R1, as measured (specification B per target; no planet missing)

| | C white | C AR(1) | D white | D AR(1) |
| --- | ---: | ---: | ---: | ---: |
| planets | 360 | 360 | 120 | 120 |
| spec-B PASS | 56 | 53 | 27 | 38 |
| one-sided 95% L of PASS | 0.125 | 0.117 | 0.164 | 0.247 |
| spec-B FAIL (holdout diagnostic) | 0 | 0 | 0 | 0 |
| one-sided 95% U of FAIL | 0.008 | 0.008 | 0.025 | 0.025 |
| legacy aggregation PASS (reference) | 108 | 118 | 61 | 69 |

The PASS hurdle (L ≥ 275/360, at least 289 of 360 and 100 of 120) is not met; the FAIL condition
(R2-KTN's U < 275/360, or FAIL's L > 0.10) is not met either: hence INDETERMINATE. **No planet of
the lot was a holdout FAIL** (in R1, R2 or any pair).

By regime (C): without variability 55 (white) and 51 (AR(1)) PASS of 180; **with variability 1 and 2
of 180**. By years: C (three) 109 of 720; D (four) 41 of 140, (five) 24 of 100. Rounds PASS: C
483 of 2160 (22.4%); D four years 227 of 560 (40.5%), five years 189 of 500 (37.8%).

## 3. The barriers (section 4's rows; counts of rounds)

| Row (barrier) | C | D |
| --- | ---: | ---: |
| 17 decided PASS/FAIL | 483 | 416 |
| **11 `insufficient_capacity_train` (K)** | **1566** | **629** |
| 13 `insufficient_capacity_hidden_noise` (N) | 88 | 15 |
| 3 `train_noise_undetermined` (G) | 13 | 0 |
| 4, 5 the train candidate's SNR, duration ratio (S) | 4 | 0 |
| 10 `train_replicas_below_r_min` (K) | 2 | 0 |
| 7 timing (T) | 2 | 0 |
| 8 window fraction (W) | 1 | 0 |
| 12 `hidden_noise_undetermined` (N) | 1 | 0 |

**Row 11, the train's capacity by the predicted error, is the dominant first stopping barrier**
(72.5% of C's rounds, 59.3% of D's); the non-PASS targets are undecided mostly by row 11 alone (C
519 of 611, D 161 of 175). Timing (row 7), the train search and the windows barely appear. A
barrier is the first stopping point, not a causal separation (section 4 of the declaration).

## 4. R2 (optimistic substitution) and R3 (the evaluator's oracle): descriptive

| PASS of n | C white | C AR(1) | D white | D AR(1) |
| --- | ---: | ---: | ---: | ---: |
| R2-K (rows 6, 10, 11) | 320 (L 0.858) | 309 (L 0.825) | 112 (L 0.883) | 114 (L 0.904) |
| R2-KT | 320 | 309 | 112 | 114 |
| R2-KTN (rows 6, 7, 10 to 13) | 350 | 356 | 120 | 120 |
| R3, oracle-detectable every year | 306 | 325 | 120 | 120 |

R2 assumes a PASS where none was measured; it chooses, validates or justifies nothing (section 5).
R3 is the evaluator's diagnostic oracle with perfect windows (the truth never reached the engine),
not T4's or any method's performance and not an upper bound. R3 shows that, with perfect windows,
this estimator detects the signal every year for most of these planets; it does not show what the
engine, or any corrected method, could recover.

## 5. Section 9's step (specification C's twelve pairs on the lot's records; no generation)

Applicable to both (INDETERMINATE, rows 11 and 13 present). The best single pairs:

| | C white | C AR(1) | D white | D AR(1) |
| --- | ---: | ---: | ---: | ---: |
| today's `E1.0+E2.0` | 56 | 53 | 27 | 38 |
| the highest count of any single pair, per column (not one pair across columns) | 83 | 65 | 37 | 43 |
| the envelope (descriptive upper bound) | 86 | 65 | 37 | 43 |
| needed (with complete records) | 289 | 289 | 100 | 100 |

**No pair meets the PASS rule in either noise model** (the envelope, an upper bound of every pair,
is far below), and no pair produced a FAIL. The per-column highest counts come from different
pairs (for C: 83 white with `E1.dp0.nomargin+E2.median`, which gives 64 in AR(1); 65 AR(1) with
`E2.dp0`, which gives 81 white). The step's cost: about 1.5 s of CPU. **At the committed pair
`(b, s)`, none of C2's candidate pairs meets the screening rule. Row 11 remains the dominant first
stopping barrier; this comparison does not isolate the contributions of the error estimator and of
the capacity threshold.**

## 6. Hypotheses recorded for future research (none adopted, none authorized)

- Decision 1's capacity rule (`s_pred,1` against the threshold at `b = 0.585`, `s = 2.883`) is the
  dominant first stopping point in these geometries; whether a recalibrated `(b, s)` pair or another
  capacity model would change that is open (neither is specified nor tested here). A released
  round's measured outcome is in the records (the calibration measures despite the decisions), which
  a future, declared reading could use; this report does not compute it.
- C's variability regime had a low PASS rate (3 of 360); its cause is not isolated here.
- D's per-round PASS (about 40%) is higher than C's (22%), but specification B needs every year;
  C against D without variability (Newcombe, two-sided 95%): R1 −0.033 [−0.140, 0.070] (AR(1)),
  +0.081 [−0.023, 0.177] (white); R2-KTN 0 [−0.021, 0.031]: no difference established.
- Identity: C 4 rounds flagged (train period more than 1% from the injected), 17 not identifiable;
  D none.

## 7. Operations

- **Determinism** (section 7): the first 24 (C) and 12 (D) tasks' curves built three times (this
  process, 1 worker, 22 workers): all agree.
- **Environment**: the record before and after the lot byte for byte equal (SHA-256 ba45540c…;
  `uv.lock` a49bfdf2…).
- **viability-c**: the first invocation stopped submitting after 575 of 720 tasks on a
  `PermissionError` while replacing its consumption record (most likely the agent's progress check
  reading that file at that moment); no failed task, no ceiling, no cost-check stop. **The one
  pre-approved resumption** was recorded on #173 before it ran and completed the 145 tasks; the
  full check found no problem. viability-d ran in one invocation; its full check found no problem.
- **Cost checks** (10%): C 46.0 s per curve, projected 9.2 LP-h and 0.42 h (ceilings 37.0 and 1.70);
  D 205.8 s, projected 13.7 LP-h and 0.62 h (30.8 and 1.40). Neither stopped.
- **Measured consumption** ([consumption.json](consumption.json)): C 8.33 LP-h, 0.39 h; D 12.28 LP-h,
  0.58 h; the lot 20.6 LP-h and 0.97 h, within the planned ceilings. **The balance, accounted with
  measurements, proxies and estimates**, from [balance.json](balance.json)'s 3297.9 LP-h and 134.0 h
  unspent: minus the lot (measured, 20.6 LP-h, 0.97 h), the determinism checks (estimated, 0.5 LP-h,
  0.05 h) and step 1's test and sabotage runs (no full suite; estimated, 2 LP-h, 1.0 h): **about 3275
  LP-h and 132 h unspent** of 4000 LP-h and 200 h.
- **Files**: [evaluation.json](evaluation.json) (every reading per target and round),
  [summary.json](summary.json), [consumption.json](consumption.json), the determinism checks and the
  environment record, [lot-file-digests.json](lot-file-digests.json) (every file of the lot
  folder). **The raw lot (14.8 MB, 2897 files) is not in git:** archived to the Drive
  (`arquivo-v0.2.1-viability-cd-lot`, zip SHA-256 149783e2…e364, its manifest
  [lot-archive-MANIFEST.sha256](lot-archive-MANIFEST.sha256)), checked from the Drive's copies by
  `scripts/archive_lot.py` (no problem; Codex verified the digests and the local zip, the Drive
  being outside its sandbox). The scripts `evaluate.py`, `summarize.py` and `consumption.py` were
  reformatted by ruff after they ran (formatting only).

## 8. What this does not show

No safety against false PASS or false FAIL was measured (no false positives, no curves without a
transit, G1 and the global gate not run); a holdout FAIL here would be a diagnostic, not a REFUTED
verdict. The FAIL of nothing and the INDETERMINATE of both say nothing on a corrected method (T4, a
repair of the hidden noise, another capacity model, a changed search) or on geometries not
selected; D's lot (12 geometries of four or five years, without variability) never replaces a full
validation.
