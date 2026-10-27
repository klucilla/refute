# The acceptance record of the C/D viability package's code

The declaration: [../reopen/stage-1/viability-cd/README.md](../reopen/stage-1/viability-cd/README.md)
(amended at 2ba9e4a; authorization 1 of 2026-10-27, implementation only). This record is committed
**before** its tests, which are committed **before** the code (`viability_cd.py`, the cases, their
generation, records and runner; `viability_cd_evaluate.py`, the readings, the rule and section 9's
step). The code reuses `population_v2` (frozen), `population_v3`, `population_v4`, `rmin_study` and
`x2_study` without editing them, and never edits the engine. **No case of the lot is generated in
step 1:** the tests use their own seed root and synthetic geometries; the geometry list (section 1
of the declaration) is computed from gate 3b's saved metadata, which holds no flux.

## 1. The geometries (G)

- **G1, the source.** `.cache/real-controls/mast-rows.json`, read once; its SHA-256 must be
  `57fb8a014e8aacc5c0de5fc30dcbf46f6bd8315b30c5642281381fdfd46567c2`, else the list is refused. Each
  entry (a TIC) has `light_curves` and `pixel_files` rows (`sequence_number`, `t_min`, `t_max`, MJD).
- **G2, the consolidation.** Per TIC and sector: the earliest `t_min` and the latest `t_max` of its
  light-curve rows (`viability-3b/scripts/viability.py`, `sectors_of`); a `t_max` that is not finite
  or below its `t_min` is an error; the target pixel files' sector set.
- **G3, the years.** The UTC calendar year of each sector's consolidated `t_min` (MJD 0 is
  1858-11-17 00:00 UTC).
- **G4, eligibility.** A TIC is **C** when it has exactly three distinct years, **D** when four or
  more; and in both, every light-curve sector has a target pixel file, and every sector's span
  `t_max − t_min` lies in **[25.5, 30.0] d** (closed). Otherwise it is ineligible, with **every**
  failing reason, in this order: `years: <n>` (fewer than three), `no target pixel file: <sectors>`,
  `span outside 25.5 to 30.0 d: <sector> <span>` (each).
- **G5, unique geometries.** Per alternative, keyed by the sorted tuple of sector numbers; the
  **lowest eligible TIC** of a key supplies its dates; the key's other eligible TICs are listed.
- **G6, the selection.** Per alternative, the unique geometries sorted by key, then permuted by
  `numpy.random.default_rng(seed).permutation(n)` with `seed` the first 8 bytes (big-endian) of
  `SHA-256("refute/v0.2.1/viability-cd/geometries/<C or D>")`; the first **24** (C) and **12** (D),
  or all if fewer; no eligible geometry: an empty selection, recorded.
