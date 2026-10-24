# The external audits of 2026-10-24: four safety fixes, recorded before X2f's S1

Two external audits, by Codex and by Gemini, of commit `c83cdf7`, on 2026-10-24. The
maintainer checked the findings A1, A2, A4 and A6 and some of Gemini's items by reading, and
decided the same day: fix four findings now (safety and execution, the exception plan B allows;
plan B's design does not change), each with its test before the code and Codex's review, before
X2f's S1, when the code freezes. **No historical record, lock, claim or published dossier is
changed.**

## The four fixes

| # | Finding | The fix | Where |
|---|---|---|---|
| A1 | The TESS adapter loaded the cached manifest at `TIC-<id>.json` without checking whose it was: an intact manifest of target B at target A's path was analysed as A. | `TessAdapter.load` refuses a manifest whose `tic_id` or `target_key` is not the requested target's; the run records the target with status `ERROR` and `INCONCLUSIVE`, no test run, never a verdict from another target's data. | `src/refute/packs/tess/adapter.py` |
| A4 | A repeated run id wrote into the earlier run's directory, and `DossierWriter` overwrote existing files. | An existing run directory is refused before any download, and the directory is created exclusively before any target is fetched or any dossier written (a run that loses it to another run is refused). `DossierWriter` creates every file exclusively (`O_CREAT \| O_EXCL`); `path()` reserves a file for a producer such as a plot; `finalize()` writes the manifest, the one file it rewrites. A resumption, if one is ever supported, needs a contract of its own. | `src/refute/core/run.py`, `src/refute/core/dossier.py` |
| A5 | A claim could list one target key twice; the two targets then share a dossier directory. | `refute.core.pack.duplicate_target_keys` (case and spacing ignored) refuses such a claim before any download or dossier: in `refute fetch`, `replicate` and `calibrate` (`run.duplicate_keys_problem`), and in the ML production at every entry that prepares or runs a paper (`production.check_target_keys` in `main`, `prepare_inputs` and `build_harness`, so `run_production`; and `integration.PaperIntegration`). | `src/refute/core/pack.py`, `run.py`, `cli.py`, `src/refute/packs/ml/production.py`, `integration.py` |
| A6 | `refute review attach` wrote `review/` files and rewrote the manifest of a sealed dossier, changing its sealed core. | `attach_review` refuses a sealed dossier, with the classification `check-dossier` uses (`dossier._sealed_layout`: a `refute-seal-1` seal is a seal even if a manifest lists it); its reports go in as annexes (`refute annex`). A dossier written before v0.3 whose manifest lists those names is a legacy dossier: it still takes a review, and the rewritten manifest keeps those names (`write_manifest(..., keep_recorded=True)`). | `src/refute/core/review.py`, `src/refute/core/dossier.py` |

**The tests, before the code.** [tests/test_audit_fixes.py](../../../../tests/test_audit_fixes.py),
committed in `d8c2de3` before any fix, with its first run
([first-run.json](first-run.json): 12 tests, 11 failing, 1 passing, the A1 control). Codex's
review asked for stricter cases (below); they were added and run on the code of `d8c2de3`, the
fixed files restored afterwards and checked by SHA-256
([scripts/before_check.ps1](scripts/before_check.ps1)):
[before-fixes-round-1.json](before-fixes-round-1.json) (24 tests: 18 failing, 6 passing, the
controls and behaviour that already held) and
[before-fixes-round-2.json](before-fixes-round-2.json) (25 tests: 20 failing, 5 passing). With the
fixes, every one passes.

**Codex's review** (read only), three rounds: round 1, objections (the writer checked and did not
reserve; the ML APIs `run_production` and `prepare_inputs` were not covered; A6 refused legacy
dossiers; tests to isolate `tic_id`, the races, the ML control and the guard's refusal through
the wrapper); round 2, objections on A6 only (a modern seal listed in a manifest; a legacy
dossier losing its names when a review is attached); round 3, `ACORDO`. After it, one refusal
that went beyond A5 was taken out (`check_target_keys` also refused a claim file without
`targets`, which broke five existing ML tests whose fixtures have none): the check now refuses
duplicates only, as reviewed.

