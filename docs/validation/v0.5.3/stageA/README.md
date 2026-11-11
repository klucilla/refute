# v0.5.3 stage A: the stop report

**For the maintainer's decision; nothing is decided here.** The maintainer's decision of 2026-11-11
(#217) approved stage A of round 3 (bounds, audits and diagnoses on development data) and asked, at
its stop, for: the bounds with their uncertainty; the draft infeasibility record of every target
whose bound leaves no room; for stage B, caps of CPU-h, tokens and days, and round 3's closing
criterion; the design questions argued both ways; whether a data set outside development exists and
was touched; and a proposal for where test renames are recorded. Stage B does not start without the
maintainer's approval of this report. `method_status: not_validated`. Every number below comes from
a file of this folder, produced by a script reviewed by Codex before its run, with its approval and
exact procedure posted on #217 before it ran, with one exception: a one-planet smoke of
`d2_bounds.py` ran in the shell process, not pinned to processors 8 to 31 and outside the ledger (a
slip, disclosed on #217 and charged afterwards at its wall time, 0.059 CPU-h). The design is frozen in
[`v0.5.3-stageA-design.md`](../../../plans/v0.5.3-stageA-design.md) (three amendments, each recorded
before the run it concerns); Codex's answers are in the
[consensus record](../../../plans/v0.5.3-consensus/README.md).

## What ran

| Item | Script, result | CPU-h | What it is |
|---|---|---|---|
| (a) A0's refusals | [`a0_refusals.py`](a0_refusals.py), [`a0-refusals.json`](a0-refusals.json) | 2.35 | which branch of A0 refuses, in every refusal of v0.5.2's diagnosis and forecast |
| (b) D2's bounds | [`d2_bounds.py`](d2_bounds.py), [`d2-bounds.json`](d2-bounds.json) | 0.67 (a smoke of 0.06 included) | the upper bound of D2's kept retention, and the evidence-qualified count |
| (c1), (c2) T2a | [`t2a_bounds.py`](t2a_bounds.py), [`t2a-bounds.json`](t2a-bounds.json) | 0.02 | the background audit (measurements) and T2a's kept-retention bound |
| (c3) above 20 sectors | [`above20.py`](above20.py), never run | 0 | cut by the tie-break after three Codex rounds, each `REFUTED` |
| (d) D1's geometric route | [`d1_geometry.py`](d1_geometry.py), [`d1-geometry.json`](d1-geometry.json) | 4.75 | a diagnostic on development curves |

The ledger is [`ledger.json`](ledger.json); the other caps are in [`caps.json`](caps.json).

## (a) A0's refusals

79 records (51 T2a injections and 28 D2 planets that version 4 loses against v0.4), 0 errors, 0
quarantined: each reproduced its v0.5.2 record. Where A0's group variance returns none, the refusing
branch is a lag correlation with fewer than `MIN_PAIRS` (20) window pairs, mostly 17 to 19 pairs at
lag 3 between full-coverage strata, unpooled (9 calls with no pair at all), or, in 11 calls, a
covariance that is not positive semi-definite. D2's `aperture_depth` "not_enough_data" (8) and
`odd_even` "insufficient_sensitivity" (5) labels are A0 refusals with the data present. The branch
totals count refusing calls, not independently attributable lost planets. It decides nothing; it
names the cause of each refusal, which is what an extension of A0's domain in stage B would address.

## (b) D2's bounds

**Kept retention's upper bound: 111 of 112** (Wilson 95 % upper end 0.998); **the evidence-qualified
upper bound: 108 of 112**. D2's requirement is v0.4's kept fraction minus 0.10, **0.8643** (97 of 112
in this sample). Version 4 keeps 81 and v0.4 108.

- Only planet 1075 is lost at the bound: its fatal `odd_even` reaches 0.912 at its bound, against 0.95.
  Three more lose the evidence-qualified PASS by the sinusoid's residual at its bound (0.885, 0.671,
  0.948), recoverable for kept retention as a warning.
- At the bound, `odd_even`'s power is 0.97 to 1.0 where A0's error left it INCONCLUSIVE, planet 1075
  excluded (0.912 at its bound, still INCONCLUSIVE): for those planets, under this model, the loss is
  the estimator's, not missing information.
- **Assumptions** (`d2-bounds.json`, `assumptions`): Gaussian noise with the generator's covariance
  (white plus each sector's exponential term), the true template and an unbiased estimator, for
  `odd_even`'s joint Fisher bound; the oracle GLS residual box under that covariance, the tested
  harmonics only and the flag's power taken as 1, for the sinusoid (necessary, not sufficient);
  warning blockers recoverable for kept retention; refusals, blockers without a bound, fatal FAILs of
  this estimator and quarantined records counted optimistically.
- **Uncertainty.** The count is deterministic for the 112 generator draws; the population's
  uncertainty is the Wilson interval above. The bound's validity rests on the assumptions, which
  the interval does not cover: a Cramér-Rao bound is a bound for the stated model, not for any
  estimator on real data.

**The bound leaves room** (111 and 108 against 97), so no draft infeasibility record of D2 follows.
Room under a bound is not reachability: that needs an attainable, calibrated construction (stage B).

## (c) T2a

**(c1) The background audit** (measurements, not bounds) on the 23 background-sensitivity losses:
A0's error on the background rise is a median **23.2** times the white box error at the series'
point-to-point scatter, and the background's out-of-transit variability a median **65** times that
scatter; under white noise all 23 would meet the 3-error rule's necessary condition (a median 0.019
of the SAP depth against 0.17223). The recorded background-rise error over the SAP depth's error has
a median of 6.57. Reading: A0's error is dominated by slow variability of the background series, not
by its white noise; whether an estimator that models that variability can certify the 0.8-depth
alternative is not established here. The scatter may itself contain variability, and the white box
error is one estimator's.

**(c2) T2a's kept-retention bound.** Under the frozen rules every blocker of T2a's 51 development
losses is recoverable (warnings, `odd_even`'s plug-in error, refusals, `period_alias`), so the upper
bound is **1 on the measured strata**. The stratum above 20 sectors (0.091 of the population) was
not measured: with it all lost, the bound is **0.909**; all kept, 1.0. T2a's requirement is
**0.897**. Conditional white-noise scenarios (not bounds): `odd_even` and the sinusoid reach 0.95 in
50 of 51.

**(c3) cut.** Its controller stayed `REFUTED` after three Codex rounds; the more conservative option
holds: nothing of it ran, and the stratum stays bounded both ways (0.909 to 1.0).

**The bound leaves room, narrowly.** 0.909 is above 0.897, so no draft infeasibility record of T2a
follows. But with the selector's refusal above 20 sectors retained (a rule), the room is 7
injections: at least 552 of the other 559 must be kept (0.987, v0.4's own in-sample rate; v0.5.2's
closing record). In practice T2a needs essentially every blocker class resolved at once, or the
stratum above 20 sectors measured and mostly kept.

## (d) D1's geometric route

2,500 development curves (v0.5.1's 600 and 1,900 new), 0 errors; eligible: P 865, PG 735, EB1 288,
EB2 279. The threshold, fixed before the measurement, is the larger of the P and PG empirical
99.73 % quantiles.

| Statistic | P quantile | PG quantile | Threshold | P, PG above | EB1 flagged | EB1 folded | EB2 flagged |
|---|---|---|---|---|---|---|---|
| `dchi2` (white weights) | 97.1 | 319.0 | 319.0 | 0 of 865, 1 of 735 | 0 of 288 | 0 of 199 | 2 of 279 (0.007) |
| `dchi2_cov` (the generator's covariance) | 97.1 | 252.4 | 252.4 | 0 of 865, 1 of 735 | 0 of 288 | 0 of 199 | 0 of 279 |

**No separation**: at a threshold that keeps the planets, the geometric route flags almost no
binary (at most 2 of 279 EB2, none of EB1). The threshold is set by PG's tail: PG's 99th percentile
(130.5) is above EB1's (110.7 and 81.5) and EB2's (128.2 and 101.6), so the planets' own spread
covers the binaries' range. These are calibration-sample fractions of one candidate route's
statistic, a diagnostic: they show that this route, as built, gives D1 no decisive test for folded
binaries; they do not show that no route exists. (d) cost 4.75 CPU-h (checkpoint projection 4.55;
the estimate was 7.7).

## The draft infeasibility records

**None.** Every bound leaves room under its stated assumptions: D2 (111 and 108 against 97), T2a
(0.909 to 1.0 against 0.897). D4 already passed in v0.5.2's forecast (0.122 INCONCLUSIVE against at
most 0.30). D1 for EB1 and EB2 has no bound; (d)'s geometric route did not separate them from the
planets, but it is a diagnostic of one candidate route, and its failure does not prove infeasibility.
D1 for EB1 and EB2 therefore has, after stage A, no route in hand: stage B has no D1 estimator to
build unless a new route is designed.

## The design questions

Argued both ways in [`v0.5.3-design-questions.md`](../../../plans/v0.5.3-design-questions.md),
**written and committed (`7896ba7`) before stage A's first run (`adc3f95` froze the design; the first
result is `7805a43`)**, validated by Codex in three rounds (`SURVIVED` in round 3). Nothing is decided:
(1) whether a warning-severity test's INCONCLUSIVE blocks the verdict; (2) the background
sub-check's alternative (a rise of 0.8 of the depth at power 0.95); (3) the sinusoid's small-residual
requirement. The known fact that D2 would pass, 98 against 97, if every non-sinusoid INCONCLUSIVE
blocker were removed is excluded there as a reason either way; any change applies only to a new
battery version, prospectively, and is accepted on data outside development.

Stage A adds facts for the maintainer, not arguments for a side: under kept retention the warning
blockers are already recoverable by a warning FAIL (rule 4 after rule 3 in `aggregate`), so question
1 changes which word is used more than which candidates are kept; (c1) shows the background's
error dominated by slow variability, which bears on question 2's "insufficient precision versus a
physical alternative"; (b)'s sinusoid bound shows three D2 planets below 0.95 even for the oracle
residual, which bears on question 3.

## The data outside development

**No confirmation set exists, and none was touched.** C1', C2' and C3' (`docs/plans/v0.5.1-plan.md`,
section 5) have never been drawn: no drand round was drawn and no real target selected in v0.5.1,
v0.5.2 or stage A. Stage A used only development records, development seeds and development light
curves already in the cache; (d)'s 1,900 new curves use v0.5.1's development seed at new indices,
disjoint from every confirmation seed (checked by Codex, round 1 of (d)). Pool metadata were examined
for T3b's planning in v0.5.2, so later population amendments are prospective, not blinded. Drawing a
confirmation set is a non-delegated stop.

## Stage B: proposed caps (for the maintainer's decision)

Stage B builds only what the bounds allow, then forecasts the targets on development data **before
any acceptance is priced**. Proposed scope, in order, cut from the end if a cap tightens:

1. **B1, estimators** (each frozen and reviewed by Codex before its calibration): an extension of
   A0's domain for the named refusals of (a) (pooled lag correlations below `MIN_PAIRS`, a PSD repair
   of the covariance); an `odd_even` estimator close to its joint Fisher bound (b); an efficient
   (GLS) sinusoid residual; a background-rise estimator that models the series' slow variability
   (c1). A new battery version; `src/` changes only after the stop that approves stage B. A change
   to `src/` changes the code hash that T2a's v0.5.2 fingerprint covers, even with its four named
   files untouched: v0.5.2's records stay reproducible from a frozen checkout of their commit, and
   stage B's forecast carries a fingerprint of its own.
