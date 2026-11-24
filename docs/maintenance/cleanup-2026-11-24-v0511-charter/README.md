# The cleanup of `.cache/r1124e` and `.cache/v0511` (2026-11-24)

This cleanup was done by the maintainer's decision received at 19:33 local (#218, comment
7146372481), item 5, after the review files were stored (item 0). [cleanup.py](cleanup.py) wrote
[record.json](record.json).

**What was deleted:**
- **`.cache/r1124e`:** the working folder of the stop on the site's approval. It held commit
  messages, comment drafts, the site checks' scripts, their logs and their JUnit files.
- **`.cache/v0511`:** the draft charter's review (`charter-review/`) and the round on the v0.5.11
  charter (`round2/`).
  - Their draft, cover, prompts and answers are stored unchanged in
    [docs/plans/v0.5.11-consensus/](../../plans/v0.5.11-consensus/README.md).
  - Their event files, standard output and process id are not stored in the repository. They
    are on the Drive.

**How:**
- 33 files (908,918 bytes) were copied to
  `K:/Meu Drive/Pessoal/Projetos/refute/cache-archive-2026-11-24-v0511-charter`, and every copy
  matched by SHA-256.
- The files were then deleted by literal path, under a guard that refuses links and junctions.
  Both folders were removed.

Nothing outside `.cache` was deleted. `.cache/r1124f`, the working folder of this stop, remains.
