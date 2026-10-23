# v0.2.1 synthetic population study: criteria, population and protocol

Status: **approved for commit.** Written 2026-10-11 on branch
`claude/v0-2-1-gauntlet-fixes-13f5e7`, before any population was generated or
measured. The criteria, the sample sizes and the choices below were decided by the
maintainer on 2026-10-11. No harness, population or measurement exists yet; none is
written or run before this document is committed.

## Purpose

The roadmap requires a synthetic population study (ROADMAP.md, v0.2.1, Exit criteria: "A
synthetic population study with known truth measures, before and after each change, the
rate of refuted planets, the rate of flagged false positives, the false-alarm rate on
noise-only light curves (white and correlated) and the INCONCLUSIVE fraction; its
metrics and acceptance limits are committed before it runs.").

Synthetic scenes are idealized (ROADMAP.md, v0.2.1, Scope: "Synthetic scenes are
idealized: synthetic numbers compare engine versions and test known mechanisms; they
set no bounds for real data."). The study is a scientific validation separate from the
usual CI: it is never part of the test suite.

## 1. Approval criteria

**Rule.** Every criterion uses a one-sided 95% exact Clopper-Pearson bound on the
observed proportion: the upper bound for rates that must be low, the lower bound for
the flagged rate.

**Criteria**, each evaluated on the confirmation population, separately for white and
correlated noise, under catalog condition (i) unless stated. **No case leaves a
denominator** because its period was not found, its analysis was inconclusive or it
ended in an error.

| Criterion | Numerator | Denominator | Limit |
|---|---|---|---|
| C1. Refuted-planet rate | planets whose final verdict is REFUTED | every planet of that SNR band and noise model (each band separately) | upper bound <= 0.10 |
| C2. Flagged-false-positive rate | false positives whose verdict, recomputed without `eb_catalog`, is REFUTED **and** that satisfy signal identity | every measurable false positive of that noise model | lower bound >= 0.60; the other bands are published without a limit |
| C3. INCONCLUSIVE fraction | cases whose final verdict is INCONCLUSIVE, analysis errors included | every case of the class (planets, false positives, separately) in the measurable band of that noise model | upper bound <= 0.20 |
| C4. False-alarm rate | cases whose final verdict is SURVIVED or WEAKENED | every case of the "no injected transit" group of that noise model | upper bound <= 0.01 (white), <= 0.05 (correlated) |
| C5. H9(a) | planets REFUTED exclusively by an own-TIC match in a same-photometry catalog | planets with such a row, catalog condition (ii) | zero |
| C6. Analysis errors | - | every set | they stay in the denominators, are published separately, and block the approval of the confirmation while any is unresolved |

**Signal identity** (C2): there is `f` in {1, 2, 1/2} such that
`|P_analyzed - f * P_injected| / (f * P_injected) <= 0.001`, where `P_analyzed` is the
period of the final candidate of the analysis. A case without a candidate does not
satisfy it.

"REFUTED exclusively by an own-TIC match" (C5) means: verdict REFUTED, `eb_catalog` is
the only fatal failure, and every catalog match with a compatible period is under the
target's own TIC in a catalog listed in `same_photometry_catalogs`.

**What the numbers are.** 0.10, 0.60, 0.01, 0.05 and 0.20 are engineering anchors for
this synthetic population, not limits demonstrated for real data. 0.10 and 0.60 repeat
the rates of the v0.1 and v0.2 calibration claims (at most 1 of 10 planets refuted, at
least 6 of 10 false positives flagged), but the requirement here is stricter: those
claims compared a point estimate on 10 targets with the limit; here the 95% confidence
bound must clear it.

**C4 limits the defined mixture**, not each subgroup. With 2200 white-noise curves the
criterion admits at most 14 false alarms. If the other subgroups have zero, 14 among the
660 curves with variability (2.12%) still pass, and 15 (2.27%) fail. C4 does not show
a rate <= 1% in each subgroup; the subgroup rates are published.

## 2. Sample sizes and power (checked by script)

Sizing rule: at least an 80% chance of passing **per criterion**, at the reference rates
declared here. The reference rates are design assumptions, not measurements.

| Criterion | n per set evaluated | Passes with | Reference rate | Chance of passing |
|---|---|---|---|---|
| C1. Refuted planets <= 0.10 | 250 per band and noise model | at most 16 (upper bound 0.0956; 17 gives 0.1003) | 0.05 | 87.5% |
| C2. Flagged >= 0.60 | 250 per noise model, measurable band | at least 164 (lower bound 0.6034; 163 gives 0.5993) | 0.70 | 94.2% |
| C3. INCONCLUSIVE <= 0.20 | 250 per class and noise model, measurable band | at most 39 (upper bound 0.1988; 40 gives 0.2031) | 0.10 | 99.8% |
| C3, sensitivity | same | same | 0.13 / 0.14 | 90.4% / 79.6% |
| C4. False alarm, white <= 0.01 | 2200 | at most 14 (upper bound 0.0099; 15 gives 0.0105) | 0.005 | 85.5% |
| C4. False alarm, correlated <= 0.05 | 600 | at most 20 (upper bound 0.0481; 21 gives 0.0500) | 0.025 | 92.0% |

**A reference calculation, not the power of the study.** If ten independent criteria
(C1 in 6 sets, C2 in 2, C4 in 2) all had true rates exactly at their references, the
chance that all ten pass would be 0.875^6 x 0.942^2 x 0.855 x 0.920 = **31.3%**. "80% per
criterion" is not 80% for the whole study. Multiplying in the four C3 criteria (31.1% at
0.10; 20.9% at 0.13; 12.6% at 0.14) does **not** give a demonstrated joint probability,
for two reasons: C3 reuses the light curves of C1 and C2, so the criteria are not
independent; and the fixed quotas of mechanisms with different rates do not follow a
single homogeneous binomial. C5 and C6 are not probabilistic. Both catalog conditions
reuse the same light curves: condition (ii) adds analyses, not independent observations.

## 3. SNR bands

Every planet and false positive belongs to one band, computed from the injected truth,
never from Refute's output. The thresholds are the code defaults
`SnrParams.min_snr = 7.1` (the SNR gate of the full analysis) and
`HoldoutParams.min_snr = 5.0` (the hidden-year test), in
`src/refute/packs/tess/params.py`, the same at every measurement point.

For a light curve, the expected SNRs are:

- `SNR_global`, over all its data, against 7.1;
- `SNR_train(y)`, over all data except year `y`, for each year `y` with data (each is
  hidden by one holdout round), against 7.1;
- `SNR_hidden(y)`, over year `y` only, for each such year, against 5.0.

Let `r` be the smallest of the ratios `SNR / threshold`. **Measurable** if `r >= 1.5`;
**below threshold** if `r < 1.0`; **near threshold** otherwise.

**Expected SNR.** For a set of observed cadences, with `I_t` the observed cadences
within half a duration of the center of transit `t`:

- `d` = the mean injected deficit over all cadences in the `I_t`, from the noiseless
  light curve of the target (for a trapezoid, the mean of `1 - model`, not the maximum
  depth; for a blend, the deficit after dilution and crowding correction);
- `SNR = d / sqrt(V)`, with `V` the variance of the mean flux over the in-transit
  cadences under the noise model:
  - **white** (standard deviation `s` per cadence): `V = s^2 / N`, `N` the number of
    in-transit cadences, so `SNR = d sqrt(N) / s`;
  - **correlated** (white `s` plus a stationary AR(1) with standard deviation `a` and
    lag-one correlation `phi = exp(-cadence / tau)`): within a transit of `m` cadences
    the sum of all covariances is `S_t = s^2 m + a^2 (m + 2 sum_{k=1}^{m-1} (m - k) phi^k)`,
    the exact AR(1) covariance applied to the in-transit cadences; transits are
    separated by much more than `tau`, so `V = (sum_t S_t) / N^2`.
- The out-of-transit baseline term is left out: it is measured on more cadences and
  adds little.

The expected SNR is computed **under the chosen noise model**. It does not include all
the difficulty created by stellar variability, trends or blends, and it does not
guarantee that Refute can measure the signal: it only places the case in a band.

Numerical check (2026-10-11, scratch script, not part of the study): one 2.5-hour
transit at 2-minute cadence (`m = 75`), `s = a = 600 ppm`, `tau = 1 h`
(`phi = 0.96722`): the formula gives a variance of the mean of `1.8709e-07`; simulated
AR(1) plus white noise gives 1.8684e-07, 1.8747e-07 and 1.8678e-07 with three seeds of
400,000 trials each (ratios 0.9987, 1.0020 and 0.9983; sampling uncertainty of a ratio
about 0.002). For 12 such transits at 2000 ppm the expected SNR is 100.0 with white
noise only and 16.0 with the AR(1) added. (A first check with 20,000 trials gave a
ratio of 1.027, about 2.7 times its sampling uncertainty; the larger runs replace it.)

**Stratified generation.** All expected SNRs of a light curve scale with its depth,
`SNR_k = depth x c_k`, where `c_k` follows from its geometry and noise model. For each
case the generator draws a target ratio `r` in its band (below: uniform in [0.5, 1.0);
near: uniform in [1.0, 1.5); measurable: log-uniform in [1.5, 6.0]) and sets
`depth = r / min_k(c_k / threshold_k)`. The depth comes from `r`; no other depth range is
imposed. Each band receives exactly its number of cases, deterministically from the
seeds.

## 4. Population

### 4.1 Classes, sizes and noise

| Class | Below threshold | Near threshold | Measurable |
|---|---|---|---|
| Planets | 250 | 250 | 250 |
| False positives | 100 (descriptive only) | 100 (descriptive only) | 250 |
| No injected transit | 2200 (white), 600 (correlated), without bands |

Per noise model. **White:** Gaussian, 600 ppm per 2-minute cadence. **Correlated:** the
same white noise plus a stationary AR(1) with a 1-hour correlation time and 600 ppm
standard deviation, started from its stationary distribution in each sector; the
parameters of the H3 measurement (`docs/validation/v0.2.1/H3/measure.py`, the `red`
noise; `docs/validation/v0.2.1/H3-acceptance.md`, section "Noise"). The H3 measurement
does not justify these values empirically: they were a protocol choice there and are
reused here as a choice, for comparability. Every light curve except the pure-noise
subgroup has the usual slow trend (0.2% sinusoid, 6-day period).

### 4.2 Common geometry

- **Cadence and sectors:** 2-minute cadence; each sector is two 13-day orbits separated
  by a 1-day gap (`sector_times` of the v0.2.0 generator). Sector starts (BTJD): 1325.0
  (2018), 1700.0 (2019), 2061.0 (2020), unless a mechanism says otherwise.
- **Star:** the default synthetic star (`make_star`: 1.0 solar radius, 1.0 solar mass,
  TIC 1, at RA 150.0, Dec -30.0).
- **Phase:** the first transit or eclipse time `t0` is uniform in one period after the
  first cadence.
- **Shape:** a trapezoid (`signal_model`), with the ingress fraction given per class.
- **Pixel data:** an 11 x 11 pixel scene with Gaussian PSFs (`Scene`,
  `render_pixels`), 21 arcsec per pixel, target at the center, rendered from the
  target's light curve (`make_aux`), so the battery runs as in the test suite.

### 4.3 Planets (250 per band and noise model)

- **Period** uniform in [1.5, 5.5] d. **Impact parameter** uniform in [0, 0.7].
  **Duration** of a circular orbit around the star: `T14 = (P / pi) asin((R*/a)
  sqrt((1 + k)^2 - b^2))`, with `k = sqrt(depth)` and `a` from Kepler's third law,
  solved together with the depth by fixed-point iteration (three passes), clipped to
  [1, 4] h. **Ingress fraction** `k / (1 - b^2)`, clipped to [0.05, 0.5].
- **Mechanisms**, assigned by the index `i` of the case in its set (0 to 249):
  - `i` 0-99 (40%): two observing years (2018, 2020), plain.
  - `i` 100-149 (20%): three observing years (2018, 2019, 2020).
  - `i` 150-199 (20%), **few training times and different distances to the hidden
    year** (H3/H3b): the train is one 13-day orbit starting at 1325.0 (2018) holding
    exactly **3 or 4 transits** (alternating by index), obtained by drawing the period in
    [3.0, 5.5] d and the phase until the count matches (each attempt is a redraw, see
    4.6); the other year is one full sector starting 1, 2 or 3 years later (BTJD
    1690.25, 2055.5 or 2420.75; assigned 17, 17 and 16 cases in that order).
  - `i` 200-249 (20%), **variability restricted to some years** (H4): three observing
    years; a sinusoid of period uniform in [0.3, 1.0] d and amplitude uniform in 2 to 4
    times the transit depth, present in two of the three years (the absent year drawn
    uniformly).

### 4.4 False positives (250 measurable, 100 per other band, per noise model)

Four mechanisms, assigned by index in that order: of 250, `i` 0-62 secondary, 63-125
odd/even, 126-187 blend, 188-249 variability (63, 63, 62, 62); of 100, 25 each in the
same order. The period that counts as catalogued is the injected orbital period of the
eclipsing system.

- **Eclipsing binary with a secondary eclipse:** period uniform in [1.0, 5.5] d;
  duration uniform in [1.5, 4] h; ingress fraction uniform in [0.2, 0.5]; secondary
  depth 20% to 40% of the primary, at phase 0.5.
- **Unequal odd and even eclipses:** same period, duration and ingress ranges; odd
  eclipses at 0.6 to 0.85 times the even depth.
- **Neighbor blend:** the eclipse is on a neighbor; scene as in `make_blend` (the pixel
  rendering and the crowding-corrected aperture photometry of the v0.2.0 generator),
  with the population's noise models instead of `make_blend`'s 300 ppm default. The
  neighbor is 1.5 to 4 pixels (31.5 to 84 arcsec) from the target at a uniform angle,
  with a flux ratio uniform in [0.1, 0.5]; its eclipse period uniform in [1.0, 5.5] d,
  duration uniform in [1.5, 4] h, ingress fraction 0.15. The neighbor's eclipse depth
  is the one that gives the drawn deficit `d` on the target after dilution.
- **Catalogued eclipse hidden by stronger variability** (H7): an eclipse as in the
  first mechanism (without secondary), plus a sinusoid of period uniform in [0.3, 1.0] d,
  redrawn while the ratio of the two periods is within 0.01 of a fraction `p/q` with
  `q <= 4`, and amplitude uniform in 2 to 4 times the eclipse depth.

### 4.5 No injected transit (2200 white, 600 correlated)

A challenge mixture defined before any measurement, two observing years (2018, 2020),
assigned by index in this order: pure noise without trend, 40% (880 / 240); noise with
the slow trend, 30% (660 / 180); noise with the slow trend and stellar variability (a
sinusoid of period uniform in [0.3, 5] d and amplitude uniform in [1000, 4000] ppm), 30%
(660 / 180).

### 4.6 Physical limits and redraws (fixed before generation)

Limits per class: a planet's transit depth at most 0.03 (a planet of about 1.7 Jupiter
radii around the 1-solar-radius star); an eclipsing binary's primary eclipse depth at
most 0.5; a blended neighbor's own eclipse depth at most 1.0 (100%). A case whose
depth, derived from `r`, falls outside its limit, or whose mechanism condition cannot be
met (the transit count of 4.3, the non-commensurate period of 4.4), is drawn again,
deterministically, from the sub-seed `SHA-256(<seed>|redraw|k)`, `k = 1, 2, ...`; the
values drawn again are all the random parameters of the case except its class, band,
noise model, mechanism and index. The number of redraws is counted and published by
class, band and mechanism.

