# v0.5 calibration protocol (`refute-tess-v0.5-calibration`)

Approved at S2 by the maintainer on 2026-11-03, with the decisions recorded in
[docs/plans/v0.5-plan.md](../../docs/plans/v0.5-plan.md), section 9a. Plan: section 4 of that
document; acceptance and the frozen C1 design:
[docs/plans/v0.5-acceptance.md](../../docs/plans/v0.5-acceptance.md), section C1; the acceptance
run and the roles: [docs/validation/v0.5/acceptance/README.md](../../docs/validation/v0.5/acceptance/README.md).

Nothing in v0.5 is a validated method: every report carries `method_status: not_validated`.
Verdicts use the discovery family only (SURVIVED, WEAKENED, REFUTED, INCONCLUSIVE); never
"confirmed", "discovery" or "TRUE".

## 0. What the lock covers, and the freeze

Every piece of code this protocol executes lives under `src/refute` (`refute.packs.tess.calib05`:
`values.py`, `plans.py`, `c1.py`, `c2.py`, `c3select.py`, `c3run.py`, `runner.py`, `steps.py`;
and the v0.4 and v0.5 modules they call), inside the code hash of the lock (`refute-code-1`:
every file under `src/`, plus `pyproject.toml` and `uv.lock`).
`calibration/v0.5/run_calibration.py` only parses its arguments and calls `steps.py`,
`c3select.py` and `c3run.py`. The values of this protocol are code in `calib05/values.py`;
section 11 states them, and `tests/test_v05_calibration.py` checks that the two agree.

**The freeze.** This protocol's commit carries the analysis code, the frozen inputs and
`inputs.json` (each source's URL, retrieval time, size and SHA-256, and the code hash of the tree
that froze them). It is **the designated freeze commit**: the one commit that added both this file
and `inputs.json` (`c3select.freeze_commit`); no other commit, even with the same bytes, stands
for it. After this commit, nothing in `src/`, `pyproject.toml`, `uv.lock`, the snapshots or this
protocol changes; a change voids the C3 selection and goes back to the maintainer. Every later
step first checks the freeze (`steps.frozen_code`): the designated freeze commit, every bound path
(`c3select.BOUND_PATHS`: the code, this protocol, the inputs, the files of the known targets, and
the v0.4 records the calibration reads: its claim, lock, catalogs and `runs/`) equal to that
commit's bytes, and the tree's code hash equal to the one that commit's `inputs.json` records; the
lock at S4 must carry it. No dependency change is planned.

## 1. The battery under test

