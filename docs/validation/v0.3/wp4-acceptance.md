# WP4 acceptance: synthetic toy papers (CI offline)

Line numbers refer to docs/plans/v0.3-plan.md at commit 8456780.

Work package WP4 of [docs/plans/v0.3-plan.md](../../plans/v0.3-plan.md) (section 11,
line 883). Issue #47. Holds the controlled test of the first exit criterion (plan
lines 47-50). Committed **before** the tests and code of the package (plan lines
871-875).

## 1. What the package must do

- **W4.1** A set of synthetic "papers": small local repositories with injected
  effects. They use numpy only, run in seconds, need no network, and contain no
  third-party code. Each one has a claim file and the expected result, fixed before
  its first run.
- **W4.2** They run end to end through the WP2 core and the WP3 pack, with the
  `subprocess` backend, in CI.
- **W4.3** The set covers:
  - **one paper per verdict path:** `REPRODUCED`, `FRAGILE`, `NOT_REPRODUCED`,
    `NOT_REPRODUCIBLE` and `INCONCLUSIVE`;
  - **the controlled `NOT_REPRODUCIBLE`** (exit criterion, plan lines 47-50): an
    artifact built to be non-reproducible, whose documented procedure fails on every
    rung of the build ladder, with complete attempts;
  - **its twin**, where the failure comes from Refute's side (an exhausted budget, an
    interruption), which must be `INCONCLUSIVE`;
  - **one paper per coverage case of #15:** zero claims, zero tests collected, an empty
    split, a metric on zero examples, nothing to compare;
  - **seed-fragile:** the predicate fails on 2 of 5 seeds;
  - **split-fragile:** the predicate fails on 1 of 3 re-splits;
  - **leaky:** duplicates between train and test above the fixed fraction;
  - **metric bug:** the printed value differs from the recomputed one beyond rounding;
  - **budget exhaustion** at setup, during the base reproduction, and during the
    attacks;
  - **an interrupted attack next to a valid failure** (must stay `FRAGILE`);
  - **n_attack = 0.**
- **W4.4** For each paper, the full verdict is checked:
  - the claim verdict;
  - the reason;
  - the status flags;
  - the claim profile;
  - the accounting record;
  - the seal of the experimental core, and the dossier verification (recomputing the
    profile from recorded outputs gives the same profile).
- **W4.5** The experimental reproduction (plan lines 815-829) runs on the controlled
  cases: each synthetic paper runs twice, and both runs give the same claim profile.

## 2. Synthetic cases

The set above is itself the list of cases. Each paper is a case that **must** give its
expected verdict.

Must-fail checks:
- the `NOT_REPRODUCIBLE` twin must not be `NOT_REPRODUCIBLE`;
- the interrupted-attack paper must not be `INCONCLUSIVE`;
- the coverage papers must not be `REPRODUCED`.

## 3. Metrics and evidence

- Test counts come from a JUnit XML file.
- CI is green on the four jobs.
- The CI time per job stays within the maintainer's target of 15 minutes; the WP4
  cases add seconds, not minutes.
- The PR lists each case of W4.3 with its test.

## 4. Regression cases

- The existing suite passes.
- Re-running the set gives byte-identical `verdict.json` files (no timestamps or
  absolute paths in the compared fields).
