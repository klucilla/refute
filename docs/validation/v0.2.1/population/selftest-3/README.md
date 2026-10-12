# Third self-test of the population harness (not a measurement)

Self-test of `../population.py` (SHA-256
`33e2d4186ea41b4c691a37bd2d83f77ed2cdc7ed825790f21595f53b2896cd85`) and `../points.json`
(SHA-256 `7f26cc75bd96c6feaa7ed40a5f5b880241af1ff4e2b43872d0684a2bdd51d3c9`), run on
2026-10-12 (UTC) on commit `448f1e526389908d5ff981ab5f4b4f3285c18eaa`, after the
corrections of the independent review (population-study.md, Amendment 2). The first
self-test (`../selftest/`) and the second (`../selftest-2/`) are left as they were.

**Self-test outcomes are not a measurement. No criterion, size, band, mechanism, limit or
amendment of the population study may be decided or justified by them.** The population
is `selftest` (seeds with the prefix `refute-v0.2.1-population-selftest`, at most 2
cases per class and mechanism in each noise model, 44 cases); no case of the development
population was generated or analyzed. The "FAILS" of the overall approval in
`metrics.md` says nothing about Refute: the self-test population has 0 to 6 cases per
criterion.

Every command and its output is in `selftest-3-log.txt`, in order.

**A first run was superseded.** A first run of this self-test on commit `39d13f8` showed
that a lot interrupted and then resumed left the lot list and check report of its
interrupted attempt in the cache. The harness was corrected in `448f1e5` (Amendment 2, N9)
and this self-test was run again in full on that commit; the first run is not published.

## What was checked

- **Determinism after N1** (the thread variables are now set to 1 before NumPy is
  imported). Five generations in separate processes (24 workers in index order, twice; 3
  workers in reverse order; 1 worker in a shuffled order; all four without writing the
  cases; and one with 24 workers writing them) gave byte-identical manifests
  (`manifest*.json`, SHA-256
  `2e6881e158bfbb2e3eb7fbe8c60bb5cc4f1fe2de53c70fb115b55f473b29e154`); a sixth, with 5
  workers in another shuffled order, was checked against `manifest.json`: 44 identical,
  0 diverged (`check-report.json`). The serialization did not change, and all 44 case
  entries (hashes, seeds, parameters, expected SNRs, redraws) are identical to
  `../selftest-2/manifest.json`; the manifest files differ only in the harness hash, the
  generator's checkout fields and the environment (`thread_env` now `1`, the OpenBLAS pool
  now 1 thread instead of 24). An inherited `OPENBLAS_NUM_THREADS=2` and
  `OMP_NUM_THREADS=4` are overridden (1 worker and 3 workers: pools of 1 thread, cases
  identical to the manifest).
- **N1, thread pools.** Every `run.json` (the main process of each point), every started
  attempt and every result (the worker that analyzed it) records one OpenBLAS pool with
  1 thread and the four variables at 1; with 1 worker (`negative-tests/c3-missing-cache-M2`)
  the two cases were analyzed in the main process, with the same pools. Every generation
  reports the pools of its workers (with 1 worker, the main process).
- **Four environments.** `orchestrate` ran M0 to M3 in lots of 15 (3 lots), each point in
  its own worktree and virtual environment, bound by `../points.json`:

  | Point | Commit | `refute.__file__` |
  |---|---|---|
  | M0 | `f4798230f1bca607bcc0e98fe47711a26ec4ee59` | `.worktrees/v0.2.0/src/refute/__init__.py` |
  | M1 | `3217db72cae26bc809b62a5239ae6226344e7a26` | `.worktrees/M1-3217db7/src/refute/__init__.py` |
  | M2 | `78d79f5b4495ab7cf7bac5cd2907b25b78c74540` | `.worktrees/M2-78d79f5/src/refute/__init__.py` |
  | M3 | `9d3f36947abdafba35eb657dd5e2e895f5ac14d3` | `.worktrees/M3-9d3f369/src/refute/__init__.py` |

  Each `run.json` records the binding (point and full commit), the SHA-256 of
  `points.json` and the repository commit it was in (`448f1e5`), an editable install of
  the point's worktree and a clean `src/`. The analysis outcomes of all 44 cases are
  identical to those of `../selftest-2/` at every point.