### 4.7 Catalog condition (ii) (H9(a))

Every planet and false positive is analyzed a second time with a synthetic catalog of
one row, assigned by the index `i` of the case: `i mod 5` in {0, 1, 2} (60%): TESS-EB, a
same-photometry catalog, under the target's own TIC, at the target's position and the
injected period; `i mod 5 = 3` (20%, control): TESS-EB, under a neighbor's TIC (2), 5 to
20 arcsec from the target at a uniform angle, at the injected period; `i mod 5 = 4` (20%,
control): an independent catalog (`Gaia-DR3-EB`, no TIC), 0 to 2 arcsec from the target,
at the injected period. The match radius is the code default
(`EbCatalogParams.match_radius_arcsec = 21.0`), and the scan record declares an
extraction radius of 120 arcsec around the target.

### 4.8 Results by mechanism

Published with counts and confidence bounds. They are descriptive, not binding, with
one rule: every family whose point estimate is worse than the limit of its criterion is
named in the report and discussed.

## 5. Seeds: development and confirmation

- **Development population.** Case `i` of class `c`, band `b`, noise model `n` uses
  the seed `SHA-256("refute-v0.2.1-population-dev|c|b|n|i")`, first 8 bytes as an
  unsigned integer. These seeds are fixed now and are distinct from the test-suite seeds
  (0-9) and the H3 seeds (0-59).
