# Contributing to Refute

Thank you for helping. Refute exists to attack claims, so contributions that
find weaknesses in Refute itself are as welcome as new features.

## Ground rules

- Read [ROADMAP.md](ROADMAP.md) first. Work only on the **current phase**.
  Pull requests that build future-phase features will be asked to wait.
- **Agents propose, deterministic tests decide.** No LLM output may ever be a
  verdict. Verdicts come only from deterministic, versioned code.
- **Never invent scientific facts.** Target IDs, periods and published
  parameters must come from an authoritative source (NASA Exoplanet Archive,
  ExoFOP, MAST), with the source and retrieval date recorded.
- **Never tune results to pass.** Thresholds in a locked claim are never changed
  after seeing the data. A failed pre-registered claim is reported, not hidden.
- Verdicts are about claims, never about authors.
- Out of scope: medical or diagnostic claims, dual-use biology or chemistry.
- Everything is written in English: code, comments, docs, commit messages.

## Development setup

Refute uses [uv](https://docs.astral.sh/uv/) and Python 3.12 or newer.

```bash
uv sync
uv run pre-commit install
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

## Tests never touch the network

`pytest` runs with `--disable-socket` (pytest-socket), so any test that tries to
open a network connection fails. Tests use synthetic light curves with injected
transits and eclipsing binaries (`refute.packs.tess.synthetic`). Real data is
only used by the CLI (`refute fetch`, `refute calibrate`), never by the test
suite or CI.

Every new falsification test needs at least one synthetic case that passes and
one that fails.

## CPU-heavy work

Analyses run in parallel with `ProcessPoolExecutor`. The default worker count is
`os.cpu_count() - 2`, configurable with `--workers`. Worker functions must be
top-level and take picklable arguments, because Windows uses the spawn start
method.

## Writing a domain pack

The engine knows nothing about any science. A pack is a Python package that
exposes a `DomainPack` object through the `refute.packs` entry-point group:

```toml
[project.entry-points."refute.packs"]
mypack = "my_package.refute_pack:PACK"
```

A pack provides a data adapter, a search, a gauntlet, a holdout strategy and an
exporter, plus pydantic models that validate its part of `claim.yaml`. See
`src/refute/core/pack.py` for the interface and `src/refute/packs/tess/` for a
complete example. Packs can live in their own repositories.

## Locks and the code hash

`refute lock` hashes the claim, its attachments **and** the source tree
(`src/`, `pyproject.toml`, `uv.lock`). Any code change after a claim is locked
makes `refute verify` report `TAMPERED`. Re-locking requires `--force` with a
`--reason`, and is recorded in the append-only `LOCK_HISTORY.md` next to the
claim. Calibration claims can only be locked from a clean, committed git tree.
See [docs/lock-format.md](docs/lock-format.md).

## Pull requests

- Keep pull requests focused. Include tests.
- `ruff check`, `ruff format --check` and `pytest` must pass.
- Do not commit data caches (`.cache/`) or run outputs (`dossiers/`).
- By contributing you agree that your contribution is licensed under
  Apache-2.0.
