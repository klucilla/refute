# Audit of exit criteria 1, 4 and 5 at the reopening of v0.2.1 (2026-10-17)

Status: **audit record.** Read-only checks on the branch `claude/v0-2-1-reopen` (Phase I).
It changes no criterion, threshold or result. Each criterion is quoted from ROADMAP.md,
"v0.2.1 Gauntlet fixes", Exit criteria.

## Criterion 1: acceptance criteria, metrics and regression cases before tests and code, with synthetic must-pass and must-fail cases including correlated noise

**Order.** The records of H7, H4 and H9(a) were committed before their tests and code; the
times are in `../pre-document-runs.md` (table "Order of the documents, tests and code"), with
the development runs and the amendments made after the code declared there. The records of
the workers equivalence and of CI option D state the same order in their status lines. The
record of #23 (`issue-23-acceptance.md`) was committed in `53e87f9`, before its tests
(`227b7b3`) and its code (`fd87ce1`).

**Correlated noise: not covered.** No case of any of these records uses correlated noise:

| Record | Noise of its synthetic cases |
|---|---|
| H7 | the named scenarios of `synthetic.py` (white only) |
| H4 | the same (white only) |
| H9(a) | the same (white only) |
| workers equivalence | `planet`, `eb_secondary`, `vanishing` (white only) |
| CI option D | the H9(a) scenarios (white only) |
| #23 | `planet` (white only) |

The generator of the test suite, `make_lightcurve` in `src/refute/packs/tess/synthetic.py`,
adds Gaussian white noise only, and `scenario_data` uses only it. The only correlated noise
in the repository is in the population harness (`../population/population_v2.py`, `_noise`:
600 ppm white plus a 600 ppm AR(1) with a 1-hour time constant) and in the H3 measurement
(`../H3/measure.py`), neither of which is part of the suite. The one suite test that names red
noise, `tests/test_gauntlet_odd_even.py::test_scatter_inflates_errors_so_red_noise_is_not_a_detection`,
predates v0.2.1.

**Consequence.** Criterion 1 is not met for the changes already made. The prospective
extension is `correlated-noise-acceptance.md`; it records the historical absence and does not
make the new cases retroactive. The TESS corrections (M4, M5) never reached the stage of an
acceptance record.

**Also found:** commit 3b of CI option D was never made; its 16 cases (E0, E1 for 13
scenarios, the E1 premise for 2 seeds) are still `xfail(strict=True)` in
`tests/test_ebcatalog_own_tic_e2e.py` (the mark `RED_UNTIL_3B`). The 15-minute target of CI
was reached otherwise, by the three shards of `scripts/ci_shard.py` (PR #73, merged
2026-10-15): the largest job of run 39075388034 took 14:36.

## Criterion 4: no synthetic test that passes at the start of v0.2.1 fails at its end without a justification written before

**Tool.** `scripts/check_test_baseline.py` gives each of the 225 node IDs of
`../baseline/v0.2.0-passing-tests.txt` one outcome in a JUnit file (passed, failed, skipped or
missing) and fails on any regression that a justifications file does not name.

**Run at the reopening.** The full suite in the worktree, at `80abc00` with the change of
`26c8292` (the `-Threads` and `-Workers` options of the test script and its three cases) not
yet committed, on logical processors 0 to 7 with 6 workers: 2320 tests, 0 failures, 0 errors,
54 skipped (the 16 xfailed cases of option D included), from the JUnit file. Against the
baseline: 224 of the 225 node IDs passed and 1 is **missing**:
`tests/test_runner.py::test_default_workers_is_cpu_count_minus_two`. It was renamed to
`test_default_workers_is_usable_cpus_minus_two` in `314a420` (2026-10-14T22:12:30-03:00), when
the default worker count changed from `os.cpu_count() - 2` to the CPUs of the affinity mask
minus 2. That change was decided before, as decision B-10 of `docs/plans/v0.3-plan.md`,
committed in `b4d48bb` (2026-10-14T14:00:34-03:00). The justification is listed in
`../baseline/justifications.txt` (written on 2026-10-17, pointing to that earlier decision);
with it, the check passes (`audit-baseline-at-reopening.json`). Whether a decision recorded in
another phase's plan counts as "a justification written before" is stated here for the gate
review to weigh.

The check applies at the end of v0.2.1 (the final suite); this run is the state at the
reopening.

## Criterion 5: no threshold set, tuned or checked on a known target or on real data; every target of the v0.1 and v0.2 calibrations, development targets included, used only for declared debugging

**Known targets.** `audit_known_targets.py` reads `calibration/targets.yaml` (v0.1, 14
targets with its development target), `calibration/v0.2/targets.yaml` (v0.2, 21 targets with
its development target) and the `excluded_known_targets` of the v0.2 selection: 35 TIC IDs. It
searched every file tracked by git outside `calibration/` (2540 text files at `80abc00`) for
each TIC number and each name (`name` and the catalog `hostname`). Output:
`audit-known-targets.json`.

| Area | Known targets named |
|---|---|
| `src/` | none |
| `tests/` | 1: `tests/test_calibration_signal_identity.py` names TOI-1481.01 in a comment of case A4 ("Fabricated values of the TOI-1481.01 type"); the values 2.185 and 1.677 d are the published and found periods of the v0.2 dossier, used as fabricated input of the counting rule; no threshold is set or checked with them (the tolerance is the claim's existing 0.001) |
| `docs/validation/v0.2.1/` | 4 records cite one target each as motivation, stating that it is not used to set, tune or validate anything: Kepler-447 b (H4), Kepler-14 b (H9(a)), TOI-1481.01 (H7), TOI-6038 A b (H3) |

The H7 use is declared in its record (case A4: "fabricated values of the TOI-1481.01 type").

**Thresholds.** `audit_thresholds.py` lists every line added to `src/refute/packs/tess` and
`src/refute/core/verdict.py` since tag `v0.2.0` that holds a number other than 0, 1 and 2
(output: `audit-thresholds.json`, 23 lines at `80abc00`). The decision thresholds among them:

| Threshold | Where | Fixed by | Seen on |
|---|---|---|---|
| `max_train_duration_period_ratio` 0.2 | `params.py` (H4) | the window geometry (H4 record, "Thresholds") | synthetic development data only, before the maintainer approved it, declared (`../pre-document-runs.md`, run `h4_survey.py`) |
| `max_hidden_window_fraction` 0.5 | `params.py` (H4) | the window geometry | the same declared run |
| signal factors P, 2P, P/2 | `params.py` (H7) | the definition of signal identity (H7 record) | none; the tolerance is the claim's existing one |
| alias names P, 2P, P/2, 3P, P/3 | `pipeline.py` | reporting only (`period_comparison`); no decision | — |

Every other line is a unit conversion (24 h, 86400 s), a display format, or a parameter of a
synthetic scenario (`synthetic.py`). No threshold of v0.2.1 was set, tuned or checked on a known
target or on real data, as far as these records and the declarations of
`../pre-document-runs.md` show. The development runs on real targets mentioned by the closure
are none: `../pre-document-runs.md` states that every run it declares was on synthetic data.

## Files

| File | What it is |
|---|---|
| `audit_known_targets.py` | the known-target search (read-only) |
| `audit-known-targets.json` | its output at `80abc00` |
| `audit_thresholds.py` | the threshold listing (read-only) |
| `audit-thresholds.json` | its output at `80abc00` |
| `audit-baseline-at-reopening.json` | the output of `scripts/check_test_baseline.py` for the run above |
| `../baseline/justifications.txt` | the justification of the one missing baseline test |
