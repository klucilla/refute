# v0.5 exit criteria 1 and 2: the test-count evidence (2026-11-05)

Written in answer to the first gate review's findings M1, M2 and M3
(`calibration/v0.5/gate/gate-1-report.md`; the maintainer's decision 4 of 2026-11-05, #199). New
records; nothing published is edited.

## Criterion 2: no synthetic test that passes at the start of v0.5 fails at its end

- **Start of v0.5:** the full suite at tag `v0.4.0` (commit `ad5fd5c`), run on 2026-11-05 in a
  detached worktree with that commit's own locked environment, through
  `scripts/run_tests_affinity.ps1` (CPUs 20-31): JUnit XML (kept locally, SHA-256
  `b26a026e1638614ad1c0c58a96aa46ede561fab5aa30bfeec522e11a08234846`): 4,267 tests, 0 failures,
  0 errors, 91 skipped. The 4,176 passing node IDs: [`v0.4.0-passing-tests.txt`](v0.4.0-passing-tests.txt),
  built by [`make_baseline.py`](make_baseline.py) (a node ID is the candidate whose file exists in
  that commit).
- **End of v0.5 (the run checked here):** the full suite at `6ecb238` plus the S5 draw files
  (2026-11-05, CPUs 8-19): JUnit XML (local, SHA-256
  `fe34d63a6db925f8994e5b2732feeb47f623a435ddc08bccbd3b3791c28a987c`): 4,530 tests, 0 failures,
  0 errors, 91 skipped. The suite after the last commit of the phase is recorded apart (finding
  M4, `suite-final.md`).
- **The check:** `scripts/check_test_baseline.py <end junit> --baseline v0.4.0-passing-tests.txt`
  → [`baseline-check.json`](baseline-check.json): 4,174 passed by exact node ID, **2 "missing"**,
  `"ok": false`.
- **The note on that FAIL record (finding M2).** The two "missing" node IDs are the two cases of
  `tests/test_ml_data_sources.py::test_host_readers_count` whose parameter is a zip archive built
  at collection time: the parameter ID embeds the archive's bytes, including its timestamp, so
  the ID changes from one run to the next. In both runs both cases exist and **pass**
  ([`compare_param_ids.py`](compare_param_ids.py): `-reader:zip:d/yacht.data!lines:rows-2` and
  `-reader:zip:k.arff!arff:rows-3`, passed at v0.4.0 and at the end). No test that passed at the
  start fails at the end; the checker's FAIL is the instability of those two IDs, not a
  regression. No justification was needed beforehand, since nothing stopped passing.
- **Historical claims give their recorded verdicts and hashes (finding M3).**
  - At their own tags: `scripts/verify_locked_tags.py` → 8 of 8 PASS (v0.1.0, v0.2.0, the five
    v0.3.0 claims, v0.4.0), run on 2026-11-05.
  - With the v0.5 code, in the end suite (all passed): `tests/test_lock_compat.py` (every case,
    among them `test_full_resolved_hash_has_not_changed[tess-calibration-v0.1]` and `[...-v0.2]`,
    `test_projection_with_the_new_code_equals_the_locked_hash[...]`,
    `test_verify_passes_the_claim_by_projection_and_stays_tampered_for_the_code[...]`);
    `tests/test_v05_battery.py::test_a_v04_analysis_is_unchanged_by_the_v05_code`.
  - On real data: C2's compatibility of the v0.4 battery run by the v0.5 code with the v0.4
    records: 1,400 curves, 0 mismatches (`calibration/v0.5/runs/c2/report.json`).

## Criterion 1: the acceptance rows, counted from a JUnit XML (finding M1)

The one acceptance run (2026-11-03) recorded its 133 rows in
`docs/validation/v0.5/acceptance/acceptance-run.json`. They are now counted from a JUnit XML by
`docs/validation/v0.5/acceptance/acceptance_rows_junit.py` (one pytest case per recorded row:
PASS passes, FAIL fails, INVALID is skipped; a **recount of the recorded outcomes, not a rerun**),
run on 2026-11-05 through `scripts/run_tests_affinity.ps1`: JUnit XML (local, SHA-256
`e31448ef5a7fca61333cc5fd52e202033a4cc009c9de5150591f6fb41f3d2ea0`): **133 tests, 11 failures, 0
errors, 3 skipped** (119 passed), the same as the README's 119 PASS, 11 FAIL, 3 INVALID. The
suite's unit and integration cases of the v0.5 tests are counted from the end suite's JUnit
above.

The JUnit XML files are not committed (their `testsuite` element records the machine's host
name); their SHA-256 are above.
