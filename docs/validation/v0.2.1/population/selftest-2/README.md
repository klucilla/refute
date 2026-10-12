# Second self-test of the population harness (not a measurement)

Self-test of `../population.py` (SHA-256
`376bd7f9e33f2e4b0b7f55157261da61b11cd11e2ae23a3a3e45e3b32895f29d`), run on
2026-10-12 (UTC) after the harness was hardened (atomic writes, validated resumption,
environment fingerprint and attempt records, provenance checks in `metrics`). The first
self-test (`../selftest/`, commit `ffcd3ad`) is left as it was.

**Self-test outcomes are not a measurement. No criterion, size, band, mechanism, limit or
amendment of the population study may be decided or justified by them.** The population
is `selftest` (seeds with the prefix `refute-v0.2.1-population-selftest`, at most 2
cases per class and mechanism in each noise model, 44 cases); no case of the development
population was generated or analyzed.

Every command and its output is in `selftest-2-log.txt`, in order.

## What was checked

- **Determinism verified in the self-test.** Five generations in separate processes
  (24 workers in index order, twice; 3 workers in reverse order; 1 worker in a shuffled
  order; all four without writing the cases; and one with 24 workers writing them) gave
  byte-identical manifests (`manifest*.json`, SHA-256
  `4e96bce466dd0b3e0775b5d36972819bcce314a2bb27fe39f2eab401b8dccb14`); a sixth, with
  5 workers in another shuffled order, was checked against `manifest.json`: 44
  identical, 0 diverged. The case hashes are the same as in `../selftest/manifest.json`;
  the two manifest files differ because each records its harness. **Input reproduction
  compares the hashes of the cases, not the manifest file, which also records the
  environment.**
- **Four environments.** `orchestrate` ran M0 to M3 in lots of 15 (3 lots), each point in
  its own worktree and virtual environment (`runs/*/run.json`):

  | Point | Commit | `refute.__file__` |
  |---|---|---|
  | M0 | `f4798230f1bca607bcc0e98fe47711a26ec4ee59` | `.worktrees/v0.2.0/src/refute/__init__.py` |
  | M1 | `3217db72cae26bc809b62a5239ae6226344e7a26` | `.worktrees/M1-3217db7/src/refute/__init__.py` |
  | M2 | `78d79f5b4495ab7cf7bac5cd2907b25b78c74540` | `.worktrees/M2-78d79f5/src/refute/__init__.py` |
  | M3 | `9d3f36947abdafba35eb657dd5e2e895f5ac14d3` | `.worktrees/M3-9d3f369/src/refute/__init__.py` |

  (`src/` clean at every point; Refute reports version 0.1.0 at M1-M3 and 0.2.0 at M0,
  as at those commits.)
- **Interruption and resumption.** During the second lot, while M1 was analyzing it,
  the `orchestrate` process tree was ended by its PID (`taskkill /PID <pid> /T /F`). At
  that moment the runs held 30, 16, 15 and 15 results; no temporary file was left. The
  same command was run again: lot 0 was skipped (every result valid at every point);
  in lot 1, M0 had 15 valid results and analyzed none, M1 had 1 and analyzed 14; lot 2
  ran in full. The 76 result files present after the kill are unchanged after the
  resumption (same SHA-256 and modification time; `snapshot-after-kill.json`). In
  `orchestrate-records/`, each completed lot records that its results were re-read and
  validated (with the SHA-256 of every result file) **before** its inputs were deleted;
  the interrupted attempt of lot 1 has only its "started" and "regenerated" records.
  (The orchestrate process's own lines in the log can appear after its subprocesses'
  lines because its standard output is buffered.)
- **Truncated result** (`negative-tests/truncated-copy-of-M0-f479823/`): in a copy of the
  M0 run, one result was cut at half its bytes; the resumption stopped with "not valid
  JSON" and changed nothing.
- **Divergent environment** (`negative-tests/fingerprint-copy-of-M0-f479823/`): resuming
  a copy of the M0 run with `OPENBLAS_NUM_THREADS=2` was refused ("fingerprint differs").
- **Mixtures in `metrics`**: refused with another manifest (`../selftest/manifest.json`);
  refused with a copy of the M1 run whose `run.json` was edited, for this test only, to
  declare another harness (`negative-tests/harness-copy-of-M1-3217db7/`, 45 problems:
  its 44 case records differ from their run, and the runs come from two harnesses;
  `negative-tests/g2-full-output.txt`); refused with the same point twice (44 repeated
  case ids). None of them wrote an output.
- `metrics.json` and `metrics.md`: `metrics` over M0 to M3 (accepted).

`SHA256SUMS` lists every file of this folder. The cached cases are in the git-ignored
`.cache/population/` and are not published.
