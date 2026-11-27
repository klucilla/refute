# I4: the CI shard rest split in two, the union check, and a proposal (not applied)

The maintainer's decision I4 (#218, comment 7222329150). Labels: `exploratory`,
`method_status: not_validated`.

## The split

`scripts/ci_shard.py` gains the shard **`heavy-g`**, with the two slowest files of `rest`:
`tests/test_v0511_identity.py` and `tests/v055/test_r1_glue.py`. `.github/workflows/ci.yml` lists
it in the shard matrix.

**The measured durations.** The CI does not keep the JUnit files as artifacts. The durations come
from the log of the slowest `rest` job of the last full run: run
[46007761301](https://github.com/klucilla/refute/actions/runs/46007761301), job 140536872495,
windows-2025 / Python 3.12.15, read on 2026-11-27.
- `rest` took 3,598 s ("4106 passed, 28 skipped, 2 xfailed ... in 3598.43s"). The heavy shards'
  jobs took 10 to 25 min.
- Its "slowest 25 durations" sum to about:
  - 1,068 s for `test_v0511_identity.py` (one setup of 775.77 s and five calls);
  - 920 s for `tests/v055/test_r1_glue.py` (three calls);
  - 348 s for `test_vm_scripts.py`, which stays in `rest`.
- Moving the first two takes about 55 % of `rest` into `heavy-g`.

**Unchanged:**
- the plan's levels and rules (`scripts/ci_plan.py` is not changed);
- every test file, so the set of tests is the set from before the split.

**What changes with the count of shards:** a full run now has 32 jobs (4 pairs x 8 shards, 28
before), and a fast run 16 test jobs (14 before) plus the 2 recorded-value jobs.
- `scripts/ci_evidence.py` derives its expected jobs from `ci_shard.HEAVY`, so it needs no change.
  Only its docstring's counts were updated.
- `tests/test_ci_plan.py`'s expected counts became 32 and 18.
- **CLAUDE.md still says "all 7 shards (14 jobs)" and "the 4 pairs, 28 jobs"** ("Working mode
  (v0.3)", item 1). Editing CLAUDE.md is the maintainer's; the proposed text is "all 8 shards (16
  jobs)" and "the 4 pairs, 32 jobs".

## The deterministic union check

The committed unit `shard-union` (`tools/shard_union.py`) wrote [shard-union.json](shard-union.json).
It uses `pytest --collect-only`, with no test run. The first run failed on a tool bug: its extra
`-q` listed files rather than test IDs. The tool was fixed and committed before the rerun.

| Value | Result |
| --- | --- |
| Tests in the full suite | 5,284 |
| Union of the 8 shards | 5,284 |
| The union equals the full set | **yes** |
| Sum of the shards' sizes = size of the union (no repetition) | **yes** |

The per-shard counts are in the record. `tests/test_ci_shard.py` and `tests/test_ci_plan.py` pass:
32 tests, 0 failures, 0 errors, 0 skipped (JUnit XML).

## Which tests read `docs/validation/**` (read only)

A search of `tests/` for the text `docs/validation` (2026-11-27) finds:
- **test files** that build or read paths under `docs/validation/`;
- helper modules they import (`tests/v0512_case_eval.py`, `tests/v0512_fixtures.py`,
  `tests/population_v3_probe.py`, `tests/spec_b_cases.py`, `tests/instrumentation_cases.py`,
  `tests/make_instrumentation_snapshot.py`, `tests/wp4_papers.py`, `tests/ml_papers.py`);
- fixture files that only mention it in their text.

The test files are:

`test_ci_plan.py`, `test_v051_wp2.py`, `test_v0512_223_cases.py`, `test_v0511_claim_hashes.py`,
`v059/test_pilot.py`, `v059/test_prototype.py`, `v058/test_stability.py`,
`test_v054_budgeted_v3.py`, `v057/test_seeded_run.py`, `v056/test_part_b.py`,
`v056/test_part_a_frame.py`, `v055/test_r2_line.py`, `v055/test_codex_tokens.py`,
`v055/test_r2_bundle.py`, `v055/test_t3b_recount.py`, `v055/test_r1_allocation_step.py`,
`v055/test_d2f_fixed_cap.py`, `v055/test_r1_fixed_cap.py`, `v055/test_ledger_v055.py`,
`v055/test_r1_glue.py`, `v055/test_pinned_hash.py`, `v055/test_r1_common.py`,
`v055/test_generator_v2.py`, `test_v054_launch_detached.py`, `v053/test_b1_smoke_validator.py`,
`v053/test_battery_b1.py`, `test_v052_driver.py`, `test_v052_fast.py`,
`test_v051_accept_wp3b_series.py`, `test_v051_accept_a0_series.py`, `test_ml_data_sources.py`,
`test_v05_acceptance_harness.py`, `test_population_v3_identity.py`, `test_viability_cd.py`,
`test_x2.py`, `test_rmin_lots.py`, `test_population_v3.py`, `test_v04_duration.py`,
`test_v04_roles.py`, `test_workers_equivalence.py`, `test_timing_trapezoid.py`, `test_spec_b.py`,
`test_synthetic_correlated_noise.py`, `test_rmin_timing.py`, `test_rmin_evaluate.py`,
`test_rmin_alteration.py`, `test_rednoise_propagation.py`, `test_rednoise.py`, `test_prewhiten.py`,
`test_population_v4.py`, `test_period_alias_rev4.py`, `test_lock_compat.py`,
`test_instrumentation.py`, `test_holdout_train_validity_e2e.py`, `test_holdout_replicas.py`,
`test_holdout_report_wording.py`, `test_holdout_isolation.py`, `test_holdout_capacity.py`,
`test_holdout_blindness.py`, `test_ebcatalog_own_tic_e2e.py`, `test_domain.py`,
`test_check_test_baseline.py`, `test_capacity_plan.py`, `test_calibration_signal_identity_e2e.py`,
`test_verify_dossiers.py`, `test_ml_repository_weights.py`, `test_ml_schema.py`,
`test_ml_integration.py`, `test_ml_provenance.py`, `test_ml_patches_tree.py`, `test_ml_patches.py`,
`test_ml_tbevents.py`, `test_ml_extract_pattern.py`, `test_paper.py`, `test_wp4_papers.py`,
`test_check_interpreter.py`, `test_seal.py`, `test_reply.py`, `test_budget.py`,
`test_holdout_train_validity.py`, `test_ebcatalog_own_tic.py`,
`test_calibration_signal_identity.py`.

The same search for `v0.5.13` in `tests/` finds nothing.
- **No test reads a file under `docs/validation/v0.5.13/`.**
- The CI's lint step (`ruff check .`) does read its Python tools, `docs/validation/v0.5.13/tools/*.py`.

## The proposal (not applied)

**`docs/validation/v0.5.13/**` cannot enter the documentation-only list as a whole.** Its
`tools/*.py` are linted by ruff in CI, and `ci_plan` treats every `.py` as code. Its Markdown is
already documentation-only (`docs/**/*.md`).

**Proposed addition to `DOCS_ONLY` in `scripts/ci_plan.py`:** only the phase's data records,
which no test, lint step or build reads:
```text
    "docs/validation/v0.5.13/*.jsonl",       # the journal and the exceptions
    "docs/validation/v0.5.13/**/*.json",     # the records, the ledger, the manifests and the unit specs
```

Effect, and limits:
- **Effect.** A push that touches only this phase's journal, ledger, records or Markdown would run
  no test job (`docs`) instead of the fast matrix. This holds unless the push carries the
  order-proof trailer, which `ci_plan` checks before the documentation rule.
- **The test to adjust.** `tests/test_ci_plan.py::test_documentation_only_runs_no_test_but_readme_and_data_files_do`
  keeps `docs/validation/x.json` as data (fast); the new patterns do not match it. A test of the new
  patterns would be added.
- **When to undo.** Each new test that reads a file of `docs/validation/v0.5.13/` must remove the
  pattern first. A rule to that effect could live in the `DOCS_ONLY` comment.
- **The unit specs** (`units/*.json`) are read by the launcher, a local tool, not by CI. Keeping
  them out of the patterns would be the more conservative choice.
