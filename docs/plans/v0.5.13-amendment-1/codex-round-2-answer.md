## Round 1 items

| Item | Status | Verification |
|---|---|---|
| 1. Population and gate | **`APPLIED`** | The full cohort remains subject to the approved gate. The 135 non-SB1 and 172 SB1 cases are prespecified descriptive groups. The thresholds and symmetry denominators are preserved. [Amendment, lines 68–104](/C:/Projetos/refute/docs/plans/v0.5.13-charter-amendment-1.md:68) |
| 2. Power | **`APPLIED`** | The new wrapper passes the full-precision 135/172 weighted probability to the frozen functions. The artifact reports `0.945942` and `0.134514`. The last two values round to zero at six decimals. The log preserves the earlier runs and records the corrected run before and after execution. [Amendment, lines 106–134](/C:/Projetos/refute/docs/plans/v0.5.13-charter-amendment-1.md:106) · [Wrapper](/C:/Projetos/refute/docs/plans/v0.5.13-amendment-1/power_a1c.py:24) · [Output](/C:/Projetos/refute/docs/plans/v0.5.13-amendment-1/power-a1c.json:15) · [Log](/C:/Projetos/refute/docs/plans/v0.5.13-amendment-1/log.jsonl:7) |
| 3. Count provenance | **`APPLIED`** | The revised text identifies the fields used and states the limitation of the local log as evidence of order. [Amendment, lines 26–40](/C:/Projetos/refute/docs/plans/v0.5.13-charter-amendment-1.md:26) |
| 4. Adoption and review | **`APPLIED`** | The status block preserves exact-SHA approval, the conditions for blind review, and the separate phase authorizations. [Amendment, lines 3–17](/C:/Projetos/refute/docs/plans/v0.5.13-charter-amendment-1.md:3) |

## Integration findings

1. **Blocking. The final power takeaway overstates the planning result.** Lines 136–139 make an SB1 survival rate near 0.30 sound sufficient to predict failure of the real gate and present an infeasibility record as the next step. The result also depends on the model’s other assumptions. The approved charter calls for sizing on documented eligibility and band sizes before authorization. [Amendment, lines 136–139](/C:/Projetos/refute/docs/plans/v0.5.13-charter-amendment-1.md:136) · [Approved charter §5.5](/C:/Projetos/refute/docs/plans/v0.5.13-charter.md:333)

   **Replace lines 136–139 with the following.**

   > Under the stated homogeneous planning approximation, assumed SB1 survival of 0.30 gives a joint pass probability of 0.134514. Before v0.6 authorization, apply the frozen sizing procedure to documented eligibility and band sizes. Record any shortfall as a feasibility finding. If the evidence supports judging an approved target infeasible, submit a separate record for that target under the advance rule. The simulation-free planning scenarios alone establish neither actual gate performance nor infeasibility.

2. **Editorial. Date the “what was known” statement to each draft.** The quoted paragraph documents the two original analyses, while this revision also had the corrected run available. Preserve the original chronology and add this sentence after line 40. [Amendment, lines 28–42](/C:/Projetos/refute/docs/plans/v0.5.13-charter-amendment-1.md:28)

   > The two analyses above were available to the first draft. This revision also had the corrected all-307 planning calculation recorded in `power-a1c.json`. The catalogue type count remained the sole new empirical result.

3. **The §5 replacement and blind-review status are consistent.** Lines 96–98 replace only “Report per-type FP results descriptively.” The next two sentences, including the infeasibility sentence, remain in force. The power section supplements the approved sizing calculation. This revision adds descriptive reporting and a planning check, so it does not trigger a fresh scientific-rule-change blind review. The exact-SHA approval and existing review requirements still apply. [Amendment, lines 3–17](/C:/Projetos/refute/docs/plans/v0.5.13-charter-amendment-1.md:3) · [Replacement scope](/C:/Projetos/refute/docs/plans/v0.5.13-charter-amendment-1.md:96) · [Approved charter §5](/C:/Projetos/refute/docs/plans/v0.5.13-charter.md:313)

## Verdict

**`NOT_APPROVABLE`** until the power takeaway is corrected. All four round-one items were applied. Verification was read-only. I inspected the scripts and records without running the scripts or accessing the Drive.