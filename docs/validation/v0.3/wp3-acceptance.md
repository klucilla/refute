# WP3 acceptance: ML pack

Line numbers refer to docs/plans/v0.3-plan.md at commit 8456780.

Work package WP3 of [docs/plans/v0.3-plan.md](../../plans/v0.3-plan.md) (section 11,
line 882). Issue #46. Also covers the pack part of #15 and the compatibility
requirement related to #30. Committed **before** the tests and code of the package
(plan lines 871-875). The claim format is described in
[docs/claim-spec.md](../../claim-spec.md) (ML section). The sandbox requirements are
in [docs/sandbox.md](../../sandbox.md).

## 1. What the package must do

### 1.0 Claim schema: design (revision of 2026-10-15, for the maintainer's approval)

This design fixes the exact form of an ML claim before any WP3 test or code (W3.1 to
W3.4). It needs the maintainer's approval as a design (CLAUDE.md, "Acceptance
documents and schemas"); code that implements exactly this design is then under the
standing approval.

**D-S1. Where the ML fields live: in the pack sections only.** One `claim.yaml` per
paper, `kind: replicate`, `pack: ml`. The core schema (`src/refute/core/claim.py`,
`Claim`) does not change: no field is added, removed or retyped, and the
canonicalization does not change. The ML claims of a paper are the entries of
`targets`, in the drawn order; the settings shared by the paper are in `test_plan`;
`pass_criteria` must be null. The TESS resolution is untouched, so W3.5 (equality with
the locked hashes, and no regression of the full resolution) holds by construction and
is still tested.

**D-S2. One dossier per ML claim.** The engine already writes one dossier per target,
named by `target_key`, with the claim file, its lock and `target.json`. The ML
`target_key` is the claim's `key`.

**D-S3. Reply draft.** W2.13a reads the ML claim fields `key`, `statement`,
`source.arxiv_id`, `source.version`, `source.location`, `source.repository_url` and
`source.repository_commit`. With D-S1 these are fields of one entry of `targets`, so
WP3 changes `refute reply-draft` to take the entry of the locked `claim.yaml` whose
`key` equals the dossier's `target.json` key, and to refuse when there is not exactly
one. The field names and every other rule of W2.13a stay as approved.

**Paper level (`test_plan`).** Every field is required unless a default is given;
every default is written out in the resolved claim.

