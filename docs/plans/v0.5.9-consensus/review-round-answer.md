OVERALL: REFUTED
BLOCKS: 8

## 1. Report

I independently reproduced the per-TOI table, the Q1–Q5 counts and cost statistics, and all 252 unit hashes. All 24 TOIs are complete. All 82 zero-coverage test results were `INCONCLUSIVE`. The exploratory labels, vocabulary and separation from historical verdicts hold.

- **Q1–Q4:** Same decided class fell from **3/14 to 1/14**, while joint abstention rose from **1/14 to 9/14**. Both modes retained the historical class on **8/8 controls**. All four Q3 bases ran and returned `OK`. E decisions fell **10→8**, S decisions **20→12**.
- **Q5 and pilot:** The ledger reconciles to **252 units, 4.12165 CPU-h, 5,869,984,714 bytes and 4,773,538,245 bytes peak disk**. The pilot differences reproduce as **1.35%, 1.24% and 0.22%** from the journal, ledger and recorded observer totals. The independent per-process and per-file readings were unavailable in the committed evidence I reviewed.
- **`331ca03`:** The pinned run files match the commit, and the draft discloses that its fixes received no further Codex review. The pilot supports accounting agreement under the observed workload. The corrections below narrow the pilot claim and fix the Q3 and post-hoc readings.

## 2. Specification

Line references in this list are to `docs/plans/battery-v5-spec.md`.

1. **PARTLY.** The v5 execution path is mapped. Screen-only tests, legacy test roles and the consensus change to the returned verdict still conflict in the draft. `40–48, 82–89, 114–129`
2. **PARTLY.** Fixed evaluation is specified. The draft conflates the pre-fit search grid with probes derived from the final fit. `131–158`
3. **ANSWERED.** Observed and simulated centroid guards, direct stage-2 tests and the zero-coverage policy are specified. `160–175`
4. **PARTLY.** Both arms run on every draw, but the flip rule and the exclusion of identity misses and operational losses leave the informative-pair endpoint ambiguous. `177–192`
5. **PARTLY.** The Wilson convention, critical counts and conditional power table reproduce. Fixed-draw power, the decision-floor rule and the lock-blocking criteria remain underspecified. `194–219, 318–342`
6. **ANSWERED.** The schema compatibility checks, frozen attachments, historical lock verification and follow-up registration commit are specified. `221–238`
7. **ANSWERED.** The charter, issue-approved reruns, separate synthetic lock, blind review and exposure/draw sequence are specified. `240–260`

**Screen and cost:** Section 3 reproduces the 250-case Wilson thresholds and covers the screen review’s two screen-specific blocks in outline. It needs an explicit assessment rule. The directed-holdout and independent-cohort gates belong to their separate routes. Section 6’s unit means and cost examples reproduce, and PC yield is correctly labelled unknown. Its identity-conditioned yields and sizing conclusion need correction.

## 3. Blocks and exact changes

1. **Pilot chronology and scope.** Replace “first batch” with **“first three batches, 3 fetches, 6 bases and 18 probes.”** Replace the claim that the pilot checked the fixes with **“the pilot checked accounting agreement under observed load.”** The recorded caps were unexercised. `docs/reports/v0.5.9-report.md:44–49,55–77`, `docs/validation/v0.5.9/prototype-ledger.json:9–120`, `docs/plans/battery-v5-spec.md:283–289`
2. **Q3 overstates what the guard caught.** Say **three of four bases** triggered the guard. TOI-734.01 E had **82,558 cadences** and `INCONCLUSIVE` from sector heterogeneity, **p = 1.6×10⁻³³**. All **12/12** of its probes triggered the guard, and both arm classes stayed `WEAKENED`. Describe the observed covariance failures without claiming the earlier overflow was reproduced. `docs/reports/v0.5.9-report.md:138–144,220–222`, `docs/validation/v0.5.9/prototype-report.md:19–23`
3. **Post-hoc claims exceed the measurements.** Replace the historical causal attribution with the observed class pattern. E and S shared bytes in this run, while v0.5.6 byte identity is unknown for **4 of the 13** historical cases. Say **8/10 first disagreements occurred on epoch probes in the fixed order** and **6/10 crossed the background sensitivity threshold**. For TOI-399.01 S/p2, `aperture_depth` alone determined `REFUTED`. `centroid_shift` also failed and was diagnostic. `docs/reports/v0.5.9-report.md:198–219`, `docs/plans/battery-v5-spec.md:267–273`, `docs/validation/v0.5.9/prototype-records.json:3796`
4. **Screen and verdict semantics.** Define exactly when a core test is assessed, including how a valid measurement with a sensitivity refusal is treated. Keep screen-only tests out of legacy aggregation and preserve configured roles, including diagnostic centroid where applicable. State that the **base aggregate** retains its semantics and the **final consensus rule** can demote it, so adoption requires blind rule review. `docs/plans/battery-v5-spec.md:40–48,55–89,114–127`
5. **Refit grid.** Define E’s bounds and pre-fit trial spacings from fixed input quantities and the raw span, including exact endpoints and when the grid may coarsen. Define the final-fit probe offsets separately. The optimum cannot supply the spacings for the search that finds it. `docs/plans/battery-v5-spec.md:133–157`
6. **Paired endpoint and yield.** Count a flip when exactly one arm gives a decided class **on the catalog signal**, or both do and differ. Tabulate identity misses and operational losses separately and freeze how they enter the primary analysis. With the original same-signal rule, the prototype gives **6 flips/16 informative pairs before consensus** and **1/9 after**. The draft’s **10/20** and **4/12** are raw class comparisons. Use identity-qualified rates for yield and raw base decision rates for probe cost. `docs/plans/battery-v5-spec.md:177–192,297–309,329–342`
7. **Power and fixed-draw sizing.** At a true flip rate of **0.05**, **320** informative pairs already give **91.6%** conditional power. **400** give **96.9%**. Remove “400 or more” as a requirement. Size fixed draws for uncertain yield and losses, specify the minimum informative count and the decision-floor denominator and consequence, and identify the lock-blocking criteria explicitly. `docs/plans/battery-v5-spec.md:210–219,318–342`
8. **Historical baseline.** Change **0.23 decidability** to **24/100 decidable** among the identity-matched v0.5.6 Part B planets. **23/100** is retention. `docs/plans/battery-v5-spec.md:280–282`, `docs/plans/research-2026-11-23/codex-answer.md:27`

### Non-blocking

- Link from Q1, Q4 and Q5 directly to the generated report’s full Wilson intervals and per-axis CPU breakdown. The draft correctly discloses the pinned report script’s download-key mismatch.
- State explicitly that the research review’s directed-holdout and independent-cohort feasibility gates remain open. This review was offline and did not re-review or execute `331ca03`.

