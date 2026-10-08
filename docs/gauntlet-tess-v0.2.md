# TESS gauntlet v0.2

This document describes what the TESS pack does to a target from v0.2 on, and the
pass/fail criterion of every test. It extends [gauntlet v0.1](gauntlet-tess-v0.1.md):
everything there still applies unless this document says otherwise. All thresholds
are defaults of the claim schema and are written explicitly into every locked claim.

**How the thresholds were set.** Each threshold below was chosen by reasoning about
the measurement, then checked on synthetic data only: the unit tests (one case that
must fail and one that must pass for every test) and the synthetic study at the end
of this document. No threshold was set or changed using real light curves or pixel
data. Synthetic scenes are idealized (Gaussian point-spread function, no pointing
jitter, no scattered light), so detection rates measured on them are upper bounds
and false-alarm rates are lower bounds for real data.

## Data (adapter v0.2)

- **Downloads** run one file at a time. Every downloaded FITS file must have exactly
  the size declared by its own headers; an incomplete file is deleted from the cache
  before the error is raised, so a retry downloads it again (issue #1). The fetch
  manifest schema is `refute-tess-fetch-2`.
- **Light curves** (SPOC 2-min) are read directly with astropy. Kept cadences:
  `QUALITY & bitmask == 0` with lightkurve's `default` TESS bitmask (its numeric
  value, 17087 with lightkurve 2.6.0, is recorded) and finite time, PDCSAP flux and
  error. Each sector is divided by its median PDCSAP flux, as in v0.1. SAP flux and
  SAP background of the same cadences are divided by the median SAP flux. The times
  of every momentum dump (quality bit 32) are read from the raw quality column
  before any cadence is removed. `CROWDSAP` and `FLFRCSAP` come from the light-curve
  header.
- **Target pixel files** (SPOC 2-min) are downloaded for every sector: the
  background-subtracted flux cube, the SPOC optimal aperture (bit 2 of the aperture
  image) and the target position in array coordinates, from the aperture HDU's WCS
  and the target's `RA_OBJ`/`DEC_OBJ`. Only the cadences kept in the same sector's
  light curve are used: a target pixel file also contains cadences whose PDCSAP flux
  SPOC left empty, and the pixel tests must use the same data as the official SPOC
  light curve. The number of dropped cadences per sector is reported by
  `centroid_shift`. (Found on the development target; see the v0.2 protocol.)
- **TIC**: besides the stellar parameters, the target row's `disposition`,
  `duplicate_id` and coordinates are recorded, and a cone query returns every TIC
  source within `neighbor_radius_arcsec` (120 arcsec) with its Tmag, separation and
  disposition.
- All of this is used only by the battery below. The blind holdout still receives
  only the PDCSAP light curve and the sector time spans.

## Coverage (no PASS without examined data)

Every test reports its coverage (the data it actually examined) and the engine turns
a `PASS` with zero coverage into `INCONCLUSIVE` ([verdicts](verdicts.md)). An audit
before the v0.2 lock looked for every path where a check that examined nothing could
pass; the fixes below are corrections of correctness, not of thresholds:

| Test | Coverage unit | INCONCLUSIVE instead of PASS (or of FAIL, or a crash) when |
|---|---|---|
| `centroid_shift` | pixel-file cadences | no usable sector; the detection floor is now `centroid_shift.max_sigma` from the claim (it was a hard-coded 3.0, same value) |
| `aperture_depth` | pixel-file cadences | the transit is not detected at `max_sigma` in either aperture (before: "the depth does not grow" passed vacuously) |
| `nearby_contamination` | TIC cone queries | no query, no target Tmag, or no CROWDSAP value; an empty query result passes and the report says which query was made |
| `period_alias` | in-transit cadences | fewer in-transit cadences than one transit at `events.min_coverage` (before: an empty box gave a fatal FAIL) |
| `systematics` | sub-checks run | any applicable sub-check could not run (strict rule): fewer than 3 transits for the dump check; no CROWDSAP, no measured transit or a non-positive depth for the SAP and background checks; the reason of each is reported. A problem found by another sub-check still gives FAIL |
| `eb_catalog` | catalog rows scanned | no scan record (`eb-catalog-scan`), the target was not part of the extraction, or the extraction radius is smaller than the match radius (before: an empty catalog file passed) |
| `holdout_by_year` | hidden-year windows measured | a round whose windows cannot be measured at any period correction (before: a crash) |

