## Verdict: WEAKENED

Round 2 resolves most of the seven objections and is a credible proposal for the maintainer to decide. **Three details need tightening first:** preserve the maintainer’s decision gate, define how `_fit_shape`’s optimizer status determines validity, and say whether D.1 must pass within each `secondary_eclipse` status.

## Round 1 objections

1. **Dependence among placements, resolved.** The proposal calls `sigma_T` a phase-placement estimate, states the placements share a curve and are dependent, and says 20 is not an effective independent sample count. It assigns calibration to D.1.

2. **Unfiltered development evidence, resolved.** It limits amendment 4’s evidence to preliminary support for the mechanism and requires recalculation under the proposed validity rule, with valid and rejected counts.

3. **Recovery fit must match the estimator, mostly resolved.** It specifies `_fit_shape`’s procedure and bounds, including its two-start selection, and gives recovery starting parameters. But the proposal also uses an optimizer success flag that `_fit_shape` currently discards.

4. **Validity rule, resolved.** It defines coverage per injected event, counts across sectors, specifies the battery minimum-event threshold, and keeps the ten-valid-placement requirement separate.

5. **Relationship to A0 depth errors, resolved.** It states that no ordering or conversion from A0’s per-event depth errors to `sigma_T` is assumed.

6. **Phase-0.5 omission, resolved.** It identifies the omitted band as a fixed duration-grid design choice, separate from amendment 5’s conditional A0 window rule, and calls for reporting D.1 by secondary-eclipse status.

7. **Obsolete decision text, not fully resolved.** The proposal would replace the paragraph containing the explicit maintainer-decision and no-code-until-decision gate. The user’s stated process still requires that gate. Keep the gate in the proposed replacement text.

## Remaining objections

1. **High: retain the maintainer decision gate.**  
   **Evidence:** The acceptance section currently says the proposal goes to the maintainer and that no code is written before the decision ([acceptance section, lines 444–452](C:/Projetos/refute/docs/plans/v0.5.1-acceptance.md:444)). Round 2 says it replaces that pending-decision paragraph ([proposal, lines 1–6](C:/Projetos/refute/.cache/v051/opening/duration-proposal-r2.md:1)).  
   **Exact change required:** Make the replacement text explicitly state that the measurement definition is **pending the maintainer’s decision** and that no code for this section is written until he accepts it. Keep amendment 4’s already-approved diagnostic status distinct from approval of this estimator.

2. **Medium: define optimizer-success validity for the two-start fit.**  
   **Evidence:** `_fit_shape` runs two fits, chooses the lower-cost result, and returns only its parameters; it does not return either fit’s success flag ([`_fit_shape`](C:/Projetos/refute/src/refute/packs/tess/battery_v51.py:235)). The proposal makes optimizer success a validity condition ([proposal, lines 18–25](C:/Projetos/refute/.cache/v051/opening/duration-proposal-r2.md:18)).  
   **Exact change required:** Define validity using the selected lower-cost fit’s success status, and require the implementation to retain that status for each start. State how to handle a lower-cost unsuccessful fit when the other start succeeds. Keep this definition aligned with the same two-start selection used for `T`.

3. **Medium: define D.1’s pass rule when split by secondary status.**  
   **Evidence:** Existing D.1 specifies 400 circular planets per noise model and “A0’s bands” ([acceptance section, line 474](C:/Projetos/refute/docs/plans/v0.5.1-acceptance.md:474)). Round 2 asks to report by noise model **and** secondary status, but does not say whether the calibration gate applies within each status or what happens when a status has too few cases ([proposal, lines 29–32](C:/Projetos/refute/.cache/v051/opening/duration-proposal-r2.md:29)). A0’s bands are pull standard deviation [0.9, 1.1] and absolute mean pull at most 0.1 ([acceptance section, line 91](C:/Projetos/refute/docs/plans/v0.5.1-acceptance.md:91)).  
   **Exact change required:** State whether these bands must pass separately for each status. If so, define a minimum group size and report undersized groups as inconclusive or unvalidated. If the status breakdown is descriptive only, say so and define which D.1 grouping controls calibration.

**All other round 1 concerns appear addressed.** The phase grid, unvalidated-error label, independent A0 error treatment, and separation of diagnostic checks from the battery verdict are explicit in round 2. D.1–D.5 are already described as not changing the verdict ([proposal, lines 38–39](C:/Projetos/refute/.cache/v051/opening/duration-proposal-r2.md:38)).

