## Verdict: WEAKENED

The scope and budget structure now survive. **The acceptance specification still needs corrections before implementation.** These are bounded specification fixes, not requests for additional studies.

No files were modified.

## 1. Round-2 items

| Item | Status | Assessment |
|---|---|---|
| Infrastructure failures cannot become diagnostics | **ADOPTED** | Plan §3 explicitly excludes enforcement, compatibility, authentication and reproduction failures. |
| Twelve-day/week-four trigger cannot start calibration prematurely | **ADOPTED** | Plan §7.3. |
| Agent-days measured consistently | **ADOPTED** | Both agents’ session-hours / 8. |
| Calibration reserve protected against core overruns | **ADOPTED** | Reserve invariant plus 50 processor-hour development limit. |
| Severity policy | **PARTLY** | Table added, but retaining the v0.4 secondary depth-ratio rule contradicts the stated requirement for model-incompatible evidence. |
| Dilution-aware centroid qualification | **ADOPTED** | Missing dilution/WCS information must explicitly produce INCONCLUSIVE. |
| Frozen C1 design supplied | **PARTLY** | Document exists, but generator definitions, truth matching and decision denominators need clarification below. |
| Phase-0.5 limitations | **ADOPTED** | Explicitly documented. |

Nominal allocations remain correct: **23 agent-days including options, leaving one day; 50 development + 100 calibration processor-hours = 150.** The reserve protection is now adequate.

## 2. Required acceptance corrections

Line references below refer to [v0.5-acceptance.md](C:/Projetos/refute/docs/plans/v0.5-acceptance.md).

### A. Sensitivity must match the complete rejection rule

**Lines 56–67:** several formulas test only one component of a compound decision.

- **Aperture depth:** the minimum effect is exactly the ratio boundary. Even with tiny errors, a true effect at that boundary cannot reliably satisfy both the significance and ratio conditions at 95% probability. Current rejection requires both: [battery.py:415](C:/Projetos/refute/src/refute/packs/tess/battery.py:415).
- **Centroid:** likewise, an offset exactly at `min_offset_pixels` cannot give 95% probability of exceeding that same measured-offset boundary. A radial magnitude near zero is also not a Gaussian scalar.
- **Single-event:** `1/sqrt(N) + z_power/SNR <= max_ratio` describes distance from an equal-event reference, not demonstrated power against the declared one-event alternative.
- **Shape:** error ≤ 0.1 does not establish sensitivity to exceeding 0.45.

**Required replacement:** calculate sensitivity against the **full rejection region**, using a declared alternative strictly beyond any effect-size boundary. Use deterministic simulations where the scalar Gaussian model does not apply. For heterogeneous event/sector errors, specify the affected event/sector and use the worst eligible location, or label the sensitivity as averaged over a prespecified distribution.

### B. Close sensitivity bypasses and missing subchecks

**Lines 37–50, 61:** reject malformed sensitivity blocks, missing `detectable`, non-finite values and unregistered categories. A statistical test must not obtain PASS merely by supplying a category.

Require **every applicable subcheck** to qualify before a composite PASS:

- `systematics` needs a distinct background-rise rule, not the SAP/PDCSAP difference rule. Its background statistic and threshold differ: [battery.py:1009](C:/Projetos/refute/src/refute/packs/tess/battery.py:1009).
- `plausibility` needs treatment of its duration branch as well as radius. Both feed its result: [gauntlet.py:289](C:/Projetos/refute/src/refute/packs/tess/gauntlet.py:289).

A detected FAIL may stand despite insufficient sensitivity to other effects.

### C. Remove unsupported fatal escalation

**Lines 127–138 and case 3.2:**

- A secondary depth ratio alone does not establish incompatibility with a planet. **Make significant secondary dips warning-only in v0.5**, while the planetary-occultation model remains deferred. Preserve the old fatal rule solely in the historical compatibility path.
- A residual box below 3 sigma is **non-detection, not evidence that variability explains the signal**. Keep sinusoid failures warning-only unless an accepted joint/model-comparison criterion demonstrates incompatibility with the declared transit.

The existing secondary code uses significance and depth ratio only: [gauntlet.py:123](C:/Projetos/refute/src/refute/packs/tess/gauntlet.py:123). Historical behavior does not scientifically justify retaining that fatal interpretation.

### D. Repair centroid control measurements