- **Confirmation population.** Same sizes, bands, mechanisms and rules, with seeds
  `SHA-256(randomness|c|b|n|i)` from the randomness of a **future drand round**, whose
  number is committed before the round is published. It runs **once, at the end, on
  frozen code**, and only its result counts as validation (ROADMAP.md, v0.2.1, Exit
  criteria: "the confirmation set, with seeds derived from a future drand round, runs
  once, at the end, on frozen code, and only its result counts as validation").

## 6. The same metric across versions

- **Flagged, as defined by the v0.2 claim** (`calibration/v0.2/self_claim.yaml`,
  `definitions.flagged`): "A known false positive whose verdict, recomputed without
  eb_catalog (pass_criteria.flag_excluded_tests) by the same deterministic rules, is
  REFUTED." Recovery uses the relative tolerance of `definitions.recovered`:
  "|P_found - P_published| / P_published <= 0.001".
- **Main comparison: flagged with signal identity** (C2), computed by the harness at
  every measurement point, M0 included. The verdict without `eb_catalog` comes from
  `refute.packs.tess.calibration.signal_verdict` of the code being measured (the same
  deterministic rules of that version); the signal identity of section 1 is computed by
  the harness itself, with the same code at every point.
- **The old definition** (without identity) is published as a separate diagnostic.
- **Paired comparisons.** Consecutive points use the same light curves. An exact paired
  (McNemar) test compares outcomes only under the same definition. Each comparison also
  publishes the difference of the rates and the pairs that changed, in each direction.
  A non-significant test does not show that there was no regression.

## 7. Identical inputs and the harness

- The population is generated **once** (light curves, sector metadata, star
  parameters, pixel data, injected truth, band, mechanism and redraw counts), with a
  `SHA256SUMS` file. Every measurement point reads the same inputs and records the
  SHA-256 of every input it read.
- **Generator:** runs once, with the harness and the helpers of
  `refute.packs.tess.synthetic` at tag `v0.2.0` (commit `f479823`): `SignalSpec`,
  `signal_model`, `sector_times`, `make_star`, `Scene`, `render_pixels`, `crowding`,
  `scene_aperture`, `make_sector_aux`, `make_aux`, `make_data`. It records that commit
  and the SHA-256 of `synthetic.py`. It does not need to exist at the other commits.
- **Reader and analysis path:** must run unchanged at `f479823`, `3217db7`, `78d79f5`,
  `9d3f369` and `a3f66c4`. It uses only: the data classes of
  `refute.packs.tess.types` (`SectorInfo`, `StarInfo`, `ProductInfo`, `LightCurveData`,
  `SectorAux`, `PixelData`, `Neighbor`, `AuxData`, `TessData`, `Candidate`);
  `refute.packs.tess.params.TessTestPlan`; `refute.packs.tess.pipeline.analyze_data`,
  `build_result`, `Analysis` and `GauntletOutcome`;
  `refute.packs.tess.calibration.signal_verdict`;
  `refute.packs.tess.ebcatalog.parse_catalog`, `COLUMNS` and the scan record format
  (`format`, `radius_arcsec`, `snapshots`, `per_target`); `refute.core.verdict`
  (`TestResult`, `TestStatus`, `Severity`); `refute.core.runner.run_processes`;
  `refute.core.io.dumps_json`. A check of 2026-10-11 (scratch script parsing each file at
  each commit with `ast`) found the same signature or fields for every one of them at
  all five commits.
- The harness does **not** use `pipeline.matching_factor` (absent at `f479823`) or
  `pipeline.conclude_analysis` (present only from `a3f66c4`); signal identity is its own
  code.
- **Analysis plan.** Every point uses the fast plan of the test suite, written in the
  harness (`{"search": {"period_max_days": 6.0, "durations_hours": [1.0, 2.0, 3.0,
  4.0]}}`, equal to `FAST_SEARCH` at every point), with every other default of the code
  being measured, and records the resolved plan (`TessTestPlan.model_dump`). The
  calibration claims search 0.5 to 20 days with durations 0.5 to 8 hours
  (`calibration/v0.2/self_claim.yaml`, `test_plan.search`). The population's periods
  (up to 5.5 days) and durations (up to 4 hours) fit inside the fast plan; it offers
  fewer periods and durations for spurious peaks than the calibration plan, so
  false-alarm rates under the calibration plan could be higher. Every report says so.
- **Size of the inputs** (estimate of 2026-10-11, from one existing test scenario held in
  memory): a two-sector case is about 1.5 MB of light curve and 73 MB of pixel data
  (pixel flux and errors, float64; the pixel flux compresses to about 35 MB), a
  three-sector case about 110 MB. The 5200 cases would take roughly 400 GB uncompressed,
  about 200 GB compressed, and the light curves alone about 8 GB. Where the inputs are
  kept (stored, or regenerated deterministically and checked by hash) is decided before
  generation, by an amendment to this document.

## 8. Measurement points and written hypotheses

M0 to M3 are **retrospective development measurements**: the code of those commits was
written and committed on 2026-10-10, before this document. Each result file records the
date and time of its measurement. The hypotheses below are written before measuring; a
prediction that turns out wrong is reported as found.

| Point | Code |
|---|---|
| M0 | `f479823` (tag `v0.2.0`); its `src/` differs from the branch point `3dec26f` only in the version string |
| M1 | `3217db7` (H7) |
| M2 | `78d79f5` (H4, with H7) |
| M3 | `9d3f369` (H9(a), with H7 and H4) |
| M4 and later | each future change, with its hypothesis written before its measurement |

**M1 (H7).** Hypothesis to check: per-target verdicts identical to M0, and every
metric of section 1 identical to M0. Mechanism: H7 changes only the calibration's count
of flagged false positives (`flag_requires_signal_recovery`, off by default); the
analysis is not touched, and C2 is computed by the harness.

**M2 (H4)**, against M1. In the code of `78d79f5`, a round whose train candidate is
invalid is INCONCLUSIVE before the hidden year is read (`holdout.py`, lines 465-470 and
541-546); `holdout_by_year` is FAIL if any round is FAIL, otherwise PASS if any round is
PASS, otherwise INCONCLUSIVE (`holdout.py`, lines 681-693); H4 only turns rounds into
INCONCLUSIVE, never into FAIL or PASS.

- Refuted-planet rate: equal or lower. A planet refuted by `holdout_by_year` through an
  invalid failing round loses that fatal failure; no new fatal failure can appear.
- INCONCLUSIVE fraction: equal or higher. When every round becomes INCONCLUSIVE the test
  is INCONCLUSIVE, and the verdict is INCONCLUSIVE (`refute/core/verdict.py`, lines
  160-162) unless another test fails fatally; an INCONCLUSIVE test cannot become decided.
- Flagged rate: equal or lower. A false positive flagged only through an invalid failing
  round loses its fatal failure.
- False-alarm rate: direction uncertain. Removing invalid failing rounds may expose
  surviving spurious signals; removing invalid passing rounds may instead make them
  inconclusive.

**M3 (H9(a))**, against M2.

- Condition (i): hypothesis to check, every metric identical to M2. Mechanism: without
  catalogs `eb_catalog` does not run, and nothing else changes.
- Condition (ii): own-TIC planets REFUTED only by `eb_catalog` fall to zero. In the code
  of `9d3f369`, an own-TIC match in a same-photometry catalog, with no other compatible
  match, is a FAIL with severity WARNING (`ebcatalog.py`, lines 297-299 and 322-327),
  and any other compatible match stays fatal (lines 309-314). Removing the only fatal
  failure leads to INCONCLUSIVE if an expected test is missing or any test is
  INCONCLUSIVE (`refute/core/verdict.py`, lines 157-162), otherwise to WEAKENED (lines
  163-167). The neighbor and independent-catalog controls stay REFUTED.

## 9. Freezing, failure and new attempts

- **Frozen before the confirmation:** the code, the harness, the generator, the
  analysis plan, these criteria, the development population and the drand round number.
- **If the confirmation fails, the failure is published.** The sample is not enlarged
  and no criterion is changed after seeing the result.
- If the code, the harness, the generation or the plan change after the confirmation
  has been examined: the previous attempt is preserved and published; the new version is
  frozen; a new future drand round is declared; and the new confirmation is identified as
  a new attempt. The engine is never corrected to repeat the same confirmation until it
  passes.
- **Infrastructure interruption:** only the cases still without a result may be resumed,
  with the same input files and the same configuration, checked by hash.

## 10. Where results go

- The harness (`docs/validation/v0.2.1/population/population.py`) is committed before
  the first generation and never edited after it; a change is a new file with a new
  name, and later measurements say which harness they used.
- One new file per measurement:
  `docs/validation/v0.2.1/population/results/<point>-<commit>-<UTC time>.json`, with the
  harness SHA-256, the code commit, the resolved plan, the environment, the SHA-256 of
  every input read, every per-case outcome and the metrics; a `.md` summary next to it.
  A result file is never edited; a correction is a new file.
- These folders are added to `.gitattributes` with `-text` and to the lint exclusions,
  like `pre-document-runs/`.

## 11. Cost

Analyses per measurement point: condition (i), every case: planets 1500, false
positives 900, no injected transit 2800, total 5200; condition (ii), every planet and
false positive again: 2400. **Total 7600.** Without the descriptive false-positive bands
(400 cases, 800 analyses) it would be 6800.

Estimate: the H9(a) test fixture analyzes 265 synthetic light curves in about 105 s on
24 logical processors (about 0.4 s of wall time per analysis), so a point would take
about 50 minutes, plus generation once. The real cost is measured and recorded at M0.
Every run uses the CPU affinity on logical processors 8 to 31.

## 12. Baseline of the test suite

The 225 tests that pass at tag `v0.2.0` are listed in
[`baseline/v0.2.0-passing-tests.txt`](baseline/v0.2.0-passing-tests.txt), with the
command and the JUnit evidence in [`baseline/README.md`](baseline/README.md).

## Still to fix before the v0.2.1 lock

- Where the inputs are kept (section 7), by an amendment before generation.
- The drand round of the confirmation population: its number, committed before the
  round is published.
- The coverage requirement of the calibration.

## Amendment 1 (2026-10-11): inputs are regenerated and checked by hash

Decided by the maintainer on 2026-10-11, after the size estimate of section 7 (roughly
400 GB uncompressed for the development population). It replaces "generated once and
saved" in section 7 by "regenerated and checked by hash". No criterion, size, band,
mechanism, seed rule or limit changes.

**a. Manifest frozen before any measurement.**

- The first generation produces, for every case, the SHA-256 of its canonical
  serialization, its seeds, its final parameters, its expected SNRs and its redraw
  counts, **without analyzing any case** (`population.py generate --no-store`, which
  computes the bytes and their hash without writing them).
- It runs twice, in separate processes; the two manifests must be identical byte for
  byte.
- The manifest is then committed and frozen. Only after that do M0 and the other points
  begin.
- A regeneration that diverges from the manifest stops that case for investigation.
  The expected hash is never updated to accept new bytes, and no case is removed from
  the population.

**b. Canonical representation `refute-population-serialization/1`.** One byte stream
per case, which is both what is hashed and what is written to the cache:

1. the ASCII line `refute-population-serialization/1` followed by LF;
2. the length of the metadata in bytes, as an 8-byte little-endian unsigned integer;
3. the metadata: JSON, UTF-8, keys sorted, no spaces (`separators=(",", ":")`), no
   NaN or infinity, every float written as Python's shortest round-trip representation
   of its binary64 value, integers as integers, seeds as decimal strings;
4. the arrays, concatenated without separators, in the order listed in the metadata key
   `arrays` (a list of `[name, dtype, shape]`), each in C order and in its declared
   dtype: `<f8` (little-endian binary64), `<i8` (little-endian 64-bit integer) or `|b1`
   (one byte per boolean).

The arrays, in this order: `lc/time`, `lc/flux`, `lc/flux_err` (`<f8`), `lc/sector`,
`lc/year` (`<i8`); for each auxiliary sector `k` in order, `aux/sectors/k/time`,
`pdcsap_flux`, `sap_flux`, `sap_bkg`, `dump_times` (`<f8`); for each pixel file `k` in
order, `aux/pixels/k/time` (`<f8`, shape `(n,)`), `flux` and `flux_err` (`<f8`, shape
`(n, 11, 11)`), `aperture` (`|b1`, shape `(11, 11)`). The metadata holds everything
else that determines the input: the case (id, class, band, noise model, index,
mechanism, catalog variant, seed, extra mechanism settings), the seed of the accepted
attempt, the redraw counts, the final parameters, the expected SNRs, the catalog of
condition (ii) (its CSV text and its scan record), the target key and TIC, the sector
information, the star parameters, the product information, the data manifest, and the
scalars of the auxiliary data (per sector: sector, CROWDSAP, FLFRCSAP; per pixel file:
sector, target position, file name, its SHA-256 field, dropped cadences; neighbors and
neighbor radius). No time of day, local path or compression setting enters the bytes.
The harness reads a case back into the data classes of the code being measured.

**c. Frozen generation environment.**

- The generator runs only in the environment of tag `v0.2.0`: the virtual environment
  of the worktree `.worktrees/v0.2.0`, built from the `uv.lock` of `f479823`, separate
  from the analysis environments. The harness refuses to generate elsewhere: it checks
  the commit of the installed Refute, a clean `src/`, and the SHA-256 of
  `synthetic.py` (`b1d9518ea96ee3fd91b861c33601d57742ad96520b15079d97bd217f391fc50d`).
- The manifest records: the Python version, the platform, the NumPy version and its
  BLAS build, the thread pools reported by `threadpoolctl`, the four thread variables,
  the random generator (`numpy.random.default_rng`, PCG64) and the sequence of random
  calls.
- Each case has its own seeds (parameters, noise, auxiliary data), derived from its
  case seed by SHA-256; there is no global random state. The helpers of `synthetic.py`
  at `v0.2.0` take a generator or a seed and do not use `numpy.random`'s global state
  (checked on 2026-10-11: `make_lightcurve` and `make_blend` build
  `np.random.default_rng(seed)`, `make_aux` builds `np.random.default_rng(seed + 1000)`,
  and `render_pixels` and `make_sector_aux` receive the generator).
- The number of workers, the order of the cases and the size of the lots do not change
  any generated number (checked by the self-test below).
- **Input reproduction is accepted when its hashes match the published manifest.** No
  promise is made that the same versions and seeds give the same bytes on any machine.

**d. Lots.** For M0 to M3 the population is processed in lots
(`population.py orchestrate`): each lot is regenerated into `.cache/population/`
(git-ignored), checked against the frozen manifest, and analyzed in the four
environments (one worktree with its own virtual environment per point, all inside
`.worktrees/`) before it is deleted. The results and records of the lot are written and
read back from disk **before** the cleanup, and files are removed only inside
`.cache/population/`. The lot size is chosen from the free RAM, the free disk of the
cache and the number of processes; measured on 2026-10-11: a case takes 56.6 MB
(single orbit plus one sector), 75.5 MB (two sectors) or 113.2 MB (three sectors), and
a worker peaks at about 0.2 GB when generating and 0.32 GB when analyzing, so a lot of
100 cases needs up to about 11 GB of cache.

**e. Complete reference cases.** A small set of cases (white noise, AR(1) noise and a
blend) is kept whole, to check the reader and the serialization without regenerating
thousands of cases. Where it is kept is decided by the maintainer after the size
measurement: on 2026-10-11 each of the three is 75.5 MB raw and about 34 MB with lzma
(36 MB with zlib).

**Harness and self-test.** The harness is
`docs/validation/v0.2.1/population/population.py` (modes `generate`, `analyze`,
`metrics`, `orchestrate`). Its self-test (`selftest/`, seeds with the prefix
`refute-v0.2.1-population-selftest`, at most 2 cases per class and mechanism in each
noise model, 44 cases) is not a measurement: no case of the development population was
generated or analyzed.

**Still to fix before the v0.2.1 lock** (replaces the list above): where the inputs are
kept is decided by this amendment (regenerated and checked by hash); where the
reference cases of item e are kept is pending; the drand round of the confirmation
population (its number, committed before the round is published); the coverage
requirement of the calibration.

## Amendment 2 (2026-10-12): independent harness review

An independent review (Phase G) of the harness at commit `6e57b35` found no blocking
issue, three corrections required before the first generation (C1 to C3) and notes N1 to
N10. The harness was corrected before any case of the development population was
generated or analyzed. No criterion, size, band, mechanism, seed rule or limit changes.

**What changed in `population/population.py`** (one line each):

- **C1, point, commit and results.** `population/points.json` binds each point name to a
  full commit; `analyze` and `orchestrate` refuse an unknown point, an installed Refute at
  another commit and a dirty `src/` (tracked changes and untracked files); every run
  records the binding (point and full commit), the SHA-256 of `points.json` at that moment
  and the commit of the repository it was in; `metrics` checks each run's binding against
  that point's line in `points.json`, checks through git that the recorded file existed at
  the recorded commit, and refuses to join runs of one point whose checkout, manifest,
  harness, plan or environment fingerprint differ.
- **C2, refused attempts.** A refusal before dispatch (no case analyzed in that attempt)
  is recorded in `attempts/` with `"results": "none"` and does not invalidate the run in
  `metrics`, which lists it; an attempt that dispatched cases goes through every
  provenance check, and every result names the attempt that wrote it.
- **C3, missing cache.** Before dispatch, every pending input must exist in the cache and
  match the manifest's SHA-256; a missing input stops the run (no result is written for
  it, the attempt is recorded), and a divergent hash is recorded and stops the run for
  investigation. The expected hash is never updated and nothing is redone in silence. The
  `refused` result status of the earlier harness no longer exists.
