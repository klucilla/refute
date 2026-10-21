OBJECAO: The delivery supports the central conclusion, **no R_min was validated**, and most calculations check out. I would accept it as development evidence, but would not endorse “exactly as declared” or consider the next-study proposal complete without the clarifications below.

All checks were read only. I compared the code and outputs, independently reproduced Q5 calculations in memory, and did not run the engine or the script’s file-writing entry point.

**1. Implementation and numerical checks**

| Item | Assessment |
|---|---|
| Gate classification | Correct for this lot. `gate_of` follows `derive_round`: G0, train replicas, decision 1, hidden noise, decision 2, measurement impediments, FAIL rule. G3 precedence matches the declaration. Across every R and cell, gate counts reconcile and no round is unclassified. See [diagnosis.py:67](C:/Projetos/refute/.cache/merge-v021/rmin/diagnosis.py:67) and [holdout.py:1729](C:/Projetos/refute/.cache/wt-merge-check/src/refute/packs/tess/holdout.py:1729). |
| Q1/Q2 denominators | Population and reach denominators are separate. T-a counts aggregated INCONCLUSIVE targets once by reason combination; T-b counts targets reaching each stop independently. See [diagnosis.py:229](C:/Projetos/refute/.cache/merge-v021/rmin/diagnosis.py:229) and [diagnosis.py:254](C:/Projetos/refute/.cache/merge-v021/rmin/diagnosis.py:254). |
| Q3 categories | Correct and exhaustive in the supplied outputs: undefined, below 5, and `[5, threshold)`. No G2 or G4 row, at any R, has an uncategorized remainder. See [diagnosis.py:293](C:/Projetos/refute/.cache/merge-v021/rmin/diagnosis.py:293). |
| Q5 | B1 retains complete selected target clusters. B2 resamples all 100 targets before applying the fixed selection, preserving duplicates. Thresholds use paired `b*` and `s*`. The unequal-cluster ANOVA uses the declared `n0` adjustment and retains negative ICC values. See [diagnosis.py:386](C:/Projetos/refute/.cache/merge-v021/rmin/diagnosis.py:386) and [diagnosis.py:477](C:/Projetos/refute/.cache/merge-v021/rmin/diagnosis.py:477). |
| Q8 | Correctly separates eligible, decided, total and evaluation-qualified targets. Eligible-error numerators are restricted to eligible targets; qualified disappearance outcomes remain identifiable. Bounds are one-sided 99%, over targets. See [diagnosis.py:345](C:/Projetos/refute/.cache/merge-v021/rmin/diagnosis.py:345). |

**The fidelity objection is Q3’s scenario pooling.** The declaration’s default is R × group × scenario. Q3 adds band and mechanism cuts without explicitly declaring scenarios pooled. The implementation keys its distributions by `group|band|mechanism`, omitting scenario, although its per-target count table retains scenario. Consequently, the 108,300 G2 rounds and associated quantiles pool all three scenarios. This needs correction or explicit acknowledgement as a departure from the frozen declaration, not retrospective amendment of that declaration. Compare [DECLARATION.md:80](C:/Projetos/refute/.cache/wt-merge-check/docs/validation/v0.2.1/reopen/rmin-study/diagnosis/DECLARATION.md:80), its Q3 specification at line 110, and [diagnosis.py:219](C:/Projetos/refute/.cache/merge-v021/rmin/diagnosis.py:219).

The numerical spot checks otherwise passed:

- **Q3:** 61,109 below-minimum + 47,191 margin-only = **108,300** G2 rounds at R = 8. Two-year and three-year thresholds are **12.507518** and **12.876998**, matching the README’s rounded components. See [capacity.json:9](C:/Projetos/refute/.cache/merge-v021/rmin/diagnosis/capacity.json:9).
- **Q5:** Raw bs-choice records reproduce every published residual selection. Both bootstrap variants reproduce all reported percentile endpoints exactly for all five R values. ICC differences are at most floating-point rounding. At R = 8, ICC is **0.469733**, and B1’s threshold interval is **[9.291935, 17.186805]**. See [bs.json:19](C:/Projetos/refute/.cache/merge-v021/rmin/diagnosis/bs.json:19) and [bs.json:96](C:/Projetos/refute/.cache/merge-v021/rmin/diagnosis/bs.json:96).
- **Q8:** AR(1), variability, disappearing gives **26/241 = 10.788%**, upper bound **16.309%**, versus **26/6400 = 0.40625%** over all targets. All 210 evaluation-qualified targets FAIL, so none of those 26 PASS targets belongs to that set. See [safety-utility.json:166](C:/Projetos/refute/.cache/merge-v021/rmin/diagnosis/safety-utility.json:166).