2. **B2, recalibration on development** of each new estimator's error model, by the existing
   acceptance machinery's rules.
3. **B3, the forecast** of D2, D4 and T2a (the stratum above 20 sectors included, under a controller
   that survives Codex's review), on development data only. (d) showed no D1 route, so D1 for EB1
   and EB2 is not forecast unless the maintainer adds the design of a new route to stage B.

| Cap | Proposal | Basis |
|---|---|---|
| CPU-h | **150** (B1 40, B2 50, B3 45, reserve 15) | v0.5.2's forecast of D2, D4 and T2a cost 16.3 CPU-h without the stratum above 20 (about 12 more at 0.4 CPU-h per injection); recalibrations are unmeasured, so B2 is the least certain line |
| Review tokens | **1.0 M** | an independent review session at stage B's stop (Codex's tokens do not count, by the decision of 2026-11-09) |
| Agent-days | **8** | four estimators, each with a Codex review of design and implementation |

The machine rules, the pause at 20:00 on 18 November and a stop at every cap are unchanged.
**Acceptance, calibration and confirmation are not in stage B**: if B3's forecast passes every
outstanding target, they are priced and brought to the maintainer as their own stop, with the
draws of C1', C2', C3'. For scale, v0.5.2's `stage2/budget.md` priced the A0 acceptance alone at
1,482 to 1,932 CPU-h, and the whole schedule at 2,956 to 3,609 CPU-h, by sizing and rescaling.