Two batteries attack the **same candidate** of each curve (`discover/paired.py`,
`calib05/plans.py`): the v0.4 compatibility battery (the v0.4 claim's plan, unchanged) and the
v0.5 battery (the same plan with discovery version 2, the `stronger` section at its defaults, and
these roles; the two plans share every parameter of the candidate generation,
`paired.check_pairing`):

| Test | Severity | Role in v0.5 | Basis |
|---|---|---|---|
| `snr` | gate | decisive (the gate) | unchanged |
| `odd_even` (v0.5 rule, group means) | fatal | decisive | acceptance 1.8 a, b, c |
| two-sided phase-0.5 check (`secondary_eclipse`) | warning | decisive | 1.8, 3.1, 3.2 |
| `sinusoid` | warning | decisive | 1.8 a, b; 3.8 |
| `duty_cycle` | fatal or warning | decisive | 3.7 (suite) |
| `edge_events` | warning | decisive | 1.8 a, b; 2.5; 2.6 |
| `aperture_depth` | fatal | decisive | 1.8 a, b, c |
| `systematics` | warning | decisive | 1.8 a, b, c |
| `period_alias` | fatal | decisive | 1.11 (its sensitivity simulation is white-noise only) |
| `plausibility`, `nearby_contamination`, `eb_catalog` | as v0.4 | decisive | categories (WP1) |
| `single_event` | fatal | diagnostic | 1.8-b failed; 1.10 failed in correlated noise |
| `event_consistency` | fatal | diagnostic | 2.1, 1.8-c, 2.7 failed in correlated noise; 1.10 |
| `centroid_shift` (in a v0.5 plan: the per-sector centroid) | fatal | diagnostic | 4.1, 4.5 INVALID: not accepted |
| `holdout_by_year` | not aggregated | diagnostic (required) | unchanged |

**No decisive centroid test in the v0.5 battery** (the S2 decision, option (a)). The v0.4 arm
keeps the v0.4 `centroid_shift`. Cost: the v0.5 battery is weaker against contamination by a
neighbouring star; `aperture_depth` covers only part of it (a source inside the larger
aperture). C1's D5 measures the remaining decisive tests and may fail; a PASS of D5 would not show
that the per-sector centroid was accepted. The per-sector centroid is left to a future phase
(#200).

**Case 8.3** is accepted as a library check (`verify_promotion_records`), not wired end to end:
v0.5 has no promotion step; item 4 of #195 stays open for the next phase with a promotion step.

## 2. Randomness

drand mainnet, default chain (`refute.drand`; chain hash
`8990e7a9aaed2ffed73dbd7092123d6f289930540d7651336225dc172e51b2ce`, period 30 s, BLS signature
verified). Each round is the first published at least 1 hour after the creation time of **the CI
push run** of a given commit: the run of workflow `ci.yml` with event `push`, `head_sha` equal to
that commit and `run_attempt` 1, read from the GitHub API (`discover.pilot.push_run_created_at`,
`refute.drand.round_after`); no such run, or more than one, stops the step. A commit of only
`docs/**/*.md` has no push run, so each of these commits carries a file outside that filter. drand
unavailable or a signature that fails: the step stops and the maintainer decides.

| Round | Fixed by the CI push run of | Seeds |
|---|---|---|
| R_c3 | this protocol's commit (the freeze) | each C3 pool's order: `int(sha256(randomness_hex + "|v0.5|c3|<label>"), 16)`, labels `planet-pool` and `eb-fp-pool`, the pool sorted by TIC ID then shuffled (`refute.drand.shuffled`) |
| R_c1 | the lock's commit B (S4) | C1 confirmation: `int(SHA-256(randomness_hex + "refute-v05-c1:<family>:<i>")[:16], 16)` (`calib05.c1.confirmation_seed`) |

R_c1 comes after the lock, so no confirmation seed is known while the code can change. **Commit B
is authenticated** (`steps.lock_commit_b`): the one commit that added `calibration/v0.5/
claim.lock.json`; its first parent must be the commit the lock records (commit A), the lock's
code hash must be the frozen one, the lock file must be B's bytes, and the C3 claim must verify
against the lock as it is now (`refute.core.lock.verify_claim`: the claim, its attachments and the
code); any other commit is refused. Any change to the code or this
protocol after commit B voids the confirmation designation; no other round ever replaces it (a
later experiment is a separate one, approved first, and the original result is kept). C2 draws nothing new: its transformed curves and injections are regenerated from the v0.4
seeds of R_inj (`calibration/v0.4/runs/r_inj.json`).

## 3. C1, synthetic population (the design frozen in the acceptance document)

- The families, generator, sizes (200 per family, PA and PX 100; 2,400 curves), matching,
  denominators and decision rules D1 to D5 are those of the acceptance document, section C1,
  unchanged. The implementation choices it leaves open are fixed in `calib05/c1.py` (its module
  docstring): sector numbers `j + 1`; the parameters from `default_rng(seed)`, the white noise from
  `default_rng([seed, 2])`, the correlated noise from `default_rng([seed, 3])`; sinusoids and edge
  ramps additive, the trend multiplicative; PA's artifact in the pixels only; PX by
  `synthetic.make_blend_sky` (the neighbor at a fixed sky offset), its trend applied to the light
  curve and to the PDCSAP and SAP series, not to the pixels. **PX's noise streams are an
  exception:** `make_blend_sky` draws the white noise from `make_lightcurve`'s own
  `default_rng(seed)`, the correlated noise from `default_rng([seed, 1])`, and the pixel and
  auxiliary noise from another `default_rng(seed)`.
- Both batteries at stage 2 (the full battery), no catalog test (no TIC), the star of the
  acceptance document (`synthetic.make_star`).
- **Cost rule:** before the confirmation run, the first 20 development seeds of each family
  (`int(SHA-256("refute-v05-c1-dev:<family>:<i>")[:16], 16)`) run (`run_calibration.py
  c1-prefix`); the projected processor-hours are the mean CPU time per curve of each family times
  its size. Above 30 processor-hours, every family's size is halved, by this rule, before the run.
  The confirmation recomputes the sizes from the prefix's authenticated records (its run
  manifest: this step, the frozen code, and the function, task identities and tasks' SHA-256 of
  the prefix rebuilt now), never from a report file, and schedules every family and every index.
- **Once:** the confirmation set runs once on the locked code, after R_c1 and after the budget
  decision of section 8 (`c1-confirm`). Before any network access, commit B is authenticated
  (section 2) and an attempt is reserved, its possible beacon exposure recorded before the beacon
  is requested; any attempt after the first needs the URL of its approval. A
  generation failure is recorded with its seed and reason and never redrawn. Every metric is
  reported, pass or fail; no rule blocks the phase; a failed rule leads to no rerun and no
  retuning (plan, section 7.4).

## 4. C2, real data, paired, light-curve tests (a reused benchmark)

- **Stars:** the v0.4 funnel's 100 stars (`calibration/v0.4/runs/funnel_run_set.json`), stage 1
  only (no pixel file), with the v0.4 claim's catalogs.
- **Inputs:** downloaded again into a new cache (`c2-fetch`) and checked against the SHA-256 of
  each star's v0.4 stage-1 dossier (`data/manifest.json`). A star with a changed, missing or new
  file is "input changed": it stays in the cohort of 100, counted apart with its problems, and is
  not run in the paired comparison (its v0.4 records describe other bytes); every C2 result is
  stated as conditional on the authenticated available inputs. Never replaced.
- **Candidates:** the v0.4 detrending, prewhitening and search, run once per curve; both batteries
  attack that candidate.
- **Compatibility (required infrastructure, plan section 3):** the v0.4 battery's outcome of every
  curve must equal its v0.4 record: the stage-1 dossier for an original curve (the candidate's
  period, epoch and SNR; each test's status and emitted severity, the holdout left out; the
  verdict), and the measurement record for a transformed or injected curve (the chain's fields,
  the injection and its recovery). Strings exactly, numbers within a relative 1e-9. **Any mismatch
  blocks C2**: it is recorded, no target is evaluated, and no curve is excluded to obtain a passing
  comparison; the maintainer decides.
- **The v0.4 references are authenticated before any use** (`c2.reference_problems`): the
  stage-1 dossiers in `.cache/v04/pilot/stage1/funnel-s1` must be exactly the stars of the
  committed `calibration/v0.4/runs/stage1/seals.json`, each dossier's sealed core (its
  `verdict.json` and `data/manifest.json` included) must have the SHA-256 recorded there, and
  `.cache/v04/pilot/measure/funnel/measurements.jsonl` must have the SHA-256 recorded in
  `calibration/v0.4/runs/stage1/records.json`; both records are bound paths of the freeze. A
  missing, unexpected or different file refuses every C2 step.
