# Decision T2: the corrections of Codex's round-3 items, and the test of each attack

The maintainer's decisions T1 to T3 (#218, comment 7227882370). The design is the maintainer's.
There is no Codex round; the maintainer's adviser reviews the diff and the tests. Labels:
`exploratory`, `method_status: not_validated`. No golden file was read, the comparator did not
run on goldens, and NR-A2's manifest is a draft outside git.

**The diff to read:** `2e86f48442f2a8c009075e5f346e48776c783696..493ce707c8ea967a232a39421d8d479fdd5371ac`.
- **Code:**
  - `docs/validation/v0.5.13/tools/comparator.py`;
  - `tools/identity_v2.py`;
  - `tools/freeze_226.py`;
  - `tools/count_keys.py` with `units/count-keys.json`;
  - `l4/comparator-schema-parts.json`, `l4/count-keys.json`;
  - `tests/test_v0513_comparator.py`.
- **The new freeze:** `manifests/freeze-226-t3/`.

## Each attack of round 3, and the test that reproduces it and shows the failure

All tests are in `tests/test_v0513_comparator.py`, on synthetic inputs only.

| Round-3 item | The attack | Test(s) |
| --- | --- | --- |
| 1 | `candidate.n_transits` 100 → 100.00001, `v05.discovery_version` 4 → 4.0 | `test_t2_1_counts_ids_and_versions_are_exact`; `test_t2_1_attack_on_the_schema_as_frozen` (the schema built as `freeze_226.py` builds it, with `cadences_used` and `failures` too) |
| 1 | equal cadence rows with an empty or `n/a` fraction, or a `bogus` count; empty cells elsewhere | `test_t2_1_empty_or_non_numeric_cells_fail` |
| 2 | spaces around the claim separator changed | `test_t2_2_claim_line_is_compared_whole` |
| 3 | a run not proven to follow the freeze, the manifest and the receipt's commit; an `after` before its `before`, of another unit; a divergent proof commit | `test_t2_3_order_pieces_missing_or_out_of_order_fail` |
| 3 | a receipt whose files, trailer, parents, CI run or attested commit are not what git holds | `test_t2_3_receipt_is_checked_against_the_commit` |
| 4 | a run with local changes, at another head, or without the code records | `test_t2_4_code_records_missing_or_divergent_fail`; `test_t2_4_the_executor_refuses_other_code` |

## What the design leaves as limits, stated

- **T2(1) is a list of keys, not of full paths.** A key in `l4/count-keys.json` is exact wherever
  it appears. That over-includes, which can only make a comparison fail.
- **The enumeration comes from source by form, and cannot be proven complete.** An integer
  written in a way the rule does not read stays under the measurement rules. Two integers of the
  same key are still compared exactly there, and only a change of notation is compared by value.
- **T2(4) asks that HEAD equal the authorized commit.** That cannot hold at the run: the
  manifest's commit and its receipt's commit come after any commit the manifest can name. The
  executor and the comparator instead require all of these:
  - the code paths (`src`, `tests`, `pyproject.toml`, `uv.lock`) at the run's HEAD are those of
    the authorized commit;
  - the porcelain status is empty;
  - the code digest is the frozen one;
  - HEAD is recorded before and after the run.

  This reading needs the maintainer's confirmation.
