# v0.5.2 stage 2: the numeric budget, and the stop it triggers

Written 2026-11-09, on the design's section 9, step 5, before any of the large workloads below was launched. It decides nothing about the method. `method_status: not_validated`.

**The result: the projection was above the hard maximum of 2,000 CPU-h of development and acceptance, so the work stopped for the maintainer** (the design's section 8; the delegation of 2026-11-08, item 6). Nothing below had been launched. **The maintainer's decision of 2026-11-09 is at the end of this page; it raises the maximum to 3,100 CPU-h.**

## The projection

CPU-hours, at the placement measured to be the best (12 workers, one per physical core). "Measured" means a unit cost measured on version 4's code; "scaled" a unit cost multiplied by a schedule; "estimate" a figure with no measurement of the final workload behind it.

| Section | CPU-h | Basis |
|---|---|---|
| Spent so far in stage 2 | about 70 | sizing 53.6 (the `state.json` of each run), the rest estimated from wall time and workers |
| A0 acceptance at `T` = 9,000 (9,669,446 curves) | 1,048 | measured per section and sector count, at 12 workers ([`probe-a0v4-cost.json`](probe-a0v4-cost.json)) |
| Known-answer gate | 820 | scaled: 4,000 replications of the whole family for each of the two distributions (Gaussian, Student's t), at 369 CPU-seconds per dataset, measured in the 200-dataset evaluation |
| Adequacy check | 95 | scaled: the whole A0 round 2 schedule on version 4 (425,400 curves) and the complete evaluation repeated |
| Sinusoid evaluation | 60 to 180 | estimate: 106,464 curves at 0.20 CPU-s for the decision; 1.3 to 4.7 CPU-s for the recovered periods; about 45 CPU-s for a full analysis, on a sample of 20 curves per cell. [`probe-other-costs.json`](probe-other-costs.json), one worker |
| Sector selector's family | 135 | estimate: about 770,000 curves at 0.3 to 0.8 CPU-s; its size is not designed yet |
| Sabotages and regimes | 30 | estimate |
| WP2, WP3 (a), (c), (d), the D lines | 62 to 100 | the 62 hours is v0.5.1's allocation estimate, never a measurement |
| **Total** | **about 2,320 to 2,480** | |

The known-answer gate needs only the two base distributions: a studentized root is unchanged by a per-member shift and scale, so the boundary and mixture scenarios reuse the same bootstraps exactly. Without that, it would be some ten times larger. Its additional checks, which only reject, are not equivariant, and leaving them out of those scenarios can only overstate incorrect permission.

**The other hard limits.** Calibration (150 CPU-h): not started, and not priced here. Agent-days: about 0.5 of 12. **Review tokens (1.0 M):** no independent reviewer session has run in stage 2. Codex's five calls used 928,026 input tokens that were not cached and 121,922 output tokens, 1.05 M together, and 19.5 M cached. Whether Codex counts against this limit is the maintainer's to say; if it does, the limit is reached. Until it is decided, no further Codex call is made, so the end-of-round review of `dbbd018` and of this page is pending.

## What was done to bring it down

The first projection for A0 was 3,781 CPU-h. The batched detrending, the reuse of unchanged windows and the blocks of 24 knots bring it to 1,048, under the equivalence criteria frozen before their evaluation. `J`, the tolerances, `T`, the strata and the family are unchanged, and no stratum was grouped.

## The maintainer's options

1. **Raise the hard maximum.** About 2,500 CPU-h would cover the projection with almost no margin; about 3,100 would hold the 30 % planning margin on what remains. Nothing in the method changes.
2. **Reduce the known-answer gate.** The specification fixes at least 4,000 replications per scenario, so this is a change to it. Student's t at 1,000 replications would save about 615 CPU-h, at the price of a weaker statement about non-Gaussian tails.
3. **Leave the selector uncertified.** About 135 CPU-h saved. Targets of five or more sectors stay INCONCLUSIVE in the A0-dependent tests: 46 of the 100 C2 stars and 16 of the 22 C3 targets.
4. **Combine 2 and 3:** about 1,630 to 1,730 CPU-h. It fits under 2,000 without the 30 % margin on what remains.

**The time, whichever is chosen.** At 12 workers, 2,300 CPU-h is about 192 hours, or about 8 days with the reduced daytime load, after the remaining development. It would pass the pause of 18 November at 20:00 and resume afterwards.

## The maintainer's decision of 2026-11-09 (#216)

**The hard maximum of stage 2 rises from 2,000 to 3,100 CPU-h** of development and acceptance. The other limits stand: calibration 150 CPU-h, 12 agent-days, 1.0 M review tokens. **Codex's tokens do not count against the review limit**, which is for independent review sessions; Codex's use is recorded per round in the consensus record when the CLI reports it. Conditions:

- Each section projects its own cost from its first 5 % and **stops if it passes 1.5 times the projection**. If the total projection passes 3,100 CPU-h, the work stops before launching.
- Units per hour are measured with 12 workers (one per physical core, on processors 8 to 31) and with 22, and the setting with the shortest wall-clock time is used. The measure is recorded, and the caps are reported in CPU-h and in wall-clock hours.
- The machine rules stand (the decision of 2026-11-08, item 10).

**The caps.** The projection is the table above, with the midpoint where it gives a range; 1.3 times it is the planning cap, 1.5 times the stop. Wall-clock hours divide by the 11.4 workers a week averages under the machine rules (118 hours at 12 workers, 50 business hours at 10) and are replaced once the placement is measured.

| Section | Projection (CPU-h) | Planning cap (x1.3) | Stop (x1.5) | Wall-clock at the projection (h) |
|---|---|---|---|---|
| A0 acceptance | 1,048 | 1,362 | 1,572 | 92 |
| Known-answer gate | 820 | 1,066 | 1,230 | 72 |
| Adequacy check | 95 | 124 | 143 | 8 |
| Sinusoid evaluation | 120 | 156 | 180 | 11 |
| Sector selector's family | 135 | 176 | 203 | 12 |
| Sabotages and regimes | 30 | 39 | 45 | 3 |
| WP2, WP3 (a), (c), (d), the D lines | 81 | 105 | 122 | 7 |
| Comb reference check (section 3 of the design) | 40 | 52 | 60 | 4 |
| **Remaining** | **2,369** | **3,080** | | **208** |
| Spent before this decision | about 70 | | | |
| **Total** | **about 2,440** | **about 3,150** | | |

The comb reference check was missing from this table until Codex's end-of-round review; its 40 CPU-h is an estimate, priced by its first 5 %. The same review restored the production preprocessing for A0.8's noise-free truth, so the A0 line of 1,048 CPU-h is low and is measured again before the acceptance. The planning cap's total passes 3,100 in this table: the limit that binds is the hard maximum on the projection (`budgeted.py`, which every line of this table runs through), and the stop column can also sum above it; the maximum wins. 204 hours of wall clock from this morning would reach the pause of 18 November at 20:00 (227 hours away) only with no gaps, and development comes first, so the work is expected to pause and to resume on the maintainer's release.

## What this does not establish

These are projections. The per-unit costs are means of a few hundred units; the items marked "estimate" have no measurement of the final workload, and the selector's family and the full-chain sample are not designed yet. No part of this page says that version 4 is calibrated.
