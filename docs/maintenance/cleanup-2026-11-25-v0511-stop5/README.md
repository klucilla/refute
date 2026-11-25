# The cleanup of v0.5.11's fifth stop (2026-11-25)

This cleanup was asked by the maintainer's decision received on 2026-11-25 at 08:47 local (#218,
comment 7161509920), item 4. [cleanup.py](cleanup.py) ran once as the metered unit
`cleanup-stop5` (launch_v9) and wrote [record.json](record.json).

**What was deleted** (all under `.cache/v0511`, by literal path):
- the screen module's draft, `draft/screen_d5.py`, which is in `src/` since `a896c49`;
- nine intermediate diffs of the hash checks under `step2/`. The reviewed, the adjusted and the
  E1 diffs are committed under `docs/validation/v0.5.11/step2/`;
- `ci-rest-windows.log`, the downloaded log of CI run 45514526728, summarized in the report (F-1)
  and the errata.

**How:**
- 11 files (1,403,899 bytes) were copied to
  `K:/Meu Drive/Pessoal/Projetos/refute/cache-archive-2026-11-25-v0511-stop5`, and every copy
  matched by SHA-256.
- The files were then deleted under a guard that refuses links and junctions, and the emptied
  `draft/` folder was removed.

Still in use, and kept: the phase's `codex/`, `runs/`, `junit/`, `golden/`, `tag-verify/`,
`papers/`, `msg/` and `tools/` folders. Nothing outside `.cache` was deleted.
