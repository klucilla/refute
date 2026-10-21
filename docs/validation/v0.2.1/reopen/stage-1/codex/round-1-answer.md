OBJECAO: The delivery preserves the maintainer’s decisions in substance, but **A, B and the instrumentation acceptance need corrections before acceptance**. The runtime arithmetic is correct; parts of the sizing rationale are not.

Reviewed the working-tree documents against code at `c45fee185afbc7ab64f2308af4e1dff82bcf49b7`. No files changed and no tests, experiments or studies ran.

**1. Faithfulness to items 0 and A to D**

| Document | Assessment |
|---|---|
| Stage-1 `README.md` | Faithful summary and authorization boundary, lines 3–21. |
| Specification A | Honest objective change; incomplete classification and acceptance contract. |
| Specification B | Faithful aggregation policy; incorrect C6 and ambiguous constant-error statement. |
| Instrumentation acceptance | Faithful purpose, but some expected behavior contradicts the code and several fields lack effective checks. |
| Experiment plan | Faithful scope restrictions and non-authorization; sizing and dependencies need clarification. |
| Study README, item 0 | Faithful, including the distinct failure mechanisms, lines 10–19. |
| Diagnosis README, item 0 | Faithful, including the correct 26/241 denominator, lines 12–17. |

The corrected summaries do not reduce the failure to sample size. They retain weakening incompatibility, coverage failures, the disappearance minimum and the target-PASS gap. [Study README:12](C:/Projetos/refute/.cache/wt-merge-check/docs/validation/v0.2.1/reopen/rmin-study/study/README.md:12), [diagnosis README:12](C:/Projetos/refute/.cache/wt-merge-check/docs/validation/v0.2.1/reopen/rmin-study/diagnosis/README.md:12).

**2. Specification A**

**The objective change is recorded honestly.** A0 explicitly withdraws the unmet criterion, dates the decision after the negative result, and replaces expected FAIL with detection at reduced depth and abstention. This is substantively different from renaming the old criterion. [Spec A:8](C:/Projetos/refute/.cache/wt-merge-check/docs/validation/v0.2.1/reopen/stage-1/spec-a-weakened-scenario.md:8).

The temporal definition also matches the intended presence test. The current `fail_rule` first rejects invalid statistics, then PASSes at `snr >= min_snr`; only a non-detection proceeds to the signed depth-inconsistency test. Consequently, a weakened detection can PASS regardless of its depth difference. [Spec A:20](C:/Projetos/refute/.cache/wt-merge-check/docs/validation/v0.2.1/reopen/stage-1/spec-a-weakened-scenario.md:20), [holdout.py:1254](C:/Projetos/refute/.cache/wt-merge-check/src/refute/packs/tess/holdout.py:1254).

Three corrections remain:

- **D/M/U/N is not exhaustive.** N covers an unrecorded `S_pred,2`, but not a recorded NaN. The engine can produce NaN predicted SNR, which satisfies none of the numeric class inequalities. Define N explicitly for missing **or non-finite** values, with boundary examples. [Spec A:34](C:/Projetos/refute/.cache/wt-merge-check/docs/validation/v0.2.1/reopen/stage-1/spec-a-weakened-scenario.md:34), [holdout.py:1517](C:/Projetos/refute/.cache/wt-merge-check/src/refute/packs/tess/holdout.py:1517).

- **Separate predicted detectability from established detectability.** `ρ = 0.3·S_pred,2` is an operational prediction using the engine’s error model. X2 has not established that model’s agreement with observed scatter. The labels are usable as predeclared operational classes, but “expected SNR” and “detectable” should carry that qualification. U PASS being reported without an error label is coherent with presence: a low prediction does not prohibit a detection. N’s “abstention by construction” should refer to the last-year round, since another year can still cause final FAIL.

- **Metrics are defined, but the success contract remains adjustable.** W1/W1e/W2 and the 3/8 boundaries are specified before new data. However, W1’s limit “if any” may be selected from pilot yields. That leaves a consequential acceptance choice open. Fix its role and the rule for choosing its limit before the pilot; pilot yields should determine feasibility and sample size. Also, an algebraically non-empty D interval does not establish a positive decided-target yield through the other gates. [Spec A:60](C:/Projetos/refute/.cache/wt-merge-check/docs/validation/v0.2.1/reopen/stage-1/spec-a-weakened-scenario.md:60), [Spec A:70](C:/Projetos/refute/.cache/wt-merge-check/docs/validation/v0.2.1/reopen/stage-1/spec-a-weakened-scenario.md:70).

