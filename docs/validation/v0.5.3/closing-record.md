# v0.5.3 Battery corrections, round 3, ended as not approved (2026-11-12)

**For the maintainer's decision; nothing here is decided by Claude or Codex.** Round 3 is the last
correction round of the advance rule (ROADMAP, "Advance rule"). It closes **not approved** by the
criterion fixed in stage A's report ([`stageA/README.md`](stageA/README.md), "Round 3's closing
criterion"), by **item 2**: T2a and D2 fail their frozen rules. B1.4's D2/D4 part stopped at its
cap; that stop is recorded as a fact, and the part was completed afterwards with the maintainer's
approval. *[The maintainer's correction of 2026-11-12, afternoon (#217): the morning decision
applied item 3 to that part's cap; item 3 concerns a cap reached with the forecast not done, and the
forecast was completed, so that application is withdrawn.]* Every measured number below comes from a committed file of
`stageA/` or `stageB/`, produced by a script reviewed by Codex before its run, with its approval and
exact procedure posted on #217 before it ran. Stage A's one exception, a smoke run outside the
ledger, was disclosed there. Prices and the rough development price are estimates, marked as such.
Development data only; no confirmation set exists or was touched; no drand round was drawn; no lock was made; no real target was selected; nothing in `src/`
changed. `method_status: not_validated`. No target is relaxed. The ROADMAP changes only after the
maintainer approves this record.

