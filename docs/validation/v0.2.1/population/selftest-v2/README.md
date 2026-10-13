# Self-test of the population harness v2 (not a measurement)

Self-test of `../population_v2.py` (SHA-256
`2e001aac326ae92d1f8608aab24bd88184ead0e0c5180e0bdf6282a9cafc6067`), its comparator
`../population_compare.py` (SHA-256
`d05716c52397332f89746bfe317f98eb6245b023b81c4178f8fe4b3f49379ab0`) and the D6 script
`../d6.py` (SHA-256 `1640cb47fc1ceb3ff18007e6ab5f26c3cd7f22e648b560c8cc5c915473b458fa`), run
on 2026-10-13 from 12:41 to 12:54 UTC on the branch at commit `68d13fd`, **before these files
were committed**. Every campaign of the self-test is a diagnostic (declared under
`.cache/population/v2-selftest-final/campaigns`, never under `../campaigns/`), so the harness
recorded, without enforcing, that its files were not the files of HEAD (R2). Committing the
files does not change their bytes; the SHA-256 above are the ones every declaration names.

**Self-test outcomes are not a measurement. No criterion, size, band, mechanism, limit or
amendment of the population study may be decided or justified by them.** The populations are
`selftest` (prefix `refute-v0.2.1-population-selftest`) and `determinism` (prefix
`refute-v0.2.1-population-determinism`, Amendment 4, item 13). No case of the development
population was generated or analyzed: case ids such as `planet-below-white-0000` exist in
both structures, but every case used here has the seed of its own prefix, and none has the
seed of a development case.

The driver is `selftest_v2.py`; every command it ran and its output are in
`selftest-v2-log.txt`, in order (the repository path replaced by `<repo>`). The lines before
the marker line belong to a first attempt that was stopped during its overhead step and is
superseded (`expectation-changes.md`, which also lists every expectation of the driver changed
after a failure during development). The heavy artifacts (manifests, block indexes,
execution records, journals, lock markers, result records, comparison reports, caches) are in
the git-ignored `.cache/population/v2-selftest-final/`; `artifacts-SHA256SUMS` lists all 352.

## What was checked

- **Reference cases.** A diagnostic campaign of the three reference cases, three generations
  (1 worker in index order, 2 in reverse order, 3 shuffled), the first one stored: the three
  manifests and block indexes are byte-identical, `check-set` accepted the set, and the cases
  keep their SHA-256 (`f3951b9e85d21ea8cbc42a23074ad5b442498d049bfbb51896c6277c85192c4e`,
  `a7dd6266f4ffd30f3cead01987a301c64db2086791a7296e0db55f3f416055c4`,
  `1817b9f776969ae050ba6cd7b1849dda968595041dabe37711390cec7b37b724`), as do the stored files.
- **Overhead per generation (Amendment 4, item 14).** The 520 cases of the determinism
  population, hash only, 24 workers, index order, six new processes alternating v1 and v2:
  wall time per process v1 34.2, 34.4, 33.6 s and v2 39.6, 38.3, 37.8 s; median(v2) /
  median(v1) - 1 = 38.3 / 34.2 - 1 = **12.0 %** (limit 25 %, accepted up to 20 %): the double
  hash is kept. The three v1 manifests give, for all 520 cases, the same SHA-256 as v2.
- **Determinism.** The 520 cases in three new processes (24 workers in index order, 12
  workers shuffled, 24 workers in another shuffled order): manifests and block indexes
  byte-identical (14060 segments, 50920 blocks of 1 MiB), set accepted. The population covers
  the mechanisms that diverged in the v1 generations (for example
  `planet-below-white-0000`, two years; `planet-below-white-0111`, three years;
  `no_transit-none-white-1544`, trend and variability).
- **Injected differences in blobs** (copies of a stored reference case), each located at the
  expected offset, segment, block and element or header path, and, from the manifest entries
  and block indexes only, at the expected segment and block: one byte of an array (block 11
  of `aux/pixels/1/flux`), the sign of one zero, the payload of one NaN (both reported as
  such, not as equal values), one header field (`/attempt_seed`), and a structural change
  (another shape, reported as structural). 5 of 5.
- **Injected differences in result records** (copies of a real record), profile `slots`: one
  metric value changed by one ULP, a missing field, an extra field, a float whose `dec` and
  `f64` disagree (invalid), a `/control` section (invalid under `slots`), and differences only
  in excluded paths (identical). The real records of slots 1 and 2 are identical. 6 of 6.
- **Journal and lock.** A file with other bytes was placed at a case's path in the cache:
  the generation left it untouched, wrote the new bytes beside it
  (`<case>.<sha256>.rpc`), wrote the lock marker and the `divergence` entry, and stopped
  (exit 2). Then `generate` (with another output directory), `check-set`, `regenerate`,
  `analyze`, `compare-slots`, `orchestrate` and `metrics` all refused (exit 1);
  `metrics --integrity-report` wrote "BLOCKED: integrity failure". Assembled copies of the
  campaign (nothing deleted): without the marker it is still blocked by the journal entry;
  with a resolution that applies a registered rule it is unblocked; with a `started`
  execution without closure it is blocked until `reconcile` records it.
- **Analysis in two slots at M0 and M3.** Four determinism cases (the mechanisms that diverged
  and a blend: `planet-below-white-0000`, `planet-below-white-0111`,
  `false_positive-measurable-white-0133`, `no_transit-none-white-1544`), three generations,
  accepted; `orchestrate` in two lots of 2: regeneration checked against the accepted
  manifest and block index, both slots at both points, records 3 per point and slot, the
  comparisons 3c (every case identical) and records 4. Run again on the finished state, it
  skipped both lots. `metrics` reconciled the records and wrote the criteria (meaningless
  with 4 cases), the redraws and the paired comparisons M0 to M3. A complete record is about
  63 KB (16 records, 1002045 bytes).
- **D6 machinery, a smoke run (not the D6).** The first 13 cases of the declared D6 rule
  (`planet-below-white-0000`, `-0011`, `-0100`, `-0111`, `-0150`, `-0200`,
  `planet-below-correlated-0000`, `-0100`, `-0150`, `-0200`,
  `false_positive-below-white-0050`, `no_transit-none-white-1544`, `-1550`), generated three
  times and accepted, at M3 only, the 7 configurations twice. Check 1, the six conditions of a
  valid conclusion and check 2 (`d6-science`, 19 pairs) passed with no scientific difference;
  the control pass (`d6-control`) found exactly the declared differences (F x R-idx 24,
  R-rev x R-idx 24, R-shf x R-idx 24, P24 x P12 2, every other pair 0); the negative control
  passed 11 of 11. Result of the smoke run: PASS. The D6 itself (40 cases, M0 and M3) has not
  run.
- **Test suite.** `pytest` with the repository's virtual environment: 505 tests, 489 passed,
  16 xfailed, 0 failures, 0 errors (from the JUnit XML). No file under `src/` changed.

`SHA256SUMS` lists every file of this folder except itself.
