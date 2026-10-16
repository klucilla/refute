# Claim specification (`claim.yaml`)

A claim states what is tested, on which data, and how it passes or fails. It is
written **before** the data are analyzed and then locked (see
[lock-format.md](lock-format.md)).

## Core fields (all packs)

| Field | Type | Meaning |
|---|---|---|
| `schema_version` | `1` | Version of this specification. |
| `id` | string | Identifier: letters, digits, `.`, `_`, `-`. |
| `kind` | `replicate` or `calibration` | `replicate`: re-derive and attack published claims about the listed targets. `calibration`: a claim about Refute itself, evaluated on a target set. (`discover` arrives in v0.4.) |
| `pack` | string | Domain pack that interprets the claim, e.g. `tess`. |
| `title`, `hypothesis` | string | Human-readable statement of the claim. |
| `created` | date | `YYYY-MM-DD`. |
| `authors` | list of strings | At least one. |
| `definitions` | map | Precise meaning of the words used in the hypothesis. |
| `data_sources` | list | `{name, url, retrieved, notes}` for every external source. |
| `attachments` | list | Files covered by the lock: `{path, role, sha256}`. `path` is relative to the claim's directory, with `/` separators and no `..`. `sha256` is optional: if given it must match. |
| `targets` | list | Inline targets (pack-specific). Used by `replicate` claims. |
| `test_plan` | map | Pack-specific search, gauntlet and holdout parameters. |
| `pass_criteria` | map or null | Required for `calibration` claims. |

Unknown fields are errors, so a typo can never silently fall back to a default.

## Resolution

The pack validates `test_plan`, `targets` and `pass_criteria` and fills in every
default. The **resolved** claim is what the lock hashes, so every threshold is
written out explicitly in the locked form. Changing a default in the code later
cannot change what a locked claim means.

## TESS pack sections

### `test_plan`

```yaml
test_plan:
  data:        {mission: TESS, author: SPOC, exptime_seconds: 120,
                flux_column: pdcsap_flux, quality_bitmask: default,
                target_pixel_files: true, neighbor_radius_arcsec: 120}
  detrend:     {method: robust-local-quadratic, window_days: 1.0, knot_spacing_days: 0.1,
                segment_gap_days: 0.5, min_points_per_knot: 30, clip_sigma: 3.0,
                clip_iterations: 2, upper_clip_sigma: 5.0,
                transit_mask_half_width_durations: 1.0}
  search:      {method: bls-two-stage, objective: likelihood, period_min_days: 0.5,
                period_max_days: 20.0, durations_hours: [0.5, 1, 1.5, 2, 3, 4, 6, 8],
                bin_minutes: 10, frequency_factor: 1.0, peaks_per_sector: 5,
                max_clusters: 5, cluster_tolerance: 0.01, block_gap_days: 10,
                refine_samples_per_width: 6, refine_width_factor: 1.5,
                final_duration_steps: 21, final_oversample: 20}
  gauntlet:
    snr:               {min_snr: 7.1}
    odd_even:          {max_sigma: 3.0, min_transits_each: 2}
    secondary_eclipse: {max_sigma: 3.0, fatal_depth_ratio: 0.10}
    plausibility:      {max_duration_ratio: 1.5, max_companion_radius_rjup: 2.5,
                        max_stellar_radius_rel_err: 0.3,
                        unreliable_tic_dispositions: [SPLIT, DUPLICATE, ARTIFACT],
                        max_tmag_mismatch: 1.0}
    holdout_by_year:   {min_snr: 5.0, timing_sigma: 3.0, min_predicted_transits: 2,
                        min_train_transits: 3, min_window_coverage: 0.5,
                        baseline_gap_durations: 0.25, baseline_outer_durations: 1.5,
                        timing_step_minutes: 1.0, timing_scan_half_width_durations: 0.5,
                        hidden_detrend_window_factor: 3.0, max_timing_sigma_durations: 1.0,
                        require_valid_train: true, max_train_duration_period_ratio: 0.2,
                        max_hidden_window_fraction: 0.5}
    events:            {min_coverage: 0.5, baseline_gap_durations: 0.25,
                        baseline_outer_durations: 1.5}
    centroid_shift:    {max_sigma: 3.0, min_offset_pixels: 0.5, min_sectors: 1}
    aperture_depth:    {core_radius_pixels: 1.5, dilation_pixels: 1, max_sigma: 3.0,
                        min_depth_ratio: 1.2}
    nearby_contamination: {max_separation_arcsec: 21.0, max_eclipse_depth: 1.0,
                        min_crowdsap: 0.8,
                        ignored_dispositions: [SPLIT, DUPLICATE, ARTIFACT]}
    period_alias:      {min_box_delta_bic: 10.0, sine_harmonics: 2,
                        detrend_window_periods: 3.0,
                        systematic_periods_days: [13.7, 6.85, 4.5667, 3.425, 1.0],
                        systematic_tolerance: 0.01}
    systematics:       {dump_margin_hours: 1.0, max_dump_fraction: 0.5,
                        min_events_for_dumps: 3, max_sap_sigma: 3.0, max_sap_rel_diff: 0.5,
                        max_background_sigma: 3.0, max_background_fraction: 0.5}
    eb_catalog:        {match_radius_arcsec: 21.0, period_tolerance: 0.01,
                        period_factors: [1.0, 2.0, 0.5],
                        same_photometry_catalogs: [TESS-EB]}
```

