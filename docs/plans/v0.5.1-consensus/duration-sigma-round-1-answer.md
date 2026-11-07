## Verdict: WEAKENED

The proposal is a plausible replacement for the deleted shifted-ephemeris mechanism, and its fixed phases match the development measurement’s phase pattern. But the 20 values are not independent recovery draws, and the development evidence did not apply the proposed validity rules. The proposal needs those limits stated and calibrated before the section can be adopted.

## Numbered objections

1. **High: the 20 recoveries are dependent, not 20 independent error draws.**  
   **Evidence:** All fits use the same flattened curve and the same residuals after adding back one fitted event model. The phase placements are fixed, and their spacing is only \(0.0222P\) within each band. A0 revision 2 explicitly measures and models dependence between its pseudo-event windows; the proposed duration estimate has no corresponding treatment. The development script likewise uses one shared curve for all 20 recoveries ([`duration_measurement.py`, recovery loop](C:/Projetos/refute/docs/validation/v0.5.1/feasibility/duration_measurement.py:112)).  
   **Exact change required:** Describe `sigma_T` as a phase-placement estimate, not a standard deviation over independent recoveries. Require D.1 to validate its pull calibration across the stated noise strata using the actual 20-placement procedure. Report phase coverage and recovery dependence; do not treat 20 as an effective independent sample count. If D.1 does not pass, keep the result diagnostic and label the error unvalidated.

2. **High: the cited development evidence did not use the proposed validity rule.**  
   **Evidence:** `measure` appends every fit result and takes their sample standard deviation. It does not check fit convergence, reject bound-limited fits, require event coverage, or require ten valid recoveries ([`duration_measurement.py`](C:/Projetos/refute/docs/validation/v0.5.1/feasibility/duration_measurement.py:99)). Thus amendment 4’s sensitivity figures support the earlier, unfiltered measurement, not the proposed one. Filtering may change both `sigma_T` and detectability.  
   **Exact change required:** State that the amendment 4 figures are preliminary evidence for the mechanism only. Recalculate the development measurement with the proposed validity rule before citing it as evidence for the adopted estimator, and report valid and rejected recovery counts and reasons.

3. **Medium: the fit used for recovery must match the battery estimator.**  
   **Evidence:** `_fit_shape` uses two ingress-fraction starts and selects the lower-cost fit ([`battery_v51.py`](C:/Projetos/refute/src/refute/packs/tess/battery_v51.py:235)). The proposal says recovery fits start from injected values. That can change the optimizer’s convergence and fit selection, so it may measure a different estimator’s error.  
   **Exact change required:** Specify that each recovery uses the same fitting procedure, bounds, and multi-start selection as `_fit_shape`. Define which injected parameters initialize the fit, and make that choice part of the D.1 calibration.

4. **Medium: the validity rule needs an operational definition.**  
   **Evidence:** A0’s `min_coverage` is a per-event coverage threshold, while its minimum usable sample is separately expressed through `n_eff >= 10` for pseudo-window measurements ([acceptance plan, A0](C:/Projetos/refute/docs/plans/v0.5.1-acceptance.md:100)). “The injected events keep at least the minimum coverage of A0 for the battery’s minimum number of events” does not say how event counts are computed across sectors or whether every injected event must pass.  
   **Exact change required:** Define, per phase, the number of injected events that meet `min_coverage`, the sector/count rule, and the battery minimum-event threshold being applied. Keep the ten-valid-recovery minimum as a separate rule. If fewer than ten qualify, return `INCONCLUSIVE not_enough_data`, as proposed.

5. **Medium: A0’s per-event depth errors do not establish the size of `sigma_T`.**  
   **Evidence:** A0 calibrates depth measurements with matched pseudo-events and coverage strata. `duration_excess` estimates the total duration from a joint trapezoid fit. These are different estimators and parameters. The A0 errors therefore do not show that `sigma_T` is too high or too low; its direction of bias cannot be inferred from them. D.1’s pull check is the relevant validation.  
   **Exact change required:** State that there is no assumed ordering or conversion between A0’s per-event depth errors and `sigma_T`. Define D.1 explicitly as pulls of fitted `T` using this `sigma_T`, with the A0 pull bands applied per noise model, and report whether those bands pass.

6. **Low: the phase-0.5 omission is separate from amendment 5’s conditional A0 rule.**  
   **Evidence:** The proposed phase grid omits the interval around 0.5 in all cases. Amendment 5 makes exclusion of A0 pseudo-windows touching phase 0.5 conditional on `secondary_eclipse` detecting a secondary ([acceptance plan, phase-0.5 rule](C:/Projetos/refute/docs/plans/v0.5.1-acceptance.md:104); [plan amendment 5](C:/Projetos/refute/docs/plans/v0.5.1-plan.md:454)). The two rules concern different measurements, so this is not inherently inconsistent. But the proposal should not imply that its unconditional phase omission inherits A0’s rule.  
   **Exact change required:** Label the omitted phase band as a separate, fixed design choice for the duration injection grid. Include its effect in D.1 calibration, including cases where `secondary_eclipse` returns `FAIL`, `PASS`, or `INCONCLUSIVE`.

7. **Low: the section still contains obsolete decision-status text.**  
   **Evidence:** The section says the definition is pending, sends the proposal for a maintainer decision, and forbids code before that decision ([acceptance plan, `duration_excess`](C:/Projetos/refute/docs/plans/v0.5.1-acceptance.md:446)). Amendment 4 already approved the diagnostic status and recorded that D1 has no built route this round ([plan amendment 4](C:/Projetos/refute/docs/plans/v0.5.1-plan.md:429)).  
   **Exact change required:** Replace the stale pending-decision paragraph with the adopted measurement definition and retain the amendment 4 boundary: computed and reported as a diagnostic, outside the verdict. Keep D.1 to D.5 as measurement and sensitivity checks, and make clear that their outcomes do not alter the battery verdict.

The proposed phases themselves are reproducible and deliberately avoid the candidate’s phase-0 and phase-0.5 regions. I find no general basis to say this must overstate or understate `sigma_T`; the unresolved issue is whether the procedure is calibrated for the duration fit it will actually use.