- **N1, thread configuration.** `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`,
  `MKL_NUM_THREADS` and `NUMEXPR_NUM_THREADS` are set to 1 at the top of the harness,
  before NumPy or Refute is imported, in the generator and at every point; threadpoolctl
  confirms one thread in every pool of the main process and of every worker (with one
  worker too), and the harness refuses to run otherwise. Determinism was checked again
  after this change (self-test 3).
- **N3, overall approval.** `metrics` publishes an overall result that requires every
  criterion, C6 included; the report says that a rate can meet its limit while the study
  fails.
- **N4.** The counts of the regeneration check are written as structured data in the
  `2-regenerated` record of each lot; `orchestrate` and its subprocesses write their
  output without buffering.
- **N7, more results in `metrics`.** Paired comparisons by band and noise model in
  conditions (i) and (ii), and in condition (ii) also by catalog variant (the aggregate
  comparisons are kept as additional information); results by mechanism in both
  conditions; redraws aggregated by class, band and mechanism; and every family whose
  point estimate is worse than the limit of its criterion is named automatically.
- **N8, integrity in `metrics`.** Every result is validated; its file name must be its
  case; with `--records`, its SHA-256 must equal the one in the `results-reread` records
  of `orchestrate`; a case id may appear only once per point; the output folder is created,
  or an existing output refused, before anything is computed.
- **N9, cleanup root.** `--project` must be the top of the harness's repository; the
  lot files (`lot-*.txt` and the check report) are removed at the end of each lot, after
  the results are re-read, only inside `.cache/population/`.
- **N10, environments and errors.** A point's Refute must be the editable install of
  that point's worktree. See "Errors and interruptions" below.

**N2, two SNRs.** The SNR that places a case in its band (section 3) is computed under the
chosen noise model, without the noise of the pixel data. For a blend, the light curve
analyzed comes from aperture photometry of the rendered pixels, which adds noise, so the
SNR with that noise is lower than the band SNR. In the review's example with white noise
(600 ppm plus about 183 ppm from the pixels) the ratio is about
600 / sqrt(600^2 + 183^2) = 0.9565, 4.4% lower. That percentage does not extend to the
AR(1) model, where the effect depends on the covariance and on the number of cadences.
The bands do not change; every report states that blend bands use the SNR without the
pixel noise.

**N5, seed rules (checked against the harness code).**

- Case seed: the first 8 bytes, big-endian, as an unsigned integer, of the SHA-256 of the
  UTF-8 string `<prefix>|<class>|<band>|<noise>|<index>`, with `<class>` one of
  `planet`, `false_positive`, `no_transit`; `<band>` one of `below`, `near`,
  `measurable`, or `none` for the cases without an injected transit; `<noise>` one of
  `white`, `correlated`; `<index>` the decimal index without padding.
- Prefixes: `refute-v0.2.1-population-dev` (development), `refute-v0.2.1-population-selftest`
  (self-tests); for the confirmation, the prefix is the randomness string of the drand
  round, as published by drand.
- Attempt `k >= 1` of a redraw uses `sub_seed(seed, "redraw", k)`; attempt 0 uses the case
  seed. `sub_seed(x, a, ...)` is the same 8-byte big-endian reading of the SHA-256 of the
  decimal `x` and the parts joined by `|`.
- With `seed_k` the seed of the accepted attempt: noise from
  `numpy.random.default_rng(sub_seed(seed_k, "noise"))` (that is, of `<seed_k>|noise`); the
  auxiliary data from `sub_seed(seed_k, "aux")` (`<seed_k>|aux`), passed to `make_aux` of
  v0.2.0, which builds `numpy.random.default_rng(seed + 1000)`; for a blend, the harness
  builds `numpy.random.default_rng(sub_seed(seed_k, "aux"))` itself, without the `+ 1000`.

**N6, commensurate periods.** The ratio tested in 4.4 is `P_eclipse / P_var`, against every
fraction `p/q` with `q <= 4` and `p <= 80`, with an absolute tolerance of 0.01. With
`P_eclipse <= 5.5` d and `P_var >= 0.3` d the ratio is at most 18.33, so `p <= 80` covers
every fraction that can occur (at most `p = 74` with `q = 4`).

**`points.json`.** Only receives new points, added at the end. An association already
used never changes: a change is a new point. A new point is committed before its
measurement (the harness refuses a `points.json` that is not committed unchanged). Each
run records the association it used, the SHA-256 of `points.json` and the repository
commit, and `metrics` refuses a run whose recorded file is not found at that commit or
whose entries were changed later.

**Errors and interruptions.** An exception raised by the analysis of a case becomes a
permanent result with status `error`: it stays in every denominator, is published and is
investigated; correcting it needs a new attempt (a new harness or new code), never a
replacement of the result. An infrastructure failure (`MemoryError`, `OSError`, an
interruption, an input missing from the cache or with a different SHA-256) stops the run
without writing a result for the case; the attempt is recorded and may be resumed only for
the cases without a result, with the same inputs, environment and harness. This also
applies to infrastructure errors already recorded: their attempt records stay as they
are, and no result is ever replaced in silence.

**Self-test.** `population/selftest-3/` tests the corrected harness (the earlier
`selftest/` and `selftest-2/` are left as they were). Self-test outcomes are not a
measurement.

## Amendment 3 (2026-10-12): resume rules and harness identity

Decided by the maintainer on 2026-10-12, after the second and third rounds of the
independent review (Phase G). It describes the harness at commit `1692d99` (SHA-256
`408020676340322f4728ce3a8b4eecae505bfbec7ec34643ad9afed0e5a76225`). No criterion, size,
band, mechanism, seed rule or limit changes.

**R1, resuming a lot.** `orchestrate` skips a lot only when every result of the lot is
valid at every point **and** its records 3 (results re-read, with the SHA-256 of every
result file) and 4 (inputs deleted) exist, with the hashes of record 3 equal to the
result files on disk. Otherwise:

- every result valid and no record 3: the results are re-read, record 3 is written, the
  lot's inputs and lot files are deleted (only inside `.cache/population/`) and record 4
  is written;
- record 3 present and record 4 absent: the hashes of record 3 are checked against the
  result files, then the inputs and lot files are deleted and record 4 is written;
- any divergence between a record and the results (a different hash, a missing or extra
  result) stops the run for investigation, and nothing is written or deleted.

**R2, a committed harness.** `generate`, `analyze` and `orchestrate` refuse to run unless
`population.py` is tracked in its repository and the running file is byte for byte the
file of the HEAD commit (`git diff --quiet HEAD` and the SHA-256 of `git show
HEAD:<path>`); a file changed on disk after the process started is refused too.

**Harness identity.** The identity of the harness is its SHA-256 (`harness_sha256`),
recorded in every manifest, run, attempt and result. The `harness_commit` recorded with it
is the HEAD of the repository at the moment of execution, not the commit that last changed
the harness (N-a). `generate --check` compares only the cases (each case entry, with the
SHA-256 of the case's bytes), not the header of the manifest (harness, harness commit,
environment): a regeneration by another harness with the same case bytes passes the check
(N-b).

**N-c, operation.** The workers do not check the harness's SHA-256 again; the check is made
by the process that starts them. Operating rule: no edit of the branch while the
development population is generated and measured (until the end of M3, except the commits
the maintainer asks for), and the SHA-256 of the harness on disk is checked at the end of
each measurement point.

**Independent review.** The harness had three rounds of independent review (Phase G), on
commits `6e57b35`, `a83e09a` and `b7c724c`; the third found it fit for the first
generation. The reports and the verifiers of the reviewer are in `population/review/`.

**Reference cases** (Amendment 1, item e). The three cases are chosen (self-test
population, by the rule declared in the draft release notes: in `selftest-2/`, the case
with the smallest index among planets with white noise and the plain two-year mechanism,
planets with AR(1) noise and the same mechanism, and false-positive blends with white
noise). Their publication is postponed until it is confirmed whether a GitHub pre-release
starts an archive in Zenodo.

**Frozen manifest.** The manifest of the development population, once generated and
checked (two generations in separate processes, byte-identical), is committed and frozen
at `population/manifest-dev.json`, with `population/manifest-dev.README.md` beside it
(generation environment, SHA-256 of the manifest, generation times, counts and redraws).

## Amendment 4 (2026-10-13): harness v2, machine qualification, generation and analysis rules

Decided by the maintainer on 2026-10-12 and 2026-10-13, after the divergence of the
development generations of 2026-10-12. No criterion, size, band, mechanism, seed rule or
limit changes.

**What happened.** The v1 harness (`population.py`, SHA-256
`408020676340322f4728ce3a8b4eecae505bfbec7ec34643ad9afed0e5a76225`) generated the
development population several times, hash only, in separate processes. Manifests B, A2, A3,
B2 and D are byte-identical (manifest B, SHA-256
`4073d96a0bce901a31241d5c2dd3d7b46192a4731a4ec3996ea1077039b833e9`); manifest A differs from
them in 2 of 5200 cases (`planet-below-white-0016` and `planet-below-white-0100`) and manifest
C in 1 (`no_transit-none-white-1731`); nine instrumented repetitions had no divergence. No
divergent byte was captured, so the difference cannot be located below the whole case. These
generations are diagnostics: none is a frozen manifest, and none is ever approved
retroactively.

**What this amendment adds.** A new harness, `population/population_v2.py` (SHA-256
`2e001aac326ae92d1f8608aab24bd88184ead0e0c5180e0bdf6282a9cafc6067`), with its comparator `population/population_compare.py` (SHA-256 `d05716c52397332f89746bfe317f98eb6245b023b81c4178f8fe4b3f49379ab0`,
schema `refute-population-compare/1`) and the D6 test script `population/d6.py` (SHA-256
`1640cb47fc1ceb3ff18007e6ab5f26c3cd7f22e648b560c8cc5c915473b458fa`). `population.py` stays as it is. The case bytes do not change: v2 builds and
serializes every case exactly as v1 (`refute-population-serialization/1`). The rules below
were written before the implementation, in the specification
`population/harness-v2-spec.md` (revision 6, committed next to the harness, SHA-256
`4433584194bf6bb93467f9d34c86e164e532b36aef013beacf9e73a381d83769`) and in the D6 proposal
(revision 4, SHA-256 `891cdcf421b212950a46984e6ecbcf2c4f735b2ae1b05c6b9c863f0b78b3eebb`,
written in Portuguese and kept with the maintainer's diagnostic records; its rules are
restated in English in item 15). The other documents the specification cites (the D7 report
and its errata, the Codex reviews) are also diagnostic records, not in the repository. Where
this text and those drafts differ, this text governs.