What each parameter does is described in [gauntlet-tess-v0.1.md](gauntlet-tess-v0.1.md)
and, for the sections added in v0.2, [gauntlet-tess-v0.2.md](gauntlet-tess-v0.2.md);
the v0.2.1 additions (`holdout_by_year` train validity, `eb_catalog` own-TIC
matches) are in
[gauntlet-tess-v0.2.1.md](gauntlet-tess-v0.2.1.md).
The `eb_catalog` test runs only if the claim has attachments with role `eb-catalog`
(format `refute-eb-catalog-1`). A second attachment with role `eb-catalog-scan`
(format `refute-eb-catalog-scan-1`) records which catalog snapshots were scanned,
their hashes and row counts, the extraction radius and the targets; without it the
test is `INCONCLUSIVE`.

### Targets

```yaml
- key: TIC-207339000          # must equal "TIC-<tic_id>"
  tic_id: 207339000
  kind: planet                # planet | false_positive | development
  name: TOI-4427 b
  published: {period_days: 4.6182621, period_err_days: 1.7e-06, t0_bjd: 2459598.71,
              depth_ppm: 18614.3, duration_hours: 2.655}
  source: {name: ..., url: ..., retrieved_utc: ..., reference: ...}
  catalog: {...}              # verbatim catalog row
  mast: {...}                 # data availability at selection time
  fp_reason: null             # false positives: catalog comment, information only
```

`replicate` claims list targets inline. `calibration` claims list them in an
attachment with `role: targets` (schema `refute-tess-targets-1`); `development`
targets in that file are never run by `refute calibrate`.

### `pass_criteria` (calibration only)

```yaml
pass_criteria:
  period_tolerance: 0.001          # relative
  expected_planets: 10
  min_recovered_planets: 9
  expected_false_positives: 3
  min_flagged_false_positives: 2
  max_refuted_planets: 1           # degeneracy guard
  flag_excluded_tests: []          # v0.2: tests ignored when counting "flagged"
  flag_requires_signal_recovery: false    # v0.2.1: "flagged" needs the catalogued signal
  flag_signal_period_factors: [1.0, 2.0, 0.5]   # v0.2.1: P, 2P, P/2
```

`flag_excluded_tests` (default empty, which is the v0.1 definition): a false
positive counts as flagged only if its verdict, recomputed with the same rules from
the other tests, is `REFUTED`. The degeneracy guard always uses the full verdict.

`flag_requires_signal_recovery` (default `false`, which is the v0.2 definition): when
`true`, a false positive counts as flagged only if its signal is also *recovered*:
the found period matches the published (catalogued) period at one of
`flag_signal_period_factors`, that is,
`|P_found - f * P_pub| / (f * P_pub) <= period_tolerance` for some factor `f`
(inclusive). A missing period (analysis error, no candidate, no published period)
is not recovered. A false positive whose signal is not recovered stays in the
denominator. `flag_signal_period_factors` must be a non-empty list of positive
numbers and is used only when `flag_requires_signal_recovery` is `true`. Planets are
not affected. With the flag on, the calibration summary also reports the false
positives whose signal was not recovered, the count under the v0.2 definition, and a
"Signal recovered" column. See `docs/validation/v0.2.1/H7-acceptance.md`.

