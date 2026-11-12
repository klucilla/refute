# v0.5.3 stage B, B1: the stop report

**For the maintainer's decision; nothing is decided here.** The maintainer's decisions of 2026-11-11
(#217) approved B1 (D2, D4 and T2a with a candidate version 5) and asked for a stop at its end. This
is that stop. It also carries a **second stop, not delegated**: B1.4's D2/D4 part reached its cap
before it finished. `method_status: not_validated`. Development data only. Nothing in `src/` or in
T2a's v0.5.2 fingerprint changed. No confirmation data was drawn or used, no drand round ran, and
nothing was accepted or calibrated.

## What ran

| Step | Records | CPU-h |
|---|---|---|
| B1.1, three smoke parts (the maintainer's split) | `b1-smoke-d2.json`, `b1-smoke-t2a.json`, `b1-smoke-above20.json` | 0.24 (plus 0.016 of the first smoke's stop) |
| B1.2, the screen on v0.5.2's 112 D2 planets | [`b1-screen.json`](b1-screen.json) | 4.79 |
| B1.3, the recalibration screen (450 C1 nulls, 13 E4 hosts) | [`b1-recal.json`](b1-recal.json), [`b1-composition.json`](b1-composition.json) | 1.25 |
| B1.4, the fetch of T2a's 84 hosts | [`b1-fetch-t2a.json`](b1-fetch-t2a.json) | 0 (1.27 GB, 212 MB downloaded) |
| B1.4, D2/D4 on C1 P indices 3000 to 3199 | [`b1-forecast.json`](b1-forecast.json), `d2_d4` | 7.09, **stopped at its cap** |
| B1.4, T2a's census of 615 injections | [`b1-forecast.json`](b1-forecast.json), `t2a` | 34.25 (5.37 + 20.54 + 8.34) |
| B1.4, the blockers of T2a (a diagnostic) | [`b1_t2a_blockers.py`](b1_t2a_blockers.py), [`b1-t2a-blockers.json`](b1-t2a-blockers.json) | negligible |

Each step's exact procedure was posted on #217 before it ran, and its code was reviewed by Codex
(the [consensus record](../../../plans/v0.5.3-consensus/README.md)).

## The stop of the D2/D4 part (not delegated)

The driver stops a part once it has spent 1.5 times its frozen projection (`budgeted.execute`). The
projection came from 10 checkpoint curves: 4.67 CPU-h for 200 curves, so the part's cap was
min(1.5 × 4.67, 19.09) = 7.01 CPU-h. The 181 curves done cost 7.03 CPU-h, 0.039 CPU-h per curve,
1.68 times the checkpoint's rate. The part stopped at 7.09 CPU-h with **181 of 200 curves done** and
no error. The stop is in the ledger (`unresolved_stop`). It was not reconciled or resumed.

`b1_b14.summarize` read the 181 records with the checked partial read (each shard against its
sidecar: fingerprint, argument and SHA-256). By the rule fixed before the run, an incomplete part's
D2 and D4 are **NOT DECIDED**. The counts below are that partial read.

**Why it spent slightly more than the cap:** the driver stops dispatching new work at the cap and
lets the work already in flight finish. The completed shards hold 7.03 CPU-h. The rest of the 7.09
is accounting beyond the work recorded in the results.

**What completing it would take:** reconciling the stop and resuming the 19 curves left.

- **Cost:** about 0.75 CPU-h, extrapolated from the cost per curve, and about 10 minutes of wall
  clock (an estimate).
- **Approval:** it needs a new cap. It is a rerun outside the plan, so it is the maintainer's to
  approve, with its procedure on #217 first.
- **What it could change:** completing it could decide D2, since a rescue is still arithmetically
  possible (next section). D4 would stay under 0.30 even in the worst case: 25 of 131 is 0.191.
- **What it cannot change:** T2a's result, D1's lack of a route, or round 3's outcome.

## 1. The forecast against the minimums

### D2 and D4 (181 of 200 curves; NOT DECIDED)

162 curves are eligible, and 112 of them are in D4's subset (target SNR 15 or more). D2's minimum is
v0.4's kept fraction minus 0.10, which is 0.869 on these curves.

| Battery | Kept (of 162) | Kept fraction [Wilson 95 %] | REFUTED (Wilson upper) | D4: INCONCLUSIVE (of 112) |
|---|---|---|---|---|
| v0.4 | 157 | 0.969 [0.930, 0.987] | 4 (0.062) | 1 |
| Version 4 | 131 | 0.809 [0.741, 0.862] | 2 (0.044) | 6 |
| **Version 5** | **130** | **0.802 [0.734, 0.856]** | 3 (0.053) | 6 |

- **D2:** version 5 keeps 0.802 against the minimum of 0.869. Its REFUTED fraction and Wilson upper
  end are inside the rule.
- **The 19 curves not run:** the kept rule is `kept5 − kept_v0.4 ≥ −0.10 n`. On the 162 read it
  stands at −27 against −16.2. Passing at 181 eligible would need version 5 to keep at least 9 more
  of the 19 than v0.4 does, after keeping 27 fewer on the 162. That is not excluded arithmetically.
- **D4:** 6 of 112 under version 5, against the 0.30 allowed.
- **Version 5 against version 4:** on these new curves they keep 130 and 131. The estimators did not
  move D2.
- **Version 5's blockers** among the eligible curves it loses (one curve can carry several):
  - INCONCLUSIVE: `event_consistency` 31, `duration_excess` 27, `odd_even` 23, `sinusoid` 21,
    `centroid_shift` 17, `period_alias` 1;
  - FAIL: `period_alias` 2, `duration_excess` 1, `odd_even` 1, `systematics` 1.

### T2a (the census: 615 injections, complete)

v0.4 reproduced every injection's record. It keeps 613 of 615, so the minimum is 0.897, or 551.5
injections: at least 552 of B's 559.

| Configuration | 2 to 4 sectors (302) | 5 to 20 (257) | Above 20 (56) | Kept of 615 |
|---|---|---|---|---|
| A (as built) | 162 | 0 (the selector refuses: not certified) | lost by the refusal rule | 162 |
| **B** (C up to 20, A above) | 162 | 169 | lost | **331** |
| C (the selector treated as certified) | 162 | 169 | 42 | 373 |

- **The answer, by the rule fixed before the run: no.** `K_B` is 331 and `U_B` is 0, so
  `K_B + U_B = 331 ≤ 551`.
- **Certification above 20 cannot rescue T2a:** C's upper end over 615 is 373 ≤ 551.
- **Against v0.5.2:** version 4's B was 0.313 on a weighted sample of 80. Version 5's B is 0.538 on
  the census. The kept fraction rises, but it stays 221 injections short of the minimum.

**What blocks it** ([`b1-t2a-blockers.json`](b1-t2a-blockers.json), configuration B, 2 to 20
sectors).

- **Lost:** 228 of 559. v0.4 kept 226 of them.
- **Blockers among those lost.** These leave out the stage's deferred tests, `aperture_depth` and
  `centroid_shift`, which are INCONCLUSIVE in every record, kept or lost, v0.4's included.
  - INCONCLUSIVE:
    - `duration_excess` 217, all `insufficient_sensitivity`;
    - `event_consistency` 188;
    - `systematics` 171;
    - `sinusoid` 96;
    - `odd_even` 86;
    - `single_event` 42;
    - `period_alias` 16.
  - FAIL:
    - `nearby_contamination` 68;
    - `event_consistency` 5;
    - `period_alias` 5;
    - `odd_even` 4;
    - `systematics` 3;
    - `single_event` 1.
- **The selector's refusals:** 42 of the losses are injections the selector refused as "outside the
  grid".
- **Single blockers:** only 5 of the 228 have a single blocker (`systematics`, all 5). The others
  have two or more.

Version 5's estimators act on `odd_even`, `sinusoid` and `systematics`, and on the variance behind
the A0-dependent tests. `duration_excess` and `event_consistency`, the two most frequent blockers,
are outside them.

**A defect, disclosed:** `b1_b14.t2a_summary` compared each test's entry, which is a dict, with a
status string, so the `blockers` field of `b1-forecast.json` is empty. The answer, `K_B` and `U_B`
read the stage verdict and are unaffected. `b1_b14.py` is in the census's fingerprint and was left
unchanged. The diagnostic reads the same verified records.

### The estimators (B1.3, an exploratory veto, not a calibration)

| Estimator | Null contrasts | Result | Note |
|---|---|---|---|
| E1, the Cauchy-Schwarz completion | 7 | UNRESOLVED (too few) | used wherever version 4's `group_variance` refuses |
| E2, the joint GLS odd/even contrast | 316 | SD 1.007 [0.90, 1.14] PASS; mean and tail UNRESOLVED | |
| E3, the ARMA(1,1) GLS | 51 of 339 eligible (288 fallbacks) | UNRESOLVED | **SD 1.35 [1.045, 1.87]: the point estimate suggests an underestimated error** |
| E4, the window-local quadratic baseline | 1 | UNRESOLVED | the overlap rule left 2 proposals in 13 hosts, so the screen carried no information |

None had a FAIL, so B1.4 ran with all four (`b1-composition.json`). E3 falls back on most curves:
81 of 112 in B1.2, with `gamma1` or `gamma2` not positive or φ outside (0, 0.99).

## 2. T2a's answer, and the price of certifying the selector

**The answer is no.** The margin does not exist without certifying the selector above 20 sectors, and
certifying it above 20 would not create it.

| Certification | Design | Price |
|---|---|---|
| Up to 20 sectors (owed by B, and by any acceptance) | v0.5.2's selector evaluation (its design, section 2); the family is not designed | about **135 CPU-h**, v0.5.2's estimate: about 770,000 curves at 0.3 to 0.8 CPU-s; about 0.7 days of wall clock |
| Above 20 sectors | the same evaluation, extended with constructions of 25, 30, 40 and 60 sectors | about **380 CPU-h**, scaled from the census. No battery was timed on its own, so this is each part's total cost divided by its number of batteries: about 267 CPU-s per injection and battery above 20 (mean 27.7 sectors) against about 95 CPU-s from 5 to 20 (mean 8.7), about 2.8 times. Multiplying 135 by 2.8 assumes a family the size of the one up to 20. That is an estimate, not a measurement, and about 1.8 days of wall clock. **It buys nothing for T2a** (C keeps 373). |

## 3. The plan and price of the acceptance and the confirmation

**Round 3's closing criterion** is the one the stage A report proposed. The B1 design (section 5)
applies it.

- Its item 2 applies: the forecast does not pass T2a, and "a rule that is NOT DECIDABLE … counts as
  not passed", which covers D2/D4.
- Its item 3 applies too: a cap was reached with the forecast not done.
- D1 has no route.

So the round closes **without acceptance**. The price below answers the maintainer's question. It is
not a proposal to run.

| Line | CPU-h | Basis |
|---|---|---|
| The rest of v0.5.2's stage-2 schedule, A0 acceptance included | 2,824 to 3,446 | v0.5.2's `budget.md`, with the known-answer rescaling, less the 163 spent there. The low end is the point-estimate sizing (2,987). The high end is the sizing with Bonferroni over the family (3,609). Version 3's schedule (2,956) is left out: it is a reference that fails the adequacy check, not an option. The A0 line (1,505 to 1,932) is a **provisional inherited reference, not a repricing**. On D2 curves, B1.4's three batteries cost 140 CPU-s per curve and v0.5.2's 145 (4.85 CPU-h for 120 curves). Those compare whole workloads on different curves. They do not isolate version 5's increment, and they do not measure cost or availability per cell of A0's family. |
| Calibration of E1 to E4 by the acceptance's rules | about 206, plus E4; **not a sizing** | B1.3's yields at its measured 10 CPU-s per null curve, with 1,000 contrasts per estimator **as an illustration of scale only**: E2 about 4 (1,424 curves), E3 about 24 (8,824), E1 about 178 (64,286). The family, its sizing and its delivery criterion are not defined. **E3 delivers 51 of 339 eligible (15 %).** More curves at that yield do not meet the screen's 80 % availability requirement, so E3's calibration is a design problem, not only a price. E4 cannot be priced without a redesign of its null: the overlap rule left 2 proposals. |
| The port into `src/` | under 5, plus 1 to 2 agent-days | tests and Codex reviews; an estimate |
| The confirmation (C1', C2', C3'; v0.4 and version 5) | at least about 33; **not priced in full** | **D2/D4:** about 5 for 200 curves at two batteries, from 0.039 CPU-h per curve at three. **T2a:** about 27 for 615 injections at two batteries. The 2-to-4 stratum already ran two batteries, since C reuses A, so only the 5-to-20 stratum is discounted. 615 is the denominator after recovery, not the whole workload of C2'. **D1 and C3:** unmeasured. The draws need drand rounds. |
| **Subtotal still to spend, without the certification above 20** | **about 3,068 to 3,690, plus E4 and the components not yet sized** | a provisional subtotal with no established upper bound. With the 163 spent in v0.5.2's stage 2, the cumulative total is 3,231 to 3,853, over v0.5.2's hard maximum of 3,100, so it would need a new cap. |
| With the certification above 20 | about 3,448 to 4,070, plus the same | cumulative 3,611 to 4,233 |

**The wall clock, on the real calendar.**

- **The rate:** 12 workers off business hours deliver about 11.4 CPU-h per hour. In business hours,
  10 workers deliver about 6 (v0.5.2's measured placement).
- **Before the pause:** from 2026-11-12 03:00 to the pause on 2026-11-18 at 20:00 there are 111 hours
  off business hours and 50 in them, at most about 1,565 CPU-h of compute if it all ran from now.
- **What fits before it: no acceptance is authorized in this state.** Compute could physically run,
  but nothing may start before:
  - the maintainer's approval and a new cap;
  - the port into `src/`, with its reviews;
  - E4's redesign and the calibration's design;
  - the selector family's design;
  - for the confirmation, the drand rounds.
- **After a release on 2026-11-19 at 00:00** (a hypothesis: the release is not automatic), continuous
  compute at the declared rates, with no development time and no E4:
  - about 3,068 CPU-h end about 2026-12-02 (13.0 days);
  - about 3,690 CPU-h end about 2026-12-04 (15.9 days);
  - with the certification above 20, 3,448 to 4,070 CPU-h end about 2026-12-03 to 2026-12-06 (14.8
    to 17.2 days).

  Development time comes on top of these.

## 4. T3b: the recommendation among A, B and C

v0.5.2's record ([`stage2/t3b-status.md`](../../v0.5.2/stage2/t3b-status.md)) concludes "none as
written". B1 does not reverse that. The question here is which definition to qualify, if one is to be
qualified.

**The recommendation: A** (the TESS disposition EB, without nearby-source text). It would be added
to the approved frame, not replace it, and only after qualification:

- positive, attributable evidence that the target eclipses;
- a frozen conflict rule: nearby-source evidence, or an unresolved identity or period, makes a star
  ineligible;
- an independent human adjudication, with its rubric and acceptance criterion fixed first.

The qualification happens **before any of Refute's results** and carries the safeguards that
`t3b-status.md` lists for the union:

- one deduplicated order, with its seed and exclusions frozen before selection;
- the proxy never used as an exclusion;
- memberships and contradictions recorded per source;
- the disclosure that the amendment is prospective, not blinded.

**The argument of class preservation.** After qualification, the adjudication is what controls
contamination. The screening set's job is then to lose as few true members of the class "the target
is the eclipsing binary" as possible. On that criterion:

- **A is the widest set:** 165 never walked, 39 passing the proxy.
- **A needs the lowest retention to reach 11:** about 64 %, against 68 % for B and 81 % for C, under
  the assumption that the passing stratum's rate of 11 of 25 holds.
- **A drops the fewest members of the approved frame if used alone:** 23, against 35 for B and 36 for
  C.
- **B is weaker evidence:** it rests on a lexical match in the TOI comments, which is weaker
  provenance than a disposition.
- **C buys no demonstrated purity:** it intersects correlated information without adding
  localization, so its smaller size buys none and loses members.

These counts justify a **planning preference**. They do not show that A preserves more true members
or admits less contamination, and they are not demonstrated purity. A's disposition still does not
say which star eclipses, which is why qualification is the condition.

**The price of the qualification.**

- **CPU:** close to zero. Metadata only: TESS's 120-s target lists and the TIC.
- **Agent work:** 1 to 2 agent-days, an estimate. That covers the rubric, the reproducible sample,
  the frozen rule, the deduplicated order and its seed.
- **Human time:** the adjudication of up to 165 stars and their conflicts. This is the main cost. It
  is not measured.
- **An open condition:** ExoFOP's data use policy, wherever TFOP notes are used as evidence.

## 5. D1's state for the closing of round 3

- **B0:** outcome C. The information bound does not settle D1 under the catalog star.
- **B0b:** outcome N. The pre-registered infeasibility criterion was not met. At 0.05 the median
  pass probabilities were 0.452 (EB1) and 0.102 (EB2), not below 0.05.
- **No route this round.** D1 stays pending. No relaxing of the target is proposed.

## 6. The consumption

| Cap | Used | Sub-cap | Stage B cap |
|---|---|---|---|
| CPU-h | 52.566 in all | B0 4.923 of 30; B1 47.643 of 120 | 150 |
| Review tokens (Codex, uncached input plus output, the last turn of each conversation) | 1,654,304: 1,476,133 before the end-of-B1 review, which counts 178,171 (its two rounds, in the consensus record) | B0 489,509 of 1.5 M (stop at 1.2 M) | 4.5 M (stop at 3.6 M) |
| Independent review sessions | 0 | | (within the 4.5 M) |
| Agent-days, measured at 2026-11-12 05:46 UTC | 0.71 active; 1.85 as the wall-clock bound | B0 2 | 8 |
| Disk under `.cache/v053/stageB/` | 1.456 GB | | 5 GB |

**Each part** (`ledger.json`; the effective cap is the smaller of 1.5 times the frozen projection and
the part's hard cap):

| Part | Allocation | Spent | 1.5 × projection | State |
|---|---|---|---|---|
| `b0_bound` | 4.0 | 2.448 | 3.55 | complete |
| `b0_infeasibility` | 4.0 | 2.451 | 3.34 | complete |
| `b1_smoke` | 1.0 | 0.016 | 0.01 | **stopped over its cap** (the workers were ended); the maintainer's split replaced it |
| `b1_smoke_d2`, `b1_smoke_t2a`, `b1_smoke_above20` | 0.5, 0.5, 1.0 | 0.005, 0.070, 0.166 | 0.01, 0.11, 0.25 | complete |
| `b1_screen` | 6.0 | 4.793 | 8.21 | complete |
| `b1_recal_c1`, `b1_recal_e4` | 8.5, 1.5 | 1.246, 0.007 | 1.91, 0.01 | complete |
| `b1_forecast_d2d4` | 14.0 | 7.093 | 7.01 | **stopped: the cap is reached** |
| `b1_t2a_2to4`, `b1_t2a_5to20`, `b1_t2a_above20` | 18.0, 24.0, 12.0 | 5.375, 20.538, 8.336 | 7.81, 35.66 (hard cap 32.73), 10.57 | complete |
| unallocated: `b0_reserve`, `b1_unallocated` | 21.9, 33.0 | 0 | | |

No cap of stage B and no sub-cap was reached. Two parts reached their own caps: the first smoke,
whose handling the maintainer already decided, and D2/D4, above.

## Decisions for the maintainer

1. **The D2/D4 stop:**
   - leave it, so D2 and D4 stay NOT DECIDED;
   - or approve the reconciliation and the 19 curves, about 0.75 CPU-h.

   Neither changes item 2 of the closing criterion for T2a and D1.
2. **The closing of round 3** under its criterion:
   - change the approach;
   - record infeasibility (the material of stage A, B0, B0b and B1);
   - or pause the line.

   No target is relaxed.
3. **T3b:** whether to qualify A as above, and with whose adjudication.

## Disclosures

- **The D2 smoke index:** B1.1's D2 smoke saw index 3000, which is inside B1.4's interval. This was
  disclosed before the run.
- **The above-20 smoke:** while it ran, its driver file was edited. It was revalidated read-only
  under its own fingerprint (`revalidate_above20.py`), and this was disclosed on #217.
- **The checkpoint projection:** D2/D4's checkpoint of 10 curves underestimated the cost per curve
  by a factor of 1.68.
- **The T2a projections:** the estimates for T2a's 5-to-20 part, 23.8 projected and 20.5 spent, and
  for the part above 20, 7.0 projected and 8.3 spent, stayed inside their caps.
