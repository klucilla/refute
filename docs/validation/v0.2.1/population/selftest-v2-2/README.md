# Second self-test of the population harness v2 (not a measurement)

Self-test of the corrected files (Amendment 4, clarifications of 2026-10-13):
`../population_v2.py` (SHA-256
`50bec0547ef4648919fcaf5c5ad4f1a88b347c7be60ee823e2d3107007a80168`),
`../population_compare.py` (SHA-256
`0e62dcc4dc99a53fcc319aa513734f31e9d877406cc81e56ea97c80042e2f01f`) and `../d6.py` (SHA-256
`7164076a84a662695db826fa7219623fe732aa30d910c9088e73b592c6ecbdb4`), run on 2026-10-13 from
15:05 to 15:19 UTC on the branch at commit `113e07c`, before the corrected files were
committed (committing them does not change their bytes; every declaration of the self-test
names these SHA-256). Every campaign is a diagnostic under
`.cache/population/v2-selftest-2/campaigns`, so R2 was recorded and not enforced. The first
self-test (`../selftest-v2/`) tested the files of commit `113e07c` and is left as it was.

**Self-test outcomes are not a measurement. No criterion, size, band, mechanism, limit or
amendment of the population study may be decided or justified by them.** The populations are
`selftest` and `determinism` (prefixes `refute-v0.2.1-population-selftest` and
`refute-v0.2.1-population-determinism`); no development case was generated or analyzed.

The driver is `selftest_v2.py` (the driver of `../selftest-v2/` with the new step
`blockers`, the declared affinity in every declaration, and this work folder); every command
it ran and its output are in `selftest-v2-log.txt`, in order (the repository path replaced
by `<repo>`, the user name by `<user>`). The artifacts (586 files: declarations, journals,
lock markers, manifests, block indexes, execution records, result records, comparison and
D6 reports, caches, the JUnit XML of the test suite) are in the git-ignored
`.cache/population/v2-selftest-2/`; `artifacts-SHA256SUMS` lists them.

## What was checked

- **Reference cases**, three generations (1 worker in index order, 2 in reverse order,
  3 shuffled), accepted: the cases keep their SHA-256
  (`f3951b9e85d21ea8cbc42a23074ad5b442498d049bfbb51896c6277c85192c4e`,
  `a7dd6266f4ffd30f3cead01987a301c64db2086791a7296e0db55f3f416055c4`,
  `1817b9f776969ae050ba6cd7b1849dda968595041dabe37711390cec7b37b724`), and so do the stored
  files.
- **Overhead per generation** (Amendment 4, item 14): six new processes alternating v1 and
  v2 on the 520 determinism cases, hash only, 24 workers, index order. Wall time per process:
  v1 36.0, 37.8, 37.8 s; v2 41.8, 41.5, 41.9 s; median(v2) / median(v1) - 1 =
  41.8 / 37.8 - 1 = **10.5 %** (accepted up to 20 %): the double hash is kept. The three v1
  manifests give, for all 520 cases, the same SHA-256 as v2 (v1 and v2 build the same bytes).
- **Determinism**: the 520 cases in three new processes (24 workers in index order, 12 and 24
  workers in two declared shuffled orders), manifests and block indexes byte-identical
  (14060 segments, 50920 blocks), set accepted.
- **Injected differences**: in blobs, 5 of 5 located at the expected offset, segment, block
  and element or header path, also without the bytes (one byte, the sign of a zero, a NaN
  payload, a header field, a structural change); in result records, 6 of 6 as expected.
- **Journal and lock**: a different file at a case's path in the cache; the lock was written
  at detection, the new bytes beside the existing file, and every campaign mode refused,
  also with another output directory; the integrity-failure report said "BLOCKED: integrity
  failure"; assembled copies showed a missing marker still blocked, a registered resolution
  unblocked, an unclosed execution blocked until reconciled.
- **Analysis in two slots at M0 and M3** (4 determinism cases, 2 lots): regeneration checked,
  both slots at both points in their bound run directories, records 3, comparisons 3c
  registered in the journal (every case identical), records 4; run again, both lots skipped;
  `metrics` reconciled everything and wrote a report labelled
  "DIAGNOSTIC: not an approval". About 63 KB per record.
- **D6 machinery, a smoke run (not the D6)**: 13 cases at M3 only, 7 configurations twice.
  Every check passed; the control pass found exactly the declared differences (F x R-idx 24,
  R-rev x R-idx 24, R-shf x R-idx 24, P24 x P12 2, every other pair 0) and only at
  `/control/cases_before_in_process`; the negative control, run inside the check, passed 11
  of 11. Result: "PASS (smoke run, not the D6)", which does not count as the D6 (matrix
  problems: a smoke run, not 40 cases, not M0 and M3).
- **The blocking findings of the code review**, 19 of 19 as expected:
  - B1: a second analysis of a unit in another folder refused;
  - B2: a record with an empty scientific section refused, and counted as an error in C6;
    `metrics` refused a lot without record 4;
  - B3: a wrong count of sets consumed before, and a sibling campaign of the chain, refused;
  - B4: a case list and a missing manifest B refused in a strict declaration;
  - B5: a smoke D6 report and a wrong qualification hash refused as prerequisites;
  - B5-D6: a run without M0 and the 40 cases does not count as the D6; a forged control value
    is caught (FAIL);
  - B6: a worker reporting a dispatch problem writes a lock;
  - B7: the lock is written at detection, before the closure, and the evidence file exists;
  - B8: two simultaneous executions of one unit: one started, one refused;
  - B9: diagnostic metrics labelled "DIAGNOSTIC: not an approval";
  - B10: another affinity than the declared one refused;
  - B11: campaign ids `..`, `C:\outside` and `a/../b` refused;
  - an output outside the project refused before anything was created; the user's home
    directory masked (N6); a malformed `f64` reported as invalid (N3).
- **Test suite** with the repository's virtual environment: 505 tests, 489 passed, 16
  xfailed, 0 failures, 0 errors (from the JUnit XML). No file under `src/` changed.

`SHA256SUMS` lists every file of this folder except itself.
