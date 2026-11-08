**Verdict: WEAKENED. The draft should not be adopted as written.**

Amendment 11 explicitly authorizes replacing “pass every row”, so changing that procedure is legitimate. It does not authorize accepting defective operational cells, narrowing failed test populations, or substituting a different control population for T3b.

This is one review exchange, not an additional correction round. Any unresolved divergence after three exchanges goes to the maintainer with both arguments. No files were changed, no acceptance or confirmation runs were launched, and the excluded folder was not accessed.

1. **Critical, (a): family acceptance does not establish calibration in every operational cell.**

   **Evidence:** [Proposal, lines 21–38](/C:/Projetos/refute/docs/plans/v0.5.2-scope-proposal.md:21) allows some rows to fail while accepting their whole family. A defective minority of cells can satisfy the count, maximum and pooled conditions. Opposite biases can also cancel in the pooled mean.

   Replacing an unreasonable sampling rule is justified. Making every constituent cell decisive because its family passed is not justified by the proposed statistics.

   **Required change:** distinguish sampling failures from substantive cell miscalibration. Specify how each operational cell receives permission to use its errors. One defensible route is simultaneous confidence or equivalence guarantees for the unchanged population mean and scale tolerances, with adequate sample sizes. Keep aggregate summaries as additional checks. A failed or insufficiently measured cell must not inherit acceptance from its neighbours.

2. **Critical, (a): the reference run is circular and does not yet define `K_F`.**

   **Evidence:** the proposed “known error” is the Monte Carlo standard deviation of the statistic over the same row’s trials. Dividing those trials by their own sample standard deviation makes their sample scatter exactly one, by construction. Resampling afterwards does not reproduce independent estimation of that scale or the variability of the production error estimator.

   Moreover, a row’s unconditional standard deviation need not be the correct error for each curve. Variable coverage, selected shapes, random weights and unavailable errors matter. The reference also requires the new statistic whose implementation has not yet been specified.

   **Required change:** replace this description with a complete reference experiment specifying:

   - The estimand and truth for every statistic.
   - Separate reference estimation and evaluation samples, or an explicit nested procedure.
   - Whether errors are conditional or marginal, and how production studentization is represented.
   - Whole-curve resampling that preserves shared row membership, event dependence and missingness.
   - Reference sizes, bootstrap sizes, quantile uncertainty and seed separation.

   **`K_F` is not presently computable before code from this text.** Either supply a fully specified reference law that permits that computation, or return the proposed reference stage to the maintainer before implementing the correction.

3. **Important, (a): the maximum and pooled bounds need definitions and operating characteristics.**

   **Evidence:** the Gaussian standard-error formulas assume independent Gaussian pulls. A0’s per-event observations can share curves, while the fitted statistics and estimated denominators need not have Gaussian tails. The two separate 1% checks also do not establish a 1% error rate for the complete acceptance procedure.

   “Pooled standard deviation” is ambiguous. Pooling within-row variances omits between-row mean differences. For ordinary concatenated observations, the descriptive variance is

   \[
   S^2=\frac{\sum_r[(n_r-1)s_r^2+n_r(\bar p_r-\bar p)^2]}
   {\sum_r n_r-1}.
   \]

   Its uncertainty must still account for shared curves.

   **Required change:** define weights, pooling, multiplicity across both statistics and both tails, and the complete procedure’s false-rejection and defect-detection probabilities. For independent Gaussian rows, use finite-sample mean and chi-square distributions rather than an unexplained Gaussian approximation for the scale. Otherwise justify the reference distribution. Explain the asymmetric `[0.97, 1.05]` tolerance as a convention. The pooled condition hardens the new conjunction, but does not restore the old per-cell guarantee.