- **Prefix:** the first 3 authenticated stars of the run set run first (`c2-prefix`: the original,
  the 3 transformed and the first 10 injected curves each; an injection's draw does not depend on
  the number per curve): their compatibility, and the CPU time per task kind for the budget of
  section 8. Their compatibility must be established before the budget and before any further
  dispatch. The prefix's authenticated records are part of the full comparison: `c2-run`
  schedules only the remaining curves, and the prefix and the run together must be exactly the
  scheduled curves.
- **Transformed curves:** 3 per star (1 inverted, 2 per-sector rotations), regenerated from the
  v0.4 seeds; inverted and rotated reported apart; signal-bearing and original-gate-negative hosts
  reported apart. Neither is a validated null.
- **Injections:** the v0.4 grid (20 per curve, or 10 by the budget rule of section 8) on every
  authenticated star, as v0.4 ran them, so each has its compatibility record; the 87
  original-gate-negative hosts and the signal-bearing hosts are reported apart, never pooled (the
  latter measure competition, not sensitivity). Per battery: survival among recovered gate-passing
  injections (the conditional cost) and recovery-and-survival among all attempted injections.
- **Summaries:** all authenticated stars (the historical comparison) and the prespecified subset
  without the three promoted stars of v0.4 (the development cases,
  `calibration/v0.4/runs/promotion.json`); the subset's v0.4 baseline is measured by the
  compatibility battery, never taken from the historical 17 of 64.