### What Amendment 4 replaces, keeps and extends

| Earlier text | Amendment 4 |
|---|---|
| Amendment 1, item a ("It runs twice, in separate processes; the two manifests must be identical byte for byte.") | **Replaced** by the rule of K = 3 generations and N = 3 sets (item 6). "The manifest is then committed and frozen. Only after that do M0 and the other points begin." and "The expected hash is never updated ... no case is removed" are **kept**. |
| Amendment 1, item b (serialization) | **Kept** (the same bytes). |
| Amendment 1, item c (frozen generation environment; the manifest records the environment) | The environment is **kept** (tag v0.2.0 only). **Where it is recorded changes**: the environment, thread variables and pools and the random generator move from the manifest to the execution record of each generation, so that the K scientific manifests of a set can be identical; v2 adds the machine record and the dispatch check (items 3 and 4). |
| Amendment 1, item d (lots) | **Extended**: every lot is analyzed in two slots (item 7). |
| Amendment 2, C3 (a divergent input hash stops the run) | **Kept**; the divergence now also writes a lock (item 5). |
| Amendment 2, N10 (infrastructure failures may be resumed) | **Restricted**: an observed divergence is never an infrastructure failure; in generation, an interrupted generation is never resumed (its set is consumed); resumption after an infrastructure failure remains only for analysis, per slot. |
| Amendment 3, R1 and R2 | **Extended** (item 9). |
| Amendment 3, N-c | **Kept**, with one declared exception: the manual, approved commits of lock markers, journal entries and resolutions. |
| Protocol section 9 (a new confirmation needs a new future drand round) | **Restated**: if the code, the harness, the generation, the comparator or the plan change after the confirmation has been examined, the attempt is preserved and published and the new confirmation needs a new future drand round; the comparison with manifest B never applies to it. |
| Protocol section 10 (where results go) | **Adjusted** (item 11). |

### 1. Machine qualification (a prerequisite of every campaign on this machine)

The campaign runs only on the current machine (AMD Ryzen 9 5900XT, Gigabyte B550M AORUS ELITE
AX, BIOS F8d, 4 x 16 GiB without ECC). No generation of a new campaign starts unless the
qualification's result is PASS. The criteria were fixed before any qualification test ran:

- **MemTest86:** at least 4 full passes of the declared test set, all testable RAM, zero
  errors.
- **y-cruncher:** version and configuration fixed before the run, an explicit list of
  components, at least 4 effective hours with every component completing a cycle, zero
  verification errors, hangs or unexpected restarts. The four hours are a requirement of the
  project, not a certification by the tool's author.
- **Result:** PASS (every requirement executed and met; only PASS allows a campaign), FAIL (an
  error or instability observed) or INCOMPLETE (an interruption or a requirement not executed;
  redone from the start and in full). After a FAIL, a new qualification is valid only with an
  identified cause and a documented corrective action. Every attempt, the failed ones
  included, is recorded and published. A relevant later change (BIOS, microcode, memory, CPU
  tuning, the EasyTune profile, operating system, NumPy build) invalidates the qualification.

**The qualification of 2026-10-12 and 2026-10-13:**

- **y-cruncher, attempt 1 (2026-10-12): FAIL.** Version 0.8.7 Build 9547 (binary
  `19-ZN2 ~ Kagari`), configuration file `qualificacao-refute.cfg`: `StressTest`,
  `AllocateLocally` true, logical cores 0 to 31, 41768774400 bytes, 120 s per test, 15000 s in
  total, `StopOnError` true, tests BKT, BBP, SFTv4, SNT, SVT, FFTv4, N63, VT3. One verification
  error in N63 on logical core 8 (`ConvolutionFailedException: Coefficient is too large`); no
  hardware event in the Windows log.
- **A diagnostic (2026-10-12), not an attempt:** N63 alone, 32 threads, about one hour, Stop on
  Error off: 29 of 29 iterations without error. It does not cancel the FAIL and does not
  identify the component.
- **MemTest86 (2026-10-12 to 2026-10-13):** 4 passes, about 12 hours, memory at 2666 MHz and
  1.20 V (the daily configuration). Tests 0 to 10 without errors. Test 13 (Hammer) failed in
  the 4 passes: 26 errors, all at the physical address `0x8C7CBD968` (about 35 GiB) and in the
  same bit, always from 1 to 0, also at the slow rate.
- **Probable cause, not demonstrated:** a weak DRAM cell, sensitive to row hammer, in one of
  the four modules. It is the probable cause of the three generation divergences and of the
  y-cruncher error of attempt 1 (an isolated, rare and silent bit, with no WHEA event on memory
  without ECC). It is not demonstrated, because no divergent byte was captured.
- **Corrective action:** the physical page `0x8C7CBD` (4 KiB) is excluded from use by Windows
  (BCD `badmemorylist`). No module was removed or replaced. The entry was checked by the
  maintainer, as administrator, on 2026-10-13.
- **The MemTest86 criterion was changed by the maintainer after seeing the result, and is
  recorded as such:** the run of 2026-10-12 to 13 is accepted, because tests 0 to 10 had no
  errors and every error of test 13 was confined to a single address, whose page is excluded.
  Reason: the exclusion holds only inside Windows, and MemTest86 runs outside it. Under the
  criterion written before the tests (zero errors), this run would have been a FAIL.
- **Residual risk, declared:** the module is still defective and may have other weak cells
  that were not detected; the exclusion holds only while the memory configuration and the BCD
  do not change. The protections of the study (K = 3 in generation, two slots in analysis)
  turn an error of this kind into a block, not into an accepted result.
- **Invalidation:** the qualification is invalid if any later test shows an error at another
  address, or if the memory, the BIOS or the `badmemorylist` entry changes.
- **y-cruncher, attempt 2 (2026-10-13, about 04:27 to 08:40): PASS.** Version 0.8.7 Build
  9547, configured by hand (the program did not find the `.cfg` file): 32 logical cores,
  45.8 GiB (1.43 GiB per thread), NUMA local, 120 s per test, 15000 s in total, Stop on Error
  on, the 8 tests. 15 complete cycles (iterations 0 to 14) with the 8 tests passed; iteration
  15 ended by the 15000 s limit; zero errors, no hang and no restart.
- **State: QUALIFIED, under the conditions above.** The cause of attempt 1 remains probable,
  not demonstrated. The three fatal machine-check events in the Windows log (2026-07-30,
  2026-08-23 and 2026-08-24) predate the processor replacement of September 2026 and are no
  evidence about the current processor.

### 2. Identity and eligibility

- **Common identity** (`campaign_id`, the SHA-256 of the committed campaign declaration, the
  chain and the set) is carried by the scientific artifacts (manifest and block index), which
  carry nothing that varies between generations.
- **Execution identity** (the common identity; the generation, or the point, lot and slot; a
  new `execution_id` per process start; `attempt`; `eligibility`; `origin`: mode, harness
  SHA-256 and HEAD commit) is carried by every execution artifact.
- A campaign lives in `population/campaigns/<campaign_id>/` (declaration, journal, lock
  markers, resolutions) and has eligibility `campaign`: every check is enforced. A campaign
  declared under any other folder is a **diagnostic**: its declaration says
  `"eligibility": "diagnostic"`, every artifact it writes is `diagnostic`, the git checks are
  recorded but not enforced, and it can never be accepted as campaign evidence. Renaming,
  moving or copying files does not change their identity; a diagnostic is never promoted.
- There are two chains, `development` and `confirmation`. A declaration names its chain, its
  predecessor and the sets the chain has already consumed; a new campaign never resets its
  chain's counter. The development chain starts with the v1 generations, a diagnostic
  predecessor that consumes no set.

### 3. Generation records

- **Scientific manifest** (`refute-population-manifest/2`): format, serialization, population,
  harness SHA-256, generator commit and `synthetic.py` SHA-256, thresholds, call sequence, the
  common identity, the block size, the SHA-256 of the block index, and every case entry. A case
  entry holds the v1 fields and, computed over slices of the final bytes: the whole SHA-256
  (computed twice with two fresh `hashlib` objects; unequal digests are an integrity error, a
  detector of transient errors, not independent of a systematic defect), the layout (header
  length and, per segment in blob order, name, dtype, shape, offset, length and SHA-256; the
  segments `magic`, `header_length`, `header` and every array cover every byte without gaps)
  and the SHA-256 of its block list.
- **Block index** (`refute-population-blocks/1`): the SHA-256 of every block of 1 MiB of every
  segment of every case. The bytes of whole generations are not retained.
- **Execution record** (`refute-population-execution/1`), one per generation: the execution
  identity, the configuration (workers, order, affinity, thread variables and pools, the
  dispatch table of the main process and of every worker), the machine record (Python, NumPy
  and its bundled libraries with their hashes, the wheels of `uv.lock`, operating system, UCRT,
  CPU and microcode, BIOS, board, memory, ECC, the EasyTune service, and the settings declared
  by the maintainer), timings, the SHA-256 of the manifest and block index it produced, and
  the operational data of every case (PID, position in its process, times).
- **Localization concession (accepted by the maintainer).** A divergence is detected by the
  hashes. Without the original bytes, the localization may end at the block (one segment and
  one block of at most 1 MiB); the element, the bits and the magnitude may not be known. A
  later regeneration is a new observation, never a capture of the earlier one.

### 4. Dispatch and cache

- The campaign declaration holds the closed inventory of NumPy dispatch: every function and
  signature of `numpy.lib.introspect.opt_func_info()` with its `current` target, and the value
  of `NPY_DISABLE_CPU_FEATURES`. The main process and every worker read the effective table
  before the first case; any difference, missing entry or unreadable table ends the execution.
  The table covers NumPy's dispatched loops only, not OpenBLAS, SciPy, Astropy or other
  compiled code.
- A case written to the cache never replaces a different existing file: equal bytes are kept;
  different bytes leave the existing file untouched, are written beside it as
  `<case>.<sha256>.rpc`, and end the execution with a lock.

### 5. Journal, lock markers and closure

- Each campaign has an append-only, hash-chained journal (`journal.jsonl`). Entries:
  `started` (before the first dispatch), `process` (every worker as it starts, with its PID),
  `closed` (after every recorded process has ended, verified by PID), `interrupted`,
  `reconciled` (the maintainer's record of an execution whose closure cannot be shown; it
  counts as interrupted), `divergence`, `accepted` (a set) and `compared` (two slots).
- At a divergence (generation, cache, input hash, slots, reconciliation of records or metrics)
  the harness writes a lock marker keyed by the campaign (`locks/`) and a `divergence` entry,
  dispatches nothing more, and waits for its processes.
