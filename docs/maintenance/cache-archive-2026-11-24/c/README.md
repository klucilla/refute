# C: the cleanup of `.cache/v059` (2026-11-24, after v0.5.9 closed)

The third cleanup of 2026-11-24 is recorded here; cleanups A and B are in [the folder's README](../README.md).

**Basis.** It is item 6 of the maintainer's decision of 2026-11-24 on the v0.5.9 gate (#218,
comment 7130900283). It ran after everything else was committed and pushed: `main` was at
`2835337`, checked against GitHub, and that commit's CI was green (run 45391720646). It follows the
rule the gate review's finding 1 asked for (#220): the script, the citation list, the manifest
and the Drive destination are committed here.

| | |
|---|---|
| Script that ran | [cleanup_v059.py](cleanup_v059.py) (`survey`, then `archive`, then `clean`) |
| Citation list, before the archive | [citations-c.json](citations-c.json), against the tracked files at `2835337` |
| Archived, SHA-256 of source and destination checked | 965 files, 37,675,017 bytes, all matching ([manifest-c.json](manifest-c.json), 13:16:13Z) |
| Drive destination | `K:/Meu Drive/Pessoal/Projetos/refute/cache-archive-2026-11-24c` (the manifest as `MANIFEST-sha256.json`, and the script) |
| Deleted | the same 965 files, each hashed again first, and 150 empty folders; `.cache/v059` itself is gone ([deletion-log-c.json](deletion-log-c.json), 13:16:19Z) |

Everything was archived before anything was deleted, so what has value is in the repository or on
the Drive, with a manifest.

## What was deleted, per folder

| Folder under `.cache/v059` | Files | Bytes | Cited by SHA-256 | Same bytes in the repository |
|---|---|---|---|---|
| top-level files (commit messages, CI wait logs, cleanup A's manifest and log, work copies) | 31 | 3,066,081 | 3 | 5 |
| `checks` (outputs of the verification scripts) | 6 | 5,186 | 0 | 0 |
| `cleanup2` (cleanup B's work files) | 8 | 27,158,075 | 5 | 2 |
| `codex-round1` to `codex-round4` (prompts, answers, raw events) | 21 | 1,030,708 | 9 | 6 |
| `comments` (the posted issue comments, as drafted) | 17 | 45,709 | 0 | 0 |
| `data` (the per-target data files `refute/tess/TIC-*.json`) | 24 | 783,790 | 24 | 0 |
| `env` (a matplotlib cache) | 1 | 140,567 | 0 | 0 |
| `gate` (the gate review) | 1 | 18,987 | 0 | 1 |
| `pilot` (the pilot's driver and observer files) | 8 | 38,212 | 0 | 1 |
| `run` (the run's attempts, unit records, results and pixel-file deletions) | 782 | 4,912,488 | 276 | 0 |
| `site` (the site draft's check outputs and messages) | 16 | 234,092 | 0 | 0 |
| `tests` (JUnit files) | 33 | 133,255 | 6 | 0 |
| `tools` (working scripts) | 17 | 107,867 | 5 | 6 |
| **Total** | **965** | **37,675,017** | **328** | **21** |

## Notes

- **The `run` folder's unit records:**
  - their content is in [prototype-units.json](../../../validation/v0.5.9/prototype-units.json), which cites each one's SHA-256;
  - the 48 mode records are in `prototype-records.json`.
- **Committed elsewhere:**
  - the scripts of `tools` that the records cite are in `docs/validation/v0.5.9/` and in A and B;
  - the gate review is in `docs/gates/`;
  - the pilot's observer readings are in `docs/validation/v0.5.9/pilot-observed.json`.
- **"Cited by path" in `citations-c.json`:**
  - committed records name `.cache/v059` as a folder, so every file shows that folder as a path citation;
  - the per-file citations by SHA-256, and by a path below the folder, are the informative ones.
- **Kept outside `.cache/v059`, by the decision:**
  - `.cache/v04`, `.cache/lock-compat`, `.cache/v055/tools` and `.cache/maint1120/site-synth`;
  - `.cache/frozen` is not present on this machine, and none of the three cleanups touched it.
- **Not verified here:** that the Drive copies are still unchanged today.
