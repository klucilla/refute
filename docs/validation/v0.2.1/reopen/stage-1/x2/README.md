# X2: results (development evidence, not validation)

Run as authorized by the maintainer on 2026-10-22, exactly as in
[../x2-execution-package.md](../x2-execution-package.md), under the declaration
[../x2-declaration.md](../x2-declaration.md) (revision 2) committed before the lot (`8b54384`), with
the resumption pre-approved in [klucilla/refute#165](https://github.com/klucilla/refute/issues/165)
(not used: the lot ran once, without interruption). Nothing here validates `R_min`, specification B,
an error model or a configuration, and nothing is adopted.

## The lot

- **8000 curves, 21 200 rounds**, in **4.03 h** on 22 workers (processors 8 to 31), started
  2026-10-22 11:06 UTC; no failure, no temporary file left, the ceiling (11 h) not reached; the lot's
  check (`x2_study.py check`) clean. Code `8b54384`, the manifest's code digest `2918fea5…`.
- The run report, the manifest and the 8000 records' SHA-256: [lot-run-report-20261022T110611671408Z.json](lot-run-report-20261022T110611671408Z.json),
  [lot-manifest.json](lot-manifest.json), [lot-record-digests.json](lot-record-digests.json) (SHA-256
  `3a5254c794c9beac750ea0358f116f850f70dbe3f4c1a5d50774978b3e2e6187`). **The records are archived**
  (2026-10-22, the maintainer's decision after X2, item 6) on the maintainer's Drive, folder
  `arquivo-v0.2.1-x2-lot`: one zip (`x2-lot-20261022T110605Z-8b54384.zip`, SHA-256
  `7a3699d69dc6dec905f1c98034f30e290f1140a63a3d6c03addcb49c7da223ec`, 8003 members: the run folder
  and the run's log), checked against the committed record digests before and read back from the
  Drive after (every member's SHA-256 equal to its source); the manifest
  [archive-MANIFEST.sha256](archive-MANIFEST.sha256) and the script
  [scripts/archive_lot.py](scripts/archive_lot.py). The run folder was then removed from `.cache`.
- **The evaluation**, `x2_study.py evaluate`, its identity check passed (the same code, plan,
  configuration and environment as the lot's): [x2-evaluation.json](x2-evaluation.json) (SHA-256
  `8e91fc4f1aea6bf85d05d6e3cb41ae7bbe86976f38a7645e29ce66aeffa70597`, with every round's row).

**A defect of the evaluator, found while reading the output:** `x2_evaluate.evaluate` stored each
ratio as `{**intervals, **cell_verdict(...)}`, and the verdict's keys `sd` and `mad` overwrote the
intervals' in the output (the verdicts were computed from the intervals first, so they are right;
only the stored intervals were lost). The evaluator was **not** changed (it is part of the lot's
identity). [scripts/x2_intervals.py](scripts/x2_intervals.py) recomputes the intervals from the
stored case-year statistics with the committed functions (`cell_interval`, `cell_verdict`, the
bootstrap's fixed seed), and checks that every stored verdict is reproduced: **36 of 36, no
mismatch** ([x2-intervals.json](x2-intervals.json), SHA-256
`cdca9969c956e6d60a3a1395ca0286587c608f5e1b04dc34b66c45c9263503b9`). The evaluator was corrected
afterwards (2026-10-22, the maintainer's decision after X2, item 4) for any later use: each ratio now
stores `sd_interval`, `mad_interval`, `sd_verdict`, `mad_verdict` and `verdict` apart, with its own test
(failing before the fix, passing after); X2's recorded results above are unchanged.

## X2-B: the calibration of the uncertainties (decided by the SD of `d_hidden − d_twin`)

`m_beta` = 1.2 (the design of `ρ_1`). The interval is the cell's 95% cluster-bootstrap interval.

| cell | case-years (excluded) | cases contributing | `ρ_1` (design 1.2) | `ρ_2` (design 1) | `ρ_h` (design 1) |
|---|---|---|---|---|---|
| AR(1), no variability | 46 (17) | 13 of 20 | not determined (fewer than 15 cases) | not determined | not determined |
| white, no variability | 46 (24) | 9 of 20 | not determined (fewer than 15 cases) | not determined | not determined |
| AR(1), variability | 60 (1) | 20 | 1.40 [1.33, 1.43]: SD overestimated, MAD [1.31, 1.52] not determined → **not determined** | 1.25 [1.15, 1.35]: SD and MAD [1.19, 1.33] → **overestimated** | 1.12 [1.08, 1.16] → **not determined** |
| white, variability | 60 (6) | 20 | 1.34 [1.29, 1.39] → **not determined** | 1.21 [1.16, 1.28]: SD and MAD [1.13, 1.31] → **overestimated** | 1.05 [1.02, 1.10]: SD calibrated, MAD [1.00, 1.20] not determined → **not determined** |

- **No cell is `underestimated`:** no safety finding of an error smaller than the scatter.
- **`e_pred,2` is overestimated in both variability cells** (by about 20 to 25%, beyond the
  tolerance, both scales agreeing): decision 2 refuses rounds a calibrated error would let through.
- **The cells without variability are not determined** because too few case-years have 30 measured
  realizations: the excluded ones are `two_years` and `few_train` (AR(1): 11 and 6 of 17; white: 17
  and 7 of 24), whose rounds are mostly never measured (rounds measured: 2612 of 4600 and 1884 of
  4600, against 5191 and 4980 of 6000 with variability). Of the excluded case-years, 10 of 17 (AR(1))
  and 15 of 24 (white) had no measured realization at all, and the others between 1 and 27 of 100
  (Codex's review): their contribution is low and it is uncertain how far more realizations would
  raise it. At the observed contribution rate about **24 cases** (AR(1)) and **34 cases** (white)
  would give 15 contributing cases (`ceil(15 / (13 / 20))`, `ceil(15 / (9 / 20))`: an estimate of the
  total, without a guarantee of 15). **Requested, not run.**
- The subset `same` with `L ≥ 0.8` (reported, not deciding) gives, in the variability cells, values
  within the intervals above (`x2-evaluation.json`); in the cells without variability it has fewer
  than 15 cases too.

## X2-A: geometry and identity

**The FAIL** here is the FAIL rule on each round's measurement with the capacity decisions **not
enforced** (as declared): it is not the study's false FAIL, which passed the gates first.
"Wrong candidate" is X2-A's diagnostic class (the train candidate's identity not `same`), not a
verdict. **These are not the engine's false FAIL** (added after the maintainer's review of
2026-10-22, [../after-x2e/README.md](../after-x2e/README.md), item 4): of the measurement FAIL, those
that passed both capacity decisions as recorded at the lot's configuration (`b = s = 0`) are 30 of 138
(`AR(1), variability`; 21 of its 58 wrong candidates) and 6 of 76 (`white, variability`; none of its
9); the full engine's outcome also depends on the calibrated thresholds, the other gates and spec B's
aggregation.

| cell | FAIL / rounds measured | the FAIL's causes |
|---|---|---|
| AR(1), no variability | 9 / 2612 | none 4, wrong candidate 2, attenuation 1, extrapolation 1, inflated 1 |
| AR(1), variability | 138 / 5191 | wrong candidate 58, **attenuation in the processing 56**, none 14, inflated train depth 10 |
| white, no variability | 37 / 1884 | **wrong candidate 23** (few_train 11, two_years 6, three_years 6), inflated train depth 8, extrapolation 3, none 2, attenuation 1 |
| white, variability | 76 / 4980 | **attenuation in the processing 40**, none 24, wrong candidate 9, inflated 2, extrapolation 1 |

- **The FAIL are concentrated:** 260 FAIL in 89 case-years; in `AR(1), variability` two case-years
  hold 77 of the 138 (`planet-near-correlated-0220`, 2019: 40; `planet-measurable-correlated-0210`,
  2019: 37, every one of these 37 a wrong candidate, an `other` period, its windows 1.2 to 1.7
  durations off the injected transits). Per-case rates are
  in `x2-evaluation.json` (`case_years`); no population rate is claimed.
- **The rounds with `Z_train ≥ 3`** (the X0c kind): without variability, `imprecise extrapolation`
  (26 of 102, AR(1); 41 of 180, white) and `wrong candidate` (20 of 102; 72 of 180), with many `none`
  (53; 60); with variability, **`attenuation in the processing`** (78 of 165, AR(1); 108 of 137,
  white) and `wrong candidate` (78 of 165; 25 of 137).
- **Identity across all rounds with an ephemeris:** `other` periods are frequent without
  variability (white: 2080 of 4245 rounds with an ephemeris; AR(1): 1113 of 4539), much less with it
  (white: 227 of 5068; AR(1): 351 of 5502); aliases are rare (at most 9 per cell). Most of those
  rounds are not measured (their cause `twin unavailable`).
- **What this answers of X0c:** of the four causes left open, the ones these cells show most are a
  wrong candidate and an imprecise extrapolation without variability (the `two_years` and
  `few_train` layouts), and an attenuation in the processing (the twin, measured with the hidden
  year's detrending and the train fundamentals, loses depth) with variability; an inflated train
  depth is the least frequent. The cause is the **dominant** factor, and factors can coexist: among
  the `attenuation in the processing` rounds with `Z_train ≥ 3`, the placement also lost more than 20%
  (`L < 0.8`) in 11 of 78 (AR(1), variability) and 46 of 108 (white, variability) (Codex's review).
  Twenty cases per cell; these are the cells' patterns, not population rates.

## Section 7 (descriptive only, no claim)

| cell | decision 1: refused by capacity / would pass with `σ_meas` | decision 2: refused / would pass | structural impediments | rounds measured |
|---|---|---|---|---|
| AR(1), no variability | 775 / 373 | 561 / 279 | 5 | 2612 / 4600 |
| AR(1), variability | 3144 / 2105 | 2572 / 1702 | 77 | 5191 / 6000 |
| white, no variability | 689 / 471 | 561 / 376 | 10 | 1884 / 4600 |
| white, variability | 3137 / 990 | 2857 / 813 | 71 | 4980 / 6000 |

Releasing those rounds is **not** presumed good: X2-A shows the FAIL these cells hold (attenuation
and wrong candidates among the measured rounds), and a released round can be a new PASS or a new FAIL.
`ρ` by mechanism and by `n_pred`: `x2-evaluation.json` (`descriptive`).

## What follows (the declaration, section 8)

- **X2-B is not calibrated in every cell** (`ρ_2` overestimated with variability; the cells without
  variability not determined): a change of the error model is to be **proposed** with its own
  specification, tests and Codex review, and X3's definitive calibration uses the corrected model.
  Nothing of that is done here.
- **The cells without variability:** the size needed (about 24 and 34 cases) is requested, not run.
- **X2-A** points at what to study next: the identity and the extrapolation of the train candidate in
  the `two_years` and `few_train` layouts, and the attenuation of the measured depth by the processing
  with variability. Any change to the engine is proposed with its own specification, tests and
  validation; no threshold or gate changes to remove these cases.

## Scripts

[scripts/x2_intervals.py](scripts/x2_intervals.py) (the intervals' reconstruction),
[scripts/x2_lot_digests.py](scripts/x2_lot_digests.py), [scripts/x2_view.py](scripts/x2_view.py) and
[scripts/x2_view2.py](scripts/x2_view2.py) (the tables above, read from the outputs), with the
package's scripts.