Both fields are resolved into the locked claim, so adding them changed the resolved
hash of older claims (the same happened to v0.1 claims when `flag_excluded_tests`
was added). Older calibrations are verified at their locked commit; see
[issue #30](https://github.com/klucilla/refute/issues/30).

All criteria must hold on a complete run. The targets file must contain exactly
`expected_planets` planets and `expected_false_positives` false positives.

## ML pack sections (v0.3)

**Status.** This section states what an ML claim must contain, following
[docs/plans/v0.3-plan.md](plans/v0.3-plan.md), sections 5 and 6.2. The exact schema
(field names, types, defaults and validation) is section 1.0 of
[docs/validation/v0.3/wp3-acceptance.md](validation/v0.3/wp3-acceptance.md), implemented
in `src/refute/packs/ml/schema.py`. The example below is the plan's illustration, not
the full form: for instance, the published SD is now an uncertainty record
(`reported_uncertainty`, section 1.0.9 there), and the command is an `argv` list.

### What a claim is

One claim is one quantitative statement that the repository of the paper documents
how to produce. The plan's example (section 5.1):

```yaml
- key: arXiv-2401.01234v2-C1
  type: value            # value | comparison
  statement: "Method X reaches 91.2% test accuracy on Dataset Y."
  source: {arxiv_id: 2401.01234, version: 2, location: "Table 2, row 'X', column 'Acc'",
           quote: "91.2 ± 0.3", retrieved_utc: ...}
  metric: {name: accuracy, split: test, higher_is_better: true,
           reported: 91.2, reported_sd: 0.3, reported_n_seeds: 5, unit: percent}
  comparison_mode: two_sided   # value claims: two_sided | one_sided_at_least | one_sided_at_most
                               # comparison claims: direction | margin | magnitude
  scope: full_training         # full_training | checkpoint_evaluation
  run: {command: "python train.py --config configs/y.yaml", workdir: ".",
        metric_extraction: {file: "results/metrics.json", json_path: "$.test.acc"}}
  tolerance: {...}
  coverage_minimum: {...}
  attacks: [...]
```

Metric extraction is deterministic: a JSON path, a CSV column or a regular expression
on the log, fixed before the lock. No LLM reads outputs to decide a value.

### Inventory and draw of the claims

The claims of each paper are drawn from a **frozen and published inventory**, with a
drand round of their own; the seed of the paper draw is never used to draw claims
(plan, section 5.2).

1. **Inventory.** Every numeric result in the paper's main-results tables (those
   referenced in the abstract or introduction as the main result) that the
   repository's instructions can produce within the budget. Granularity: one numeric
   cell is one candidate. Canonical ID: table, row and column as printed in the
   paper. Order: reading order of the paper. Eligibility rules and the closed list of
   exclusion reasons are fixed in the protocol.
2. **Approved before the draw.** For every candidate, the maintainer approves its
   transcription (value, location, metric, split, command), its type (`value` or
   `comparison`) and, for a comparison, its reference method. Each candidate names
   the method and its comparison reference, the dataset and split, the metric and the
   published number, and the execution conditions. A comparison claim evaluates the
   difference between methods under equivalent conditions. Whether a paper has an
   **eligible comparison** is determined by the rules of the protocol and approved
   with the inventory, before it is frozen; never from the draw or from any run.
3. **Frozen and published.** The inventories, their SHA-256 hashes and the
   implementation of the claim draw are committed and pushed before a future drand
   round reserved for the claims, fixed in the protocol. If they are not published
   before that round, the round cannot be used for them.
4. **Draw.** For each paper,
   `random.Random(int.from_bytes(sha256(claim_seed_bytes || arxiv_id_utf8), "big"))`
   shuffles the inventory, and the first **K = 3** candidates are drawn:
   - if the frozen inventory has at least one eligible comparison, a comparison is
     required: if none of the 3 drawn is a comparison, the 3rd is replaced by the
     first comparison in the shuffled order;
   - if it has none, the paper stays in the sample and up to 3 value claims are
     drawn; its dossier states explicitly that no comparison was evaluated.

   The absence of a comparison is never a reason to exclude a paper. If the inventory
   has 3 candidates or fewer, all are taken. The drawn order is the claim order used
   by the budget and by the report.
