# v0.2.1 CI time, option D (one H9(a) analysis for both rules): acceptance criteria

Status: **criteria fixed before any validation runs.** This file is committed on its
own, before the tests and the code it describes. Written 2026-10-11 on branch
`claude/v0-2-1-gauntlet-fixes-13f5e7`.

## Problem

Every CI job runs the whole test suite on a 4-core GitHub runner
(`os.cpu_count()` = 4, `REFUTE_WORKERS` = 4, no `pytest-xdist`). The maintainer's
target is **at most 15 minutes per job**. The rule decided on 2026-10-10: if every job
is at or under 15 minutes, stop; otherwise choose between marking the slow tests and
running each H9(a) analysis once for both rules. The second option (D) was chosen.
This document fixes how D is done and how it is judged.

### Baseline (CI run 38098624281, commit `89bd3b4`, 2026-10-11)

| Job | Job wall time | pytest | H9(a) fixture | H4 fixture | Blindness fixture |
|---|---|---|---|---|---|
| ubuntu-latest / Python 3.12 | 26:11 | 25:55 | 771 s | 325 s | 148 s |
| windows-latest / Python 3.12 | 25:17 | 24:41 | 716 s | 288 s | 133 s |
| windows-latest / Python 3.13 | 18:10 | 17:29 | 512 s | 209 s | 96 s |
| ubuntu-latest / Python 3.13 | 14:36 | 14:19 | 422 s | 186 s | 86 s |

Fixture times are the `setup` durations reported by `pytest --durations=25`:
`tests/test_ebcatalog_own_tic_e2e.py` (module fixture `analyses`),
`tests/test_holdout_train_validity_e2e.py` and `tests/test_holdout_blindness.py`.
All 489 tests passed in every job. Three of the four jobs are above the target.

The H9(a) fixture is the largest single cost. It runs **265 complete analyses**:
13 scenarios x seeds 0-9 x two rules (the default `same_photometry_catalogs:
["TESS-EB"]`, "on", and the switch `same_photometry_catalogs: []`, "off"), plus 5
`blend` analyses with a neighbor's catalog row. The two rules differ **only in the
`eb_catalog` test**: the detrending, the search, the gauntlet tests a-d, the rest of
the battery and the blind holdout do not read `test_plan.gauntlet.eb_catalog`. Each
pair therefore repeats the same expensive work to change one test.

## Definition of option D

### Production seam (behavior-neutral refactor of `src/refute/packs/tess/pipeline.py`)

Two steps that `analyze_data` already performs are extracted into named functions,
so that production and the test helper call **the same code**:

- `eb_catalog_test(data, candidate, plan, catalogs, catalog_scan) -> TestResult`:
  the call of `check_eb_catalog` that `battery_tests` makes today (target key, star,
  the final candidate's period, `plan.gauntlet.eb_catalog`). `battery_tests` calls it.
- `conclude_analysis(search, flattened, gauntlet, holdout, catalogs_configured)
  -> Analysis`: the coverage rule (`enforce_coverage`) and the aggregation
  (`aggregate` with `expected_tests`) that end `analyze_data` today.
  `analyze_data` calls it.

Nothing else in the pipeline changes. The outputs of every analysis are unchanged
(checked by F4 below). The code hash changes, as it already does for every v0.2.1
change; the v0.2 lock is verified at `cc9d104` and is not affected.

### Shared path (test helper in `src/refute/packs/tess/synthetic.py`)

A picklable helper runs, for one scenario and seed:

1. the **complete analysis with the default rule**, through `analyze_data`
   exactly as `analyze_scenario_with_catalog` does today (the "on" analysis);
2. for the switch-off rule, the **"off" analysis derived from the same expensive
   work**: the `eb_catalog` test is **recomputed by `eb_catalog_test`, that is by
   `check_eb_catalog`, with `same_photometry_catalogs: []`**, it replaces the
   `eb_catalog` test of the gauntlet, and the analysis is concluded again by
   `conclude_analysis` (coverage rule and verdict aggregation recomputed). When there
   is no candidate, `eb_catalog` is "not run" under both rules (as in
   `attack_candidate`) and only the conclusion is recomputed.

**Prohibited:** producing the switch-off result by editing the default result (for
example changing the severity of `eb_catalog` from WARNING to FATAL, or copying the
default verdict). Both rules pass through the production decision code:
`check_eb_catalog` for the test, `enforce_coverage` and `aggregate` for the verdict.
Sabotage S7 below checks that such a shortcut would be caught.

### Complete switch-off runs kept as the control

The fixture also keeps **complete switch-off analyses** (`analyze_data` with
`same_photometry_catalogs: []`, no sharing) for **seeds 0-1 of every scenario**. They
are the reference against which the shared path is checked (E1).

### What the fixture runs after D

| Analyses | Before | After |
|---|---|---|
| Default rule, complete (`analyze_data`) | 130 | 130 (each also yields the derived switch-off analysis) |
| Switch off, complete | 130 | 26 (seeds 0-1, control for E1) |
| `blend` with the neighbor's row, complete | 5 | 5 (unchanged) |
| **Total complete analyses** | **265** | **161** |

All tasks run in one process pool (`run_processes`, `default_workers()`), as today.

### What stays exactly as it is

- The text, seeds and assertions of cases B1-B3, C and D of
  `docs/validation/v0.2.1/H9a-acceptance.md`: B and C on seeds 0-4, **D on seeds 0-9
  for every scenario** (the D seeds are not reduced). Their "off" analyses now come
  from the shared path; for seeds 0-1 E1 ties them to the complete ones.
- Every other test module, the CI workflow, `REFUTE_WORKERS`, and the slow tests (none
  is marked or skipped).

## Acceptance criteria

Option D is accepted when every item below holds.

### E. Shared path equals the complete path (new cases in `tests/test_ebcatalog_own_tic_e2e.py`)

- **E1. Exact equality, every scenario, seeds 0-1.** For each of the 13 scenarios and
  seeds 0 and 1, the derived switch-off analysis equals the complete switch-off
  analysis:
  - the per-target verdict record (`build_result` with the switch-off plan and the
    same target and context, serialized as JSON with sorted keys) is **identical
    byte for byte**: verdict, verdict reason, candidate, ephemeris, every test (name,
    status, severity, message, metrics, thresholds, coverage), holdout rounds, search
    diagnostics and key values;
  - the gauntlet test lists (before the coverage rule) are identical (`to_dict`).
  No tolerance: the expensive work is the same computation in both paths.
- **E1 premise (non-vacuous).** For `planet` seeds 0 and 1, the derived switch-off
  analysis differs from the default one (switch off: REFUTED with `eb_catalog` fatal;
  default: WEAKENED with `eb_catalog` warning). Without this, E1 could pass by
  copying the default analysis.

### F. No regression

- **F1.** Cases B1-B3, C and D pass, unchanged in text and seeds.
- **F2.** The 5 neighbor-row `blend` analyses stay complete analyses (B3 unchanged).
- **F3.** The full suite passes. The only test module edited is
  `tests/test_ebcatalog_own_tic_e2e.py`, and its existing cases are edited only in the
  fixture that supplies the analyses.
- **F4.** The refactor is neutral: `tests/test_workers_equivalence.py` and every
  existing pipeline, holdout, catalog and calibration test pass unchanged.
- **F5.** `ruff check .` and `ruff format --check .` pass.

### S. Sabotages (run after the code passes, never committed)

Each run against `tests/test_ebcatalog_own_tic.py` and
`tests/test_ebcatalog_own_tic_e2e.py` only, reverted with an empty `git diff` before
the next. Sabotage scripts are written to files with the editor, not generated by
shell heredocs (Amendment 1 of H9(a) records a failed first run caused by a heredoc).

**Redone, as planned in H9(a)** (applied to `src/refute/packs/tess/ebcatalog.py`):

| Sabotage | Must be caught by |
|---|---|
| S1. The rule is ignored (own-TIC same-photometry matches stay fatal) | A1, B1, C2, C3 |
| S2. Any TESS-EB row counts as the target's own (neighbors downgraded) | A2, A5, B3 |
| S3. Position-only matches (Gaia rows) downgraded | A3 |
| S4. The catalog list is ignored (any catalog with the target's TIC downgraded) | A4 |
| S5. The downgrade gives PASS instead of a warning | A1, B1 |
| S6. The switch is inverted (empty list downgrades, default does not) | A1, A7 |

E1 is **not** expected to catch S1-S6: they change the production rule, which both the
shared and the complete path run. The failing counts may differ from H9(a)
Amendment 1 because the module now has more cases; the planned catches must not.

**New, against the shared path** (applied to the helper in `synthetic.py`):

| Sabotage | Must be caught by |
|---|---|
| S7. The switch-off result is fabricated from the default one: `eb_catalog` severity changed from WARNING to FATAL and the verdict re-aggregated, without calling `check_eb_catalog` | E1 |
| S8. The switch-off analysis keeps the default `eb_catalog` test (not recomputed) | E1 and its premise |
| S9. `eb_catalog` is recomputed but the analysis is not concluded again (default verdict kept) | E1 and its premise |

### T. Time (measured, never assumed)

- **Local:** the H9(a) module, before and after, with the usual CPU affinity
  (logical processors 8-31; the first four physical cores left to Windows), wall
  time and the fixture's `setup` duration.
- **CI:** after the push that the maintainer approves, the job wall times and the
  `--durations` lines of every job, compared with the baseline above.
- **Estimate (not a result).** Scaling the H9(a) fixture by 161/265 saves about 40%
  of it: roughly 300 s on the Python 3.12 jobs and 165-200 s on the Python 3.13 jobs.
  On the baseline that would put the Python 3.13 jobs near or under 15 minutes and
  leave the Python 3.12 jobs around 20-21 minutes.
- **Decision rule.** If every job is at or under 15 minutes, the CI-time work stops.
  Otherwise this document records the measured times and states only that **the
  options evaluated so far (`REFUTE_WORKERS` set to all runner cores, then option D)
  have not yet reached the target**. The 15-minute target is not declared
  unreachable. Any further option, or any revision of the target, is an explicit
  decision of the maintainer, recorded here before it is implemented.

## Risks

- **A future step added to `analyze_data` after the gauntlet.** The derived analysis
  would miss it unless it goes through `conclude_analysis`. The seam is in production
  code, so the helper follows it; E1 compares the complete records and would show a
  missing step on seeds 0-1.
- **Hidden state in the `eb_catalog` decision.** Today it reads only the catalog
  entries, the scan record, the target key, the star and the final period. If that
  changed, E1 is the check, on seeds 0-1 only.
- **Seeds 2-9 rely on the shared path without a complete control.** That is the price
  of D; E1 on seeds 0-1 of every scenario, with exact equality, is the evidence that
  the path is the same.

## Open items (not part of D)

- The Python 3.12 jobs take about 1.5-1.8 times as long as the Python 3.13 jobs on the
  same runners and the same tests. The cause is not investigated.
- After D, the next largest costs are the H4 property fixture (186-325 s) and the
  blindness fixture (86-148 s). No change to them is planned here.