- **G7, the dates.** BTJD = MJD − 56999.5, for the layout; each sector keeps its real number.
- **G8, the list.** `geometry_list` returns, and the command `geometries <out>` writes once (never
  replaced): the source's SHA-256 and retrieval times, the rule's constants, every TIC's eligibility
  or reasons, the unique geometries per alternative with their representative TIC, sectors, years,
  BTJD dates and spans, the selected lists in order, and, per selected sector, the **analytic
  per-attempt acceptance** of the orbit draw (L2) and the expected number of exhausted draws over
  the lot (a disclosed risk of OPERATIONAL CLOSURE; nothing is drawn with the lot's seeds).

## 2. The cases (K)

- **K1, the sizes.** C: per noise model (`white`, `correlated`) the regimes `three_years` (180) and
  `variability_some_years` (180); D: per noise model `three_years` (120). 720 and 240 cases.
- **K2, a case.** `class` `planet`, `band` `measurable`, `noise`, `mechanism` the regime, `index`
  `i`, `catalog_variant` `own`, `id` `<a>-<noise>-<regime>-<iiii>`, and `extra`: the alternative and
  the geometry's position.
- **K3, the seeds.** The first 8 bytes (big-endian) of
  `SHA-256("<root>/<a>/<n>/<r>/<i>")`, `<root>` `refute/v0.2.1/viability-cd` for the lot (the tests
  use `refute/v0.2.1/viability-cd-test`), `<n>` `white` or `AR(1)`, `<i>` in decimal; all distinct.
- **K4, the assignment.** Case `i` of an alternative, noise model and regime takes the selected
  geometry `i mod G`.
- **K5, the task order.** For `i` from 0: for each (noise model, regime) in the order white then
  correlated, `three_years` then `variability_some_years`, case `i` if it exists.
- **K6, the target name.** `<prefix>/<id>`, the prefix `refute-v0.2.1-viability-cd-1` for the lot.

## 3. The layouts (L)

- **L1, the stream.** Attempt `a` of a case draws from `default_rng(sub_seed(seed, "layout", a))`.
- **L2, a sector** of real span `S` from `t_min'` (BTJD), in time order, draws in this order: the
  orbit gap `g` U(0.5, 2.0) and `δ` U(−0.5, 0.5), the first orbit `(S − g)/2 + δ`, the second
  `S − g` minus the first; both in [12.5, 14.0] or `g` and `δ` drawn again, up to `MAX_ATTEMPTS`
  (1000; exhausted: `RuntimeError`, a defect, never a silent replacement); then the number of loss
  blocks (0 to 4), each block's length U(600, 21600) s and place U(0, 1), the loss rate U(0, 0.05),
  the per-cadence uniforms and jitters; the time stamps by `population_v4._sector` from `t_min'`.
- **L3, the checks.** `refute.packs.tess.domain.check_domain` on the time stamps: **D3 and D4**
  must hold for both alternatives; **D1** for C; **four or more distinct labels** (every label
  defined) for D. A failure redraws the whole layout at `a + 1`, the reason counted as
  `layout:D3`, `layout:D4`, `layout:D1` or `layout:labels`; `MAX_ATTEMPTS` attempts, else
  `RuntimeError`.
- **L4, the labels.** Each sector's label is the domain's (the year of its first kept time stamp).

## 4. The generation (P)

- **P1, the parameters** as `population_v4.build_case` does for a planet: attempts
  `seed_k = seed` then `sub_seed(seed, "redraw", k)`; `draw_parameters` with the first time stamp;
  the variability-free year mapped (P2); `_mechanism_condition`; `_place_in_band` with the SNR gate
  and the hidden minimum of the default parameters; a refused draw counted by its reason.
- **P2, the variability-free year.** `var_absent_year` drawn from (2018, 2019, 2020) names the
  curve's **sorted distinct label** at its position (C has three), recorded with
  `var_absent_position`.
- **P3, the curve.** `var_amplitude = var_amplitude_factor × depth`; per sector in time order the
  model `signal × trend + variability` (the variability absent in the variability-free year) plus
  `population_v2._noise` from `default_rng(sub_seed(seed_k, "noise"))`; `flux_err` 600 ppm; the
  sectors' `SectorInfo` with their real numbers, labels and first and last time stamps.
- **P4, the twin.** `rmin_study.noiseless_model(case, p, time, year, 1.0)`; `flux − twin` is the
  noise, exactly.
- **P5, determinism.** The curve's SHA-256 (over its arrays and sector information) is the same in
  any process and with any worker count.

## 5. The record (R)

- **R1, the rounds.** One per observing year, by `calibration_measurement` on the R_min study's
  configuration (its identity checked, `rmin_study.study_configuration_problems`), with the twin;
  the evaluator's truth (`rmin_study.EvaluatorTruth`, `s` = 1) made before the calls, read after.
- **R2, after the calls only:** the identity flag (R3) and the oracle (R4), computed by the
  evaluator from the truth and the curve.
- **R3, the identity flag** of a round: when its `train_ephemeris` exists, `identifiable` true and
  `flag` = `|P_train / P_injected − 1| > 0.01`; otherwise `identifiable` false, `flag` null.
- **R4, the oracle** of a year (the declaration, section 5, R3): the injected centres inside the
  year's hidden sectors (closed spans); per centre the in-transit cadences `|t − t_k| ≤ T14/2` and
  the baseline `T14 ≤ |t − t_k| ≤ 3 T14`, both without the cadences within `T14` of another
  injected centre; kept with at least 5 in-transit and 10 baseline cadences on each side; a line by
  ordinary least squares on the baseline; `D` the mean of the kept deficits, `σ² = Σ r² / (N_B − 2K)`,
  `E = σ / √N_in`; detectable when `E > 0`, `D` and `E` finite and `D/E ≥ min_snr`, otherwise with
  its reason (`no kept transit`, `non-finite or zero error`, `below min_snr`).
- **R5, the record's fields:** its format, target, case id, alternative, noise, regime, index,
  geometry (position, key, representative TIC), seed, attempt seed, layout (attempt, redraws, the
  orbit draws per sector), parameter redraws, years, sectors (number, year, first and last time
  stamp, cadences), the curve's SHA-256, the configuration, the rounds (every calibration field),
  the identity flags and the oracle per year, the truth. No wall time (the bytes must not depend on
  the run).
- **R6, the record check** (`record_problems`) refuses a record that is not the task's: format,
  target, case and seed, configuration, the sectors equal to the geometry's numbers and the layout's
  labels, one round per year with every field, one identity entry and one oracle entry per year,
  the truth's keys.

## 6. The runner (X)

- **X1, the manifest** first, published atomically, never replaced; it binds the sub-lot, the tasks
  and their seeds, the geometry list's SHA-256, the configuration, the resolved plan's SHA-256, the
  code's digest (the engine, the lock files and the modules used) and the numeric environment; a
  relaunch with any of them changed is refused.
- **X2, records** written atomically (`x2_study.write_record_atomic`), never replaced; an existing
  incomplete record stops the run.
- **X3, markers and decisions** as `x2_study` (`attempts/`, `failed/`, `not-submitted/`,
  `retry-decisions/`; the task key `(case id, 0)`): a failed or interrupted task is not submitted
  again without a recorded decision.
- **X4, the ceiling:** the sub-lot's submission hours (C 1.70, D 1.40), counted across invocations
  (`consumption/`), read right before each submission; at the ceiling no submission, the tasks in
  flight end.
- **X5, the cost check:** once the first `ceil(N / 10)` tasks in task order all have a record and a
  timing (`timings/`, outside the records), the mean task seconds `m` gives the projections
  `m × N / 3600` LP-h and `m × N / workers / 3600` h; if either exceeds the sub-lot's ceiling (C
  37.0 LP-h or 1.70 h, D 30.8 LP-h or 1.40 h), the run stops submitting, `cost-check.json` records
  it, and the sub-lot's outcome is OPERATIONAL CLOSURE; the check runs once per sub-lot.
