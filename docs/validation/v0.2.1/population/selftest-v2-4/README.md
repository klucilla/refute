# Fourth self-test of the population harness v2 (not a measurement)

Self-test of the committed files (Amendment 4, clarifications of 2026-10-13):
`../population_v2.py` (SHA-256
`8b3b6ad6aca6e713636b04e40db5a7d253c05458c8b143c38d984100072c1f82`),
`../population_compare.py` (SHA-256
`0e62dcc4dc99a53fcc319aa513734f31e9d877406cc81e56ea97c80042e2f01f`) and `../d6.py` (SHA-256
`bef4ab9db52b059ae63bcb6bc27bdc77ec2db51cf8bf762c13278d76f5f70466`), with the comparator
profiles `slots` `a3e7e797828786b513221071666ff78e1ec07d5ef0158cce8d4cd2b403c95571`,
`d6-science` `ce6816bea4354535901c34657e604d495ad24590284404ea18887efeaefca084` and
`d6-control` `86f232108d6be8fdf5630a8801b560406098705d79f40d5c023081dc73d1019a`. It ran on
2026-10-13 from 16:57 to 17:15 UTC on the branch at commit `113e07c`, before the files were
committed (committing them does not change their bytes; the log records these SHA-256 at the
start). Every campaign is a diagnostic under `.cache/population/v2-selftest-4/campaigns`, so
R2 was recorded and not enforced. It follows the third code review, whose two remaining
blocking points (items 3 and 6 of the clarifications) were completed without a fourth review,
by the maintainer's decision; the new tests of the step `blockers4` prove those corrections.
The earlier self-tests (`../selftest-v2/`, `../selftest-v2-2/`, `../selftest-v2-3/`) are left
as they were.

**Self-test outcomes are not a measurement. No criterion, size, band, mechanism, limit or
amendment of the population study may be decided or justified by them.** The populations are
`selftest` and `determinism` (prefixes `refute-v0.2.1-population-selftest` and
`refute-v0.2.1-population-determinism`); no development case was generated or analyzed.

The driver is `selftest_v2.py` (the driver of `../selftest-v2-3/` with the new step
`blockers4`, two more declarations and this work folder); every command it ran and its
output are in `selftest-v2-log.txt`, in order (the repository path replaced by `<repo>`, the
user name by `<user>`). The artifacts (declarations, journals, lock markers, manifests, block
indexes, execution records, result records, comparison and D6 reports, caches, the JUnit XML
of the test suite) are in the git-ignored `.cache/population/v2-selftest-4/`;
`artifacts-SHA256SUMS` lists them.

## What was checked

- **Reference cases**, three generations, accepted: the cases keep their SHA-256
  (`f3951b9e85d21ea8cbc42a23074ad5b442498d049bfbb51896c6277c85192c4e`,
  `a7dd6266f4ffd30f3cead01987a301c64db2086791a7296e0db55f3f416055c4`,
  `1817b9f776969ae050ba6cd7b1849dda968595041dabe37711390cec7b37b724`), and so do the stored
  files.
- **Overhead per generation** (Amendment 4, item 14): six new processes alternating v1 and
  v2 on the 520 determinism cases. Wall time per process: v1 36.8, 36.7, 38.0 s; v2 41.3,
  42.8, 43.1 s; median(v2) / median(v1) - 1 = 42.8 / 36.8 - 1 = **16.5 %** (accepted up to
  20 %; it was 12.2 % in `../selftest-v2-3/`). The three v1 manifests give, for all 520
  cases, the same SHA-256 as v2.
- **Determinism**: the 520 cases in three generations (24 workers in index order, 12 and 24
  workers in two declared shuffled orders), manifests and block indexes byte-identical
  (14060 segments, 50920 blocks), set accepted.
- **Injected differences**: 5 of 5 in blobs (also without the bytes), 6 of 6 in result
  records.
- **Journal and lock**: as in `../selftest-v2-2/`; every campaign mode refused after the
  lock, and the integrity-failure report said "BLOCKED: integrity failure".
- **Analysis in two slots at M0 and M3** (4 determinism cases, 2 lots), run again with both
  lots skipped; `metrics` labelled "DIAGNOSTIC: not an approval". About 63 KB per record.
- **D6 machinery, a smoke run (not the D6)**: 13 cases taken from the accepted set of the
  whole `determinism` campaign, at M3 only, 7 configurations twice (19 pairs compared). Every
  check passed; the control pass found exactly the declared differences (F x R-idx 24,
  R-rev x R-idx 24, R-shf x R-idx 24, P24 x P12 2, every other pair 0); the negative control
  passed 11 of 11. Result: "PASS (smoke run, not the D6)", which does not count as the D6.
- **The blocking findings of the first review**, 19 of 19 as expected (`blockers`), and **of
  the second review**, 14 of 14 (`blockers3`).
- **The findings of the third review**, 18 of 18 as expected (`blockers4`):
  - B2, end to end on two campaigns with one lot analyzed at M3 and compared once: a second
    comparison of the lot and point by `compare-slots` with another `--records` folder, and
    with the same folder, refused, the journal unchanged; `orchestrate` with another
    `--records` folder refused before writing any record; the registered comparison report
    altered afterwards: `orchestrate` wrote a lock; the report moved away afterwards (nothing
    deleted): `metrics` wrote a lock; two `compared` entries for one lot and point are
    damaged evidence;
  - B5: the real qualification record passes on this machine; a PASS record without the
    machine-checked conditions, with part of them, with an empty value, with no memory
    module, with a module without its part number, or with an unknown condition is refused;
    the prerequisite gate refuses an incomplete record named by its correct SHA-256 and
    passes the real record with a D6 PASS of the current versions;
  - the mask covers dictionary keys; `d6.py` and `population_v2.py` refuse to run when the
    project folder is inside the user's home directory (the detector simulated in the test
    process, since this project is not inside it).
- **Test suite** with the repository's virtual environment: 505 tests, 489 passed, 16
  xfailed, 0 failures, 0 errors (from the JUnit XML). No file under `src/` changed.

## Expectation changed during development

In the development run of `blockers4` (outside this folder), the test "a PASS qualification
record with no memory module is refused" expected the message "lacks the conditions"; the
code refused the record with "lists no memory module" (an empty list is present, not
missing). The expectation was changed to that message before this run; the code was not
changed.

## Coverage still partial (left open)

The tests prove the mechanism of each correction, not every path:

- B2 is not tested through `orchestrate` on a lot that has records 3 and a damaged
  comparison of only one of several points;
- check 1 of the D6 is not tested with an execution record whose checkout is at a wrong
  commit;
- B7 is tested for a generation stopped after a detection, not for a regeneration nor for
  the later events of an execution;
- the refusal of a project inside the home directory is tested with the detector simulated,
  not with a project actually placed there;
- B8 checks the outcomes of two simultaneous executions, without forcing both to reach the
  former race window;
- the containment of the default root is tested only for the normal root, not for a root
  redirected outside the project.

`SHA256SUMS` lists every file of this folder except itself.
