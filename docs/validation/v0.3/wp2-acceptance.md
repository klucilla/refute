# WP2 acceptance: core (paper verdicts, coverage, budget, seal, reply draft, workers)

Line numbers refer to docs/plans/v0.3-plan.md at commit 8456780.

Work package WP2 of [docs/plans/v0.3-plan.md](../../plans/v0.3-plan.md) (section 11,
line 881). Issue #45. Also covers #32 and the core part of #15. Committed **before**
the tests and code of the package (plan lines 871-875). The rules implemented here are
documented in [docs/verdicts.md](../../verdicts.md) (paper section) and
[docs/right-of-reply.md](../../right-of-reply.md).

Everything in WP2 is engine code in `src/refute/core/` with offline synthetic tests.
No third-party code runs and no network is used. `src/` is part of the code hash, so
WP2 lands before any v0.3 lock.

## 1. What the package must do

### 1.1 Paper verdicts and claim aggregation (plan 8.1-8.3, lines 614-692)

- **W2.1** `PaperVerdict` gains `INCONCLUSIVE`. `DiscoveryVerdict` and the discovery
  function `aggregate` keep their behavior; the existing tests of `aggregate` pass
  unchanged.
- **W2.2** A new, separate function aggregates **one claim**. It takes:
  - the results of the base reproduction, with the gates `environment_build`,
    `data_present`, and `run_completed` and `metric_extracted` of the base runs;
  - the fatal checks `base_reproduction` and `metric_recompute`;
  - the results of each attack, each with its own prerequisites;
  - the expected attacks;
  - the attribution of every failed gate (W2.3).

  It returns the verdict, the reason, the status "Basic reproduction obtained;
  robustness inconclusive" when it applies, the attacks not executed, and a flag for
  incomplete coverage. The order is the one of plan lines 627-638, steps 0 to 6.
- **W2.3** Attribution (plan lines 653-664). A failed gate becomes `NOT_REPRODUCIBLE`
  only when its cause is recorded as a failure of the artifact's documented
  procedure with complete attempts. Every other cause (exhausted budget, operational
  guard, Refute error, transient network failure, interrupted stage, undetermined) is
  `INCONCLUSIVE`. A missing or unknown cause is treated as undetermined.
- **W2.4** An interruption or a failed prerequisite of an attack makes only that
  attack `INCONCLUSIVE`; it never changes the gates of the base reproduction (plan
  lines 619-621).
- **W2.5** A valid negative conclusion is kept when later checks are missing:
  `NOT_REPRODUCED` stays `NOT_REPRODUCED`, and a valid attack failure stays `FRAGILE`,
  with the remaining checks recorded as not executed (plan lines 671-677).

### 1.2 Minimum coverage (plan 8.4, lines 694-716)

- **W2.6** Each check carries a minimum coverage for a positive conclusion and one for
  a negative conclusion, both given by the claim.
  - Below the positive minimum, a PASS becomes `INCONCLUSIVE`.
  - Below the negative minimum, a FAIL gives no negative conclusion unless the valid
    evidence already obtained establishes it (plan lines 696-701).
  - The existing `enforce_coverage` (zero or undeclared coverage) stays, and applies
    first.

### 1.3 The result of a paper (plan lines 681-692)

- **W2.7** A function builds the claim profile of a paper:
  - the claims in the drawn order, with their verdicts;
  - counts by verdict, with `INCONCLUSIVE` in the denominator;
  - the headline: "<k> of <k> drawn claims: <VERDICT>" only when every claim has the
    same verdict, otherwise "Mixed results: see the claims";
  - a flag that is true when any claim verdict is negative (`FRAGILE`,
    `NOT_REPRODUCED`, `NOT_REPRODUCIBLE`).

  A paper with only `INCONCLUSIVE` claims, or `INCONCLUSIVE` and `REPRODUCED`, gets no
  wording that calls it positive or reproduced.

### 1.4 Budget accounting (plan 7.3, lines 535-565)

