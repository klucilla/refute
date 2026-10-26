# Codex's audit of 2026-10-26: four fixes, X2f as S1 + S2, recorded before X2f's S1

Codex's audit of commit `ab4c233`, on 2026-10-26. The maintainer checked R1, R2, R3 and the
divergence of S3 by reading and decided the same day: everything before X2f's S1, when the code
freezes; validity and execution, so plan B's design does not change. **No historical record,
lock, claim or published dossier is changed.**

## The fixes (each with its test before the code)

| # | Finding | The fix | Where |
|---|---|---|---|
| R1 | `write_archive` could write its zip (or its `.sha256`) inside the tree it archives, as one of its entries or over one, and overwrote an existing zip. | A destination, or its digest, inside the archived tree (also through a link) is refused, and an existing zip or digest is refused, both before any write; the zip and the digest are created exclusively; the entries are named from the resolved root (so `.` or `a/..` give the folder's name, an older defect found by the review); `refute archive` exits 1. | `src/refute/core/dossier.py`, `src/refute/cli.py` |
| R2 | A task that failed left no record and was submitted again by any relaunch. | Each submission is recorded before it runs (`attempts/`) and each failure at once (`failed/`); a relaunch does not submit again a task that failed, or whose outcome is unknown (its run was cut short), unless a decision recorded in the run folder (`retry-decisions/*.json`, with a non-empty `decision` text) names that marker in `covers`; a new failure needs a new decision. | `docs/validation/v0.2.1/population/x2_study.py` |
| R3 | The ceiling was counted from each invocation's own start, so a relaunch had a fresh budget. | Every invocation records its time (`consumption/<started>.json`: at every check, after every task, and closed at its end) and the ceiling compares the lot's whole time with it; an invocation that did not close its record stops every relaunch until a recorded decision gives its time, never below the time it had recorded; a time that is not a finite, non-negative number is refused. The ceiling is read last, after the submission's record is written and right before the submission; a task it stops is recorded as not submitted (`not-submitted/`), not as an unknown outcome. The reports give the time before, during and in all. | `x2_study.py` |
| R4 | A claim could list one attachment twice, also with paths equal only after normalizing. | The claim's validation refuses two attachments with equal normalized paths, also by case, before any lock or dossier; no field is added and no claim hash changes (Codex checked the seven locked claims: canonical form and hash unchanged). The ML production, which reads its claim file as JSON, applies the same rule before anything is prepared. | `src/refute/core/claim.py`, `src/refute/packs/ml/production.py` |

**The tests, before the code:** [tests/test_audit2_fixes.py](../../../../tests/test_audit2_fixes.py)
(R1, R4) and [tests/test_x2.py](../../../../tests/test_x2.py) (R2, R3, X2f), committed in
`4d95826` with their first run ([first-run.json](first-run.json): 68 tests, 17 failing, every
new fix; 51 passing, the controls and the unchanged tests). Codex's review asked for adversarial
cases (a run cut short, an open or non-finite consumption, a link, a relative root, the ML
production's attachments); they were added and run on the code of `4d95826`, the fixed files
restored afterwards and checked by SHA-256
([before-fixes-round-1.json](before-fixes-round-1.json): 73 tests, 21 failing, 51 passing, 1
skipped: the link case needs a privilege this account does not have). Its second review added
two R3 cases (a reconciliation below the recorded time; a write that crosses the ceiling before
the submission), also run on that code first
([before-fixes-round-2.json](before-fixes-round-2.json): 75 tests, 23 failing, 51 passing, 1
skipped). With the code, all pass. **Codex's review:** three rounds: round 1,
objections (R2 a failure that could stay unmarked, R3 an interrupted run's time and non-finite
times, R1 relative roots, R4 the ML production's JSON input, a self-contained resumption
procedure); round 2, objections on R3 only (a reconciliation below the measured time, the clock
read before the attempt's write); round 3, `ACORDO`.

`rmin_study.run_lot` (the R_min study's own runner, finished and frozen) is not changed; its
retry and budget behaviour stays as recorded with that study.

## X2f is S1 + S2

As plan B (section 6) foresaw: `X2F_SEQUENCE = ("x2f-s1", "x2f-s2")`, `LOTS` without S3, the
command line refusing an unknown lot; the declaration's
[Revision 1](../reopen/stage-1/after-x2e/x2f-declaration.md): **184 cases, 18 400 curves**; estimate
**201.5 LP-h, 9.16 h**; ceilings 3.25 h and 10.50 h, **13.75 h** in all; the runner's R2 and R3
replace the manual remaining budget of the resumption procedure.

## Recorded, not coded now

- **Gate 2 and before X5:** [../reopen/stage-1/plan-b/additions-2026-10-26.md](../reopen/stage-1/plan-b/additions-2026-10-26.md):
  the profile O2's acceptance gets a test with a year whose flux is entirely invalid after the
  filters (the required years from the domain, before the flux filters; a disappearing year never
  allows a PASS with fewer years; outside the domain a fatal diagnostic FAIL never becomes
  `REFUTED`); a new evaluator of G1, G2, B5 and W1e besides C1 to C6, before X5; B2's count, 275 of
  360 (the 195 of 250 of the earlier documents does not apply to B2).
- **Erratum E2 of the v0.2 calibration** ([../../../../calibration/v0.2/ERRATA.md](../../../../calibration/v0.2/ERRATA.md)):
  the post-mortem's explanation of TOI-6038 A b ("1 degree of freedom, so its error is not
  inflated") is not supported by the locked code (`ephemeris.py` at `v0.2.0-calibration-lock`
  scales the covariance by `max(1, chi2_red)` whenever `dof > 0`). The FAIL of v0.2 does not
  change; the post-mortem is not edited.

## The suite, here and in Codex's run

- **Here:** the full suite on the fixes' tree, before the commit: 3934 tests, 0 failures, 0
  errors, 89 skipped (JUnit).
- **In Codex's run** (its audit): the 35 errors in the VM tests and the 1 in the "outside a git
  repository" fixture came from **its environment**, not from the code (recorded by the
  maintainer on 2026-10-26); in this machine's environment the same tests pass. The fixture
  assumed that the temporary folder lies outside any git repository; it now sets
  `GIT_CEILING_DIRECTORIES` (`tests/test_canonical_lock.py`), so git never looks above it.

## The code after the fixes

- The fixes' commit: `2baa0c6f7001216fe8b6e5ba66b609c297baa3aa`; its `refute-code-1` hash
  `8062739ccc53e85c1e86b6be52a59b36e204d6f9817184f62444ac5e4cb104b1` and X2's lot code digest
  `f06f57ad7672aae790a46d12a65cb44a9d17973ecdef3747b00c6415fbb64630`
  ([../audit-2026-10-24/scripts/code_hashes.py](../audit-2026-10-24/scripts/code_hashes.py), after
  checking that every covered file is the committed one). These are before the dependency update
  of 2026-10-27, which changes both; X2f's S1 records its own in its declaration.
