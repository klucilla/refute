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
