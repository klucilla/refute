## Verdict: **WEAKENED**

All three round 2 objections are resolved in the round 3 proposal. One calibration detail still needs to be fixed before the maintainer decides.

## Round 2 objections

1. **Maintainer decision gate, resolved.** The proposal states at the top that the estimator is pending the maintainer’s decision and that no code for this section will be written before acceptance. It also distinguishes that decision from amendment 4’s already-approved diagnostic status ([proposal, lines 3–8](</C:/Projetos/refute/.cache/v051/opening/duration-proposal-r2.md:3>)).

2. **Two-start fit validity, resolved.** Validity follows the lower-cost fit selected for `T`; its success flag is required, and a successful alternate start does not override a failed selected fit ([proposal, lines 21–29](</C:/Projetos/refute/.cache/v051/opening/duration-proposal-r2.md:21>)).

3. **D.1 by secondary status, resolved.** Calibration is decided per noise model over all its planets using A0’s bands. The `secondary_eclipse` breakdown is descriptive only and includes group sizes ([proposal, lines 35–40](</C:/Projetos/refute/.cache/v051/opening/duration-proposal-r2.md:35>)).

## Remaining objection

1. **Medium: define D.1’s usable pull count and handling of undefined pulls.**  
   **Evidence:** D.1 calls for pulls on 400 planets per noise model, while the proposal makes `sigma_T` unavailable when fewer than 10 placements are valid. It does not say whether a planet with no valid `sigma_T` is excluded from the pull bands, makes D.1 inconclusive, or is handled some other way. A zero `sigma_T` would also make the pull undefined. Silently calibrating only the remaining planets could produce a survivor-biased result.  
   **Exact change required:** State that D.1 uses only finite pulls with `sigma_T > 0`, report the usable and unusable planet counts and reasons, and define the consequence for the per-noise-model decision. For example, require all 400 pulls to be usable, otherwise mark D.1 inconclusive for that noise model; alternatively, set a minimum usable count in advance and make clear that the calibration applies to that subset.

I made no changes and ran nothing. The proposal is ready for the maintainer once this D.1 denominator rule is explicit.