## Round 3's closing criterion (the last of three)

Proposed; round 3 closes at the first of:

1. **Approved**: B3's forecast passes D1 (EB1 and EB2), D2, D4 and T2a, and then the acceptance,
   calibration and confirmation on data outside development pass, under their own approved caps.
2. **Not approved, forecast**: B3's forecast does not pass an outstanding target under that
   target's frozen rule, each read in its own direction (`calib05.c1.decision_rules`; v0.5's T2a
   rule): **D1** for EB1 and EB2, the SURVIVED fraction's Wilson 95 % upper end at most 0.10 and
   no more SURVIVED than v0.4; **D2**, the kept fraction at least v0.4's minus 0.10, the REFUTED
   fraction at most 0.05 and its Wilson 95 % upper end at most 0.10; **D4**, the INCONCLUSIVE
   fraction at target SNR 15 or more at most 0.30; **T2a**, the kept fraction at least v0.4's minus
   0.10 (0.897). A rule that is NOT DECIDABLE, or a forecast interval that leaves it undetermined,
   counts as not passed. The round closes without acceptance.
3. **Not approved, stage B**: no estimator of B1 survives its review and calibration, or a cap is
   reached with the forecast not done.
4. **Not approved, the maintainer's**: the maintainer stops the round, for example after deciding a
   design question differently.

