# Diagnosis of the R_min study (option B): results, problems and one proposal

Declared in [DECLARATION.md](DECLARATION.md) (revision 3, committed and pushed in `254f447` before
any computation; Codex ACORDO, [codex-review.md](codex-review.md)). From the recorded fields only:
no light curve was built and the engine was not run. Code: the study's, `claude/v0-2-1-reopen` at
`2e4ff99`. The records matched their committed digests, bs-choice gave its committed evaluation
again, and the residuals gave the committed `(b, s)` pairs again (checked by
[scripts/diagnosis.py](scripts/diagnosis.py) before any table). The R_min result is unchanged:
**no R_min was validated**; the lot is development evidence. The numbers below are descriptions
(declaration, section 1): no simultaneous guarantee, nothing validated.

**A departure from the declaration, found and corrected.** The first run pooled the three
scenarios in Q3 (its distributions were keyed by group, band and mechanism), while the
declaration's default is R × group × scenario. Codex's opinion on the delivery found it. The
script was corrected to key Q3 by scenario too, as declared, and run again; the declaration was
not changed. The five other outputs of the second run are byte-identical to the first's; the
first run's `capacity.json` (SHA-256 `cad84bd9…9610`) is kept on the side, not used here.

Outputs: [gates.json](gates.json) (Q1), [interruptions.json](interruptions.json) (Q2),
[capacity.json](capacity.json) (Q3), [bs.json](bs.json) and [bs-residuals.json](bs-residuals.json)
(Q5), [weakening.md](weakening.md) (Q6), [not-answerable.md](not-answerable.md) (Q4, Q7),
[safety-utility.json](safety-utility.json) (Q8), [exploratory.md](exploratory.md) (apart).

## What the declared outputs show

**Q1, the gates** (share of all rounds stopped at each gate, R = 8, constant; the gate order of
`derive_round`; no round unclassified, at any R or cell):

| group | G0 before capacity | G1 train replicas | G2 decision 1 | G3 hidden noise | G4 decision 2 | G6 FAIL rule reached |
|---|---|---|---|---|---|---|
| white, no variability | 0.504 | 0.003 | 0.303 | 0.079 | 0.010 | 0.101 |
| white, variability | 0.171 | 0.011 | 0.803 | 0.000 | 0.009 | 0.006 |
| AR(1), no variability | 0.252 | 0.004 | 0.460 | 0.080 | 0.028 | 0.176 |
| AR(1), variability | 0.091 | 0.009 | 0.839 | 0.002 | 0.026 | 0.033 |

