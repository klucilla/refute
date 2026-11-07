# TIC-1: SURVIVED

**Verdict: `SURVIVED`.** every test passed

> A verdict is about a claim, never about its authors. Refute produces candidates and verdicts only: nothing here is a confirmed discovery, and nothing has been submitted to any scientific body.

> **Scope.** Refute is calibrated only in an easy regime defined by pre-registered selection filters (see the claim's protocol attachment): confirmed planets with orbital periods between 0.5 and 10 days, transit depths of at least 1000 ppm, TESS magnitude 12 or brighter, a single known planet in the system, and SPOC 2-minute data in at least two calendar years; false positives with the same period, depth and magnitude limits. The calibration says nothing about longer periods, shallower transits, fainter stars, multi-planet systems or other data products.

## Claim

- Claim: `synthetic-v02` (calibration)
- Hypothesis: h
- Target: synthetic (TIC 1, calibration role: exploration)

## Signal

| Quantity | Found | Published |
|---|---|---|
| Period (d) | 3.7000046 | n/a |
| Epoch (BJD_TDB) | 2.45833e+06 | n/a |
| Duration (h) | 2.205 | n/a |
| Depth (ppm) | 1860.9 | n/a |
| SNR | 115.2 | |

- Relative period error: n/a (tolerance n/a, within: n/a, alias: none)

## Gauntlet

| Test | Status | Severity | Result |
|---|---|---|---|
| snr | PASS | gate | SNR 115.2 >= 7.1 |
| odd_even | PASS | fatal | odd/even depth difference 2.35 sigma (<= 3.0) |
| secondary_eclipse | PASS | fatal | no significant eclipse at phase 0.5 (1.14 sigma) |
| plausibility | PASS | fatal | companion radius 0.42 R_Jup and duration ratio 0.75 are plausible |
| centroid_shift | PASS | fatal | transit source consistent with the target (offset 0.01 px, 0.0 sigma; 3 sector(s), 56160 cadences) |
| aperture_depth | PASS | fatal | depth does not grow with the aperture (ratio 1.00, -0.1 sigma; transit detected at 64.6 sigma) |
| nearby_contamination | PASS | warning | TIC cone query of 120 arcsec returned 0 source(s): 0 within 21 arcsec, none could produce the signal; median CROWDSAP 1.00 |
| period_alias | PASS | fatal | the dip needs a transit on top of a sinusoid (BIC gain 2136, 1419 in-transit cadences); not near a known systematic period |
| systematics | PASS | warning | no problem in 3 sub-checks: momentum dumps (24 in the quality column), SAP versus PDCSAP, background |
| holdout_by_year | PASS | fatal | predictions confirmed in 3 of 3 hidden years |

The `eb_catalog` test is not part of this gauntlet: the claim attaches no eclipsing-binary catalog.

## Blind holdout by year

Each year is hidden in turn, and the ephemeris is fitted on the other years only. In each round that reaches the measurement, the whole hidden year is detrended once before any logged read, with each predicted window masked out to the inner edge of its baseline band; that step is not logged, and its outlier clipping can drop hidden cadences. After it, the test reads only the predicted transit windows, the phase-0.5 control windows and their baseline bands, and every such read is logged.

| Hidden year | Status | Windows with data | Hidden SNR | Control SNR (phase 0.5) |
|---|---|---|---|---|
| 2018 | PASS | 7 | 47.7 | 1.4 |
| 2019 | PASS | 7 | 58.7 | 0.2 |
| 2020 | PASS | 7 | 40.8 | 1.4 |

## Data

- Product: synthetic light curve (refute.packs.tess.synthetic), flux column `flux`, quality bitmask `none` (value None), read with numpy.load
- Sectors: [1, 2, 3]; observing years: [2018, 2019, 2020]; cadences used: 56160
- Stellar parameters: synthetic (refute.packs.tess.synthetic), TIC version synthetic, retrieved None: R = 1.000 +- 0.050 Rsun, M = 1.000 Msun
- File hashes and source URLs: `data/manifest.json`

## Independent review

Reports by fresh, read-only reviewer sessions are attached after the verdict, in
`review/` (index: [review/index.md](review/index.md)), following
`docs/reviewer-protocol.md`. Reviewers raise objections; they never change the
verdict. `refute check-dossier` verifies that the analysis and `verdict.json` are
unchanged since the reviews were attached. No `review/` folder means no review.

## Provenance

- Claim SHA-256: `None`
- Code SHA-256: `None`
- Lock commit: `None`; run commit: `None`
- Run: `None`, Refute None
- Reproduce: see `REPRODUCE.md`. Integrity: `MANIFEST.sha256`.