- **W2.8** A deterministic accountant, with no I/O. Amounts are integer microseconds of
  CPU time (cgroup `usage_usec`), so no rounding enters a decision. It implements:
  - the limit per paper (384 CPU-hours);
  - the base pool (192 CPU-hours), with the setup account charged first;
  - the base reserve per claim, (192 − S) / n_base;
  - the sharing rule: a claim may use the balance minus the reserves of the claims
    that have not run;
  - the attack pool, frozen after **all** base runs, as 192 CPU-hours plus the base
    balance;
  - n_attack, the claims with base obtained and at least one applicable attack, kept
    in the drawn order;
  - the attack reserve, pool / n_attack;
  - n_attack = 0, recorded as "no distribution";
  - no transfer from attacks back to the base.
- **W2.9** For every charge, the accountant answers whether it is allowed, and the
  remaining balance and reserves. When a charge exceeds what is allowed, it is
  refused with the reason `budget_exhausted`, and the reason names the pool (`setup`,
  `base` or `attacks`).
- **W2.10** The meter. Usage is summed over every container of the paper, **including
  the builder and every failed build attempt**; the orchestration on the host is
  recorded separately.
  - **Records:** WP2 receives `(container_id, account, usage_usec)` records, where
    `usage_usec` is the cumulative total of that container, read once when it ends.
  - **How a shared cost is attributed only once:** every container belongs to exactly
    one account (setup, one claim's base, or one claim's attack). A container that
    serves several claims is setup; the builder is setup.
  - **Rejected records:** an unknown account; the same `container_id` twice; a
    negative value.
  - **Completeness check:** all containers of a paper run under one parent cgroup per
    paper, implemented in WP3. The accountant compares the sum of the records with
    the parent cgroup's own usage. A difference above a tolerance fixed in the WP3
    acceptance revision makes the paper's accounting invalid, recorded as a Refute
    error (`INCONCLUSIVE`), never as a pass.
  - The reading of `cpu.stat` itself is implemented in WP3 (runner).

### 1.5 Seal and annexes (plan 9.1, lines 722-729)

- **W2.11** A command seals the experimental core of a dossier: the locked claims,
  outputs, logs, `verdict.json` and the manifest. It writes the SHA-256 of a
  deterministic archive of the core, and a combined hash for a set of dossiers.
  The archive is deterministic: sorted paths, fixed timestamps and modes, and no
  dependence on the platform's line endings for binary content.