- **Targets** (each PASS, FAIL or NOT DECIDABLE below 20 in its denominator; none blocks the
  phase; none is evaluated while compatibility is not established):
  - T2a. Injections into original-gate-negative hosts, conditional cost: the v0.5 survival
    (SURVIVED or WEAKENED at stage 1) among recovered gate-passing injections at least the
    compatibility battery's minus 0.10, on the same injections.
  - T2b. Transformed curves: the v0.5 count of gate-passing detections that survive the stage's
    decisive tests not above the compatibility battery's, inverted and rotated separately.
  - T2c. Original curves, subset: the v0.5 SURVIVED count (stage 1) not above the compatibility
    battery's.

## 5. C3, real controls, full battery, newly drawn (a feasibility sample)

- **Size:** 8 confirmed planets and 8 known false positives, each with its source and retrieval
  date. About 8 + 8 is a feasibility sample, not a class-wise validation.
- **One false-positive class** (the S2 decision): the 8 false positives are eclipsing binaries.
  **Limit:** C3 tests no off-target and no variability false positive (no authoritative source
  for those classes was identified); variability is covered only by the synthetic families of C1
  and by C2; a source for those classes is left to v0.6.
- **Domain:** v0.4's D-1 to D-9 (`calibration/v0.4/PROTOCOL.md`, section 3), with S_max frozen in
  `inputs.json` (section 0); the per-star checks are live MAST and TIC queries during the walk,
  each answer kept.
- **Known targets excluded:** every target of v0.1 to v0.4, development targets included
  (`calib05.c3select.known_targets`: v0.1, v0.2, the v0.2.1 gate-3b planets, and every target of
  the v0.4 claim).
