# Third self-test of the population harness v2 (not a measurement; superseded)

Self-test of an intermediate version of the files, after the corrections of the second code
review (Amendment 4, clarifications of 2026-10-13): `../population_v2.py` (SHA-256
`5df09622b9f32ca3bb649e8993f8edc529afe571c94cbc2d69518facbbaad2fa`),
`../population_compare.py` (SHA-256
`0e62dcc4dc99a53fcc319aa513734f31e9d877406cc81e56ea97c80042e2f01f`) and `../d6.py` (SHA-256
`1df4efc02a475cbebe59246b9b605eee589546081c8ed9d642c34bdd66577c98`), run on 2026-10-13 from
16:05 to 16:19 UTC on the branch at commit `113e07c`, before any of these files was
committed. The third code review then found two of the corrections incomplete (items 3 and 6
of the clarifications); the files were corrected again and the self-test of the committed
files is `../selftest-v2-4/`. This folder is kept as the record of that round, unchanged.

**Self-test outcomes are not a measurement. No criterion, size, band, mechanism, limit or
amendment of the population study may be decided or justified by them.** The populations are
`selftest` and `determinism` (prefixes `refute-v0.2.1-population-selftest` and
`refute-v0.2.1-population-determinism`); no development case was generated or analyzed.
Every campaign is a diagnostic under `.cache/population/v2-selftest-3/campaigns`.

The driver is `selftest_v2.py` (the driver of `../selftest-v2-2/` with the new step
`blockers3`, two more declarations and this work folder); every command it ran and its
output are in `selftest-v2-log.txt`, in order (the repository path replaced by `<repo>`, the
user name by `<user>`). The artifacts are in the git-ignored `.cache/population/v2-selftest-3/`;
`artifacts-SHA256SUMS` lists them.

## What was checked

- **Reference cases**: the three cases keep their SHA-256, and so do the stored files.
- **Overhead per generation**: v1 36.0, 36.1, 35.5 s; v2 40.2, 40.4, 41.3 s;
  40.4 / 36.0 - 1 = **12.2 %** (accepted up to 20 %); v1 and v2 give the same SHA-256 for all
  520 cases in the three runs.
- **Determinism**: 520 cases, three generations byte-identical (14060 segments, 50920
  blocks), set accepted.
- **Injected differences**: 5 of 5 in blobs, 6 of 6 in result records.
- **Journal and lock**, **analysis in two slots at M0 and M3**, **D6 machinery (smoke run,
  not the D6)**: as in `../selftest-v2-2/`; the D6 smoke run took its 13 cases from the
  accepted set of the whole `determinism` campaign, found exactly the declared control
  differences, and its negative control passed 11 of 11.
- **The blocking findings of the first review**, 19 of 19 as expected, and **of the second
  review**, 14 of 14 (`blockers3`): a FAIL qualification record and another BIOS refused; a
  D6 report of another `d6.py` refused; a D6 planned from a subset refused and a swapped case
  list caught; a stop after a detection keeps the observation and the lock; a registered
  comparison altered or missing is damaged; a superseded predecessor stays usable; the mask
  of `/home/<user>`; the default root contained.
- **Test suite**: 505 tests, 489 passed, 16 xfailed, 0 failures, 0 errors (JUnit XML).

`SHA256SUMS` lists every file of this folder except itself.
