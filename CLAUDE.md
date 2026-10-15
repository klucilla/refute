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
Paper claims: `REPRODUCED`, `FRAGILE`, `NOT_REPRODUCED`, `NOT_REPRODUCIBLE`,
`INCONCLUSIVE` (Refute could not decide for reasons on its side, such as an
exhausted budget or the hang guard; never a failure of the artifact).
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
- No check may PASS without evidence that it examined data. Every TestResult
  reports its coverage; zero coverage is INCONCLUSIVE, never PASS. This applies
  to every domain pack.

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
- Never end a process by name or by a pattern (`taskkill /IM`, `pkill`,
  `killall`, `Stop-Process -Name`, or any filter that can match other
  processes). End only a process that this session started, by the PID
  recorded when it was started. Other sessions and programs run Python on
  the same machine.
- Always run Python from the project's virtual environment, by its path
  (`.venv/Scripts/python.exe` on Windows, `.venv/bin/python` elsewhere) or
  through `uv run`; never a bare `python`, `python3` or `py`. On Windows a
  bare `python` may be the Microsoft Store alias, which hangs.
- Test counts (passed, failed, errors, skipped) are reported from a JUnit
  XML file (`pytest --junitxml=<path>`), never from the progress markers or
  the console summary line.
- `calibration/*/audit/` and `docs/validation/v0.2.1/pre-document-runs/` hold
  published records (scripts, outputs, transcript extracts) whose bytes are cited
  by SHA-256. Never edit, reformat or normalize line endings there; linters and
  pre-commit hooks exclude these folders on purpose. A correction is a new file
  or a new record, never an edit.
- Never print webhook or secret configuration (for example
  `gh api repos/.../hooks` without a filter): its URLs can contain tokens. Use a
  `--jq` filter that leaves out `config`.

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

### Standing approval (v0.3)

The maintainer gave this standing approval in chat on 2026-10-14 and extended it on
2026-10-15, for phase v0.3. It replaces the per-action approval above only for what it
lists.

- **Allowed without asking each time:**
  - commits, pushes and pull requests for the work the maintainer assigned;
  - merging a pull request that contains only acceptance documents, WP1 documents
    other than README, or code with synthetic tests;
  - recording minor follow-ups in the "v0.3 follow-ups" issue (#59). Recording an
    item does not authorize implementing it.
- **Conditions for that merge:**
  - a merge commit, pinned to the head that was checked;
  - CI green, or skipped as expected by the paths-ignore list;
  - every acceptance criterion checked one by one in the pull request;
  - the Codex review resolved, with question, answer, verdict and reason recorded in
    the pull request.
- **After every merge:** the agent checks the CI run of the merge commit on main until
  its final result. If it fails, the agent stops and tells the maintainer. When the
  paths-ignore list skips the run (documentation only), the agent records that no run
  was expected; a run missing for any other reason is treated as a failure.
- **Never under the standing approval:**
  - README, the site or any other public communication about the project; the
    acceptance and WP1 documents listed above are the only documentation it covers;
  - locks, drand rounds, and any change to a lock, a locked hash or a published
    dossier;
  - any change to the claim schema, claim serialization or canonicalization, the
    lock format or lock verification, or to acceptance criteria; these need the
    maintainer's explicit approval, also when the pull request is otherwise in scope;
  - running third-party code, and the VM;
  - sending email;
  - changes to `ci.yml` that loosen checks;
  - deletions outside `.cache/`.
- The items that are always asked individually (list above) stay so.

## Tech standards

- Python 3.12+, `pyproject.toml`, `uv` as package manager.
- CLI with `typer`. Config and claims in YAML.
- Science stack: `numpy`, `astropy` (BoxLeastSquares), `lightkurve` (TESS data
  via MAST), `matplotlib`.
- Tests with `pytest`. Lint/format with `ruff`. CI on GitHub Actions.
- Everything in English: code, comments, docs, commit messages.
- License: Apache-2.0.

## Project folder hygiene

Only files in use, or planned for use in an open task, stay in the project folder
(C:\Projetos\refute).

- **Never deleted by this rule:** tracked files, the published records of
  `calibration/*/audit/` and `docs/validation/v0.2.1/pre-document-runs/`, and
  published dossiers.
- **Still in use, or planned for use in an open task:** kept. This includes the
  project's main virtual environment and the environments of analyses or fixes in
  progress. When in doubt, keep it and ask the maintainer.
- **No longer used, with value** (results, scripts, logs, published texts): archived
  to `K:\Meu Drive\Pessoal\Projetos\refute\<new subfolder>` with a saved script and a
  SHA-256 manifest of source and destination, checked; only then deleted from the
  project folder.
- **Regenerable, no longer used and with nothing worth keeping** (caches of finished
  runs, worktrees and virtual environments of finished investigations, old builds,
  unused downloads; anything with value is archived first, as above): deleted
  without archiving; inside `.cache/` without a prior approval round. Every deleted
  path is listed in the report of that round.
- **How:** deletion only by full literal path, with a guard that the path is inside the
  project folder; never from a broad root and never with `git clean -x`. A deletion
  outside `.cache/` still needs the maintainer's approval (see "Standing approval
  (v0.3)"). Nothing outside the project folder is ever deleted, and the forbidden
  deletion roots of the operating rules above stay forbidden.
- At the end of each work package, the agent reports what fell out of use and archives
  or deletes it by these rules.
