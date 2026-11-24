# The `.cache` cleanups of 2026-11-24: the record

This folder is the verifiable record of the two cleanups of `.cache` done on 2026-11-24 during
v0.5.9. The v0.5.9 gate review found that neither had left a record in the repository (finding 1,
important: [docs/gates/v0.5.9-review.md](../../gates/v0.5.9-review.md); issue #220). The
maintainer's decision of 2026-11-24 (#218, comment 7130900283, item 1) asked for this record, as in
the precedent [docs/validation/v0.5.5/archive/](../../validation/v0.5.5/archive/).

The cleanups deleted only inside `.cache` (git-ignored), by literal path. A guard refused any path
outside the named folders and any link or junction. Every deleted file was hashed before it was
deleted.

## The two cleanups

| | A: first cleanup | B: second cleanup |
|---|---|---|
| Decision | #218 comment 7122240195, item 5 (the named paths) | #218 comment 7125778250, item 4 (`.cache/v052`, `v053`, `maint1120`, `v05`, `v055`) |
| Script that ran | [a/archive_and_clean.py](a/archive_and_clean.py) | [b/cleanup_survey.py](b/cleanup_survey.py), [b/cleanup_citations.py](b/cleanup_citations.py), [b/cleanup_classify.py](b/cleanup_classify.py), [b/cleanup2.py](b/cleanup2.py) |
| Drive destination | `K:/Meu Drive/Pessoal/Projetos/refute/cache-archive-2026-11-24` | `K:/Meu Drive/Pessoal/Projetos/refute/cache-archive-2026-11-24b` |
| Archived, SHA-256 of source and destination checked | 6 files, all matching ([a/manifest-a.json](a/manifest-a.json)) | 10,194 files, 2,912,867,864 bytes, all matching ([b/manifest-b.json](b/manifest-b.json)) |
| Deleted | 57 files, 10,730,844 bytes; 6 folders ([a/deletion-log-a.json](a/deletion-log-a.json)) | 10,194 files, 2,912,867,864 bytes; 314 empty folders ([b/deletion-log-b.json](b/deletion-log-b.json)) |
| Citation list | [a/citations-a.json](a/citations-a.json), computed **after** the deletion | [b/citations-b.json](b/citations-b.json), from the search that ran **before** the deletion |
| Kept | not applicable | `.cache/maint1120/site-synth/` and `.cache/v055/site-pause/` (two git worktrees of the site repository), `.cache/v055/tools/` (`pinrun.py`) |

The scripts, manifests and deletion logs here are byte-for-byte copies of the files those cleanups
wrote. Their SHA-256 are in [summary.json](summary.json). The Drive copy of each manifest is
`MANIFEST-sha256.json` at the root of its Drive folder.

## What each citation list shows

**A (57 files).** That cleanup deleted named paths; it did not search for citations first. Its
deletion log recorded each file's SHA-256. From those hashes, [build_record.py](build_record.py)
searched the git-tracked files at the commit before this record, for each deleted file's SHA-256
and for its path. It also looked for tracked files with the same bytes, a stored copy.
- 40 of the 57 files are cited by a tracked file.
- 42 have a stored copy in the repository, mostly the v0.5.8 Zenodo record (`docs/validation/v0.5.8/zenodo/`) and Codex's stored answers.
- The two cited files without a stored copy (`.cache/v058/zenodo/metadata.json` and `.cache/v058/zenodo/record/MANIFEST-sha256.json`) are among the 6 archived to the Drive.
- The files neither cited nor stored are Codex's raw event logs and their process files:
  - the four `codex-events.jsonl` were archived;
  - the rest are `codex.pid`, `codex-stdout.txt` and `codex-stderr.txt` files of 7 to 141 bytes.
- So every cited file of A is stored in the repository or archived.

**B (10,194 files).** The citation search ran before the deletion, on every git-tracked text file,
for each file's SHA-256 and for paths under the five folders ([b/cleanup_citations.py](b/cleanup_citations.py)).
Each file was then classified ([b/cleanup_classify.py](b/cleanup_classify.py)):
- 10,069 were `cited` by a SHA-256 or a path (mostly the FITS files and records of v0.5.2 and v0.5.3);
- 89 were `value`;
- 36 were `regenerable`.

All 10,194 were archived and checked before any deletion. Before it deleted a file, [b/cleanup2.py](b/cleanup2.py) hashed it again and refused if the bytes differed from the archived copy.
In `citations-b.json`, each row gives the file's class, its reason and the committed records that
cite it (indices into `citing_records`).

The two large work files of B's search are on the Drive under `cache-archive-2026-11-24b/record/`,
with their SHA-256 checked ([b/drive-extra.json](b/drive-extra.json)). They are above 5 MB, so they
are not in git:
- the survey of every file in the five folders (`survey.json`);
- the classification of every file (`classes.json`).

A copy of the raw citation index (`citations.json`) is next to them.

## How to check

- **Re-run the summary check:** `summary.json` gives every file's SHA-256 and checks that every file B deleted was archived with the same SHA-256.
- **Check a file cited by a committed record:** take its SHA-256 from the record, find it in `b/manifest-b.json` or `a/manifest-a.json`, and read the Drive path next to it.
- **Check the Drive copies:** the Drive is the maintainer's. Hash a copy and compare it with `destination_sha256` in the manifest.

## Not verified here

- That the Drive copies are still unchanged today: the manifests record their hashes at archiving time.
- For A, that no file was cited before 2026-11-24 by a record that has since changed. The search ran on the tracked files at the commit before this record.