4. **Important, (a): a four-standard-error paired effect is insufficient sabotage acceptance.**

   **Evidence:** a detectable change can be harmless and leave a broken estimator accepted. Conversely, cadence-sharing sabotage is a structural violation, not naturally a four-standard-error effect. Dropping an insensitive sabotage can remove the only evidence that a required protection matters.

   **Required change:** specify, per sabotage, its direction, minimum meaningful effect, uncertainty estimator and planned detection power. Resample paired curves, not correlated rows. Require the baseline to satisfy its correctness criterion and the sabotage to violate the criterion it protects. Keep structural sabotages as deterministic invariants. Replacing or dropping a required protection needs an explicit design decision, not merely a record that its effect was small.

5. **Important, (a): the runtime noise rule and “5 or more” stratum remain unjustified.**

   **Evidence:** testing 5, 8 and 12 sectors does not validate 6, 7, 9–11, or arbitrarily many sectors. The [closing record](/C:/Projetos/refute/docs/validation/v0.5.1/closing-record.md:83) expressly cautions that file or available-sector counts do not establish measured-event sector counts.

   A measured lag correlation is also a noisy selector. Being observable at runtime does not establish that it reliably distinguishes the noise regimes.

   **Required change:** define the actual runtime sector-count quantity and a bounded domain. Validate interpolation or a justified worst-case envelope before grouping counts. Unsupported counts remain INCONCLUSIVE. If runtime stratification is retained, freeze its classifier and thresholds before implementation, then calibrate the entire selection procedure, including misclassification and boundary cases. Otherwise retain acceptance under every tested noise model.

6. **Important, (b): the crossover is useful, but the proposed decision rule does not isolate the mechanism.**

   **Evidence:** changing masks changes both measured signal fluctuations and their estimated errors. Requiring the crossover pull scatter to fall below 0.95 is a prediction of a particular quantitative mechanism, not a necessary consequence of mask asymmetry. White noise can also change under detrending.

   The comb construction is underspecified. The real mask currently has half-width `T`, rather than just the transit core’s `T/2`. Detrending uses a one-day window, blended quadratic fits, clipping and a sector-wide clipping scale. Disjoint pseudo-windows therefore need not have disjoint detrending influence. See [detrending implementation](/C:/Projetos/refute/src/refute/packs/tess/detrend.py:66).

   **Required change:** freeze the exact mask width, grid, comb assignment, treatment of other real masks, segment boundaries, clipping and coverage. Establish a reference implementation that masks each control separately, and demonstrate that the comb approximation reproduces it within a fixed tolerance. Evaluate paired changes in numerator variance, estimated variance, bias and availability, with uncertainty. Failure of the specified pattern should reject that quantitative explanation, not establish that masks have no role.

7. **Critical, (c): noise-only pseudo-ephemerides are not automatically the odd/even null.**

   **Evidence:** the relevant null includes equal-depth transits with unknown common shape and depth. A shape selected from those transits has a different distribution from one selected from noise. Random phases additionally change event counts, parity allocation, gaps, coverage and weights.

   The current rejection statistic uses an A0 error, and its sensitivity assumes a Gaussian alternative. A pseudo-ephemeris distribution does not automatically calibrate either quantity. See [the implemented statistic](/C:/Projetos/refute/src/refute/packs/tess/battery_v51.py:346).

   **Required change:** define and validate the equal-depth null across the relevant signal strengths, shapes, noise models and observing geometries. Repeat every relevant selection and error-estimation step. Specify whether pseudo-ephemerides estimate a standard error or directly calibrate a rejection tail, then make the sensitivity calculation consistent with that choice.

   Fix `K` and its precision requirement. If calibrating a 0.0027 rejection tail empirically, approximately **370 independent replicates provide only one tail-probability increment**. Approximately **1,109** are needed for a 95% chance of seeing even one exceedance at that rate. Correlated phase placements provide less information. A variance-only route may cost less, but then needs a separately validated tail model.