- Every campaign mode refuses while a lock marker or a `divergence` entry has no committed
  resolution, while an execution has `started` without `closed` or `reconciled`, or while the
  journal chain is broken; the lookup is by campaign, whatever run directory is used. Deleting
  a marker is not a resolution (the `divergence` entry still blocks, and a marker deleted from
  git is found in the history). A lock is lifted only by a committed resolution record that
  names the lock by its SHA-256 and applies a rule registered in the declaration.
- **The harness never runs a git command that writes.** Committing markers, journal entries
  and resolutions is a manual step approved by the maintainer, after every process has
  stopped. **Accepted risk, not resolved:** until that commit, the marker and the journal exist
  only on disk and could be deleted or altered by hand; every report repeats it.

### 6. Generation rule and budget (decided by the maintainer)

- A **set** is K = 3 generations of the whole population, each in a new main process with new
  workers, in configurations declared in advance (proposed: 24 workers in index order, 12
  workers in a declared shuffled order, 24 workers in another declared shuffled order). A set
  is complete when its three manifests and block indexes are byte-identical; each generation
  is compared with the earlier ones of its set as soon as it ends.
- `check-set` accepts the first complete set only if every execution of the campaign is
  closed and the **blocking comparisons** find nothing: no case differs from a value that
  appeared in two or more generations of another set of the campaign; and, for the
  development population only, every case's SHA-256 equals manifest B. These comparisons can
  only block. The accepted manifest is then committed and frozen. Cases or executions of
  different sets are never combined.
- **Budget:** N = 3 sets per campaign; at most 6 sets in the development chain and 6 in the
  confirmation chain. A set consumes budget when its first generation starts, also when it
  ends interrupted or divergent; an interrupted generation leaves its set incomplete and
  consumed, never completed by another generation. Reaching the ceiling prevents new sets
  only: the sixth set, if complete, unanimous and unblocked, is accepted normally; otherwise
  the chain is blocked and published. The ceiling is never raised after failures are seen; the
  number 6 is a decision of cost and governance with no statistical guarantee. A software or
  environment change opens a new campaign in the same chain. This budget applies to
  generation only.

### 7. Analysis rule: two slots

- Every lot is analyzed at every point in two slots, each an independent execution (new main
  process and workers), on the same inputs checked by hash, with the same configuration; the
  slots differ only in the order of the cases (two permutations of the population frozen in
  the declaration with their SHA-256).
- An interrupted slot resumes only its own remaining cases (infrastructure only); a result
  never migrates between slots.
- The two complete records of every case are compared with the comparator's profile `slots`.
  A divergence writes a lock and blocks the lot and the approval; there is no repetition until
  agreement and no majority vote. Resuming after an investigation needs a report that
  identifies the cause or declares it unknown, delimits the scope and applies a rule
  registered in the declaration; a correction is a new version and a new campaign.

### 8. Complete scientific record, envelope and typed contract

- Per case, point and slot: `refute-population-result/3`, with exactly the members `/format`,
  `/identity`, `/case`, `/input` (SHA-256 of the bytes read and of the manifest entry),
  `/status` (`analyzed` or `error`; a missing record counts as `missing`), `/traceback` (only
  with `error`), `/conditions/i` and, except without transit, `/conditions/ii` (each with
  `/scientific`, the complete output of `build_result` of the code being measured, and
  `/harness_outcomes`: signal identity, its factor, the verdict without `eb_catalog`),
  `/configuration` (thread variables, pools, dispatch table SHA-256), `/operational` (PID,
  seconds, peak memory, times, position in the process), `/comparison` and `/integrity`.
  Records are never rewritten: the effective comparison status and integrity come from the
  comparison reports and the locks.
- **Typed contract** (closed list; anything else is a harness error with status `error`):
  `None`, booleans, integers in the int64 range, strings, lists, tuples, dicts with string keys;
  every `float` and `numpy.float64` as `{"f64": <16 hex digits, big-endian binary64>, "dec":
  <repr>}`, the bits taken from the original value (sign of zero and NaN payload kept), a
  finite `dec` checked to give the same bits. `numpy.float32`, `numpy.float16`, arrays and
  other types are errors. JSON is UTF-8, keys sorted, no spaces.

### 9. Comparator (`refute-population-compare/1`), R1, R2, N10 and N-c

- **Blobs:** structure first (each blob's layout parsed on its own; a structural difference is
  reported as such), then bytes (first differing offset, segment, block; for the header, the
  JSON paths; for an array, the first differing element and the count), then, only as an
  explanation, absolute and relative differences and ULPs; differences only in the sign of
  zero or in a NaN payload are counted apart and never treated as equal. Without bytes, from
  the manifest entries and block indexes, it locates the segment and the block.
- **Records:** structure, then values by their typed encoding, skipping exactly the paths of
  the named profile. There is no default profile. **`slots`** excludes exactly
  `/identity/slot`, `/identity/execution_id`, `/identity/attempt`,
  `/identity/origin/harness_commit`, `/operational/pid`, `/operational/seconds`,
  `/operational/peak_memory_mb`, `/operational/started_utc`, `/operational/ended_utc`,
  `/operational/sequence_position`, `/comparison/status`, `/comparison/report_sha256` and
  `/integrity` (a record with `/control` is an error under it). **`d6-science`** excludes
  those 13 plus `/configuration/thread_env`, `/configuration/threadpools`,
  `/configuration/dispatch_table_sha256` and `/control`. **`d6-control`** compares only
  `/control`. Every report records the profile and the SHA-256 of its definition
  (`slots` `a3e7e797828786b513221071666ff78e1ec07d5ef0158cce8d4cd2b403c95571`, `d6-science` `ce6816bea4354535901c34657e604d495ad24590284404ea18887efeaefca084`, `d6-control` `86f232108d6be8fdf5630a8801b560406098705d79f40d5c023081dc73d1019a`). The comparator's file
  SHA-256, version, schema and profiles are frozen in the campaign declaration.
- **R1 (extended).** A lot is finished only when both slots have every result valid at every
  point, each slot has its record 3 (results re-read, with hashes), the comparison of the two
  slots has every case identical (record 3c, with its hash), and record 4 (inputs deleted)
  exists. The completion rules of Amendment 3 apply per slot; a missing comparison is run
  before record 4; any divergence between records and results, or between slots, writes a
  lock.
- **R2 (extended).** Every campaign mode refuses unless `population_v2.py` and
  `population_compare.py` are, byte for byte, the files of HEAD and their SHA-256 equal the
  declaration.
- **N10 (restricted)** and **N-c (kept)** as in the table above.

### 10. Metrics and the integrity-failure report

- C1 to C6, their limits and bounds do not change. A blocked lot, a divergent case and a case
  `missing` or `error` in either slot count as integrity errors in C6.
- Before computing anything, `metrics` reconciles: every case of the frozen manifest exactly
  once per point and slot, with a valid record; the denominators per stratum equal the
  manifest's counts; the records equal records 3 and the comparisons 3c; and, with
  `--check-against`, the recomputed metrics equal the ones already recorded. Any mismatch
  writes a lock.
- `metrics --integrity-report` (for a locked campaign) reads every lock, divergence,
  resolution and execution, never lifts or requires lifting a lock, never computes an
  approval, and writes a publishable report whose approval is "BLOCKED: integrity failure".

### 11. Records: where they go (adjusts protocol section 10)

Committed (manually): the campaign declaration, journal, lock markers and resolutions; per
lot, the index of the SHA-256 of every result record; the aggregated metrics; every divergence
in full (both records, the comparison report, the lock). Published as a compressed release
asset: the complete result records (pending the Zenodo question of Amendment 3). Measured in
the self-test: about 63 KB per record (one case, one point, one slot), so about
2.6 GB for the development population at four points and two slots.

### 12. Prohibitions

Never update a frozen manifest or any expected hash to accept an observed variant. Never
regenerate or re-analyze until a result matches, and never use a later coincidence as the
resolution of an earlier divergence. Never replace the evidence of an earlier attempt. Never
combine cases or executions of different sets, slots or campaigns. Never accept a diagnostic
artifact as campaign evidence.

### 13. The determinism and measurement population

`population determinism`: the cases of the development structure built with the prefix
`refute-v0.2.1-population-determinism`, keeping, in every class, band and noise model, the
index `10 j + (j mod 5)` for `j = 0, 1, ...` (one case in ten consecutive indexes): 520 cases,
10 % of every block, with the same mix of classes, bands, noise models, mechanisms and catalog
variants as the development population, and including the mechanisms that diverged (planets
below threshold with white noise, two and three years; no transit with trend and variability,
white noise). v1 builds the same cases with `--population
confirm:refute-v0.2.1-population-determinism` and `--cases-from` the list of their ids.

### 14. Overhead per generation (fixed before any campaign is frozen)

One v2 generation may take at most 25 % more time than one v1 generation of the same
population, machine, workers and order. Measurement: the determinism population, hash only,
24 workers, index order, six runs alternating v1 and v2, each a new process; overhead =
median(v2) / median(v1) - 1 on the wall time of each process; accepted at 20 % or less.
**Measured in the self-test: 12.0 %** (wall time per process, v1 34.2, 34.4, 33.6 s, v2 39.6, 38.3, 37.8 s; medians 34.2 and 38.3 s). **Decision: the double hash
is kept.** It is recorded in every campaign declaration and never changes during a campaign.

### 15. D6 (a requirement of v2, not yet run)

D6 (`population/d6.py`) tests systematic dependence of the analysis on the process history,
the order of the cases, the partition between workers and the NumPy dispatch target, in the
contrasts of a declared matrix only. Its inputs: a closed list of 40 cases of the determinism
population, chosen by a rule declared in `d6.py` from the generation parameters (never from
analysis results), generated in K = 3 new processes and accepted as a diagnostic campaign.
Seven configurations, each run twice in new processes at M0 and M3: F (a new process per
case), R-idx, R-rev and R-shf (one process, index, reverse and a declared shuffled order),
P24 and P12 (24 and 12 processes, worker w receiving the fixed list `cases[w::24]` or
`cases[w::12]`), and E (as R-idx, with `NPY_DISABLE_CPU_FEATURES=X86_V3`). Contrasts:
F x R-idx, R-rev x R-idx, R-shf x R-idx, P24 x P12, E x R-idx and P24 x F, plus the two
repetitions of every configuration.

- **Check 1:** the observed configuration (thread variables, pools, dispatch table) against
  the one declared for each variant, and the observed sequence (each declared process
  position, with its PID, analyzed exactly its declared list in order; no case analyzed twice).
- **Check 2:** the science between variants with the profile `d6-science`.
- **Control pass:** every D6 record carries `/control/cases_before_in_process`; the profile
  `d6-control` must report a difference exactly where the declared assignment makes the value
  differ, and nowhere else.
- **Negative control:** injected differences in copies of records (a changed character, the
  sign of a zero, a NaN payload, a header field, a metric value, a missing field, an extra
  field, a float whose `dec` and `f64` disagree) located by `d6-science`; a control difference
  ignored by `d6-science` and found by `d6-control`; a copy of E's execution record with the
  default dispatch table refused by check 1.
