# TESS gauntlet v0.1

This document describes exactly what the TESS pack does to a target, and the
pass/fail criterion of every test. All thresholds below are defaults of the claim
schema and are written explicitly into every locked claim. They were fixed using
synthetic data only, before any calibration light curve was analyzed.

## Data

- **Product**: TESS SPOC 2-minute light curves (`author=SPOC`, `exptime=120`),
  downloaded from MAST with lightkurve and cached in `.cache/`.
- **Flux**: `PDCSAP_FLUX` with lightkurve's `default` SPOC quality bitmask (its
  numeric value is recorded). NaNs are removed and each sector is divided by its
  median. FFI products (TESS-SPOC, QLP) are not used in v0.1.
- **Stellar parameters**: TESS Input Catalog (TIC) row queried from MAST at fetch
  time: radius and its error, mass, Teff, log g, Tmag, TIC version, retrieval time.
- **Observing year**: calendar year of a sector's first cadence (BTJD converted to
  a date treating TDB as UTC; the 69 s difference does not matter). It is the
  unit hidden by the blind holdout.
- Every file's SHA-256 is recorded at download and verified at every load.

## Detrending

Robust local quadratic: knots every 0.1 d; at each knot a quadratic is fitted to
the unmasked flux within a 1-day window, with two rounds of 3-sigma clipping;
between knots the two neighbouring quadratics are blended linearly. The search
uses an unmasked detrend. Tests a to d use a second detrend in which points within
one transit duration of each transit of the found ephemeris are masked, so the
transit does not pull the trend. Points more than 5 robust sigma **above** the
trend are removed (flares); points below are never removed.

A running median was tried first and rejected on synthetic data: on a star with
slow sinusoidal variability it left curvature residuals large enough to pass the
SNR gate with no transit present.

## Period search: two-stage BLS

1. **Stage 1, per sector**: the light curve is binned to 10 minutes; astropy's
   `BoxLeastSquares.autopower` grid covers 0.5 days to min(20 days, sector span / 2)
   with durations 0.5 to 8 hours; the 5 strongest distinct peaks (1% apart) are
   kept with their signal detection efficiency (SDE).
2. **Clustering**: peaks from all sectors within 1% in period are merged; the 5
   clusters with the highest summed SDE are refined at P, 2P and P/2.
3. **Stage 2, hierarchical refinement**: from the cluster's strongest sector,
   data are added in growing spans (the sector, its block of contiguous sectors,
   then other blocks by distance in time). The grid step is
   `duration * P / (6 * span)` and its half-width `1.5 * duration * P / previous span`,
   so the cycle count across multi-year gaps is chosen by the data.
4. The refined candidate with the highest log-likelihood on all binned data wins.
   It is re-evaluated on unbinned data with a fine duration grid (0.5 to 1.5 times)
   and a fine period scan (one tenth of the last grid step).

Limitation: periods longer than half of the longest single sector span are not
searched in stage 1.

## Per-event depths

Tests b and c measure each event (transit, or phase-0.5 window) separately: mean
flux in a baseline band (from 0.25 to 1.5 durations outside the event) minus mean
flux inside the event. Events need half of their expected cadences. Group means
use inverse-variance weights; their error is the **larger** of the white-noise
error and the scatter of the individual depths divided by sqrt(n) (n >= 3), so red
noise and real event-to-event variation are not mistaken for a detection.

## Tests

| Test | Criterion | Severity on failure | INCONCLUSIVE when |
|---|---|---|---|
| a. `snr` | BLS depth / depth error >= **7.1** | gate | never (no candidate = FAIL) |
| b. `odd_even` | \|depth(even) - depth(odd)\| / combined error <= **3.0** | fatal | fewer than 2 even or 2 odd transits |
| c. `secondary_eclipse` | phase-0.5 depth / error < **3.0** -> PASS. Otherwise FAIL: fatal if phase-0.5 depth / primary depth >= **0.10**, warning if below | fatal or warning | no data at phase 0.5 |
| d. `plausibility` | implied companion radius sqrt(depth) * R_star <= **2.5 R_Jup** (else fatal FAIL); duration <= **1.5** times the longest central transit of a circular orbit, P/pi * asin((1+k) R_star / a), a from Kepler's third law (else warning FAIL) | fatal or warning | TIC radius missing, without error, or with relative error > **0.3**; or no stellar mass (TIC mass, else from log g and radius) for the duration part. Never PASS in these cases |
| e. `holdout_by_year` | see below | fatal | fewer than 2 observing years, or no conclusive round |

