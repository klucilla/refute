# Diagnosis of the R_min study (option B): what will be measured, declared before the analysis

The maintainer's decision of 2026-10-21 ("DIAGNÓSTICO (opção B)"): a diagnosis of the R_min
study's result **from the fields already recorded only**, with no new light curve and no run of
the engine. This file fixes, before any of it is computed, the questions, the cuts, the
denominators, the conventions and the outputs. It is committed and pushed before the analysis,
after a read-only Codex review (revision 3: the eight points of its first round and the one of
its second applied; its third position, ACORDO, is recorded in
[codex-review.md](codex-review.md)).

The study's result stands as recorded ([../study/README.md](../study/README.md)): no `R_min` was
validated; the lot is development evidence. This diagnosis changes no result, threshold,
criterion or code, proposes nothing from a number chosen to pass, and never reduces a dispersion
to lower a gate. The synthetic labels below serve the diagnosis only; they are never given to
the engine.

## 1. Scope of what runs, and of what is exploratory

- **Only what is declared here is computed.** An incidental observation made while doing it is
  written in `exploratory.md`, marked exploratory. It cannot change a declared cut, denominator,
  output or conclusion. An undeclared calculation is not run: it is written in `exploratory.md` as
  an unexecuted proposal, pending a separate declaration.
- **No inferential claim.** The bounds and bootstrap points below are descriptions. There is no
  simultaneous guarantee across the many cuts (Amendment 19 already says its 0.99 bounds do not
  make all intervals jointly 95%); no subgroup is selected by significance; no binomial interval
  treats rounds as independent (intervals are over targets only); nothing here validates anything.

## 2. The data and the code

- **The study lot:** the 76 800 records of `refute-v0.2.1-rmin-study`, read from
  `.cache/wt-v021/.cache/v021/rmin-study-run/records/` and checked first against
  [../study/record-digests.json](../study/record-digests.json) (every file's SHA-256; any
  difference stops the analysis).
- **The bs-choice lot:** the 100 records of [../bs-choice/](../bs-choice/), checked first:
  `evaluate_bs_choice` on them must give `../bs-choice-evaluation.json` again.
- **The target's identity** is the record's `target` field, `<prefix>/<case id>`, with its
  scenario apart. A target in a table is one (target, scenario) record.
- **Design labels derived from the target's id only**, by the committed rules of
  `docs/validation/v0.2.1/population/population_v2.py`, with no random draw and no light curve:
  the band (`near`, `measurable`), the noise (`white`, `correlated`), the index, the mechanism
  `_planet_mechanism(index)` (`two_years`, `few_train`, `three_years`, `variability_some_years`)
  and, for `few_train`, `_few_train_extra(index − 150, 50)` (as `population_cases` calls it):
  its design train transits (3 or 4) and distance (1 to 3 years). These are the generator's design
  labels, not recovered quantities. The group is `rmin_study.group_of`.
- **Fields of the engine as recorded:** per round the stage, the reason, decisions 1 and 2, the
  train and hidden replica counts per dP, `hidden_noise_undetermined`, `s_pred_1`, `s_pred_2`,
  `s_meas`, `d_train`, `e_train`, `d_hidden`, `e_hidden`, `d_twin`, `twin_status`,
  `measurement_status`, `n_years`, `dp`; per record the observing years.
- **The derivation at each R:** `rmin_evaluate.target_outcomes` / `holdout.derive_round` at
  `R ∈ {8, 10, 12, 15, 20}` with the committed pair of bs-choice for that R (`k` = 2);
  `min_snr` = 5; the capacity threshold `min_snr − b + Φ⁻¹(1 − 0.005/n_years)·s`
  (`holdout.capacity_threshold`).
- **The code:** the code of the study, `claude/v0-2-1-reopen` at `2e4ff99`, through
  `../study/scripts/run-with-study-code.ps1` (its venv, no bytecode written in `.cache/wt-v021`).
  The outputs go to `.cache/merge-v021/rmin/diagnosis/` and then to this folder; the analysis
  scripts are committed here with the outputs and their SHA-256 as run.

## 3. Conventions fixed before the analysis

- **Reason kinds:** the raw reason is kept; its kind is `kind()` of
  `../study/scripts/summarize.py` (the leading run of letters, `_`, `-` and spaces, stripped).
  A kind not listed in a table is shown under its own name, never merged into "other".
- **Gates (Q1):** each round's first stop in `derive_round`'s order, with the subcauses of G3 in
  this precedence: `stage == "hidden_noise"`; else `hidden_noise_undetermined` true; else hidden
  replicas below R; with a cross-table of the flag and the replica condition for every G3 round.
