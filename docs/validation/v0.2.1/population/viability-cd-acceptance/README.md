# The C/D viability package's acceptance: the sabotages and the tests

The acceptance record: [../viability-cd-acceptance.md](../viability-cd-acceptance.md), section 9.
The script: [../viability_cd_sabotage.py](../viability_cd_sabotage.py). Each sabotage replaced one
literal of the committed code (e8942d4), ran its matching tests through
`scripts/run_tests_affinity.ps1` with a JUnit file after a control run of the same tests on the
unmutated code, and wrote the original bytes back (checked against the index). No full suite ran
at the same time.

## The two runs, both kept

- **[sabotages.json](sabotages.json), the first run: 16 of 17 caught.** S11 (a complete record's
  task run again) was **not caught**: on a relaunch, the mutated loop sent every task, but each
  already recorded task was blocked by its submission marker, so nothing was dispatched and the
  test, which checked only `dispatched` and `submitted`, still passed. The mutation was real; the
  test was too weak.
- **The test strengthened** (`tests/test_viability_cd.py`,
  `test_x_a_complete_run_the_manifest_s_binding_and_records_never_replaced`): the relaunch of a
  complete sub-lot must also have no terminal failure and be complete.
- **[sabotages-2.json](sabotages-2.json), the second run, with every sabotage again: 17 of 17
  caught.**

Three tests were added after the code's commit, before the sabotages ran, because the sabotages
S8, S9 and S11 needed a direct check: the variability-free year with two sectors in one year
(`test_p2_...`), the oracle's bands with a bump between them (`test_r4_the_oracle_s_bands_...`),
and the relaunch of a complete sub-lot (in `test_x_a_...`).

## The tests

`tests/test_viability_cd.py` after these changes: **30 tests, 0 failures, 0 errors, 0 skipped**
(JUnit, `scripts/run_tests_affinity.ps1`, 2026-10-27).