- **X6, the platform:** 22 workers, spawned, on logical processors 8 to 31 (affinity
  `0xffffff00`), one thread per numeric library.
- **X7, resumption:** an interrupted sub-lot relaunched gives the same record bytes as a continuous
  run.
- **X8, the lot check** (`lot_problems`): every task has one record at its own path, complete (R6),
  no record outside the tasks; with `full`, the tasks are exactly the declared sub-lot's.

## 7. The readings and the rule (E)

- **E1, the derivation:** `derive_round(record, 8, 0.585, 2.883, min_snr)` per round; per target
  `spec_b_outcome` over all its years (a completeness error is an integrity error) and the legacy
  aggregation (`rmin_study.aggregate`).
- **E2, the rows:** every derived (status, reason) maps to exactly one row of the declaration's
  section 4 (rows 6 and 7 by their message's form); an unmapped one raises. The reason-producing
  functions of `holdout.py` (`plan_round`, `train_validity`, `_round_corrected`, `replica_stats`,
  `measure_windows`, `measure_with_replicas`, `calibration_measurement`, `derive_round`,
  `fail_rule`) are pinned by the SHA-256 of their source: a change fails a test, so the table is
  reviewed again before any reading.
- **E3, R2:** the three sets of rows (K: 6, 10, 11; KT: 6, 7, 10, 11; KTN: 6, 7, 10 to 13), each
  undecided round of a set's row counted PASS, then specification B.
- **E4, R3:** per target, oracle-PASS when every year is detectable; counts per noise model.
- **E5, the bounds:** one-sided 95% Clopper-Pearson (`population_v2.cp_lower`, `cp_upper`); the
  missing planets assigned the worst way for each condition, and both ways in the report.
- **E6, the outcome** per alternative, in this order: OPERATIONAL CLOSURE (more than 5% of a noise
  model's planets without a record, an integrity error, the cost check or a generation defect),
  PASS, FAIL, INDETERMINATE, exactly as the declaration's section 6. *Harmonized by amendment B
  with E10:* the submission ceiling reached before completion is not by itself a cause; the
  records it leaves missing follow the completeness rule (the declaration's section 7). The text
  first written here ("the ceiling before completion" a cause) is kept below for the record.
  - *As first written (958638c):* "OPERATIONAL CLOSURE (more than 5% of a noise model's planets
    without a record, an integrity error, the cost check or the ceiling before completion)".
- **E7, C against D:** on the planets without variability, the difference of the spec-B PASS
  fractions (R1 and R2-KTN) per noise model with Newcombe's hybrid score (Wilson) 95% interval;
  the rounds' PASS fraction by the number of years.
- **E8, the step (section 9):** the seven candidate models' `e_pred` from the record's fields (C2;
  `nan` unless every grid value is finite and non-negative and `n_pred` positive); a pair's
  derivation `derive_round`'s order with only `s_pred,1` and `s_pred,2` changed; **`E1.0` with
  `E2.0` equals `derive_round` on every round**; the twelve pairs' counts and bounds, the envelope's
  (descriptive), the applicability and the closing criterion exactly as section 9.
- **E9, the destination** of each of the sixteen combinations of C's and D's outcomes, as section
  9's table.

## 8. The tests (`tests/test_viability_cd.py`; synthetic, offline)

| Test | Criteria |
| --- | --- |
| the source's SHA-256 is checked | G1 |
| consolidation, years and every reason of ineligibility, on synthetic rows | G2 to G4 |
| unique keys, the lowest TIC's dates, the seeded selection and its sizes | G5, G6 |
| BTJD dates and the analytic acceptance (against a Monte Carlo) | G7, G8 |
| the case sizes, ids, seeds (the text), assignment and the interleaved order | K1 to K6 |
| a layout: its draw order (rebuilt by hand), the orbits in range, D3/D4/D1/labels, the redraw reasons, exhaustion raises | L1 to L4 |
| a built curve: the mapped variability-free year, flux − twin = noise, the sectors' numbers and labels, its determinism across processes | P1 to P5 |
| a record from the real engine on a synthetic geometry (small): fields, flags, oracle, the truth guard | R1 to R6 |
| the oracle on a constructed curve (a known depth and noise), skipped transits | R4 |
| the runner: manifest binding, atomic records, markers, ceiling, cost check, resumption byte for byte, the lot check | X1 to X8 |
| every row's mapping, an unmapped reason raises, the pinned sources | E2 |
| R1, R2 and R3 on constructed records | E1, E3, E4 |
| the bounds, the hurdle counts (289/26 of 360, 100/6 of 120), the worst assignment, every outcome | E5, E6 |
| Newcombe's interval against a known value | E7 |
| the candidate models, `E1.0`+`E2.0` equal to `derive_round` on real and constructed records, a released round's measured FAIL, the envelope's bounds, applicability and closing | E8 |
| the sixteen destinations | E9 |

## 9. The sabotages (`viability_cd_sabotage.py`)

Each mutates the staged code once (a literal replacement), runs the matching tests through
`scripts/run_tests_affinity.ps1` with a JUnit file, and restores the file from the index (its
SHA-256 checked); caught when at least one matching test fails and the unmutated run passes. Never
run at the same time as a full suite.

| # | Mutation | Caught by |
| --- | --- | --- |
| S1 | the span's lower bound 25.0 | G4 |
| S2 | the highest TIC supplies a key's dates | G5 |
| S3 | the selection not shuffled | G6 |
| S4 | the seed text without the regime | K3 |
| S5 | the assignment `i mod (G − 1)` | K4 |
| S6 | `δ` drawn U(−1, 1) | L2 |
| S7 | D4 not required | L3 |
| S8 | the variability-free year mapped to the label at the sector's position | P2 |
| S9 | the oracle's baseline from `0.5 T14` | R4 |
| S10 | the identity tolerance 10% | R3 |
| S11 | a record replaced | X2 |
| S12 | the cost check's projection without the factor `N` | X5 |
| S13 | row 13 mapped to row 12 | E2 |
| S14 | R2-K releasing row 12 | E3 |
| S15 | the PASS rule on the point estimate | E6 |
| S16 | `E2.dp0` from the grid's maximum | E8 |
| S17 | the destination of C FAIL with D FAIL not ending the investment | E9 |

## Amendment A (after Codex's review of the round, 2026-10-27; the code at b5f3b34)

Codex's review found that the code did not yet meet the declaration on these paths; the criteria
below are added (or made exact) and the code, the tests and the sabotages follow them. No decided
rule of the declaration changes.

- **G8, wording.** The orbit draw's acceptance is a numerical integral (the trapezoid rule over
  `g`), not a closed form; the expected exhausted draws count one pass per sector and case (the
  layout redraws are not counted, so the figure is a lower bound).
- **X9, a generation defect stops the lot.** An orbit draw, a layout or a parameter draw that
  exhausts `MAX_ATTEMPTS` raises `GenerationDefectError`; the runner records `defect.json` (once),
  submits nothing more in this or any later invocation, and the sub-lot's outcome is OPERATIONAL
  CLOSURE.
- **X10, one stamp per invocation.** An invocation's stamp (its consumption record and markers) is
  never an earlier invocation's.
- **X11, the determinism check** of the declaration's section 7: `determinism <out> --lot <name>
  --n <k>`, the first `k` tasks' curves built in this process, on one worker and on 22, every digest
  equal. It builds curves of the lot: authorization 2 only.
- **R6, exact.** The record's geometry (position, key and representative TIC) is the case's; its
  attempt seed, curve digest (64 hexadecimal characters), redraws and layout (one entry per
  geometry sector) are present; each sector is the geometry's, in time order, starts within 1 s of
  its real `t_min` (the jitter is at most 0.25 s), ends before its real `t_max` (within 1 s), is
  labelled by the year of its first time stamp and has cadences; C has three labels, D four or
  more; the years are the sectors' labels.
- **X8, never an exception.** A damaged manifest or record file is a problem of the lot check,
  never an exception before the outcome.
- **E10, the evaluator's causes and notes.** OPERATIONAL CLOSURE causes: an unreadable manifest or
  one that is not the sub-lot's (lot, alternative, prefix, seed root, ceilings, task list, the
  geometry list's SHA-256, configuration, plan, code, environment); a record that does not parse,
  is not at its path or fails R6; a round that cannot be derived; the cost check's stop; a
  generation defect. **The submission ceiling, an interrupted invocation and failed tasks are
  notes:** they leave records missing, and the completeness rule decides (the declaration, section
  7: at the ceiling "what ran is evaluated as section 6 says"; section 6: more than 5% missing in a
  noise model is OPERATIONAL CLOSURE, otherwise the worst assignment).
- **E11, the step after the joint destination.** Both alternatives' outcomes first; then section 9's
  table; then the step, once, only over the alternatives the table names and only where it
  applies; its ceiling (1 LP-h, this process's CPU time, checked after each pair) exceeded is an
  OPERATIONAL CLOSURE of the step; then the final reading (the proposals, the specification C
  validation proposal if the step succeeded, the alternatives ended, and whether the effort ends as
  not approved). An alternative with no selected geometry is INDETERMINATE ("no geometry").
- **E5, the report's bounds.** Each R2 set's PASS and FAIL bounds both ways, whether it reaches
  `L ≥ 275/360`, R3's bounds; the step's PASS and FAIL bounds both ways.
- **Sabotages S18 to S22:** the defect not stopping the dispatch (X9); the record's TIC not checked
  (R6); the cost check's stop ignored by the evaluator (E10); the step's ceiling not checked (E11);
  the step run over both alternatives whatever the destination (E11).

## Amendment B (after Codex's second review of the round, 2026-10-27; the code at 1f690f9)

- **X8 and R6, typed.** A record whose fields have the wrong types (a sector number or label that
  is not an integer, a date that is not a number, a round that is not a mapping) is a problem of
  the record check, never an exception: the sectors' fields are type-checked before any
  conversion, and any structural failure of a check is reported as a malformed record.
- **E11, the step's ceiling exact.** Both of the declaration's limits, **1 LP-h** (this process's
  CPU time) and **0.5 h** of wall time, shared by the step's alternatives, checked after each pair
  **and after the envelope**; either exceeded is an OPERATIONAL CLOSURE of the step.
- **E6 harmonized with E10** (above). **For the maintainer's confirmation in the request for
  authorization 2:** the declaration's sections 6 and 7 can be read either way for a sub-lot that
  reaches its submission ceiling with at most 5% of a noise model's planets missing (section 6
  lists the ceiling among operational failures, "when the work ends because of them" OPERATIONAL
  CLOSURE; section 7 says that at the ceiling "what ran is evaluated as section 6 says"). The code
  follows the completeness rule (evaluated under the worst assignment); the other reading would
  make it OPERATIONAL CLOSURE. Codex agreed the arithmetic is not in dispute and left the reading
  to the maintainer.
- **Sabotages S23 and S24:** the envelope not counted against the ceiling; the malformed-record
  guard narrowed.

## 10. Order

This record (its own commit), then the tests (their own commit), then the code (its own commit),
then the sabotages and their results, Codex's review, and the geometry list (its own commit). The
run waits for authorization 2.