Why these numbers:

- 7.1 is the classic Kepler detection threshold for a transit signal.
- 3 sigma is the common vetting threshold for odd/even and secondary eclipses.
- A 10% depth ratio separates a stellar secondary eclipse (deep) from a planet's
  occultation (hot Jupiters reach a few hundred ppm on a 1% transit), which is
  only a warning.
- 2.5 Jupiter radii is above the largest known inflated planets (about 2 R_Jup),
  so real planets are not refuted, while an equal-depth eclipsing binary (found by
  BLS at half its period, passing odd/even and secondary checks) is.
- A factor 1.5 on the circular-orbit maximum duration leaves room for eccentric
  orbits.

## Blind holdout by year (test e)

The holdout receives only the raw normalized light curve, the sector time spans
(metadata) and the test plan. It has **no argument for the candidate found on all
data**, and tests check that its output is byte-identical whatever the global
search returns. For each observing year H in turn:

1. **Train** = all other years, detrended without a mask; the full two-stage
   search runs on train only. No candidate: round INCONCLUSIVE.
2. Train is re-detrended with a mask at the **train-only** ephemeris. Individual
   transit times are measured by a chi-square scan of a box (1-minute steps,
   +-half a duration; error from delta chi-square = 1, floored at half a cadence;
   edge minima discarded). Fewer than 3 times: round INCONCLUSIVE.
3. A weighted linear ephemeris is fitted (errors inflated by sqrt of the reduced
   chi-square when above 1).
4. **Predicted windows** in H come from that ephemeris and H's sector time spans:
   half-width = duration/2 + 3 * sigma_T(epoch), sigma_T from the full covariance.
   Control windows are placed at phase 0.5.
5. The hidden year is wrapped in `HiddenYear`: its raw data are detrended with a
   mask made only of the predicted windows, and afterwards data can be read only
   inside a registered window or its registered baseline band. Any other access
   raises an error and every access is logged in the dossier.
6. **Measurement**: a box of the train duration is placed in every window at
   `t_pred + (epoch - n_ref) * dP`, scanning one period correction dP over
   +-3 sigma_P (steps moving the farthest window by at most duration/8). In each
   window the depth is measured against a straight line fitted to the window's
   out-of-box points. Window depths are stacked with inverse-variance weights and
   an error that is the larger of the white-noise error and their scatter. The
   SNR at the best dP must be **>= 5.0**, with at least **2** windows having half
   of their expected cadences; otherwise the round is INCONCLUSIVE (too few
   windows) or FAIL (no signal). The control windows get the identical procedure;
   their SNR is reported, not judged, and shows the false-alarm level.
7. The test PASSES if every conclusive round passes, FAILS if any round fails.

Why the window scan: when one training year predicts another year, the
ephemeris uncertainty can exceed the transit duration; averaging the whole window
would dilute a real transit several-fold and refute real planets. Why local lines
and scatter errors: on synthetic data, a signal-free hidden year with stellar
variability otherwise produced a spurious 9-sigma "confirmation".

## Synthetic validation

`tests/` runs every test on synthetic light curves (no network): a planet
(passes everything), pure noise (gate fails), an eclipsing binary with a deep
secondary eclipse (secondary test fails), one with unequal odd and even eclipses
(odd/even fails), an equal-depth binary (plausibility fails), a signal present
only in the training year (holdout fails), a missing TIC radius (plausibility
inconclusive) and a single observing year (holdout inconclusive).

## Known limitations of v0.1 (addressed from v0.2)

No centroid or pixel-level tests, so a signal from a nearby star cannot be told
apart from one on the target. No aperture-dependent depth, period-alias battery,
eclipsing-binary catalog cross-match or momentum-dump checks. No radial velocities,
so a low-mass stellar companion of planet-like size survives. The calibration
covers only the easy regime described in `calibration/PROTOCOL.md`.