**3. Specification B**

**The necessary-years definition is metadata-only as written.** `raw.years` is the sorted unique cadence-year metadata. It does not depend on the candidate, capacity or round outcome. [Spec B:18](C:/Projetos/refute/.cache/wt-merge-check/docs/validation/v0.2.1/reopen/stage-1/spec-b-target-pass.md:18), [types.py:137](C:/Projetos/refute/.cache/wt-merge-check/src/refute/packs/tess/types.py:137).

B2 correctly specifies FAIL precedence, requires every necessary year for PASS, and otherwise abstains. B3 covers the principal outcomes and preserves the existing one-year refusal. Permutation tests address outcome order independence. [Spec B:30](C:/Projetos/refute/.cache/wt-merge-check/docs/validation/v0.2.1/reopen/stage-1/spec-b-target-pass.md:30), [holdout.py:1782](C:/Projetos/refute/.cache/wt-merge-check/src/refute/packs/tess/holdout.py:1782).

**C6 is incorrect.** Changing year Y’s hidden flux must preserve the train-only preparation of **the round hiding Y**. Other rounds train on Y, so their decisions may legitimately change. The existing blindness test compares the same hidden-year round before and after replacement. [Spec B:73](C:/Projetos/refute/.cache/wt-merge-check/docs/validation/v0.2.1/reopen/stage-1/spec-b-target-pass.md:73), [tests/test_holdout_blindness.py:73](C:/Projetos/refute/.cache/wt-merge-check/tests/test_holdout_blindness.py:73).

The controls also need explicit completeness checks: one round per necessary year, missing/duplicate years, empty input, and zero/one-year guards. This matters because the current study evaluator constructs a dictionary keyed by year and aggregates the records supplied. [rmin_evaluate.py:156](C:/Projetos/refute/.cache/wt-merge-check/docs/validation/v0.2.1/population/rmin_evaluate.py:156).

**B5 correctly measures final target false PASS over all decided targets**, including those omitted by the old power filter. Error and utility are reported separately, and the rise in abstention is explicitly visible.

However, “false FAIL unchanged by B” needs qualification: **FAIL counts remain unchanged; error among decided targets can change**, because PASS targets become INCONCLUSIVE and leave that denominator. Require both denominators explicitly for constant targets. [Spec B:81](C:/Projetos/refute/.cache/wt-merge-check/docs/validation/v0.2.1/reopen/stage-1/spec-b-target-pass.md:81).

**4. Instrumentation acceptance**

**The quantities exist, but not every promised source survives every return path.**

- Capacity quantities are computed in `cap`, including grid, variances and predicted errors. [holdout.py:1408](C:/Projetos/refute/.cache/wt-merge-check/src/refute/packs/tess/holdout.py:1408).
- The fitted ephemeris, duration and timing information exist at the timing stop.
- At `train_noise_undetermined`, a candidate already exists, but `plan_round` returns neither that candidate nor its duration in the returned plan. Meeting “as soon as the candidate exists” therefore requires retaining diagnostics inside `plan_round`, not merely copying the existing calibration result. [holdout.py:981](C:/Projetos/refute/.cache/wt-merge-check/src/refute/packs/tess/holdout.py:981).

The acceptance contract has four concrete gaps:

1. **AB2 gives the wrong empty-grid result.** Empty counts fail `replicas_enough` before `e_pred_1` is computed. The actual stop is `train_replicas_below_r_min`, with the predicted error still unavailable. `period_grid` ordinarily produces a non-empty grid, so an empty-grid boundary also needs an explicitly injected fixture. [Acceptance:62](C:/Projetos/refute/.cache/wt-merge-check/docs/validation/v0.2.1/reopen/stage-1/instrumentation-acceptance.md:62), [holdout.py:1490](C:/Projetos/refute/.cache/wt-merge-check/src/refute/packs/tess/holdout.py:1490).

2. **AB3 conflates production stops with calibration recording.** Calibration calls `_round_corrected(enforce=False)`, so decisions 1 and 2 do not stop subsequent computation. Later fields can correctly be populated despite those decisions failing. Specify separate expected-field matrices for actual calibration returns and enforced execution. [holdout.py:1701](C:/Projetos/refute/.cache/wt-merge-check/src/refute/packs/tess/holdout.py:1701).

