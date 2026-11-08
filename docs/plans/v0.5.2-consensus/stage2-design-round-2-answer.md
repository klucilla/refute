**Revision 2 resolves several round-1 objections, but still has HIGH blockers.** The main ones are the fixed-`q` evaluation, the residual-box sinusoid rule, CPU accounting across interruptions, and the ordering of sizing versus changes to the calibrated procedure.

I inspected the files read-only. I did not execute the tests or experiments, edit files, or access the excluded path.

**1. Plasmode and sizing evaluation: HIGH. Answers (a) and (b).**

**The plasmode is a sound conditional reference model**, with a narrower interpretation than “the distribution of every correctly calibrated version-4 estimator.”

Standardizing each member gives its empirical distribution mean zero and variance one. Whole-curve resampling preserves shared observations, event multiplicities, dependence and missingness. That is a substantial improvement over the previous simulation.

Two qualifications remain:

- Separate member standardizations need not describe a physically realizable light curve with mutually consistent odd, even and difference measurements. It is a reference distribution for the inference machinery.
- Thousands of resampled curves do not establish the real population’s tail law from a few hundred source curves. Version-3 shapes remain an uncertain proxy for version 4.

**Keep the 8.5-sigma observation.** Its repetition does not distort the declared empirical model. At `T = 10,000`, that component draws roughly 19,022 source curves, producing about 14,239 contributions to this member. Approximately 27 repetitions preserve the original frequency, one in 524 contributing curves.

That observation contributes about **13.7% of the member’s empirical second moment**. Removing or downweighting it because it limits power would change the reference model favorably after seeing the result.

**Correction:** retain it, verify its provenance and computation, and report sensitivity to uncertainty in the tail frequency and magnitude. If an independently established defect explains it, correct that defect and rebuild the reference through a recorded development revision. Do not selectively discard the observation.

The evaluation revision has a legitimate part and an unsupported part:

- **Legitimate:** increasing Monte Carlo precision through an explicitly recorded prospective development amendment, using new seeds, a fixed candidate order and multiplicity-adjusted bounds. The original failed assessment remains failed.
- **Unsupported:** replacing the actual random critical value with the largest of 80 observed values and calling that conservative without qualification.

Certification is monotone in `q`, but that establishes conservatism only on datasets whose actual critical value is at most 4.63. **An observed maximum is not an upper bound on future critical values.** The 80 observations also come from two sizes, so they do not establish a uniform bound at 11,000 and 12,000.

**Correction:** preferably evaluate the actual procedure, including its own bootstrap, in each evaluation dataset. Alternatively, establish a justified bound

`P(actual q > 4.63) <= δ`

over every candidate size, and require the fixed-`q` power lower bound to reach at least `0.90 + δ`, accounting jointly for estimation uncertainty and the four candidate sizes.

Bonferroni over four looks addresses selection among sizes. It does not address substitution of the critical value.

**“T governs power only” is too strong.** With an independently selected size and an inference procedure valid at that size, insufficient size mainly reduces certification power. But here:

- `G_min = 0.95 T` changes retention and the minimum permitted cluster count.
- Finite-sample bootstrap validity and studentization depend on sample size and tail behavior.
- Availability affects which observations and members enter the calculation.
- Version-4 empirical-error estimation determines the pull distribution being approximated.

A small size can still produce an erroneous permission. The requirement is control of that probability, not impossibility of a false PASS.

The nested evaluation must reproduce every data-dependent step of the actual acceptance: retention before resampling, shared missingness, estimated standard errors, degenerate-replicate handling and the additional rejecting checks. A frozen development availability estimate need not be re-estimated inside every replicate, but its version-4 adequacy needs an explicit validation criterion.

There are also concrete discrepancies in [plasmode.py](/C:/Projetos/refute/docs/validation/v0.5.2/stage2/plasmode.py:260):

- It does not implement the specified family-level failure when at least 11 bootstrap replicates are degenerate.
- It bootstraps members before applying the count-retention rule.
- It omits the additional aggregate checks that can reject certification.
- Source errors and certain unavailable records are silently skipped during construction rather than represented as scheduled unavailable curves. The published source summary reports zero such errors here, so this is a latent defect, not evidence that these results lost records.

