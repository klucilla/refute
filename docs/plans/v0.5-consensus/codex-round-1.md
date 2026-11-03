## Verdict: WEAKENED

The direction survives. **I recommend approval after the changes below**, principally to power semantics, C2 pairing, severities, and the stop rule. No files were modified; filesystem reads stayed inside the repository.

## Review of sections 0 to 9

| Section | Decision | Required change and reason |
|---|---|---|
| **0. Lessons** | **AGREE** | Add the lesson that fewer survivors can mean more **INCONCLUSIVE**, rather than better rejection. Measure both separately. |
| **1. Goal** | **Change** | Replace “a synthetic-only result validates nothing on real data” with “synthetic acceptance does not establish real-data validity.” C2/C3 do use real data, although they cannot validate the method generally. Keep `not_validated`. |
| **2. Scope** | **Change** | Keep the core direction, but remove mandatory masking of signal-bearing injection hosts. Using the 87 hosts without an original gate-passing signal already addresses #180 within this calibration. Keep masking as deferred work. Make WP9 optional with its own small cap. Explicitly retain the unimplemented parts of #181, #182 and #191 as open. |
| **3. Acceptance pattern** | **Change** | Use test-specific sensitivity rules, not one Gaussian formula for everything. Separate development seeds from unseen acceptance seeds. Preserve historical schemas and outputs, but do not imply current source hashes remain compatible with old locks. |
| **4. Calibration** | **Change** | Keep C1/C2/C3, with the pairing, denominators and uncertainty changes below. C2 is a reused benchmark, not independent confirmation. |
| **5. Exit criteria** | **Change** | Distinguish **accepted completion** from **termination without acceptance**. A failed core implementation cannot simultaneously block closure forever and be silently downgraded under section 7. Specify reproduction comparisons and tolerances. |
| **6. Exclusions** | **Mostly AGREE** | Deferring #9’s validated null, #11, #12 and #192 is defensible. Remove “a probability rather than a deterministic refutation” as a reason to exclude #12: a probability calculation can be deterministic and reproducible. The reasons are scope, dependencies and separate validation. |
| **7. Caps** | **Change** | Define accounting, per-WP limits, calibration reserves, and the outcome when a core WP fails. Trigger scope reduction by effort consumed as well as calendar date. |
| **8. Stops** | **Change** | Freeze the C1 confirmation design, sample-size rule and decision rules before development acceptance results can influence them. Future seeds alone do not prevent scenario selection after development. S2 can finalize the already specified protocol and targets. |
| **9. Renumbering** | **AGREE, with completion** | Preserve all text and historical references. Include the Mathematics milestone if it exists, rename in descending version order, and distinguish current references from historical records. Keep the pending v0.4 release as a separate tracked item. |

## Scope and effort: questions a and b

**The full draft is ambitious for 20 agent-days.** The bottleneck is acceptance and error-model work across existing tests, not adding nine test functions. The five-day v0.4 calendar history is not a reliable effort estimate for that work.

My scope recommendation:

- **Core:** WP1 to WP4, WP6, reproducibility, C1 to C3.
- **Optional:** WP5, with explicit retained limitations if dropped.
- **#176:** retain **one bounded attempt, first to drop**, only if it has an independent allocation, for example one agent-day and a predefined compute limit. Start it only after the core implementation is accepted and calibration resources are reserved.
- Remove host masking from the required implementation. Keep #188’s study bounded, but its outcome must not choose favorable C2 reporting categories retrospectively.

Do not close broad issues merely because their v0.5 subset ships. In particular:

- #181’s planetary-occultation compatibility is absent.
- Three fixed SWEET periods do not implement #182’s proposed multi-frequency alternative.
- #191’s timing-duration comparison is only partially addressed.
- #186’s mismatched `candidate.sde` provenance is missing from WP6.

## C2 and transformations: questions c and f

**Reusing the 100 stars is legitimate for a descriptive paired benchmark. Newly drawn stars are not mandatory for C2.** However, the population’s observed failures influenced the new test selection. “Thresholds were never tuned” does not make it an untouched confirmation sample. C1’s unseen confirmation seeds and C3’s new targets provide separate evidence.

Required details:

1. **Keep two summaries:** all 100 stars for historical comparison, and the prespecified analysis subset excluding development targets. The full record’s **17/64 cannot be the baseline for an excluded subset**. The two control stars also were not members of that 100-star funnel.
2. Verify input hashes **directly**. Reproducing 17/64 does not establish identical inputs.
3. Freeze search, detrending, prewhitening and candidate identity for the battery-only comparison. If any changes, report an additional end-to-end comparison separately.
4. Treat “v0.4 battery on v0.5 code” as a **compatibility implementation requiring verification**. Match per-curve candidates, statuses, emitted severities and stage-survival flags against the historical implementation or records. Aggregate counts and regression fixtures alone are insufficient.

The current chain performs search and attack together, so splitting candidate generation from battery evaluation requires explicit implementation: [measure.py:33](C:/Projetos/refute/src/refute/packs/tess/discover/measure.py:33).

