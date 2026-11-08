# v0.5.1 Battery corrections ended as not approved (2026-11-08)

**The maintainer's decision of 2026-11-08** (#208; [plan](../../plans/v0.5.1-plan.md), amendment 11):
v0.5.1 closes before its confirmation as **not approved**, by stop rule 6 of the plan (section 10:
"an incomplete phase is never a success"). No target of v0.5.1 passed or was declared infeasible;
all stay outstanding. It counts as the first of the three correction rounds of the advance rule
(`ROADMAP.md`). **No confirmation data was used, no drand round was drawn, no protocol or lock was
made, and no real target was selected for it.** No gate review was run and none passed; **no exit
criterion of v0.5.1 is ticked**. Nothing is deleted or rewritten. `method_status: not_validated`.

The targets, all outstanding: D1 for EB1 and EB2 (#202), D2 and D4 (#201), T2a (#201). The targets
that must not regress (D1 for SE, V1, V2, ER, NR; D3; D5; T2b; T2c; T3a; T3b) were not measured
either.

## What led here

Every acceptance run of this phase ran once on frozen code, and its result stands as it came out:

- **A0, the empirical per-event errors.** The first run stopped: A0.1 failed in 12 of 15 strata, the
  runner having handed raw curves to functions that receive the flattened one in the pipeline. The
  maintainer approved a second run under conditions (a byte-identity proof of the series first; new
  seeds; only `SURVIVED` runs); it ran once and A0 was **not accepted** (below).
- **WP3 (b), the sinusoid per harmonic.** After its byte-identity proof and a fourth, authorized
  Codex round (`SURVIVED`), it ran once and was **not accepted** (below).
- The analysis of item 3 ([feasibility/strategy/README.md](feasibility/strategy/README.md), commit
  `44c9b4a`; Codex `SURVIVED` in round 3; development data only) showed what A0's result implies; the
  maintainer chose path B, recommended by the agent and by Codex.

## What was built, what was accepted, what was not

| Work package | State at closing |
|---|---|
| WP1, the feasibility forecast | done; a diagnostic ([feasibility/README.md](feasibility/README.md)) |
| A0 (`src/refute/packs/tess/a0.py`) | built; acceptance run once; **not accepted** |
| WP2, per-event tests made decisive (#209) | wired on A0; acceptance not run (it depends on A0) |
| WP3 (a), `aperture_depth` and `systematics` with A0's errors; amendment 6's applicability rule | built; acceptance not run (it depends on A0) |
| WP3 (b), the sinusoid per harmonic | built; acceptance run once; **not accepted** |
| WP3 (c), `period_alias` | built; acceptance not run |
| WP3 (d), `odd_even` with the matched trapezoid | built; acceptance not run; its statistics are A0's rows, which failed |
| `duration_excess`, the diagnostic of the eclipsing-binary route | built as a diagnostic; two development measurements; acceptance rows not run |
| WP4, INCONCLUSIVE classes | built and tested (`tests/test_v051_wp4.py`) |
| WP5, version 3 and the historical records | row 5.1 (load-time refusal) in the suite; row 5.2 complete under amendments 7 and 8: v0.1 failed reproduction with current-code inputs and was reproduced at its locked tag under the approved exception; for v0.2, v0.4 and v0.5, current outputs are byte-identical to the v0.5.0 calibration-lock code on the same inputs; against the recorded dossiers, class (i)/(ii)/(iii) differences are respectively 2/13/0, 2/0/0 and 2/0/0; row 5.3: 260 of 260 records of the v0.5 C1 prefix reproduced; row 5.4: the packaging rehearsal passes in the suite |
| Combined non-regression gates, D lines | not written, not run |
| WP6, CI time (#210) | shards in place; **the criterion is not met on the last run read**: 36.4 minutes for the longest job (run 42470952364, windows-2025 / Python 3.12 / rest), against 30; earlier runs 27.1 to 27.6 |
| Calibration C1', C2', C3' | claim and task scaffolding built and exercised on synthetic rehearsal data; confirmation not run; no confirmation protocol or calibration lock |

Version 3 of the battery (`discovery.version: 3`) stays in the repository, was never locked and was
never used in a confirmation. The v0.4 and v0.5 batteries are unchanged.

## The results as they came out

**A0, second run** ([acceptance/a0r2-result.json](acceptance/a0r2-result.json), commit `7fdb79f`; 101.9
processor-hours; 0 errors).

| Row | PASS | FAIL | NOT DECIDABLE |
|---|---|---|---|
| A0.1 per-event pulls | 10 | 5 | 0 |
| A0.2 group statistics | 162 | 138 | 60 |
| A0.3 window structure | PASS | | |
| A0.4 sectors of different noise | 87 | 117 | 66 |
| A0.5 unequal events | 493 | 225 | 1,172 |
| A0.6 independence beyond lag 5 | reported only | | |
| A0.7 heterogeneous strata (the rule) | 4 | 14 | 0 |
| A0.8 conditional phase-0.5 rule | 195 | 98 | 712 |

Six of six sabotages were recorded as detected (three of them not distinguishable from the
unsabotaged rows: strategy README, section (d)).

**WP3 (b)** ([acceptance/wp3b-result.json](acceptance/wp3b-result.json), commit `db9fdd6`; 15.58
processor-hours; 0 errors; `rows_pass: false`): 3.3, 3.4, 3.5, 3.6 and 3.8 (a), (b) pass; 3.2 fails
in its 4 cases (false failures 37 to 50 of 200 against a limit of 2, in the noise models with a
stellar trend); row 3.2's SNR-20 correlated-trend case also fails the detectable-fraction condition,
183/200 against 184; 3.1 is NOT DECIDABLE in its red-noise case (no trial met its construction); 3.7
fails in one case (183 against 184); 3.8 (c) fails in the two trend cases. Three of three sabotages
detected on their own targets.

**Development measurements** (they decide nothing): WP1's forecast, the D1 route search (recorded
only, #215), the `duration_excess` measurements, the SAP rule's effect (0 verdict changes of 91),
item 3.

## The diagnosis of item 3 (commit `44c9b4a`; development data; it decides nothing)

- By the acceptance's rule, with the noise model unknown at run time, the strict reading accepts no
  per-event cell and no cell of `odd_even`'s statistic. Group rows cover 2 to 4 sectors. Of the
  development references, 46/100 C2 stars have at least five light-curve files and 16/22 C3 targets
  have at least five sectors; these counts do not establish their measured-event sector counts.
- A development forecast: as built D2 kept 0.879 and D4 INCONCLUSIVE 0.030; with the strict rule,
  kept 0.000 and INCONCLUSIVE 1.000. D2's kept requirement and T2a would fail whenever their paired
  v0.4 kept fraction exceeds 0.10; D4 depends on the data; D1 would be met vacuously.
- The real pools: 901 planets never walked; 22 eclipsing-binary false positives never walked, against
  41 walked per confirmation at v0.5's yield.
- The matched estimators' mean bias comes from selecting the trapezoid's shape, epoch and duration on
  the same data, not from a half-normal at the depth's bound. The decisive `matched_diff` fails on
  its scatter (standard deviation 1.41 to 1.55 in correlated and long noise).
- The lag window is not the cause of the 1.10 to 1.21 dispersion in those simulations. The leading
  explanation is the detrending mask (real windows masked, pseudo-windows not): a diagnostic supports
  it and does not isolate it.
- Under the perfectly calibrated Gaussian-pull model with 400 trials per row, about 77 failures are
  expected across A0's 1,548 decidable rows; 597 were recorded.

## Lessons

1. **A runner hands the tests the pipeline's own series.** A byte-identity test comes before any
   acceptance run (A0's first run).
2. **Test equivalent treatment of real and pseudo-windows.** The mask asymmetry is the leading
   explanation of the dispersion; isolate it experimentally before adopting a correction.
3. **An estimator's calibration must include its selection**: a shape fitted on the same data the
   depths are measured on shifts them.
4. **A "pass every row" acceptance is a design limit**: with many rows at a two-standard-error band,
   a perfectly calibrated estimator fails some. A criterion must be fixed before the code.
5. **A sabotage must have an effect distinguishable from an ordinary run**; a failing row is not
   detection when the same row fails without it.
6. **What the code can know at run time has to be settled before a rule depends on it** (the noise
   model is not known at run time; real stars have more sectors than the calibrated cells).
7. **A target can pass vacuously** (D1 with no curve SURVIVED) and such a PASS has to be excluded in
   advance.
8. **Costs come from a probe of the actual workload.** The caps were set before version 3 existed
   (amendment 10), and the development smoke of WP3 (b) was ten times too low; the 5 % probes were
   right (14.8 projected, 14.5 spent).
9. **The real-binary false-positive pool is scarce.** Resolve the failed acceptances and the
   conditional failure forecast before spending fresh confirmation controls.
10. **The agent-day ledger the plan requires was not kept** (below).

## Use of the caps

| Cap | Value | Used | Note |
|---|---|---|---|
| Development processor-hours | 200 (warning at 160) | about 157.8 | before A0's second run 36.4; A0's second run 101.9; WP3 (b) 15.58; item 3 3.91 |
| Calibration processor-hours | 80 (warning at 64) | 0 | not started |
| Reviewer tokens | 1.0 M | 0 | no independent review session ran |
| Disk | 20 GB | about 0.84 GB in `.cache/v051` | point measurement of 2026-11-08; `.cache/v05` 0.30 GB (its baseline) |
| Agent-days | 12 (warning at 9.6) | **not measured** | **Deviation:** the plan's accounting (section 10: each working round's wall time, logged) was not kept for every round, and `.cache/v051/cost.jsonl` was not written. An upper bound for Claude's share from the wall clock since the opening (2026-11-06 about 12:50 UTC to the closing) is about 49 hours, or 6.2 agent-days; Codex's time was not summed, so this bounds Claude's share only and does not demonstrate compliance with the total cap |

Two work allocations were exceeded and stayed below their 1.5-times stopping thresholds: WP1, 5.03
processor-hours against 4; the D1 route search, 12.04 against 10.

## Preserved, unchanged

Every FAIL, every record and every criterion of v0.5.1: the plan and its amendments, the acceptance
documents, the runners and their proofs, the result files, the feasibility and strategy analyses,
Codex's answers (`docs/plans/v0.5.1-consensus/`), the code of version 3. Built components are
distinct from a validated method, which v0.5.1 did not deliver.

## What this does not show

Not a proof that the corrections cannot work, that any target is infeasible, or that A0's design is
wrong in every respect. Not a verdict on any real target. The forecast and the diagnosis are
development readings. The mask explanation is the leading one, not a demonstrated cause.

## Left open

- The scope of v0.5.2, correction round 2: proposed to the maintainer before any code.
- Issues kept open with the part left: #201, #202, #203, #204, #205 (beyond the INCONCLUSIVE
  classes), #209 (WP2 not accepted), #210 (CI above 30 minutes), #211, #212, #213, #214, #215. #208
  is closed by comment after the closing commit has a green CI.
- The note for the package of 19 November: the draft README of the v0.5.0 release cites "v0.5.1
  Battery corrections (to be scoped)"; it will have to say that v0.5.1 closed as not approved and
  that v0.5.2 is next (the drafts are not touched now).
