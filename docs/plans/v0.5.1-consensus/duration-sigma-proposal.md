# Proposal: the measurement of `duration_excess` after A0 revision 2 (round 3)

**Pending the maintainer's decision; no code of this section is written until he accepts it.**
Amendment 4 already approved the diagnostic status (computed and reported, outside the verdict);
this estimator is a separate approval. If accepted, it replaces, in
docs/plans/v0.5.1-acceptance.md, section "The eclipsing-binary route: `duration_excess`", the
`sigma_T` part of "Measurement" and D.1's wording, and the pending-decision paragraph becomes the
record of his decision. The bound, the decision rule, the sensitivity rule and rows D.2 to D.5 keep
their text.

1. **`T`.** The total duration of the trapezoid fitted by `battery_v51._fit_shape` on the
   flattened curve the battery uses (its procedure, bounds and two-start selection unchanged).
2. **`sigma_T`, a phase-placement estimate.** The fitted trapezoid is subtracted from the curve
   (the real events removed) and injected again at the candidate's period with its epoch shifted
   by phase `phi_j`, ten evenly spaced in [0.20, 0.40] and ten in [0.60, 0.80]. Each placement is
   recovered by exactly `_fit_shape`'s procedure, started from a candidate whose epoch is the
   shifted one and whose depth and duration are the fitted ones. `sigma_T` is the sample standard
   deviation of the valid placements' `T`. The 20 placements share one curve and are dependent: 20
   is not an effective independent sample count, and `sigma_T` is not a standard deviation over
   independent recoveries; whether it is calibrated is what D.1 measures.
3. **A valid placement.** The fit `_fit_shape` selects (the lower-cost of its two starts, the same
   selection as for `T`) reports success (the optimizer's flag, which the implementation keeps for
   each start) and has no parameter at a bound; when the selected fit failed, the placement is
   invalid even if the other start succeeded (the selection is never changed by the flag); and
   the number of its injected events whose coverage is at least A0's `min_coverage`
   (in-event cadences over a full event's, counted over all sectors) is at least the battery's
   minimum number of events (`gauntlet` minimum events of the candidate). At least 10 valid
   placements, else INCONCLUSIVE `not_enough_data`. The valid and rejected counts, with the reasons,
   are reported.
4. **The phase band.** The band around phase 0.5 is left out of the placement grid by a fixed
   design choice of this measurement, independent of amendment 5's conditional exclusion of A0's
   pseudo-windows (which concerns another measurement).
5. **No conversion from A0.** No ordering or conversion between A0's per-event depth errors and
   `sigma_T` is assumed.
6. **D.1, explicit:** the pulls `(T - T_true) / sigma_T` of this procedure on 400 circular planets
   per noise model; the calibration is decided **per noise model over all its planets** by A0's
   pull bands (standard deviation of the pulls in [0.9, 1.1], absolute mean pull at most 0.1). The
   breakdown by `secondary_eclipse` status (PASS, FAIL, INCONCLUSIVE) is descriptive only, with its
   group sizes. D.1 uses only finite pulls with `sigma_T > 0`; the usable and unusable planets are
   counted and the reasons reported. **Denominator rule (Claude's choice, for the maintainer to
   confirm):** a noise model is decided only when at least 380 of its 400 planets (95 %) give a
   usable pull, and the calibration then applies to that subset; otherwise D.1 is NOT DECIDABLE for
   that noise model. If D.1 does not pass, or is not decidable, for a noise model, the diagnostic
   stays reported with its error labelled "not validated".
7. **The evidence of amendment 4** (docs/validation/v0.5.1/feasibility/duration_measurement.py)
   was obtained with the unfiltered mechanism; it is preliminary evidence for the mechanism only.
   Before it is cited for the adopted estimator, the development measurement is re-run with this
   validity rule (development data; about 2.3 processor-hours), reporting valid and rejected
   placements.
8. **Outcomes:** D.1 to D.5 are measurement and sensitivity checks of a diagnostic; their outcomes
   never change a battery verdict.