- **Two target conventions, both reported, never mixed:** (T-a) the aggregated INCONCLUSIVE
  targets, each counted once under the `+`-joined sorted combination of its INCONCLUSIVE rounds'
  reason kinds (the evaluator's `_inconclusive`); (T-b) the targets with at least one round
  stopped at a given gate, whatever their aggregated status.
- **Denominators:** every fraction states its numerator and denominator. For a gate: the rounds
  of the cell (population) and the rounds that reach the gate (reach).
- **Undefined values** are a category of their own, counted beside every quantile: missing,
  non-finite, zero or negative where a ratio needs a positive value. Nothing is dropped silently.
- **Statistics:** quantiles by `numpy.quantile` (default, linear); standard deviation with
  `ddof = 1`; `MAD` the median absolute deviation, `s = 1.4826 MAD`; "beyond 3 s" means
  `|residual − b| > 3 s`.

## 4. The questions, cuts and outputs

Unless said otherwise every table is per **R** (the five values), **group** (4) and **scenario**
(constant, disappearing, weakened). "Last round" is the round hiding the largest year of the
target's metadata.

**Q1. The passage through each gate** (`gates.json`). The gates: (G0) before the capacity rule,
by recorded reason kind: the timing rule (`train-only timing uncertainty in the hidden year`),
`train_snr_below_gate`, `train_noise_undetermined`, `duration_period_ratio_above_max`,
`no_predicted_window`, and every other kind by name; (G1) train replicas below R; (G2) decision 1,
`insufficient_capacity_train`; (G3) the hidden noise, with its subcauses; (G4) decision 2,
`insufficient_capacity_hidden_noise`; (G5) the measurement's impediment (`measurement_status`
not `ok`, by its value); (G6) the FAIL rule: PASS, FAIL, INCONCLUSIVE
`not_detected_not_inconsistent`, INCONCLUSIVE `non_finite_statistic`. Outputs per gate: rounds
reaching it, rounds it stops (population and reach denominators); targets (T-b) with a round
stopped there; per target, the furthest gate reached by any round and the gate of the last
round.

**Q2. The interruptions by cut** (`interruptions.json`). The INCONCLUSIVE rounds by gate and
reason kind, and the INCONCLUSIVE targets (T-a), cut by: group × scenario × band × mechanism ×
number of observing years × R; for `few_train` also by design train transits and distance; by
the measured train SNR `d_train/e_train` in the bins (0, 5], (5, 10], (10, 20], (20, 40], (40, ∞)
for the rounds that recorded both values (others: "not recorded", by gate). For the rounds
stopped by the timing rule, by the **rounded textual** ratio `σ_T/T14`, both parsed from the
reason (`... in the hidden year (<σ_T> h) exceeds 1 transit duration(s) (<T14> h)`, two
decimals): bins "≤ 1 (rounding)", (1, 1.5], (1.5, 2], (2, 3], (3, 5], (5, 10], (10, ∞),
"T14 printed 0", "unparsed"; every such round stays in the timing total. The measured train-SNR
and rounded timing-ratio cuts apply to rounds only; the T-a target tables use only the
target-level design labels (group, band, mechanism, few_train design) and the number of observing
years. The injected geometry (depth, duration, period, impact) is not recorded and is not cut
(Q7).

**Q3. What puts S_pred below the threshold** (`capacity.json`), per round only (with, per
target, the count of its rounds stopped at G2 and at G4). For the rounds stopped at G2 (`s_pred_1`)
and at G4 (`s_pred_2`), at each R, three exhaustive categories: `S_pred` undefined (missing or
non-finite); `S_pred < min_snr`; `min_snr ≤ S_pred < threshold` (stopped only by the threshold's
margin `−b + z·s`). The threshold's parts (`min_snr`, `−b`, `z(n_years)·s`) per R and number of
years. The quantiles (5, 25, 50, 75, 95%) of `S_pred` per group × band × mechanism, with valid
and undefined counts. Two algebraic factors, valid only when `d_train` and `e_train` are finite,
`e_train > 0` and `S_pred` is finite and positive: `d_c/d_train` (`d_c = d_train − e_train`,
`CAPACITY_K` = 1) and `e_pred/e_train` (`e_pred = d_c/S_pred`); their quantiles per group × band ×
mechanism with valid and invalid counts. These are an algebraic description of the recorded
quantities, not independent causal contributions; the split of `e_pred` into replica variance,
`m_β` and the number of predicted transits is not possible (Q7).

**Q4. Whether the recovered candidate is the injected transit.** The records keep no recovered
period, epoch or duration (except the rounded `T14` of timing-stopped rounds) and no injected
one; the twin measures the noiseless injected model at the windows predicted from the train's
ephemeris, which tests the depth at those windows, not the candidate's identity. **Not
answerable** from the records; listed in Q7. The twin's pulls are the coverage criterion already
and are not reinterpreted.

