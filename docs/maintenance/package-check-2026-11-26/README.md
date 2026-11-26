# Installable package: a check only (2026-11-26)

The maintainer's decision of 2026-11-26, item A4 (#218, comment 7203695669): build the wheel and
the sdist in a `.cache` directory without changing dependencies, record their content and size,
and check, read only, whether the name `refute` is free on PyPI and TestPyPI. **Nothing was
published.** Publishing is the maintainer's decision.

## What ran

- `build_check.py` is a byte copy of the script that ran, as `.cache/v0513prep/a4_build.py`
  (its paths are relative to that location), launched through `scripts/launch_affinity.ps1`
  (threads 8 to 31; PID 18388; exit 0).
- It ran `uv build --offline --out-dir .cache/v0513prep/dist` (uv 0.12.24, hatchling from the
  local uv cache, no network) at `02b6ddf` plus this round's uncommitted documentation files.
- `pyproject.toml` and `uv.lock` have the same SHA-256 before and after (`463546f8…` and
  `767bbb38…`): the build needed no change to them or to any dependency.
- The full record is `build-check.json` (exit code, hashes, per-folder counts and sizes, the
  largest members).

## The wheel: `refute-0.5.0-py3-none-any.whl`

- **632,042 bytes** (1,970,600 uncompressed), 131 members, SHA-256 `c7397206…f38588`.
- Content: only `refute/` (126 files: `core` 24, `packs` 93, `selection` 6, `cli.py`,
  `drand.py`, `__init__.py`) and `refute-0.5.0.dist-info/` (5 files). No data file and no file
  outside `src/refute`: it meets "only `src/refute` and small data".
- The largest member is `refute-0.5.0.dist-info/METADATA` after five modules (49,786 bytes): it
  embeds the whole `README.md` as the long description.

## The sdist: `refute-0.5.0.tar.gz`

- **69,280,535 bytes** (383,835,301 uncompressed), 5,109 files, SHA-256 `88f4d11f…857bb6`.
- **Finding: it holds the whole repository**, because `pyproject.toml` sets only
  `[tool.hatch.build.targets.wheel]` and hatchling's default sdist takes every file not excluded
  by `.gitignore`: `docs/validation/` (3,519 files, 314 MB uncompressed, its largest file 47.8 MB),
  `docs/maintenance/`, `docs/plans/`, `calibration/`, `tests/`, `scripts/vm/`, `uv.lock`,
  `CLAUDE.md` and `.claude/`.
- **It also takes local files that git ignores only through `.git/info/exclude`** (hatchling
  reads `.gitignore`, not that file): here `.claude/scheduled_tasks.lock`, a session lock that is
  not tracked.
- A smaller sdist needs a `[tool.hatch.build.targets.sdist]` include list in `pyproject.toml`.
  That is a change to `pyproject.toml`, which is part of the code hash, so it is the maintainer's
  decision and is **not** made here.

## The name on PyPI and TestPyPI

Read only, on 2026-11-26 at 21:29Z (HTTP status of each URL; no account, no upload):

| URL | Status |
|---|---|
| https://pypi.org/pypi/refute/json | 404 |
| https://pypi.org/simple/refute/ | 404 |
| https://test.pypi.org/pypi/refute/json | 404 |
| https://test.pypi.org/simple/refute/ | 404 |

A 404 means that no project was registered under that name on that date. It does not
guarantee that an upload would be accepted: PyPI can still refuse a name at upload (for example
one too similar to an existing project, or a reserved one), and that cannot be checked without
an upload.

Alternatives checked the same way, all 404 on both indexes: `refute-science`,
`refute-framework`, `refute-tess`, `refuter`, `refutation`.

## Cleanup

The built files in `.cache/v0513prep/dist` are deleted by item A6 of the same decision; this
record keeps their hashes and content.
