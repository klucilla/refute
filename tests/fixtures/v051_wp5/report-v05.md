# TIC-1: SURVIVED

**Verdict: `SURVIVED`.** every test passed

> A verdict is about a claim, never about its authors. Refute produces candidates and verdicts only: nothing here is a confirmed discovery, and nothing has been submitted to any scientific body.

> **Method status: `not_validated`.** No discovery method of Refute is validated: the v0.1 and v0.2 calibrations failed, and v0.2.1 ended as not approved (docs/validation/v0.2.1/closing-2026-10-27.md). A verdict here is the deterministic outcome of the declared tests, not a validated measurement.

## Roles and stage

- Meaning of SURVIVED in this claim: the signal survived the declared decisive battery; temporal confirmation was not required; the method is not validated
- Stage of this run: 2 of 2
- Decisive tests (the verdict aggregates only these): snr, odd_even, secondary_eclipse, plausibility, aperture_depth, nearby_contamination, period_alias, systematics, edge_events, sinusoid, duty_cycle
- Diagnostic tests (reported, never part of the verdict): centroid_shift, event_consistency, holdout_by_year, single_event
- Temporal diagnostic (`holdout_by_year`): **inconclusive**. It never changes the verdict; a `pass` is not a signal confirmed in time, and a `fail` is not evidence against the signal, because the holdout is not validated.

## Claim

- Claim: `synthetic-v05` (discover)
- Hypothesis: h
- Target: synthetic (TIC 1, calibration role: exploration)

## Signal

| Quantity | Found | Published |
|---|---|---|
| Period (d) | 3.7000046 | n/a |
| Epoch (BJD_TDB) | 2458326.299375 | n/a |
| Duration (h) | 2.205 | n/a |
| Depth (ppm) | 1860.9 | n/a |
| SNR | 115.2 | |

- Relative period error: n/a (tolerance n/a, within: n/a, alias: none)

## Gauntlet

| Test | Status | Severity | Result |
|---|---|---|---|
| snr | PASS | gate | SNR 115.2 >= 7.1 |
| odd_even | PASS | fatal | odd/even depth difference 2.37 sigma (<= 3.0) |
| secondary_eclipse | PASS | warning | no significant dip or brightening at phase 0.5 (1.14 sigma) |
| plausibility | PASS | fatal | companion radius 0.42 R_Jup and duration ratio 0.75 are plausible |
| centroid_shift | INCONCLUSIVE | diagnostic | qualification failed: 3 of 3 sector(s) do not qualify |
| aperture_depth | PASS | fatal | depth does not grow with the aperture (ratio 1.00, -0.1 sigma; transit detected at 64.6 sigma) |
| nearby_contamination | PASS | warning | TIC cone query of 120 arcsec returned 0 source(s): 0 within 21 arcsec, none could produce the signal; median CROWDSAP 1.00 |
| period_alias | PASS | fatal | the dip needs a transit on top of a sinusoid (BIC gain 2136, 1419 in-transit cadences); not near a known systematic period |
| systematics | PASS | warning | no problem in 3 sub-checks: momentum dumps (24 in the quality column), SAP versus PDCSAP, background |
| single_event | PASS | diagnostic | largest single-event SNR 0.24 of the total (<= 0.88) |
| event_consistency | PASS | diagnostic | per-event depths: chi2 36.0 for 20 dof, p = 0.015 |
| edge_events | PASS | warning | 0 of 21 events near a segment edge (0%) |
| sinusoid | PASS | warning | no significant sinusoid at P/2, P or 2P |
| duty_cycle | PASS | fatal | duration over period 0.025 (<= 0.5) |
| holdout_by_year | INCONCLUSIVE | diagnostic | PASS refused: no sensitivity rule or category registered (predictions confirmed in 3 of 3 hidden years) |

## v0.5 rules

- Sensitivity rule (#185): a fatal or warning test PASSes only when it could have detected its declared alternative; otherwise it is INCONCLUSIVE, with the reason. A PASS means no failure was detected with the declared sensitivity, never that an effect is absent. Each test's sensitivity is in `verdict.json` (`tests[].sensitivity`).
- SDE: the candidate's `sde` is the stage-1 SDE of the per-sector peak that seeded it (with a kept period at a multiple of the seed's, not the SDE of the kept peak); `sde_kept_peak` is the SDE of the kept period itself, computed for this report after the selection (#186). SDE of the kept peak (largest over sectors): 18.54.
- `secondary_eclipse` limits: eccentric secondaries away from phase 0.5 are not covered; a secondary alone does not classify an eclipsing binary; a planet's occultation is not modelled (#181).
- Period 3.699995743202161 d (error 4.283063556342308e-06) and epoch 2458707.3996915924 BJD_TDB (error 0.0003490311016253537), from: linear ephemeris fit of the transit times (one fit).
- A PASS of the pixel tests (`centroid_shift`, `aperture_depth`) does not exclude unresolved blends closer than the minimum offset of `centroid_shift` (see its thresholds).

### Cadences used per sector

| Sector | Used | In span | Fraction |
|---|---|---|---|
| 1 | 18720 | 19439 | 0.963 |
| 2 | 18720 | 19439 | 0.963 |
| 3 | 18720 | 19439 | 0.963 |

The `eb_catalog` test is not part of this gauntlet: the claim attaches no eclipsing-binary catalog.

## Blind holdout by year

Each year is hidden in turn, and the ephemeris is fitted on the other years only. In each round that reaches the measurement, the whole hidden year is detrended once before any logged read, with each predicted window masked out to the inner edge of its baseline band; that step is not logged, and its outlier clipping can drop hidden cadences. After it, the test reads only the predicted transit windows, the phase-0.5 control windows and their baseline bands, and every such read is logged.

| Hidden year | Status | Windows with data | Hidden SNR | Control SNR (phase 0.5) |
|---|---|---|---|---|
| 2018 | PASS | 7 | 47.7 | 1.4 |
| 2019 | PASS | 7 | 58.7 | 0.2 |
| 2020 | PASS | 7 | 40.8 | 1.4 |

| Hidden year | Train ephemeris matches the candidate | Depth consistency (sigma) |
|---|---|---|
| 2018 | yes | 2.83 |
| 2019 | yes | 8.82 |
| 2020 | yes | 4.52 |

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
