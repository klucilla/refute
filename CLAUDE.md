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
   rest and checked at predicted windows. In a round that reaches the measurement, the
   hidden year is detrended once before any logged read, each window masked out to the
   inner edge of its baseline band (its
   clipping can drop hidden cadences); after that, only the predicted windows, their
   baseline bands and the control windows are read, and every read is logged.
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
  16 cores / 32 threads). Default worker count: the CPUs allowed by the
  process's affinity mask, minus 2 (`refute.core.runner.default_workers`),
  configurable. Use `ProcessPoolExecutor` or equivalent.
- Always deliver complete files, never partial snippets.
- Data cache lives inside the project (`.cache/`, git-ignored).
- Raw outputs larger than 5 MB never enter git (decided by the maintainer on 2026-10-24,
  before X2f): they are archived to the Drive with a SHA-256 manifest of source and
  destination, checked; the repository keeps the script that produced them, a summary and
  that manifest. Where the raw outputs are published for external reproduction is the
  maintainer's decision.
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
- Every legal or license statement written to the repository (README, protocols,
  data-license files, release notes) gives the source URL, the retrieval date and a
  short literal excerpt stored in the repository, in a `sources/` record next to the
  statement, so that it can be checked later even if the page changes. A statement
  that cannot be sourced is marked as unconfirmed, or is not made. This applies to
  new statements from the adoption of this rule on (issue #34).

## Communication

- Always talk to the maintainer in Brazilian Portuguese.
- Everything written to the repository (code, comments, docs, commit
  messages, issues, release notes) is in English.

## GitHub operations

- The agent has GitHub access. Which git and GitHub operations need the maintainer is
  decided by the working mode below ("Working mode (v0.3)"), decided by the maintainer on
  2026-10-17. It replaces the per-action approval and the standing approval of 2026-10-14
  and 2026-10-15.
- Always asked individually: force push, history rewrite, deleting a branch (except those
  the maintainer approves), changing repository visibility, deleting releases or the
  repository.
- Pre-registration checkpoints (lock before calibrate) still require an explicit stop and
  approval at each step.

### Working mode (v0.3)

Decided by the maintainer on 2026-10-17. It replaces the earlier rules of pull requests
and review (the standing approval of 2026-10-14 and 2026-10-15).

1. **Do, decide, go on.** Changes to code, tests, scripts, configuration and documentation
   go as **direct commits to main** (the branch `main` and the full SHA checked before and
   after), with no pull request and no wait for CI. Before each commit: ruff exits 0, and
   the affected tests pass through `scripts/run_tests_affinity.ps1` (not the whole suite,
   unless the change is broad). Corrections are batched into **one push per batch**, never
   one push per correction: each push triggers CI. CI on main runs by itself; if it turns
   red, fix forward and go on with the rest.
2. **Codex** (read only, sandbox read-only, CPU affinity 8 to 31) is consulted on design
   and security decisions; the two reach a verdict and go on. At the end of each round,
   **one** Codex review of all the round's commits; its findings become a direct fix or an
   item of #59. Decisions the maintainer already took are not reopened with Codex; it only
   checks their implementation.
3. **Ask the maintainer only before:**
   - running third-party code for the first time;
   - creating or changing locks, drand rounds or published dossiers;
   - publishing or changing public text (the root README, the site, a release, a new public
     announcement issue);
   - deleting anything outside `.cache/`;
   - a force push, a history rewrite, or deleting a branch (except those the maintainer
     approves);
   - any step as Administrator or in Hyper-V; on a VM, changing the sudoers or the proxy's
     configuration, or any interactive sudo; and the console answers of an installation
     ("yes" to the autoinstall). The maintainer runs these; the agent prepares the exact
     commands, in plain text, one line per command, with what to check.

   Since 2026-10-17 (the maintainer's decision), the agent runs itself, from the
   maintainer's machine and without Administrator: the endpoint's operations in an
   ordinary window (`-Status`, and each operation simulated before it is run with the
   simulated plan), network checks, and SSH to the VMs with the checked host keys. Endpoint
   steps are delivered in a form a script can run (for example
   `.cache\vm\refute-step.ps1 -Op <operation> -Args1 '<arguments>' -Mode Sim|Run`).

   Since 2026-10-18 (the maintainer's decision), the agent itself executes every step on
   the VM through the JEA endpoint and by SSH, without elevation, and never hands such a
   step to the maintainer; steps as Administrator or in Hyper-V stay with the maintainer.
   The commands the VM's sudoers already allows without a password (`sudo -n`), inside
   approved scripts (`scripts/vm/launch-paper.sh`, the stop of a paper by `systemctl`), stay
   with the agent.

   Everything else, the agent decides and does.
4. Free research on the internet; an external fact in a document carries its URL and the
   date it was read.
5. Claude subagents of any kind need the maintainer's approval first (purpose, number and
   cost). The "second agent" is Codex.
6. Cleanup only inside the project folder, by literal path with a prefix guard; anything of
   value is archived to the Drive first (a script and a checked SHA-256 manifest). The
   forbidden deletion roots of the operating rules above stay forbidden. Private keys and
   keyrings never enter generic archiving and are never deleted automatically.
7. CI waits, when there are any, run in the background with a time limit. A **short**
   status summary at the end of each round.

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
  outside `.cache/` still needs the maintainer's approval (see "Working mode
  (v0.3)"). Nothing outside the project folder is ever deleted, and the forbidden
  deletion roots of the operating rules above stay forbidden.
- At the end of each work package, the agent reports what fell out of use and archives
  or deletes it by these rules.
