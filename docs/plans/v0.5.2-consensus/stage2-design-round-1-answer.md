**The draft is not ready for implementation.** The main blockers are the sizing simulation, the sinusoid gate, and rules that could remove necessary protections without establishing their replacement’s validity.

I reviewed the requested documents and code read-only. I made no edits, launched no experiments, and did not access the excluded path.

**1. Acceptance and sizing: HIGH. Answers (a) and (b).**

**The whole-family reading is the right conservative interpretation:** at least 90% probability of simultaneously certifying every required member of the declared family under a specified correctly calibrated reference model. Per-member power, or the fraction of cells reaching 90%, does not establish that.

However, this is a choice of reference model, not a promise for every distribution inside the tolerances. A population arbitrarily close to an equivalence boundary cannot have the same certification power as one at mean zero and sd one.

The [sizing script](/C:/Projetos/refute/docs/validation/v0.5.2/stage2/sizing.py:97) does not establish the proposed sizes:

- **The formula for `q` is a Gaussian Bonferroni approximation**, `NormalISF(0.033 / (4M))`, rather than a simulated independent maximum. Its protection against dependence requires valid marginal tail approximations. Studentized variance roots need not have those Gaussian tails. The two small-family bootstrap comparisons already exceed the formula, so “slightly optimistic” is not a quantified correction.
- **The family-power calculation multiplies marginal certification probabilities.** Within a run, odd, even, difference, and other statistics share curves. Their certification events are dependent. The product is neither the actual power nor a generally valid lower bound. Preserving joint dependence is central to the resampling method. [Romano and Wolf](https://econ-papers.upf.edu/papers/712.pdf)
- **Kurtosis is insufficient to specify the simulated law.** For non-Gaussian pulls, the script independently generates a normal mean and a moment-matched gamma variance. It omits skewness, mean–variance dependence, random estimated fourth moments, and the tails of the studentized variance root.
- **One pull per curve does not reproduce the per-event estimand.** Actual curves contribute unequal numbers of correlated events. Replacing them with one independent pull changes the sampling law and potentially the weighting.
- **Availability is replaced by its expectation.** The script uses rounded `units × fraction`. It does not simulate joint missingness, branch membership, retention at `G_min`, or degeneracy.
- **The proposed availability guarantee is not simultaneous.** Even if 717 independent run-level delivery events each succeeded with probability 0.999, their joint probability would be about **0.488**. Checking only the “most demanding” member also requires proof that it controls every other member’s count distribution.
- **Monte Carlo uncertainty matters at these extreme marginal powers.** With 200,000 draws, probabilities of failure around a few parts in 100,000 are estimated from very few failures. Multiplying those estimates across thousands of members magnifies that uncertainty.

The script’s own sensitivity results undermine the Gaussian recommendation:

| Expected contributing curves `T` | Gaussian family power | Kurtosis-6 family power |
|---|---:|---:|
| 8,000 | 0.999 | 0.424 |
| 9,000 | 0.9999 | 0.906 |
| 10,000 | 0.999995 | 0.984 |

These remain **toy-model projections**, not validated powers.

**Correction:** simulate the actual joint curve layout, cluster sizes, missingness and retention, using the specified studentized bootstrap. Select sizes on development sizing seeds, then evaluate the selected design on separate development evaluation seeds. Require a one-sided lower confidence bound of at least 0.90 for whole-family certification.

**What should `G_min` be?** No final numerical value is justified yet. It must be a minimum number of **contributing independent curves**, selected jointly with the fixed schedule. For the present Gaussian approximation, the draft’s roughly 7,200–7,600 is only a candidate. The kurtosis-6 sensitivity moves the candidate toward 9,000–10,000. I would include **10,000 as a sizing candidate**, not approve it as the answer. Neither a small bootstrap-stability minimum nor A0’s ten pseudo-windows substitutes for this calculation.

Also retain every required member in the operational permission map. A member omitted from pricing because of the 0.25 floor still blocks permission where applicable.

**Twelve workers are legitimate.** Reducing SMT contention can reduce actual processor time per completed workload. It must be measured, not obtained by dividing the old hours by a speedup factor.

Count cumulative user plus kernel CPU time for the controller and all owned workers, including startup, imports, bootstrap summaries, failed attempts, interrupted shards and retries. Record wall time and throughput separately. Verify physical-core topology rather than assuming even-numbered logical processors identify distinct cores. Benchmark representative final workloads with thread counts controlled.

Finally, the draft proposes probing final code “before fixing `T`,” while guideline 1 requires `T` and `G_min` before the code. Fix the statistical sizes through development simulation first. A final-code cost probe may trigger STOP; it must not quietly reduce the frozen statistical requirement.

**2. Sector selection: HIGH. Answer (c).**

The ranking is **flux-blind conditional on the ephemeris and cadence set**. That qualification matters: the ephemeris comes from the search, and cadence availability can become flux-dependent through clipping.

The proposal also ranks sectors using in-event coverage, although an event’s measurement requires usable baseline bands. The selected four could therefore contain fewer usable measurements than the ranking suggests.

**Correction:**

- Define eligibility from frozen timestamps and permitted quality information, including the baseline geometry.
- Freeze and record the selected sector IDs before event measurements or empirical-error availability are examined.
- Do not replace a selected sector because its statistic or error later becomes unavailable.
- Determine the operational sector count from the sectors that actually contribute measured events.

**Yes, selection changes what acceptance certifies.** The existing grid tests directly generated two-, three-, and four-sector constructions. It does not automatically certify four sectors selected from a larger candidate set, with an ephemeris estimated using all sectors.

Validate that selection procedure on development constructions with five or more sectors, including unequal noise, gaps and changing event coverage. This tests the selector without extending the operational sector-count grid. Report the requested real-development effects, including resulting INCONCLUSIVE fractions, not just events lost.

**3. A0 version 4 and mask symmetry: HIGH.**

Arm D supports investigating this correction. Its results do not establish the full production procedure.

The [E1 reference comparison](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/e1_mask.py:175) compares window values, per-stratum error estimates and availability. It does not directly establish the cross-window correlations and group covariance used by A0. Interleaved combs can alter those correlations even when marginal errors agree.

There is also a missing integration specification. The aperture and SAP difference paths use their own additive preprocessing in [ `a0_depth` ](/C:/Projetos/refute/src/refute/packs/tess/battery_v51_diff.py:67). Applying the ordinary flux-detrending correction alone would leave those paths untreated.

**Correction:** specify the mask-aware preprocessing operation for every decisive A0 consumer. Validate comb versus individual-window reference for marginal errors, lag correlations, final group variances, availability and decisions across the required constructions.

Freeze the reference sample and numerical tolerances before acceptance. Its failure must block affected permissions.

Using the box for `odd_even` correctly implements guideline 2. E2 still supplies no acceptance certificate for that estimator.

**4. Sabotages and simplifications: HIGH. Answer (d).**

The “stays if” rule is too mechanical.

An sd of **1.11** already violates the protected bound. Failure to reach **1.15** does not establish that the protection is unnecessary. Likewise, an indistinguishable contrast can mean insufficient power, an ineffective sabotage, or an insensitive regime.

The 0.05 distance is defensible as a **planned sabotage effect for power calculations**. It is unsafe as the sole deletion threshold.

**Correction:** require an accepted baseline, a correctly implemented paired sabotage, uncertainty on its effect, and the planned power. Simplification is justified only when the replacement itself passes the required acceptance and preserves relevant availability and sensitivity. Examine mean bias and availability as well as sd.

Specific problems:

- **Pooling sectors:** equal pooled calibration can conceal errors in unequal-noise sectors and change inverse-variance weighting. Validate the replacement across the required heterogeneity patterns.
- **Removing `n_eff`:** ten dependent windows are not equivalent to ten effective observations. Validate both the variance correction and the availability rule being replaced.
- **Stronger `rho_zero` regimes:** appropriate, but longer noise also challenges the fixed lag cutoff. Correlations beyond `MAX_LAG = 5` cannot remain merely descriptive if they materially affect a certified group error. Include both positive group weights and signed odd/even contrasts.

**Always excluding phase-0.5 windows is a plausible simplification, not automatically safe.**

There is a concrete availability cliff. The current overlap rule excludes pseudo-window centres within `2h` of each primary and half-phase centre. Those exclusions cover the whole period when:

`P <= 8h`.

With the default baseline geometry, `h = 2 × duration`. At duration 0.10 d, **periods at or below 1.6 d have no eligible pseudo-window centres**, even before gaps.

Moreover, excluding secondary windows from the variance sample does not necessarily remove their influence on detrending.

Adopt unconditional exclusion only with acceptance and development sensitivity measurements covering this loss. Removing the conditional branch does not remove the need for secondary-contaminated and no-secondary constructions, including the near-threshold secondary depths. The quoted 61% cost saving must be recomputed.

**5. Sinusoid gate: HIGH. Answer (e).**

Returning INCONCLUSIVE for ambiguity and retaining it in denominators legitimately implements guideline 3. **The proposed `S_TOL = 0.01` justification does not establish the 0.0027 limit.**

Multiplying `0.2 × 0.01` assumes a suitable frequency-offset density and conditional rejection behavior. E3 establishes neither near zero. It also uses true separation, while the proposed gate uses an estimated, selected frequency.

A direct counterexample is a permitted stellar trend exactly at a tested harmonic. As its signal-to-noise increases, `s_hat` approaches zero and the gate admits it increasingly reliably. Narrowing a fixed tolerance cannot resolve that observational ambiguity.

Further problems:

- Define the residual construction precisely. Subtracting the tested sinusoid before searching for its frequency removes the signal being checked. Searching a frequency against residuals from a fixed-frequency fit can also distort the objective.
- E3 uses the injected candidate period. It does not test the uncertainty, bias and aliases of a sinusoid recovered as a box.
- Widening the gate for period error would change its false-alarm behavior. The relevant uncertainty is joint uncertainty in `f_hat − 1/(factor × P_hat)`, including their same-data dependence.
- Existing amplitude-only sensitivity calculations would overstate the power of the gated decision.

**Better rule:** define an explicit composite planet-plus-stellar-variability null, allowing nuisance frequencies near the tested harmonics. Jointly refit nuisance terms when profiling frequency. Permit FAIL only through a rejection rule calibrated against the allowed null configurations; return INCONCLUSIVE where null and alternative cannot be distinguished.

If those models overlap exactly, there is no uniformly powerful discriminator there. Guideline 3 allows acknowledging that limitation.

A frequency-consistency gate could remain an empirical candidate, but its cutoff must survive separate development evaluation across separation, amplitude, phase, gaps, correlated noise and search-recovered period errors. Demonstrate the **complete decision’s** false-alarm bound with uncertainty. E3’s existing 150 curves per cell cannot establish a 0.0027 upper limit even with zero failures.

Measure D1’s two conditions separately for V1 and V2, with their paired v0.4 comparator. Keep the approved 0.10 margins and report the paired uncertainty.

**6. T3b: MEDIUM, with a HIGH identity requirement. Answer (f).**

**Qualified yes:** the amendment preserves the approved catalog-defined class if it means a TOI FP whose target is independently catalogued as an eclipsing-binary candidate. It does not establish that every member is a verified binary, that the binary caused the TOI signal, or that the amended distribution equals the old TESS-EB frame.

Gaia’s table contains candidates selected through automated classification and subsequent EB processing. Its evidential status differs from T10K’s vetted sample. Report that distinction. [Gaia catalogue paper](https://doi.org/10.1051/0004-6361/202245330), [T10K paper](https://arxiv.org/abs/2506.05631)

**TESS-EB → T10K → Gaia is acceptable for the display label only.** Retain all memberships, identifiers, periods and conflicts. Precedence must not silently resolve scientific disagreement or change eligibility.

“By TIC” also needs an actual Gaia identity rule. A nearby Gaia EB is insufficient. Freeze the TIC-to-Gaia association, release mapping and ambiguity handling. The existing position-only selection helper does not establish that association.

**I recommend catalog-to-TOI period consistency for T10K and Gaia**, fixed before drawing targets. Define the proposed 1% tolerance and allowed half/double aliases mathematically. Prefer a consistent rule across all three catalogs; otherwise document the asymmetry and its sampling-frame consequences.

Keep this separate from the existing search-output-to-TOI identity check. Matching the recovered TOI signal does not establish that it is the catalogued binary signal. Missing or conflicting periods must follow a frozen rule, with no favorable post-result catalogue choice.

**7. Driver and resume: HIGH. Answer (g).**

**A shard can be an acceptable unit.** It needs fixed membership, a bounded size, stable curve identifiers and seeds independent of workers and execution order. It must not become a large container that defeats stopping and checkpoint requirements.

A content hash establishes integrity, not compatibility. Skip only after validating the shard against the expected schedule and fingerprints of code, environment, plan, inputs, seed namespace and result schema.

The proposed resume test is necessary but insufficient:

- Interrupt during computation, temporary-file writing, and between result publication and manifest update.
- Exercise missing, truncated, corrupt, duplicated and stale shards.
- Resume with a different permitted worker count.
- Verify exact scientific record membership and canonical result bytes.
- Include error and unavailable outcomes in the comparison.
- Account for discarded and repeated work.

**Separate scientific bytes from operational metadata.** Current records contain `cpu_seconds`; timing and PID fields naturally differ between executions. Comparing a combined artifact byte-for-byte would fail for legitimate reasons.

The cap wording also fails guideline 8: **stop launching units at the cap**, not merely new batches. Cancel queued, unstarted shards and prevent dispatch from an already-created batch. The watchdog must measure cumulative live consumption, including work without committed results, and terminate only owned processes at the approved excess threshold.

Finally, a predicted 30-minute batch is not a bounded batch. Define the wall-time guard and interruption behavior.

**8. Caps: HIGH.**

Section 8 provides a formula and hard maxima, but no concrete allocation. It is not yet an enforceable budget.

**Correction:** produce a numeric worksheet covering development probes, sizing, known-answer validation, all acceptances, references, sabotages, remaining work packages, calibration, reviews and storage. Explicitly price the nested validation workload.

Distinguish the 30% planning allowance, the per-section 1.5-times rule and the 10% experiment overshoot termination threshold. State their bases and which limit binds first. None overrides the global hard maxima.

Count previous attempts and resume overhead in cumulative ledgers. Define token and agent-day accounting, and keep calibration separate from development and acceptance. A projection exceeding a hard maximum triggers STOP before that workload is launched.

**9. Sequence and mandatory stops: HIGH.**

The sequence currently puts implementation before unresolved statistical decisions and places the T3b inventory late.

**Correction:** finalize the family, selector, simplification criteria, sinusoid rule, sizing procedure and numeric budgets first. Complete the T3b inventory before protocol finalization and any draw.

Then implement isolated version-4 paths, prove preprocessing parity and driver recovery, validate the inference machinery, and freeze the complete code and acceptance specification before acceptance runs. Version-3 behavior needs explicit compatibility evidence because shared A0 and pipeline imports can otherwise change it.

Record design changes prompted by development results. After freeze, failures follow the existing bounded revision and rerun rules. Carry forward the CI requirement, all outstanding acceptances and the protocol stop explicitly.

VERDICT: REFUTED