- **Pools** (`calib05.c3select.pools`), each sorted by TIC ID, shuffled by its R_c3 seed and
  walked until 8 + 3 stars are accepted; the first 8 are chosen, the next 3 are the ordered
  reserves; every decision (accepted or rejected, with the first failing rule) is in the ordered
  ledger (`selection/ledger.json`):
  - planets: NASA Exoplanet Archive `pscomppars` rows with `tran_flag = 1`, `sy_pnum = 1`, a TIC,
    `0.5 < pl_orbper < 13 d` and `pl_trandep >= 0.1 %`, one row per TIC (as v0.4);
  - eclipsing-binary false positives: ExoFOP TOI rows with TFOPWG disposition `FP`,
    `0.5 < period < 13 d`, depth at least 1000 ppm, exactly one TOI for the TIC, no `pscomppars`
    planet (as v0.4), **and the TIC in TESS-EB** (the static edition, used privately, never
    redistributed, #33).
- **Signal identity** (H7), decided before any disposition is scored: the planet's found period
  within a relative 0.001 of the published period (aliases not counted); the false positive's at
  one of the factors 1, 2, 0.5 (`calib05.c3run.identity`).
- **The runs:** the C3 claim (`claim.yaml`, written by `run_calibration.py claim` after the
  selection: the v0.4 claim's thresholds, the v0.5 roles, `max_sector` = S_max, the hashes of this
  protocol, the inputs and the selection) is locked at S4; `refute discover` produces the
  dossiers; `run_calibration.py c3-fetch` downloads stage 2 (light curves and pixel files) of
  every chosen control and reserve and records each one's product state; `c3-run` runs both
  batteries on the same candidate for each, at stage 2, **twice: with the claim's catalogs and
  without them**. Why: the pool of the eight false positives is drawn from TESS-EB itself, so a
  catalog test that looks them up in TESS-EB is not evidence of the battery (its own-TIC match is
  a warning, H9a, which alone keeps a control from SURVIVED). The targets read the run without the
  catalog test; both runs are reported; the two must share the search candidate and the final
  candidate of each battery, or the control is an error record.
- **Targets** (feasibility; none blocks the phase), on the v0.5 battery without the catalog test:
  T3a. at most 1 of the 8 planets REFUTED; T3b. at most 2 of the 8 false positives SURVIVED. A
  target can PASS only with all 8 valid, identity-qualified outcomes of its group; otherwise it is
  NOT DECIDABLE, with the errors and the shortage reported apart. The four verdict counts per
  battery, with and without the catalog test, and the paired transitions are always reported, so
  an all-INCONCLUSIVE sample is never described as a successful classification. **Limits:** T3a
  and T3b bound the number of adverse outcomes; both can PASS with eight INCONCLUSIVE outcomes in
  each group, so they do not measure successful classification; removing the catalog test removes
  the lookup circularity, but the false-positive sample stays restricted to catalogued eclipsing
  binaries.
- **Reviews:** the C3 dossiers drawn for review by the rule fixed at S5 (number and cost).
- **Reproduction:** one C3 dossier reproduced in a clean clone from the generated instructions
  (`refute prepare-inputs`, then `refute verify` and the run), identical data hashes and
  `key_values` within 1e-6.

## 6. Replacement rules

- C1: none (generation failures are counted, never redrawn).
- C2: none (an input change is counted apart in the cohort; a compatibility mismatch blocks C2).
- C3 (`calib05.c3run.assign`): a control that fails the signal identity, or whose products are
  missing, is replaced by the next reserve of its pool in order, at most 3 replacements in total
  per pool (the planet pool included); then the pool is short and its target is NOT DECIDABLE. The
  decision reads only the identity and the product state, never a verdict; an error record is not
  a replacement reason (it keeps its place and makes the target NOT DECIDABLE). **Missing
  products** (`c3run.product_state`, from `c3-fetch`) means only: the adapter's
  `NoProductsError` (MAST lists no SPOC 120-s light curve up to S_max), or a fetched manifest that
  is valid (a supported schema; its target; a `files` list; every record with its sector, path,
  SHA-256 and a format the adapter reads: `spoc-fits` or `synthetic-npz` for light curves,
  `spoc-tpf` for pixel files; the SHA-256 of every file it lists) and has no light-curve file or a
  light-curve sector without a pixel file. Any other failure (an invalid manifest, a
  file with other bytes, an unsupported format, a loading failure, a network error) is an error
  state or an error record, never absence. The ordered ledger of every replacement is in the C3
  report; the selection ledger is committed with the selection.
- Transient errors of a selection query: 5 attempts, 120 s apart, then the step stops for the
  maintainer (`discover.selection.walk`). The fetch steps do not retry: a C2 fetch failure stops
  `c2-fetch` before its record is written; a C3 fetch failure is that control's error state.

## 7. Corrupted runs

Frozen before any run (`calib05/runner.py`):

- **Ownership:** every operation that writes to a run folder (a run, a resumption, an attempt's
  reservation) holds an operating-system exclusive lock on its `owner.lock` from its first check
  to its last write (`runner.owned`); the system releases it when the process ends, so a second
  writer is refused while the first lives. Readers take no lock: a run still writing keeps its
  marker and its records are refused.
- **A run folder** is created exclusively before any task is dispatched, with its **manifest**
  (`manifest.json`: the task function, the ordered task identities, the SHA-256 of the tasks'
  content, the provenance: the step, the code hash and the step's inputs such as the round) and a
  marker (`running.marker`) that only the run's normal end removes; a second run into it is
  refused.
- **A task is complete** when its record is appended to `records.jsonl` (then its line in
  `cost.jsonl`; a cost line lost by an interruption between the two writes is restored from the
  record, which holds the same CPU seconds). A task that raises, times out or fails its validation
  is complete as an error record, kept in the denominators with its message, and never rerun.
- **An interruption** is the end of the run process before its normal end: the marker remains and
  the folder's lock is free. Only then may the run resume (`runner.resume`), under the folder's
  lock: the same function, the same tasks and the same provenance as the manifest (identical code,
  inputs and seeds); a run that ended normally and a run another process owns are refused; before
  any write the records are checked (no task twice, no unscheduled task); only the tasks without a
  record run; when every task has its record, the resumption only finalizes (the cost lines
  restored, no task run); the marker is removed only after exact membership and cost coverage are
  checked, and stays on a failure; a task already recorded is never run again. Before the resumption, its approval is recorded in an issue with the reason and the exact
  procedure, and its URL is passed to the resumption.
- **The records of a run are used** only when they are exactly the manifest's tasks, each once,
  each with its cost line, and the run is not marked as unfinished (`runner.all_records`).
- **Steps that read a beacon** (the selection, R_c3; the C1 confirmation, R_c1) reserve a numbered
  attempt folder under their attempts folder's lock before the beacon is requested, recording its
  possible exposure first (`runner.reserve_attempt`); **any attempt after the first needs the URL
  of its approval**. The reservation serializes the allocation of attempts, not whole executions:
  two approved attempts are never run at once by the maintainer's procedure. The selection
  reserves its attempt only once the round is published: the round's number and time come from
  the public creation time of the CI push run (the GitHub API, before the reservation; no
  randomness is read), and the selection is refused until 60 seconds after the round's
  publication time; it holds the attempt's lock while it reads the beacon and walks, and logs
  every domain answer as it comes (`decisions.jsonl`).
- **A defect found in locked code** is reported, and the failed attempt's outputs are kept. A
  repair after the C1 confirmation seeds have been exposed is a separate experiment, declared and
  approved in an issue first, with fresh confirmation randomness; it never replaces the original
  confirmation result.

## 8. Budget and order

Inside the plan's caps: the calibration reserve is 5 agent-days, 100 processor-hours (C1 at most
30 by its rule), 1.5 M reviewer tokens; disk 15 GB.

**The budget decision** (`run_calibration.py budget`, `steps.budget`, written once, before C1's
confirmation and before C2 and C3 run), from the authenticated C1 and C2 prefixes: C1's projected
hours with its sizes (section 3); C2's with 20 and with 10 injections per curve (the remaining
curves at the prefix's mean CPU per task kind, plus the prefix stars' injections 10 to 19 when 20
are used); C3's (every chosen control and reserve, two paired runs each, at the larger of C1's and
C2's mean CPU per curve, doubled for the pixel tests of stage 2); against the reserve minus the
hours the prefixes used. The decision is 20 when C1 + C2 + C3 fit, else 10 when they fit, else
**stop**: nothing runs and the maintainer decides. `c1-confirm`, `c2-run`, `c3-fetch` and `c3-run`
read it and refuse to run without it or on a stop.

