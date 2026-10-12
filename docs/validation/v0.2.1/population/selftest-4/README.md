# Fourth self-test of the population harness (not a measurement)

Focused self-test of `../population.py` (SHA-256
`408020676340322f4728ce3a8b4eecae505bfbec7ec34643ad9afed0e5a76225`), run on 2026-10-12
(UTC) on commit `1692d9927a1dbdd4f94d0ff7db5c6fbbfbd0b033`, after the corrections R1 and
R2 of the second round of the independent review. The earlier self-tests (`../selftest/`,
`../selftest-2/`, `../selftest-3/`) are left as they were.

**Self-test outcomes are not a measurement. No criterion, size, band, mechanism, limit or
amendment of the population study may be decided or justified by them.** The population
is `selftest` (seeds with the prefix `refute-v0.2.1-population-selftest`); no case of the
development population was generated or analyzed. The "FAILS" of the overall approval in
`short/metrics.md` says nothing about Refute: the short manifest has 6 cases.

Every command and its output is in `selftest-4-log.txt`, in order.

## What was checked

- **Determinism.** Two generations of the 44 self-test cases in separate processes, with
  24 workers in index order and with 1 worker in a shuffled order (hash only), gave
  byte-identical manifests (`manifest.json`, `manifest-workers1-shuffle7.json`, SHA-256
  `cc0cb9a7edfdd13208d335406f119d96a596fdce811b07b0b0da7de357397d5c`). All 44 case
  entries, hashes included, are identical to `../selftest-3/manifest.json`; the manifest
  files differ only in `harness_sha256` and the new `harness_commit`. The three reference
  cases keep their SHA-256.
- **A short orchestrate at the four points.** `short/manifest-short.json` holds 6 cases
  (`short/short-cases.txt`: one planet, one false positive and one case without transit
  per noise model, with entries identical to the full manifest). `orchestrate` analyzed
  them at M0 to M3 in lots of 2 (3 lots, `short/runs/`, `short/orchestrate-records/`);
  each `run.json` records `harness_commit` `1692d99…`. The analysis outcomes of the 6
  cases are identical to those of `../selftest-3/` at every point. Run again on the
  finished state, `orchestrate` skipped the three lots after checking that their results
  equal record 3 and that record 4 exists. `metrics` over the four runs, with every
  result checked against the records, was accepted (`short/metrics.json`, `.md`).
- **R1, by assembled states** (no timing of a kill). Each state is a copy of the short
  runs and records (`r1-states/<state>/`), built by copying only; the inputs of lot 0 were
  regenerated into the cache (checked against the manifest), and a copy of the lot list
  (`lot-0000-assembled.txt`) was put in the cache as the lot file an interrupted attempt
  leaves. A SHA-256 snapshot of the state and the cache was taken before and after the
  resumption (`r1-states/<state>-snapshot-*.json`):
  - **(a)** every result valid, records 3 and 4 of lot 0 absent: the resumption wrote a
    record 3 and a record 4 for lot 0, deleted the two inputs and the lot file, and
    skipped lots 1 and 2. Added: the two records; removed: the three cache files;
    changed: none.
  - **(b)** record 3 of lot 0 present, record 4 absent, inputs still in the cache: the
    resumption checked the hashes of record 3 against the results, deleted the two inputs
    and the lot file, and wrote record 4 (with the prefix of record 3). Added: record 4;
    removed: the three cache files; changed: none.
  - **(c)** as (b), with one SHA-256 of the copied record 3 changed: the resumption
    stopped for investigation ("record ... and the results on disk diverge (1 files)").
    Added, removed and changed: none.
- **R2, committed harness.** One line was appended to `../population.py` without
  committing it; `generate`, `analyze` and `orchestrate` each refused ("has changes that
  are not committed", "the running harness is not ... of commit 1692d99... (SHA-256)").
  `analyze` recorded its refusal as an attempt without results (`r2/analyze-run/`). The
  file was restored with `git restore`: its SHA-256 is again `40802067…` and
  `git status --porcelain` shows nothing for it.

`SHA256SUMS` lists every file of this folder except itself. The cached cases are in the
git-ignored `.cache/population/` and are not published.
