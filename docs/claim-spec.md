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
                flux_column: pdcsap_flux, quality_bitmask: default}
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
                        max_stellar_radius_rel_err: 0.3}
    holdout_by_year:   {min_snr: 5.0, timing_sigma: 3.0, min_predicted_transits: 2,
                        min_train_transits: 3, min_window_coverage: 0.5,
                        baseline_gap_durations: 0.25, baseline_outer_durations: 1.5,
                        timing_step_minutes: 1.0, timing_scan_half_width_durations: 0.5}
    events:            {min_coverage: 0.5, baseline_gap_durations: 0.25,
                        baseline_outer_durations: 1.5}
```

What each parameter does is described in [gauntlet-tess-v0.1.md](gauntlet-tess-v0.1.md).

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
```

All criteria must hold on a complete run. The targets file must contain exactly
`expected_planets` planets and `expected_false_positives` false positives.