**Correction:** make the simulator execute the complete acceptance procedure and check source completeness against the archived schedule and manifests.

**2. Sector rule: MEDIUM.**

The revised rule correctly addresses blindness, baseline coverage, recording selected sectors, and refusing replacements after error availability is known. Its conditional-blindness wording is appropriate.

What remains unspecified is how the selector earns acceptance.

**Correction:** freeze its evaluation criteria before evaluating it, including supported observing geometries, allowable calibration deviations, availability requirements and outcome reporting. State how raw eligibility maps to the eventual measured-sector count.

The tests at 5, 8 and 12 original sectors are useful constructions. They do not alone establish an unrestricted guarantee for any original sector count and geometry. Bound the supported domain or justify the extension.

**3. A0 version 4: MEDIUM.**

The common mask-aware callable and expanded reference comparison answer the principal integration objections.

However, “preprocessing” must include **every mask-dependent operation**, including any active global-component refit, clipping and additive preprocessing. Naming `pipeline.detrend` alone is insufficient where the production path performs more work.

**Correction:** specify the callable’s complete contract, including cadence alignment, masks, normalization and model-error treatment. Freeze quantitative reference tolerances and the exact permission-blocking rules before reference evaluation.

The reference comparison must establish the quantities A0 actually uses. It remains a comparison to an implementation, not an independent proof that either implementation has calibrated errors.

**4. Sabotage regimes: HIGH for the unresolved fallback.**

The revised regimes are sensible candidates. Correcting `force_phase_half` to force **no exclusion** resolves the naming ambiguity. Treating the 0.05 distance as a power-planning effect rather than a deletion threshold is also correct.

The fallback at lines 120–121 does not complete guideline 7. Retaining the mechanism indefinitely as an open question supplies neither a demonstrated regime nor a validated simplification.

**Correction:** predeclare that failure to demonstrate the required effect blocks completion of that item. Resolve it through a recorded, validated simplification or another prospectively specified regime. It cannot be reported as guideline compliance merely because the mechanism remains in code.

Also freeze:

- Which statistic and bound each sabotage protects.
- Baseline acceptance and sabotage-effect criteria.
- Sample sizes, paired uncertainty and planned power.
- The consequence of material correlations beyond the lag cutoff.

The stronger-noise and secondary regimes add required validation work. Their members, availability and costs must enter the final family and worksheet before sizing is finalized.

**5. Sinusoid and `box_after`: HIGH.**

This is a plausible development candidate, but the proposed argument does not establish its false-alarm rate.

**A residual depth below 3 sigma is a non-detection. It is not evidence that variability explains the dip.** Increasing the estimated error makes FAIL more likely under this rule. Poor coverage, uncertain nuisance extrapolation or strong correlated noise can therefore push a genuine transit toward FAIL.

The existing implementation explicitly recognizes this distinction in [battery_v5.py](/C:/Projetos/refute/src/refute/packs/tess/battery_v5.py:367).

The initial search SNR does not resolve it. A candidate found at SNR 12 need not retain that significance under a different estimator, raw-data treatment, nuisance fit, mask and error model.

**Correction:** distinguish an accurately measured small residual from an uncertain residual. Require valid coverage and a calibrated residual-depth uncertainty before any FAIL. Prefer positive evidence for attenuation or a variability-only explanation, using a predeclared meaningful residual-depth limit. Otherwise return INCONCLUSIVE.

If retaining the proposed classifier, describe it as an empirical rule pending validation. Remove the claim that its 3-sigma construction itself controls false alarms.

The residual error also needs a concrete specification. Subtracting an estimated model introduces uncertainty and covariance. For a fixed linear fit, the relevant form is

`Var(aᵀ residual) = aᵀ(I − H) Σ (I − H)ᵀa`,

where `H` represents fitting on the out-of-transit data and prediction on the complete series. Residual scatter with a `beta` multiplier does not automatically estimate this quantity. Frequency selection adds further uncertainty.

