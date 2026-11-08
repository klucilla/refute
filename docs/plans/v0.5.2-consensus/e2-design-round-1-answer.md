**Verdict: WEAKENED. Round 1 of at most 3.**

The estimator wiring largely survives. The evaluator and frozen choice rule need correction before the full run. This verdict concerns the experiment’s ability to support a recommendation, not whether any estimator ultimately works.

I inspected the current files, E1’s result, the E1/E3 review records, and the existing smoke. Verification used isolated in-memory fixtures. **No experiment units were executed, no files were written, and the prohibited directory was not accessed.** The reviewed E2 fingerprint is `9890e48ec426d683`.

What survives:

- The generator implements equal-depth trapezoids under the null and odd-only, full-depth events under the alternative.
- `built`, `built_masked`, and `candidate_shape` receive the intended patches. Matched-function and shape-fit restoration passed injected-exception checks. The box replacement is protected by `finally`.
- `_crossfit` fits each parity and measures the other. Each group’s pseudo-windows use that group’s measurement template. An instrumented fixture confirmed the routing and returned `sqrt(4 + 9)` for group variances 4 and 9. Summing them assumes zero cross-group covariance, as the design acknowledges.
- The schedule contains **960 null, 360 alternative, and 60 short-period units**. Fingerprints are checked on both resume and summary, and duplicate or incomplete unit identities prevent a choice.

1. **HIGH: Ordinary unavailable box errors crash summarization.**

   **Evidence:** [_box](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/e2_matched.py:301) can return `[difference, None]` when A0 cannot supply a group variance. The existing smoke contains **12 such box results**. [valid()](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/e2_matched.py:499) calls `float(None)`, raising `TypeError`. Replaying an actual smoke value reproduced this.

   Box availability in that smoke is **26/44 finite difference/error pairs**, although 38/44 results are non-null objects.

   **Exact change required:** Normalize an unavailable error to an unavailable estimator result, retaining its reason. Validate a two-element numeric pair without throwing, require a finite positive error, and keep unavailable curves in availability and unconditional-power denominators. A zero difference with a valid error must remain available.

2. **HIGH: Unit identities are checked, but their contents are not. Undefined power can receive EVALUATED.**

   **Evidence:** [summarize](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/e2_matched.py:472) does not validate metadata against the scheduled identity or require the complete estimator schema. In complete synthetic schedules:

   - Changing every null record’s `shape` to 0 removed half the cell table without blocking a choice.
   - Relabeling alternative records as `short` produced null powers but **EVALUATED**, with `no_candidate_qualifies=true` despite every qualification flag being true.
   - Removing one estimator key raised `KeyError`.

   **Exact change required:** Validate scheduled kind, noise, SNR, period, shape, index, required estimator keys, result types, and numeric fields before aggregation. Validate expected cell counts explicitly. Structural failures or undefined decision statistics must produce **NOT ESTABLISHED**, named reasons, and a null choice.

3. **HIGH: Pooling can hide both severe miscalibration and completely unavailable cells.**

   **Evidence:** [Qualification](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/e2_matched.py:512) uses noise-pooled results alone. In-memory fixtures qualified every estimator and selected `box` when:

   - Individual cells had means **+0.8 and −0.8**, with SD approximately **0.608**, while pooled moments met the tolerances.
   - One required null cell per noise had **0/40 available curves**, while pooled availability was 0.875.

   The promised explicit “qualifies only when pooled” label is also absent.

   **Exact change required:** Make every required null cell constrain recommendation, with frozen minimum availability and descriptive calibration criteria. Undefined required cells must block recommendation. Keep pooled summaries as additional diagnostics and explicitly flag pooled-only agreement. These development checks must remain distinguished from population-equivalence acceptance.

4. **HIGH: The choice rule permits a vacuous recommendation and includes an undeclared candidate.**

   **Evidence:** [Selection](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/e2_matched.py:563) selected **`box` with zero power in every alternative cell**, because its null pulls qualified. The code also allows `built` to win, although the design names it as the baseline and omits it from the candidate tie-break order.

   The implemented tie calculation itself is sensible: it compares each eligible candidate with the global maximum and chooses the simplest within 0.02.

   **Exact change required:** Add a frozen absolute sensitivity requirement before ranking, assessed on unconditional detection in each required alternative cell. Tie it to the registered sensitivity target, explicitly labeling any lower development benchmark as exploratory. If none meets it, recommend none. Exclude `built` from candidate eligibility unless the design explicitly adds retaining the baseline as a possible choice.

