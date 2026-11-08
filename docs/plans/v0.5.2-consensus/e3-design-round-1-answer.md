**Verdict: WEAKENED. Round 1 of at most 3.** The constructions and arm wiring largely match the design, but the reading rules and evaluator can produce misleading recommendations. Resolve the high-severity objections before running E3.

The review was read-only. I did not run E3, write files, or access the prohibited directory. Verification included static inspection, deterministic frequency arithmetic, and synthetic, in-memory checks of the summarizer.

What survives:

- `_planet_curve` supplies the specified planet and noise constructions. The schedule contains **600 planets and 200 alternatives**, each shared across all three arms.
- `extra6` changes the parameter actually consumed by the prewhitening loop. `narrow` patches the function actually called, halves its width, and restores it in `finally`. It narrows exclusions around **both tested and previously selected extra frequencies**.
- The frequency formula correctly includes P/2, P and 2P. `trend["amplitude"] / cand.depth` correctly expresses the injected trend’s semi-amplitude relative to the declared depth.
- Duplicate, missing and unexpected unit identities, and recorded worker errors, prevent an established decision.

1. **HIGH: “Detection” can count the wrong harmonic and misses the boundary affected by `narrow`.**

   **Evidence:** The alternative injects only an exact-P sinusoid of amplitude `2 × depth`, while the summary counts **any raw FAIL** as its detection. A trend flag at 2P therefore counts even when the injected P signal was missed. This differs from WP3b row 3.8(a), which requires **Q itself flagged**. See [alternative construction](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/e3_sinusoid.py:93), [detection counter](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/e3_sinusoid.py:235), and [WP3b requirement](/C:/Projetos/refute/docs/validation/v0.5.1/acceptance/wp3b-design.md:144).

   Exact P also remains inside both exclusion windows. It does not test whether `narrow` absorbs variability in the newly available band, `0.5 < |Δf|T_span < 1`, which the existing exclusion deliberately protects.

   **Required change:** Record the injected target Q and count `Q in flagged`. Cover exact Q at P/2, P and 2P, plus a frozen near-harmonic control inside that changed band, for example `|Δf|T_span = 0.75`. Keep these supplementary alternatives separate from the original planet population. Report sensitivity at the registered **one-depth** alternative separately from recovery of the injected **two-depth** signal.

2. **HIGH: The promotion rule permits vacuous detection preservation and ignores lost availability.**

   **Evidence:** [The rule](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/e3_sinusoid.py:248) compares separate Wilson lower bounds, with no absolute detection requirement. In an in-memory fixture with a complete schedule and **zero detections in every arm**, both variants were declared worth carrying forward. The same happened when every status was INCONCLUSIVE.

   The code records final status and detectable fraction, but neither constrains promotion. Comparing two marginal lower bounds is also not a confidence bound for the paired detection difference.

   **Required change:** Require an adequate baseline before judging preservation. Freeze an absolute detection benchmark tied to the stated 0.95 target, and assess non-regression using a **paired difference** on the same curves with the 0.05 margin. Require the SNR-20 all-applicable-harmonics detectable fraction to meet its stated benchmark. Tabulate raw and final PASS/FAIL/INCONCLUSIVE separately, retaining all scheduled curves in denominators. INCONCLUSIVE must never count as evidence that a nuisance change solved the problem.

3. **HIGH: The 5% threshold is not the existing false-failure limit, and pooling hides required cells.**

   **Evidence:** The design says “lowers the failure rate to the limit,” then substitutes upper Wilson ≤0.05. The existing limit is **0.0027**. Even zero failures among all 600 planets gives a Wilson upper bound of approximately **0.00636**; among 150, approximately **0.02497**. This experiment cannot certify the original limit using that criterion.

   [The summary](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/e3_sinusoid.py:220) pools SNRs, and its decisive separated and detection statistics also pool noise models. The original requirements apply per SNR/noise cell. The rule does not even require improvement over `built` on the separated subset.

   **Required change:** Label 0.05 explicitly as an **exploratory screening threshold**, with the 0.0027 requirement unresolved. Produce the map and comparisons per SNR/noise cell, and detection per noise/target-harmonic cell. Require an actual paired reduction relative to `built` before calling it an improvement. Preserve unconditional results beside every conditional result; passing the separated subset cannot establish unchanged-population acceptance.

