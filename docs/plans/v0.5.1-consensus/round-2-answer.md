## Verdict: WEAKENED

The revision resolves several round-one scope gaps, but two feasibility claims still overreach their statistical bounds. The new combined gates also need protection against selecting the battery on the same acceptance seeds and against warnings that improve D1 without materially harming D2.

## Remaining objections

1. **Critical, the D1 Neyman–Pearson bound does not yet bound the target’s conditional survival rate.** The composite-null reduction is valid in principle: if a test has size at most \(\alpha\) at every planet parameter, it has size at most \(\alpha\) at \(\theta^*\). For fixed Gaussian hypotheses with common known covariance, the stated power formula is also appropriate. [Neyman and Pearson (1933)](https://www.stats.org.uk/statistical-inference/NeymanPearson1933.pdf)

   The application here is different in two ways. D1 divides by curves whose **searched candidate passed the gate**, so it is a conditional rate. The oracle fits \(\theta^*\) at the candidate found from the same data; the raw Gaussian model does not by itself give the distribution conditional on that search and gate selection. Also, the per-test false-failure bound limits failures, but the D1 metric counts only SURVIVED. A battery can reduce SURVIVED by returning INCONCLUSIVE or WEAKENED, which the stated \(\alpha\) bound does not constrain.

   **Required change:** Bound the exact conditional, end-to-end D1 outcome after candidate search and eligibility, or justify why the bound applies to that conditional experiment. Model the full verdict states and the other target constraints. Do not use the current per-test false-failure bound alone to declare D1 infeasible.

2. **Critical, the Cramér–Rao calculation is not yet a bound on the battery’s sensitivity decision.** The classical bound applies to estimator variance under regularity conditions, commonly for unbiased estimators. The plan uses it to infer that a rule cannot mark an alternative detectable, but the rule uses the estimator’s *reported* standard error. A biased estimator, a plug-in error estimate, or an estimator that understates its own error is not ruled out by the proposed unbiased-estimator bound. [MIT estimation notes](https://web.mit.edu/gallager/www/papers/chap4.pdf)

   The T2a floor has a related problem: taking the lower of pipeline error and observed scatter is plausibly optimistic, but is not shown to be a lower bound on the real white-noise variance. It also does not account for conditioning on recovered, gate-passing injections.

   **Required change:** Bound the actual registered sensitivity calculation, including estimator bias and error calibration, or restrict the claim to a specified estimator with validated sampling variance. For T2a, establish a defensible optimistic covariance floor and apply it to the same search and recovery conditioning as T2a. Otherwise, report these calculations as diagnostics, not infeasibility bounds. [Plan, WP1 bounds](/C:/Projetos/refute/docs/plans/v0.5.1-plan.md:170)

3. **Important, the bootstrap rule is conservative by intent but is not yet a defined confidence procedure.** The 95th percentile, 2,000 replicates, fixed seed, and tie toward feasibility are meaningful protections against declaring infeasibility from a favorable point estimate. The text does not specify the exact resampling and quantile procedure, how C1 clusters are defined, or the interval used to decide whether Monte Carlo uncertainty crosses 0.05. Nor does a bootstrap percentile automatically guarantee 95% coverage for these thresholded target outcomes.

   **Required change:** Freeze the bootstrap algorithm, cluster unit for each case, seed, quantile convention, and Monte Carlo interval before computation. Call the result an upper bootstrap quantile unless coverage is established. For T2a, also justify using v0.5 C2 stars to estimate the new C2′ design, which excludes prior targets. [Plan, target-level probability and decision rule](/C:/Projetos/refute/docs/plans/v0.5.1-plan.md:186)

4. **Important, the combined gates can still select changes using the acceptance data.** The gates now cover D3 and D5, which resolves the omission I flagged. But a failed gate triggers a one-change-at-a-time sabotage, then another run on the same acceptance seeds without the selected change. That second run is not an independent acceptance of the revised configuration. A fresh C1′ confirmation protects the final target result, but the plan should not describe both runs as acceptance. [Plan, combined gates](/C:/Projetos/refute/docs/plans/v0.5.1-plan.md:103)

   The #10 warning also needs a sharper guard. It can move binaries from SURVIVED to WEAKENED, improving D1 while leaving D2’s “kept” count unchanged. The specified planet false-warning rate of 0.0027 addresses that loophole only if it has an operational, defensible acceptance rule. A small observed count on the acceptance curves alone cannot establish such a low rate.

   **Required change:** Treat the sabotage run as development or screening, then freeze the chosen configuration and run an independent acceptance gate, or rely on C1′ as the only formal acceptance and label the earlier gates accordingly. Define how the duration warning’s 0.0027 limit is established, including uncertainty or validated analytical error control, and report SURVIVED-to-WEAKENED transitions separately.

5. **Important, the period_alias proposal is preregistered in spirit, but the per-candidate boundary is not automatically a pre-data test.** The plan appropriately forbids conditioning on the observed BIC. However, the candidate period, depth, times and errors are data-derived, and the boundary is calibrated on a simulated alternative using those candidate-specific values. Choosing a boundary from the alternative distribution can ensure the desired power while changing the false-refutation rate on planets.

   **Required change:** Define a fixed calibration procedure that controls false refutation or false warning on the planet/null side as well as sensitivity under the sinusoid alternative. Calibrate the full candidate-search procedure, or account for selection when using candidate-derived quantities. The D2 gate is a useful backstop, but does not substitute for specifying the test’s error control. [Plan, WP3(c)](/C:/Projetos/refute/docs/plans/v0.5.1-plan.md:97)

6. **Important, clarify the folded-binary route before accepting it as a correction.** “`odd_even` at the twice-the-period fold” is ambiguous. For an EB found at half its true period, ordinary odd/even epochs at the found period already alternate primary and secondary events. Folding at twice that period can instead group repeated primary events together. The route may be correct if it defines a different event comparison, but the current text does not say which.

   **Required change:** Define the event epochs, fold period, and comparison for EB1 and EB2 explicitly. Include cases with equal and unequal eclipse depths in the acceptance section, and report which test is expected to catch each case. [Plan, EB correction route](/C:/Projetos/refute/docs/plans/v0.5.1-plan.md:118)

## Round-one objections resolved

- **Joint photon/error covariance:** Resolved at the scope level. The plan now calls for a measured joint model and specified pull checks rather than assuming covariance. The independent pipeline implementation and its acceptance remain future work. [Plan, WP3(a)](/C:/Projetos/refute/docs/plans/v0.5.1-plan.md:97)
- **Sample-size fallback and C2 cost discrepancy:** Resolved. Minimum sizes are fixed with no cost fallback, and the plan records the C2 figure as 39.13 hours. A prefix that cannot fit the allocation stops before confirmation. [Plan, calibration sizes](/C:/Projetos/refute/docs/plans/v0.5.1-plan.md:235)
- **CI split:** Resolved as a scope proposal. The matrix update and first-push runtime and test-ID checks are now hard acceptance conditions. [Plan, CI acceptance](/C:/Projetos/refute/docs/plans/v0.5.1-plan.md:260)
- **Missing feasible-EB route:** Resolved in part. A route now exists, but its odd/even fold definition and the warning’s false-warning acceptance need the clarifications above.
- **Combined gates:** Resolved in part. They now include D3 and D5 and use frozen criteria, but the same-seed sabotage and rerun must be classified as screening, not independent acceptance.
- **Infeasibility review budget and incomplete-phase rule:** Resolved. Reviews have an allocation, accounting is defined, and an incomplete phase cannot settle targets. [Plan, caps and stop rule](/C:/Projetos/refute/docs/plans/v0.5.1-plan.md:295)

I agree with keeping the sensitivity rule, rejecting TOST-style PASS decisions and aggregation changes, and keeping #200, the EBLM part of #202, #205 beyond WP4’s classes, #206 and #12 outside this correction scope. #10 now has a relevant route, subject to the warning-control issue above. I would not finalize the consensus until the remaining objections are addressed.