G5 (the measurement's impediments) stops no round. In the groups without variability G0 is mostly
the timing rule (white: 6506 of 7264 G0 rounds; AR(1): 3426 of 3623); with variability G0 is
`train_noise_undetermined`, `train_snr_below_gate` and `duration_period_ratio_above_max`. At R = 20,
G1 and G3 grow (for example AR(1), no variability, constant: G1 0.112, G3 0.185; the G3 rounds then
mostly have the noise determined but fewer than 20 hidden replicas).

**Q2, the interruptions by cut** ([interruptions.json](interruptions.json)): every cut of the
declaration. Two readings. The timing-stopped rounds have a rounded `σ_T/T14` spread over all bins
(white, no variability, constant, R = 8: 990 in (1, 1.5], 729 in (1.5, 2], 1156 in (2, 3], 1724 in
(3, 5], 1590 in (5, 10], 313 above 10, 4 at ≤ 1 by rounding). And most INCONCLUSIVE rounds that
recorded a train SNR have `d_train/e_train` above 10: for example AR(1), variability, constant,
R = 8: 15 085 of the 16 823 that recorded it (89.7%); 81.2% of all 18 574 INCONCLUSIVE rounds,
1751 of which did not record it. The rounds stopped at decision 1 are mostly not rounds with a weak
train detection.

**Q3, what puts S_pred below the threshold** ([capacity.json](capacity.json), per scenario). In
the constant scenario at R = 8, of the 42 524 rounds stopped at decision 1, **22 438 (52.8%) have
`S_pred,1 < 5`** (below the minimum SNR itself) and **20 086 (47.2%) have `5 ≤ S_pred,1 <
threshold`** (stopped only by the threshold's margin `−b + z·s` ≈ 7.5 to 7.9); none is undefined
(disappearing: 19 194 and 12 759 of 31 953; weakened: 19 477 and 14 346 of 33 823; their train years
include the altered year in the rounds that hide an earlier year). At R = 20 (threshold 9.9 to 10.3)
the margin still stops 15 699 constant rounds. The threshold's parts at R = 8: `min_snr` 5, `−b`
−0.58, `z·s` 8.09 (two years) and 8.46 (three). The algebraic factors: `d_c/d_train` has medians 0.89
to 0.95 (the one-sigma deduction removes 5 to 11% of the depth); **`e_pred/e_train` has medians
1.49 to 3.18** in the constant scenario (the predicted hidden error is 1.5 to 3.2 times the train's
own depth error; near 3 in the variability groups). The split of `e_pred` into replica variance,
`m_β` and `N_pred` is not recorded (Q7).

**Q5, b and s** ([bs.json](bs.json)). At R = 8: 79 rounds of 40 targets (17 with one round, 7 with
two, 16 with three); `b` = 0.58, `s` = 2.88, but the standard deviation is 4.37 and 4 rounds lie
beyond 3 s. The intraclass correlation is **0.47** (the rounds of one target are far from
independent; the two-round correlations, from the 7 targets with exactly two, are 0.30 Pearson and
0.25 Spearman). The cluster bootstrap puts the paired two-year threshold between **9.3 and 17.2**
(B1; B2 9.3 to 16.7). The regimes differ: two-year curves (19 rounds) have a residual median of 3.58
and `s` 7.71, three-year curves (60 rounds) 0.53 and 2.13; `two_years` 4.17 and 7.10 against
`three_years` 0.53 and 1.93. These are descriptions; no estimator is proposed from them and no gate
is lowered.

**Q6** ([weakening.md](weakening.md)): the design meant "no longer at its predicted depth, to the
point of being undetectable" (criterion 5, "Power, incompatible weakening", filter
`0.3·S_pred,2 ≤ 3`); the engine PASSes at `S_meas ≥ 5` before the depth test; the filter was
compatible with the study's own settings `b = s = 0` (window `5 ≤ S_pred,2 ≤ 10`); with the
calibrated pairs the window is empty at R = 8 to 15 and narrow (`[9.89, 10]`, two-year curves) at
R = 20. The definition is the maintainer's.

**Q8, safety and utility apart** ([safety-utility.json](safety-utility.json)), R = 8:

| group | constant: decided / total | constant: false FAIL / decided | disappearing: decided / total | disappearing: false PASS / decided | weakened: PASS, FAIL (no label) |
|---|---|---|---|---|---|
| white, no variability | 801 / 6400 (12.5%) | 6 / 801 (0.75%; upper 1.81%) | 630 / 6400 (9.8%) | 1 / 630 (0.16%) | 546, 84 |
| white, variability | 81 / 6400 (1.3%) | 0 / 81 (upper 5.53%) | 41 / 6400 (0.6%) | 0 / 41 (upper 10.6%) | 13, 28 |
| AR(1), no variability | 1344 / 6400 (21.0%) | 0 / 1344 (upper 0.34%) | 1172 / 6400 (18.3%) | 1 / 1172 (0.09%) | 989, 184 |
| AR(1), variability | 476 / 6400 (7.4%) | 2 / 476 (0.42%; upper 1.75%) | 241 / 6400 (3.8%) | **26 / 241 (10.8%; upper 16.3%)** | 175, 85 |

Utility is low everywhere (0.6 to 21% of the targets get a decision). Among decided constant targets
the false FAIL stays at or below 0.75%. The disappearing scenario's **target-level false PASS** is
high in `AR(1), variability` (10.8% at R = 8, 9.0% at R = 20); all 210 qualified targets of that
cell FAIL at R = 8, so none of the 26 is in the evaluation's qualified set, which never saw them
(exploratory.md, 1). Over all 6400 targets that is 0.41%: an error frequency under abstention, not a
measure of safety.

## The problems, one by one

| # | Problem | Evidence | Cause | Correction proposed | The test able to refute it |
|---|---|---|---|---|---|
| 1 | The weakening criterion cannot be evaluated | n = 0 in every group and R | **confirmed** (algebra) at R = 8 to 15: the filter `S_pred,2 ≤ 10` was fixed with `b = s = 0` and the calibrated pairs raise the gate above 10; at R = 20 the two-year window `[9.89, 10]` is non-empty, and its zero yield is empirical, not a mathematical impossibility; no compatibility check existed between the calibration and the lot | the maintainer's definition first (Q6); then a filter derived from the defined event, and the mandatory compatibility check below | the compatibility check itself: for the calibrated `(b, s)` and each number of years, the window and the pilot's qualified yield against the size's need; an empty window or a too small yield refutes the design before the lot |
| 2 | The false-FAIL minimum (866) is reached in one group only | eligible constant targets 81 to 1344 of 6400 (1.3 to 21%) | **confirmed**: the sizing assumed a uniform eligible fraction of 0.15 in every group and scenario; the observed fractions depend strongly on the group. The calibrated threshold can only lower admission, but its share of the lost eligibility was not measured apart | size each group from a separate pilot run with the corrected gates, by a sizing rule declared before (below), never from a uniform rate | the main lot's minima: if a minimum is not reached, that is the result (reported, not repaired by extending the lot); the pilot's estimate is planning evidence, and a main-lot yield outside its interval does not by itself refute the sizing |
| 3 | Decision 1 stops most rounds, about half only by the margin | Q3: 20 086 of 42 524 constant G2 rounds in `[5, threshold)` at R = 8; `e_pred/e_train` medians 1.5 to 3.2 | **hypothesis**: the predicted hidden error (the replica variance at the worst `dP`, times `m_β` = 1.2, over `√N_pred`) is inflated against the hidden year's real sampling error, most in the variability groups. `e_pred/e_train > 1` does not establish it; the records cannot separate the factors (Q7) | record `train_var_rep`, `hidden_var_rep` and `N_pred` (no decision changes), with coherence tests | on cases with known noise, white, AR(1) and with variability, `e_pred` against the empirical scatter of the hidden-year depth over repeated noise realizations, with a tolerance declared before: agreement in a regime refutes the inflation hypothesis for that regime |
| 4 | `b` and `s` are estimated on few, dependent rounds from a mixture | 40 targets, ICC 0.47, threshold 9.3 to 17.2 under the bootstrap; two-year residuals median 3.6, `s` 7.7 against 0.5, 2.1 for three years | **hypothesis**: `S_pred,2` mispredicts two-year curves differently, and the pooled `s` mixes the regimes; the ICC and the bootstrap spread describe this sample, they do not establish a population-level cause | a calibration lot of its own, new seeds, sized for the threshold's precision with targets as the unit, the regimes reported apart; the estimator declared before, never chosen to lower the gate | in the calibration lot, a comparison of the residual distributions by number of years with an equivalence margin and a precision declared before: equivalence within the margin refutes the mixture hypothesis; a failure to detect a difference does not |
| 5 | A target-level false PASS of the disappearing scenario is invisible to the criteria | AR(1), variability: 26 of 241 decided at R = 8 (10.8%), 42 of 467 at R = 20; at R = 8 none in the qualified set | **confirmed** (aggregation and criterion): the aggregation gives PASS to a target with no FAIL round and some PASS; when the altered last-year round is stopped before the measurement, the PASS comes from an earlier year; the disappearance criterion counts only targets whose last round passes both decisions. Why it concentrates in this group is not answered (exploratory.md) | a declared target-level false-PASS criterion for the disappearing scenario over all decided targets, beside the power criterion; what a target PASS means when the altered year is undecided is a scope decision with its own specification (no asymmetric mode without validation) | in the corrected study, that criterion's upper bound against its declared limit; a bound above the limit is the result |
| 6 | The weakened scenario mostly PASSes | decided weakened targets: PASS 546 of 630, 989 of 1173 (no-variability groups, R = 8) | **confirmed** code behaviour: `fail_rule` PASSes at `S_meas ≥ 5` before the depth test; whether these are errors awaits the definition | none before the definition of Q6 | not applicable until the definition |
| 7 | Utility is low | 0.6 to 21% of targets decided (R = 8) | **confirmed** counts and stopping places (decision 1 and the timing rule above all); they say where rounds stop, not that the error model is wrong, and they are not a causal split of the abstention | the work of problems 1 to 4, and the timing study of Amendment 28 when it is unblocked | measured in the corrected study, per group, against the coverage requirement the protocol will fix |

## One proposal: a corrected study, in stages, with a scope rule fixed before its main lot

Each stage has an acceptance record committed before its tests and code (ROADMAP, v0.2.1 exit
criterion 1), and its own declaration before it runs.

1. **Before any lot.** The maintainer's definition of the weakened scenario (Q6). The calibration
   record extended to carry `train_var_rep`, `hidden_var_rep`, `N_pred` and the train candidate's
   period, epoch and duration, and the evaluator's side to keep each case's injected parameters
   (never given to the engine), with no decision changed. Its acceptance record fixes first the
   coherence cases (each new field equals what the decision used; `S_pred` recomputed from the
   fields), the boundary cases (an empty grid, `N_pred` = 0, non-finite variances), their expected
   outcomes and tolerances. Any change to a decision of the engine comes only with non-vacuous
   controls fixed before: an eligible constant planet that must PASS with its coverage, an eligible
   disappearance that must FAIL, both in white and correlated noise, and the abstention and refusal
   controls kept apart from them.
2. **The b/s calibration lot**: new seeds, targets as the unit, its size fixed by a declared
   precision of the threshold, the regimes reported apart, the estimator declared before.
3. **The mandatory compatibility check**, right after the calibration and before any large lot:
   for the calibrated `(b, s)`, every filter of every criterion has a non-empty window at each
   number of years, written down with its numbers. If any is empty, the study stops and goes to
   the maintainer.
4. **A separate pilot** with the corrected gates, new seeds, to estimate the yields per group and
   scenario (eligible, decided, qualified). Declared before it: the precision wanted for each yield,
   how the uncertainty is carried across the groups and scenarios, the sizing formula with its
   allowance for that uncertainty (a prediction for the main lot, not the pilot's interval alone),
   the ceilings, and **the scope rule**: which group is sized from the pilot within the budget and
   which is excluded from what is validated, by a rule fixed before the pilot's numbers are read.
   (For planning only: a yield near 1.3% to ±25% at 95% needs about 4700 targets of that group.) An
   excluded group needs a boundary the engine can observe by its own quantities, never a synthetic
   label, and a reduced scope is never presented as the validation of the four-group claim. The
   pilot's cost is measured, not assumed.
5. **The main study lot**: seeds from a future drand round declared before; the sizes from the
   pilot; the criteria fixed before, with the target-level false-PASS criterion of problem 5 and the
   weakening criterion of the defined event; the choice rule (the smallest R meeting all the
   criteria in every group in scope) and the budget fixed before; run once; an unmet minimum is the
   result.
6. **The independent reserve**, only if a configuration is chosen, by the contract of the map
   (Amendment 19, "the reserve"): seeds from a future drand round declared at the choice, the same
   composition and sizes, the pairs frozen, the same criteria and confidence; a failure is the
   result, and no second R is tried after it.

The cost of this run, for planning: 76 800 light curves in 45.24 h on 6 workers (processors 0 to
7). The next lots may use the project's default workers, with the gain measured and the budget
presented to the maintainer before each lot.

## What this result blocks or changes

- **T4 (map Amendment 28): blocked under the approved order.** T4's PASS gate uses the chosen
  `R_min` (the hidden replicas meeting it at every `dP`), and its order puts the code, the timing
  lot and the calibration after the R_min study and its reserve; no `R_min` was chosen. T4's
  admitted rounds bypass the capacity decisions and read no `b` or `s`, so their validity rests on
  T4's own calibration and evaluation, not on this study. Its criterion E4 reuses Amendment 19's
  eligibility, and it reports the weakened PASS as "a detection of the weakened signal, not a false
  PASS", which presupposes the definition of Q6.
- **Amendment 28's sizing: to be redone with fresh evidence.** It used "T0's eligible fraction of
  constant targets 0.15 and of disappearing and weakened targets 0.15 (as Amendment 19)", the
  uniform rate problem 2 shows false. This lot does not measure T4's yields directly (T4's
  population is the two-year layouts and its admission path differs): T4 needs a pilot of its own
  population and path.
- **The exit criteria of v0.2.1:** the population study before and after each change (criterion 2)
  has no validated M4, and it also needs the false-positive and noise-only measurements; the
  confirmation run once on frozen code (criterion 3) cannot start; the new thresholds before the
  protocol (6), the coverage requirement before the lock (7) and the new calibration (8 to 10) stay
  deferred; the AR(1) results here are development evidence and do not discharge criterion 1's
  acceptance controls. A corrected R_min study that succeeds would not by itself close any of
  them; its reserve is not the v0.2.1 confirmation. No negative result resting on the blind holdout
  by year is published until there is a validation; nothing is promoted to `SURVIVED`.

## Codex's opinion

See [codex-opinion.md](codex-opinion.md): OBJECAO in its first round (all points applied), ACORDO
in its second.

## The scripts and the files

The scripts were run from `.cache/merge-v021/rmin/` with `../study/scripts/run-with-study-code.ps1`
(the study's code and venv at `2e4ff99`). Their copies as run, the first run's pooled
`capacity.json` and `MANIFEST.sha256` (SHA-256 `46152488…10d7`) are on the Drive,
`arquivo-v0.2.1-rmin-study/diagnosis-as-run/`, checked from the Drive's copies. The copies here
were formatted by ruff and given lint comments only (`noqa: B023` for the bootstrap's inner
functions, called in the same iteration; a renamed unused loop variable and a wrapped line in
`view.py`); `diagnosis.py` as committed was run once more into a new folder and gave the six
outputs byte for byte. `view.py` read the first run (its Q3 key is the pooled one); `view3.py`
read the second run's Q3.

| Script | SHA-256 as run | SHA-256 here |
|---|---|---|
| `diagnosis.py` | `49efd33199e035e2f88a362d07828c852704616a1cf10ca63f4238e8a6dfa2a1` | `048a402b830774f21b76b2e5673367ccbd53cdd02e3e28a25d3f261fc7e1d364` |
| `view.py` | `ad03e440a1acffd0151340c2324189e49a66666c575c64431a992973071b1f45` | `fd6c23306e867d0b7e3cad7d292195744d45defce77bdcff31af6cfb5628d027` |
| `view2.py` | `9a0a0e21bd284874c5e607574ab8c838354304242e2ed9ccce1c5dcd76a7ab11` | `9c14a0be5a3530bdced9023b38b2ddd4a2d10c0a2ea35930c2332a1d87d8f08e` |
| `view3.py` | `058ac7fac749d54950a08bda45945e285d726d441f79f609fe7c053269057667` | `04f6a89d05459b6f2e8fe4d5a87635fd49ff67713985cb7f51690dd01f598056` |

| Output | SHA-256 |
|---|---|
| `gates.json` | `021dece49c61ba425873fe9de04505883bc02026e9f318d43082f0c3b69f1eff` |
| `interruptions.json` | `7f13a3c1abeebf34da59e118bfbde66868305d79fe5791d5948fb75842fe7e5d` |
| `capacity.json` | `8baa8af1e9eca14644e9ac3c2c82f26d093a3c729f3d5b975aa50c1fc7839e82` |
| `safety-utility.json` | `3eb513c88e698682b12b6f7a968b720d905d79f8a55c6ddbcaa53bfc9a60944a` |
| `bs.json` | `d50985cf709523d768c9133c0b6e4e22b42a670bf7eb2ae031ad2adeb6df1d2c` |
| `bs-residuals.json` | `cdcf78ff12198f66cc0c6b79fc312e7aa85bd102f84db08a55a266b0832fc7c7` |
