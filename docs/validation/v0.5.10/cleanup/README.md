# The cleanup of `.cache/v0510` (2026-11-24)

The maintainer's decision of 2026-11-24 (#218, comment 7139692729, item 4) said to delete
`.cache/v0510/` (the tools' environment, the downloaded light curves, the query caches) with a
committed record, after keeping in the repository what has value. The cleanup ran after the gate
review.

[cleanup_v0510.py](cleanup_v0510.py) ran three steps, each refusing if the one before it did not
complete:

| Step | Record | Result |
|---|---|---|
| `survey` | [survey.json](survey.json) | 28,762 files, 7,105,806,829 bytes. The environment's files are recorded per package folder; every other file is listed with its SHA-256. |
| `archive` | [manifest.json](manifest.json) | 557 files, 50,111,278 bytes, copied to `K:/Meu Drive/Pessoal/Projetos/refute/cache-archive-2026-11-24-v0510`, all matching. The SHA-256 of source and destination are checked, and `MANIFEST-sha256.json` and the script are copied there too. |
| `clean` | [deletion-log.json](deletion-log.json) | 28,762 files deleted (7,105,806,829 bytes) and 4,600 folders, `.cache/v0510` itself included. Each file was hashed again first, and each Drive copy was checked again. |

**Kept on the Drive:**
- census and route (e): the per-target census tables and the cached catalog answers;
- the Codex working files;
- every engine run's job, stdout, stderr and result;
- the workers that ran, including the two GPL-chain workers (never in the repository);
- the tools, the probe and the synthetic inputs.

**Deleted without archive, as regenerable:**
- **The engines' environment:** `wheelhouse-manifest.json`, `install-record.json` and the scripts
  rebuild it.
- **The MAST files:** `data-check.json` gives their URLs and SHA-256.
- **The staged TIC and Gaia tables:** `stage_catalogs.py` queries them again. Gaia rows are not
  archived.
- **The runs' private caches.**

**Also deleted, inside `.cache`:**
- the gate's detached worktree, by `git worktree remove`;
- its two helper folders, `.cache/gate-v0510` (4 files) and `.cache/gate-v0510-tools` (2 files),
  whose review and prompt are stored in `docs/gates/`.

**Not touched (outside the project):**
- the AppContainer profile `refute.v0510.engines`. Its removal is the maintainer's, with
  `engines/delete_profile.py`;
- the uv-managed CPython builds.

## The closing cleanup (2026-11-24, after the phase closed)

By the maintainer's decision received at 17:50 local (#218, comment 7144131066), item 6.
[cleanup_scratch.py](cleanup_scratch.py) wrote [scratch-record.json](scratch-record.json).
- **Folders:** `.cache/r1124`, `.cache/r1124b` and `.cache/r1124c` were this phase's working
  folders: commit messages, comment drafts and helper scripts.
  - 52 files (2,337,435 bytes) were copied to
    `K:/Meu Drive/Pessoal/Projetos/refute/cache-archive-2026-11-24-v0510-close`, all matching.
  - They were then deleted by literal path, and the three folders were removed.
- **Branches:** the two local branches already merged into `main` were deleted with
  `git branch -d`, after `git merge-base --is-ancestor <branch> main` (CLAUDE.md, the permanent rule
  of the same day):
  - `claude/v0-2-1-integration`, at `5b86736`;
  - `claude/v0-2-1-reopen`, at `2e4ff99`.

  `claude/v0-3-planning-draft-abff23`, `diag/clock-info` and `v04-lock-attempt-1` are not merged,
  and they stay.
- **Kept:** the folders of other phases that are still in use (`lock-compat`, `maint1120`,
  `tools`, `v04`, `v055`, `vm`, `wt-v021`) and the AppContainer profile, which the maintainer
  removes.

## The cleanup of `.cache/r1124d` (2026-11-24, after the closing stop)

By the maintainer's decision received at 18:59 local (#218, comment 7145663950), item 2.
[cleanup_r1124d.py](cleanup_r1124d.py) wrote [r1124d-record.json](r1124d-record.json).
- **The folder:** `.cache/r1124d` was the working folder of the closing stop. It held the commit
  messages of the closing cleanup and of the site draft, and the two helper scripts that edited the
  site's draft branch.
- **The files:** 4 files (9,245 bytes) were copied to
  `K:/Meu Drive/Pessoal/Projetos/refute/cache-archive-2026-11-24-v0510-r1124d`, all matching. They
  were then deleted by literal path, and the folder was removed.
