# D: the cleanup of the `.cache` folders out of use (2026-11-24, after the round of 11:09)

This is the fourth cleanup of 2026-11-24; parts A to C are in [the folder's README](../README.md)
and [c/](../c/README.md).

**Basis.** The maintainer's decision received at 11:09 local (#218, comment 7133936093), item 4.
It is recorded as the rule of #220's finding asks: the script, the citation list, the manifest
and the Drive destination are committed here.

| | |
|---|---|
| Script | [cleanup_d.py](cleanup_d.py) (`survey`, `archive`, `clean`) |
| Citation list, before the archive | [citations-d.json](citations-d.json), against the tracked files at `654deda` |
| Archived, SHA-256 of source and destination checked | 9,418 files, 217,416,355 bytes, all matching ([manifest-d.json](manifest-d.json), 14:35:42Z) |
| Drive destination | `K:/Meu Drive/Pessoal/Projetos/refute/cache-archive-2026-11-24d` (the manifest as `MANIFEST-sha256.json`, and the script as it was at archiving time) |
| Deleted | the same 9,418 files and 1,436 empty folders ([deletion-log-d.json](deletion-log-d.json), 14:36:28Z) |

**Citations.**
- 749 of the files are cited by SHA-256 in a committed record, and 202 have a copy with the same
  bytes in the repository.
- 8,350 are cited by SHA-256 or by a path, the file or a folder above it. Committed records name
  most of these folders as wholes.
- Everything was archived before anything was deleted.

**The interrupted first attempt.**
- `clean` first stopped at a read-only file, a git pack file under `.cache/tb/maxwent/.git`,
  after deleting 1,504 files and before writing its log. Each of those files had been hashed and
  had matched the archive before it was deleted.
- The script was then changed in two ways:
  - it clears a file's read-only attribute before deleting it;
  - it logs, as "deleted by the interrupted first attempt", each archived file that is no longer
    present, with the size and SHA-256 recorded in the manifest.
- The second run deleted the other 7,914 files, each hashed again first.
- The copy of the script on the Drive is the one that ran `survey` and `archive`; the committed
  one is the one that ran `clean`.

## What was deleted, and why it was out of use

| Folder | Files | Bytes | What it held |
|---|---|---|---|
| `.cache/codex` | 1,071 | 49,090,435 | Codex work of October 2026 (v0.3 and earlier); the answers that count are stored in `docs/` |
| `.cache/data` | 9 | 12,000,627 | the UCI files of the v0.3 paper study (2309), closed |
| `.cache/proposta-v04` | 4 | 76,324 | a v0.4 proposal note on Gaia data, never used |
| `.cache/pub1119` | 203 | 6,030,637 | the publication of 2026-11-19/20: drafts, comments, tools (done) |
| `.cache/seal` | 92 | 373,895 | the v0.3 seal's work files (closed 2026-10-20) |
| `.cache/tb` | 372 | 82,214,098 | v0.3 third-party benchmark patches, checks and clones (closed) |
| `.cache/v051` | 572 | 37,602,181 | v0.5.1 work files (closed 2026-11-08) |
| `.cache/v054` | 6,430 | 11,542,385 | v0.5.4 work files (closed 2026-11-13) |
| `.cache/v056` | 23 | 339,958 | v0.5.6 site and hygiene work files (closed) |
| `.cache/v057` | 66 | 6,149,440 | v0.5.7 work files (closed) |
| `.cache/v058` | 573 | 11,992,726 | v0.5.8 work files (closed) |
| `.cache/v059-closing` | 3 | 3,649 | the v0.5.9 stop's work files |
| **Total** | **9,418** | **217,416,355** | |

## Kept, and why

| Path | Why |
|---|---|
| `.cache/v04` | `tools/codex_affinity.ps1` and the v0.4 records; kept by the maintainer's decisions |
| `.cache/lock-compat` | the lock-compatibility worktrees (git worktrees of this repository); kept by the decisions |
| `.cache/v055/tools` | `pinrun.py`, used to pin every run to processors 8 to 31 |
| `.cache/maint1120/site-synth` | a git worktree of the site repository; kept by the decision of 09:03 |
| `.cache/tools` | the tools of the working mode (CI waits, JUnit counts) in use |
| `.cache/vm` | the VM scripts, SSH and GnuPG material: private keys and keyrings are never archived or deleted automatically (CLAUDE.md) |
| `.cache/wt-v021` | the TESS-EB table cited by `src/refute/packs/tess/discover/pilot.py` (`TESS_EB_STATIC`) |
| `.cache/r1124` | this round's work files, in use until its stop |

`.cache/frozen` is not present on this machine.