- **W2.12** An annex (a reviewer report, a `reply/` record, the authors' reply) has its
  own manifest that cites the core hash. `refute check-dossier` reports separately:
  - whether the core is intact against its seal;
  - whether each annex is intact against its manifest.

  Adding an annex never changes the core hash.

### 1.6 Reply draft (plan 9.1, item 4, lines 732-737)

- **W2.13** `refute reply-draft <dossier>` writes a draft email, in English, from the
  dossier only:
  - the claim and its location;
  - the paper version and commit;
  - the verdict and its meaning;
  - the reproduction commands;
  - an invitation to reply within the period, and an offer to publish the reply.

  The address comes only from the corresponding-author field recorded in the claim
  from the paper. The command never sends anything and opens no network connection;
  it prints the SHA-256 of the draft.
- **W2.14** The template contains no words about people beyond addressing the
  authors. A fixed list of forbidden words (for example "misconduct", "error by the
  authors", "fraud", "sloppy") is checked by a test.

### 1.7 Workers and affinity (plan 7.2, lines 524-533; issue #32)

- **W2.15** The default worker count is the number of CPUs the process may use under
  its affinity mask, minus 2, at least 1. `REFUTE_WORKERS` still overrides it.
  - **On Windows**, the mask is read with `GetProcessAffinityMask`.
  - **On Linux**, with `os.sched_getaffinity(0)`.
  - Elsewhere, the fallback is `os.cpu_count()`.

  **Finding behind this rule (2026-10-14, local, Python 3.13.5, Windows 11):** with
  the mask `FFFFFF00`, `os.cpu_count()` and `os.process_cpu_count()` both returned
  32, while `GetProcessAffinityMask` returned 24 bits. On Windows, neither standard
  function reflects the affinity, so the API is required.
- **W2.16** `init_worker()` run in the current process (one worker, or one task) leaves
  `os.environ` as it was before the call (issue #32). Spawned workers keep setting the
  thread variables for themselves.

## 2. Synthetic cases

All offline and deterministic, in `tests/`.

**Must pass** (the expected verdict or value is produced):
- one case per step of the order (0 to 6), each giving its verdict;
- a `NOT_REPRODUCIBLE` for each artifact-procedure cause of W2.3;
- `REPRODUCED` with full coverage;
- `FRAGILE` from a valid failure in `seeds` (2 of 5 runs fail the predicate) and in
  `data_split` (1 of 3);
- a profile with a unanimous headline and one with "Mixed results";
- the accountant on the plan example (3 claims, S = 30: 54 CPU-hours per claim);
- the attack pool frozen after base runs with leftovers;
- n_attack = 0;
- a seal, then an annex added: the core is still intact;
- a reply draft with the address taken from the claim;
- the worker count under a restricted mask: 6 CPUs gives 4, 2 CPUs gives 1.

**Must fail, or must not reach the negative or positive verdict:**
- a gate failure with cause `budget_exhausted`, `operational_guard`, `refute_error`,
  `transient_network`, `interrupted` or a missing cause, which must be `INCONCLUSIVE`
  and never `NOT_REPRODUCIBLE`;
- a valid `seeds` failure next to an interrupted `data_split`, which must be `FRAGILE`
  and not `INCONCLUSIVE`;
- an attack interrupted with no valid failure, which must be `INCONCLUSIVE` with the
  status "Basic reproduction obtained; robustness inconclusive";
- a PASS with zero coverage, or below the positive minimum, which must not be
  `REPRODUCED` (#15 cases);
- a profile of `INCONCLUSIVE` and `REPRODUCED` claims, which must not produce a
  "REPRODUCED" headline;
- a charge above the pool balance minus the reserves of the claims not yet run,
  which is refused (`budget_exhausted`). The opposite case **must pass**: a charge
  above a claim's own reserve but within the leftovers. In the plan example (3 claims,
  S = 30, reserve 54), after the first claim uses 30, a charge of 60 for the second is
  allowed, because 54 stays reserved for the third;
- a transfer from attacks to the base, which is refused;
- a usage record with an unknown account, or the same container twice, which is
  rejected;
- records whose sum differs from the parent cgroup's usage, for example a builder
  left out, which make the accounting invalid (`INCONCLUSIVE`);
- a changed byte in the core, which `check-dossier` reports as core not intact;
- a changed annex, which is reported as that annex not intact, with the core still
  intact;
- the reply draft, which must open no socket (the test suite runs with
  `--disable-socket`) and must contain no forbidden word;
- `os.environ` after an in-process `init_worker()`, which must be unchanged.

**Platform-specific:**
- the affinity test on Windows starts a child Python process, restricts its own
  affinity to a known subset of the CPUs available to it, and checks
  `default_workers()`;
- the Linux variant uses `os.sched_setaffinity`;
- each variant is skipped on the other system, with the reason;
- CI has both systems (`windows-2025`, `ubuntu-24.04`).

## 3. Metrics and evidence

- Test counts come from a JUnit XML file (`pytest --junitxml`), never from the console
  line (CLAUDE.md).
- CI is green on the four jobs.
- Each criterion W2.1 to W2.16 is listed in the PR with the test that covers it.

## 4. Regression cases

- The full existing suite passes, including the discovery `aggregate` tests and the
  workers-equivalence test.
- `refute verify` on the v0.1 and v0.2 claims still passes at their locked commits.
  WP2 changes `src/`, so the code hash at the WP2 commit differs, as expected before a
  v0.3 lock.
- `docs/verdicts.md` and the code agree: a test checks that the verdict names in the
  enum match the paper verdict list of the document.
