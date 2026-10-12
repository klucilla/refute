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
