---
description: Check that the previous phase gate passed, then plan only the current phase (talks in Brazilian Portuguese)
---

# Next phase

Talk to the maintainer in **Brazilian Portuguese**. Everything written to the
repository stays in English. This command does not change files, git or GitHub.

## Step 1: find where the project stands

1. Read `CLAUDE.md`, `ROADMAP.md` and `README.md`.
2. Note the phase under "Current phase" in `ROADMAP.md` (call it C) and the phase
   listed right before it (call it P).

## Step 2: check the gate

Look for gate reviews in `docs/gates/`.

- **`docs/gates/<C>-review.md` exists with a passing verdict.** Phase C was
  reviewed but not yet closed in `ROADMAP.md`. Do not plan. Propose, for approval,
  the closing change that `CLAUDE.md` requires: tick C's exit criteria with links to
  the evidence and move "Current phase" to the next phase, in one commit. Then stop.
- **`docs/gates/<P>-review.md` exists.** The gate passed only if:
  - its verdict is `SURVIVED`, or `WEAKENED` with every important finding linked to
    a GitHub issue that is open, or closed by a fix (check with `gh issue view`);
  - every exit criterion of P is ticked in `ROADMAP.md`.
- **Anything else** (no review, verdict `REFUTED`, findings without issues, unticked
  criteria): **stop**. Explain exactly what is missing and what the maintainer needs
  to run or approve, usually `/gate-review` in a fresh session. Do not plan.

## Step 3: plan only the current phase

1. Plan **only** phase C. Never pull in work from future phases.
2. Read P's post-mortem, gate review and open issues. List which of them this phase
   addresses and which it leaves for later.
3. If the phase includes a new pre-registered claim:
   - targets used in earlier calibrations are a **known set** and cannot be used to
     validate fixes or new tests;
   - a new seeded selection, with a **new seed**, is defined and locked before any
     analysis of the new targets;
   - thresholds are fixed on synthetic data before any real target is analyzed.
4. List every checkpoint that needs the maintainer's approval: commits, pushes,
   locks, runs, issues and releases.
5. Ask clarifying questions only when a decision is genuinely the maintainer's.

## Step 4: wait

Present the plan and **wait for explicit approval**. Do not implement anything
before that.