5. **HIGH: `_diff_at` does not calculate the as-built matched difference. Its phase controls do not reproduce the full selected null.**

   **Evidence:** [_diff_at](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/e2_matched.py:249) weights events by matched information alone. Production `check_odd_even` uses inverse squared **`max(model_error, empirical_error)`**, drops events without calibrated stratum errors, and uses event metadata. `_diff_at` omits those empirical-error and retention steps.

   Moreover, [_pseudo](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/e2_matched.py:280) fits shifted ephemerides largely on noise, retains the original selected candidate and flattened series, and does not repeat upstream selection. Those controls are not automatically exchangeable with a shape fitted to equal-depth transits.

   **Exact change required:** Either share the production difference calculation across real and pseudo ephemerides, including weights and retention, or explicitly freeze this as a distinct information-weighted estimator. Describe the phase dispersion as a **conditional variance hypothesis**, tested by the equal-depth simulations. Do not claim it repeats every selection step or establishes the rejection-tail model.

6. **HIGH: Moving the decisive periods after the smoke is an outcome-informed amendment. The supplement does not preserve the original question.**

   **Evidence:** The archived smoke manifest specifies **1.5 and 5.0 d**. Availability was inspected before those periods became **3.3 and 7.0 d** in the decisive rule. Availability is itself a qualification endpoint. The remaining [1.5 d supplement](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/e2-design.md:20) covers only one SNR, one shape, and availability, with no alternative-power assessment.

   **Exact change required:** Explicitly record the old freeze, smoke fingerprint, inspected outcomes, amendment, and affected inference.

   **It must be flagged, but need not automatically be undone for exploratory development.** Either restore the original required cells with fresh evaluation seeds, or formally narrow the amended question to the new period cells and carry the original short-period question forward as unresolved. Any recommendation must state that restriction. An availability-only supplement cannot support a general estimator replacement.

7. **HIGH: The processor-hour cap is checked after spending and can be bypassed on resume.**

   **Evidence:** [run()](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/e2_matched.py:417) checks spending after dispatch. A mocked resume already at **3.0 processor-hours dispatched another unit**. A limited 44-unit probe projected only its truncated queue and reported zero remaining units. Failed workers omit elapsed CPU time, and the projection gate allows 1.5 times the frozen cap.

   **Exact change required:** Check spending before dispatch, project against the entire unfinished schedule independently of invocation limits, account for failed-unit CPU time, and size or terminate work against the remaining budget. A capped incomplete run must remain NOT ESTABLISHED. Apply the same budget standard already requested in E3.

8. **MEDIUM: Promised uncertainty and pseudo-ephemeris affordability assessments are missing.**

   **Evidence:** [Cell summaries](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/e2_matched.py:543) lack the promised mean/SD intervals. Availability has no intervals; alternative cells contain counts without the promised uncertainty. Only total unit CPU time is retained, so pseudo-ephemeris cost cannot be assessed separately.

   The approximately 16% error-scatter statement assumes independent Gaussian replicates. Twenty phase placements on one selected curve do not establish those assumptions.

   **Exact change required:** Implement the promised curve-bootstrap intervals, preserving unavailable scheduled curves when estimating availability. Record estimator-specific timing. Freeze a precision/affordability criterion for `pseudo_ephemeris` and assess it with repeated phase sets on a fixed subset. Label 16% as an idealized calculation unless measured assumptions support it.

9. **MEDIUM: Provenance and wording overstate what is established.**

   **Evidence:** [The fingerprint](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/e2_matched.py:50) omits Astropy’s runtime version, although candidate finalization uses Astropy BLS, and does not identify the E1 result supporting the design premise.

   “Every candidate is measured on the production path” also needs qualification: this uses local finalization initialized with the **true period and true duration hint**, rather than the complete production search. Finally, E1’s full arm-D range is approximately **0.969–1.008**; **0.983–1.008** describes its non-white cells.

   **Exact change required:** Include Astropy’s version and the E1 result hash in the manifest. Describe the experiment as conditional on oracle-initialized candidate refinement, with full-search calibration unresolved. Correct or qualify the quoted E1 range, while retaining E1’s overall NOT ESTABLISHED verdict.