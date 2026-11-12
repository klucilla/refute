# v0.5.3 Battery corrections, round 3, ended as not approved (2026-11-12)

**For the maintainer's decision; nothing here is decided by Claude or Codex.** Round 3 is the last
correction round of the advance rule (ROADMAP, "Advance rule"). It closes **not approved** by the
criterion fixed in stage A's report ([`stageA/README.md`](stageA/README.md), "Round 3's closing
criterion"), applied as the maintainer's decision of 2026-11-12 (#217) states: **item 2, by T2a**
(the forecast does not pass it), and **item 3, by a cap reached** (B1.4's D2/D4 part stopped at its
cap with the forecast not done). Every measured number below comes from a committed file of
`stageA/` or `stageB/`, produced by a script reviewed by Codex before its run, with its approval and
exact procedure posted on #217 before it ran. Stage A's one exception, a smoke run outside the
ledger, was disclosed there. Prices and the rough development price are estimates, marked as such. Development data only; no confirmation set exists or was
touched; no drand round was drawn; no lock was made; no real target was selected; nothing in `src/`
changed. `method_status: not_validated`. No target is relaxed. The ROADMAP changes only after the
maintainer approves this record.

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
| **3. Not approved, stage B:** no estimator survives, or a cap is reached with the forecast not done | **yes: a cap was reached** | the part `b1_forecast_d2d4` stopped at its cap with 181 of 200 curves. That stop stays recorded as a fact; the part was completed afterwards under the maintainer's approval |
| 4. Not approved, the maintainer's | not invoked | |

## The state of each target

| Target | Frozen rule | State at the close | Source |
|---|---|---|---|
| **D1, EB1 and EB2** | the SURVIVED fraction's Wilson 95 % upper end at most 0.10, and no more SURVIVED than v0.4 | **pending, no route.** B0 gave outcome **C**: under the catalog star the bound does not settle it. The oracle leaves an expected 29.2 (EB1) and 35.5 (EB2) non-rejected at the primary level against an allowance of 10; with the star known, 11.9 and 11.2. B0b gave outcome **N**: the pre-registered infeasibility criterion is not met (median pass probabilities 0.452 and 0.102 at 0.05, not below 0.05). Stage A's geometric route (d) did not separate the binaries | `stageB/README.md`, `stageB/b0b-record.md`, `stageA/README.md` (d) |
| **D2** | kept fraction ≥ v0.4's minus 0.10; REFUTED ≤ 0.05 and its Wilson upper end ≤ 0.10 | **FAIL** on the completed part: 200 new C1 planets, 178 eligible. v0.4 keeps 173, so the minimum is 0.872. Version 5 keeps 141 (0.792 [0.727, 0.845]), with 3 REFUTED (Wilson upper end 0.048). Version 4 keeps 142. Disclosed: the part stopped at its cap at 181 of 200 curves, a stop kept on file, and was completed with the maintainer's approval (0.707 CPU-h, no new stop) | `stageB/b1-forecast-d2d4-complete.json`; `stageB/b1-stop-report-addendum.md` |
| **D4** | INCONCLUSIVE fraction at target SNR ≥ 15 at most 0.30 | **PASS** in this forecast: version 5 has 7 of 122 INCONCLUSIVE (0.057). It passed in v0.5.2's forecast too (0.122). A forecast is not an acceptance: D4 stays to be accepted with the others | the same |
| **T2a** | kept fraction ≥ v0.4's minus 0.10, so 0.897 of 615 (551.5) | **no**, by the census rule fixed before the run: `K_B` 331 and `U_B` 0 of 559, against at least 552. C, with the selector treated as certified above 20, keeps 373 of 615, so certification cannot rescue it | `stageB/b1-forecast.json`; the counts are recomputed in `stageB/b1-blockers-decisive.json` |
| **T3b** | the EB truth population (v0.5.2: "none as written") | **not executed** in round 3. The recommendation is **A**, added to the approved frame, conditional on qualification; it is pending the maintainer's decision. The qualification costs close to zero CPU and 1 to 2 agent-days; the human adjudication of up to 165 stars is not measured, and ExoFOP's data use policy is an open condition | `stageB/b1-stop-report.md`, section 4 |

## Stage A's limits (bounds, not attainability)

- **D2: room.** Kept retention's upper bound is 111 of 112, and the evidence-qualified bound is 108,
  against the 97 required.
  - The bound rests on Gaussian noise with the generator's covariance, a joint Fisher bound for
    `odd_even` and the oracle GLS residual for the sinusoid.
  - Three planets stay below 0.95 even for the oracle sinusoid residual.
- **T2a: narrow room.** The upper bound is 0.909 with the stratum above 20 sectors all lost, and 1.0
  with it all kept, against 0.897.
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

**D2, version 5 (37 losses of 178):**

| Test | Losses it blocks | As the only blocker | Estimator of version 5, where the test blocks |
|---|---|---|---|
| `odd_even` | 26 | 9 | E2 operated in 22 and fell back in 4 |
| `sinusoid` | 25 | 8 | E3 operated in 2 and fell back in 23 |
| `period_alias` | 3 | 3 | none |
| `systematics` | 1 | 0 | E4 called, no measurement completed |

- 17 losses carry both `odd_even` and `sinusoid`: 16 with only those two, and 1 with `systematics` too.
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
- **E3**, the ARMA(1,1) GLS of the sinusoid's residual: it delivered 51 of 339 eligible in B1.3. Its
  SD is 1.35 [1.045, 1.87], a warning. It falls back on 547 of 559 T2a attacks of B and on 149 of
  178 D2 attacks (φ outside (0, 0.99), or autocovariances not positive). So **the sinusoid's T2a losses are all version 4's computation**,
  and 23 of its 25 D2 losses are.
