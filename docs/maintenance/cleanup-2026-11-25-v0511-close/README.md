# The cleanup of v0.5.11's working folder at the close (2026-11-25)

This cleanup was asked by the maintainer's decision received on 2026-11-25 at 11:53 local (#218,
comment 7165994585), item 4. [cleanup.py](cleanup.py) ran once as the metered unit
`cleanup-close` (launch_v9), committed before the run (`1b83afe`), and wrote
[record.json](record.json).

**What was deleted:** everything under `.cache/v0511` that fell out of use when the phase closed:
- the Codex rounds' raw events;
- the JUnit files;
- the golden outputs;
- the tag verification;
- the downloaded papers;
- the comment and commit-message drafts;
- the ad hoc inspection tools;
- the run outputs;
- the site test logs and JUnit files;
- the gate files, which are stored unchanged in `docs/gates/`.

**How:**
- 504 files (16,021,246 bytes) were copied to
  `K:/Meu Drive/Pessoal/Projetos/refute/cache-archive-2026-11-25-v0511-close`, and every copy
  matched by SHA-256. The manifest is `MANIFEST-sha256.json` there and `record.json` here.
- The files were then deleted under a guard that refuses links and junctions, and the emptied
  folders were removed.

**Kept, still in use:**
- `.cache/v0511/launcher.lock`;
- the unit's own run folder under `.cache/v0511/runs/`.

The launcher writes one run folder per later unit there, the closing commit's among them.
Nothing outside `.cache` was deleted.

**Branches:** no merged branch was left to delete.
- In this repository, `claude/v0-3-planning-draft-abff23`, `diag/clock-info` and
  `v04-lock-attempt-1` are not ancestors of `main`, so they stay under the rule of "GitHub
  operations".
- In refute-site, `maint/synthetic-deps-2026-11-20` is not merged either.