8. **Important, (c): cross-fitting does not justify the existing sum-of-events variance, and the choice rule is incomplete.**

   **Evidence:** with templates fitted on opposite parities, both final group estimates still depend on both folds. Random templates and weights introduce dependence that a fixed-template covariance sum can miss, including dependence across otherwise independent events. Different fitted shapes can also give the two amplitudes different meanings.

   The search candidate is data-selected, so calling its shape “a priori” is inaccurate. Avoiding an additional fit removes one selection step, not the upstream search.

   **Required change:** define a common amplitude estimand and calibrate the entire cross-fitted difference, including template uncertainty, cross-fold covariance and upstream selection. Treat cross-fitting as an experimental candidate, not an established guarantee.

   Freeze E2’s sample sizes, required cells, uncertainty criteria, minimum availability, power aggregation and tie-breaker. Use separate development evaluation data where practical. The box fallback must pass its own acceptance and sensitivity checks before becoming decisive.

9. **Critical, (d): the proposed out-of-claim row is a relaxation.**

   **Evidence:** [the existing acceptance](/C:/Projetos/refute/docs/plans/v0.5.1-acceptance.md:366) requires performance on planets with C1-like trends. Removing near-harmonic trends changes that population after its failure was observed. Preregistration before the next run and reporting the excluded fraction make the change transparent, but do not preserve the target.

   There is also an identifiability problem: if a permitted nuisance sinusoid and the alternative produce the same observations, no procedure can simultaneously have a 0.0027 rejection probability under one interpretation and 0.95 power under the other.

   **Required change:** remove the exclusion option. E3 should map frequency separation, amplitude and identifiability, then evaluate a joint nuisance model where separation is possible. Ambiguous cases remain INCONCLUSIVE and remain in the existing target denominators. That does not automatically satisfy the detectability requirement. If the requirements conflict, report the conflict and seek a maintainer decision on approach. Do not call the narrowed test an unchanged acceptance.

10. **Important, (e): the D1 addition genuinely hardens, but its interpretation and final variant must be fixed.**

    **Evidence:** conjoining the proposed refutation floor with D1 can only remove PASS outcomes. Applied to the historical report, it requires at least 91 refutations for EB1 and 52 for EB2. Their recorded counts are 62 and 69. All five previously passing families satisfy the proposed floor.

    However, EB2 still satisfies that floor while returning 73/186 INCONCLUSIVE. The floor prevents an all-INCONCLUSIVE result from passing when the reference refutation fraction exceeds 0.10, but does not establish satisfactory classification more generally.

    **Required change:** explicitly identify 0.10 as a maintainer-approved empirical non-regression margin, using the paired v0.4 result on the **new round’s same eligible set**, not historical counts. Freeze the optional condition before code.

    **Recommendation:** retain both the refutation floor and the proposed INCONCLUSIVE ceiling. The latter exposes EB2’s unresolved outcomes, and also preserves all five historically passing families. Keep `FAIL` as the result and put “vacuous” in its reason.

11. **Critical, (f): the extended catalog pool cannot substitute for original T3b.**

    **Evidence:** [the protocol](/C:/Projetos/refute/calibration/v0.5/PROTOCOL.md:200) defines controls through TOI FP disposition **and** TESS-EB membership, with further eligibility and identity rules. Generic catalog binaries can be much easier controls than planet-like signals that entered the TOI process. Reporting separate pools avoids silent numerical pooling, but does not authorize one pool to settle the other’s target.

    “Planet-like depth” is also undefined here. The cited protocol supplies a minimum depth, not a complete planet-like selection definition.

    **Required change:** state that original T3b retains its population, eight valid outcomes and shortage rule. A catalog-only extension is a separately named feasibility measurement, with no substitution of its PASS for T3b. Any source replacement intended to satisfy original T3b needs an explicit population-equivalence argument and maintainer decision. Freeze deduplication, prior-use exclusions, selection order, period/depth definitions, identity checks and catalog-disabled scoring.

