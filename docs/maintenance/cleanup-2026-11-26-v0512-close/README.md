# The cleanup of v0.5.12's working folder at the close (2026-11-26)

Asked by the maintainer's decision recorded in #218, comment 7202383280, item 6. The repetition
was approved in comment 7202817195, item 1. [cleanup.py](cleanup.py) was committed before any run
(`30cc0f2`) and is unchanged since.

**The first attempt was interrupted.** It ran as the unit `cleanup-close` with a 10 MB disk
reservation. The meter stopped it while it copied to the Drive, so nothing was deleted (deviation
17 in the report's dated correction).

**The approved repetition succeeded.** It ran as the unit `cleanup-close2` with a 500 MB
reservation, through `launch_v4.py`, and wrote [record.json](record.json) at 2026-11-26 20:34:34Z.

**Archived, then deleted.** These are files of `.cache/v0512` that fell out of use:
- the comment and commit-message drafts;
- the Codex rounds' raw events and answers;
- the JUnit files;
- the golden and tag outputs;
- the ad hoc inspection tools (`diag/`);
- the gate files, stored unchanged in `docs/gates/`;
- the site's JUnit files from the draft;
- the run folders.

1,114 files (76,240,554 bytes) were copied to
`K:/Meu Drive/Pessoal/Projetos/refute/cache-archive-2026-11-26-v0512-close`.
- The new copy overwrote the 447 partial copies of the first attempt.
- Every copy matched by SHA-256. The manifest is `MANIFEST-sha256.json` there and `record.json`
  here.
- The originals were then deleted under a guard that refuses links, junctions and anything
  outside `.cache/v0512`.

**Deleted without archiving.** These are regenerable copies of installed programs;
`docs/validation/v0.5.12/container.json` records what they were:
- `cpy/`, the container's CPython copy;
- `git/`, Git's `mingw64/bin` copy;
- `cvenv/`, the container's venv copy;
- `gitconfig` and `blob.tmp`.

That is 3,533 files (213,807,299 bytes). 1,791 emptied folders were removed.

**Nothing extra on the Drive.** The read-only lister [drive_extras.py](drive_extras.py) found
1,116 files in the Drive folder:
- the 1,114 of the manifest;
- the manifest itself;
- the copy of the script.

There are no extras and none missing. Nothing on the Drive was deleted.

**Kept, still in use:**
- `.cache/v0512/launcher.lock`;
- the run folders written from the unit's start on.

The launcher writes one run folder per later unit there.

**Branches:** no merged branch was left to delete.
- In this repository, `claude/v0-3-planning-draft-abff23`, `diag/clock-info` and
  `v04-lock-attempt-1` are not ancestors of `main`.
- In refute-site, `maint/synthetic-deps-2026-11-20` is not merged.
- `draft/status-2026-11-26-v0512` is the open pull request #14.

**Not touched, outside the project:** the AppContainer profile `refute.v0512.offline` and the
grants. Their removal is the maintainer's, with
[../../validation/v0.5.12/close/appcontainer-commands.md](../../validation/v0.5.12/close/appcontainer-commands.md).