**Keep inversion and rotations for the historical C2 comparison.** Always report inversion separately, plus signal-bearing and original-gate-negative hosts. Do not call either transformation a validated null. LEO-Vetter explicitly rejected inversion for TESS and used orbit/sector scrambling, which differs from Refute’s cyclic rotations. [Kunimoto et al., §V.4](https://arxiv.org/html/2509.10619v1#S5.SS4)

For injections, report both:

- Survival among recovered, gate-passing injections, the conditional vetting cost.
- Recovery-and-survival among **all attempted injections**, the end-to-end outcome.

The 87 hosts are **original-gate-negative**, not known signal-free stars.

## Power rule: question d

**Accept the formula only for its stated statistical model.**

For a prespecified scalar estimator with approximately Gaussian error and a one-sided rejection threshold,  
`delta_min / sigma >= z_threshold + z_power`  
is a valid model-based power requirement. It is not a universal rule for chi-square heterogeneity, ratios, two-dimensional centroids, maxima or categorical catalog checks.

Require each test to declare:

- Effect, rejection region, uncertainty model and minimum detectable effect.
- Analytic or deterministic simulation-based sensitivity calculation.
- An explicit justified applicability category for non-statistical checks.

**Do not call a powered non-rejection evidence of equivalence.** If PASS is intended to exclude effects outside a bound, use a prespecified confidence-bound/equivalence rule. The proposed power guard alone supports the narrower statement “no failure detected, with declared sensitivity.”

Validation should use unseen seeds across white noise, correlated noise, gaps, few events, unequal errors and boundary cases. Check false failures, achieved detection probability and uncertainty calibration. Inject upstream of detrending. Existing event errors and aggregation need scrutiny: [events.py:174](C:/Projetos/refute/src/refute/packs/tess/events.py:174) uses a scatter-based error floor, which does not itself establish calibrated power.

**Exempt `snr` from this non-rejection guard.** It is a positive detection gate, not an absence-of-discrepancy test: [gauntlet.py:36](C:/Projetos/refute/src/refute/packs/tess/gauntlet.py:36). Still test its noise model and detection behavior separately.

## Severities: question e

Fatal means refuting the **declared signal claim**, not identifying its astrophysical cause.

| Test | Recommended severity |
|---|---|
| `single_event` | **Fatal**, within an accepted multi-event applicability domain. |
| `event_consistency` | **Fatal** for a declared common-depth model, with calibrated errors and dilution handling. |
| `edge_events` | **Warning** for proximity alone. Fatal only for an accepted test demonstrating artifact dependence; insufficient remaining data means INCONCLUSIVE. |
| Two-sided secondary | **Warning** for a significant dip or brightening alone. Fatal only with an accepted criterion incompatible with the declared planetary model. |
| Sinusoid | **Warning** for significant variability alone. Fatal when the accepted comparison establishes that variability accounts for the candidate signal. |
| Duty-cycle bound | **Fatal** for a genuinely excluded geometry; warning or applicability failure for a heuristic search-domain bound. |
| `transit_shape` | **Warning**. Grazing planets can be V-shaped. |
| `depth_stability` | **Warning initially**, unless corrected dilution and uncertainty acceptance justify a fatal common-depth rejection. |
| Per-sector centroid | **Fatal** only with qualified, consistent multi-sector offset evidence; otherwise INCONCLUSIVE. |

For centroid, compare offsets in a common sky frame and include uncertainty/systematic treatment. Raw aperture and dilution-corrected light-curve depths cannot simply be required to match. Also guard against sector selection hiding genuine contamination.

The current statistic sums sector chi-squares, so one sector can dominate: [battery.py:281](C:/Projetos/refute/src/refute/packs/tess/battery.py:281). The proposed two-sector safeguard is reasonable, but is **Refute’s conservative policy**, not LEO-Vetter’s method; LEO-Vetter chooses the sector with the best PRF fit quality. [Kunimoto et al., §IV.5](https://arxiv.org/html/2509.10619v1#S4.SS5)

## Exit criteria, targets and stopping: questions g and h

**The scientific targets are appropriately non-blocking.** Implementation acceptance may require passing tests, provided a rejected implementation can terminate without being accepted.

Leave numerical scientific targets to **S2**, with their rationale and attainable precision. Halving survivors and limiting loss to 10 percentage points are reasonable aspirations, not justified performance commitments yet. Eight planets plus eight false positives is a small feasibility sample, not precise class-wise validation.

Add these safeguards:

- Report REFUTED, WEAKENED, INCONCLUSIVE and SURVIVED transitions separately. Current survival counting includes WEAKENED: [measure.py:30](C:/Projetos/refute/src/refute/packs/tess/discover/measure.py:30).
- Report paired discordances. Do not treat injections or transformations sharing a star as independent observations.
- Prespecify zero-denominator handling, errors, unavailable controls and bounded replacement rules.
- Define agent-days as accumulated work, CPU accounting, storage baseline and reviewer-token accounting.
- Reserve resources for calibration, reproduction and gate review before optional work begins.
- At any hard cap, issue a terminal report. If required evidence is incomplete, end **without acceptance**. No automatic extension or new preliminary study.
- Allow bounded repairs to implement the frozen specification; prohibit changing the method or thresholds to rescue results. Prespecify how corrupted runs are handled.

One consequential interaction needs an integration acceptance case: **a warning test returning INCONCLUSIVE currently makes the entire verdict INCONCLUSIVE**, before warning failures produce WEAKENED: [verdict.py:258](C:/Projetos/refute/src/refute/core/verdict.py:258). Extending the power guard to every warning therefore materially changes battery behavior.

## Missing v0.4 lessons

Add acceptance cases for real transits **coexisting with** variability, edge proximity, grazing shape, dilution changes and unequal event coverage. Otherwise stronger tests can reject the nuisance rather than correctly assess the transit.

Also require:

- Transit masking in the sinusoid fit.
- Explicit limits of the phase-0.5 secondary check.
- Full signal-identity checks for C3 before scoring dispositions.
- Authenticated promotion inputs when stage-1 dossiers are absent, with missing/tampered-input failures.

**With these changes, I would support the draft as the v0.5 scope consensus.**