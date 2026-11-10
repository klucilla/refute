**I recommend path (ii), closing v0.5.2 as not approved.** The measured failures, failed adequacy gate and unresolved budget support that recommendation. The record needs corrections, particularly its claims about coverage and information limits.

1. **LOW: the measured T2a failure is supported, independently of the unrun stratum.**

   I verified 615 eligible historical injections, split **302 / 257 / 56**. Historical v0.4 kept **300 / 257 / 56**, giving the fixed minimum **0.896748**. The successful forecast contains 80 records, zero errors and zero compatibility problems.

   The reported hypergeometric construction conservatively combines stratum intervals and unknown outcomes. Its upper endpoints for v3 and C, **0.6423 and 0.5707**, remain below the minimum even allowing every unrun outcome to be kept.

   **Require:** label v3’s 0.3894 and C’s 0.3126 as *pessimistic endpoints of partially identified estimates*, rather than ordinary point estimates. Keep the exact historical v0.4 baseline separate from its weighted sample estimate. The general summary rule “FAIL if the point is below minimum” could misclassify an unresolved case with missing outcomes, although that defect does not change this forecast’s conclusion.

2. **HIGH: `not_enough_data` does not establish an irreducible coverage limit.**

   `systematics.not_run_class` collapses several causes into that class. Crucially, [A0’s depth function](C:/Projetos/refute/src/refute/packs/tess/a0_v4.py:130) can return `None` because empirical errors are unavailable, contributing sectors fall outside the grid, or group variance cannot be calculated. `systematics` can then report “no transit measured” as `not_enough_data`. The v3 function similarly conflates absent events with unavailable calibrated errors.

   The core coverage rule only converts a **PASS without positive declared coverage** into INCONCLUSIVE. The additional requirement that every applicable `systematics` sub-check complete is implemented inside that test. Neither establishes that an improved measurement could never complete it.

   **Require:** replace “T2a is out of reach under the coverage rule” with “the current battery is forecast to fail, and the unresolved `systematics` measurements require diagnosis.” Do not propose changing T2a’s target definition as a necessary remedy.

   Even treating the current `systematics not_enough_data` classifications as permanent, an optimistic calculation removing every other INCONCLUSIVE gives v4 a simultaneous upper endpoint of approximately **0.9024**, still above 0.89675. Population-level unreachability is therefore not established by these 80 injections.

   The closing-record quotation concerns the earlier strict A0 acceptance interpretation, not proof of an unavoidable conflict between T2a and the general coverage principle.

3. **MEDIUM: the T2a blocker calculation is useful, but its scenario descriptions overstate it.**

   The T2a helper correctly uses decisive, non-deferred tests, retains fatal FAILs, and treats warning FAILs as kept. I reproduced its baseline kept/not-kept classification on all 80 records.

   **Require three corrections:**

   - For **B with the cap retained**, above-20 outcomes are known losses. The all-kept upper endpoint represents an additional counterfactual extension, not uncertainty about B itself.
   - Removing `outside_domain` is an oracle scenario requiring a prospective, validated domain extension. It is not an admissible estimator correction by itself.
   - “Mostly kept” is arithmetically wrong. In the odd_even + sinusoid + all-systematics row, the weighted estimates require approximately **14%** of the above-20 stratum kept for v4, and **25%** for v3. The “every INCONCLUSIVE” row already exceeds the minimum at its lower endpoint.

   Add sampling uncertainty before using these what-ifs to claim impossibility. Their ranges currently bound the unrun stratum only.

4. **HIGH: 16/17 does not establish “no information limit for odd_even.”**

   It shows that an optimistic calculation, using the true shape and known noise model, reaches the sensitivity threshold on 16 selected problem curves. It does not demonstrate an attainable estimator with estimated covariance, fitted ephemeris, nuisance parameters and valid uncertainty. WP1’s 98.9% is another information forecast, not independent evidence of attainability.

   **Require:** say **“the diagnosis does not establish an information limit, and does not support a D2 infeasibility finding.”** That conclusion is justified. “There is no information limit” is stronger and unsupported.

   Path (iii) would need a bound on attainable testing performance under clearly stated assumptions, mapped to enough of D2’s population to force failure. An optimistic Cramér–Rao variance plugged into Gaussian power is not, by itself, a universal impossibility or feasibility proof.

