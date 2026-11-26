# Cleanup of `.cache/v0512` and of the build artifacts (2026-11-26)

The maintainer's decision of 2026-11-26, item A6 (#218, comment 7203695669): clean up what was
left in `.cache/v0512` (95 files) and the artifacts of item A4, by the hygiene rules of
`CLAUDE.md`, with a record.

**What ran:** [cleanup.py](cleanup.py), launched through `scripts/launch_affinity.ps1` (threads 8
to 31; PID 37092; exit 0). Its full output is [record.json](record.json).

## Archived, then deleted (logs with value)

- **95 files, 120,067 bytes,** from `.cache/v0512/`:
  - the close maintenance's run logs (`runs/*/stdout.txt` and `stderr.txt`, journaled by their
    hashes in `docs/validation/v0.5.12/log.jsonl`);
  - the comment and commit-message drafts;
  - three site JUnit files;
  - the launcher's empty lock file.
- **The copies:** each file was copied to
  `K:/Meu Drive/Pessoal/Projetos/refute/cache-archive-2026-11-26-v0512-rest/v0512/...` and
  checked by SHA-256. All 95 match, and only then was anything deleted.
- **On the Drive,** that folder now holds 97 files: the 95, the manifest `MANIFEST-sha256.json`
  and a copy of the script.

## Regenerable, deleted without archiving

| Path | Files | Bytes | Why it can be regenerated |
|---|---|---|---|
| `.cache/v0513prep/dist/` | 3 | 69,912,578 | the A4 wheel and sdist, and uv's `.gitignore`; their hashes and contents are in [../package-check-2026-11-26/](../package-check-2026-11-26/README.md) |
| `.cache/v0513prep/clean-clone/` | 23,131 | 999,656,567 | A3's clean local clone with its virtual environment; its timing is recorded on the README draft's branch |

## The emptied folders

The emptied folders were removed, deepest first: 3,458 of them, `.cache/v0512/` included.

## The guard

- **What can be deleted:** only the three roots above, by literal path, with no junction or link
  in the way. Git's read-only object files were made writable before deletion.
- **Never touched:**
  - nothing outside `.cache/`;
  - no other `.cache/` folder;
  - nothing on the Drive is deleted.

## What remains in `.cache/v0513prep/`

The working files of this round: the Codex prompts, answers and events, the generators and the
run logs. They stay until the maintainer's stop is answered, and are cleaned up afterwards by the
same rules.