3. **AC1–AC4 do not check every new field effectively.** There is no explicit source-equality check for recorded `e_pred_1/2`, duration, transit-time count or grid values. Comparing SNR formulas and array lengths cannot establish those values. Add independent source comparisons, formula applicability conditions, and zero/negative/non-finite variance cases.

4. **The sabotages are not all guaranteed to bite.** S2 can permute hidden variances across `dP` while preserving their maximum and length, passing AC1–AC3. Require elementwise `(grid_dp[i], variance[i])` checks with unequal values. S5 needs exact-threshold and adjacent-representable-value fixtures; ordinary cases can miss a one-ulp comparator mutation. S6 needs a defined prohibited-read witness, beyond unchanged signatures. [Acceptance:43](C:/Projetos/refute/.cache/wt-merge-check/docs/validation/v0.2.1/reopen/stage-1/instrumentation-acceptance.md:43), [Acceptance:80](C:/Projetos/refute/.cache/wt-merge-check/docs/validation/v0.2.1/reopen/stage-1/instrumentation-acceptance.md:80).

AC5’s exact preservation requirement is appropriate. It protects existing behavior but cannot, by itself, validate newly added fields.

**5. Experiment costs, sizing and dependencies**

The rate conversion and displayed curve-to-hour arithmetic are correct:

`45.24 × 3600 × 6 / 76800 = 12.72375 worker-seconds/curve`

Throughput is **1697.61 curves/hour on six workers**.

| Planned curves | Recomputed hours |
|---:|---:|
| X2: 6,000 | 3.534 |
| X3: 2,600 | 1.532 |
| X5: 56,400 | 33.223 |
| X5 alternative: 28,800 | 16.965 |
| X6 illustration: 200,000 | 117.813 |

These are throughput projections for different future workloads. [Experiment plan:8](C:/Projetos/refute/.cache/wt-merge-check/docs/validation/v0.2.1/reopen/stage-1/experiments-plan.md:8).

**The sizing qualifications need correction:**

- **X5’s “smallest yield seen, about 1.3%” is false.** The diagnosis reports disappearing utility of `41/6400 = 0.640625%`. Under the same pointwise normal approximation, ±25% at 95% needs approximately **9,534 targets for that cell**, versus approximately 4,667 at 1.3%. The new aggregation and D classes introduce additional unknown yields. [Diagnosis:99](C:/Projetos/refute/.cache/wt-merge-check/docs/validation/v0.2.1/reopen/rmin-study/diagnosis/README.md:99), [experiment plan:22](C:/Projetos/refute/.cache/wt-merge-check/docs/validation/v0.2.1/reopen/stage-1/experiments-plan.md:22).

- **X3’s 520 rounds is conditional.** It matches the usual normal-distribution asymptotic approximation for MAD precision, not a distribution-free guarantee. The plan also substitutes precision of `s` for the diagnosis’s requested precision of the **threshold**, which depends on `b` too. Its 40% yield must apply to the complete selected set, including each R’s replica restrictions, with the round selected beforehand. [Experiment plan:20](C:/Projetos/refute/.cache/wt-merge-check/docs/validation/v0.2.1/reopen/stage-1/experiments-plan.md:20), [rmin_evaluate.py:104](C:/Projetos/refute/.cache/wt-merge-check/docs/validation/v0.2.1/population/rmin_evaluate.py:104).

- **X2’s regimes are ambiguous.** “White; AR(1); with variability” does not define disjoint cells. Six thousand curves is correct for three cells; four crossed cells would require 8,000, approximately 4.71 hours.

The broad order is sound: instrumentation before X2, independent calibration before compatibility checks, pilot before main, reserve after selection. Explicitly require accepted instrumentation before dependent lots, and require renewed acceptance/calibration if X2 motivates an error-model change. X4 can establish algebraic compatibility; X5 must establish practical yield.

**Item C is faithful:** operational features, misclassifications included, no automatic exclusion, and an explicitly reduced validated population. The plan also clearly authorizes nothing. [Experiment plan:28](C:/Projetos/refute/.cache/wt-merge-check/docs/validation/v0.2.1/reopen/stage-1/experiments-plan.md:28).

**Recommendation:** retain the decisions and historical summaries, revise these specification and acceptance gaps, then review the revised documents. Calibration, pilot and main study remain unauthorized. The maintainer makes the final decision.

