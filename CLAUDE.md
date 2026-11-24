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
   For advancement from 2026-11-21 on, apply the amendment below.
4. When a phase closes, update "Current phase" in ROADMAP.md and tick only the
   exit criteria met with evidence, in the same commit.

**Amendment of 2026-11-21 (the maintainer's decision, #218).** A phase may advance when the
previous phase (a) met its exit criteria, or (b) has an infeasibility record, or (c) closed with
declared limits: its failed targets are listed, its battery carries a limits label (for v0.5:
'WEAKENED; does not meet D1, D2, D4, T2a'), and every later result that uses that battery carries
the label. (c) relaxes no target and changes no verdict. This amendment was adopted with the
results of v0.5 to v0.5.5 known. *(It applies from 2026-11-21 on; the advance rule in ROADMAP.md
carries the same text.)*

**Process diet 2** (adopted 2026-11-24, #218; for phases opened after its adoption): items 3 (time
box) and 6 (gate) are in ROADMAP.md, "How phases work"; items 1, 2, 4, 5 and 7 are in "Exploratory
and confirmatory work" below.

## Core principle

**Agents propose. Deterministic tests decide.**

A claim is never "proven". It only survives, or it doesn't. No LLM output is
ever the final verdict. Verdicts come only from deterministic, versioned,
reproducible code.

**Explore freely, conclude strictly** (the maintainer's decision of 2026-11-21, #218). Exploring
may change the point of view as often as needed, under light rules; concluding keeps the full
rigour. No earlier verdict changes.

## Exploratory and confirmatory work

- **Exploratory:** quick, cheap, logged. Outputs are labelled "exploratory": they are never
  verdicts, never "candidates" in a public claim, and never submitted. Any public target may be
  looked at, with the choice and its reason logged. Codex: one round.
- **Confirmatory:** what exploration picks is confirmed only on targets or data not used to pick
  it, or prospectively, under a lock and pre-registration as below. Codex: up to three rounds.
  A blind review only for rule changes.

**Process diet** (from 2026-11-21):
- Codex: one round by default, up to three for a lock, a verdict or a rule change. Each later
  round resumes the same conversation (`codex_affinity.ps1 -Thread <id>`).
- A caps ledger only for runs above 5 CPU-h.
- Decision blocks and records stay short.
- The rules on safety, privacy, the machine, deletion and dependencies below do not change.

**Process diet 2** (adopted by the maintainer's decision of 2026-11-24, #218, comment 7122240195,
as the final text of its blind review, with the maintainer's choices N1 and N2; record:
[docs/plans/process-diet-2/](docs/plans/process-diet-2/README.md)). Items 1, 2, 4, 5 and 7 are
here; items 3 and 6 are in ROADMAP.md, "How phases work". The numbers 1 to 7 are the same in both
files. v0.5.9 keeps the rules it was opened with.

Process diet 2 (#218). Applies to phases opened after its adoption is recorded. Existing phase
authorizations and historical records remain in force. Apart from what items 1, 5 and 6 state, it
relaxes no rule of CLAUDE.md or ROADMAP.md; in doubt, the existing rule applies.

1. **Charter.** Before work starts, one charter file is committed and linked from the phase's
   ROADMAP section, and the maintainer approves it in the phase issue, citing its commit SHA. It
   fixes the question, target and data scope, resource caps (CPU-h, downloads, disk peak), exit
   criteria, reviews and stops. It may approve named reruns, each with its reason, exact procedure
   and the conditions that trigger it, written so that a record can check them. A charter adds
   stops and never removes one of item 2 or a safeguard of item 7. A change to it is a dated
   amendment, approved the same way before the work it covers, that states which results were
   known. Authorized work proceeds within that scope.
2. **Stops.** Keep all mandatory individual approvals, pre-registration checkpoints and
   phase-specific stops. The list that follows is not exhaustive. Stop before a lock or drand
   checkpoint, the approval of public text or of the phase report, a publication, a dependency
   change, or work beyond the charter. Where the charter calls for it, stop before the first
   commit in `src/`, with Codex's review of the diff attached. Decisions ready at the same time go
   in one issue comment, each with its own explicit approval. A pre-registration checkpoint is
   never merged with the step after it: that step's approval may share the comment only if it
   names the deterministic check that must pass in between, and a failed check returns the stop
   to the maintainer. Obtain any Claude review authorization with purpose, number and cost.
3. *Time box: in ROADMAP.md, "How phases work".*
4. **Exploration and reruns.** Within the charter and all applicable stops, explore on synthetic
   development data or on public data already exposed. A public target not yet exposed may be
   looked at only inside a pool the charter names; the choice and its reason are logged, and from
   then on it is exposed and unusable for confirmation. Without a higher cap in the charter,
   exploration stays within 5 CPU-h and 20 GB of downloads per phase, cumulatively; above 5 CPU-h
   the caps ledger applies. A rerun is any execution that gives a case a new value of an output it
   already has on record (a test status, class, score, door or criterion), on all or part of a
   recorded run's cases, including failed or incomplete ones, whatever the code, seed, threshold,
   input or entry mode. Every rerun needs issue approval of its reason and exact procedure before
   it runs, in the charter or later. A reviewer's read-only recount, `refute verify` and
   `refute check-dossier` are verification, not reruns. A new diagnostic may reuse exposed data
   without that approval only if (i) it yields a quantity no recorded run yielded for those
   cases, (ii) its question, quantity and cases are logged before it runs, and (iii) its result
   replaces or re-scores no recorded result and is reported beside it as exploratory and post
   hoc. In doubt, it is a rerun. The runner writes one append-only log per phase: before each
   run, the question and choices with a machine timestamp; after it, provenance, coverage and
   every outcome, including failures and abandoned attempts. The phase report links that log.
   Label outputs `exploratory` and carry applicable limits. Use findings only to generate
   hypotheses. Claims, acceptance and verdicts require locked, pre-registered confirmation on
   targets or data that are unexposed and did not inform the choices, or on prospective data; a
   claim that follows a failed or weakened one on the same question cites every earlier attempt
   in its pre-registration. No holdout, hidden window or reserved confirmation set is read before
   its own lock reveals it, whether its phase is open, paused or closed. Preserve the original
   results and stop decisions.
5. **Records.** The charter is the plan; keep one phase report. A working exploratory report (not
   approved, published, locked or hashed) is corrected in place by a commit, with a dated entry in
   one append-only errata log per phase: source commit, correction and impact. Approved,
   published, locked or hashed records, and any verdict-related correction, get a separate dated
   correction file, and the original is never edited. Track findings that affect a gate.
6. *Gate: in ROADMAP.md, "How phases work".*
7. **Safeguards.** Preserve pre-registration order, locks, hidden data, rerun approval,
   deterministic verdicts and their vocabulary, evidence for every PASS, zero coverage as
   `INCONCLUSIVE`, "results are never tuned to pass a gate", "no earlier verdict changes", the
   advance rule with its 2026-11-21 amendment, the non-negotiable rules, and all safety, privacy,
   machine, deletion and dependency rules.

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
  that manifest. From X2f on they are published for external reproduction on Zenodo, with a
  DOI ([docs/data-publication.md](docs/data-publication.md)): only synthetic data and Refute's
  own results, never data under a restricted license (TESS-EB, Gaia) or anything about a paper
  in its reply period; a license in every record; the agent prepares a **draft** only (files,
  SHA-256 manifest, metadata) and **never publishes a record** (the maintainer publishes).
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
  or a new record, never an edit. The same holds, from 2026-11-24, for
  `docs/validation/v0.5.8/zenodo/` (the published Zenodo record's files) and the
  stored plan records `docs/plans/process-diet-2/` and `docs/plans/research-2026-11-23/`.
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

   **CI in two levels** (the maintainer's decision of 2026-11-24, #218 comment 7133936093,
   item 2; `.github/workflows/ci.yml`, `scripts/ci_plan.py`):
   Codex's blocking items are applied
   ([docs/plans/ci-two-level-consensus/](docs/plans/ci-two-level-consensus/README.md)).
   - **Every push to main and every pull request starts a run.** There is no trigger-level
     path filter; the plan job is the only path classifier.
   - **The fast matrix** is the default: ubuntu-24.04 with Python 3.12.15 and windows-2025
     with Python 3.13.16, all 7 shards (14 jobs). The recorded-value tests also run on the
     two other pairs, because `docs/validation/v0.3/wp3-acceptance.md` requires them on
     every CI job.
   - **The full matrix** (the 4 pairs, 28 jobs) runs:
     - when any commit of the push or pull request touches `src/**`, `pyproject.toml`,
       `uv.lock`, `calibration/**` or `.github/workflows/**`;
     - when a push is not a fast-forward;
     - every night (schedule);
     - when a tag is created;
     - by `workflow_dispatch`.
   - **No test job** runs for a change whose every path is documentation that no test
     reads (the former `paths-ignore` list).
   - **One CI per round.** A push that exists only to prove pre-registration order (for
     example the seed before the draw) runs no test job, under these conditions:
     - its commit message has the trailer line `CI: order-proof`;
     - it is that commit alone, a fast-forward and not a merge;
     - it touches no code path.

     Its run still records the push time. The round's final push runs the tests.
     - GitHub's `[skip ci]` is **never** used for such a push. It creates no run, and the
       order proofs read the `created_at` of the commit's push run of `ci.yml`
       (`refute.selection.publication`, `push_run_created_at`).
     - Tags start CI through the `create` event, never through `push`, so a tag adds no
       second push run for a commit. Tags are created one at a time.
   - **Test evidence is `scripts/ci_evidence.py <sha> --level full|fast`, never a run's
     green status:** a documentation-only or order-proof run is green with no test job.
     - A rule that requires green CI before a lock, a tag, a release, a dependency change or
       an acceptance that names four green jobs requires `--level full` on that exact commit,
       before the gated step.
     - If that commit's run was fast, the full matrix is started with `workflow_dispatch`
       while the commit is the tip of `main`, and the run's `head_sha` is checked.
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

   **The session does not wait for CI to stop** (the maintainer's decision of 2026-11-24,
   #218 comment 7136727624, item 1).
   - At each stop it gives the link of the last CI run and its state at that moment.
   - A failure becomes a fix in the next round ("fix forward").
   - **The exception:** locks, tags, releases, acceptances and dependency changes still require
     `scripts/ci_evidence.py <sha> --level full` to pass on the exact commit **before** the step.

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
  `calibration/*/audit/` and `docs/validation/v0.2.1/pre-document-runs/`,
  published dossiers, and the frozen inputs under `.cache/frozen/` (v0.5, #196:
  inputs of locked claims, each in a folder named after its SHA-256).
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
- **Already integrated or incorporated** (the maintainer's decision of 2026-11-24, #218
  comment 7139692729, item 4): discarded like what is no longer used, by the rules above. It
  is archived first if it has value, and deleted outside `.cache/` only with the maintainer's
  approval.
  - **Merged branches:** a branch already merged into `main` may be deleted without a new
    approval, once checked that it is merged: its tip is an ancestor of `main`
    (`git merge-base --is-ancestor <branch> main`).
  - **Not covered:** a branch that is not merged stays under the rule of "GitHub operations".
- **How:** deletion only by full literal path, with a guard that the path is inside the
  project folder; never from a broad root and never with `git clean -x`. A deletion
  outside `.cache/` still needs the maintainer's approval (see "Working mode
  (v0.3)"). Nothing outside the project folder is ever deleted, and the forbidden
  deletion roots of the operating rules above stay forbidden.
- At the end of each work package, the agent reports what fell out of use and archives
  or deletes it by these rules.
