# Test renames and replaced test IDs

An append-only record of every test ID that is renamed, replaced or removed, so that a change in
the CI test-ID check (`scripts/ci_ids_check.py`) can be traced to its commit and reason. Adopted
by the maintainer's decision of 2026-11-11 (#217), after #210, where these entries were kept
before, was closed.

**Rules.**

- Entries are only appended, never edited or deleted. A correction is a new entry that names the
  entry it corrects.
- An entry is written in the same commit as the rename, replacement or removal it records.
- Each entry gives: the date, the commit, the old ID and the new ID (or "removed"), and the reason.
  New tests with no old ID need no entry.

## Entries copied from #210

Copied on 2026-11-11 from the comments of #210 (closed on 2026-11-10), in their order, with their
original dates, commits and wording; each links its source comment.

### 2026-11-06, `955710c` (CI run 42261320399)

Source: https://github.com/klucilla/refute/issues/210#issuecomment-6691811631

- Removed: the two zip cases of `test_host_readers_count`, whose IDs held the zip's build time and
  changed from run to run. They now have explicit ids (`zip-yacht-lines`, `zip-kin8nm-arff`).
  `scripts/ci_ids_check.py 42261320399 --reference 42236583766`: 16 added (the new tests, and the
  two renamed IDs) and 2 removed. The reference from then on was run 42261320399.

### 2026-11-07, `64f3c2d` (v0.5.1 WP3 (a))

Source: https://github.com/klucilla/refute/issues/210#issuecomment-6699697448

- `tests/test_v051_sinusoid.py::test_the_v3_registry_changes_only_the_sinusoid` ->
  `tests/test_v051_sinusoid.py::test_the_v3_registry_changes_only_the_sinusoid_and_the_sap_sub_check`
  (the version-3 registry also makes `systematics`' SAP sub-check conditional).
  `scripts/ci_ids_check.py 42315074545 --reference 42261320399` reports it as one removed and one
  added ID.

### 2026-11-07, `911c9a5` (Codex's end-of-round review of round 4, objection 1)

Source: https://github.com/klucilla/refute/issues/210#issuecomment-6704172129 (relative to the
last commit CI ran, `6f8d805`)

- `tests/test_v051_wp3a.py::test_sabotage_the_written_rule_makes_the_affine_case_detectable` ->
  `tests/test_v051_wp3a.py::test_sabotage_the_written_rule_makes_row_3a7_fail_on_the_detectable_block`
  (the sabotage now checks row 3a.7's own "must" on three curves, with its preconditions).

### 2026-11-07, `d3978cf`, `6aa9531` and `90071c3`

Source: https://github.com/klucilla/refute/issues/210#issuecomment-6705380513 (CI run 42360087820:
72 added and 1 removed against 42344929297, the removed one being the rename of `911c9a5`)

- `tests/test_v051_wp4.py::test_4_2_earlier_claims_keep_the_bytes_of_their_outputs` (it existed
  only in the failed runs 42353283742 and 42356576130) -> replaced by
  `tests/test_v051_wp5.py::test_5_2_earlier_claims_code_paths_give_the_baseline_bytes`: recorded
  analysis bytes do not travel between machines, so the analysis is compared differentially with
  the code of the v0.5.0 calibration lock (`b6249b5`) on the machine that runs the test.
- `tests/test_v051_wp5.py::test_5_2_the_plans_of_earlier_claims_produce_the_recorded_bytes[*]`,
  `::test_5_2_the_paired_chain_of_the_v05_calibration_keeps_its_bytes` and
  `::test_the_fixture_comparison_rule` (only in the failed run 42356576130) -> replaced by
  `::test_5_2_the_recorded_verdicts_render_the_recorded_reports[*]` and
  `::test_5_2_the_recorded_paired_chain_has_no_version_3_fields`.

### 2026-11-07, `78157d3` and `063ac1f`

Sources: https://github.com/klucilla/refute/issues/210#issuecomment-6711314499 and
https://github.com/klucilla/refute/issues/210#issuecomment-6713054408

- No test renamed or removed (new files `tests/test_v051_rehearsal.py` and
  `tests/test_v051_duration.py` only).

## Entries from 2026-11-11 on

(none yet)