**A consequence to weigh now:** D1 for EB1 and EB2 is an outstanding target and stage A leaves it
with no route ((d) did not separate). Unless a new D1 route is designed and survives, criterion 1
cannot be met, whatever D2 and T2a do; stage B could then at most show D2, D4 and T2a reachable, a
partial result recorded as such. In every "not approved" case, the advance rule's end applies: the maintainer decides between
changing the approach, recording infeasibility (the material of this report and of B), or pausing
the line. No target is relaxed and the rule of evidence stays, whatever the case.

## Where test renames are recorded

#210 (CI time) carried the record of test renames and removals, because `scripts/ci_ids_check.py`
reports a rename as one ID removed and one added; #210 is now closed. **Proposal:** an append-only
file in the repository, `docs/testing/test-renames.md`, one row per change (date, commit, the old and
new test IDs, the reason, the CI run whose `ci_ids_check` showed it), written in the same commit as
the rename; earlier entries never edited (a correction is a new row). The rows of #210 are copied in
as its first entries, with the comment links. A file is versioned with the code and readable
offline; an issue comment is neither. Alternative: a new open tracking issue, as #210 was.

## The project folder (item 4 of the decision)

The adequacy check, the plasmode, stage 1 (`e1` to `e3`, the worksheet) and v0.5.1's WP5 were
archived to the Drive: 12,438 files, 804,486,375 bytes, each copy checked by size and SHA-256 against
the manifest kept in `.cache/v053/archive/manifest-2026-11-11.json`; only then deleted, inside
`.cache/` only. T2a's light curves and the worktrees of the locks are kept.

## Sources

Literature read for this report, with URLs, dates and excerpts:
[`docs/plans/sources/v0.5.3-stageA-literature-2026-11-11.md`](../../../plans/sources/v0.5.3-stageA-literature-2026-11-11.md)
(the Kepler DR25 Robovetter's minor flags; Christiansen et al. on injection-recovery; Burke on
per-target detection efficiency; Battley et al. 2022 on scattered light in TESS). They inform the
discussion only; no number of stage A comes from them.

## Consumption

| Cap | Spent | Of |
|---|---|---|
| CPU-h | **7.78** ((a) 2.35, (b) 0.67, (c) 0.02, (d) 4.75) | 50 |
| Review tokens | 0 (no independent review session in stage A; Codex's tokens recorded in the consensus record) | 0.5 M |
| Agent-days | 0.74 wall-clock upper bound, 0.21 active (`caps.json`, check of 11:47 UTC) | 4 |

No cap was reached. (c3) cut and (d) under its estimate leave most of the CPU unspent.