**Q5. b and s** (`bs.json`, `bs-residuals.json`), on the bs-choice records only (constant
scenario), `k` = 2, and for each R the rounds of `pair_for_r` (`_k_set` meeting R; R = 8: 79 rounds
of 40 targets; R = 20: 48 rounds of 24 targets). The residual is `S_meas − S_pred,2`.
- **Per target** (`bs-residuals.json`): every residual keyed by target, hidden year, R and regime,
  with the difference of the two rounds (later year minus earlier) where a target has two; and,
  per R, the sorted residuals (the empirical distribution), pooled and per regime.
- **Per R:** the targets with one and with two rounds; median, `s`, standard deviation, IQR, the
  5/25/50/75/95% quantiles, the count beyond 3 s; the variance split within and between targets
  by the one-way ANOVA estimator for unequal cluster sizes (`n0` adjustment), the intraclass
  correlation reported as computed, a negative value shown as is and noted; the Pearson and
  Spearman correlations of the two rounds' residuals (earlier year against later) over the
  targets with two.
- **Per regime** (group; band; mechanism; number of years): count, median and `s`; an empty
  regime is listed with count 0.
- **Cluster bootstrap**, 2000 resamples, `numpy.random.default_rng(20261021)`, two variants
  reported apart: (B1) the targets of the R's selected set drawn with replacement (as many as
  the set has), each with all its selected rounds; (B2) the 100 bs-choice targets drawn with
  replacement, then the fixed selection (`_k_set` at k = 2 and R) applied. Duplicated clusters
  are kept, each round counted; `b* = median`, `s* = 1.4826 MAD` of the resample's residuals;
  for each draw the **paired** threshold at two years, `5 − b* + Φ⁻¹(1 − 0.0025)·s*`; the 2.5 and
  97.5% points of `b*`, `s*` and the threshold.

This is descriptive: it measures how stable and how dependent `b` and `s` are, and how mixed the
residuals are; it proposes no other estimator and lowers no gate.

**Q6. The weakening scenario: its intended definition** (`weakening.md`, text only). Quoted from
the committed documents (map Amendment 19 and its readings; `rmin_study.SCENARIOS` and
`alter_last_year`; criterion 5 in `rmin_evaluate`): how the weakened scenario is built (the last
year's signal times 0.3) and what its criterion expected; and from `holdout.fail_rule` the order
of the rule: PASS when `S_meas ≥ min_snr`, before the depth inconsistency `Z > 3` is tested. The
question for the maintainer: whether a weakened signal that is still detected should count as
present (PASS correct) or as no longer at its predicted depth (FAIL expected). **No substitute
number** (no other filter, threshold or rate) is computed for weakening before that definition.

**Q7. What the records do not answer** (`not-answerable.md`): at least the injected geometry
(depth, duration, period, impact, ingress), the recovered candidate's identity (Q4), the
components of `e_pred` (replica variances, `N_pred`), the train SNR of the rounds stopped before
`d_train` was recorded, `σ_T` beyond the rounded text, and anything that needs a light curve or a
run of the engine; each item with what would be needed.

**Q8. Safety and utility, measured apart** (`safety-utility.json`), per R × group × scenario,
with explicit denominators: total targets; study-eligible targets (`target_outcomes`
eligibility); decided targets (aggregated PASS or FAIL); and errors. Errors: constant, FAIL;
disappearing, PASS (false PASS). Reported: error/eligible, error/decided, error/total and
decided/total; the disappearing FAIL fraction (correct) on the same denominators; and the
evaluation's own qualified sets kept identifiable (disappearance: last round passing both
decisions). For the weakened scenario only the PASS and FAIL fractions, **without an error label**
and not as a substitute criterion (Q6). error/total is the error frequency under abstention, not
evidence of safety for the undecided targets. One-sided Clopper-Pearson bounds over targets at
`1 − 0.05/5`, as descriptions only.

## 5. The delivery

For each problem found: the evidence (which output and number), whether the cause is confirmed
or a hypothesis, the correction proposed and the test able to refute it. Then **one** proposal
of next step (a corrected study or an explicit reduction of scope) with: the mathematical check
of compatibility between filters and gates, after the b/s calibration and before any large lot;
the coherence and boundary tests before any code change; positive and negative controls for any
correction of the engine; a separate pilot to estimate the yield per group and scenario; the
sizes, criteria, choice rule and budget fixed before; new seeds; an independent reserve. And the
list of what this result blocks or changes (T4, Amendment 28, the exit criteria of v0.2.1). With
Codex's opinion. Then the work stops for the maintainer.
