# X2's execution package (for the maintainer's authorization; not run)

Prepared on 2026-10-21 under the maintainer's decisions after X0c and X1b (items 3, 4, 6, 7, 8), and
revised after Codex's review of the package (section 8). **X2's lot has not run.** This package is
what the lot needs; it runs only after the maintainer's authorization, and the work stops here until
then. X3's definitive calibration waits for X2's result; no threshold or gate changes only to correct
the old cases.

## 1. What is run, and what is decided

- **The declaration:** [x2-declaration.md](x2-declaration.md), revision 2 (X2-A, geometry and
  identity; X2-B, the calibration of the uncertainties, decided by the standard deviation), with its
  metrics, rules, criteria and evaluation procedure, committed before the lot.
- **The lot:** 80 cases (4 groups × 20, the declared rule) × 100 noise realizations = **8000 light
  curves**, the constant scenario, every observing year's round by `calibration_measurement` on the
  study's M4 configuration (`m4-configurations/rmin-study.json`), with the noiseless twin and the
  registered windows. Records only; no verdict, no study result.
- **The evaluation, after the lot:** `x2_study.py check`, then `x2_study.py evaluate` (X2-A's and
  X2-B's quantities and verdicts, exactly as declared), a results record, Codex's review, a stop.

## 2. The code (in this commit, with its tests)

| File | What |
|---|---|
| `docs/validation/v0.2.1/population/x2_study.py` | the cases, the seeds, the realizations, the record (with the registered windows), the record's completeness check, the resumable lot runner, the evaluation's driver (`run`, `check`, `evaluate`) |
| `docs/validation/v0.2.1/population/x2_evaluate.py` | X2-A (identity, measurement centers, offsets, overlaps with the registered windows, the three factors, the cause, the FAIL) and X2-B (the case-year statistics, the cluster bootstrap, the verdicts with the SD/MAD rule), and `evaluate`, the whole declared output with the findings' order |
| `tests/test_x2.py` | 24 tests: the cases and the seeds as declared; a realization with the case's own seed is the case byte for byte, another seed changes the noise only; the measurement centers equal the engine's; the overlaps use every registered window (a true transit inside a control window's mask is masked); each cause, the ties, the undefined factors and the exact three-factor split; the FAIL and the counts over every round, those without an ephemeris included; the case-year statistics, the bootstrap's fixed seed, the verdicts and the scales' disagreement; the whole evaluation's order and denominators; the resumption (below); an incomplete or misplaced record refused at the check and at the relaunch; the manifest bound to the code and published atomically; the ceiling read right before each submission; the workers explicit; a record never replaced; a write cut short leaving no record; the truth unreadable during the engine's calls |

`population_v2.py` is frozen (its SHA-256 pinned by `population_v3.py`) and is **not** edited: a
realization is the case built by it with its noise drawn again, sector by sector in time order as it
draws it; with the case's own noise seed the result equals the case byte for byte (checked on one
case of each group and mechanism, and in the tests).

## 3. The seeds

[x2/x2-seeds.json](x2/x2-seeds.json) (SHA-256
`84a77ccde92afe0390512b9a1f3c5ca8f57928f458130e9724d829f5d48f3884`), made by
[x2/scripts/x2_seeds.py](x2/scripts/x2_seeds.py): **8000 seeds, all distinct, no collision** with the
696 800 seeds of the earlier lots checked (each case's seed and the noise seed of its first draw, in
bs-choice, the R_min study's 64 prefixes, the timing lot and X2's own cases). The bootstrap's seed:
the first 8 bytes of the SHA-256 of `refute/v0.2.1/stage-1/X2/bootstrap`.

## 4. The resumption condition (item 6), met

**The design:** the manifest (the tasks, the configuration, the resolved plan's SHA-256, the code's
digest over `src/refute`, the lock files and the lot's modules, and the numeric environment) is
published first, atomically, and must match on a relaunch; a task whose record exists **and is
complete** is not run again, and an existing incomplete or misplaced record stops the run (it is never
replaced); a record is written to a temporary file, flushed to disk, then linked to its name (the link
fails if the name exists) and the temporary name removed, so a record file is complete or absent; a
leftover temporary file starts with a dot, is never read as a record, and is listed in the run report;
the ceiling is read right before each submission; the workers are given explicitly (22), never read
from the environment.

**The tests** (`tests/test_x2.py`, with the real engine on a test plan): a lot stopped by its deadline
after one task, with a truncated temporary file planted, relaunched, gives the records of a continuous
run **byte for byte**; and the refusals listed in section 2.

**The check on the real configuration** (`x2/scripts/resume_check.ps1`, `x2/scripts/compare_lots.py`,
result [x2/resume-check.json](x2/resume-check.json), SHA-256
`b04e2a5ccf358db79cc6380e1d313710f9ec5c2699136d38a46b611169029a3e`, its line endings LF), with the
final code (the manifest's code digest
`2918fea526a8da513e8580bba55cd546348ac09c5bf53f9070a7585dbd7398bb`): a subset of
32 tasks (2 cases per group × realizations 0 to 3) on processors 8 to 31 with 22 workers, run
continuously; the same subset started again, **stopped by its own process ID and its 22 workers'
IDs** once 14 records existed, then relaunched to completion: **the 32 records are byte for byte those
of the continuous run**, no integrity problem, no temporary file left. (The check was run four times
as the code changed during Codex's review, each with the same result: 16, 14, 14 and 14 records at
the stop; the record here is the last, with the code of this commit.)

**Disclosed:** those 32 realizations are tasks of the lot itself, made before the lot to check the
resumption and the evaluation's pipeline (realizations 0 to 3 of the first two cases of each group).
What was read of them: by the agent, the integrity checks, the record digests and the evaluation run
once printing its structure only (keys and counts of rows), no value; **by Codex, while reviewing the
code** (Codex's second review states it): one train ephemeris's numbers, the counts of
`measurement_status` and that 10 of their 80 rounds had no train ephemeris, which showed a defect of
the code (fixed). No metric, criterion or rule was changed because of a value read. The lot is
generated again from nothing in a new folder; these checks' folders are not part of it.

**A resumption of the real lot is a rerun:** if the lot is interrupted, its relaunch needs its
approval recorded in a GitHub issue first (CLAUDE.md), with the reason and the procedure (the same
command on the same folder, `-RunDir`).

## 5. The run (proposed)

- **Where:** `.cache/x2-lot/<UTC date>/` in the integration worktree; the manifest, the records and
  the run reports there; the results committed afterwards with their digests.
- **Command** (one window, not as Administrator; the affinity set first, then inherited by the
  workers): [x2/scripts/run_x2_lot.ps1](x2/scripts/run_x2_lot.ps1) (the affinity mask `0xFFFFFF00`,
  the configuration `m4-configurations/rmin-study.json`, the code's commit printed,
  `x2_study.py run <folder> --workers 22 --deadline-hours 11`, then `check`).
- **Affinity and workers:** logical processors 8 to 31; **22 workers**, explicit.
- **Cost:** with the final code (the registered windows recomputed on the evaluator's side add a
  second train pass per round), the resumption check's continuous runs did 32 curves in 68 to 71 s on
  22 workers (process start included), about 0.45 curves per second: **about 5 h** for 8000; three-year
  and variability cases are slower than this subset's mix, so the estimate is **5 to 7.5 h** (the gain
  of more workers is measured, not assumed).
- **Ceiling:** `--deadline-hours 11` (1.5 times the upper estimate): no task is submitted after 11 h,
  those in flight end, the lot is then incomplete and reported as such; nothing is extended without
  the maintainer.

## 6. CI (item 8)

heavy-a's jobs on `acc9dda` (run 39696817920): 13.8 and 11.5 min on Ubuntu, **15.6 and 22.3 min on
Windows** (11.8 to 11.9 min before the 32 controls, run 39665417272): over the 15-minute target.
**Changed:** the 32 controls now run in parallel worker processes (locally 107 s instead of 448 s;
on CI's 4-processor runners the default gives 2 workers), and `tests/test_spec_b.py` and
`tests/test_x2.py` move to a new fifth shard, `heavy-d` (`scripts/ci_shard.py`, the workflow's
matrix, and a new test that the matrix lists every shard). The `rest` shard is **also over the
target** (17 to 46 min on `acc9dda`, 30 to 32 min before it): a breach that predates X1b, recorded
and not addressed here (its heaviest files locally: `test_rmin_derivation.py` 520 s,
`test_prewhiten.py` 193 s, `test_holdout_capacity.py` 155 s, `test_rednoise_propagation.py` 106 s);
rebalancing it is a separate change. The durations after this commit are read on its CI run.

## 7. What the maintainer is asked

To authorize the lot of section 5 (its size, seeds, affinity, workers, cost and ceiling), or to
change any of it. Nothing else is asked; X3 is not part of this request.

## 8. Codex's review of the package (OBJECAO, all points applied before this record)

1. Rounds without a train ephemeris had no cause and broke the counts: every round now gets one
   (`twin unavailable`), and the counts run over every round.
2. The masks were an envelope of the transit windows only: the record now carries the **registered
   windows** (transit, control, replica, their own widths), recomputed with the engine's functions
   after its calls, and the overlaps use them exactly.
3. The check accepted incomplete or duplicated records: each record is now checked whole (format,
   task, seed, configuration, years, one round and one windows entry per year, truth), at its own
   path, at the relaunch and at the close.
4. The manifest was not bound to the code and was written in place: it now carries the plan's, the
   code's and the environment's identity and is published atomically.
5. The declared output was not a complete procedure: `x2_evaluate.evaluate` now gives it whole (the
   FAIL rows, the offsets in `σ_T,max`, the layouts, the exclusions, the subset `same` with `L ≥ 0.8`,
   the findings' order), and the FAIL counted is fixed in the declaration (the measurement's FAIL rule,
   the capacity decisions not enforced).
6. The ceiling was read before the wait: it is now read right before each submission; the workers are
   explicit. And `tests/test_spec_b.py`'s worker test now crosses a real process boundary.

Codex's second and third rounds (OBJECAO, applied): the record files' paths compared exactly with the
tasks' (a `0000.json` beside `000.json` refused); the sectors and years checked against the case's
layout and every round's calibration-record fields required; the per-round metrics, the case-year
statistics and section 7 kept in the output; the evaluator inside the code's digest and the
evaluation refused with another code, plan, configuration or environment than the lot's; the
disclosure of what was read of the check's realizations made exact; and section 7's counterfactual
limited to the capacity refusals, the structural impediments counted apart. Each with its test.

**Sabotages of the fixes** (each applied to the staged code, `tests/test_x2.py` run, the file
restored; the diff empty after each), all caught: S1 the ceiling read before the wait (1 test
failing); S2 an existing record skipped without its check (1); S3 the manifest without the code's
digest (1); S4 the masks of the transit windows only (1); S5 a round without an ephemeris left
without a cause (2).