Two reporting clarifications matter:

- The train-SNR paragraph uses **15,085/18,574**, but 18,574 includes **1,751 unrecorded SNRs**. Among recorded SNRs, the denominator is **16,823**, giving 89.7%; over all INCONCLUSIVE rounds it is 81.2%. See [README.md:39](C:/Projetos/refute/.cache/merge-v021/rmin/diagnosis/README.md:39) and [interruptions.json:3050](C:/Projetos/refute/.cache/merge-v021/rmin/diagnosis/interruptions.json:3050).
- Q5 has **17 one-round, 7 two-round and 16 three-round targets** at R = 8. Reporting only “seven targets with two rounds” understates the visible extent of repeated observations unless the three-round clusters are also mentioned. The bootstrap and ICC correctly include them. See [bs.json:3](C:/Projetos/refute/.cache/merge-v021/rmin/diagnosis/bs.json:3) and an example at [bs-residuals.json:110](C:/Projetos/refute/.cache/merge-v021/rmin/diagnosis/bs-residuals.json:110).

**2. Confirmed causes versus hypotheses**

For the seven rows in the [problems table](C:/Projetos/refute/.cache/merge-v021/rmin/diagnosis/README.md:86):

| Problem | My assessment |
|---|---|
| 1. Weakening eligibility | **Confirmed with a qualification:** algebraic incompatibility holds at R = 8–15. At R = 20, the two-year window is narrow but non-empty; zero observed yield is empirical, not mathematical impossibility. The summary saying calibration made the window empty needs that exception. |
| 2. Insufficient eligible counts | **Confirmed:** uniform 15% sizing was an assumption, and measured yields differ sharply by group. Raising the calibrated threshold can only restrict gate admission, but its quantitative contribution to lost target eligibility was not separately measured. |
| 3. Inflated predicted error | **Honestly labelled hypothesis.** `e_pred/e_train > 1` does not establish inflation relative to the hidden-year sampling error. A white-noise check alone also cannot refute the proposed concentration in variability groups. |
| 4. Regime mixture | **Honestly labelled hypothesis.** The residual distributions differ descriptively. ICC and bootstrap spread do not establish a population-level causal explanation. “No difference refutes” needs a predeclared equivalence margin and sufficient precision; failure to detect a difference is insufficient. |
| 5. Unexamined target PASS | **Confirmed aggregation/criterion mismatch.** Aggregation permits an earlier-year PASS when the altered last year is undecided, while disappearance power examines the qualified last-year subset. The reason for concentration in AR(1), variability remains unanswered, correctly acknowledged in `exploratory.md`. |
| 6. Weakened PASS | **Confirmed code behavior:** detection precedes depth inconsistency. That explains the decision branch, but whether these PASSes are errors awaits the maintainer’s definition. |
| 7. Low utility | **Confirmed counts and stopping locations.** These establish where rounds stop, not that the error model is defective or a quantitative causal decomposition of target-level abstention. |

The relevant engine behavior is explicit in [fail_rule:1257](C:/Projetos/refute/.cache/wt-merge-check/src/refute/packs/tess/holdout.py:1257), [aggregate:144](C:/Projetos/refute/.cache/wt-merge-check/docs/validation/v0.2.1/population/rmin_evaluate.py:144), and the qualified-set selection at [rmin_evaluate.py:279](C:/Projetos/refute/.cache/wt-merge-check/docs/validation/v0.2.1/population/rmin_evaluate.py:279).

**3. The single proposal**

The sequence is sound: definition, instrumentation, calibration, compatibility check, separate pilot, main study, independent reserve. It avoids substituting a weakening number and explicitly forbids choosing an estimator to lower the gate. See [README.md:96](C:/Projetos/refute/.cache/merge-v021/rmin/diagnosis/README.md:96).