- **Result:** PASS only with all six conditions of a valid conclusion (every analysis present;
  every status `analyzed`; inputs verified; records complete and valid under the typed
  contract; integrity and every execution closed; check 1 and the negative control passed) and
  no difference in check 2. FAIL on any scientific difference, a control that misreports, or a
  record with status `error`. INCOMPLETE on a missing analysis, an execution invalidated by
  check 1, an interruption or an input that does not match its hash; an INCOMPLETE D6 is
  redone from the start, in full. Only PASS meets the requirement. A negative result holds
  only for the contrasts of the matrix and the inputs exercised.

D6 runs only when the maintainer releases it. The self-test ran its machinery once, on 13
cases at M3 only (a smoke run, not the D6).

### 16. Revalidation before any campaign

Reference cases with their SHA-256
(`f3951b9e85d21ea8cbc42a23074ad5b442498d049bfbb51896c6277c85192c4e`,
`a7dd6266f4ffd30f3cead01987a301c64db2086791a7296e0db55f3f416055c4` and
`1817b9f776969ae050ba6cd7b1849dda968595041dabe37711390cec7b37b724`); the determinism
cases in K = 3 new processes, identical in every segment and block; the injected differences
located by the comparator (with and without the bytes) and in result records; the journal and
the lock; the overhead per generation; the size of the records; D6 with result PASS; the
machine qualification with result PASS, recorded before the campaign declaration. The
self-test of v2 is in `population/selftest-v2/` (every check passed; the D6 smoke run of 13 cases at M3 gave PASS, which is not the D6); D6 is pending.

### 17. Residual risk

Three identical generations and two identical slots make an undetected transient error
unlikely, but do not demonstrate the absence of a defect and do not detect a systematic one.
D6 tests systematic dependence only on its matrix. The cause of the 2026-10-12 divergences is
probable, not demonstrated.

### Amendment 4, clarifications of 2026-10-13

Decided by the maintainer on 2026-10-13, after an independent read-only review of the code of
commit `113e07c` (by Codex; the review and its critique are kept with the maintainer's
diagnostic records). The review found ways for the code to accept evidence that the rules
above exclude; the three files were corrected **before any campaign started** (no campaign
directory exists yet), and keep their names: their identity is their SHA-256,
`population_v2.py` `8b3b6ad6aca6e713636b04e40db5a7d253c05458c8b143c38d984100072c1f82`, `population_compare.py` `0e62dcc4dc99a53fcc319aa513734f31e9d877406cc81e56ea97c80042e2f01f`, `d6.py` `bef4ab9db52b059ae63bcb6bc27bdc77ec2db51cf8bf762c13278d76f5f70466`
(profiles: `slots` `a3e7e797828786b513221071666ff78e1ec07d5ef0158cce8d4cd2b403c95571`, `d6-science` `ce6816bea4354535901c34657e604d495ad24590284404ea18887efeaefca084`, `d6-control` `86f232108d6be8fdf5630a8801b560406098705d79f40d5c023081dc73d1019a`). The text of
Amendment 4 above is not changed; these rules are added to it, each with its reason. No
criterion, size, band, mechanism, seed rule or limit changes.

1. **One run directory per analysis unit, the first valid observation.** The first
   execution of an analysis unit (point, lot, slot) fixes its run directory in the journal; a
   later execution of the unit is accepted only in that directory and only for the cases
   without a record, and a second analysis of the unit in another directory is refused. A
   record counts only if it was written by an execution of its unit, started and closed (or
   reconciled) in the journal, in the unit's directory. So each case has exactly one record
   per slot and point: the first valid observation. *Reason:* otherwise a unit could be
   analyzed again elsewhere and the folder to compare chosen afterwards.
2. **The complete scientific record is required.** A record with status `analyzed` must
   carry, in every condition, the minimal content of `build_result` at the four points
   (`schema` `refute-tess-verdict-1`, `status` `OK`, a verdict in SURVIVED, WEAKENED,
   REFUTED, INCONCLUSIVE, the tests with name, status and severity, `expected_tests`, and the
   other declared members); a record without it is invalid, and a condition without a valid
   verdict counts as an error in C6, never as a successful analysis. *Reason:* an empty
   scientific section would otherwise count as analyzed and fall outside every numerator.
3. **R1 in metrics.** `metrics` computes nothing unless every lot has, at every point, the
   records 3 of both slots, the comparison 3c registered in the journal (by the SHA-256 of
   its report) with every case identical and naming the same files, and record 4; a lot not
   finished is a refusal, a mismatch is a lock. Comparison reports not registered in the
   journal are ignored. There is one comparison per lot and point: a second one is refused,
   whatever the records folder (by `compare-slots`, and by `orchestrate` before it writes any
   record), and the check and the `compared` entry are made under the journal lock; two
   `compared` entries for one lot and point, or a registered report that is later missing or
   altered, are damaged evidence and a lock (in `metrics`, `orchestrate` and
   `compare-slots`). *Reason:* R1 was checked by `orchestrate` but not by `metrics`, a damaged
   report was treated as a lot not yet compared, and a comparison repeated in another records
   folder replaced the registered one.
4. **Campaign declarations** (under `population/campaigns/` only). The whole population,
   never a case list; the chain given by the population (`dev`: development; `confirm:...`:
   confirmation); for the development population, manifest B
   (`4073d96a0bce901a31241d5c2dd3d7b46192a4731a4ec3996ea1077039b833e9`) as the reference, and
   no reference for any other population. *Reason:* a case list or a missing reference would
   allow a population or a comparison chosen after seeing diagnostics.
5. **The chain's counter is verified.** A declaration names its predecessor (campaign id and
   declaration SHA-256) or, for the first campaign of a chain, the kind `v1-diagnostic`
   (development) or `none` (confirmation) with 0 sets consumed before it; the harness checks
   that the predecessor exists with that SHA-256 and has no unclosed execution, that the sets
   consumed before equal the predecessor line's count, and that every other campaign of the
   chain is an ancestor or a successor (one line per chain; see item 15). *Reason:* the count was declared, not verified.
6. **Prerequisites are enforced.** A campaign generation is refused unless the declaration
   names, by path and SHA-256, the structured machine qualification record
   (`refute-machine-qualification/1`; the record of this machine is
   `population/machine-qualification.json`, SHA-256 `707faf63d13f39d77cb8dc7e278c45994d9552aa77378e41c911a0a1a64d6fe1`, the published record; the
   local working notes it names are not published) and the report of the full D6. The
   qualification's result is read from its record (never from the declaration) and must be PASS; its seven
   validity conditions that can be read without elevation (CPU name, processor id, microcode
   revision, BIOS version, BIOS date, board, and the memory modules with their bank, slot,
   part number, capacity, configured speed and voltage) must all be present, with values and
   at least one memory module (an incomplete PASS record is refused before any comparison),
   and must equal the machine at the start of the generation; the BCD
   `badmemorylist` entry is attested by the maintainer (2026-10-13) and not machine-verified,
   because reading it requires administrator rights; the BIOS settings (defaults or Auto, no
   manual CPU or memory tuning) and the absence of an EasyTune profile are stated by the
   maintainer (2026-10-12) and not machine-verified either. The D6 report must be a PASS
   that counts as the D6 (item 13) produced by the current `d6.py`, harness and comparator
   profiles (their SHA-256 in the report); a D6 of another version does not count. *Reason:* the
   qualification and D6 were required but not checked by the code, then the PASS was taken
   from the declaration and an old D6 counted.
7. **The affinity is declared.** Every declaration declares the affinity of its executions
   (on this machine, logical processors 8 to 31); generation, regeneration, analysis and
   orchestration refuse another, and the run record and its fingerprint (compared between the
   two slots) carry it. *Reason:* the slots share one configuration, affinity included.
8. **Campaign ids and paths.** A campaign id is a plain folder name (lowercase letters,
   digits, dots and hyphens, no `..`), its folder is directly under its root, and every path
   the harness and the D6 script write (outputs, caches, records, reports, the given roots
   and the default root, resolved) must be inside the project folder. The user's home
   directory (`Users/<user>` or `home/<user>`) is masked in every string and dictionary key
   of every record, journal entry, machine record and traceback before it is written, and the
   harness and the D6 script refuse to run when the project folder is inside the user's home
   directory (the mask would then change the paths the harness reads back). *Reason:* an id with path components could move a strict
   campaign out of `population/campaigns/`, and the records are meant for publication.
9. **Detection writes the lock at once, and every observation is kept.** Every result of a
   generation or regeneration (entry, blocks, problems, operational data) is appended, as it
   arrives, to the execution's observations file (one JSON line per case, flushed at once,
   synchronized to disk at a divergence and at the end), named in the `started` entry; a
   divergence writes its lock marker and journal entry at the instant it is detected, after
   its observation; every later event of the same execution is written to the journal at
   once (kind `event`); at a normal end a generation stopped by integrity also writes an
   evidence file. An interruption after a detection therefore keeps the lock and every
   observation made until then. An earlier generation or another set whose artifacts are
   missing or changed is a lock, never skipped. A worker that reports a dispatch or
   thread-pool difference is an integrity divergence (lock), never an infrastructure
   failure. *Reason:* a stop between the detection and the end of the pool lost the
   divergence and the observations, and a skipped artifact removed evidence from the
   blocking comparisons.
10. **One execution per unit.** The refusals of a unit and its `started` entry are evaluated
    and appended under the journal lock in one step, so that two simultaneous executions of a
    unit can never both start; two executions of one generation found later are a lock; a new
    set starts with generation 1. Final files are created exclusively by a hard link (no window
    between a test and a rename). *Reason:* a race could start a generation twice and hide one
    of them.
11. **Records 3 on resumption.** A record 3 that exists must equal the results; a missing one
    (a stop while records 3 were written) is rebuilt from complete, valid results. *Reason:* a
    partial set of records 3 produced a false lock.
12. **Diagnostic metrics are labelled.** `metrics` of a diagnostic campaign writes its
    eligibility and identity, and its report says "DIAGNOSTIC: not an approval" instead of an
    overall approval; every metrics report repeats the accepted risk of item 5 of Amendment 4.
    *Reason:* a diagnostic report could be read as an approval.
13. **The D6 result counts only for the declared matrix.** A D6 run counts as the D6 only with
    exactly the declared matrix (40 distinct cases, M0 and M3, the seven configurations, two
    repetitions, the declared assignment); any other run, even with every check passed, is
    reported as "PASS (smoke run, not the D6)". The 40 cases are authenticated: the
    selection manifest must be the accepted set of a campaign of the whole `determinism`
    population (no case list, no lock, exactly its 520 cases and seeds), the cases are
    recomputed from it by the declared rule both in `plan` and in `check`, and the inputs
    campaign must be restricted to exactly these cases. Check 1 also verifies every
    execution record (closed; naming the declaration, `d6.py`, the harness, the
    configuration, the repetition and the point; its checkout at the point's commit in
    `points.json`, clean and editable) and the SHA-256 of every record file; the control
    value of every record must equal its declared value, and the control pass must find
    differences only at `/control/cases_before_in_process`; the negative control runs inside
    the check, on the same records, with a new copy of E's execution record each time; the
    inputs campaign must be unblocked with K = 3. *Reason:* the earlier check could pass
    without the matrix, the closures, the control values or an authenticated selection.
14. **Comparator.** A malformed `f64` and an integer outside the int64 range make a record
    invalid (reported, never an exception); a manifest comparison also compares the block
    lists and the block index headers. *Reason:* robustness of the reports.