## Shared measurement

The pixel and systematics tests measure a time series (aperture flux, centroid, SAP
flux, background) the same way: it is detrended additively with the robust local
quadratic of v0.1 (transits of the candidate masked), and each transit contributes
the mean of its local baseline band minus the mean inside the transit, as in the
v0.1 per-event depths. Group errors are the larger of the white-noise error and the
event-to-event scatter.

## New tests

| Test | Fails when | Severity | INCONCLUSIVE when |
|---|---|---|---|
| `centroid_shift` | transit source offset from the target with significance >= **3.0** sigma **and** distance >= **0.5** pixel | fatal | no usable sector (no target pixel file, no WCS, too few cadences, transit not seen in the aperture flux at 3 sigma) |
| `aperture_depth` | depth in a dilated aperture exceeds the core depth by >= **3.0** sigma **and** by a factor >= **1.2** | fatal | no usable pixel data or no transit coverage |
| `nearby_contamination` | a TIC source within **21** arcsec could produce the signal with an eclipse depth <= **1.0**, or the median `CROWDSAP` is below **0.8** | warning | no neighbor query, or no Tmag for the target |
| `period_alias` | adding a transit box to a sinusoid at the found period improves the BIC by less than **10** (fatal); otherwise, period within **1%** of a known systematic period (warning) | fatal or warning | never |
| `systematics` | at least **50%** of the transits (at least **3** with data) fall within duration/2 + **1 h** of a momentum dump; or the SAP depth differs from `CROWDSAP` x PDCSAP depth by >= **3** sigma and >= **50%**; or the background rises in transit by >= **3** sigma and >= **50%** of the SAP depth | warning | no SAP, background or quality data |
| `eb_catalog` | an eclipsing-binary catalog entry within **21** arcsec (or with the target's TIC ID) has a period equal to **1, 2 or 0.5** times the found period within **1%** (fatal); a match without that period (warning) | fatal or warning | no target coordinates. Runs only when the claim attaches catalogs |

### centroid_shift

For each sector, the flux-weighted centroid (x, y) inside the SPOC aperture of the
target pixel file is computed at every cadence. With aperture flux F, fractional
depth d and out-of-transit centroid c_out, a source at position s that loses d*F
moves the centroid by dc = d (c_out - s) / (1 - d), so

    s = c_out - dc (1 - d) / d.

This locates the light that actually dims, whatever other stars put into the
aperture. The offset s - target (target position from the file's WCS) and its error
(from the errors of dc and d) give a chi-square with 2 degrees of freedom per
sector; the sum over sectors is converted to a one-sided Gaussian significance.

- 3 sigma is the vetting convention already used by the odd/even and secondary
  tests.
- 0.5 pixel (about 10 arcsec; a TESS pixel is about 21 arcsec): an absolute floor,
  so that at high signal-to-noise a tiny systematic offset (point-spread-function
  asymmetry, WCS error) does not refute a planet. On synthetic transits on the
  target, the offsets stay below 0.05 pixel.
- Without a WCS the test is INCONCLUSIVE, never PASS.

### aperture_depth

The core aperture is the SPOC aperture pixels within **1.5** pixels of the target
(at least the single closest pixel); the large aperture is the SPOC aperture
dilated by **1** pixel. For a transit on the target, the large aperture only adds
light from other sources, so the depth stays the same or decreases (ratio <= 1 in
every synthetic on-target case). A signal from a star outside the core gets deeper
as the aperture grows to include that star. The errors of the two depths are
combined as if independent; the apertures overlap, so this overestimates the error
of the difference and makes a FAIL harder, never easier. The 20% margin on the
ratio guards against systematics that the synthetic scenes do not have.

### nearby_contamination

A neighbor `dm` magnitudes fainter than the target, assumed to have the same
fraction of its light in the aperture, needs an eclipse of depth
`depth x 10^(0.4 dm)` to produce the observed (crowding-corrected) depth. A source
closer than one TESS pixel (21 arcsec) cannot be separated from the target by the
centroid and aperture tests, so if such a source could produce the signal (needed
eclipse depth <= 1, the physical limit) the claim is weakened, never refuted: the
neighbor *could* be the source, it is not shown to be. Neighbors without Tmag are
counted as able to produce the signal. TIC rows with disposition SPLIT, DUPLICATE
or ARTIFACT are ignored (they are not distinct stars). A median `CROWDSAP` below 0.8
(more than 20% of the aperture's flux from other sources) is also a warning.

### period_alias

The PDCSAP light curve is detrended with a window of at least **3** periods
(transits masked), so a variation at the found period survives. Two models are
fitted to all points: a Fourier series with **2** harmonics at the found period,
and the same series plus a box at the transit. If the box does not lower the BIC by
at least 10 (Kass and Raftery's "very strong" level), the dip is part of a periodic
variation (stellar variability, an ellipsoidal variable) and not a transit: fatal.

A first version compared a box alone with a sinusoid alone. On a synthetic star
with variability at the candidate's period it preferred the sinusoid, which would
refute real planets around stars whose rotation shares the period. The joint model
asks the right question: does the dip need a transit on top of the variability?
`tests/test_battery.py` keeps that case.

The second part is a warning when the period is within 1% of a period of a known
TESS systematic: 13.7 days (the TESS orbital period; Ricker et al. 2015, Journal of
Astronomical Telescopes, Instruments, and Systems 1, 014003), its harmonics 13.7/2,
13.7/3 and 13.7/4 days, and 1 day.

### systematics

Three warnings, each a reason to doubt the signal without refuting it:

- **momentum dumps**: at least half of the transits (and at least 3) fall within
  duration/2 + 1 hour of a momentum dump;
- **SAP versus PDCSAP**: PDCSAP removes the flux of other sources and divides by the
  flux fraction, so the SAP depth should equal `CROWDSAP` x the PDCSAP depth. A
  difference of at least 3 sigma and at least 50% means the PDC correction made or
  changed the signal;
- **background**: the SAP background rises in transit by at least 3 sigma and by at
  least 50% of the SAP depth: an over-subtracted background can create a dip.

### eb_catalog

Catalogs are claim attachments with role `eb-catalog`, so the lock covers them, in
the normalized format `refute-eb-catalog-1` (a CSV file with the header
`catalog,source_id,tic_id,ra_deg,dec_deg,period_days`; `tic_id` and `period_days`
may be empty; see `src/refute/packs/tess/ebcatalog.py`). The script that builds a
snapshot records the source URL, retrieval time and SHA-256 of the raw catalog.
Without such attachments the test is not part of the gauntlet, and every dossier
report says so.

Because a catalog may share sources with the dispositions used to select known
false positives, a calibration claim can list `eb_catalog` in
`pass_criteria.flag_excluded_tests`: a false positive then counts as *flagged* only
if its verdict, recomputed with the same rules from the other tests, is REFUTED. The
count with every test is reported as information. The degeneracy guard always uses
the full verdict: a planet refuted by a catalog counts against Refute.

## Changes to v0.1 tests

- **d. plausibility** (issue #3): if the TIC row has disposition SPLIT, DUPLICATE
  or ARTIFACT, its stellar parameters may not describe the star that dominates the
  light curve, and the test is INCONCLUSIVE with that reason. A TIC Tmag that
  differs by more than **1** magnitude from the target's catalog Tmag is listed as a
  data-quality warning in the report (not a test).
- **e. holdout_by_year** (issue #2): the hidden year is detrended with a window of
  at least **3** times the widest masked span (window plus baseline gap), so knots
  inside a wide mask no longer extrapolate the trend. A round is INCONCLUSIVE, not
  FAIL, when the train-only timing uncertainty in the hidden year exceeds **1**
  transit duration: the windows then cannot locate the transits, and a
  non-detection would not be evidence. On synthetic pure noise the rounds are now
  INCONCLUSIVE instead of FAIL (the train "transits" have a reduced chi-square far
  above 1); noise never passes, and its gate fails anyway.

## Synthetic validation

Unit tests (`tests/test_battery.py`, `tests/test_ebcatalog.py`,
`tests/test_v02_fixes.py`) give every test a case that must fail and one that must
pass:

| Test | Must fail | Must pass |
|---|---|---|
| `centroid_shift` | eclipse on a neighbor 2 pixels away (scenario `blend`) | transits and eclipses on the target (`planet`, `planet_three_years`, `eb_equal`) |
| `aperture_depth` | the same blend | `planet`, `eb_equal`, `vanishing` |
| `nearby_contamination` | a star 2 mag fainter at 10 arcsec; crowding 0.6 to 0.7 | a star 8 mag fainter at 10 arcsec; a bright star at 60 arcsec; an ARTIFACT row |
| `period_alias` | a pure 0.7-day sinusoid (`sinusoid`); a period of 13.7/4 days (warning) | transits, eclipses, a transit on a star varying with the same period |
| `systematics` | transits on momentum dumps; a SAP light curve without the dip; a background that rises in transit | a clean transit |
| `eb_catalog` | a catalog entry 5 arcsec away at 2 x the period; an entry with the target's TIC ID; an entry at 10 arcsec with another period (warning) | an entry 60 arcsec away; an empty catalog |
| plausibility (#3) | a 25.7% eclipse with a normal TIC row (refuted) | the same eclipse with a SPLIT, DUPLICATE or ARTIFACT row (INCONCLUSIVE, not refuted on unreliable parameters) |
| holdout (#2) | `vanishing` still fails | one training sector projected about five years with 15-minute timing scatter: no round fails |

### Synthetic study

`scripts/synthetic_battery_study.py` (seed 20261008, 200 cases per kind) runs the
battery with these thresholds against the injected ephemeris:

- **planet**: a transit on the target with depth 1000 to 10000 ppm, noise 300 to
  1500 ppm, period 0.8 to 9 days, duration 1 to 4 hours, stellar variability up to
  0.3% (at the planet's period in a quarter of the cases), and in half of the cases
  a neighbor 1.5 to 4 pixels away with 5% to 50% of the target's flux and no
  signal. Every failure is a false alarm;
- **blend**: the same signal range produced by an eclipse on a neighbor 1.5 to 3
  pixels away with 10% to 50% of the target's flux;
- **sinusoid**: a pure sinusoid with the same amplitudes at the candidate period.

| Case | Test | PASS | FAIL fatal | FAIL warning | INCONCLUSIVE |
|---|---|---|---|---|---|
| planet | centroid_shift | 200 | 0 | 0 | 0 |
| planet | aperture_depth | 200 | 0 | 0 | 0 |
| planet | nearby_contamination | 200 | 0 | 0 | 0 |
| planet | period_alias | 192 | 0 | 8 | 0 |
| planet | systematics | 200 | 0 | 0 | 0 |
| blend | centroid_shift | 0 | 200 | 0 | 0 |
| blend | aperture_depth | 0 | 200 | 0 | 0 |
| blend | nearby_contamination | 200 | 0 | 0 | 0 |
| blend | period_alias | 195 | 0 | 5 | 0 |
| blend | systematics | 200 | 0 | 0 | 0 |
| sinusoid | centroid_shift | 45 | 0 | 0 | 155 |
| sinusoid | aperture_depth | 28 | 0 | 0 | 172 |
| sinusoid | nearby_contamination | 200 | 0 | 0 | 0 |
| sinusoid | period_alias | 18 | 179 | 3 | 0 |
| sinusoid | systematics | 142 | 0 | 2 | 56 |

Reading the table:

- No fatal false alarm in 200 synthetic planets. The 8 period-alias warnings are
  periods within 1% of a systematic period, as designed.
- Every synthetic blend 1.5 to 3 pixels away is refuted by both pixel tests. Blends
  closer than about one pixel are not separable this way; `nearby_contamination`
  covers them with a warning.
- 179 of 200 sinusoids are refuted by `period_alias`; 21 are not, so stellar
  variability can still slip through. Most sinusoids leave too few out-of-transit
  cadences for a centroid measurement, hence INCONCLUSIVE.
- The coverage audit before the lock changed only the sinusoid rows: 172 sinusoids
  that `aperture_depth` used to PASS without seeing any transit in the pixels, and
  56 that `systematics` used to PASS with sub-checks that could not run, are now
  INCONCLUSIVE. The planet and blend rows did not change.
- The study also found a defect before any real data were used: a significance
  conversion failed for chi-square values with p below about 1e-17. It was fixed and
  a unit test covers it.

## Known limitations of v0.2

- Pixel tests assume the SPOC aperture and WCS are right; the synthetic scenes have
  ideal Gaussian point-spread functions, no pointing jitter and no scattered light.
- A neighbor closer than about one pixel, or a hierarchical triple, is only flagged
  as possible (warning), never refuted.
- No radial velocities: a low-mass stellar companion of planet-like size with no
  secondary eclipse still survives.
- Catalog cross-matching depends on the catalogs attached to the claim.
