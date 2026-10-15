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

Every model is strict (unknown fields are errors), like the core schema. Every
default is written out in the resolved claim. **"Proposal"** marks a value or rule
that the plan does not fix and that this design proposes.

#### 1.0.1 Placement and execution

- **D-S1. The ML fields live in the pack sections only.** One `claim.yaml` per paper,
  `kind: replicate`, `pack: ml`. The core schema (`src/refute/core/claim.py`, `Claim`)
  does not change: no field is added, removed or retyped, and the canonicalization
  does not change. The ML claims of a paper are the entries of `targets`, in the
  drawn order; the settings shared by the paper are in `test_plan`; `pass_criteria`
  must be null. This keeps new defaults out of the shared schema; W3.5 still depends
  on the historical projection and on its two tests (`tests/test_lock_compat.py`),
  which keep running. A claim hash that matches its lock does not mean
  `refute verify` passes with new code: the code component stays `TAMPERED` when the
  code differs from the lock (lock-compat-acceptance.md).
- **D-S2. One dossier per ML claim.** The engine writes one dossier per target, named
  by `target_key`, with the claim file, its lock and `target.json`; the ML
  `target_key` is the claim's `key`.
- **D-S3. Reply draft.** W2.13a reads `key`, `statement`, `source.arxiv_id`,
  `source.version`, `source.location`, `source.repository_url` and
  `source.repository_commit`. With D-S1 these are fields of one entry of `targets`:
  WP3 changes `refute reply-draft` to take the entry of the sealed `claim.yaml` whose
  `key` equals the `key` of the sealed `target.json`, and to refuse when the key is
  missing, when no entry or more than one entry matches, or when the entry differs
  from `target.json` in any of these fields. Both files are in the sealed core. The
  field names and every other rule of W2.13a stay as approved.
- **D-S4. Execution is coordinated per paper, in phases.** D-S2 is about the layout of
  the dossiers only. An ML run does not use the engine's per-target dispatcher
  (`run_processes` over targets): a paper runs as one job that goes through the
  setup, the base reproduction of every claim in the drawn order, and only then the
  attacks, with the shared reserves of the WP2 accountant (plan section 7.3).
  Parallelism exists only inside one claim's step.

#### 1.0.2 Paper level (`test_plan`)

