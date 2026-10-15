# WP3 acceptance: ML pack

Line numbers refer to docs/plans/v0.3-plan.md at commit 8456780.

Work package WP3 of [docs/plans/v0.3-plan.md](../../plans/v0.3-plan.md) (section 11,
line 882). Issue #46. Also covers the pack part of #15 and the compatibility
requirement related to #30. Committed **before** the tests and code of the package
(plan lines 871-875). The claim format is described in
[docs/claim-spec.md](../../claim-spec.md) (ML section). The sandbox requirements are
in [docs/sandbox.md](../../sandbox.md).

## 1. What the package must do

### 1.1 Schema

- **W3.1** The `ml` pack validates and resolves ML claims with the fields of the claim
  spec: `type`, `statement`, `source` (with location and quote), `metric`,
  `comparison_mode`, `scope`, `run` (with metric extraction), `tolerance`,
  `coverage_minimum` and `attacks`, plus the comparison reference, the orientation of
  `d`, and the approvals.
- **W3.2** `comparison_mode` is required.
  - Value claims accept only `two_sided`, `one_sided_at_least` and
    `one_sided_at_most`.
  - Comparison claims accept only `direction`, `margin` and `magnitude`.
  - `margin` requires `g_pub`; `magnitude` requires `d_pub`.
  - `higher_is_better` alone never fills `comparison_mode`.
- **W3.3** Every default of the tolerance (`rel_tol = 0.02`, `k_sd = 2`, the `abs_floor`
  per metric scale) is written out in the resolved claim. A per-claim override needs
  a written reason (plan lines 418-421).
- **W3.4** The applicability and the order of the attacks, and the minimum coverage of
  each check, are part of the claim. A claim without them is not ready to lock (plan
  lines 321-334).

### 1.2 Compatibility of locked claims (related to #30)

- **W3.5** A test loads the **historical locked claims** (the v0.1 claim and the v0.2
  claim, each with its lock file), recomputes the canonical form and the claim hash
  **with the new code**, and requires **equality with the hashes recorded in the
  locks**. Running the verification only at the old commits does not count. If a WP3
  change would alter those hashes, the change is redesigned (for example, ML fields
  stay in the ML pack schema). The locks are never edited. The test runs offline in
  CI.

### 1.3 Adapter

- **W3.6** arXiv metadata, the repository at a pinned commit (the three commits of plan
  lines 383-388), and datasets and weights with reference, version, license,
  retrieval date and hashes.
- **W3.7** Network access happens only in explicit fetch commands. Tests use fixtures
  and never the network.

### 1.4 Sandbox runner

- **W3.8** One interface, two backends:
  - `docker`, for the VM; tested locally, since CI cannot pull images;
  - `subprocess`, tested in CI on synthetic repositories (plan lines 406-408).
- **W3.9** The build ladder, the allowed-patch list and the logging of every attempt
  (plan lines 392-402). The recorded causes of each failure feed the attribution rule
  of WP2.
- **W3.10** Usage records `(account, usage_usec)` for the WP2 accountant: from cgroup
  `cpu.stat` in the docker backend, and from the process accounting of the
  subprocess backend.

### 1.5 Metric extraction

- **W3.11** Deterministic extraction (JSON path, CSV column, or a regular expression on
  the log), fixed in the claim.
- **W3.12** A non-finite value, or a metric on zero examples, does not pass
  `metric_extracted`.

### 1.6 Attacks

- **W3.13** The predicates of plan section 6.2 (lines 410-462), the attack rules of
  plan section 6.3 (lines 467-492), and the general rules of the attacks:
  - only `seeds` and `data_split` use the claim's predicate;
  - in `seeds`, the predicate is also applied to the mean, and one-sided modes stay
    one-sided;
  - `data_split` requires 3 of 3;
  - a missing or invalid run is never a scientific failure.

### 1.7 `metric_recompute`: open decision, settled here before tests and code

The implementation used by `metric_recompute` is still to be chosen: scikit-learn, or
Refute's own code. scikit-learn 1.9.1 is already in `uv.lock` through `lightkurve`
(see [wp0-acceptance.md](wp0-acceptance.md), section 2). Before any test or code of
`metric_recompute`, a revision of this document records the choice and defines
(issue #46):

- **W3.14** what code or library the recomputation must be independent of: at least,
  the code of the paper's repository that computed the printed value;
- **W3.15** the conventions of each supported metric (for example averaging for F1,
  ties in AUROC, division by zero), so that a convention mismatch cannot pass for a
  disagreement;
- **W3.16** the reference cases that validate each computation: known inputs and
  outputs, fixed in the tests;
- **W3.17** how unsupported metrics or formats are handled. They make the check
  `INCONCLUSIVE` with a reason; **a limitation of Refute never produces a negative
  scientific verdict**;
- **W3.18** a trusted verifier environment, separate from the paper's environment:
  inside the VM, pinned, and counted in the CPU-hour accounting of the base
  reproduction (plan line 545; `metric_recompute` is part of the base budget).

### 1.8 Exporter

- **W3.19** Writes the reply draft (through WP2) and a summary for a human. It never
  submits or sends anything.

## 2. Synthetic cases

**Must pass:**
- a valid claim of each type and mode resolves, with all defaults written out;
- the subprocess backend runs a synthetic repository and extracts its metric by JSON
  path, CSV column and regular expression;
- each comparison mode reproduces on values inside its predicate;
- equality at the limit reproduces for the value modes and for `magnitude`.

**Must fail (rejected at validation, or the check does not pass):**
- a claim with no `comparison_mode`;
- a value claim with a comparison mode, and the reverse;
- `margin` without `g_pub`;
- `magnitude` without `d_pub`;
- an override without a reason;
- `direction` with d_rep = 0, which does not reproduce;
- `margin` with d_rep ≤ 0, even when g_pub − tol_d ≤ 0, which does not reproduce;
- a non-finite metric;
- a metric on zero examples;
- an empty split (#15);
- an extraction path that matches nothing.

**Compatibility (W3.5):** the v0.1 and v0.2 locked claims recompute to their recorded
hashes with the new code.

Every coverage row of [docs/verdicts.md](../../verdicts.md) gets a case that must not
pass and one that must, here or in WP4.

## 3. Metrics and evidence

- Test counts come from a JUnit XML file.
- CI is green on the four jobs.
- Each criterion W3.1 to W3.19 is listed in the PR with its test or its document
  revision (W3.14 to W3.18).

## 4. Regression cases

- The existing suite passes, including the TESS pack.
- W3.5 passes.
- The `tess` pack and its claims are unaffected: entry points and resolved TESS claims
  are unchanged.