**This record was revised on 2026-11-12 (afternoon)** by the maintainer's decision of that day
(#217):
- **The independent review's corrections.** The review read commit `40aa485`, and its report,
  [`closing-review.md`](closing-review.md), is unchanged. Its nine points (section 5) are applied,
  each marked as the review's. Codex checked each one against the annexes, and its answer per point
  is in the [table below](#the-independent-reviews-points-and-codexs-check).
- **The review's own answer** and its proposed order for a change of approach are in a section of
  their own, as the review's, not adopted.
- **The maintainer's correction** on item 3, marked as the maintainer's.

## What led here

- **The advance rule** (ROADMAP): a new capability phase starts only when every declared target
  of the line either PASSes or is shown infeasible, with one infeasibility record per target. After
  three correction rounds without success, the maintainer decides between a change of approach, an
  infeasibility record, or a pause.
- **v0.5.1 and v0.5.2** (rounds 1 and 2) closed not approved; see
  [`../v0.5.2/closing-record.md`](../v0.5.2/closing-record.md).
- **The outstanding targets** at round 3's start: **D1** for EB1 and EB2, **D2**, **D4** and
  **T2a**, each with its frozen rule (`calib05.c1.decision_rules`; v0.5's T2a rule). T3b was open as
  v0.5.2 left it ("none as written").
- **Round 3** ran in two stages, each approved by the maintainer on #217:
  - **Stage A** produced bounds, audits and diagnoses ([`stageA/README.md`](stageA/README.md)).
  - **Stage B** ran three steps ([`stageB/`](stageB/)):
    - **B0:** D1's information bound ([`stageB/README.md`](stageB/README.md));
    - **B0b:** D1's pre-registered infeasibility test ([`stageB/b0b-record.md`](stageB/b0b-record.md));
    - **B1:** a candidate battery version 5 with four estimators, and the development forecast of D2,
      D4 and T2a ([`stageB/b1-stop-report.md`](stageB/b1-stop-report.md) and its
      [addendum](stageB/b1-stop-report-addendum.md)).

## The closing criterion, as it applies

The criterion of stage A's report. Round 3 closes at the first of four items:

| Item | Applies? | Why |
|---|---|---|
| 1. Approved: the forecast passes D1, D2, D4 and T2a, then acceptance and confirmation pass | no | T2a does not pass, and D1 has no route |
| **2. Not approved, forecast:** an outstanding target fails its frozen rule, or is NOT DECIDABLE | **yes: T2a**. Also D2, which FAILs on the completed part, and D1, which has no forecast and so is not passed | T2a's `K_B` is 331, against 552 needed. D2 version 5 keeps 141 of 178, against at least 156 |
| 3. Not approved, stage B: no estimator survives, or a cap is reached with the forecast not done | **no** *[the maintainer's correction, afternoon]* | the part `b1_forecast_d2d4` stopped at its cap with 181 of 200 curves. The cap was reached at 181 of 200, a fact kept in the ledger. The forecast was completed afterwards with approval, which makes the application of item 3 to that part's cap of no effect, without undoing the event. No stage cap was reached. The morning decision's application of item 3 to that part's cap is withdrawn |
| 4. Not approved, the maintainer's | not invoked | |

## The state of each target

| Target | Frozen rule | State at the close | Source |
|---|---|---|---|
| **D1, EB1 and EB2** | the SURVIVED fraction's Wilson 95 % upper end at most 0.10, and no more SURVIVED than v0.4 | **pending, no route.** B0 gave outcome **C**: under the catalog star the bound does not settle it. The oracle leaves an expected 29.2 (EB1) and 35.5 (EB2) non-rejected at the primary level against an allowance of 10; with the star known, 11.9 and 11.2. B0b gave outcome **N**: the pre-registered infeasibility criterion is not met (median pass probabilities 0.452 and 0.102 at 0.05, not below 0.05). Stage A's geometric route (d) did not separate the binaries | `stageB/README.md`, `stageB/b0b-record.md`, `stageA/README.md` (d) |
| **D2** | kept fraction ≥ v0.4's minus 0.10; REFUTED ≤ 0.05 and its Wilson upper end ≤ 0.10 | **FAIL** on the completed part: 200 new C1 planets, 178 eligible. v0.4 keeps 173, so the minimum is 0.872. Version 5 keeps 141 (0.792 [0.727, 0.845]), with 3 REFUTED (Wilson upper end 0.048). Version 4 keeps 142. Disclosed: the part stopped at its cap at 181 of 200 curves, a stop kept on file, and was completed with the maintainer's approval (0.707 CPU-h, no new stop) | `stageB/b1-forecast-d2d4-complete.json`; `stageB/b1-stop-report-addendum.md` |
| **D4** | INCONCLUSIVE fraction at target SNR ≥ 15 at most 0.30 | **PASS** in this forecast: version 5 has 7 of 122 INCONCLUSIVE (0.057). It passed in v0.5.2's forecast too (0.122). A forecast is not an acceptance: D4 stays to be accepted with the others | the same |
| **T2a** | kept fraction ≥ v0.4's minus 0.10, so 0.897 of 615 (551.5) | **no**, by the census rule fixed before the run: `K_B` 331 and `U_B` 0 of 559, against at least 552. C, with the selector treated as certified above 20, keeps 373 of 615, so certification cannot rescue **version 5's** forecast. For a change of approach it is T2a's margin lever: C keeps 42 of 56 above 20 sectors, which raises the losses allowed on 2 to 20 sectors from 7 to about 49 (559 − 510). *[The independent review, [`closing-review.md`](closing-review.md), section 5, item 1.]* | `stageB/b1-forecast.json`; the counts are recomputed in `stageB/b1-blockers-decisive.json` |
| **T3b** | the EB truth population (v0.5.2: "none as written") | **not executed** in round 3. The recommendation is **A**, added to the approved frame, conditional on qualification; it is pending the maintainer's decision. The qualification costs close to zero CPU and 1 to 2 agent-days; the human adjudication of up to 165 stars is not measured, and ExoFOP's data use policy is an open condition | `stageB/b1-stop-report.md`, section 4 |

## Stage A's limits (bounds, not attainability)

- **D2: room.** Kept retention's upper bound is 111 of 112, and the evidence-qualified bound is 108,
  against the 97 required.
  - The bound rests on Gaussian noise with the generator's covariance, a joint Fisher bound for
    `odd_even` and the oracle GLS residual for the sinusoid.
  - Three planets stay below 0.95 even for the oracle sinusoid residual.
- **T2a: narrow room, and not an information bound.** The upper bound is 0.909 with the stratum
  above 20 sectors all lost, and 1.0 with it all kept, against 0.897. It is a recoverability count by
  rule ("every blocker of the 51 losses is recoverable"), on v0.5.2's 51 losses, not a bound on
  information like D2's. So its room is weaker than D2's. *[The independent review, [`closing-review.md`](closing-review.md), section 5, item 2.]*
  - With the selector's refusal above 20 sectors kept as a rule, at least 552 of the other 559 must
    be kept, which leaves 7 injections of room.
- **The background's error.** A0's error on the background rise is a median 23.2 times the white
  error, dominated by the series' slow variability (c1).
- **A0's refusals** are lag correlations with fewer than 20 window pairs, or a covariance that is
  not positive semi-definite (a).
- **D1:** no bound from stage A. Its geometric route flagged at most 2 of 279 EB2 binaries and none
  of EB1.

An information bound is not attainability, and its absence is not infeasibility. Stage A recorded
no draft infeasibility record, and B0 and B0b add none.

## What blocks D2 and T2a (decisive blockers only)

The stop report's blocker lists counted diagnostics and warning FAILs as blockers. The corrected
counts are in the [addendum](stageB/b1-stop-report-addendum.md) and in
`stageB/b1-blockers-decisive.json`. They count only what the verdict aggregates: the gate, fatal
FAILs, and decisive stage tests INCONCLUSIVE or missing. T2a's answer, `K_B` and `U_B` are
unaffected.

**T2a, configuration B (228 losses of 559):**

| Test | Losses it blocks | As the only blocker | Estimator of version 5, where the test blocks |
|---|---|---|---|
| `systematics` | 169 (107 insufficient sensitivity, 42 grid refusals, 20 not enough data) | 72 | E4 measured in 110, was called without completing a measurement in 17, and was not reached in 42 |
| `sinusoid` | 95 (insufficient sensitivity) | 29 | **E3 operated in none**: it fell back in all 95 |
| `odd_even` | 89 (43 insufficient sensitivity, 42 grid refusals, 4 FAIL) | 9 | E2 operated in 35, fell back in 12, and was not reached in 42 |
| `period_alias` | 17 | 11 | none |

- 121 losses have a single decisive blocker.
- 42 are refusals of A0's grid: measured events outside 2 to 4 sectors.
- **A what-if, not a forecast:** removing whole blocker classes recovers
  - 72 (`systematics`);
  - 124 (with `sinusoid`);
  - 211 (with `odd_even`);
  - 228 (all four).

  T2a needs 221 of them, so essentially every class at once.

  This what-if also recovers the 5 REFUTED losses (fatal FAILs: 4 `odd_even`, 1 `period_alias`).
  If those five remain REFUTED, B tops out at 554 against 552, so at most 2 of the 223 INCONCLUSIVE losses may
  stay lost. Counted over the INCONCLUSIVE losses only, the recoveries are 72, 124, 207 and 223.
  *[The independent review, [`closing-review.md`](closing-review.md), section 5, item 3.]*

**D2, version 5 (37 losses of 178):**

| Test | Losses it blocks | As the only blocker | Estimator of version 5, where the test blocks |
|---|---|---|---|
| `odd_even` | 26 | 9 | E2 operated in 22 and fell back in 4 |
| `sinusoid` | 25 | 8 | E3 operated in 2 and fell back in 23 |
| `period_alias` | 3 | 3 | none |
| `systematics` | 1 | 0 | E4 called, no measurement completed |

- 17 losses carry both `odd_even` and `sinusoid`: 16 with only those two, and 1 with `systematics` too.
- **No class recorded:** 24 of the 26 `odd_even` and 17 of the 25 `sinusoid` losses are
  INCONCLUSIVE with no class recorded in the D2 records. So these records do not show a sensitivity
  cause for them. *[The independent review, [`closing-review.md`](closing-review.md), section 5, item 6.]*
- **A what-if:** D2 needs 15 more kept. `odd_even` alone recovers 9, `sinusoid` alone 8, and both
  33. So D2 needs both resolved.
- The diagnostics the stop report had counted (`event_consistency`, `duration_excess`,
  `centroid_shift`) never enter the verdict.

## What round 3 built, and how it behaved

B1 built version 5 outside `src/`: four estimators, each Codex-reviewed before its run, and none
calibrated. B1.3's exploratory veto had no FAIL, so all four were used.

- **E1**, the Cauchy-Schwarz completion of A0's group variance: 7 null contrasts, so it is
  uninformative.
- **E2**, the joint GLS odd/even contrast: its SD of 1.007 [0.90, 1.14] passes. It operates on most
  attacks it reaches.
  - **Against the Fisher bound:** in B1.2, on the 31 earlier losses within v0.5.2's 112 planets
    that carry `error_ratios` in `b1-screen.json`, the 28 finite ratios of version 5's `odd_even`
    error to stage A's Fisher bound run from 0.82 to 2.12, with a median of 1.44. They are almost
    the same as version 4's where both exist. This is not a measurement over all 112 planets. The B1 design did not claim to reach that bound, which
    assumes the true template.
  - **B1.2's gain** on those planets (81 to 86 kept) did not carry over to the 178 fresh planets
    (142 to 141). *[The independent review, [`closing-review.md`](closing-review.md), section 5, item 4.]*
- **E3**, the ARMA(1,1) GLS of the sinusoid's residual: it delivered 51 of 339 eligible in B1.3. Its
  SD is 1.35 [1.045, 1.87], a warning. It falls back on 547 of 559 T2a attacks of B and on 149 of
  178 D2 attacks (φ outside (0, 0.99), or autocovariances not positive). So **the sinusoid's T2a losses are all version 4's computation**,
  and 23 of its 25 D2 losses are.
- **E4**, the background sub-check's window-local quadratic baseline: its null screen carried no
  information (2 eligible proposals, 1 contrast, availability 0.0). *[The independent review, [`closing-review.md`](closing-review.md), section 5, item 9.]* It measured in 110 of the 169 T2a losses that `systematics` blocks, and
  `systematics` stayed INCONCLUSIVE in each. The records do not show which of its sub-checks
  kept it so.

**Against version 4:**
- **D2:** version 5 keeps 141 of 178, and version 4 keeps 142.
- **T2a:** version 5's B is 0.538 on the census, against version 4's 0.313 on v0.5.2's weighted
  sample of 80. The two are not the same sample.
- **Where version 5 moved T2a,** this record does not attribute it to an estimator.
- **On D2,** the four estimators together did not improve retention: 142 with version 4, 141 with version 5.

## The prices (for information; nothing is proposed to run)

From the B1 stop report (sections 2 and 3). Every figure is provisional:

| Line | CPU-h |
|---|---|
| The selector's certification up to 20 sectors | about 135 |
| The selector's certification above 20 sectors (it buys nothing for version 5's T2a forecast; for a change of approach it is T2a's margin lever, item 1 of the review's section 5) | about 380 |
| What remains of v0.5.2's acceptance schedule | 2,824 to 3,446 |
| The estimators' calibration (an illustration of scale; E4 unpriced; E3's availability is a design problem) | about 206 |
| The port into `src/` | under 5, plus 1 to 2 agent-days |
| The confirmation, not priced in full | at least about 33 |
| **Subtotal still to spend** (without the 380 above 20; the 135 up to 20 are already inside v0.5.2's inherited schedule) | **about 3,068 to 3,690**, plus E4 and unsized components: a provisional subtotal with no established upper bound |
| Cumulative, with the 163 that v0.5.2's `stage2/budget.md` counted as spent (its budget's base; v0.5.2's closing record reports 179.5 CPU-h for stage 2 in all, the forecast and diagnoses included) | 3,231 to 3,853, over v0.5.2's 3,100 |

None of this is authorized in the current state.

Calendar: 12 workers off business hours give about 11.4 CPU-h per hour; 10 in business hours give
about 6.

## The three options of the rule (for the maintainer's decision)

### 1. Change the approach

A new battery version, built prospectively. The targets and the rule of evidence are unchanged; it
would be accepted only on fresh data outside development. In the order the decisive blockers
suggest:

1. **`systematics`' background sub-check** (T2a: 169 losses, 72 as the only blocker; D2: 1).
   - **The finding:** E4's local baseline measured in 110 of these losses and `systematics` stayed
     INCONCLUSIVE; the records do not show which sub-check kept it so, and that needs a diagnosis
     first. Stage A (c1)
     found the background error dominated by slow variability.
   - **What to try:** a noise model of the background series with an exact likelihood on gapped
     data, then the rise tested against that covariance. Candidates are a state-space ARMA through
     a Kalman filter (Jones 1980) or a celerite-type Gaussian process (Foreman-Mackey et al. 2017).
   - **What must come first:** an information bound under that model on T2a's hosts. That is v0.5.2's
     lesson 5: check a power requirement against the population's noise before building.
   - **Price:**
     - about 2 to 10 CPU-h and 2 to 3 agent-days for the bound (v0.5.2's estimate, unmeasured);
     - then an estimator, a screen and a calibration, of the order of tens of CPU-h;
     - unpriced beyond that.
2. **The sinusoid's residual** (T2a: 95 losses, 29 as the only blocker; D2: 25 losses, 8 as the only blocker, E3 operating in 2 of them).
   - **The finding:** E3's moment estimates fail on almost every curve. 17 of D2's 25 `sinusoid`
     losses have no recorded class, so their cause is not shown. *[The independent review, [`closing-review.md`](closing-review.md), section 5, item 6.]*
   - **What to try:** a maximum-likelihood fit of the same noise family on the gapped series (Kalman,
     Jones 1980), or a Gaussian-process kernel. Gate its availability against B1.3's 80 % requirement
     before any calibration.
   - **The limit:** stage A's bound already shows three D2 planets below 0.95 even for the oracle
     residual.
   - **Price:** of the order of B1's development, about 20 to 40 CPU-h; unmeasured.
3. **A0's coverage** (T2a: 42 grid refusals, which block `odd_even` and `systematics`).
   - **What to try:** extend A0's domain beyond measured events in 2 to 4 sectors, and certify the
     selector up to 20 sectors.
   - **Price:** about 135 CPU-h for the certification, plus the extension's development.
   - **The certification above 20 sectors,** about 380 CPU-h (an estimate), belongs here too, as
     T2a's margin lever. It changes T2a's need from all four blocker classes, with a margin of about
     2, to three classes, with a margin of about 28. *[The independent review, [`closing-review.md`](closing-review.md), section 5, item 1.]*
4. **`odd_even`'s sensitivity** (T2a: 43 insufficient sensitivity outside the refusals; D2: 26 losses, 9 as the only blocker. There E2 operated in 22, and `odd_even` stayed INCONCLUSIVE in 21 of them and FAILed in 1, so the current E2 was not enough there; that does not show that every better contrast would fail).
   - **The finding:** E2 operates where it is reached. In B1.3 only its SD criterion passed; its mean and tail stayed UNRESOLVED.
   - **What to try:** use E2's joint contrast where it applies, and widen its domain with A0's.
   - **On this evidence** E2 alone would not close the gap: its error is 0.82 to 2.12 times the
     known-template Fisher bound (median 1.44, 28 finite ratios). And D2's `odd_even` losses mostly have no recorded class, so a
     sensitivity cause is assumed, not shown. *[The independent review, [`closing-review.md`](closing-review.md), section 5, item 4.]* *[The independent review, [`closing-review.md`](closing-review.md), section 5, item 6.]*
5. **`period_alias`** (T2a: 17). Not addressed in round 3. It needs its own diagnosis.

**Before choosing,** three design questions stay open. They were recorded before stage A's first
run ([`v0.5.3-design-questions.md`](../../plans/v0.5.3-design-questions.md), `7896ba7`), and only the
maintainer can weigh them:

- whether a warning test's INCONCLUSIVE should block a verdict;
- the background sub-check's alternative (0.8 of the depth at power 0.95);
- the sinusoid's small-residual requirement.

These are test rules, not targets. Any change applies only to a new battery version, prospectively,
and they are listed here as open, not as proposals.

**D1 needs a new route** before any forecast. B0 points at the star's density, which the catalog
radius and mass errors blur. A route would need information beyond the light curve and a catalog
star with 5 % errors, or a test whose power survives them; none is designed. Severity matters too.
D1 counts SURVIVED only, and warning-severity tests exist (`secondary_eclipse` is one). So a warning
FAIL keeps a binary out of D1's count. Its planet-side price is WEAKENED, which D2 counts as kept,
when no earlier rule of the aggregation gives REFUTED or INCONCLUSIVE. The
quantity missing from B0 and B0b is that planet-side cost, by severity. *[The independent review, [`closing-review.md`](closing-review.md), section 5, item 8.]*

**A rough price for one more round of development** like stage B: 60 to 150 CPU-h and 5 to 8
agent-days, before any acceptance. That is an estimate, not a measurement. It is scaled from round
3's own use: stage A 7.8 CPU-h and stage B 53.3 so far, with about 3 agent-days as stage B's
wall-clock bound. The acceptance and confirmation above come only if a forecast then passes.

### 2. Record infeasibility

**No target has a basis for an infeasibility record now.** The rule asks for evidence that the
target cannot be met with the available data, reviewed by Codex and by an independent review.

| Target | Basis? | Why |
|---|---|---|
| D1, EB1 and EB2 | **no** | B0b's pre-registered criterion was not met (outcome N). Under the catalog star the oracle bound leaves about three times the allowance at the primary level, but that is a bound on one information model. A binary the oracle does not reject is not a SURVIVED: a binary held INCONCLUSIVE does not survive under D1's frozen rule, so the bound's excess does not show that the frozen target cannot be met. The criterion fixed before the run did not declare infeasibility. It is also incomplete: B0 and B0b measured only the binary side. A D1 record would need a joint pre-registered test, with the binaries SURVIVED within the allowance, and no more SURVIVED than v0.4, together with the planet-side rules, for any severity. No number on file addresses that. *[The independent review, [`closing-review.md`](closing-review.md), section 5, item 8.]* |
| D2 | **no** | stage A's bound leaves room: 111 and 108 against 97, on v0.5.2's 112 planets. Under stage A's model, `odd_even`'s losses are the estimator's, not missing information. Version 5's FAIL is on a different sample (178 fresh planets), and the bound was not recomputed there. So the bound leaves room under its assumptions on the 112, without showing attainability, and it was not recomputed on the 178 *[The independent review, [`closing-review.md`](closing-review.md), section 5, item 5.]* |
| D4 | **no** | it passes in both forecasts (0.057 here, 0.122 in v0.5.2), so there is nothing to record |
| T2a | **no** | no bound exists for its dominant blocker. Stage A's "bound" is a recoverability count, not an information bound *[The independent review, [`closing-review.md`](closing-review.md), section 5, item 2.]*. The 7 injections are the margin under the refusal rule, not an infeasibility threshold. The census shows what blocks, not that it cannot be unblocked |
| T3b | **no** | not measured in round 3; its population is "none as written", a problem of definition, not an information limit *[The independent review, [`closing-review.md`](closing-review.md), section 5, item 7.]* |

An infeasibility record for T2a would need a bound on the background sub-check's attainable
error per host, under its declared alternative. It would also need the grid refusals' information
bounded (v0.5.2's closing record).

### 3. Pause the line

- **What it means:** nothing is deleted. The records, ledgers and consensus record stay as they
  are, and #217 stays open with this record.
- **The cache:** the T2a cache (`.cache/v053/stageB/t2a-cache`, 1.27 GB) is kept until the
  maintainer's decision, then archived to the Drive with a SHA-256 manifest, or deleted as
  regenerable.
- **Price:** none.
- **What the advance rule implies:** v0.5's capability stays outstanding, and no new capability
  phase starts.

## The independent review's answer and proposed order (the review's, not adopted)

This section reports the review ([`closing-review.md`](closing-review.md), sections 1, 3 and 4). It
is not adopted: the choice belongs to the maintainer.

- **Does any target have a basis for an infeasibility record?** The review says no, and agrees with
  this record. It finds the reasons sound for D2 and D4, weaker for T2a (no information bound), and
  incomplete for D1 (the binary side alone).
- **Are D2 and T2a reachable by a battery that only passes with evidence?** The review says the
  evidence does not establish it either way.
  - **D2:** it has a model-based room, but attainment is far from it.
  - **T2a:** it has no information bound for its dominant blocker. Its margin is about 2 losses with
    the refusal above 20 sectors kept, and about 28 with the selector certified above 20.
  - The review does not count design questions 1 to 3 as a reachability route, because they lie
    outside the premise of a battery that only passes with evidence.
- **What a change of approach should try first,** in the review's order:
  1. **Log what the records cannot tell:**
     - which `systematics` sub-check holds the 110 losses where E4 measured;
     - D2's missing INCONCLUSIVE classes.
  2. **A per-host bound on the background-rise error** under a fitted model of the slow
     variability, with a pre-registered rule: about 64 of 615 shown unreachable gives a draft
     infeasibility record, and otherwise an estimator target.
  3. **A joint pre-registered D1 test,** with the planet side (P and PG under D2, D3 and D4) for
     fatal and warning severity.
  4. **`odd_even`'s Fisher bound with the transit shape as a nuisance parameter.** A shape-fitted
     contrast comes only if room remains.
  5. **The sinusoid's residual** by exact likelihood on gapped data, with availability gated at 80 %.
  6. **Coverage:** A0's grid, and the selector's certification up to 20 sectors and above 20, the
     latter priced as T2a's margin lever.
  7. **`period_alias`'s diagnosis,** needed only if the stratum above 20 stays refused.

## The independent review's points and Codex's check

Each point is from [`closing-review.md`](closing-review.md), section 5. Codex checked each one
against the annexes and answered accepted, accepted with a caveat, or rejected with the reason. A
rejected point stays here with its reason. Codex's answers are in the consensus record, unchanged.

Codex's check is conversation `b1-revision`, archived unchanged in the consensus record:
[round 1](../../plans/v0.5.3-consensus/b1-revision-round-1-answer.md) (the nine answers) and
[round 2](../../plans/v0.5.3-consensus/b1-revision-round-2-answer.md), and
[round 3](../../plans/v0.5.3-consensus/b1-revision-round-3-answer.md) (`SURVIVED`), with their
SHA-256 in [the consensus README](../../plans/v0.5.3-consensus/README.md) under "The closing
record's revision".

| Point (section 5) | Codex's answer | Reason or caveat |
|---|---|---|
| 1. Certification above 20 is T2a's margin lever | **accepted** | C keeps 42 of 56 above 20, so 552 − 42 = 510 of 559 are needed and 49 losses are allowed. The margin of about 28 depends on the what-if's 207 recoveries |
| 2. T2a's stage-A "bound" is a recoverability count | **accepted** | `t2a-bounds.json` counts the recoverability of v0.5.2's 51 losses under an optimistic rule. It is not an information limit |
| 3. The what-if also recovers the 5 REFUTED losses | **accepted with a caveat** | 4 `odd_even` and 1 `period_alias` FAIL. If they remain REFUTED, the ceiling is 554, and the INCONCLUSIVE-only recoveries are 72, 124, 207 and 223. The condition is now explicit |
| 4. E2's distance to the Fisher bound; B1.2's gain | **accepted with a caveat** | The 81-to-86 gain and its absence on the 178 (142 to 141) check out. The ratios cover the earlier losses' subset, and their full range is 0.82 to 2.12. Both are now stated |
| 5. The bound's sample (112) versus the FAIL's (178) | **accepted with a caveat** | The over-reaching "no information limit" was removed. The bound leaves room under its assumptions on the 112 and was not recomputed on the 178 |
| 6. D2 losses with no recorded class | **accepted** | 24 of 26 `odd_even` and 17 of 25 `sinusoid`. These records do not show a sensitivity cause |
| 7. T3b missing from the infeasibility table | **accepted** | Added: not measured, "none as written", no basis |
| 8. D1's planet side and severity | **accepted with a caveat** | `secondary_eclipse` is a warning; D1 counts SURVIVED only (`c1.py:641-649`), and D2 counts WEAKENED as kept (`:654`). The v0.4 clause and the aggregation's precedence are now kept |
| 9. E4's null screen "empty" | **accepted** | 2 eligible, 1 contrast, availability 0.0. "Carried no information" replaces "empty" |

No point was rejected.

## Use of the caps (round 3)

| Cap | Stage A | Stage B | Note |
|---|---|---|---|
| CPU-h | **7.78** of 50 | **53.273** of 150: B0 4.923 of its 30; B1 48.350 of its 120, of which the D2/D4 completion took 0.707 | `stageA/ledger.json`, `stageB/ledger.json`. Two parts reached their own caps, and both stops are reconciled and kept: B1's first smoke, which the maintainer's split replaced, and D2/D4, completed afterwards. No stage cap was reached |
| Review tokens | 0 of 0.5 M (Codex's tokens did not count in stage A) | **2,278,749** of 4.5 M (the stop is at 3.6 M): Codex 2,058,175 over 13 conversations (B0 489,509), and the independent review 220,574, by the session tool's count. After this revision and the decision page: **2,623,789** (Codex 2,403,215 over 15 conversations, the review 220,574) | stage B counts Codex's uncached input plus output, from the last turn of each conversation, plus the independent review |
| Agent-days | 0.74 wall-clock bound, 0.21 active, of 4 | **3.0** wall-clock bound, **0.91** active, of 8 (`stageB/caps.json`, the check after the independent review); after the revision and the decision page, 3.16 and 0.99 | Claude's transcripts. Codex's and the reviewer's time is not counted |
| Disk | | 1.46 GB under `.cache/v053/stageB/`, of 5 GB | the T2a cache is 1.27 GB of it |

## Preserved, unchanged

Every record of stage A, B0, B0b and B1 is unchanged, with one disclosed exception:

- their scripts and outputs;
- the ledgers, except that stage B's `ledger.json` received the two reconciliations below, each
  appended under `reconciled` without deleting its stop;
- every stop, each kept in `ledger.json` under `reconciled`:
  - the D2/D4 cap stop;
  - B1's first smoke, reconciled on 2026-11-12 (afternoon) by the maintainer's decision as superseded
    by the split approved on 2026-11-11. Its driver stop file is kept as
    `stop-reconciled-000.json`;
- `b1_b14.py`, `b1_t2a_blockers.py` and their outputs;
- the stop report, corrected by a new addendum, not by an edit.

Nothing under `src/` or `calibration/` changed. v0.5.0's release files are untouched.

## What this does not show

- It is not a proof that any target is infeasible, nor that the approach cannot work.
- It is not a verdict on any real target.
- Every measured number is a development reading; the prices and the rough development price are
  estimates.
- The what-ifs remove blockers without designing anything.
- Prices marked as estimates are not measurements.

## Left open

- **The maintainer's decisions:**
  - the approach (change, infeasibility or pause);
  - T3b: whether to qualify A, and with whose adjudication.
- **The ROADMAP** changes only after the maintainer approves this record.
- **The independent review** of this record (the maintainer's item 4) read commit `40aa485`. Its
  report, [`closing-review.md`](closing-review.md), is unchanged. Its points are applied above and
  checked in [the table](#the-independent-reviews-points-and-codexs-check). Its answer and its order are in
  [their own section](#the-independent-reviews-answer-and-proposed-order-the-reviews-not-adopted).
- **The decision page** for the approach and T3b is [`v0.5.3-after-round3-decision.md`](../../plans/v0.5.3-after-round3-decision.md).
- #59 and the open issues are as triaged in v0.5.2.

## Sources (read on 2026-11-12; they inform the options only, no number comes from them)

- Jones, R. H. (1980). *Maximum likelihood fitting of ARMA models to time series with missing
  observations*. Technometrics 22, 389–395. https://www.tandfonline.com/doi/abs/10.1080/00401706.1980.10486171.
  The abstract page describes "calculating the exact likelihood function of a stationary
  autoregressive moving average" model with missing observations.
- Foreman-Mackey, D., Agol, E., Ambikasaran, S., Angus, R. (2017). *Fast and scalable Gaussian
  process modeling with applications to astronomical time series*. https://arxiv.org/abs/1703.09710.
  The method needs no evenly spaced observations or uniform noise.
- Pont, F., Zucker, S., Queloz, D. (2006). *The effect of red noise on planetary transit detection*.
  https://arxiv.org/abs/astro-ph/0608597. The detection threshold under correlated noise "can be
  much higher" than under white noise.
- Kunimoto, M. et al. (2025). *LEO-Vetter: Fully Automated Flux- and Pixel-Level Vetting of TESS
  Planet Candidates to Support Occurrence Rates*. https://arxiv.org/abs/2509.10619. A Robovetter-style automated vetter with
  flux- and pixel-level tests.
- Stage A's literature: [`../../plans/sources/v0.5.3-stageA-literature-2026-11-11.md`](../../plans/sources/v0.5.3-stageA-literature-2026-11-11.md).