The period-error problem is **reduced, not eliminated**. Period errors still alter the tested harmonics, transit mask, nuisance fit and residual-box alignment. Full-chain evaluations with recovered periods remain necessary.

The changed rows need more complete definitions:

- Retaining the false-failure requirement while dropping the conflicting detectability requirement is consistent with guideline 3.
- Planet-plus-harmonic cases can become ambiguous.
- The old sensitivity alternative and amplitude-only power calculation cannot certify the new decision.
- “Not flagged” must not become PASS through an obsolete sensitivity block.
- Row 3.8’s sub-check flag counts must be distinguished from final FAIL outcomes.

Finally, **1,109 zero-failure trials establish the stated one-sided bound for one fixed Bernoulli population**. Pooling configurations establishes a mixture-average bound, which can conceal a problematic regime.

**Correction:** freeze the null populations, per-cell versus mixture claims, evaluation sizes, confidence rules and failure consequences before running the evaluation. Preserve D1’s approved conditions separately for V1 and V2.

**6. T3b identity and inventory: MEDIUM, HIGH before drawing targets.**

The catalog-defined class and display-only precedence remain acceptable. The conclusion that these additions provide **no demonstrated solution to the projected shortage** is appropriately cautious.

The Gaia identity rule is still insufficient: one EB within two arcseconds can be a neighbor rather than the TIC target. Uniqueness among EB entries does not establish uniqueness among all possible counterparts. The inventory also uses TOI-table coordinates where the draft says TIC coordinates.

**Correction:** use an established TIC-to-Gaia association, or a documented counterpart procedure with position epochs, ambiguity handling and provenance. Unresolved identity makes the target ineligible.

The inventory does not implement its stated uniqueness requirement. [gaia_matches](/C:/Projetos/refute/docs/validation/v0.5.2/stage2/t3b_inventory.py:74) returns all matches, and eligibility uses `any(period-consistent match)`.

There is another latent precedence defect: `base` includes T10K members before period consistency is applied. A period-inconsistent T10K membership can therefore suppress an otherwise eligible Gaia addition.

**Correction:** form eligibility from the union of independently qualifying source memberships. Apply label precedence afterward. Retain source identifiers and conflicting period evidence.

The current zero additions mean these defects do not demonstrate a changed current eligible count. They must nevertheless be corrected before the refreshed inventory or draw.

Two reporting qualifications:

- The generated inventory supports “zero additional eligible T10K false positives.” It does not record the broader “seven TOI hosts, none false positives” claim.
- Expected yield 5.9, even with its estimated interval, does not prove that eleven acceptances are impossible. Twenty-two unwalked stars could produce eleven. This is a shortage forecast, not an infeasibility finding or an automatic NOT DECIDABLE result.

**7. Driver and tests: HIGH.**

Atomic publication, separate science bytes and worker-count resume comparison are useful improvements. The driver still does not enforce the stated accounting and batch guarantees.

In [driver.py](/C:/Projetos/refute/docs/validation/v0.5.2/stage2/driver.py:98):

- Failed process-time queries return zero. `_live()` can therefore lose previously observed CPU consumption.
- A controller crash loses uncommitted worker charges and overhead, since overhead is persisted only after `_batch()` returns.
- An ordinary shard exception stops the watchdog in `finally`, while the executor context can still wait for other running work.
- Dispatch uses a watchdog snapshot refreshed every two seconds. Many short shards can start after the actual cap is reached.
- Controller CPU time is omitted.

**Correction:** retain owned process handles, maintain monotone counters, and persist cumulative charges independently of scientific-result commits. Failed queries must not erase charges. Keep monitoring active until all owned workers stop, including exception paths. Reconcile interruptions conservatively before resuming. Windows exposes user and kernel totals through process handles. [Microsoft documentation](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getprocesstimes)

The batch rule also remains weaker than the guideline: **dispatch ending at 30 minutes does not bound the batch to 30 minutes** if running shards continue indefinitely.

**Correction:** bound shard duration and enforce the batch deadline through checkpointing or interruption of owned workers. Do not silently substitute a dispatch window for a batch-duration limit.

