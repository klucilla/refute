# v0.5.1 WP5: re-executions (rows 5.2 (b) and 5.3)

Development evidence only; nothing here decides a verdict or changes a published record. Both
re-executions were approved by the maintainer on 2026-11-07, and the approval and procedures were
recorded on #208 before they ran.

## Row 5.3: the v0.5 C1 development prefix

- Script: [reproduce_c1_prefix.py](reproduce_c1_prefix.py); output:
  [reproduce-c1-prefix.json](reproduce-c1-prefix.json).
- Started at commit `90071c3` and finished after `7f07583`. The script reads `git rev-parse
  HEAD` at the end, so its output names `7f07583`; between the two commits only
  `docs/validation/v0.5.1/wp5/reproduce_dossiers.py` was added, and the analysis code is the same.
- Result: **260 of 260 records reproduced exactly** (every field except `cpu_seconds` and the
  runner's `task` identity), against `.cache/v05/calibration/c1-prefix/records.jsonl` (SHA-256
  `93f23b04dfacc89924cbe2bd50f1493d810e19a1388171b146fd315165b4ab32`).
- Processor time: 3.49 hours (estimate 3.2; the stop at 1.5 times the estimate, 4.8 hours, was
  watched by a separate process and did not trigger).

## Row 5.2 (b): one recorded dossier per TESS version

- Script: [reproduce_dossiers.py](reproduce_dossiers.py) (commit `7f07583`); the dossiers, their
  archives and the commands are in its docstring and on #208.
- **v0.1 (`TIC-138819293`): not reproduced under the fixed rule with current-code inputs**
  ([reproduce-dossiers-v0.1.json](reproduce-dossiers-v0.1.json)); `verdict.json` is not
  byte-identical either. Recorded verdict SURVIVED
  ("every test passed", 5 tests); with the current code REFUTED ("fatal failure in:
  centroid_shift", 10 tests). The light-curve files fetched from MAST have the recorded SHA-256;
  the TIC star and neighbor records differ from the recorded ones (fields added since v0.1), and
  the key values differ in the sixth significant digit.
- Why, from the code's history (not a new measurement): the current code resolves the v0.1
  claim with defaults that commit `deaa4eb` (2026-10-08, v0.2, before tag `v0.2.0`) introduced:
  `data.target_pixel_files` defaults to true and the tests `centroid_shift`, `aperture_depth`,
  `nearby_contamination`, `period_alias` and `systematics` run by default. The v0.1 claim does not
  name them, so every code version from v0.2 on runs them on it. The result is not code alone:
  the `centroid_shift` failure comes from two target pixel files fetched today (the v0.1 run read
  none), and the TIC records are today's; the differences are kept next to the verdict in the
  output. Codex's review (`docs/plans/v0.5.1-consensus/wp5-reexec-answer.md`) also notes that the
  script's "reproduced" predicate leaves out the byte identity that row 5.2 names; for v0.1 the
  bytes differ as well, so the outcome is the same. The v0.1 dossier's own
  `REPRODUCE.md` reproduces it at its locked commit, which is how it was reproduced in 2026-10
  (`refute-v0.1-reproduction.zip`, asset of release v0.1.0).
- Following the maintainer's condition, the work stopped at this version: v0.2, v0.4 and v0.5
  were **not run**, and the question went to the maintainer on #208.