5. **After the draw.** Only corrections of transcription that keep the scientific
   identity of the candidate are allowed, each recorded. A drawn candidate may be
   invalidated only for a reason of a closed list fixed in the protocol; the original
   record is kept, and the next candidate in the shuffled order replaces it, of the
   same type when the comparison requirement must be kept. A candidate is never
   replaced because of an unfavorable result, an observed cost or an `INCONCLUSIVE`
   verdict.

A paper with no measurable number is excluded at triage as
`outside_v03_experimental_scope`; it is never `NOT_REPRODUCIBLE` (plan, section 5.3).

### Definitions required before the lock

Each claim specifies, before the lock (plan, section 5.4):

| Definition | Where |
|---|---|
| The tolerance for counting the result as reproduced, and the comparison mode | `tolerance`, `comparison_mode` |
| Seeds, repetitions and how variability is treated | the base run seeds and the `seeds` attack |
| The robustness changes that can produce `FRAGILE`, and their order | `attacks`, with applicability and order decided before the lock |
| The minimum coverage of each check, for a positive and for a negative conclusion | `coverage_minimum` (see [verdicts.md](verdicts.md), "Coverage for paper claims") |
| The scope: full training, or evaluation of a released checkpoint | `scope`; a checkpoint evaluation also follows the checks on model weights ([sandbox.md](sandbox.md)) |
| What separates a limitation of Refute from an impossibility to reproduce | the attribution rule in [verdicts.md](verdicts.md) |

A claim that does not specify all of these is not ready to lock.

Approvals are part of the locked claim: `approved_by`, `approved_utc` and the commit
in which the maintainer approved. The published inventory, including candidates not
drawn, is an attachment covered by the lock (plan, section 5.5).

### Tolerance and comparison modes

For one number (plan, section 6.2):

```
tolerance = max(abs_floor, rel_tol * |reported|, k_sd * reported_sd)
```

Defaults: `rel_tol = 0.02`, `k_sd = 2`, and `abs_floor` per metric scale (for example
0.5 percentage points for an accuracy in percent). Without a published SD the `k_sd`
term is absent. Per-claim overrides only before the lock, with a written reason. A
non-finite value does not pass the gate `metric_extracted`.

The mode comes from what the claim states, written in the claim (`comparison_mode`)
before the lock. The field `higher_is_better` alone never decides it.

**Value claims:**

| What the paper states | `comparison_mode` | Reproduced when |
|---|---|---|
| A published value "X" | `two_sided` | \|x_rep − X\| ≤ tolerance |
| A bound, "at least X" | `one_sided_at_least` | x_rep ≥ X − tolerance |
| A bound, "at most X" | `one_sided_at_most` | x_rep ≤ X + tolerance |

**Comparison claims.** `d` is the difference between the method and its reference,
oriented so that a positive `d` is an advantage in the claimed sense; the orientation
is written in the claim before the lock.

| What the paper states | `comparison_mode` | Reproduced when |
|---|---|---|
| A direction only | `direction` | d_rep > 0 (a tie does not keep the direction) |
| A minimum published margin g_pub | `margin` | d_rep ≥ g_pub − tol_d **and** d_rep > 0 |
| A published difference d_pub | `magnitude` | \|d_rep − d_pub\| ≤ tol_d |

A claim that states a direction and a margin uses `margin`, which requires both.

`tol_d = sqrt(tol_m² + tol_b²)`, where `tol_m` and `tol_b` are the tolerances of the
two numbers. This is an **operational acceptance convention**: it is not a confidence
interval and does not claim a demonstrated statistical uncertainty, since the
individual tolerances are not necessarily standard deviations and the compared
results may be correlated. When the paper publishes an uncertainty of the paired
difference, that value is used instead; the treatment of its absence is fixed before
the lock.

Equality at the limit counts as reproduced for the value modes and for `magnitude`;
it never does for `direction` or for the `d_rep > 0` part of `margin`.

Outside tolerance, the dossier records the value obtained, the difference and the
quantitative reason. It infers neither an error in the paper nor a change of
configuration.

If the paper reports a mean over n seeds, the base run uses n seeds, capped by the
budget; the cap is fixed before the lock.