Affinity is verified only for supplied pin entries. A standalone run with `pin=None` neither sets nor verifies the allowed parent affinity. Require and verify the launcher contract, or enforce the mask before spawning. Check priority-setting success and actual worker settings.

The tests do not cover these failures:

- The cap test checks already-recorded expenditure before a new invocation.
- There is no live 110% watchdog-termination test.
- The batch-limit test changes the limit to 3,600 seconds and never exercises expiry.
- Killing the controller and sleeping three seconds does not prove worker termination or retained CPU charges.

**Correction:** add targeted boundary tests for live dispatch stopping, watchdog termination, batch expiry, worker exceptions, lost queries and crash/resume accounting. Keep the scientific byte-equivalence test.

There is also a concrete provenance defect in [plasmode.fingerprint](/C:/Projetos/refute/docs/validation/v0.5.2/stage2/plasmode.py:337): it hashes the component table’s **file size**, not its contents.

**Correction:** hash the table bytes, source manifests and environment. Use stable component ordering and semantic seed identities. A same-size replacement must never reuse existing shards.

**8. Costs and the three routes: HIGH. Answer (c).**

The current projection correctly blocks launching the full workload. It is not yet a complete budget.

**Route 2 cannot claim the old 22-worker speedup as a saving against this projection:** the projection already uses one-worker baseline costs. Twelve physical-core workers might improve elapsed time while increasing CPU time per unit.

I would first establish a reproducible baseline and worker-count measurement, then optimize implementation, then consider a smaller comb as a method change.

For **“faster code, same numbers,”** require:

- The same mathematical operations and conventions, including masks, clipping, gaps and fitting thresholds.
- Numerical comparisons with tolerances fixed before evaluation.
- Identical availability, branch choices, covariance-validity decisions and final outcomes.
- Scientific byte identity if the claim is exact numerical equivalence.
- Reference fallback near boundaries where numerical differences could change a decision.

Batched fits and reordered reductions do not automatically satisfy this. Tests on comfortably passing examples are insufficient.

For **`J = 2` or `3`**, section 3’s reference comparison is necessary but insufficient. Smaller combs mask more neighboring windows during each preprocessing fit. That can change clipping, trends, correlations, availability and pull tails.

**Correction:** treat smaller `J` as a prospective method revision. Require its full calibration, sabotage behavior, availability and sensitivity checks, then reassess whether the sizing reference and delivery schedule remain valid. Select it before final sizing.

There is a useful arithmetic limit: holding the worksheet’s assumptions fixed, halving the comb cost gives approximately:

| Size | Approximate `J = 2` cost | With 30% allowance |
|---|---:|---:|
| 9,000 | 2,372 CPU-h | 3,083 CPU-h |
| 10,000 | 2,635 CPU-h | 3,426 CPU-h |

Thus **a smaller comb alone does not solve the projected budget**, even before omitted validation and development work.

The numeric budget must also subtract expenditure already incurred and reserve the remaining inference validation, acceptances and reviews. Independent per-run caps do not enforce the global maximum.

**9. Order and frozen choices: HIGH. Answer (e).**

Section 9 still finalizes sizes before development steps that can invalidate them:

- Version-4 availability and tails can differ.
- Added regimes and selector validation can change the required family.
- A smaller comb changes the measurement procedure.
- The sinusoid rule and its error/sensitivity definitions remain incomplete.

It also places inference validation before freezing the acceptance text, allowing validation results to influence their own judging criteria.

**Correction:** use this dependency order:

1. Freeze the methods, family, validation criteria, candidate-selection rules and bounded development budgets.
2. Complete the designated development work needed to justify the sizing reference and cost assumptions.
3. Run the prospectively specified sizing evaluation and fix `T`, `G_min` and delivery schedules.
4. Implement the isolated production paths and establish numerical equivalence where claimed.
5. Freeze the inference-validation criteria before evaluating that gate.
6. Freeze the final code, complete acceptance specification and numeric budget before acceptance runs.

If a later probe contradicts a sizing assumption, STOP and record a prospective redesign. Do not silently change the schedule, reference model, judging criterion or candidate set.

Fresh development data can support a new design. They do not retrospectively turn a failed frozen assessment into a passed one.

VERDICT: REFUTED