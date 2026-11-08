## Verdict: WEAKENED, round 1 of at most 3

**The four-arm implementation survives inspection. The reference gate and reporting need correction before the full run.** These are fixable defects, not evidence against the mask hypothesis.

Read-only review completed. No files changed, no E1 units executed, and the prohibited directory was never accessed. I confirmed the existing smoke contains 44 records and zero recorded errors. That does not establish scientific correctness.

## What survived

- **Arms and dispatch:** A/D measure real events on `flat_a`; B/C use `flat_b`. C’s pseudo-series mask the comb without real masks; D’s add the real mask. The saved original `box_measure` prevents recursive dispatch. The replacement affects pseudo-measurements, while `per_event_depths` receives each arm’s own series. See [arm construction](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/e1_mask.py:127) and [measurement path](/C:/Projetos/refute/docs/validation/v0.5.1/acceptance/a0.py:180).
- **Grids and widths:** A/D use `flat_a`’s sector origins; B/C use `flat_b`’s. Grid spacing is 0.40 d, measurement half-span is 0.20 d, and mask half-width is 0.10 d.
- **`rho`:** The implementation computes the declared event-weighted `sqrt(sample Var(d) / mean(e²))`. Resampling whole curves preserves dependence among events within each retained curve. This is a variance-agreement diagnostic, distinct from pull standard deviation.
- **Numerical rule:** The six correlated-noise D bounds and both white D−A bounds are coded exactly as written, conditional on `comb_established`.

## Numbered objections

### 1. High: the reference gate checks the wrong “empirical error”

**Evidence:** [_reference](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/e1_mask.py:204) stores ordinary standard deviations pooled across sectors. The [gate](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/e1_mask.py:313) compares those SDs. A0 actually uses a **sector-and-stratum variance with a dependence correction and an `n_eff ≥ 10` availability condition**, through [stratum_error](/C:/Projetos/refute/src/refute/packs/tess/a0.py:188).

Equal ordinary SDs do not imply equal empirical errors. For example, with 100 windows, changing `n_eff` from 100 to 10 changes the correction factor from 1 to approximately 1.049, already beyond the frozen 2% tolerance. Crossing below 10 removes the error entirely.

The reference also silently excludes windows unavailable in either construction, hiding availability disagreements.

**Exact change required:** Build reference and comb `Window` collections with their sector, segment, index, coverage and stratum. Compare actual `a0.stratum_error` outputs per sector/stratum, including availability disagreements. Apply the frozen 2% gate to those errors. Freeze the aggregation explicitly, including whether the 10% RMS criterion is pooled or averaged per curve.

### 2. High: comb validation does not cover the constructions receiving certification

**Evidence:** The [reference branch](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/e1_mask.py:161) checks only **D/full**, for white, correlated and long noise. Its result certifies C and D, both coverage kinds, including `correlated_trend`.

**J = 4 is reasonable for the local fits.** With retained knots spaced by 0.1 d, local influence extends approximately `0.10 + 0.50 + 0.10 = 0.70 d` from the mask centre. Comb centres are 1.6 d apart, providing adequate separation for the target’s ±0.20 d measurement span.

However, [sector-wide clipping](/C:/Projetos/refute/src/refute/packs/tess/detrend.py:127) uses a scale computed from the arm’s unmasked points. That creates nonlocal coupling which this spacing argument cannot eliminate.

**Exact change required:** Freeze a bounded reference allocation covering C/D, full/partial and all four noises, and gate each construction separately. If the cap prevents that coverage, mark the uncovered constructions **not established**. Clarify that J establishes local separation, while empirical reference checks must establish equivalence of the complete procedure.

### 3. High: incomplete runs can receive a positive decision

**Evidence:** [summarize](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/e1_mask.py:267) drops error records without requiring schedule completion. `comb_established` checks only reference groups that happen to exist.

An isolated, in-memory check of the actual summarizer returned both booleans `true` with **8/2,400 synthetic units and one white reference curve**, with correlated and long references absent. No experiment units or file writes were involved.

**Exact change required:** Before issuing a decision, require unique records matching the complete schedule, all 300 successful units per noise/kind, and every required reference allocation. Validate finite inputs and positive denominators. Missing units, errors or failed reference establishment must yield **NOT ESTABLISHED**, with reasons. Also label C/D explicitly as unestablished when their reference gate fails.

### 4. Medium: the required paired diagnostic decomposition is absent

**Evidence:** [scope item (b)](/C:/Projetos/refute/docs/plans/v0.5.2-scope-proposal.md:132) requires changes in numerator variance, estimated variance, bias and availability, **with uncertainties on paired curves**. The [summary](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/e1_mask.py:242) provides marginal `rho` intervals and point summaries instead. Each arm consumes separate bootstrap draws; curves without retained events disappear.

This leaves a change in retention able to resemble a change in variance calibration.

**Exact change required:** Report `Var(d)`, `mean(e²)`, depth bias, availability and their paired arm contrasts with curve-bootstrap intervals. Resample the same scheduled curve IDs across arms, preserving empty outcomes. Store event identities and report retention differences, plus a common-event comparison when retention differs. State the event weighting explicitly.

### 5. Medium: resumability does not preserve the frozen experiment’s identity

**Evidence:** [run](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/e1_mask.py:219) resumes solely by `noise:kind:i`. Existing records contain no design, code or configuration fingerprint. After a review correction, those smoke records could silently coexist with revised results.

**Exact change required:** Freeze a manifest covering the design, experiment script, imported measurement/generator code, resolved plan, constants and environment versions. Associate records with its fingerprint and reject mismatches. Use a separate output namespace for a revised freeze, retaining the original smoke separately.

## Decision-rule assessment

**Keep the numerical thresholds as a stage-1 descriptive rule.** Their conjunction matches the frozen question, and the crossover need not become an additional mandatory pattern.

Describe a positive outcome as **“the prespecified development pattern was observed.”** The point-estimate rule, whose intervals do not affect the decision, does not establish population equivalence, calibrated pulls or a unique causal mechanism. Fix objections 1–5 before treating its output as the completed E1 diagnostic.