4. **HIGH: The concentration rule assigns evidence for another cause to “unseparated trends.”**

   **Evidence:** [The frozen rule](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/e3-design.md:30) and its implementation count

   `s < 1 OR amplitude_over_depth < 0.5`.

   Thus, if every failure had `s ≥ 1` and a subthreshold injected trend, the output would still claim failures were concentrated at unseparated trends. The design itself says those subthreshold cases have another cause.

   **Required change:** Define the concentration fraction using **only `s < 1`**. Report subthreshold-trend failures separately, cross-tabulated with separation. Treat a low injected amplitude as an attribution diagnostic, not proof about the fitted harmonic: noise and projection through the selected joint model still affect its fitted amplitude.

5. **HIGH: The fingerprint guarantee is not enforced by `summarize`.**

   **Evidence:** [Resume checks fingerprints](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/e3_sinusoid.py:155), but [summarization does not](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/e3_sinusoid.py:191). A complete synthetic record set containing exclusively foreign fingerprints was reported as EVALUATED. E1 explicitly performs this check.

   E3’s manifest also omits the resolved-plan identity promised by “As E1,” and records neither Astropy nor SciPy runtime versions.

   **Required change:** Validate every record’s fingerprint during summarization, before aggregation. Include the resolved plan and relevant runtime versions in the manifest. Validate expected arms and record metadata against each scheduled identity. Any mismatch must yield NOT ESTABLISHED, with recommendation fields null.

6. **HIGH: Undefined decision statistics do not trigger NOT ESTABLISHED.**

   **Evidence:** `wilson(…, 0)` returns null, but [the decision logic](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/e3_sinusoid.py:250) converts an empty separated stratum into `worth=False` while retaining EVALUATED. Non-finite separations silently fail every bin comparison. Both behaviours were reproduced in memory. Zero baseline failures similarly leaves concentration undefined without an explicit reason.

   **Required change:** Validate finite separation and amplitude ratio, positive finite depth, and valid fit inputs. Keep undefined quantities null. An undefined statistic required by a decision must make that decision NOT ESTABLISHED, naming the affected arm/cell. Empty descriptive bins may remain null without invalidating unrelated decisions. With zero baseline failures, explicitly state that concentration is undefined because there are no failures to classify.

7. **MEDIUM: The map’s resolution and retained diagnostics are insufficient for its causal interpretation.**

   **Evidence:** E3 uses the full-curve span, whereas [the test computes its width after transit masking](/C:/Projetos/refute/src/refute/packs/tess/battery_v51.py:127). For the full grid, approximately:

   - `T_span = 54.3986 d`, nominal width `1/T_span = 0.0183828 d⁻¹`.
   - Lomb–Scargle grid spacing is `0.2/T_span = 0.00367656 d⁻¹`.
   - Tested frequencies are `0.606061`, `0.303030`, `0.151515 d⁻¹`.

   Trend frequencies range from 0.1 to 0.333333 d⁻¹, so **P/2 is never the nearest harmonic**. The minimum separation is useful, but cannot explain which harmonic actually failed. Moreover, [unit records discard `fits`](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/e3_sinusoid.py:112), despite the design promising fitted amplitudes.

   **Required change:** Compute separation from the test’s exact retained cadences. Store per-harmonic separations, the nearest harmonic, fitted amplitudes/errors/significances, and sensitivity blocks. Describe `s ≥ 1` as a nominal separation category, not established identifiability. For attribution, project the known noise-free trend through the trial’s selected joint design, following WP3b row 3.7’s precedent.

8. **MEDIUM: The frozen probe and cost cap lack an executable gate.**

   **Evidence:** [The design](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/e3-design.md:41) requires a probe and at most 1.5 processor-hours. `run()` defaults to submitting the entire schedule, without projection or cap enforcement. A short prefix contains planets only, excluding alternative workloads.

   **Required change:** Freeze a representative probe covering both cases, both noise models and both planetary SNRs. Record projected remaining cost before full submission, and enforce the remaining CPU budget in bounded batches. An incomplete capped run must retain NOT ESTABLISHED status.

These are repairable design and evaluator defects. The current frozen version does **not** support a reliable recommendation about preserving detection while resolving the stellar-trend failures.