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
W3.4). The maintainer approved its core on 2026-10-15, with the decisions recorded in
place: the run seed (1.0.2), the development budget split (1.0.2), the random
baseline (1.0.6), the published uncertainty and the paired SD (1.0.9), the holdout
rule (1.0.10), and the distinction between `metric_recompute` and the base
reproduction (1.7). Code that implements exactly this design is under the standing
approval (CLAUDE.md, "Acceptance documents and schemas"); no predicate is implemented
before 1.0.9 is merged.

Every model is strict (unknown fields are errors), like the core schema. Every
default is written out in the resolved claim.

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
| `paper.run_seed_sha256` | the per-paper **run seed** (plan lines 488 and 491, "the per-paper seed"), 64 lowercase hex digits: the SHA-256 digest of the concatenation, with no separator, space or line break, of (1) `claim_seed_bytes`: the 32 bytes obtained by decoding the hex `randomness` of the drand round reserved for the claims, (2) the 16 bytes of the ASCII text `refute/v0.3/runs`, and (3) the UTF-8 bytes of the canonical arXiv ID without version (for example `2401.01234`). It is derived from the claim-draw seed with its own domain string, so it differs from the seed that shuffled the claim inventory, `sha256(claim_seed_bytes || arxiv_id_utf8)` (plan line 297). All the derived seeds of 1.0.4 come from it. Decided by the maintainer on 2026-10-15 |
| `budget.profile` | `main` (384 / 192 / 192 CPU-hours: paper / base / attacks, plan section 7.3) or `development` (96 / 48 / 48 CPU-hours; the 96 come from plan section 4.5, the split 48 / 48 was decided by the maintainer on 2026-10-15). The three values are written out and must equal the profile; no other value is accepted |
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
| `metric` | `name`, `split`, `unit` (`percent`, `fraction` or `native`), `higher_is_better` (information only), `reported` (finite; value claims only), `reported_uncertainty` (1.0.9; value claims only), `reported_n_seeds` (≥ 1 or null), `n_examples` (≥ 1; equal to the split's `expected_examples`) |
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
  generator is `random.Random(int.from_bytes(sha256(run_seed || D_utf8), "big"))`,
  where `run_seed` is the 32 bytes of `paper.run_seed_sha256` (1.0.2),
  and the seeds are its successive `randrange(2**31)` values, skipping repeats and
  any value already used by the base run. The derived lists are written out in the
  resolved claim and checked again at validation:
  - `seeds.attack`: 5 seeds (plan line 488), whatever `seeds.base_cap` is;
  - `seeds.data_split`: 3 seeds, one per re-split (plan line 489);
  - `seeds.holdout`: 1 seed (plan line 491).

#### 1.0.5 Comparison claims

`comparison`: `method`, `reference`, `orientation` (`method_minus_reference` or
`reference_minus_method`, so that a positive `d` is an advantage in the claimed
sense), `reported_method`, `reported_reference`, `uncertainty_method` and
`uncertainty_reference` (1.0.9), `g_pub` (required for `margin`, absent otherwise),
`d_pub` (required for `magnitude`, absent otherwise), `paired_uncertainty` (1.0.9),
and `reference_run`.

- **Tolerances.** `tol_m` and `tol_b` are the one-number tolerance (plan line 415) of
  each method's reported value, `max(abs_floor, rel_tol · |x|, k_sd · sd_x)`, with
  `sd_x` from its uncertainty (1.0.9; the `k_sd` term is absent when the paper gives
  none), under the claim's `tolerance` parameters.
  - **Without a paired uncertainty:** `tol_d = sqrt(tol_m² + tol_b²)` (plan lines
    449-455).
  - **With a paired uncertainty** (plan line 453: "that value is used instead"): the
    same one-number tolerance applied to the published difference,
    `tol_d = max(abs_floor, rel_tol · |p|, k_sd · sd_d)`, where `p` is `d_pub`
    (`magnitude`) or `g_pub` (`margin`), and `sd_d` is the standard deviation of the
    paired difference (1.0.9). In `direction` mode no tolerance is used.
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
| `holdout` | `split_argument`; the fraction and the wider tolerance are not free parameters: they follow the rule of 1.0.10. The holdout is carved with `seeds.holdout` before training |
| `leakage` | `max_overlap_fraction` in [0, 1); the unit is one example, hashed (SHA-256) from its bytes as stored in the declared dataset format; the overlap is the fraction of test examples whose hash appears in train |
| `trivial_baseline` | `kind`: `majority` (the most frequent class of the training labels, predicted for every test example) or `random` (decided by the maintainer on 2026-10-15: its expected value under uniform random guessing, computed exactly, with no random draw). `labels`: the `K ≥ 2` classes of the task, declared. **Where it applies:** only for `accuracy` and `error_rate`, on a single-label classification task (binary or multi-class: each example has exactly one true class among the `K` declared ones). Then `random` gives accuracy `1/K` and error rate `1 − 1/K`, whatever the class frequencies (each guess is right with probability `1/K`). **Outside that** (any other metric, regression, multi-label or multi-output tasks, an undeclared or unknown number of classes) `trivial_baseline` cannot be declared applicable: validation refuses it, and the claim records it as not applicable with the reason. The claim must beat the baseline by more than its tolerance. **Known limitation** (recorded by the maintainer's decision of 2026-10-15): the `random` baseline is that of a uniform guess, so on imbalanced data it is more lenient than the `majority` baseline. For example, with 90% of the test examples in one of `K = 2` classes, `random` gives accuracy 0.5 and `majority` gives 0.9. The choice is deliberate, so that this attack never produces a false failure; a claim that beats the `random` baseline is not thereby shown to beat the majority class. **Tie for the majority class** (decided by the maintainer on 2026-10-16, with the usual tolerance): when several classes tie for the most frequent training class, every tied class is a possible baseline; the attack passes only if the claim beats every tied class (the one with the highest test accuracy), fails if it does not beat even the tied class with the lowest test accuracy, and is `INCONCLUSIVE` in between; the tied classes and their test accuracies are recorded. The concession: a claim that beats some tied classes but not all gets no conclusion from this attack |

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

#### 1.0.9 Published uncertainty: SD, SE, CI or none (closes `paired_sd`)

An uncertainty record (`reported_uncertainty`, `uncertainty_method`,
`uncertainty_reference`, `paired_uncertainty`) has:

- `kind`: `sd` (standard deviation of the runs), `se` (standard error of their mean),
  `ci` (confidence interval of their mean) or `none` (the paper reports nothing);
- `value` (for `sd` and `se`), or `lower`, `upper`, `level` and `method` (for `ci`;
  `level` in (0, 1), for example 0.95; `method` as the paper states it: `t` for
  mean ± t·SD/√n, `normal` for mean ± z·SD/√n, or `other_or_unknown`);
- `n`: the number of runs the published uncertainty is over, as the paper states it
  (≥ 2), or absent when the paper does not state it;
- `unit` as printed (`percent`, `fraction` or `native`), `location` and `quote` in
  the paper.

**Provenance.** Every number of an uncertainty record comes from the paper, transcribed
with its location and quote and approved with the inventory (plan section 5.2). None
comes from Refute's runs: a tolerance is fixed before the lock and never depends on a
result of the sample.

**Unit.** The record is converted from its printed unit to `metric.unit` (× 100 or
÷ 100), like the reported values; the resulting `sd` is in `metric.unit`.

**Definition and formulas.** `sd` is the standard deviation of the individual runs
(the plan's `reported_sd`, the `k_sd` term of plan line 415). For a paired
uncertainty, the runs are the per-run differences
`d_i = metric_method,i − metric_reference,i` (with the claim's orientation) over the
same `n` seeds, and `sd_d` is their standard deviation.

| `kind` | `sd` used by the tolerance |
|---|---|
| `sd` | `value` |
| `se`, with `n` | `value · sqrt(n)` |
| `ci`, `method: t`, with `n`, symmetric | `se = (upper − lower) / (2 · t(1 − (1 − level)/2, n − 1))`, then `se · sqrt(n)` |
| `ci`, `method: normal`, with `n`, symmetric | `se = (upper − lower) / (2 · z(1 − (1 − level)/2))`, then `se · sqrt(n)` |
| `none` | no `k_sd` term (plan line 420): the paper reports no uncertainty |
| anything else: `se` or `ci` without `n`; `ci` with `method: other_or_unknown` (bootstrap, transformed, model-based, not stated); a `ci` that is not symmetric about the reported value (the two half-widths differ by more than 1% of the width) | **reported but not convertible** (below) |

`t(q, df)` and `z(q)` are quantiles of Student's t and of the normal distribution,
computed with SciPy (`scipy.stats.t.ppf`, `scipy.stats.norm.ppf`; SciPy 1.18.1 in
`uv.lock`). The resolved claim writes out the quantile used and the resulting `sd`.
These conversions hold for the usual standard error of the mean of `n` independent
runs and for an interval built as mean ± quantile · SD/√n; nothing else is inverted.

**Reported but not convertible.** It is never treated as "no uncertainty". The true
tolerance is unknown; it is only known to be **at least** the tolerance computed
without the `k_sd` term (the "lower tolerance"):

- one value: `max(abs_floor, rel_tol · |x|)`;
- a comparison whose `paired_uncertainty` is reported but not convertible: the paired
  structure is kept, `tol_d = max(abs_floor, rel_tol · |p|)`; the branch without a
  paired uncertainty (1.0.5) is used only when the paper reports no paired
  uncertainty at all, since it is not necessarily narrower.

A conclusion stands only if it would hold for **every** tolerance at or above the
lower tolerance; otherwise the check is `INCONCLUSIVE`, with the reason "reported
uncertainty not convertible". By predicate:

| Predicate | A larger tolerance makes it | With the lower tolerance, what stands |
|---|---|---|
| value modes, `magnitude`, the `seeds`, `data_split` and `holdout` attacks (the claim's predicate) | easier to pass | a `PASS`; a `FAIL` becomes `INCONCLUSIVE` |
| `margin` (`d ≥ g − tol` and `d > 0`), `ablation` in `margin` (`d_abl ≥ g_abl − tol_abl` and `d_abl > 0`), and the attacks that apply these predicates | the first condition: easier to pass; the second does not use a tolerance | a `PASS`; a `FAIL` because `d ≤ 0` (or `d_abl ≤ 0`) stays `FAIL`, since it holds for every tolerance; a `FAIL` with a positive difference but too small a margin under the lower tolerance becomes `INCONCLUSIVE` |
| `trivial_baseline` (beat the baseline by more than the tolerance) | harder to pass | a `FAIL`; a `PASS` becomes `INCONCLUSIVE` |
| `direction`, `ablation` in `direction` | no tolerance | unaffected |

**Source** (retrieved 2026-10-15):

- Cochrane Handbook for Systematic Reviews of Interventions, version 6.5, chapter 6,
  section 6.5.2.2,
  https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-06:
  "A standard deviation can be obtained from the SE of a mean by multiplying by the
  square root of the sample size"; a 95% interval is 3.92 SE wide only for large
  samples, and "If the sample size is small (say fewer than 60 participants in each
  group) then confidence intervals should have been calculated using a value from a t
  distribution".
- NIST/SEMATECH e-Handbook of Statistical Methods, 1.3.5.2 "Confidence Limits for the
  Mean", https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm: the limits
  are the mean ± t(1 − α/2, N − 1) · s/√N, "with N - 1 degrees of freedom".
- NIST Dataplot reference manual, "T TEST",
  https://itl.nist.gov/div898/software/dataplot/refman1/auxillar/t_test.htm: the
  paired statistic uses "the standard deviation of the differences of the paired
  samples" and √n, with n − 1 degrees of freedom. For paired runs the `n` differences
  are one sample, so the degrees of freedom are `n − 1`.

#### 1.0.10 Holdout: fraction and wider tolerance (closes the holdout factor)

- **Where it applies.** Only when all of these hold; otherwise the attack is not
  applicable, with the reason, decided before the lock:
  - the metric is a mean of per-example values: `accuracy`, `error_rate`, `mae`,
    `mse`;
  - the claim's mode has a tolerance to widen: any value mode, `margin` or `magnitude`.
    A `direction` claim has no tolerance (1.0.5), so a sign flip from noise cannot be
    told apart from a real one: the holdout does not apply to it;
  - a `train` split is declared and `m ≥ 100` (below).
- **Fraction.** Fixed, not a parameter: `m = floor(0.1 · n_train)` examples of the
  training split (`datasets[].splits.train.expected_examples`) are carved out with
  `seeds.holdout` before training, and the model trains on the rest. With `m < 100`
  (so `n_train < 1000`, including `m = 0`) the attack is not applicable: the holdout
  estimate would be too noisy to tell a real deviation apart (for a rate near 0.5 its
  standard error would be above 0.05).
- **Wider tolerance.** The claim's predicate (the same mode) is applied to the value
  measured on the holdout, with the claim's tolerance multiplied by
  `factor = max(1, sqrt(n_examples / m))`, where `n_examples` is the size of the split
  the claim reports on (`metric.n_examples`). The factor and `m` are written out in the
  resolved claim.
- **Why this factor: an operational convention, under stated assumptions.** For a
  mean of per-example values, the standard error of the estimate is the per-example
  standard deviation divided by the square root of the number of examples (NIST
  e-Handbook 1.3.5.2 and Cochrane Handbook 6.5.2.2, cited in 1.0.9). If the per-example
  variance on the holdout is comparable to that on the reported split, the examples
  are independent enough, and the variance is finite, an estimate on `m` examples
  varies `sqrt(n_examples / m)` times as much as one on `n_examples`. The factor widens
  the tolerance by that ratio and never narrows it (factor ≥ 1). It is a convention
  motivated by that approximation, not a derived guarantee: the claim's tolerance
  also holds a floor, a relative term and the SD between runs, not only the sampling
  error between examples.
- **Concession: the training bias is not modelled.** Training on 90% of the training
  split can lower the result, and on small datasets the drop can matter; the factor
  does not account for it. The WP4 cases check behaviour in defined scenarios on both
  sides: no false `FRAGILE` from sampling noise or from a smaller training set inside
  the bound, and a real deviation (a model fitted to its evaluation split) still
  detected. They do not guarantee the absence of false failures on real papers; an
  attack failure is reported with this concession.
- **Fixed before the lock.** The fraction 0.1, the factor rule and every value derived
  from them are fixed before the lock and are never adjusted because of results on
  the sample, the pilot or the development papers.

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

### 1.4a Reading interval, stopping margin and completeness tolerance (W3.10; WP2 W2.10 and W2.10a)

Revision of 2026-10-16, taken during the maintainer's absence under the night
delegation of 2026-10-15, after a Codex review recorded in its pull request (#92),
choosing at each point the option that leads to `INCONCLUSIVE` rather than to a false
failure or a false pass; ratified by the maintainer on 2026-10-16, preserving the
validation conditions and the documented concessions. It fixes the values that W3.10
requires before the runner code. They decide when a run or the accounting of a paper is invalid
(a Refute error, `INCONCLUSIVE`), never a verdict about the paper.

- **Reading interval Δ = 1 s.** While a container runs, the docker backend reads the
  cumulative usage of its cgroup (`cpu.stat`, `usage_usec`) every Δ and stops the
  container when a reading reaches F, its threshold (W2.10a). The subprocess backend
  (CI and local tests only, never a real paper's budget) polls at most every Δ; tests
  may use a shorter interval.
- **CPU limits admitted.** Every container of a paper runs with a CPU quota in
  `cpu.max` (quota and period) and with `cpu.max.burst` equal to 0, so the group
  accumulates no unused bandwidth from earlier periods. Sources:
  https://docs.kernel.org/admin-guide/cgroup-v2.html#cpu-interface-files and
  https://docs.kernel.org/scheduler/sched-bwc.html ("A value of 0 for cpu.cfs_burst_us
  indicates that the group can not accumulate any unused bandwidth"), both accessed
  2026-10-16. The runner refuses to start a container whose quota is `max` (no limit),
  whose burst is not 0, whose limit (quota / period) is above C, or whose period is
  above P.
- **Stopping margin M, derived, not assumed:**
  `M = 2 × C × (P + Δ + D + S) + N × σ`, in CPU-seconds, converted to integer
  microseconds and rounded up, where:
  - `C` is the largest CPU limit (quota / period) any container of the paper may get,
    at most the 24 vCPU of the VM; one M per paper, given to the WP2 accountant;
  - `P` is the largest `cpu.max` period any container of the paper may get;
  - `D` is the largest detection delay measured on the VM in WP6 V22: from the planned
    reading instant to the moment the stop request is issued for a reading that
    reached F (the reading itself and the decision);
  - `S` is the largest stop latency measured on the VM in V22: from the stop request to
    the moment every process of the container's cgroup and of its descendants has
    ended (the cgroup is no longer populated), not only two equal readings;
  - `N × σ` covers the per-CPU runtime slices that the kernel hands out ahead of use
    and that can let a group briefly exceed its quota ("typically at most 1ms per
    cpu", sched-bwc.html above): `N` is the number of CPUs of the VM and `σ` the value
    of `/proc/sys/kernel/sched_cfs_bandwidth_slice_us` read on the VM (default 5 ms),
    used instead of the smaller 1 ms;
  - the factor 2: with periodic quotas and no burst, the usage in an interval of length
    L is at most `C × L + 2 × C × P` (two partial periods at its ends), which
    `2 × C × (P + L)` covers, with `L = Δ + D + S` the longest time from the last
    reading below F to the end of the container's usage.

  The measured maxima of V22 check the implementation on the VM; they do not prove a
  universal worst case. A usage above R = F + M is a breach (W2.10a): the accounting of
  the paper is invalid (`INCONCLUSIVE`, a Refute error), never absorbed.

  Example only, not a decision: C = 24, P = 0.1 s, D = 0.1 s, S = 1 s, N = 24,
  σ = 5 ms give M = 2 × 24 × 2.2 + 0.12 = 105.72 CPU-s, about 0.03 CPU-hour.
- **Completeness (W2.10).** Two checks, both required:
  - **every expected container has its final record:** the containers of a paper are
    those the runner started, each after a grant of the accountant; a container granted
    without a final record makes the accounting invalid, whatever its usage;
  - **the parent cgroup agrees with the records within T:**
    `|parent − Σ records| ≤ T`, with `T = 1 CPU-s × (n_containers + 1)` in
    microseconds, `n_containers` being the number of containers of the paper, `parent`
    the usage of the paper's parent cgroup, and the records the final reading of each
    container. There is no term proportional to the total, so the size of the paper
    never widens T.

  T is an operational tolerance, provisional until V22: usage that no record covers
  (for example build steps that ran outside every container of the runner) is detected
  only when it is larger than T, and below T it is bounded by T, not excluded. Measured
  in V22 on runs of known synthetic containers, builders and failed attempts included,
  the difference must stay below T/2; otherwise T is revised with the maintainer before
  the lock.
- **Fixed before the lock, never after.** Δ, the formula of M, the measured maxima D
  and S, C, P, N, σ and T are written in the protocol before the lock and are never
  adjusted because of a run of the sample, the pilot or the development papers.
- **D and S recorded, with an alert (decided by the maintainer on 2026-10-16).** For every
  container stopped by its threshold or a guard, the runner records the detection delay
  (from the planned reading instant to the stop request) and the stop latency (from the
  request to the end of every process of the run) it measured. When a value exceeds its
  V22 maximum, an alert is recorded with the paper's run, for the maintainer. Nothing is
  adjusted automatically: M, T, the thresholds and every other limit stay as fixed before
  the lock.
- **Subprocess backend.** It has no parent cgroup, so the completeness check is
  recorded as not applicable there; this backend never runs a real paper (PR #87).
- **Synthetic cases (WP3):**
  - **must pass:** a container stopped at F with a final usage ≤ F + M; a difference
    between the parent and the records of exactly T;
  - **must give `INCONCLUSIVE` (accounting invalid):** a final usage above R = F + M; a
    granted container (a builder, for example) without its final record; a difference
    between the parent and the records of T + 1 µs, such as a builder's usage of more
    than T that no record covers;
  - **must be refused before the start:** a container without a CPU quota, with a burst
    other than 0, with a limit above C or with a period above P.

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

**Two different checks, kept apart in the text and in the code** (decided by the
maintainer on 2026-10-15):

- **`metric_recompute` checks the chain inside one run:** it recomputes the metric from
  the run's saved predictions and compares it with the value **that same run printed**.
  It says whether the printed number is what the predictions give. It never looks at
  the paper.
- **The base reproduction compares the run with the paper:** the value the runs
  produced (`x_rep`, 1.0.4) is compared with **the claim published in the paper**
  (`metric.reported`, or the comparison of 1.0.5), with the claim's mode and
  tolerance.

The code keeps them in separate functions and separate results (`metric_recompute`
and `base_reproduction` in the WP2 aggregation), and neither reads the other's
reference value.

**What is compared by `metric_recompute`.** For each base run (each seed and, for a
comparison claim, each method), the metric recomputed from that run's saved
predictions is compared with the value that run printed through the claim's fixed
`metric_extraction`: the same channel as the base reproduction, never another print,
and never the paper's `metric.reported`.

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
  do not sum to 1 or differ from `original_proportions`; `holdout` applicable for a
  metric outside 1.0.10 or with no `train` split, or with a fraction or factor given
  by hand; `ablation` with no `orientation`, or in `margin` mode without
  `reported_full`, `reported_ablated` or `g_abl`, or with a `g_abl` different from
  their oriented difference; `leakage.max_overlap_fraction` outside [0, 1);
  `trivial_baseline` for a metric other than `accuracy` or `error_rate`, for a task
  that is not single-label classification, or with fewer than 2 declared `labels`;
- uncertainty (1.0.9): an unknown `kind` or CI `method`; an `n` below 2 (an absent
  `n` is valid and makes `se` or `ci` not convertible); a `ci` with `lower` ≥ `upper`
  or `level` outside (0, 1); a negative `sd` or `se`; a record without `location` and
  `quote`;
- coverage: a `coverage_minimum` name WP2 would refuse for this claim.

**Schema, must pass:** the run seed of 1.0.2 for a fixed `claim_seed_bytes` and arXiv
ID equals a value recorded in the test, and differs from the claim-draw seed; the
derived seed lists from it equal values recorded in the test; a claim with
`build.allowed_patches: []` resolves; the resolved claim writes out every default and
every accepted coverage name.

**Uncertainty conversion (1.0.9), must pass with recorded values:** `sd` kept; `se`
times `sqrt(n)`; a 95% `ci` with `method: t` and `n = 5` converted with `t(0.975, 4)`;
a 90% `ci` with `t(0.95, n − 1)`; a 95% `ci` with `method: normal` converted with
`z(0.975)`; a printed unit in `fraction` for a claim in `percent`; a paired
uncertainty giving `tol_d = max(abs_floor, rel_tol · |p|, k_sd · sd_d)`; without a
paired uncertainty, `tol_d = sqrt(tol_m² + tol_b²)`.

**Reported but not convertible (1.0.9):** `se` without `n`, a `ci` with
`method: other_or_unknown`, and an asymmetric `ci`:
- value claim: a result inside the lower tolerance is `PASS`; a result outside it is
  `INCONCLUSIVE` with the reason "reported uncertainty not convertible", never `FAIL`
  (published 80%, SE 2 points with no `n`, reproduced 75%); `kind: none` with the same
  numbers gives `FAIL`;
- comparison with a paired SE of 0.05 points and no `n` (published 90 and 80, so
  `d_pub` = 10, reproduced `d` = 8, `magnitude`): `tol_d` is the lower paired
  tolerance `max(0.5, 0.2) = 0.5`, not the marginal `sqrt(1.8² + 1.6²)`; the deviation
  of 2 gives `INCONCLUSIVE`, never `PASS` and never `FAIL`;
- `margin` with a paired uncertainty reported but not convertible (`g_pub` = 10): a
  reproduced `d` of 0 or below gives `FAIL` (it fails for every tolerance); a
  reproduced `d` of 8, positive but below `g_pub` minus the lower tolerance, gives
  `INCONCLUSIVE`; the same for `ablation` in `margin` with `d_abl`;
- `trivial_baseline` with a reported but not convertible uncertainty (accuracy
  published and reproduced 60%, baseline 50%, SE 10 points with no `n`): an advantage
  of 10 points over a lower tolerance of 1.2 gives `INCONCLUSIVE`, never `PASS`; an
  advantage below the lower tolerance gives `FAIL`.

**Holdout rule (1.0.10), must pass with recorded values:** `m = floor(0.1 · n_train)`
and `factor = max(1, sqrt(n_examples / m))` for a large and for a small holdout; the
factor is 1 when `m ≥ n_examples`; `m < 100` (`n_train < 1000`, including `m = 0`), a
`direction` claim and a metric outside the list make the attack not applicable. The
cases on both sides (no false `FRAGILE`, a real deviation still detected) are
end-to-end papers of WP4 (W4.3a, PR #79).

**Random baseline (1.0.6):** `1/K` accuracy and `1 − 1/K` error rate for `K` = 2, 3
and 10 declared classes, independent of the class frequencies.

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
