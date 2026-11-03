# v0.5 acceptance: the rate cases of WP1 to WP4 (one run, 2026-11-03)

The single acceptance run of [acceptance.py](acceptance.py) on the reserved acceptance seeds,
reported as unused before this run (they are deterministic from public strings, so the record
shows the procedure, not that they were unknowable), from commit `75c02e2` (a clean tree), after
three Codex reviews of the harness (two NO-GO, then GO). Synthetic data with known truth; `method_status: not_validated`. Nothing here
validates the method on real data.

- Summary: [acceptance-run.md](acceptance-run.md) and [acceptance-run.json](acceptance-run.json)
  (133 rows: 41 cases in white, correlated and stellar-trend noise, 200 trials each, 400 for the
  error pulls).
- Every trial: `acceptance-run-detail.json` (36,540,637 bytes, SHA-256
  `9e77ccd09b9819e391c1924b4f2752ea198b08a650677b9a4df2f4d7c9cf3557`), above the 5 MB limit of
  git, archived to the Drive by [archive_detail.py](archive_detail.py) with the checked manifest
  [acceptance-run-detail.manifest.json](acceptance-run-detail.manifest.json).
- Cost: 14.67 processor-hours (sum of the workers' CPU), 41.2 minutes of wall time on 22
  workers.

**Result: 119 of 133 rows PASS, 11 FAIL, 3 INVALID.** By the stop rule of the plan (section 3), a
test whose scientific acceptance fails is recorded as failed and is diagnostic only in v0.5;
nothing is retuned and no case is rerun on these seeds.

## The rows that did not pass

| Row | Noise | Observed | Rule |
|---|---|---|---|
| 1.10 error pulls (per event) | white | sd 1.166, mean 0.081 | sd in [0.9, 1.1], mean at most 0.1 |
| 1.10 error pulls (per event) | correlated | sd 1.348, mean 0.178 | same |
| 1.8-single_event-b (below the rule) | white, correlated, trend | 8, 8 and 5 PASS of 200 | never PASS |
| 2.1-event_consistency null, N = 6 | correlated | 22 FAIL of 200 | at most 2 |
| 2.1-event_consistency null, N = 20 | correlated | 30 FAIL | at most 2 |
| 2.1-event_consistency null, N = 40 | white; correlated | 4; 85 FAIL | at most 2 |
| 1.8-event_consistency-c (detectable null) | correlated | 14 FAIL | at most 2 |
| 2.7-event_consistency partial events | correlated | 14 FAIL | at most 2 |
| 4.1-centroid-a | white; correlated | INVALID: 199 FAIL, 1 trial "sectors disagree" | FAIL at least 184, every trial constructed |
| 4.5-centroid-c | correlated | INVALID: 199 PASS, 1 trial "qualification failed" (2 of 3 sectors) | at most 2 FAIL, every other trial PASS |

The group-mean pulls pass in every noise model (sd 1.027, 1.074, 1.022; the scatter floor used in
238, 370 and 239 of 400 curves), and so do the per-event pulls in the stellar-trend model.

**Observations, recorded, not repaired:**

- *1.10 white.* The decided window is each curve's first measured window, 0.67 day after a segment
  start, inside the reach of the 1-day detrending window; the pulls of all 7200 windows have
  sd 1.061 in white noise (reported, not decided). The white failure may come from that choice of
  window; the correlated failure does not (all windows: sd 1.350).
- *4.1 and 4.5 (INVALID).* The harness marks a trial unconstructed when the test returns before
  computing its sensitivity block; three trials did ("sectors disagree"; a qualification failure
  of an on-target planet in correlated noise, with the aperture depths at 3.5 and 4.1 sigma from
  the light-curve depth). Under the frozen rules these rows are INVALID: acceptance is not
  established. Counting the trials as they are, 4.1 would meet its rule (199 FAIL) and 4.5 in
  correlated noise would not (one trial neither PASS nor FAIL).
- *single_event-b.* The alternative of the test's sensitivity block is defined at the observed
  total SNR, so noise can make a below-design trial detectable and its ratio rule pass.
- *event_consistency in correlated noise.* The chi-square uses the per-event errors, which the
  correlated-noise error model underestimates (row 1.10).
- *sinusoid (3.3).* The test FAILs every trial at P while its sensitivity block, the worst of P/2,
  P and 2P, is near zero: the fits at P/2 and 2P carry the unmodeled variability at P in their
  beta. A FAIL is never changed by the block, so the row is unaffected.
- *period_alias in correlated noise:* 181 of 200 FAIL, all detectable (rule: at least 171).

## Roles in the v0.5 battery (the plan's stop rule, section 3)

| Test | Severity | Role | Basis |
|---|---|---|---|
| `odd_even` (v0.5 rule, group means) | fatal | decisive | 1.8 a, b, c pass; group-mean pulls pass |
| two-sided phase-0.5 check (dip and brightening) | warning | decisive | 1.8, 3.1, 3.2 pass |
| `sinusoid` | warning | decisive | 1.8 a, b and 3.8 pass |
| `edge_events` (group means) | warning | decisive | 1.8 a, b, 2.5, 2.6 pass |
| `aperture_depth` | fatal | decisive | 1.8 a, b, c pass |
| `systematics` (SAP, background) | warning | decisive | 1.8 a, b, c pass |
| `period_alias` | fatal | decisive | 1.11 passes; its sensitivity simulation draws white noise internally, so the correlated-noise trials do not validate a correlated internal simulation |
| `single_event` | fatal | **diagnostic** | 1.8-b fails in every noise model; it rests on per-event errors (1.10 fails in correlated noise: the acceptance document, after row 1.11) |
| `event_consistency` | fatal | **diagnostic** | 2.1, 1.8-c and 2.7 fail; per-event errors (1.10) |
| per-sector centroid (`centroid_v5`) | fatal | **not accepted** (diagnostic), unless the maintainer decides otherwise at S2 | 4.1 and 4.5 INVALID; neither counterfactual reading establishes acceptance (4.5 in correlated noise would still not be met) |

The engine rule (`enforce_sensitivity`) stays in force for every test (the acceptance document,
WP1). The rows not in this run (1.1 to 1.7, 1.9, 2.4, 3.4 to 3.7, 4.2 to 4.4, WP5 to WP10) are
unit and integration tests of the suite.