- **E4**, the background sub-check's window-local quadratic baseline: its null screen was empty (2
  proposals in 13 hosts). It measured in 110 of the 169 T2a losses that `systematics` blocks, and
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
| The selector's certification above 20 sectors (it buys nothing for T2a) | about 380 |
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
   - **The finding:** E3's moment estimates fail on almost every curve.
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
4. **`odd_even`'s sensitivity** (T2a: 43 insufficient sensitivity outside the refusals; D2: 26 losses, 9 as the only blocker. There E2 operated in 22, and `odd_even` stayed INCONCLUSIVE in 21 of them and FAILed in 1, so the current E2 was not enough there; that does not show that every better contrast would fail).
   - **The finding:** E2 operates where it is reached. In B1.3 only its SD criterion passed; its mean and tail stayed UNRESOLVED.
   - **What to try:** use E2's joint contrast where it applies, and widen its domain with A0's.
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
star with 5 % errors, or a test whose power survives them; none is designed.

**A rough price for one more round of development** like stage B: 60 to 150 CPU-h and 5 to 8
agent-days, before any acceptance. That is an estimate, not a measurement. It is scaled from round
3's own use: stage A 7.8 CPU-h and stage B 53.3 so far, with about 3 agent-days as stage B's
wall-clock bound. The acceptance and confirmation above come only if a forecast then passes.

### 2. Record infeasibility

**No target has a basis for an infeasibility record now.** The rule asks for evidence that the
target cannot be met with the available data, reviewed by Codex and by an independent review.

| Target | Basis? | Why |
|---|---|---|
| D1, EB1 and EB2 | **no** | B0b's pre-registered criterion was not met (outcome N). Under the catalog star the oracle bound leaves about three times the allowance at the primary level, but that is a bound on one information model. A binary the oracle does not reject is not a SURVIVED: a binary held INCONCLUSIVE does not survive under D1's frozen rule, so the bound's excess does not show that the frozen target cannot be met. The criterion fixed before the run did not declare infeasibility |
| D2 | **no** | stage A's bound leaves room (111 and 108 against 97); under stage A's model, `odd_even`'s losses are the estimator's, not missing information; version 5's shortfall shows no information limit |
| D4 | **no** | it passes in both forecasts (0.057 here, 0.122 in v0.5.2), so there is nothing to record |
| T2a | **no** | stage A's bound leaves 7 injections of room; the census shows what blocks, not that it cannot be unblocked |

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

## Use of the caps (round 3)

| Cap | Stage A | Stage B | Note |
|---|---|---|---|
| CPU-h | **7.78** of 50 | **53.273** of 150: B0 4.923 of its 30; B1 48.350 of its 120, of which the D2/D4 completion took 0.707 | `stageA/ledger.json`, `stageB/ledger.json`. Two parts reached their own caps: B1's first smoke, which the maintainer's split replaced, and D2/D4, completed afterwards. No stage cap was reached |
| Review tokens | 0 of 0.5 M (Codex's tokens did not count in stage A) | **2,278,749** of 4.5 M (the stop is at 3.6 M): Codex 2,058,175 over 13 conversations (B0 489,509), and the independent review 220,574, by the session tool's count | stage B counts Codex's uncached input plus output, from the last turn of each conversation, plus the independent review |
| Agent-days | 0.74 wall-clock bound, 0.21 active, of 4 | **3.0** wall-clock bound, **0.91** active, of 8 (`stageB/caps.json`, the check after the independent review) | Claude's transcripts. Codex's and the reviewer's time is not counted |
| Disk | | 1.46 GB under `.cache/v053/stageB/`, of 5 GB | the T2a cache is 1.27 GB of it |

## Preserved, unchanged

Every record of stage A, B0, B0b and B1 is unchanged:

- their scripts, outputs and ledgers;
- every stop: the D2/D4 cap stop, reconciled, is kept in `ledger.json` under `reconciled`; B1's first smoke stays an `unresolved_stop`, its handling decided by the maintainer;
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
- **The independent review** of this record (the maintainer's item 4) is
  [`closing-review.md`](closing-review.md), kept unchanged. It ran on commit `40aa485`, after Codex's
  review.
  - **Its verdict: WEAKENED.** It agrees that the round closes not approved and that no target has
    a basis for an infeasibility record now.
  - **It lists nine points** where this record overstates or omits (its section 5). Among them:
    - the certification above 20 sectors "buys nothing" holds only for version 5's forecast; for a
      change of approach it is T2a's margin lever;
    - T2a's stage-A "bound" is a recoverability count, not an information bound;
    - the T2a what-if also recovers the 5 REFUTED losses;
    - E2's error stays about 1.1 to 2.1 times the Fisher bound;
    - 24 of 26 `odd_even` and 17 of 25 `sinusoid` D2 losses have no INCONCLUSIVE class recorded;
    - T3b is missing from the infeasibility table;
    - D1's planet side and severity are missing.
  - **It proposes another order** for a change of approach. First, record what the records cannot
    tell. Then a per-host bound on the background rise, a joint D1 test with the planet side, and
    `odd_even`'s bound with the transit shape as a nuisance. Estimators come after.
  - **None of its points is applied to this record.** They are left to the maintainer's decision,
    which follows this review.
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
