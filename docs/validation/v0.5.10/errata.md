# v0.5.10 errata log (append-only)

Process diet 2, item 5: one append-only errata log per phase. Each entry gives the date, the
source commit, the correction and its impact.

## 2026-11-24: a variable name redacted before the first commit

- **Source:** not yet committed. The phase log's entry 23 (the isolation test's `before`) and
  `engines/isolation-test.json` named the Windows variable of the local application-data folder.
  The record of what the AppContainer profile created outside the project used that name.
- **Correction:** the name was replaced by `<local application-data folder>`, before either file
  was first committed. The privacy check of `scripts/commit_checked.py` bars that name in any
  line, whether or not it is part of a path. No path or user name was involved.
  - The code got the same change: `sandbox.py`, `isolation_test.py`, `delete_profile.py`. The
    variable names are now built from parts, and the private folders of a run are called `ad`
    and `lad`.
  - The phase log records the redaction in a `note` entry.
- **Impact:** none on any result. The isolation test ran with the earlier folder names, and the
  change renames two private folders only.

## 2026-11-24: entry 2, five runs whose worker hash was the empty file's

- **Source:** `0a96209`. In `log.jsonl`, the `before` entries of `exovetter:TIC-124206468`,
  `leo:TIC-142937186`, `leo:TIC-372596795`, `triceratops:TIC-124206468` and
  `triceratops:TIC-142937186` give `worker_sha256` = the SHA-256 of an empty file.
- **Cause:** `run_engines.stage_worker` copied the worker into one shared file and hashed it. With
  runs in parallel, one thread hashed the file while another was rewriting it.
- **Correction:** the five runs, their logs and their result files are kept unchanged.
  `build_table.py` lists them as provenance gaps and treats their outputs as
  `unavailable_provenance` in G1 to G5, as Codex's round on the report asked (blocking item 1).
- **Impact:** in G1 and G3, LEO-Vetter loses two classes (one FA, one PC), TRICERATOPS two joint
  outcomes, and exoVetter one TOI. The report uses the corrected table.

## 2026-11-24: entry 3, the isolation test had 24 checks, not 25

- **Source:** the phase log's `after` entry of `isolation-test-2` and the commit message of
  `67bfbb7` say "all 25 checks hold".
- **Correction:** `isolation-test.json` holds 24 checks: 14 network, read and write checks, 7
  imports, 2 controls and the listener. All 24 hold.
- **Impact:** none on the result.

## 2026-11-24: entry 4, when the crosswalk was written

- **Source:** the phase log's `crosswalk` note says it was written "before any engine result on a
  TOI is read".
- **Correction:** it was written after the first TLS runs had finished. At that time only their
  status and CPU seconds had been seen (`ok 232.7` and the like), and no metric.
  - The G2 pair "TLS SDE ≥ 9 against LEO-Vetter FA:weak" is not in the note; `table.json`
    labels it so.
  - The centroid aggregation (the minimum over the sectors) and the FPP rule (outside [0, 1] is
    unavailable) were chosen after the runs. `table.json` labels both post hoc.
- **Impact:** the comparisons were already post hoc and descriptive. No class or threshold
  changes.

## 2026-11-24: entry 5, TGLC zeros and counting units

- **Source:** `census-kepler.json` stores TGLC counts as `0`. Its `tglc_note` says they are not
  determined.
- **Source:** the report gave several counts without naming the unit. Kepler and K2 planets are
  rows; CTOIs are entries.
- **Correction:** the report reads TGLC as "not determined" and names each unit. The distinct-TIC
  counts are in `recheck-after-codex.json`.
- **Impact:** none on the ranking.
