## Verdict: WEAKENED

Most round-1 changes are adopted. Remaining requirements concern **severity policy, the missing frozen C1 design, and budget/stop-rule consistency**.

I accept the release correction. I also **agree with unchanged aggregation**: an underpowered decisive warning can make the verdict INCONCLUSIVE, provided the integration case and separate reporting remain.

## 1. Round-1 changes

| Required change | Status | Assessment |
|---|---|---|
| Distinguish rejection from increased INCONCLUSIVE | **ADOPTED** | Sections 0, 1 and 4. |
| Correct validation wording; retain `not_validated` | **ADOPTED** | Section 1. |
| Defer host masking; bound optional #176; retain unfinished issue scope | **ADOPTED** | Section 2. |
| Include kept-peak SDE provenance | **ADOPTED** | WP6. |
| Test-specific sensitivity; Gaussian formula limited; gate exemption; no equivalence claim | **ADOPTED** | WP1 and section 3. |
| Unseen acceptance seeds, noise/coverage/coexistence cases, calibrated errors | **ADOPTED** | Section 3. |
| Historical outputs/schema compatibility distinguished from source-lock compatibility | **ADOPTED** | Section 3.8. |
| C2 reused benchmark, direct hashes, development exclusions, fixed upstream pairing | **ADOPTED** | Section 4. |
| Verify compatibility per curve | **ADOPTED** | Section 4, wherever historical records exist. Counts alone remain limited evidence. |
| Separate transformations and host categories; both injection denominators | **ADOPTED** | C2. |
| Four verdict counts, paired transitions, clustering, zero denominators | **ADOPTED** | Shared reporting rules. |
| C3 identity check and feasibility wording | **ADOPTED** | C3. |
| Severity recommendations | **PARTLY** | Shape, depth stability and centroid are explicit. Single-event, consistency, edge, secondary, sinusoid and duty-cycle severities remain unspecified. |
| Centroid frame, systematics and contamination-selection safeguard | **PARTLY** | Mostly adopted. Explicitly require dilution-aware depth qualification, rather than raw aperture versus corrected light-curve equality. |
| Completion versus termination; reproduction tolerances | **PARTLY** | Distinction and tolerance adopted. Infrastructure failures still need explicit treatment, below. |
| Accounting, allocations, reserves and effort-triggered stopping | **PARTLY** | Numbers supplied, but accounting and enforcement conflict. |
| Freeze C1 design, sample-size rule and decision rules before development | **PARTLY** | Promised, not supplied. The linked `docs/plans/v0.5-acceptance.md` does not exist. Section 4 lists scenarios but no frozen sample-size or decision rule. |
| Correct exclusions and preserve renumbered history | **ADOPTED** | Sections 6 and 9. |
| Transit masking, phase-0.5 limitations, authenticated promotion inputs | **PARTLY** | Masking and promotion adopted. Explicitly state that phase 0.5 does not cover eccentric secondaries and alone cannot classify an EB. |

## 2. Concrete remaining problems

1. **Section 3, lines 112–115:** “scientific acceptance fails … diagnostic … not a reason to stop.”  
   Acceptable for individual scientific tests. Explicitly exclude failed **engine enforcement, historical compatibility, input authentication and reproduction infrastructure**. Those cannot be downgraded to diagnostics while satisfying acceptance.

2. **Section 7.3:** “at 12 agent-days … the calibration starts with what is accepted.”  
   Core implementation allocations total **15.5 days**. This trigger can begin calibration before core reporting and reproducibility work finishes. Replace with: **drop unstarted optional work and reassess remaining core work; calibrate only after required infrastructure is accepted and the tested battery is frozen.**

3. **Section 7 accounting:** “one per UTC calendar day” conflicts with allocations of **0.5 and 1.5 days**.  
   Use accumulated session-hours divided by a fixed hours-per-agent-day, counting both agents, or convert every allocation to the stated calendar accounting.

4. **Severity policy:** add the round-1 severity table, including the conditions for fatal escalation. Significant variability, edge proximity or a secondary alone must not automatically become fatal.

5. **Section 4:** “the C1 design … is frozen now, in the acceptance documents.”  
   That statement is currently unsupported because the referenced document is absent. Supply it before implementation, including scenario distributions, sample-size rule and decision rules.

## 3. Budget arithmetic and reserve

**The nominal arithmetic is correct:**

- Core implementation: **15.5 agent-days**
- Calibration reserve: **5**
- Core total: **20.5**
- Optional WP5 + WP9: **2.5**
- Total: **23**, leaving **1 day** beneath the 24-day cap.

**The reserve is not yet protected against core overruns.** Allowing implementation WPs to reach 150% consumes **23.25 days before calibration**, exceeding the total cap once the five-day reserve is added.

Require this invariant before **every WP start and overrun**, including core work:

> Remaining budget must cover the untouched calibration reserve; otherwise stop implementation and record the reduced scope or terminate without acceptance.

Likewise, the 150-hour cap leaves **50 processor-hours for all development** after reserving 100. State that limit explicitly. Treat the five calibration days as an allocation subject to the hard total, not permission for a 50% reserve overrun.

**No further scientific scope expansion is needed.** Resolve these planning inconsistencies and supply the frozen acceptance design; I would then support SURVIVED for the scope consensus.