- **Interruption and resumption.** During the second lot, while M1 was analyzing it, the
  `orchestrate` process tree was ended by its PID (`taskkill /PID <pid> /T /F`). At that
  moment the runs held 30, 16, 15 and 15 results; no temporary file was left. The same
  command was run again: lot 0 was skipped; in lot 1, M0 had 15 valid results and
  analyzed none, M1 had 1 and analyzed 14; lot 2 ran in full. The 76 result files present
  after the kill are unchanged after the resumption (same SHA-256 and modification time;
  `snapshot-after-kill.json`). Each completed lot records the regeneration check as data
  (`2-regenerated`), that its results were re-read and validated **before** its inputs were
  deleted, and the lot files it removed; at the end of lot 1 these include the lot list
  and check report of the interrupted attempt (N9). The cache was empty at the end.
- **Truncated result** (`negative-tests/truncated-copy-of-M0-f479823/`): one result of a
  copy of the M0 run was cut at half its bytes; the resumption was refused before dispatch
  ("not valid JSON") and changed nothing.
- **Divergent environment** (`negative-tests/fingerprint-copy-of-M0-f479823/`): resuming a
  copy of the M0 run whose `run.json` fingerprint declares another NumPy version was
  refused ("fingerprint differs"). The divergence is constructed: with the thread
  variables fixed at 1 by the harness, the environment variable used in `../selftest-2/`
  no longer changes the fingerprint.
- **C1, points.** The M3 environment with `--point M0` (on the M0 run of this self-test)
  was refused (the point is another commit); an unknown point (`M9`) was refused; a
  dirty `src/` in the M3 worktree was refused in both forms, (a) one comment line appended
  to the tracked `src/refute/__init__.py` and (b) a new untracked
  `src/refute/_dirty_probe.py`. The tracked file was restored with `git restore` (SHA-256
  equal to before) and the new file removed by its explicit path; afterwards
  `git status --porcelain --ignored -- src/` shows only the ignored `__pycache__/`
  folders, as before. `metrics` refused a point that mixes two commits (the M1 run copied
  with its `run.json` declaring point M0, `negative-tests/n8/mixed/`; 53 problems, the
  first 30 printed).
- **C2, refused attempts.** Every refusal above was recorded in the run's `attempts/` as
  `refused` with `"results": "none"`. `metrics` over M0 to M3 accepted the M0 run and
  lists the refused attempt of the M3 environment; `metrics` over the C3 run below
  accepted it and lists its refusal for missing inputs
  (`negative-tests/c2-metrics-of-c3-run/`).
- **C3, cache.** With an empty cache, two cases were refused before dispatch and no result
  was written; the same command with the right cache (the two cases regenerated and
  checked) analyzed both normally (`negative-tests/c3-missing-cache-M2/`). A copy of one
  input with its last byte changed was refused for its SHA-256 and the run stopped with no
  result written (`negative-tests/c3-divergent-hash-M2/`; its first attempt listed both
  cases and was refused for the one missing from that cache, as the log notes).
- **N8, integrity in `metrics`.** Refused: the same point twice (44 case ids repeated); a
  result whose condition (i) verdict was changed in a copy of the M2 run (its SHA-256
  differs from the `results-reread` record); two result files whose names were exchanged
  in a copy of the M1 run (the file name is not its case); an existing output (refused
  before anything was computed); another manifest (`../selftest-2/manifest.json`). None of
  them wrote an output. The constructed copies and their edits are in
  `negative-tests/n8/` and `negative-tests/n8-copies.log`.
- `metrics.json` and `metrics.md`: `metrics` over M0 to M3, with every result checked
  against the orchestrate records (accepted).
- **Reference cases.** The three cases of the draft reference release
  (`planet-measurable-white-0000`, `planet-measurable-correlated-0000`,
  `false_positive-measurable-white-0004`) are in `manifest.json` with the same SHA-256 as
  in its table.

`SHA256SUMS` lists every file of this folder except itself. The cached cases are in the
git-ignored `.cache/population/` and are not published.
