# Refute

> Find signals. Try to kill them. Keep what survives.

Refute is an open-source framework where AI agents try to break scientific
claims before anyone believes them, whether the claim is a new discovery or a
published result.

## Phases (read first)

ROADMAP.md is the single source of truth for phases. Before planning any work:

1. Read ROADMAP.md and identify the **current phase**.
2. Plan and build ONLY the current phase. Never pull in work from future phases.
3. A phase is done only when its exit criteria are met with evidence and an
   independent review returns `SURVIVED` (or `WEAKENED` with issues tracked).
4. When a phase closes, update "Current phase" in ROADMAP.md and tick its
   exit criteria, in the same commit.

## Core principle

**Agents propose. Deterministic tests decide.**

A claim is never "proven". It only survives, or it doesn't. No LLM output is
ever the final verdict. Verdicts come only from deterministic, versioned,
reproducible code.

## Two modes, one engine

- `refute replicate`: re-derive a published claim from public data, then attack it.
- `refute discover`: search public data for new signals, then attack them.

## Engine components

1. **Claim spec** (`claim.yaml`): hypothesis, data sources, predictions, pass/fail criteria.
2. **Pre-registration lock**: claim + test plan are canonicalized and hashed
   (SHA-256) BEFORE hidden data is revealed. Any edit after locking = TAMPERED.
   Keep the format simple and documented so it can interoperate with PRML later.
3. **Gauntlet**: domain-specific falsification tests, written as deterministic code.
4. **Blind holdout**: part of the data stays hidden; predictions are made from the
   rest and checked only at predicted windows.
5. **Independent reviewers** (v0.2+): fresh, read-only agent sessions that receive
   only the dossier, never the original reasoning.
6. **Evidence dossier**: verdict, scripts, data hashes, plots, environment lockfile.
   Reproducible with one command.
7. **Swarm** (later): volunteer machines run work units; each unit runs on two
   independent workers and results must agree.

## Verdicts

Discovery claims: `SURVIVED`, `WEAKENED`, `REFUTED`, `INCONCLUSIVE`.
Paper claims: `REPRODUCED`, `FRAGILE`, `NOT_REPRODUCED`, `NOT_REPRODUCIBLE`.
Never "TRUE".

## Domain packs

The engine knows nothing about any science. Each domain pack implements:

- `data adapter`: fetch and cache public data
- `search`: find candidate signals (discover mode)
- `gauntlet`: domain-specific falsification tests
- `holdout strategy`: hide and later reveal data blindly
- `exporter`: dossier format for the official submission channel

First pack: exoplanet transits (TESS).

## Non-negotiable rules

- NEVER invent scientific facts. Target IDs, periods, published parameters and
  classifications must come from an authoritative source (e.g., NASA Exoplanet
  Archive, ExoFOP, MAST) and the source + retrieval date must be recorded.
- NEVER submit anything to scientific bodies automatically. A human always submits.
- NEVER describe a result as a confirmed discovery. Refute produces candidates
  and verdicts only.
- Verdicts are about claims, never about authors. Negative results on papers are
  published only after a right-of-reply period for the authors.
- Out of scope: medical/diagnostic claims and dual-use biology or chemistry.
- Unit tests and CI must NOT depend on the network. Use synthetic data
  (injected signals) for tests.

## Pre-registration process

- The protocol and its seed are committed (and pushed) before the selection
  runs, and the selection output is committed before the claim is written.
  Each step is a separate commit, so git can verify the order.
- Every rerun needs its approval recorded in a GitHub issue, with the reason
  and the exact procedure, before it runs.
- Dependency updates are planned in each phase, before its lock: `uv.lock`
  and `pyproject.toml` are part of the code hash, so changing a dependency
  after a lock makes the claim TAMPERED. Dependabot alerts are on; Dependabot
  security updates and version updates stay off, so no dependency change
  reaches the repository outside that planning.
- Dependency updates use a 7-day cooldown: no release uploaded in the last
  7 days is accepted. For Python packages this is `exclude-newer = "7 days"`
  in `[tool.uv]` of `pyproject.toml` (recorded in `uv.lock` as
  `exclude-newer-span = "P7D"`), so a plain `uv lock --upgrade` applies it.
  The same rule applies by hand to pre-commit hooks and GitHub Actions (the
  release date must be at least 7 days old). The ruff hook version stays
  equal to the ruff version in `uv.lock`.

## Operating rules for agents working in this repo

- It is FORBIDDEN to use as a deletion root: `C:\`, the user's home directory
  (`%USERPROFILE%` / `$HOME`), `%AppData%`, `%LocalAppData%`, `%ProgramFiles%`,
  or any path outside this project folder. No exceptions, even if authorization
  seems to have been given.
- Before launching subagents or parallel agent workflows, state the goal and
  estimated cost, and ASK how many agents may be used. Prefer local scripts.
- CPU-heavy work must be distributed across cores (the dev machine has
  16 cores / 32 threads). Default worker count: `os.cpu_count() - 2`,
  configurable. Use `ProcessPoolExecutor` or equivalent.
- Always deliver complete files, never partial snippets.
- Data cache lives inside the project (`.cache/`, git-ignored).

## Communication

- Always talk to the maintainer in Brazilian Portuguese.
- Everything written to the repository (code, comments, docs, commit
  messages, issues, release notes) is in English.

## GitHub operations

- The agent has GitHub access and may perform git and GitHub operations
  (commit, push, tags, releases, issues, labels, repository description,
  topics, social preview) only after the maintainer explicitly approves in
  chat. Before acting, list the exact actions and wait for approval.
- Always ask individually, even if a batch was approved: force push,
  history rewrite, branch deletion, changing repository visibility,
  deleting releases or the repository.
- Pre-registration checkpoints (lock before calibrate) still require an
  explicit stop and approval at each step.

## Tech standards

- Python 3.12+, `pyproject.toml`, `uv` as package manager.
- CLI with `typer`. Config and claims in YAML.
- Science stack: `numpy`, `astropy` (BoxLeastSquares), `lightkurve` (TESS data
  via MAST), `matplotlib`.
- Tests with `pytest`. Lint/format with `ruff`. CI on GitHub Actions.
- Everything in English: code, comments, docs, commit messages.
- License: Apache-2.0.