**Lines 162–165:** applying `source_offset` at transit-free pseudo-epochs is not a usable systematic estimator as written. It requires a detected positive aperture dip and divides by its depth: [battery.py:232](C:/Projetos/refute/src/refute/packs/tess/battery.py:232), [battery.py:241](C:/Projetos/refute/src/refute/packs/tess/battery.py:241).

**Required specification:**

- Measure pseudo-epoch **centroid shifts**, then propagate them using the actual transit depth; do not divide by pseudo-event depths.
- Exclude real primary/secondary windows and overlapping controls.
- Declare handling when 20 valid controls are unavailable.
- Specify whether the estimated scatter is total measurement noise or an additional systematic component, avoiding double-counting.
- Retain WCS/Jacobian information and covariance through sky-frame conversion. `PixelData` currently stores target pixel coordinates, not WCS: [types.py:171](C:/Projetos/refute/src/refute/packs/tess/types.py:171).

### E. Fix contradictory acceptance cases and sabotage checks

- **Case 1.6(b):** “INCONCLUSIVE in every trial” conflicts with “a detected FAIL stands.” Replace with **“never PASS; INCONCLUSIVE unless a valid failure is detected.”**
- **Sabotage after 1.8:** removing `z_power` need not change case 1.6(a), whose errors already provide ample sensitivity. Add a boundary case where `z_threshold < delta_min/sigma < z_threshold + z_power`, with a non-rejecting observation.
- **Case 2.2:** distinguish one physical dip from six **covered, measured event windows**. If only one window has usable coverage, the specified domain requires INCONCLUSIVE.
- **Cases 2.3, 3.1, 3.2, 4.6 and 5.3:** specify sufficient SNR/errors or statistical rate requirements. Doubling a noisy event, or opposite offsets consistent within large errors, cannot unconditionally require rejection.
- Coexistence case 3.4 should require no unsupported fatal rejection, **not that every other test remain unaffected**.

### F. Label threshold provenance accurately

I found **no evidence of real-data tuning**, but several numbers are currently unsupported rather than declared conventions.

Explicitly label as Refute conventions, with applicability and acceptance requirements:

- Brightening floor 0.1 × depth.
- Sinusoid amplitude floor 0.5 × depth.
- Shape threshold 0.45 and error limit 0.1.
- Chi-square alpha 0.00135.
- Twenty centroid controls, 50% qualification guard, 45/50 simulation rule.
- Pull bands and D1–D5 targets.

LEO-Vetter’s 0.88 single-event threshold applies to **at most ten transits**. Restrict Refute’s domain to 3–10, or explicitly declare and validate the extension beyond ten. Its gap statistic uses **mid-centers**, whereas this document uses windows near edges. SWEET’s published significance threshold does not include Refute’s additional amplitude floor. These are adaptations, not identical published definitions. [Kunimoto et al., §§III.3, III.11–12](https://arxiv.org/html/2509.10619v1)

### G. Finish freezing the C1 generator

**Lines 270–300:** supply deterministic definitions for:

- Sector lengths, spacing, gaps, epochs and stellar trends.
- Transit profile and consistent radius, depth, impact parameter and duration.
- EB2, pixel-source brightness/geometry and artifact amplitudes.
- Whether NR/NW override the general correlated-noise/trend mixture.
- “Expected SNR,” including its noise model.
- V1/V2 amplitude generation without repeatedly searching until a candidate passes.
- Cost-projection procedure used to halve sample sizes, based on development measurements only.

The **2,400-curve arithmetic is correct**. PA’s fixed three sectors must explicitly override the general sector draw.

### H. Make D1–D5 score the intended signals

**Lines 302–320:**

- **PA contains a real planet.** Include PA with the planet families, not “other families, truth: not a planet.”
- Require period-and-epoch identity matching for P/PG/PV/PA. A surviving unrelated noise peak is not a retained planet. Report mismatches and missed injections separately.
- Define every denominator: D2–D3 and D5 currently leave some REFUTED fractions ambiguous; D4’s `n ≥ 20` must apply to its **high-SNR subset**.
- Use the same eligible, identity-matched candidate set for each paired battery comparison.
- Define rule outcomes as **PASS / FAIL / NOT DECIDABLE**, with the latter never satisfying a target. The current blanket “each PASS or FAIL” contradicts the small-sample rule.
- Report D1’s SURVIVED endpoint **and SURVIVED + WEAKENED separately**. Calling only SURVIVED “spurious survival” otherwise makes a warning-only relabeling look like rejection.

These corrections can be applied directly. **Because required changes remain after round 3, record WEAKENED and follow the delegated escalation rule, without opening another scope-review round.**