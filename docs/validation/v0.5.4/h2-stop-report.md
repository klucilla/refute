# v0.5.4, second half: the stop report (#217)

**The decision.** This report answers item 8 of the maintainer's decision of 2026-11-12 (night):
"PARE no fim dos passos 1 a 7 ... com: o resultado de cada passo, o consumo e a recomendação
entre seguir e pausar, pelos critérios da seção 6 do relatório."

**Status.** Steps 1 to 7 ran or stopped as planned ([`v0.5.4-h2-plan.md`](../../plans/v0.5.4-h2-plan.md)),
before the drain of 2026-11-18 19:30.
- Every step's rule was frozen in a commit before its data were read, and Codex reviewed the
  design and the code before each run.
- Each exact procedure was posted on #217 before its run.
- `method_status: not_validated` throughout. No record here is a negative result, an
  infeasibility draft, a confirmation or a validation of the battery.
- Nothing about step 8 is proposed (decision 5).

## Each step's result

| Step | What it asked | Result | Record |
|---|---|---|---|
| 1 | D2's joint floor; T2a's non-fixable class-(ii) losses | D2: `F_strict` 8, `F_rule` 16, `F_upper` 21 against an allowance of 22. T2a: `F_strict` 20 against B's margin of 7 (2 if the 5 REFUTED stay; 49 in C). The margins were known before; only the per-case overlaps are new. | [`h2-step1-floor.json`](h2-step1-floor.json) |
| 2 and 3 | I3 corrected on the increment, in a population version | `INCONCLUSIVE`, no stop. At τ* = 124.80, from calibration only, the strict planet budgets fail at their upper Clopper-Pearson ends. EB1 keeps 275 of 381 not rejected and EB2 332 of 373, against D1's allowance of 10 each, so D1's joint bound is vacuous (−1.0). | [`h2-step3-i3.json`](h2-step3-i3.json) |
| 4 | B0's oracle with 1, 2 and 3 % stellar errors | **STOPPED for the maintainer** at 63 of 77 shards (1.409 CPU-h). The checkpoint underestimated the cost twice: once in the part, once in the one pre-approved completion (7c). There is no summary. | [#217 comment](https://github.com/klucilla/refute/issues/217) |
| 5 | E2's distance to the information bound, decomposed | `INCONCLUSIVE` by design. E2's effective response is unknown, so only the Fisher inflations are given (windows about 1.15, box about 1.02). | [`h2-step5-gap.json`](h2-step5-gap.json) |
| 6 | I2's first stage on the 102 class-(i) injections | `INCONCLUSIVE (too many unknown)`, as disclosed before the run. All 102 are UNK: 96 inadequate at the transit's scale (Box-Pierce) and 6 with an OU τ below three bins. None is freed. The T2a margins stay at −221 in B and −179 in C. | [`h2-step6-i2.json`](h2-step6-i2.json) |
| 7 | Sinusoid's joint bound in D2; T2a's feasibility reading | D2: the Fréchet certificate at the oracle gives a floor of 11 and an upper count of 27 against 22. It is the battery's own rule under the generator's model, not a universal impossibility. T2a: `INCONCLUSIVE` by design (no true covariance for real hosts). | [`h2-step7-sinusoid.json`](h2-step7-sinusoid.json) |

What each record does not show:
- **Step 3** requires D1 from the new test alone, assuming the other tests reject nothing. Its
  failure bounds that test only; it does not exclude D1's fatal class.
- **Step 6** shows no information limit: no case reached a valid bound.
- **Step 1's `F_upper`** and step 7's conditional floor carry explicit limits. Neither is a
  demonstrated, unavoidable floor.

**T3b** (decision 6, metadata only) counted 2 of the 22 remaining stars of the approved frame as
domain-eligible: 13 of the frame's 63 in all, against the 11 needed. It adjudicated nothing.
A shortage of 9 is a counted fact, not an infeasibility record
([`t3b-count.json`](t3b-count.json)).

**Record defects** (decision 7d) are new records in [`record-defects.md`](record-defects.md) and
items of #59:
- the ambiguous-sinusoid class label;
- the 27/26 count, which is not a defect;
- I4's 15 convergence failures, whose cause is not established;
- the decision page's prices.

Nothing in `src/` changed.

## Consumption

| Resource | Used | Cap |
|---|---|---|
| CPU, phase | 29.04 CPU-h (first half 17.17; second half 11.87) | 50 (second half 25); the 80 % barrier is 40 |
| Review tokens, Codex | 2,028,020 | 3.5 M; stop at 2.8 M |
| Review tokens, independent review (Fable 5.2, counted apart) | 266,456 | as above |
| Review tokens, together | 2,294,476 (66 % of 3.5 M) | as above |
| Agent-days | 1.25 by wall clock; 0.75 active | 10 |
| Disk (records and caches of the phase) | about 10 MB counted; 19 MB in `.cache/v054` | 5 GB |

The second half's CPU by step:

| Step | CPU-h |
|---|---|
| 3 | 6.55 (planets 3.79, binaries 2.77) |
| 6 | 3.78 |
| 4 | 1.41 |
| 7 | 0.06 |
| 5 | 0.06 |
| summaries | about 0.001 |

The Codex conversations of the second half were audit, T3b and steps 1, 3, 4, 4rest, 6 and 7.
Their answers are in [`../../plans/v0.5.4-consensus/`](../../plans/v0.5.4-consensus/), with the
tie-breaks recorded. The end-of-round review returned `SURVIVED` (`h2-close`).

## The recommendation: pause

This is a strategic judgment, by the audit's section 6 criteria
([`v0.5.4-fable-audit.md`](../../plans/v0.5.4-fable-audit.md), section 6) as Codex's check
qualified them ([`v0.5.4-audit-check.md`](../../plans/v0.5.4-audit-check.md)): judgments, not
frozen rules or measured probabilities. Against the second half's records:

1. **T2a's non-fixable losses exceed B's margin.** 20 losses that no procedure fixes, under the
   stated rules and assumptions, against a margin of 7. This was foreseeable from the known
   marginals and is not a new demonstration of infeasibility.
2. **No route for D1's fatal class was found by the density test**, under its design (step 3).
3. **D2's joint floor is met only at the upper counts.** `F_upper` is 21 and step 7's upper
   count is 27, against 22. The strict and rule floors are 8, 16 and 11. This criterion is
   therefore not met on the strict reading.

Steps 5 and 6 opened no estimator route; both are `INCONCLUSIVE`. T3b adds a counted shortage of
9 confirmation stars.

**What this recommendation does not claim:**
- three demonstrated criteria;
- a universal impossibility or a formal infeasibility;
- any confirmation or validation of the battery.

The section 6 figures ("more than 3,500 CPU-h", "four simultaneous estimators", "well below one
half") are not measurements or frozen rules. An infeasibility record, an amendment to the
sampling frame and step 8 are the maintainer's.

**Open for the maintainer:** step 4's stop (63 of 77 shards), and the decision between going on
and pausing. The pause is set for 2026-11-18 20:00. Work resumes only on the maintainer's
release, after the publication of 2026-11-19.
