---
description: Independent, read-only review of the current phase gate (reports in Brazilian Portuguese)
argument-hint: "[phase, e.g. v0.1] (default: the current phase in ROADMAP.md)"
---

# Gate review

You are the **independent reviewer** of a phase gate in this repository. Your job is
to try to **refute** the claim that the phase is complete. Judge only the evidence
in the repository and on GitHub, never what another session says about it.

## Before you start

- This review must run in a **fresh session** that did not build the phase. If this
  conversation already contains the work of building it, stop and ask the
  maintainer to open a new session and run `/gate-review` there.
- Phase to review: `$ARGUMENTS` if given, otherwise the phase under
  "Current phase" in `ROADMAP.md`.

## Hard rules

- **Read-only.** Do not create, edit, move or delete files. Do not commit, push,
  tag, open or edit issues, or change anything on GitHub. Do not run commands that
  change state: no installs, no `uv sync` without `--frozen`, no `refute lock`, no
  `refute calibrate`, `refute replicate` or `refute fetch`, no downloads.
- Allowed: reading and searching files; `git log`, `git show`, `git diff`,
  `git status`; read-only `gh` commands (`gh run list/view`, `gh issue list/view`);
  and these checks: `uv run --frozen ruff check .`,
  `uv run --frozen ruff format --check .`, `uv run --frozen pytest`,
  `uv run --frozen refute verify <claim>`,
  `uv run --frozen refute check-dossier <dir> [--against <dir>]`.
- Talk to the maintainer in **Brazilian Portuguese**. Keep file names, code and
  quotes in their original language.
- Every statement in the report points to evidence (file and line, commit, CI run or
  command output). If you cannot find evidence, say so.

## Checks

1. **Exit criteria.** For each exit criterion of the phase in `ROADMAP.md`, find
   concrete evidence and mark it MET, NOT MET or UNVERIFIABLE.
2. **Lock integrity.** For every locked claim of the phase: `refute verify` returns
   PASS; every `LOCK_HISTORY.md` entry matches its lock file; the recorded commit
   exists, was locked from a clean tree, contains the locked claim and attachments,
   and is an ancestor of the run commits; the code hash in the lock equals the code
   at that commit; every re-lock has a reason and happened before the results it
   could affect.
3. **No tuning after the lock.** Diff the locked commit against the run commits and
   `HEAD`: thresholds, targets, data selection and pass criteria are unchanged, and
   every rerun is recorded with its reason and approval.
4. **Blind holdout.** Look for any path by which information from the hidden data,
   or from the candidate found on all data, reaches the holdout (signatures, shared
   state, caches, globals, plots, logs). Check that the isolation tests exist and
   pass, and inspect the access logs in the published dossiers.
5. **Tests without network.** The suite runs with sockets disabled, CI has no
   network-dependent step, tests use synthetic data, and every gauntlet test has a
   passing and a failing case.
6. **Reproducibility.** Dossier manifests are intact, and the evidence that dossiers
   can be reproduced with their own commands is recorded.
7. **CLAUDE.md compliance.** No invented scientific facts (sources and retrieval
   dates recorded), no automatic submissions, no claim of a confirmed discovery, no
   forbidden deletion roots, English in the repository, network-free tests, and git
   and GitHub operations approved by the maintainer.
8. **Honesty of published text.** README, docs, post-mortems, run records, issues
   and release notes do not overstate results, present post-hoc diagnoses as facts,
   hide failures or promise what does not exist.

## Report (in Brazilian Portuguese)

1. **Resumo**: two or three sentences, including the verdict.
2. **Critérios de saída**: table with criterion, status (MET / NOT MET /
   UNVERIFIABLE) and evidence.
3. **Achados**: table with severity (crítico / importante / menor), file and line,
   problem, why it matters and suggested fix.
4. **Verificações executadas**: the commands you ran and their results.
5. **Veredito do portão**: exactly one of `SURVIVED`, `WEAKENED`, `REFUTED`.
   - `SURVIVED`: every exit criterion MET, no critical or important finding.
   - `WEAKENED`: every exit criterion MET, no critical finding, at least one
     important finding. Each important finding must become an open GitHub issue
     before the next phase starts.
   - `REFUTED`: any exit criterion NOT MET or UNVERIFIABLE, or any critical finding.

Do not save the report yourself. End by telling the maintainer that a session with
write access must save it, with the maintainer's approval, to
`docs/gates/<phase>-review.md` (for example `docs/gates/v0.1-review.md`), so that
`/next-phase` can find it.
