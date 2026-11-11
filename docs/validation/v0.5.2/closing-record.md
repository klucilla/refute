# v0.5.2 Battery corrections, round 2, ended as not approved (2026-11-10)

**The maintainer's decision of 2026-11-10, third set** (#216, item 2): v0.5.2 closes as **not approved**
(path (ii) of the [paths record](stage2/forecast-paths.md)). It counts as the second of the three
correction rounds of the advance rule (`ROADMAP.md`). **No target passed and none was declared
infeasible; all stay outstanding.** No acceptance run ran, no confirmation data was used, no drand
round was drawn, no protocol or lock was made, and no real target was selected. No gate review was
run and none passed; no exit criterion is ticked. Nothing is deleted or rewritten; every result below
stands as it came out. `method_status: not_validated`.

The targets, all outstanding: D1 for EB1 and EB2 (#202), D2 and D4 (#201), T2a (#201). The targets
that must not regress (D1 for SE, V1, V2, ER, NR; D3; D5; T2b; T2c; T3a; T3b) were not measured.

**Reviews of this record.** Codex reviewed it in three rounds (the consensus record,
`docs/plans/v0.5.2-consensus/`). One independent review session, read only, answered the maintainer's
question; its report is [closing-review.md](closing-review.md), unchanged (`WEAKENED`). Its corrections
of fact are applied below, each marked as the review's; its answer to the question and its proposals
for round 3 are its own.

## What led here

Stage 1 (2026-11-08, [report](stage1/README.md)), a bounded diagnostic on development data, then
stage 2 under the maintainer's delegation of 2026-11-08 to a Claude and Codex consensus, with hard
maxima (2,000 CPU-h of development and acceptance, raised to 3,100 on 2026-11-09; 150 CPU-h of
calibration; 1.0 M review tokens; 12 agent-days). Every stop below was a mandatory stop of that
delegation:

1. **The budget stop** (2026-11-09, `666fd16`, [budget.md](stage2/budget.md)): the projection
   (2,320 to 2,480 CPU-h) passed 2,000. The maintainer raised the maximum to 3,100 CPU-h.
2. **The adequacy check failed** (2026-11-09, `c1e717e`): the frozen check that the A0 round-2
   schedule, run on version 4, delivers enough contributions to every member of the acceptance's
   family certified none (lower bound 0.0; 91 to 113 members not measured in each of the 200
   datasets), because version 4's availability is below version 3's, on which the schedule was
   sized (812 of 2,293 members have fewer curves; [adequacy-diagnosis.json](stage2/adequacy-diagnosis.json)).
   The redesign, repriced (`182ea89`), passed 3,100 CPU-h in every option with a margin: a stop.
3. **The forecast** (2026-11-10, released by the maintainer under the failed gate, at most 25 CPU-h,
   development data only): D2 fails with version 4 (`09cfb1b`); T2a fails with every battery
   (`81252a2`); the stop of the three paths, where Claude, Codex and the advisor recommended (ii).
4. **The diagnosis of T2a's losses** (2026-11-10, item 1 of the third set), then this closing.

## What was built, what was accepted, what was not

| Component | State at closing |
|---|---|
| Stage 1: E1 (detrending mask), E2 (matched odd/even estimator), E3 (sinusoid under trends) | ran once each on frozen designs: E1 and E3 NOT ESTABLISHED by their frozen rules; E2 evaluated, no candidate qualifies |
| The acceptance specification and its sizing (`T` = 9,000, `G_min` = 8,550, `4ac7dee`) | written; the acceptance never ran |
| Version 4 of the battery (`discovery.version: 4`): fast detrending, `a0_v4`, `battery_v52`, `pipeline_v52`, the sector selector | built (`569d127`..`dbbd018`), byte-identity of the fast detrending shown on 300 of 300 curves; **not accepted, not certified**, never locked |
| The budget runner (`budgeted.py`, `driver.py`) | built and used for every run of stage 2 |
| The adequacy check | ran once; **failed** |
| The selector's certification, the known-answer gate, the sinusoid evaluation, sabotages, WP2/WP3 lines | not run |
| The forecast of D2, D4 and T2a, the `odd_even` diagnosis, the diagnosis of T2a's losses | ran on development data; diagnostics that decide nothing |
| Calibration, protocol, lock | not started |

The v0.4 and v0.5 batteries and version 3 are unchanged. Version 4 stays in the repository, unlocked.

## The results as they came out

Development data and development seeds only; none of these is an acceptance and none decides a
target.

**Stage 1** ([report](stage1/README.md)): E1, the detrending mask, NOT ESTABLISHED by its frozen rule
(one of 16 comb constructions failed availability, 2.5 % against 1 %); E2, the matched odd/even
estimator, evaluated with no candidate qualifying (null cells and power fail); E3, the sinusoid under
trends, NOT ESTABLISHED (the near-harmonic control's baseline recovers its target only at 0.74 and
0.20), with all 112 failures of the built arm within one frequency-resolution unit of a harmonic.

**The adequacy check** ([result](stage2/adequacy-result-aa037e23d0e2d011.json), `c1e717e`): failed,
0 of 200 datasets certified.

**D2 and D4** ([forecast-v4.json](stage2/forecast-v4.json), 112 eligible synthetic development
planets): D2 kept v0.4 0.964, version 3 0.839, version 4 **0.723** against the minimum 0.864 (FAIL);
D4 INCONCLUSIVE 0.122 (at most 0.30: PASS).

**T2a** ([forecast-t2a.json](stage2/forecast-t2a.json); 80 of 615 recovered development injections,
the stratum above 20 sectors not run; minimum 0.897):

| Battery | Estimate | Interval | Forecast |
|---|---|---|---|
| v0.4 (weighted sample) | 0.988 | 0.876 to 0.998 | |
| Version 3 | 0.389 to 0.480 | 0.239 to 0.642 | FAIL |
| Version 4 A, as built | 0.135 | 0.067 to 0.276 | FAIL |
| Version 4 B, selector certified | 0.313 | 0.174 to 0.488 | FAIL |
| Version 4 C, B and the refusal above 20 lifted | 0.313 to 0.404 | 0.174 to 0.571 | FAIL |

**The `odd_even` diagnosis** ([forecast-v4-diagnosis.json](stage2/forecast-v4-diagnosis.json)): on the
17 synthetic planets turned INCONCLUSIVE by the sensitivity rule, A0's error is 1.49 times the
Cramer-Rao bound (median); the diagnostic split is about 1.10 for A0 and 1.33 for the box estimator's
conditional error. At the bound, 16 of the 17 would reach the rule's threshold: this does not
establish an information limit, nor that an attainable estimator would reach it.

**The diagnosis of T2a's losses** ([forecast_t2a_diagnosis.py](stage2/forecast_t2a_diagnosis.py),
[forecast-t2a-diagnosis.json](stage2/forecast-t2a-diagnosis.json), its reading
[forecast-t2a-diagnosis-reading.json](stage2/forecast-t2a-diagnosis-reading.json); `074c32c` frozen
before the run, `b245f6b` the result; 2.64 CPU-h). The approval and the exact procedure were posted on
#216 before it ran; Codex reviewed the design in three rounds. All 80 injections reproduced the
forecast's records, and none was quarantined. **The frozen diagnosis detected no class-(c) blocker and
no instrumentation quarantine, so its stop was not triggered**; this is not a proof that no defect
exists. Version 4 B's 51 losses against v0.4, by decisive blocker. They overlap. The frozen
classification stands in its file; the reading makes two stated corrections: it leaves out the 15
FAILs of severity warning, which give WEAKENED, a kept verdict, and it reads `odd_even`'s "no calibrated
error" as A0's group variance returning none:

| Test | Class | Losses | Evidence |
|---|---|---|---|
| `systematics` | (a) missing data | 0 | no sub-check was stopped by a missing product, a missing CROWDSAP or too few transits |
| `systematics` | (b) lack of power, data present | 23 (the only blocker of 15) | all in the background sub-check, after all three sub-checks ran without a problem: a background rise of 0.8 of the depth is detectable with probability 0.0015 to 0.92 (median 0.14), against 0.95. A0's error on the rise is 0.18 to 5.0 times the SAP depth (median 0.41) in these 23 losses. A Gaussian approximation of the 3-sigma condition alone needs about 0.17; that is a necessary condition, not sufficient for the block's joint rule (the rise must also reach 0.5 of the depth) |
| `systematics` | (d) a procedural refusal of A0 or of the selection | 25 (the only blocker of 10) | A0's group variance returned none in 15 (the exact branch, a lag correlation below `a0.MIN_PAIRS` window pairs, a covariance that is not positive semi-definite or a variance that is not positive, was not diagnosed); measured events in 0 or 1 sector, outside A0's grid of 2 to 4, in 9 (in 4 of them no sector contributes a measured event, so "data present" is not established there); the comb measured no event in 1 |
| `odd_even` | (d) | 12 | A0's group variance returned none in 6; outside the grid in 6 |
| `odd_even` | (b) | 4 | power 0.79 to 0.93, against 0.95 |
| sinusoid | (b) | 15 (the only blocker of 2) | the reported value is the Fréchet lower bound max(0, p + small − 1) of the flag's simulated power p and the small-residual probability `small` (`battery_v52.py`, lines 341 to 371). For all 15 losses, the stored `small` ranges from 0.062723 to 0.945319. **Under the declared Gaussian residual model, the joint rejection probability is at most `small`, hence below 0.95**; this does not establish a calibrated power on the actual data (the independent review's reading, bounded by Codex's round 3) |
| `period_alias` | (b) | 2 | probability 0.898 and 0.207, against 0.90 |