5. **MEDIUM: the error decomposition is approximate, not a clean attribution to A0 versus estimator.**

   `sigma_box_true` holds observed weights, selected events and preprocessing output fixed, then applies the generator’s original covariance. It omits detrending effects and randomness in those choices. Meanwhile, the Cramér–Rao calculation uses the true template and full original data.

   **Require:** rename it a *conditional linear-box error under the generator covariance*. Describe the ratios as diagnostic comparisons. They mix estimator weighting, selection, preprocessing, nuisance knowledge and potentially different depth responses. They do not establish that A0 adds exactly 10% and the estimator exactly 33% to the operational error.

6. **MEDIUM: the combined D2 figure is not “odd_even at the bound plus sinusoid.”**

   **0.892857, or 100/112**, removes every odd/even sensitivity blocker. Curve 1075 remains below the required power at the bound and also has a sinusoid blocker. Restricting odd/even removal to the bound-supported curves gives **99/112 = 0.883929** when sinusoid blockers are removed.

   **Require:** distinguish those scenarios and reduce the stated margin from approximately 0.029 to **0.020** for the bound-supported combination. Both remain optimistic blocker-removal calculations, not predicted performance of a constructed estimator.

   Also make the D2 helper severity-aware, as the T2a helper already is. It currently treats all FAILs as blockers, although warning FAILs can yield a kept WEAKENED verdict.

7. **MEDIUM: the literature supports candidates for investigation, not a ready correction.**

   E2’s conclusion is accurately reported: none of its candidates qualified. However, “shape-fixed” alone is not the new ingredient, because E2 already tried fixed candidate templates.

   **Require:** identify the prospective difference precisely, such as a joint correlated-noise likelihood with explicit treatment of shape, timing, covariance estimation and odd/even covariance.

   The literature statement also needs narrowing. [Carter and Winn](https://arxiv.org/abs/0909.0747) report simulation evidence for improved uncertainty estimates under their assumed correlated-noise processes. That does not validate Refute’s odd/even statistic. [LEO-Vetter](https://arxiv.org/html/2509.10619v1#S4.SS4) supports the proposed fitting approach but also reports unavailable fit uncertainties. Neither source supplies Refute’s required calibration evidence. Sources checked on 2026-11-10.

8. **MEDIUM: consumption is correct; path costs and dates need reconciliation.**

   I obtain **13.673 CPU-h** for the forecast and **176.833 CPU-h** spent in stage 2, agreeing with the record.

   | Path | What the record can reasonably claim |
   |---|---|
   | **(i)** Amendment | Estimator exploration at 20–60 CPU-h is an unmeasured estimate. Taking the stated 2,979 remaining hours and uplift literally gives **3,297–3,933 additional CPU-h**, or **3,474–4,110 total** including current spending. Reconcile overlapping allocations before quoting a final total. At 9.8 CPU-h/hour, that is roughly **14–17 compute days**, plus development and pauses. |
   | **(ii)** Close not approved | Essentially no further experiment CPU; approximately one day for documentation/review is a planning estimate. Review tokens and agent effort still count. |
   | **(iii)** Infeasibility investigation | The quoted 2–5 CPU-h and one or two days price only a proposed sinusoid diagnostic, not a complete infeasibility record. The latter remains unpriced. |

   **Require:** separate spent, additional work, lifetime total and planning allowance. Reprice from the prospective estimator and revised validation workload, rather than assuming a generic 10–30% increase. December completion cannot be asserted without a resume date after the November pause. The 6.1 agent-day figure also needs explicit scope and accounting across agents.

9. **LOW: provenance is mostly sound, with wording corrections.**

   The reviewed forecast uses development inputs, separate cache artifacts and derived reports. I found no source or calibration-file changes across the forecast commits examined. This is not a confirmation run or an acceptance rerun.

   **Require:** correct `476968c` to **`4769684`**. Say the exclusion was decided before the main run, **after an end-to-end timing smoke**, rather than before any result. Preserve committed measurements and publish corrections as new derived records. Retain both failed gates and the STOP.

**My recommendation remains (ii).** Close as **not approved**, without declaring either D2 or T2a infeasible. Path (i) currently lacks an integrated, calibrated solution and an approved budget. Path (iii) lacks the necessary impossibility evidence. Before committing the remaining round, diagnose the unresolved `systematics` causes while preserving both the target and the coverage requirements.

WEAKENED