15. **Smaller additions.** `reconcile` (which writes to the journal) applies R2 in a strict
    campaign; the execution record names the random generator; the declaration must record
    the overhead decision (the double hash kept). A campaign with a successor in its chain
    (a campaign whose predecessor line includes it) is superseded: no generation runs in it
    (neither a new set nor the continuation of a set), and its reconciliation, metrics,
    status and integrity-failure report still work.

**Left for later, with the reason.** The confirmation prefix is not yet checked against a
drand round (the confirmation campaign is not in view; it will be checked before it, from
the round number and randomness declared); the loss of the tail of a journal before it is
committed remains the accepted risk of item 5; `status` reads the campaign without applying
R2, and the integrity-failure report reads the campaign and writes only its own report.

**Reviews and self-tests.** Two further read-only reviews of the corrections were made. The
second found four remaining blocking points (items 3, 6, 9 and 13); the third found two of
them resolved (items 9 and 13) and two partly resolved (items 3 and 6). The maintainer
decided to complete items 3 and 6 without a fourth review, proven by specific tests. The
self-test of these files is `population/selftest-v2-4/` (reference cases kept; overhead 16.5 %; determinism byte-identical; injections 5 of 5 and 6 of 6; D6 smoke run PASS (not the D6), negative control 11 of 11; review findings 19 of 19, 14 of 14 and 18 of 18; test suite 505 tests, 0 failures, 0 errors);
`population/selftest-v2/` tested the files of commit `113e07c`, and
`population/selftest-v2-2/` and `population/selftest-v2-3/` intermediate versions (after the
first and the second review); all three are left as they were.

## Amendment B (2026-10-23): the profile `three-observing-years/1`

Adopted by the maintainer on 2026-10-23, with the ROADMAP's scope amendment B and the plan
`reopen/stage-1/plan-b/README.md` (frozen on adoption). Nothing here changes a result already
recorded.

**Precedence.** For the profile `three-observing-years/1` only, this amendment supersedes the
population, the sizes and the SNR bands' quotas of sections 2 and 4 and the confirmation's
population of section 5; sections 1 (the criteria), 3 (the SNR bands' definition), 5 (the rule of
development and confirmation) and 6 to 12 apply as written. For every earlier version, the original
sections, records and procedures stand unchanged.

**The input of the domain** (the same for the profile O2 and for the generator's check): per
sector, the product's cadence timestamps and quality flags, the cadences kept by the plan's quality
mask, **before any filter that reads a flux or flux-error value** (the adapter today drops
non-finite flux before it builds the spans, `adapter.py`, lines 440 to 455; the profile's
implementation records the pre-filter timestamps' summary per sector so that the domain never
depends on a flux value); in the synthetic harness, the generated timestamps. Each sector is
labelled by the year of its first kept cadence, as the adapter does (`adapter.py`, line 577).
Definitions: a sector's **span** is its last kept timestamp minus its first plus one cadence; an
**internal gap** is an interval between consecutive kept timestamps longer than 10 minutes; the
**orbit gap** is the sector's longest internal gap, and the two parts on either side are its
**orbits**; its **coverage** is the number of kept cadences times 120 s over its span.

**The operational domain** (tolerances fixed here, before any result):
- **D1, years:** exactly three observing years (the distinct year labels of the sectors; the
  engine's count, `holdout.py`, line 1910). Never a selection of three years out of a longer curve.
- **D2, sectors:** exactly one sector in each observing year (three sectors).
- **D3, cadence:** the two-minute cadence (full-frame-image cadences are outside): every interval
  between consecutive kept timestamps that is not an internal gap equals `k × 120 s` within
  ± 0.5 s, with `k` from 1 to 4 (`k − 1` missing cadences: an isolated masked cadence gives about
  240 s); the residual `interval − k × 120 s` is the timing tolerance; the missing cadences count
  toward the coverage of D4.
- **D4, each sector:** each orbit 12.5 to 14.0 d long; the orbit gap 0.5 to 2.0 d; at most four
  other internal gaps, each at most 6 h; coverage at least 0.84.
- **D5, spacings:** the two separations between consecutive sectors' first timestamps, each either
  **about one year** (345 to 385 d) or **about two years** (710 to 750 d), **at most one** about two
  years.

**Why these properties and these widths.** The holdout's train ephemeris and its extrapolation to
the hidden year depend on the times through differences: the separations (D5) set the lever of the
timing diagnosis (`reopen/m4-implementation-map.md`, Amendment 28), the sampling (D3) and the
orbits, gaps and coverage (D4) set the windows' and the replica bands' coverage. The widths are
design choices, fixed before any result: ±20 d around one and two years change the extrapolation's
lever by about 5% and 3%, inside one bin of the stopped fraction's steep dependence on the lever
read in the two-year diagnosis (`reopen/stage-1/viability/two-year-results.md`, section a); D4
keeps a two-orbit sector with one downlink-like gap and limited losses; D3's ±0.5 s is far below
the windows' width (hours) and the cadence the plan assumes (`exptime_seconds` 120). **Their
adequacy for real sectors is not claimed:** a real sector outside them is outside the domain.

**The calendar date.** The timing geometry depends on differences only, but the complete engine is
not invariant under a shift of every date: the prewhitening bins the **absolute** phase
(`prewhiten.py`, lines 136 to 158, which decides the components it accepts), so a shift changes
its statistic. The domain therefore names no calendar year; the generator draws the first sector's
start uniformly over one year, which randomizes the absolute phase of every variability period it
injects (0.3 to 5 d), so the population represents the date's effect statistically; no
equivalence for a particular date is claimed.

**The represented geometries** (the generator's primitive proposals use the uniform distributions
listed here, followed by the declared rejection; the realized quantities, some of them derived,
such as the coverage, or shaped by the rejection, must meet the generator's acceptance 2,
`reopen/stage-1/plan-b/README.md`, section 3; the same available geometries for every class,
allocated with the declared rounding): **G-a**, both separations about one year; **G-b**, one
about one year and one about two years, in either order (50 : 50); each separation uniform in its
interval; the first sector's start uniform over one year from 1325.0 BTJD; each orbit's length
uniform in 12.5 to 14.0 d; the orbit gap uniform in 0.5 to 2.0 d; from 0 to 4 loss blocks
(uniform count), each of a length uniform in 10 min to 6 h, placed uniformly inside the orbits;
single-cadence losses at a rate uniform in 0 to 5%, never four or more adjacent; each timestamp
jittered uniformly by ±0.25 s (so every residual of D3 stays within ±0.5 s; the residuals'
distribution is triangular, not uniform). The coverage floor 0.84 of D4 is an acceptance floor: the
generator's lowest coverage is about 0.844, so the floor itself is not claimed as generated. A draw
that would fall outside D1 to D5 (for example a sector across a year boundary) is redrawn by the
generator's own rule, recorded with its reason, never by an engine output.

**The population (B2), per noise model** (white; AR(1) correlated; the noise models, mechanisms and
proportions of section 4): planets, 360 per band (below, near, measurable), 180 without and 180 with
variability (`three_years`-type and `variability_some_years`-type); false positives, below 100,
near 100, measurable 250, the four mechanisms as section 4 allocates them (for 250: 63, 63, 62,
62); curves without a transit, 2200 (white) and 600 (correlated), with section 4's mixture (40%
pure noise, 30% trend, 30% trend with variability, rounded as section 4). **The layouts:** within
each class, noise model, band (where the class has one) and regime or mechanism, the cases are
split between G-a and G-b, G-a taking the extra case when the count is odd. Bands, mechanisms and
parameters drawn as section 4 from the injected truth only. **The variability-free year**
(`var_absent_year`) keeps its uniform draw over three positions, mapped to the curve's own three
observing years, so that exactly two observed years carry variability in every
`variability_some_years` planet.

**The criteria:** C1 to C6 of section 1 unchanged (limits, rule, denominators), their acceptance
counts at the new sizes: C1 at most 26 of 360 per band and noise model; C2 at least 164 of 250; C3
at most 59 of 360 (planets) and 39 of 250 (false positives); C4 at most 14 of 2200 (white) and 20 of
600 (correlated). **Added, per noise model and regime in the measurable band:** G1, planets
delivered as SURVIVED or WEAKENED with signal identity, lower bound at least 0.60 (at least 120 of
180); G2, planets refuted, upper bound at most 0.10 (at most 11 of 180). **G3 = C2, G4 = C4, G5 =
C3**, each with its per-mechanism or per-regime publication and no added limit; G6, the cost
measured on the pilot fits the budget. One-sided 95% exact Clopper-Pearson, each criterion judged
individually. **The holdout criteria** of specification B (B5: the false PASS per target, upper
bound at most 0.02) and of specification A (W1e: the false FAIL at reduced depth, upper bound at
most 0.02) are binding acceptance criteria of the main study, their sizing rules fixed in the
pilot's declaration, before the pilot.

**The planning rates** (0.70 delivered, 0.05 refuted per regime) are hypotheses for the sizing, not
observed performance; a criterion's chance of passing at them (G1 0.85, G2 0.81, C1 0.975) is
**not** the chance of approving the phase. Criteria and counts are fixed before any new result and
are never lowered afterwards. A criterion whose required coverage or minimum is not reached is not
met.

**The populations and their roles:** the **development** population (the pilot, X5, and the
before-and-after comparisons of each change, section 6 of this protocol, on identical inputs); the
**main confirmation** (X6: B2, seeds from a future drand round declared before, run once at the end
on frozen code); the **independent replication** (X7: the same composition and sizes, its own drand
round declared at its own checkpoint after X6's result and before that round is available, run only
if X6 passes). **The configuration is chosen on development data and frozen before X6**; nothing is
chosen on X6's or X7's data. **The synthetic study passes only if X6 and X7 both pass.** Spec C's
confirmation is a separate lot (an error model's confirmation, not the population study).

**If X7 fails after X6 passed:** the failure is a result and is never ignored; both lots are
reported in full; neither is chosen as the more favourable one, and they are never pooled to pass;
the synthetic study is not accepted and the profile stays proposed for validation; the calibration
on real targets does not start; any later attempt needs the maintainer's recorded decision, under
the rule for criterion failures (an amendment declared after the result, Codex's design review, new
seeds, the same criteria and sizes), with its own authorization.

## Study status

**Closed on 2026-10-14 by a scope decision of the maintainer**, without a demonstration that
approval was impossible (record: `population/closure-record.md`).

- M0 to M3: FAILS on the development population, with full integrity
  (`population/campaigns/dev-campaign-1/`).
- Confirmation: not run; no drand round was declared.
- M4 and M5: not implemented, not measured.
- Proposed corrections: hypotheses and plans, with 6 of the 9 rows of their last revision still
  open (`population/corrections-plan/`).
- The calibration population of the corrections plan: never generated nor analyzed.

Nothing in this document changes with the closure: the criteria, their limits, the frozen
manifest, `points.json` and the results stay as recorded above. The conditions for a future
resumption are in the closure record.

**Resumed for the profile `three-observing-years/1` on 2026-10-23** under Amendment B (above),
following the gates of `reopen/stage-1/plan-b/README.md`; nothing of it has run yet, and every
execution has its own authorization. The closure's record and the results of the original
population stay as they are.
