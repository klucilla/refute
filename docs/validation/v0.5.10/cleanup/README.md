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
