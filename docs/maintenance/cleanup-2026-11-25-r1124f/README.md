# The cleanup of `.cache/r1124f` (2026-11-25)

This cleanup was asked by the maintainer with the approval of the v0.5.11 charter (#218, comment
7146858167). [cleanup.py](cleanup.py) ran once as the metered unit `cleanup-r1124f`
(launch_v5) and wrote [record.json](record.json).

- **The folder:** `.cache/r1124f` was the working folder of the stop that proposed the charter. It
  held commit messages, comment drafts and helper scripts.
- **How:**
  - 15 files (32,059 bytes) were copied to
    `K:/Meu Drive/Pessoal/Projetos/refute/cache-archive-2026-11-25-r1124f`, and every copy
    matched by SHA-256.
  - The files were then deleted by literal path, under a guard that refuses links and
    junctions, and the folder was removed.

Nothing outside `.cache` was deleted.