| Field | Type and rule |
|---|---|
| `paper.arxiv_id`, `paper.version` | new-style arXiv id (`NNNN.NNNNN`), integer version ≥ 1; every claim's `source` must match |
| `repository.url` | `https://` URL; every claim's `source.repository_url` must match |
| `repository.commit` | 40 hexadecimal characters; every claim's `source.repository_commit` must match |
| `repository.latest_commit_at_draw` | 40 hexadecimal characters (plan lines 383-388) |
| `repository.commit_reason` | `tag`, `readme` or `latest_at_draw`; `tag` also needs `repository.tag` |
| `build.ladder` | ordered list from `own_environment`, `requirements_compiled`, `requirements_compiled_next_python` (plan lines 392-399) |
| `build.python_ladder` | ordered list of Python versions (`"3.10"`, ...) |
| `build.exclude_newer` | date of the pinned commit (`uv pip compile --exclude-newer`) |
| `build.base_image` | image reference pinned by digest (`...@sha256:<64 hex>`) |
| `datasets`, `weights` | lists of `{name, url, reference, version, license, retrieved_utc, sha256, size_bytes}`; may be empty; `scope: checkpoint_evaluation` needs at least one weights entry |
| `budget` | `paper_cpu_hours` (default 384), `base_cpu_hours` (default 192), `attack_cpu_hours` (default 192); the three must satisfy base + attack = paper |
| `guards` | `no_progress_hours` (default 2), `active_time_limit_hours` (required, > 0) |
| `attempts` | `absent_artifact_attempts` (required, ≥ 1), `absent_artifact_interval_minutes` (required, > 0), `stage_retries` (required, ≥ 0) |
| `threads` | map of thread variables fixed for every container: `OMP_NUM_THREADS`, `MKL_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `NUMEXPR_NUM_THREADS` all required, positive integers (plan section 7.1) |

Values that the protocol of WP5 fixes (guards, attempts, thread counts) have no code
default: a claim without them is not valid.

**One ML claim (an entry of `targets`).**

| Field | Type and rule |
|---|---|
| `key` | `arXiv-<arxiv_id>v<version>-C<n>`, equal to its `source` and unique in the file |
| `type` | `value` or `comparison` |
| `statement` | non-empty text |
| `source` | `arxiv_id`, `version`, `location` (table, row and column as printed), `quote` (as printed), `retrieved_utc`, `repository_url`, `repository_commit` |
| `inventory` | `candidate_id` (canonical ID in the frozen inventory) and `position` (1, 2, 3, ... equal to the order in `targets`); the inventory is an attachment with role `claim-inventory` |
| `metric` | `name`, `split`, `unit` (`percent`, `fraction` or `other`), `higher_is_better` (information only), `reported` (finite; value claims), `reported_sd` (≥ 0 or null), `reported_n_seeds` (≥ 1 or null), `n_examples` (≥ 1 or null: the size of the evaluated split) |
| `comparison` | comparison claims only, absent otherwise: `method`, `reference`, `orientation` (`method_minus_reference` or `reference_minus_method`, so that a positive `d` is an advantage in the claimed sense), `reported_method`, `reported_reference`, `g_pub` (required for `margin`, absent otherwise), `d_pub` (required for `magnitude`, absent otherwise), `paired_sd` (≥ 0 or null) and `paired_sd_absent` (default `combine`: `tol_d = sqrt(tol_m² + tol_b²)`, plan lines 449-455) |
| `comparison_mode` | required; `two_sided`, `one_sided_at_least`, `one_sided_at_most` for `value`; `direction`, `margin`, `magnitude` for `comparison` |
| `scope` | `full_training` or `checkpoint_evaluation` |
| `run` | `argv` (list of strings, run without a shell), `workdir` (relative, `/` separators, no `..`), `seeds` (list of integers, the base run; its length is `reported_n_seeds` capped by `seed_cap`), `seed_cap` (≥ 1), `seed_argument` (a template such as `--seed={seed}`, or null when the repository has no seed option), `metric_extraction` |
| `run.metric_extraction` | `from`: `file` or `log`; `file` (relative path, when `from: file`); exactly one of `json_path`, `csv` (`column`, and `row` as `{column, equals}`), `regex` (`pattern`, `group`); the value must be finite |
| `reference_run` | comparison claims only: `same` (the reference value comes from the same run, with its own `metric_extraction`) or a full `run` block |
| `tolerance` | `rel_tol` (default 0.02), `k_sd` (default 2), `abs_floor` (default 0.5 for `percent`, 0.005 for `fraction`, no default for `other`), `override_reason` (required when any value differs from its default, or when `unit` is `other`) |
| `coverage_minimum` | map from check name to `{positive, negative}`, integers ≥ 1; only names of this claim's checks; defaults written out: `base_reproduction` = the number of base seeds for both, every other check 1 and 1 |
| `attacks` | ordered list with **each** of `seeds`, `data_split`, `ablation`, `holdout`, `leakage`, `trivial_baseline` exactly once: `name`, `applies` (bool), `reason` (non-empty, also when it applies), `params` (only when it applies; per attack: `data_split.proportions`, `ablation.flag`, `holdout.fraction` and `holdout.tolerance_factor`, `leakage.max_overlap_fraction`, `trivial_baseline.kind` = `majority` or `random`); the order of the applicable ones is the effective order (plan section 7.4) |
| `metric_recompute` | section 1.7 |
| `approvals` | `approved_by`, `approved_utc`, `approved_commit` (40 hexadecimal characters) |

Every model is strict (unknown fields are errors), like the core schema.

### 1.1 Schema

- **W3.1** The `ml` pack validates and resolves ML claims with the fields of section
  1.0 (and of the claim spec): `type`, `statement`, `source` (with location and quote), `metric`,
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

- **W3.5** **Compatibility of the locked claims** (revised on 2026-10-15 by decision
  of the maintainer; the earlier revision of 7497955 had replaced the requirement
  without approval). The mechanism and its safeguards are in
  [lock-compat-acceptance.md](lock-compat-acceptance.md). Two separate requirements,
  both offline in CI:
  1. **Equality with the locked hashes.** A test loads the historical locked claims
     (the v0.1 claim and the v0.2 claim, each with its lock file), resolves them with
     the new code, and requires that their historical projection equals the
     `claim_sha256` recorded in each lock. Running the verification only at the old
     commits does not count.
  2. **No regression of the full current resolution.** The full resolved claim hash of
     each claim equals a value recorded in the test, with the commit it comes from.
  - Any WP3 change that alters either is redesigned, for example by keeping ML fields
    in the ML pack schema. Until the maintainer approves the compatibility pull
    request, no WP3 change touches the claim schema or claim serialization.
  - **Attachments** are checked separately by the existing lock verification
    (`src/refute/core/lock.py`).
  - The locks are never edited.

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
- **W3.10** Usage records for the WP2 accountant, `(container_id, account,
  usage_usec)`.
  - **Docker backend:** the records come from cgroup `cpu.stat`. Every process of a
    paper, **including the build steps** (the `RUN` steps of a Dockerfile) and every
    failed attempt, runs under one parent cgroup per paper; its usage is reported for
    the WP2 completeness check.
  - **Subprocess backend:** the records come from the process accounting of the child
    processes.
  - **Fixed in this document's revision, before the runner code:** the tolerance of
    the completeness check, and the reading interval of the in-run control (WP2
    W2.10a).
- **W3.10b** **The builder is not privileged.** Buildx's `docker-container` driver
  creates its builder container as privileged (`HostConfig.Privileged: true`;
  https://github.com/docker/buildx/blob/v0.29.1/driver/docker-container/driver.go#L117-L121,
  accessed 2026-10-14). The sandbox forbids `--privileged` (plan lines 375-379), so
  that driver is **not** used.
  - The revision of this document chooses, before the runner code, a builder
    configuration and version shown to be compatible with the sandbox: no privileged
    container; build steps under the paper's parent cgroup; and the entitlement
    restrictions of V9. Candidates to evaluate: the Docker Engine's built-in BuildKit
    (`docker` driver) with the build steps placed under the paper's cgroup, and
    rootless BuildKit.
  - The choice is checked by WP6 tests V7, V8 and V21.

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

### 1.7 `metric_recompute`: decision (revision of 2026-10-15, for the maintainer's approval)

**Proposed decision: two independent implementations, Refute's own (numpy) as the
primary, scikit-learn as the second; a conclusion only when both agree.**
scikit-learn 1.9.1 is already in `uv.lock` through `lightkurve` (see
[wp0-acceptance.md](wp0-acceptance.md), section 2), so no dependency is added. The
check is fatal (a valid failure gives `NOT_REPRODUCED`), so a bug of Refute must not
be able to produce it alone:

| Own result vs scikit-learn | Own result vs the printed value | Check |
|---|---|---|
| agree | agree | `PASS` |
| agree | disagree beyond rounding | `FAIL` (valid failure) |
| disagree | either | `INCONCLUSIVE` (Refute-side: implementations disagree) |
| one cannot compute | either | `INCONCLUSIVE` |

Requirements of issue #46:

- **W3.14 Independence.** The recomputation is independent of the code of the paper's
  repository that computed the printed value: it reads only the saved predictions and
  labels and never imports or runs repository code. Two implementations are used
  because a repository may itself call scikit-learn: an agreement of Refute's numpy
  code with scikit-learn, against a printed value, shows a disagreement that does not
  come from either library. The implementations agree when
  `|a − b| ≤ 1e-9 · max(1, |a|)`.
- **W3.15 Conventions, fixed per claim before the lock** in
  `metric_recompute.convention`, and passed explicitly to both implementations (no
  library default is used):
  - supported metrics in v0.3: `accuracy`, `error_rate`, `precision`, `recall`, `f1`
    (`average`: `binary` with `pos_label`, `macro`, `micro` or `weighted`),
    `mae`, `mse`, `rmse`, `r2`, `auroc` (binary, from scores; tied scores count one
    half, the Mann-Whitney convention);
  - `zero_division`: `0`, `1`, or `undefined`; `undefined` makes a zero denominator
    `INCONCLUSIVE`, never a disagreement;
  - `scale`: `fraction` or `percent`, matched to `metric.unit`;
  - **rounding**: the printed value is compared with the recomputed one within half a
    unit of its last printed decimal when it was extracted as text (log, CSV, a JSON
    string); a JSON number is compared within `1e-9 · max(1, |value|)`.
  A metric or convention outside this list cannot be declared applicable.
- **W3.16 Reference cases.** For each metric and convention: hand-computed cases with
  known outputs fixed in the tests (including ties in AUROC, a zero denominator under
  each `zero_division`, and percent versus fraction), plus property cases (invariance to
  the order of examples). scikit-learn is the second implementation at run time, never
  the oracle of its own tests.
- **W3.17 Unsupported metrics or formats.** Applicability is decided per claim before
  the lock (`metric_recompute.applies`, with a `reason`); a claim may declare it
  applicable only for a supported metric and a saved-predictions format of the list
  below. At run time, a missing or unreadable predictions file, a count of examples
  different from `metric.n_examples`, a non-finite value or a disagreement between
  the two implementations makes the check `INCONCLUSIVE` with its reason. **A
  limitation of Refute never produces a negative scientific verdict.** Coverage unit:
  examples recomputed; the expected coverage is `metric.n_examples` (a row to add to
  the coverage table of [docs/verdicts.md](../../verdicts.md) in the same pull
  request as the code).
- **W3.18 Trusted verifier environment.** A container separate from the paper's: built
  from Refute's own pinned environment (`uv.lock`, base image by digest), with no
  network, the predictions mounted read-only, and no repository code. It runs inside
  the VM; its CPU time is counted in the base reproduction budget (plan line 545).

**Claim fields** (`metric_recompute` in each ML claim): `applies` (bool), `reason`;
when it applies: `predictions` (`file`, relative path; `format`: `npy`, `csv` or
`jsonl`; `fields`: `y_true` and `y_pred` or `y_score`) and `convention` (`metric`,
`average`, `pos_label`, `zero_division`, `scale`). `metric_recompute_applies` of the
WP2 aggregation is this `applies`.

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

**Schema (section 1.0), must fail:** an ML field at the top level of the claim (the
core schema refuses it); `pass_criteria` set; a claim whose `source` differs from
`test_plan.paper` or `test_plan.repository`; a `key` that does not match its `source`,
or a duplicate `key`; `inventory.position` different from the order in `targets`; an
attack missing, repeated or unknown; an attack that applies with no `params`, or one
that does not apply with `params`; `comparison` on a value claim, or missing on a
comparison claim; `g_pub` outside `margin`, `d_pub` outside `magnitude`; a tolerance
different from its default, or `unit: other`, with no `override_reason`; a
`coverage_minimum` for a check the claim does not have; `scope: checkpoint_evaluation`
with no weights; `run.argv` given as one string; a `workdir` or extraction `file` with
`..` or an absolute path; a missing protocol value (`guards.active_time_limit_hours`,
`attempts`, `threads`).

**`metric_recompute` (section 1.7):**
- must pass: each supported metric and convention on its reference cases, with both
  implementations agreeing and agreeing with the printed value;
- must give `FAIL`: both implementations agree and the printed value differs beyond
  rounding;
- must give `INCONCLUSIVE`, never `FAIL`: the two implementations disagree (simulated
  by a patched implementation in the test); a zero denominator under
  `zero_division: undefined`; a predictions file missing, unreadable or with a count
  of examples different from `metric.n_examples`; a non-finite value;
- must be refused at validation: `applies: true` for an unsupported metric, format or
  convention.

**Compatibility (W3.5):** with the WP3 code, the historical projection of the v0.1
and v0.2 claims equals the `claim_sha256` of each lock, and their full resolved hashes
equal the recorded values. A change in the TESS resolution must fail this test.

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
- The sandbox requirements that WP6 relies on but that are code of this package are
  tested here and named in the WP6 table (`wp6-acceptance.md`, V14 to V22).