Labels that do not name the cause (a labelling defect; it causes no loss): 19 `systematics`
INCONCLUSIVE labelled `not_enough_data` are A0's or the selection's refusals, and 6 `odd_even` labelled
`insufficient_sensitivity` are A0's group variance returning none. Among the 23 background losses, the
error ratio is large even for deep, high-SNR injections (one of 3,925 ppm at SNR 36 has 1.28); with 23
selected losses, this does not establish whether the ratio depends on the depth or on the SNR. The
recorded background-rise error over the recorded SAP-depth error has a median of 6.57 over the 23
losses (the independent review's estimate of about 8 used the candidate's search SNR, which does not
measure the SAP estimator's uncertainty). The review's explanations, scattered-light variability that
cancels in SAP or a normalization or units issue of the statistic, are untested and not exhaustive.
**A FITS-column unit mismatch and unequal adapter normalization are ruled out for these 547 cached
files:** all give SAP_FLUX and SAP_BKG in e-/s, and the adapter divides both by the same sector
median of SAP_FLUX on the same kept cadences (`adapter.py`, lines 527 to 531). Normalization defects
at the level of the statistic remain unexcluded; background variability that cancels in SAP stays an
open question about the statistic, not a finding.

`aperture_depth`, named in the maintainer's decision, is INCONCLUSIVE in all 80 injections and
deferred to stage 2 in all 80, so it blocks no stage-1 verdict of T2a: in 74 "no target pixel data
usable for aperture photometry" (an injection has no target pixel file, by design: `inject` does not
change pixels, and the sample's cache manifests list none), in 6 the selection's grid refusal.

What-ifs (removals, not estimators; the stratum above 20 all lost to all kept): every refusal (d)
removed, 0.50 to 0.60; the background sensitivity removed, 0.50 to 0.59; both, **0.69 to 0.78** (upper
sampling bound 0.90 against 0.897); every lack of power (b), 0.62 to 0.71; every blocker, 0.91 to
1.00.

## D2 and T2a against the v0.4 baseline

The v0.4 battery had no sensitivity rule: a test that could not have failed still returned PASS
(#185). v0.5 added the rule (an INCONCLUSIVE unless the declared minimum effect is detectable), and
its calibration measured T2a at 42.4 % against v0.4's 99.7 % (#201). This section reads the
injections and planets that v0.4 kept and the evidence-only batteries lose: which present rule blocks
each, and whether that loss is information absent from the data or an estimator below what the data
allow. Classifying version 4's blockers does not measure v0.4's own power, and v0.4 had no sinusoid
test at all, so this is not a decomposition of the share of v0.4's retention attributable to #185.
**"Information absent" is established for none of the losses**: it would need a bound on attainable
performance, and none was computed.

### T2a (v0.4 0.988 in the development sample; version 4 B 0.313)

The 51 injections are v0.4-kept injections blocked by version 4's present rules: a PASS without the
declared power (b), or no calibrated error at all (d). In the population-weighted what-ifs, which
overlap and are blocker removals, not attributions, removing every (b) raises the kept fraction by
0.31, every (d) by 0.19, and both by 0.60. The stratum above 20 sectors (0.091 of the population) is
lost by the selector's refusal, a rule. **With the refusal retained, at least 552 of the other 559
injections must be kept (0.987)**, v0.4's own in-sample rate. If it is lifted and k of those 559 are
kept, at least max(0, 552 − k) of the 56 above 20 are needed. The independent review judges that T2a
would need essentially every blocker class resolved at once (its judgment).

| Test | Losses | Information absent or estimator? | Evidence |
|---|---|---|---|
| `systematics`, background sub-check (b) | 23 | **Undetermined.** | Under the Gaussian approximation of the 3-sigma condition, the error would have to shrink by 2.4 times at the median of these 23 (up to about 29). These factors are improvements over that approximation, not information bounds, and no bound was computed for the background rise. |
| `systematics` and `odd_even`, refusals (d) | 25 and 12 | **Undetermined**: a procedural refusal of the present procedure, not evidence about the information. | The grid of 2 to 4 contributing sectors, A0's group variance returning none, and the selector's validation to 20 sectors. Extending A0's domain is unpriced. `budget.md` prices the existing acceptance schedules at 1,482 to 1,932 CPU-h, which says nothing about an extension. |
| sinusoid (b) | 15 | **Undetermined** between information and estimator; under the declared residual model the power is below 0.95 in all 15 (above). | The declared Gaussian residual model requires σ_r / D ≤ 0.107646; if SNR is defined as D / σ_r, this corresponds to 9.29, and its equivalence to the candidate's search SNR is not established. Uniform box weights may lose efficiency with unequal or correlated errors; the attainable gain was not measured. In E3's SNR 12, correlated-trend cell, 0 of 150 planets had every harmonic detectable ([stage 1](stage1/README.md)). |
| `odd_even` (b) | 4 | **Undetermined.** | Power 0.79 to 0.93 against 0.95. D2's synthetic comparison does not establish T2a's estimator efficiency. |
| `period_alias` (b) | 2 | **Undetermined.** | 0.898 and 0.207, against 0.90. |

### D2 (v0.4 0.964 on 112 synthetic planets; version 4 0.723)

Of the 28 planets that v0.4 kept and version 4 does not, the blockers (they overlap;
[forecast-v4-losses.json](stage2/forecast-v4-losses.json)) are: `odd_even` 23 (17 PASS turned
INCONCLUSIVE by the sensitivity rule, 5 more INCONCLUSIVE labelled `insufficient_sensitivity`, 1
refused outside the grid), the sinusoid 13, `aperture_depth` 9 (8 labelled `not_enough_data`, 1
outside the grid) and `systematics` 6 (5 labelled `not_enough_data`, 1 outside the grid).

- **`odd_even`: undetermined; the evidence available points to the estimator rather than the data.**
  On the 17 sensitivity conversions, A0's error is 1.49 times the Cramer-Rao bound, and at the bound
  16 of the 17 reach the threshold; that is not attainability. E2 found no calibrated estimator that
  does better. The 5 INCONCLUSIVE labelled `insufficient_sensitivity` are not covered by that
  diagnosis; on T2a, the 6 `odd_even` with that label were A0's group variance returning none, so
  these may be refusals too (not established).
- **The sinusoid: not diagnosed on D2**; 12 of its 13 INCONCLUSIVE carry no class in the forecast's
  records. On T2a, under the declared residual model, every one of its 15 refusals has a power below
  0.95.
- **The sinusoid's place in D2, a removal arithmetic.** The minimum needs 97 of the 112 planets kept.
  The independent review computed that removing every blocker but the sinusoid leaves at most 96 and
  concluded that D2 needs the sinusoid. **Codex's round 3 corrects that arithmetic:** removing every
  non-sinusoid INCONCLUSIVE blocker, retaining the fatal failures, also recovers two planets that v0.4
  lost (1074 and 1110) besides the existing gain (1057), and gives **98 of 112 (0.875)**, above the 97
  required. This hypothetical removal does not establish attainable performance, nor that resolving
  the sinusoid is necessary. The review's report is kept unchanged.
- **`aperture_depth` and `systematics` `not_enough_data`: not diagnosed on D2.** On T2a, every one of
  the 19 `systematics` labels `not_enough_data` turned out to be a refusal by A0 or the selection. The
  D2 labels may hide the same thing; this is not established.

### What an infeasibility record would need (none is declared)

- **T2a.** The allowance is 0.10 absolute retention: the minimum is 0.896748. A record would need an
  upper bound on attainable testing performance, with the population's sampling uncertainty, that
  forces the maximum retention below that minimum. For the background sub-check, that means a bound on
  the attainable error of the background-rise statistic per host, from the background series' own
  noise, mapped to T2a's population. Two quantities must be kept apart. Removing the background
  blockers recovers about 0.19 (the marginal recovery in the what-ifs). The losses that carry a
  background blocker weigh about 0.26 (the weighted incidence). Such a bound would hold only **under
  the sub-check's declared alternative** (a rise of 0.8 of the depth at power 0.95), a requirement of a
  warning-severity sub-check that only the maintainer can weigh. The refusals (d) and the stratum above
  20 are procedural, so they cannot enter such a record unless their information is bounded too. The
  current sample establishes neither infeasibility nor an information limit. Price, an unmeasured
  estimate: about 2 to 10 CPU-h and 2 to 3 days for the background bound, plus a Codex review.
- **D2.** Gains and losses are paired: version 4 keeps planets v0.4 did not. A record would need an
  upper bound on attainable testing performance that accounts for both, forcing the kept count below
  0.864 of 112. For example, 16 losses that no estimator can recover would leave at most 96 kept. The
  Cramer-Rao comparison points the other way for `odd_even`. Developing and calibrating a better
  estimator (path (i)) is feasibility research: its failure would not prove infeasibility. The
  sinusoid's power would need its own bound. Prices, unmeasured estimates: path (i)'s 20 to 60 CPU-h,
  which already include the sinusoid's and `systematics`'s diagnoses, then a validation repriced from
  the estimator. The whole is unpriced.

## Lessons

1. **Forecast the targets before pricing a full acceptance.** A 16 CPU-h development forecast showed
   that D2 and T2a fail with version 4, after a design and a budget of about 3,000 CPU-h had been
   built around an acceptance that version 4 would not have passed.
2. **Keep the message and the inputs of every INCONCLUSIVE, not only its class.** The forecast's
   records kept the class only. Diagnosing them took a rerun, and 25 of the classes turned out not to
   name the cause.
3. **A warning test's INCONCLUSIVE blocks the verdict; its FAIL does not.** `core.verdict.aggregate`
   applies rule 3 (any INCONCLUSIVE gives INCONCLUSIVE) before rule 4 (a warning FAIL gives WEAKENED).
   In T2a, `systematics`, a warning, is the only blocker of 25 of the 51 losses. Whether a warning
   test that cannot decide should block a verdict is a design question for the maintainer; nothing
   was changed here.
4. **A calibrated domain is a coverage limit.** A0's grid of 2 to 4 sectors, its group variance
   returning none and the selector's 20 sectors give 37 blockers of T2a's losses and the whole stratum
   above 20. The domain
   must be sized against the target's population before the estimator is built: 313 of T2a's 615
   injections are in hosts of 5 or more sectors, and 56 above 20.
5. **Check a power requirement against the target population's noise before building the test.**
   Under a Gaussian approximation, the background sub-check's alternative needs an error of about
   0.17 of the depth. The 23 T2a losses it blocks have a median of 0.41. That is a selected subset,
   not the development injections as a whole.
6. **Size on the code that will run.** The adequacy check failed because the schedule was sized on
   version 3's availability.
7. **An information bound is not attainability**, and its absence is not infeasibility (the
   `odd_even` diagnosis).
8. **A design review before a run pays.** Codex's three rounds on the diagnosis removed a
   classification that would have called sampling artefacts code defects, and added a binding stop.
   The tie-break after three rounds kept the work moving.
9. **Hosts of many sectors outlast the 30-minute batch** (39 minutes for one injection of 31
   sectors). Measuring T2a above 20 sectors needs a cheaper battery or a different batching.
10. **The agent-day ledger was kept for Claude** this time, as a wall-clock bound and as active time
    (below). Total agent-day compliance is still not established, since other agents are not counted.

## Use of the caps

| Cap | Value | Used | Note |
|---|---|---|---|
| Stage 1 CPU-h | 12 | about 5.55 | [stage 1 report](stage1/README.md); **deviation:** E1 used 2.657 CPU-h against its allocation of 2.5 |
| Development and acceptance CPU-h (stage 2) | 2,000, raised to 3,100 on 2026-11-09 | 179.5 | `budgeted.spent` (ledger): about 70 before the decision of 2026-11-09 (approximate: partly estimated from wall time), the adequacy check, the probes and the forecast; no acceptance ran |
| The forecast, D2/D4/T2a and both diagnoses | 25 (the maintainer, 2026-11-10) | 16.3 | D2/D4 4.85, `odd_even` diagnosis 1.41, T2a 6.63 (and 0.01 of a failed attempt), the loss diagnosis 2.60 and its smokes 0.04, charged smokes 0.77 |
| Calibration CPU-h | 150 | 0 | not started |
| Review tokens | 1.0 M | 203,057 | the one independent review session of this record (at most 350,000 by the maintainer's decision; [closing-review.md](closing-review.md)); Codex's tokens do not count (the maintainer, 2026-11-09), and each round's are in the consensus record |
| Agent-days | 12 | Claude: at most 6.8 by wall clock (54.2 hours), about 2.1 active (16.7 hours), at 2026-11-11 00:08 UTC | measured from the session transcripts since 2026-11-08 17:57 UTC (`.cache/v052/tools/agent_time.py`; gaps capped at 10 minutes for active time); Codex's and the reviewer's time not counted, so total compliance is not established |
| Advisor consultations | 3 | 3 | an opinion only; the third, on this closing, is in the consensus record ([advisor-round-3-answer.md](../../plans/v0.5.2-consensus/advisor-round-3-answer.md)) |
| Disk | | about 1.3 GB in `.cache/v052` | of which 1.0 GB the T2a light curves (`t2a-cache`) |

## Preserved, unchanged

Every FAIL, record and criterion of v0.5.2: the scope proposal, stage 1's designs and results, the
stage 2 design and its consensus record (`docs/plans/v0.5.2-consensus/`, Codex's answers unchanged),
version 4's code, the budget ledger with both failed gates (`adequacy`, `planet_forecast`) and every
attempt, the forecasts and diagnoses. Built components are distinct from a validated method, which
v0.5.2 did not deliver.

## What this does not show

Not a proof that any target is infeasible or that the corrections cannot work. Not a verdict on any
real target. The forecasts and diagnoses are development readings on small samples (112 synthetic
planets, 80 injections); the what-ifs remove blockers without designing anything.

## Left open

- **Round 3 (v0.5.3, the last correction round of the advance rule): to be scoped**, not started.
  If round 3 also ends without success, the maintainer decides between changing the approach,
  recording infeasibility, or pausing the line.
- #59 keeps two findings of Codex's end-of-round review that touch fingerprinted files: the
  forecast's cumulative cap across parts, and `budgeted.fail_gate` replacing a gate's detail (so
  `forecast_t2a.py summarize` must not run again before a fix).
- The open issues were triaged after this record ([issue-triage.md](issue-triage.md)): the
  milestone v0.5.3 holds what round 3 will probably attack. #216 is closed by comment after the
  closing commit has a green CI.
- A scope proposal for round 3, for the maintainer's decision:
  [docs/plans/v0.5.3-scope-proposal.md](../../plans/v0.5.3-scope-proposal.md).
- For the package of 19 November: the draft README of the v0.5.0 release must say that v0.5.1 and
  v0.5.2 closed as not approved (the drafts are not touched now).