Each step is its own commit:

1. This protocol, with the frozen code, the inputs record and the small inputs (fixes R_c3).
2. After R_c3 (S3): `run_calibration.py select --protocol-commit <sha>`, refused unless the
   commit is the designated freeze commit, every bound path is its bytes and the code hash is the
   frozen one; the selection, the ledger and the targets.
3. The C3 claim (`run_calibration.py claim`).
4. S4: lock commit A (code, the code hash frozen in step 1) and commit B (lock), push (fixes R_c1).
5. C1 prefix; C2 fetch and prefix; the budget decision; C1 confirmation; C2 run; C3 fetch,
   dossiers and run; each result committed, raw outputs above 5 MB archived to the Drive with a
   checked SHA-256 manifest.
6. S5 reviews; then the gate and S6.

Any rerun needs its approval recorded in an issue before it runs.

## 9. Sources

| Use | Source |
|---|---|
| S_max | the TESS two-minute target lists page `https://tess.mit.edu/public/target_lists/target_lists.html` (its highest listed sector) and MAST `Observations.query_criteria_count` (SPOC, timeseries, `t_exptime` in [119.5, 120.5] s, by sector), as v0.4 |
| Planet pool | NASA Exoplanet Archive TAP, `pscomppars` (the v0.4 query) |
| False-positive pool | ExoFOP-TESS TOI table (`download_toi.php`); TESS-EB, the static edition obtained on 2026-10-18 (VizieR `J/ApJS/258/16/tess-ebs`; not redistributed, #33) |
| Catalog attachments of the C3 claim | TESS-EB as above; Gaia DR3 EB, the v0.2.0 release asset (checked against its SHA-256 and row count) |
| Domain | MAST through `lightkurve` listings and the TIC via `astroquery`, live during the walk |
| C2 data | MAST, SPOC 120-s light curves, checked against the v0.4 dossiers |

Each file's URL, retrieval time, size and SHA-256 are in `inputs.json`. Data credits and license
statements are written with their `sources/` records before any publication (CLAUDE.md); this file
makes none.

## 10. What this calibration does not show

C2 is a reused benchmark (these stars' failures shaped the new tests), not an independent
confirmation; transformed curves are not a validated null and their counts are not a false-alarm
rate; C3 is a feasibility sample of two classes; C1 is synthetic. The calibration cannot validate
the method: `method_status` stays `not_validated`.

## 11. The values (checked against `refute.packs.tess.calib05.values`)

```yaml
c3: {planets: 8, false_positives: 8, reserves: 3, period_min_days: 0.5, period_max_days: 13.0,
     planet_min_depth_percent: 0.1, fp_min_depth_ppm: 1000.0, identity_period_tolerance: 0.001,
     fp_identity_factors: [1.0, 2.0, 0.5], max_planets_refuted: 1, max_fp_survived: 2,
     retry_attempts: 5, retry_backoff_seconds: 120.0}
c1: {sizes: {P: 200, PG: 200, PV: 200, PA: 100, EB1: 200, EB2: 200, V1: 200, V2: 200, SE: 200,
             ER: 200, NW: 200, NR: 200, PX: 100},
     development_prefix: 20, max_processor_hours: 30.0, not_decidable_below: 20,
     seed_prefix: refute-v05-c1}
c2: {stars: 100, injections_per_curve: 20, injections_fallback: 10, transformed_per_star: 3,
     float_rel_tolerance: 1.0e-09, not_decidable_below: 20, t2a_margin: 0.1}
budget: {reserve_processor_hours: 100.0, reserve_agent_days: 5.0,
         reserve_reviewer_tokens: 1500000, disk_bytes: 15000000000}
roles: {decisive: [snr, odd_even, secondary_eclipse, plausibility, aperture_depth,
                   nearby_contamination, period_alias, systematics, eb_catalog, edge_events,
                   sinusoid, duty_cycle],
        diagnostic: [holdout_by_year, single_event, event_consistency, centroid_shift]}
```