**It remains an outline, with these required specifications:**

1. **Put acceptance criteria before tests and code.** “Before any lot” is weaker than the maintainer’s requirement. State explicitly that coherence and boundary cases, expected outcomes and tolerances are fixed before instrumentation changes. ROADMAP requires acceptance records before tests and code: [ROADMAP.md:200](C:/Projetos/refute/.cache/wt-merge-check/ROADMAP.md:200).

2. **Make the controls non-vacuous.** “A constant planet must not FAIL” permits universal INCONCLUSIVE. Include an eligible positive control that must PASS with coverage, and an eligible disappearance that must FAIL, including correlated-noise cases. Keep abstention and refusal controls separate.

3. **Predeclare how pilot evidence determines sizing.** Specify precision, confidence treatment across groups/scenarios, the sizing formula, uncertainty allowance, scope-choice rule and ceilings. A confidence interval for pilot yield is not automatically a prediction interval for the main lot’s observed yield. Falling outside it does not by itself refute sizing. The approximately 4,700-target example is reasonable planning arithmetic, not a finished design.

4. **Specify the reserve contract.** “Own seeds, run once” omits its size, composition, criteria, confidence level and failure consequence. The existing reserve specification requires future drand seeds declared at selection, the same composition and sizes, frozen pairs, and no second R tried after reserve failure: [map:2117](C:/Projetos/refute/.cache/wt-merge-check/docs/validation/v0.2.1/reopen/m4-implementation-map.md:2117).

5. **Constrain scope reduction before observing the main lot.** Yield-based exclusion can satisfy the authorized scope-reduction option, provided its rule is fixed beforehand and the retained scope has an observable engine boundary. Excluding a synthetic group does not itself define that boundary. It must not be represented as validation of the original four-group claim.

I found **no implemented tuning toward PASS**, dispersion reduction, substitute weakening criterion or adoption of an asymmetric mode. The proposal’s open choices could create those problems later unless these constraints are explicit.

**4. “Blocks or changes”**

The list is substantially right, with three qualifications:

- **T4 remains blocked under the approved order.** It requires the chosen R_min and follows the study and reserve. However, admitted T4 rounds bypass capacity decisions and do not use b/s; their validity requires T4’s own calibration and evaluation. See [map:731](C:/Projetos/refute/.cache/wt-merge-check/docs/validation/v0.2.1/reopen/m4-implementation-map.md:731), [map:830](C:/Projetos/refute/.cache/wt-merge-check/docs/validation/v0.2.1/reopen/m4-implementation-map.md:830), and [map:874](C:/Projetos/refute/.cache/wt-merge-check/docs/validation/v0.2.1/reopen/m4-implementation-map.md:874).
- **Amendment 28 sizing needs fresh evidence.** Its 15% assumptions are explicit. But this broader R_min lot does not directly measure T4 yields in its restricted two-year population and admission path. The T4 pilot must match that population and path. See [map:774](C:/Projetos/refute/.cache/wt-merge-check/docs/validation/v0.2.1/reopen/m4-implementation-map.md:774) and [map:844](C:/Projetos/refute/.cache/wt-merge-check/docs/validation/v0.2.1/reopen/m4-implementation-map.md:844).
- **The R_min reserve cannot replace v0.2.1 confirmation.** Criterion 2 also requires planet, false-positive and noise-only measurements; criterion 3 requires the final frozen-code confirmation. AR(1) development results do not discharge criterion 1’s acceptance controls. The stated downstream deferrals are appropriate, but success in a corrected R_min study alone would not close them. See [ROADMAP.md:208](C:/Projetos/refute/.cache/wt-merge-check/ROADMAP.md:208), [ROADMAP.md:216](C:/Projetos/refute/.cache/wt-merge-check/ROADMAP.md:216), and [ROADMAP.md:233](C:/Projetos/refute/.cache/wt-merge-check/ROADMAP.md:233).

**Recommendation to the maintainer:** retain the diagnosis as development evidence, request a reporting correction/addendum and a fully specified staged protocol before authorizing execution. Preserve the failed study, publication containment and absence of any SURVIVED promotion. The decision remains yours.

