**Verdict: WEAKENED.** The rewrite addresses all 14 round-1 objections in substance. The two-stage structure is appropriate, and I have no remaining scope objection to (b)–(f) or (h), provided their detailed specifications are frozen at the stated checkpoints.

Section (a) still needs corrections before adoption. Its equivalence principle is sound, but the sample-size statement and known-answer validation do not yet support the proposed use.

1. **Important: 1,600 is an interval-width calculation, not a reasonable certification sample size.**

   **Evidence:** [Lines 50–53](/C:/Projetos/refute/docs/plans/v0.5.2-scope-proposal.md:50). For independent unit-variance Gaussian pulls and a fixed critical value \(c=4\), mean equivalence requires

   \[
   |\bar p|+\frac{4}{\sqrt n}<0.1.
   \]

   At \(n=1{,}600\), the interval half-width is exactly 0.1. In this idealized calculation, the probability of certifying a true zero mean is zero.

   For the **mean alone, in one cell**, the approximate sizes are:

   | Desired certification probability | Independent pulls needed |
   |---|---:|
   | 80% | 2,790 |
   | 90% | 3,187 |
   | 95% | 3,553 |

   These follow from \(n\approx[(4+z_{(1+q)/2})/0.1]^2\). Requiring both mean and scale, or many cells to earn permission, increases the requirement. Shared events also mean that retained pull counts cannot automatically be treated as independent sample sizes.

   **Exact change required:** describe 1,600 as an illustrative minimum for interval width, explicitly insufficient for useful certification power. Require the worksheet to specify desired certification probability, distance from the tolerance boundaries, independent-curve counts, clustering and joint mean/scale performance. Do not use 1,600 per cell as the workload estimate.

2. **Critical: the analytic box control is sound only for a precisely defined fixed linear measurement.**

   **Evidence:** [Lines 55–62](/C:/Projetos/refute/docs/plans/v0.5.2-scope-proposal.md:55) leave “exact conditional variance” undefined.

   For raw Gaussian noise \(\epsilon\), known covariance \(\Sigma\), and box-contrast coefficients \(a\) fixed independently of that noise,

   \[
   D=a^\top\epsilon,\qquad
   Z=\frac{D}{\sqrt{a^\top\Sigma a}}
   \]

   is an exact standard-normal control. The denominator is the **standard deviation**, not the variance. The covariance must include every generated noise component and the generator’s actual treatment of gaps and sectors.

   This formula is not automatically exact after production detrending. [The implementation](/C:/Projetos/refute/src/refute/packs/tess/detrend.py:112) estimates a trend from the flux, divides by it and removes flux-dependent outliers. Conditioning on the resulting selected mask does not make the original noise remain an unselected Gaussian vector.

   **Exact change required:** define the analytic control as a fixed linear contrast on raw noise, with exogenous observing geometry and masks, and use the square-root denominator above. Explicitly state that it validates the inference machinery in that control experiment, not the correctness of errors after adaptive production preprocessing. Any stronger analytic claim requires its own derivation.

3. **Critical: the validation currently measures power and gross-defect detection, but misses the main protection against incorrect permission.**

   **Evidence:** the specified outputs are rejection of the correct estimator and detection under denominator factors 1.15 and 0.85. Those factors produce pull scales approximately 0.870 and 1.176, both comfortably outside the permitted interval.

   Equivalence testing must protect against **certifying an out-of-tolerance population**. Acceptance probability for a correct estimator measures certification power; it does not establish that protection. Failure to establish equivalence also differs from evidence of miscalibration. [Lakens’s equivalence framework](https://doi.org/10.1177/1948550617697177) makes this distinction.

   **Exact change required:** preregister and measure:

   - Simultaneous confidence-region coverage and familywise incorrect-permission probability.
   - Behaviour at and just beyond each mean and scale boundary, including mixtures of correct and defective cells.
   - Correct-estimator certification probability, separately from erroneous “miscalibrated” classifications.

   Include Monte Carlo uncertainty and fixed success criteria for these measurements. The validation must exercise the actual shared-curve layout, unequal contributions, unavailable observations and retention rules. Add known-distribution non-Gaussian controls relevant to the proposed statistics. A Gaussian oracle alone cannot validate the statement that the bootstrap handles fitted-statistic tails.

4. **Important: whole-curve resampling is the right unit, but “max-t bootstrap” is not yet a complete procedure or an unconditional guarantee.**

   **Evidence:** [Lines 38–49](/C:/Projetos/refute/docs/plans/v0.5.2-scope-proposal.md:38) omit the confidence level, studentization and treatment of the different simulation designs. Romano–Wolf’s guarantee is asymptotic and depends on distributional and standard-error consistency assumptions. It is not a finite-sample guarantee for arbitrary tails. See [the original paper, section 4](https://users.ssc.wisc.edu/~behansen/718/RomanoWolf2005.pdf).

   **Exact change required:** make the stage-1 specification explicitly fix:

   - The familywise error level, simultaneous family and centered bootstrap roots.
   - Standard-error estimation and its treatment inside resamples.
   - Resampling strata and preservation of shared-curve membership across rows.
   - Weighting, missing observations, retention rules and minimum independent-curve counts.
   - Bootstrap replication count, quantile uncertainty and applicable moment assumptions.

   Construct intervals for the signed mean, rather than bootstrapping the absolute sample mean without justification. Correct “two one-sided tests per bound” to **one test per bound, two per parameter’s equivalence interval**.

   Replace “the bootstrap carries them” with a conditional statement: its suitability for the relevant tails and clustered design must be justified and checked. These details may be stage-1 deliverables, but must precede use of the procedure for permission decisions.

5. **Important: operational cells must retain the required construction-specific checks.**

   **Evidence:** the new cell definition is coverage × sector count × statistic, under each noise model. Existing acceptance also requires separate treatment of unequal-event patterns, spacings, sector-noise arrangements, heterogeneous coverage correlations and the two secondary-exclusion branches. See [A0.4–A0.8](/C:/Projetos/refute/docs/plans/v0.5.1-acceptance.md:193).

   Pooling those constructions within an operational cell could conceal a defective configuration despite the new prohibition on inheriting acceptance from neighbouring cells.

   **Exact change required:** state that permission requires equivalence in **every required construction and conditional branch applicable to that operational cell**, or a separately justified worst-case guarantee. Include those checks in the simultaneous family and worksheet. Aggregate calibration cannot replace them.

6. **Minor, (g): “at least 97 hours” is not an established lower bound.**

   **Evidence:** [Lines 209–214](/C:/Projetos/refute/docs/plans/v0.5.2-scope-proposal.md:209) correctly identify old-chain measurements and allocation estimates, but then infer a lower bound for a different, undecided chain. A simpler selected estimator could reduce costs.

   **Exact change required:** replace that sentence with: “The previous-chain extrapolation was approximately 97 processor-hours; this is neither a measured version-4 cost nor a lower bound.”

   Distinguish stage-1 measurements of existing code or prototypes from projections for unimplemented corrections. Require probes of the final frozen workload before full acceptance and confirmation, within caps already authorized.

**The central answer:** simultaneous per-cell equivalence is a defensible replacement for the old rule. The proposed analytic AR(1) control can be exact, but only under the fixed-linear conditions above. As written, it would test a simpler experiment and would not establish that the procedure works as used on adaptive, studentized production statistics.

The remaining changes concern statistical specification and costing. They do not require widening tolerances or changing the targets. No files were changed, and the excluded folder was not accessed.