## Also in this batch

- **The command guard's hook** (`.claude/settings.json`) runs on every platform: it takes
  `.venv/Scripts/python.exe` or `.venv/bin/python`, whichever exists, and blocks the command when
  neither exists; tested first ([tests/test_hook_settings.py](../../../../tests/test_hook_settings.py):
  the POSIX case failed before the change), and through the wrapper the guard still refuses, and
  a guard that cannot run blocks.
- **A new rule** (CLAUDE.md, "Operating rules"): raw outputs larger than 5 MB never enter git;
  they are archived to the Drive with a checked SHA-256 manifest, and the repository keeps the
  script, a summary and that manifest.
- **Not fixed now, mandatory before any new paper execution** (issue #59): A2, the ambiguous
  reading of CSV and JSONL with repeated names in `recompute.py`; A3, the production entry that
  does not require a verified lock.
- **Backlog** (no work now): #168 optional dependencies per pack; #169 the `uv` version pinned
  for external contributors; #170 the code hash outside a checkout (v0.7); #171 a disk quota for
  the ML containers on the VM (before ML runs again); #172 the two `exofop_toi.csv` snapshots.

## Does any fix affect an earlier result? (read only, 2026-10-24)

Assessed, not presumed. The scan: [scripts/scan_prior.py](scripts/scan_prior.py), output
[scan-prior.json](scan-prior.json).

- **The v0.2.1 synthetic studies** (the population study, the `R_min` study, X2, X2e,
  `population_v4`'s acceptance): their harnesses call none of the changed code paths
  (`execute_run`, the TESS adapter's `load`, `DossierWriter`, `attach_review`; none is named in
  `docs/validation/v0.2.1/**/*.py`). Their results stand as recorded. The code hash changes
  (below), so a lot run later records the new code.
- **A1:** no TESS dossier is in the repository (the v0.1 and v0.2 dossiers are release assets).
  Both calibrations fetched each target with `refute fetch`, which writes the manifest under the
  target's own TIC with that TIC's `tic_id` and `target_key` (`TessAdapter.fetch`), then ran
  `--offline` on that cache (`calibration/results/20261007T221214Z-5701c54c/RUNS.md`,
  `calibration/v0.2/RUNS.md`); a mismatch would need a cache edited by hand. **Not checked on the
  released dossier archives**, which record each target's `data/manifest.json` and can be checked
  there.
- **A4:** the five dossiers in the repository (v0.3, sealed) verify against their manifests and
  their seals. The full suite passes with exclusive file creation, so the code paths that use
  `DossierWriter` never write a file twice in what the suite exercises. Whether a published run
  of v0.1 or v0.2 was ever written twice into one directory cannot be shown from the
  repository; each published run folder carries its own manifest.
- **A5:** of the 19 files in the repository that list target keys (claims and targets files), none
  lists a key twice; the TESS calibration targets file already refused duplicates, and the TESS
  schema ties each key to its `tic_id`.
- **A6:** the five sealed v0.3 dossiers have no `review/` folder and their seals verify; their
  reviews were added as annexes.

**No earlier result is shown to be affected**, within the limits stated (the released v0.1 and
v0.2 dossier archives were not opened).

## The code after the fixes (before X2f's S1)

- The fixes' commit: `aab2b26c15ce1168d92a68b43d86162210b526a2`.
- `refute-code-1` code hash of that commit (`refute.core.codehash.compute_code_hash`):
  `90de12110a099f7e9f6a2b11cbeb096555b385a55276225f674551b11abe666c`.
- X2's lot code digest of that commit (`x2_study.code_digest()`, the digest X2f's lot records):
  `2674f6ff8304678f2d5367dd666700c4cd502ebb3cf7206381bed99298d696c4`.
- Both computed by [scripts/code_hashes.py](scripts/code_hashes.py), after checking that every
  file they cover is the committed one.
- The full suite on it: 3911 tests, 0 failures, 0 errors, 88 skipped (JUnit).
- These are the hashes before the dependency update of 2026-10-27, which changes `uv.lock` and so
  both; the hashes X2f's S1 runs with are recorded in its own declaration.
