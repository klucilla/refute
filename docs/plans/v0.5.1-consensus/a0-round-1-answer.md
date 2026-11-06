# A0 verdict: WEAKENED

The maintainer’s approval resolves the stop-rule objection for A0. Removing event-count scaling resolves the independence objection behind that scaling. Replacing the nominal minimum with an effective-count rule addresses the overlapping-shift objection in principle.

Two important gaps remain before I can mark A0 **SURVIVED**.

1. **Critical, the variance correction is not justified for the stated robust statistic.** A0 defines `s_i` as `1.4826 × MAD`, then applies `s_i² (n−1)/(n−n/n_eff)`. The expectation cited for that correction applies to the ordinary sample variance under the specified covariance model, not to squared MAD. Also, `n_eff` uses only lags 1–5, so the same variance identity does not follow if dependence persists beyond lag 5. A0.1 and A0.2 do require empirical pull calibration, which is valuable, but the text still presents this formula as a derived variance correction without defining what validates it when those assumptions fail.

   **Exact change:** In “Per-event error,” replace the claim that the corrected variance follows from the expectation of the sample variance with a method whose assumptions match the estimator. Either use the ordinary sample variance in that correction, or define a MAD-based uncertainty estimator and require its pull calibration to pass in each applicable stratum. State what happens when dependence beyond lag 5 fails validation: the affected errors and verdicts must remain diagnostic or inconclusive, never decisive.

2. **Important, calibration is not consistently specified for every promised stratum, and the unequal-event pattern is underspecified.** The strata paragraph promises calibration by noise model × coverage, and by sector count for group statistics. But A0.2 instead defines its strata as noise model × number of sectors, and A0.5 says “per stratum” without specifying the required count-mismatch patterns, event spacing, or sector-noise combinations. That leaves the required group-pull calibration unclear for the cases that motivated the change.

   **Exact change:** Define A0.2’s strata explicitly as noise model × coverage × sector count, and define A0.5’s prespecified unequal-count and gap patterns within those strata. Require the group-pull bands for each pattern and report the results by stratum. If a required combination cannot be calibrated, group statistics that rely on it must stay diagnostic or inconclusive.

A0.6 directly checks dependence beyond lag 5 and requires group-pull calibration, which is the right safeguard. But its “within `2 / sqrt(n)` of zero” condition is not, on its own, proof of independence. The direct pull requirement should remain the acceptance gate for the affected strata.

# Duration finding

The arithmetic is sound to the stated approximation. For small `R*/a`, the central circular duration scales roughly as `P^(1/3)`, so `T_max(2P) − T_max(P)` is about `(2^(1/3) − 1) T_max(P)`, or **26%** of `T_max(P)`. With independent 5% radius and mass errors, their contribution to `sigma_Tmax / T_max` is approximately `sqrt(0.05² + (0.05/3)²) = 5.27%`. The sensitivity threshold is `3 + 1.645 = 4.645`, so the combined uncertainty must be at most about `26% / 4.645 = 5.6%` of `T_max`. That leaves `sigma_T` at roughly `sqrt(5.6² − 5.27²)% = 1.9%` or less. Uncertainty in the fitted depth can make the constraint tighter.

**I support option (i): make `duration_excess` a reported diagnostic outside the verdict.** Its present sensitivity rule makes detectability depend on unusually precise duration and TIC stellar parameters. Keeping it decisive risks making many otherwise assessable planets inconclusive. As a diagnostic, it can still report the duration comparison and calibration, while EB1/EB2 verdicts rest on `odd_even`. If that leaves the required binary separation infeasible, the plan’s existing post-confirmation infeasibility path can evaluate that outcome. This needs the maintainer’s decision because it changes material outside A0 after the acceptance document’s revision allowance.