12. **Important, (f): the sources are plausible, but labels, terms and inventory need completion.**

    **Evidence:** T10K merits consideration as a photometrically vetted EB catalog. Its full paper describes machine-learning screening followed by photometric, photocenter and human vetting. Citizen participation is not grounds for dismissing it. That process does not establish that every entry is a vetted TOI false positive or a spectroscopically confirmed binary. [Kostov et al.](https://arxiv.org/html/2506.05631v1)

    The Gaia license statement is supported by [ESA’s license page](https://www.cosmos.esa.int/web/gaia-users/license). The quoted completeness estimate does not establish the comparative “lower purity” assertion. T10K’s catalog terms are correctly marked unconfirmed.

    The [ExoFOP policy](https://exofop.ipac.caltech.edu/tess/pcp.php) contains contributor-data provisions beyond acknowledgment and citation. Their applicability must be distinguished from use of the compiled TOI table.

    **Required change:** record the full relevant label methodology and limitations; remove or source the comparative purity claim; distinguish article licenses, catalog terms and host-service policies. Retain unconfirmed labels until resolved. Add an inventory checkpoint covering overlaps, exclusions, available products and plausible selection yield. A nominal catalog size is not an eligible-pool inventory.

13. **Important, (g): the arithmetic is broadly consistent, but the workload projection is not established.**

    **Evidence:** 2,400 × 110 seconds is 73.3 processor-hours. However, that measurement covers family P with the old chain. The “62 hours” for other acceptances was a remaining allocation estimate, not a measurement of completed acceptances.

    The A0 projection omits expanded sector counts and comb detrendings. Adding equal-sized groups at 5, 8 and 12 sectors to 2, 3 and 4 increases the sector total from 9 to 34, a **3.78-fold exposure multiplier for affected work** under linear scaling. That is an illustration, not a total-cost forecast. Reference simulations, `K`, changed sample sizes and joint cross-fit calibration remain unpriced.

    **Required change:** produce a task-count and cost worksheet for the actual proposed design. Probe all C1 families and representative C2/C3 workloads, including longer curves and nested fitting. Account for reference generation, experiments, development diagnostics, compatibility checks, prefixes and reviews. Add a disk cap and preserve calibration/review reserves.

    Hard caps must bind from authorization. A probe may stop work or trigger a new decision; it must not retroactively make spending authorized.

14. **Important, (h) and completeness: version 4 is preferable, but auditability and carried obligations need explicit treatment.**

    **Evidence:** version 4 clearly identifies changed semantics. Nevertheless, version 3 imports shared A0 and pipeline functions, so preserving `battery_v51.py` alone does not preserve its behaviour.

    Also, [common.py](/C:/Projetos/refute/docs/validation/v0.5.1/acceptance/common.py:43) pins the old code hash, output directory and seed namespace. It cannot pass on unchanged to run version 4.

    **Required change:** create version-specific correction paths and runners while preserving the original artifacts. Specify schema validation, registry dispatch, reporting, accepted-cell records, fresh seed namespaces and output directories. Preserve a pinned closing commit, environment, runner hashes, result hashes and raw-output manifests. A tag is useful but is not the whole provenance record.

    Explicitly carry forward:

    - Every acceptance still unrun, the combined gates and their bounded failure procedure.
    - The hard CI requirement of every job below 30 minutes, with test-ID coverage preserved.
    - Minimum confirmation sizes, reserve invariants, bounded revisions, no unauthorized reruns and per-target infeasibility review.
    - The exact role of `duration_excess`. It currently remains diagnostic and cannot be credited with improving D1.

**Scope recommendation:** this is too broad for a confidently priced implementation round in its present form. Keep the bounded diagnostic stage, then require a concrete acceptance specification and revised cost decision before correction code.

Cut the runtime pseudo-ephemeris candidate unless it demonstrates both validity and affordable precision. Defer the optional noise classifier and Gaia tie-break. Avoid an unbounded “5 or more” domain. Do not add a catalog-only confirmation campaign merely to replace a scarce T3b pool. These cuts reduce optional mechanisms, not targets. If the remaining design cannot satisfy the unchanged targets, stop and report that outcome.