| Field | Type and rule |
|---|---|
| `paper.arxiv_id`, `paper.version` | new-style arXiv id (`NNNN.NNNNN`), integer version ≥ 1; every claim's `source` must match |
| `paper.seed_sha256` | the per-paper seed: `sha256(claim_seed_bytes || arxiv_id_utf8)` of the claim draw (plan line 297), 64 hex digits. All the derived seeds of 1.0.4 come from it. **Proposal:** the plan says "the per-paper seed" (lines 488, 491) without defining it; this design uses the claim-draw seed, which is public and fixed before the lock |
| `budget.profile` | `main` (384 / 192 / 192 CPU-hours: paper / base / attacks, plan section 7.3) or `development` (96 CPU-hours, plan section 4.5; **proposal:** 48 / 48). The three values are written out and must equal the profile; no other value is accepted |
| `repository.url` | `https://` URL; every claim's `source.repository_url` must match |
| `repository.commit` | 40 hexadecimal characters; every claim's `source.repository_commit` must match |
| `repository.latest_commit_at_draw` | 40 hexadecimal characters (plan lines 383-388) |
| `repository.version_basis` | `named_in_paper`, `named_in_readme` or `latest_at_draw` (D-8); the first two also need `repository.named_ref` (the tag or commit as written there) and `repository.named_ref_location` |
| `build.ladder` | fixed, not configurable: `own_environment`, `requirements_compiled`, `requirements_compiled_next_python`, in this order (plan lines 392-399). A rung whose input does not exist in the repository is recorded at run time as not applicable; the first rung that builds is used |
| `build.python_ladder` | non-empty list of distinct Python versions (`"3.10"`, ...), in increasing order; the base Python is the first |
| `build.exclude_newer` | the date of the pinned commit (`uv pip compile --exclude-newer`) |
| `build.base_image` | image reference pinned by digest (`...@sha256:<64 hex>`) |
| `build.allowed_patches` | required list, possibly empty; each `{attachment, reason}`, where `attachment` is the path of an attachment with role `allowed-patch` (its hash is covered by the lock). A patch not in this list is refused (plan lines 400-402) |
| `datasets`, `weights` | lists of `{name, url, reference, version, license, retrieved_utc, sha256, size_bytes, local_copy_allowed}`; `scope: checkpoint_evaluation` needs a weights entry named by the claim |
| `datasets[].splits` | map from split name (`train`, `validation`, `test`, ...) to `{expected_examples (≥ 1), source}` as stated by the paper or the repository; `size_tolerance` (default 0: exact). This is what `data_present` checks |
| `stages` | one entry for each of `build`, `data`, `base_run`, `metric_recompute`, `attack_run`: `active_time_limit_hours` (> 0), `no_progress_hours` (default 2, at most the active limit), `progress_signal` (only value: `cpu_or_output`: the CPU time of the stage's containers grows, or its log or declared outputs grow), `retries` (≥ 0) |
| `absent_artifact` | `attempts` (≥ 1) and `interval_minutes` (> 0): the attempts that make an artifact count as absent (plan section 8.2) |
| `threads` | `OMP_NUM_THREADS`, `MKL_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `NUMEXPR_NUM_THREADS`: all required, positive integers, the same for every container (plan section 7.1) |

The values the protocol of WP5 fixes (`stages`, `absent_artifact`, `threads`) have no
code default. An interruption by a stage guard or by the budget is `INCONCLUSIVE`
with an operational reason (`budget_exhausted` or the guard's name); it is never a
`GateFailure` cause of the artifact (WP2 attribution).

#### 1.0.3 One ML claim (an entry of `targets`)

| Field | Type and rule |
|---|---|
| `key` | `arXiv-<arxiv_id>v<version>-C<n>`, equal to its `source` and unique in the file |
| `type` | `value` or `comparison` |
| `statement` | non-empty text |
| `source` | `arxiv_id`, `version`, `location` (table, row and column as printed), `quote` (as printed), `retrieved_utc`, `repository_url`, `repository_commit` |
| `inventory` | `candidate_id` and `position` (1, 2, 3, ... equal to the order in `targets`). The claim file has exactly one attachment with role `claim-inventory` and one with role `claim-draw`, both with `sha256`; the pack checks that the candidate is in the inventory with the same transcription (value, location, metric, split, command) and that the positions are those of the draw. Their formats are fixed in WP5 |
| `dataset` | the name of an entry of `test_plan.datasets`; `metric.split` must be one of its splits |
| `metric` | `name`, `split`, `unit` (`percent`, `fraction` or `native`), `higher_is_better` (information only), `reported` (finite; value claims only), `reported_sd` (≥ 0 or null), `reported_n_seeds` (≥ 1 or null), `n_examples` (≥ 1; equal to the split's `expected_examples`) |
| `comparison_mode` | required; `two_sided`, `one_sided_at_least`, `one_sided_at_most` for `value`; `direction`, `margin`, `magnitude` for `comparison` |
| `comparison` | comparison claims only (1.0.5) |
| `scope` | `full_training` or `checkpoint_evaluation`; the second also needs `weights` (the name of a weights entry) |
| `run` | `argv` (list of strings, run without a shell), `workdir` (relative, `/` separators, no `..`), `seed_argument` (a template with exactly one `{seed}`, such as `--seed={seed}`, or null), `metric_extraction` |
| `run.metric_extraction` | `from`: `file` or `log`; `file` (relative path, when `from: file`; it may contain `{seed}`); exactly one of `json_path`, `csv` (`column`, and `row` as `{column, equals}`), `regex` (`pattern`, `group`); `unit`: the unit in which the repository prints the value on this channel (`percent`, `fraction` or `native`; `native` only when `metric.unit` is `native`). The extracted token is kept as text (1.7, rounding) and converted from the channel's unit to `metric.unit` (× 100 or ÷ 100) before any comparison; the value must be finite. Every extraction (the method's, the reference's) declares its own `unit` |
| `seeds` | 1.0.4 |
| `tolerance` | `rel_tol` (default 0.02), `k_sd` (default 2), `abs_floor` (default 0.5 for `percent`, 0.005 for `fraction`, no default for `native`), `override_reason` (required when a value differs from its default, and always for `native`). The three values must be finite and ≥ 0, whatever the reason given. See 1.0.8 |
| `coverage_minimum` | 1.0.7 |
| `attacks` | 1.0.6 |
| `metric_recompute` | 1.7 |
| `approvals` | `transcription`: `{approved_by, approved_utc, approved_commit, inventory_sha256}`, the maintainer's approval of the transcription before the draw (plan line 283), bound to the inventory by its hash; `claim`: `{approved_by, approved_utc, approved_commit}`, the approval of the complete claim before the lock (plan line 336). `approved_commit` is 40 hexadecimal characters |

#### 1.0.4 Seeds

- **Base run.** `seeds.base`: a list of distinct integers in `[0, 2^31)`; its length
  `n_base` is `reported_n_seeds` capped by `seeds.base_cap` (≥ 1, fixed before the
  lock; plan line 465), and 1 when `reported_n_seeds` is null. `seeds.base_source`:
  `documented` (the seeds the paper or the repository states, in their order) or
  `derived` (below).
- **No seed option.** With `run.seed_argument: null`, `n_base` must be 1 and the
  `seeds` attack does not apply (reason: the repository exposes no seed): repeating
  a command whose seed is not controlled does not give distinct repetitions.
- **Base value.** The reproduced value `x_rep` is the arithmetic mean of the `n_base`
  extracted values. With `n_base` < `reported_n_seeds`, the dossier says the mean
  is over fewer seeds than the paper's.
- **Derived seeds.** For a domain `D` (`base`, `seeds`, `data_split`, `holdout`), the
  generator is `random.Random(int.from_bytes(sha256(paper_seed || D_utf8), "big"))`
  and the seeds are its successive `randrange(2**31)` values, skipping repeats and
  any value already used by the base run. The derived lists are written out in the
  resolved claim and checked again at validation:
  - `seeds.attack`: 5 seeds (plan line 488), whatever `seeds.base_cap` is;
  - `seeds.data_split`: 3 seeds, one per re-split (plan line 489);
  - `seeds.holdout`: 1 seed (plan line 491).

#### 1.0.5 Comparison claims

`comparison`: `method`, `reference`, `orientation` (`method_minus_reference` or
`reference_minus_method`, so that a positive `d` is an advantage in the claimed
sense), `reported_method`, `reported_reference`, `reported_sd_method` and
`reported_sd_reference` (≥ 0 or null), `g_pub` (required for `margin`, absent
otherwise), `d_pub` (required for `magnitude`, absent otherwise), `paired_sd` (≥ 0 or
null), and `reference_run`.

- **Tolerances.** `tol_m` and `tol_b` are the one-number tolerance (plan line 415) of
  each method's reported value with its own SD, under the claim's `tolerance`
  parameters. Without `paired_sd`: `tol_d = sqrt(tol_m² + tol_b²)` (plan lines
  449-455). With `paired_sd` (**proposal**, plan line 453 says only that it "is used
  instead"): `tol_d = max(abs_floor, k_sd · paired_sd)`.
- **Pairing.** Both methods run with the same seeds, the same data and the same split.
  `d` is computed for each seed and `d_rep` is the mean of the per-seed differences
  (equal to the difference of the means).
- **`reference_run`.** `same`: the reference value comes from the same runs, with its
  own `metric_extraction`; or a full `run` block (`argv`, `workdir`, `seed_argument`,
  `metric_extraction`) run with the same seeds. A comparison whose methods cannot run
  with the same seeds and split is not eligible (decided at the inventory, plan
  section 5.2).

#### 1.0.6 Attacks

`attacks` lists **each** of `seeds`, `data_split`, `ablation`, `holdout`, `leakage`,
`trivial_baseline` exactly once, each with `name`, `applies` (bool), `reason`
(non-empty, also when it applies) and `params` (present only when it applies). The
order of the applicable ones is the effective order (plan section 7.4).

| Attack | `params` and rule |
|---|---|
| `seeds` | none (5 seeds from 1.0.4; WP2 `seeds_attack`) |
| `data_split` | `original_proportions` (as the repository uses them) and `proportions`: lists of finite numbers in (0, 1) that sum to 1 within 1e-9 and are equal to each other; `split_argument` (how the repository takes the split seed). Not applicable to a fixed benchmark test set (plan line 489). WP2 `data_split_attack` |
| `ablation` | `disable` (the `argv` items added, or `{config_file, key, value}`: the value that turns the component off); `orientation` (`full_minus_ablated` or `ablated_minus_full`, so that a positive `d_abl` means the component helps in the claimed sense); `mode`: `direction` (`d_abl > 0`) or `margin`, which also needs the paper's published values `reported_full` and `reported_ablated` (with `reported_sd_full`, `reported_sd_ablated`, ≥ 0 or null) and `g_abl` = their oriented difference; then `tol_abl = sqrt(tol_full² + tol_ablated²)`, each the one-number tolerance of that published value under the claim's `tolerance` parameters, and the rule is `d_abl ≥ g_abl − tol_abl` and `d_abl > 0`. `d_abl` is the mean over the attack's runs, which use the base seeds. The same for value and comparison claims (on a comparison claim, the full model is the claim's method). Only when the repository exposes the switch (plan line 490) |
| `holdout` | `fraction` in (0, 0.5]; `tolerance_factor` > 1 (**proposal:** the wider tolerance is `tolerance_factor` times the claim's tolerance); `split_argument`. The holdout is carved with `seeds.holdout` before training |
| `leakage` | `max_overlap_fraction` in [0, 1); the unit is one example, hashed (SHA-256) from its bytes as stored in the declared dataset format; the overlap is the fraction of test examples whose hash appears in train |
| `trivial_baseline` | `kind`: `majority` (the most frequent class of the training labels, applied to the test split) or `random` (**proposal:** its expected value under uniform random guessing, computed exactly, with no random draw). Only for `accuracy` and `error_rate`; the claim must beat the baseline by more than its tolerance |

#### 1.0.7 Coverage minimums

`coverage_minimum` maps a check name to `{positive, negative}`, integers ≥ 1. The
accepted names are exactly those WP2 accepts for this claim (`aggregate_claim`): the
four gates, `base_reproduction`, `metric_recompute` when it applies, each applicable
attack, and the prerequisites of each applicable attack (`<attack>:run`,
`<attack>:metric`). Every accepted name is written out in the resolved claim:

- `base_reproduction`: positive and negative = `n_base` (the compared value is the
  mean of the base runs);
- `metric_recompute`: 1.7;
- every other name: 1 and 1. This is only a floor. Each check enforces its own
  completeness: `data_present` requires every split at its expected size, `seeds` and
  `data_split` require their fixed number of valid runs (WP2), `metric_recompute`
  requires all the examples of each run.

#### 1.0.8 Tolerance defaults and their concession

`abs_floor` 0.5 for `percent` and 0.005 for `fraction` are the same floor in two
scales; 0.5 percentage points is the plan's example (plan line 419). The formula
depends on how a metric is expressed: an accuracy of 99% gets a relative term of 1.98
percentage points, while the same performance written as an error rate of 1% gets
0.02, so the floor of 0.5 decides. This is an operational convention, not a neutral
one. The defaults apply to bounded rates in `percent` or `fraction`; any other metric
uses `native` and states its tolerance with a reason, and an override of a default
always needs a written reason before the lock.

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
primary and scikit-learn as the second; a conclusion only when both agree with each
other.** scikit-learn 1.9.1 is already in `uv.lock` through `lightkurve` (see
[wp0-acceptance.md](wp0-acceptance.md), section 2), so no dependency is added. The
check is fatal (a valid failure gives `NOT_REPRODUCED`), so one implementation's bug
must not be able to produce it alone. Alternatives considered: Refute's code only
(meets the minimum independence, but puts a fatal computation on one new
implementation) and scikit-learn only (less code, but it may be the very library the
paper used, and there is no cross-check by a different algorithm).

**What is compared.** For each base run (each seed and, for a comparison claim, each
method), the metric recomputed from that run's saved predictions is compared with
the value that run printed through the claim's fixed `metric_extraction`: the same
channel as the base reproduction, never another print, and never the paper's
`metric.reported`.

**The printed interval.** The extracted token is kept as text. If it has `d` digits
after the decimal point and an exponent `e` (0 when absent), its quantum is
`q = 10^(e−d)`, in the token's unit. `metric_recompute.printed_rounding`, fixed before
the lock, gives the interval of true values that print as that token:

- `nearest` (default): `[v − q/2, v + q/2]`;
- `truncate`: the sign is read from the token's text, not from its value: a token
  without a leading `-` gives `[v, v + q)`, a token with a leading `-` (including
  `-0.0`) gives `(v − q, v]`. A zero token without a sign (for example `0.0`, which a
  truncated negative value may also print) gives `(−q, q)`;
- `unknown`: `[v − q, v + q]`, which contains both the rounded and the truncated
  readings; with `unknown` the check can pass (both values inside, widened by `ε`) but
  never fail: what would be a failure is `INCONCLUSIVE`.

A JSON number gets the same treatment from its source text: a repository that saved
a rounded number gets the interval of that rounding. **Units.** The token and its
interval are converted from the unit declared by the channel's `metric_extraction.unit`
to `metric.unit`; the two implementations compute rates as fractions, and their
results are converted separately from `fraction` to `metric.unit` (`native` metrics are
not converted). A channel whose unit is not declared cannot be declared applicable.

**Decision, with `ε = 1e-9 · max(1, |a|)`:**

| Condition | Check for that run |
|---|---|
| either implementation cannot compute, or `|a − b| > ε` | `INCONCLUSIVE` (Refute side) |
| `a` and `b` both inside the interval widened by `ε` | `PASS` |
| `a` and `b` both outside the interval widened by `ε`, on the same side | `FAIL` (valid failure) |
| any other case (a boundary case) | `INCONCLUSIVE` |

The check passes when every base run passes. One valid failure establishes the
failure (the printed value is not what that run's predictions give); otherwise a run
that is not decided makes the check `INCONCLUSIVE`.

Requirements of issue #46:

- **W3.14 Independence.** The recomputation never imports or runs the code of the
  paper's repository: it reads only the saved predictions and labels. The second
  implementation guards against a computation error of either one. An agreement of
  the two reduces the risk of a Refute-side error; it does not remove it: both read
  the same arrays through the same reader and both use numpy, so a parsing, scale or
  alignment error would be shared. The reader is therefore minimal and covered by its
  own reference cases (W3.16).
- **W3.15 Conventions, fixed per claim before the lock** in
  `metric_recompute.convention`, and applied explicitly by both implementations; no
  library default decides anything:

  | Metric | Convention fields | Rules |
  |---|---|---|
  | `accuracy`, `error_rate` | `labels` | single-label, single-output classification |
  | `precision`, `recall`, `f1` | `labels`, `average` (`binary` with `pos_label`, `macro`, `micro`, `weighted`), `zero_division` (`0`, `1`, `undefined`) | `macro` and `weighted` average over **all** the declared `labels`, including a class absent from the data; a zero denominator under `undefined` makes the run `INCONCLUSIVE`; it is checked by Refute before either implementation runs (scikit-learn's own handling of zero denominators is never relied on) |
  | `auroc` | `labels` (two), `pos_label` | binary only; `y_score` is the score of `pos_label`, higher meaning more likely positive; labels are encoded to 0 and 1 before both implementations; tied scores count one half (Mann-Whitney), the convention of scikit-learn's `roc_auc_score` for a binary AUC |
  | `mae`, `mse`, `rmse` | none | single-output regression; `unit: native` |
  | `r2` | none | single-output regression; `unit: native`; a constant `y_true` (zero variance) makes the run `INCONCLUSIVE` (Refute checks it; scikit-learn is called with `force_finite=False`) |

  Not supported in v0.3 (so `applies` must be false): sample weights, multi-output or
  multi-label targets, top-k metrics, average precision, any other metric. `scale`
  is `fraction`, `percent` or `native`, equal to `metric.unit`.
- **W3.16 Reference cases.** For each metric and convention: hand-computed cases with
  known outputs fixed in the tests: ties in AUROC; a class absent from the data under
  `macro` and `weighted`; a zero denominator under each `zero_division`; a constant
  `y_true` for `r2`; percent versus fraction; the printed interval for `nearest`,
  `truncate` and `unknown`, scientific notation, and the boundary cases of the
  decision table. Property cases: invariance to the order of examples. The reader has
  its own cases (each format, a wrong dtype, a wrong length, a missing field).
  scikit-learn is the second implementation at run time, never the oracle of its own
  tests.
- **W3.17 Unsupported metrics or formats.** Applicability is decided per claim before
  the lock (`metric_recompute.applies`, with a `reason`); `applies: true` is refused
  at validation for anything outside W3.15 or outside the formats below. At run time,
  a missing or unreadable predictions file, a count of examples different from
  `metric.n_examples`, a non-finite value or a disagreement between the two
  implementations makes the run `INCONCLUSIVE` with its reason. **A limitation of
  Refute never produces a negative scientific verdict.** Coverage unit: base runs
  recomputed in full (all `n_examples` examples); `coverage_minimum` defaults:
  positive = the number of base runs (× 2 for a comparison with predictions for both
  methods), negative = 1 (one valid failure establishes it). The coverage table of
  [docs/verdicts.md](../../verdicts.md) gets this row in the same pull request as the
  code.
- **W3.18 Trusted verifier environment.** A container separate from the paper's, built
  from Refute's own pinned environment (`uv.lock`, base image by digest), with no
  network, the predictions mounted read-only, and no repository code. The readers
  execute no stored object: `npy` is read with `allow_pickle=False` and a numeric or
  string dtype; `csv` with the standard library and declared columns; `jsonl` with the
  standard JSON parser and declared keys. It runs inside the VM; its CPU time is
  counted in the base reproduction budget (plan line 545). Its isolation is checked on
  the VM by the WP6 tests (network none, read-only mounts, no repository code).

**Claim fields** (`metric_recompute` in each ML claim): `applies` (bool), `reason`;
when it applies: `predictions` (`file`, relative path with `{seed}`, and `{method}`
for a comparison whose two methods save predictions; `format`: `npy`, `csv` or
`jsonl`; `fields`: `y_true`, and `y_pred` or `y_score`), `convention` (the fields of
W3.15 for its metric, plus `metric` and `scale`) and `printed_rounding`. For a
comparison claim, the predictions of both methods are recomputed when both are saved;
otherwise `applies` is false with the reason. `metric_recompute_applies` of the WP2
aggregation is this `applies`.

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

**Schema (section 1.0), must fail at validation:**
- placement: an ML field at the top level of the claim (the core schema refuses it);
  `pass_criteria` set;
- identity: a `source` different from `test_plan.paper` or `test_plan.repository`; a
  `key` that does not match its `source`, or a duplicate `key`; `inventory.position`
  different from the order in `targets` or from the draw; a candidate absent from the
  inventory, or with a different transcription; zero or two attachments with role
  `claim-inventory` or `claim-draw`; `approvals.transcription.inventory_sha256`
  different from the inventory attachment's hash;
- paper level: a `budget` that differs from its profile; a `build.ladder` that is
  given, reordered or shortened; an unsorted or repeated `python_ladder`;
  `version_basis: named_in_paper` or `named_in_readme` with no `named_ref`;
  `build.allowed_patches` missing (an empty list is valid), or naming a file that is
  not an `allowed-patch` attachment; a missing `stages` entry, `absent_artifact` or
  `threads` value; `no_progress_hours` above the stage's active limit;
- one claim: a `dataset` or `metric.split` not declared in `test_plan.datasets`;
  `metric.n_examples` different from the split's `expected_examples`; `comparison` on
  a value claim, or missing on a comparison claim; `g_pub` outside `margin`, `d_pub`
  outside `magnitude`; a tolerance different from its default, or `unit: native`, with
  no `override_reason`; a negative or non-finite `rel_tol`, `k_sd` or `abs_floor`, even
  with a reason; a `metric_extraction` with no `unit`, or with `native` for a metric in
  `percent` or `fraction`; `scope: checkpoint_evaluation` with no `weights`;
  `run.argv` given as one string; a `workdir` or extraction `file` with `..` or an
  absolute path; a `seed_argument` without exactly one `{seed}`;
- seeds: repeated base seeds; a base list longer than `base_cap` or than
  `reported_n_seeds`; `seed_argument: null` with `n_base` > 1, or with the `seeds`
  attack applicable; derived seed lists that differ from the derivation of 1.0.4, or
  that overlap the base seeds;
- attacks: an attack missing, repeated or unknown; an attack that applies with no
  `params`, or one that does not apply with `params`; `data_split` proportions that
  do not sum to 1 or differ from `original_proportions`; `holdout.tolerance_factor`
  ≤ 1 or a `fraction` outside (0, 0.5]; `ablation` with no `orientation`, or in
  `margin` mode without `reported_full`, `reported_ablated` or `g_abl`, or with a
  `g_abl` different from their oriented difference; `leakage.max_overlap_fraction` outside
  [0, 1); `trivial_baseline` for a metric other than `accuracy` or `error_rate`;
- coverage: a `coverage_minimum` name WP2 would refuse for this claim.

**Schema, must pass:** the derived seed lists of a fixed `paper.seed_sha256` equal
values recorded in the test; a claim with `build.allowed_patches: []` resolves; the
resolved claim writes out every default and every accepted coverage name.

**Reply draft (D-S3):** must refuse when the sealed `target.json` has no `key`, when
no entry or two entries of `targets` match it, when the matching entry differs from
`target.json` in a W2.13a field, and when either file was changed after the seal; must
pass on a sealed dossier with one matching entry.

**Execution (D-S4):** with the subprocess backend on synthetic repositories, every
claim's base reproduction ends before the first attack of any claim, in the drawn
order, and the accountant's reserves are those of WP2.

**`metric_recompute` (section 1.7):**
- must pass: each supported metric and convention on its reference cases, with both
  implementations agreeing with each other and inside the printed interval;
- must give `FAIL`: both implementations agree and are both outside the printed
  interval (widened by `ε`) on the same side;
- must pass: `0.50` printed with `nearest`, `a = 0.5050000004`, `b = 0.5049999996`
  (both inside the interval widened by `ε`, whose upper end is `0.505000001`); a
  truncated `-0.0` with `a = b = −0.04`; a channel in `fraction` (`0.912`) for a claim
  in `percent` (`91.2`);
- must give `INCONCLUSIVE`, never `FAIL`: the two implementations disagree (simulated
  by a patched implementation in the test); one inside and one outside the widened
  interval while agreeing with each other (for example `0.50` printed, `a =
  0.5050000014`, `b = 0.5050000006`); a zero
  denominator under `zero_division: undefined`; a constant `y_true` for `r2`;
  `printed_rounding: unknown` with values outside the interval; a predictions file
  missing, unreadable or with a count of examples different from `metric.n_examples`;
  a non-finite value; an `npy` file that needs pickle;
- must be refused at validation: `applies: true` for an unsupported metric, format or
  convention, or with sample weights, multi-output or multi-label data.

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
