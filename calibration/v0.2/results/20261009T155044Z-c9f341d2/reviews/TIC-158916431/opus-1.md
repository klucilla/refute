## Summary
The dossier for TIC 158916431 (TOI-2146.01, a known false positive with TFOPWG disposition FP) is intact. Its REFUTED verdict follows from two independent pixel-level failures, centroid_shift and aperture_depth, that agree with each other and with the catalogue depth. I found no objection that weakens the verdict. The objections below are about borderline PASSes, a holdout control above the pass threshold, and report wording and precision.

## Objections

| Severity | Evidence | Why it matters |
|---|---|---|
| important | `secondary_eclipse` PASS passed narrowly: 290.9 ± 103.7 ppm, 2.81 sigma against a 3.0 limit, depth ratio 0.091 against a 0.1 limit (`verdict.json` tests[2]). Separately, the hidden-year control at phase 0.5 measured `control_phase05_depth_ppm` 392 at `control_phase05_snr` 5.54, which is above the holdout's own `min_snr` 5.0 (`holdout_rounds[0].metrics`). In `plots/secondary.png` a shallow dip of about 400 ppm sits at roughly 0 to +2 h, partly outside the 2.2 h box centred on phase 0.5. | Two independent measurements point to a dip at phase 0.5, which is a typical eclipsing-binary signature. The fixed box at phase 0.5 may have under-measured it, so this PASS may be a near-miss rather than a clean null. It does not change this verdict, which is already REFUTED. |
| important | Holdout control SNR (5.54) is at or above the holdout pass threshold `min_snr` 5.0 (`thresholds` of holdout_by_year). The code reports the control but never judges it (`holdout.py`: "reported, not judged"). | The control is meant to show the false-alarm level of the period-correction scan, and here that level exceeds the pass bar. The 2021 round is still robust, because its SNR of 42.5 is far above both. As a general matter, a PASS near SNR 5 would not be distinguishable from the control. |
| minor | Per-sector centroid source offsets disagree: S40 is about 1.10 px (−0.84, −0.70), S52 about 0.60 px (−0.11, −0.59 ± 0.10), S53 about 1.00 px (−0.45, −0.89 ± 0.05). The reported `mean_offset_pixels` is 0.97. | The source-position formula in `battery.py` `source_offset` gives the in-aperture centroid of the varying light. For a contaminant partly outside the SPOC aperture this is biased toward the aperture and changes with each sector's aperture. "0.97 px from the target" is therefore not a source location, and is likely an underestimate. Each sector on its own still shows an offset of at least 5.8 sigma, so the FAIL holds. |
| minor | The report says "the signal comes from another star", but no star is identified. `nearby_contamination` looks only within 21 arcsec, where it finds TIC 1507863670 (Tmag 18.54, would need an eclipse depth of 9.1, so not viable). In `data/manifest.json` the only TIC neighbour at roughly 1 to 1.5 px that could produce the signal is TIC 158916451 (27.2 arcsec, Tmag 14.34). It would need an eclipse of about 19%, from 3214 ppm × 10^(0.4 × 4.43). TIC 158916415 (59 arcsec, Tmag 13.16, about 6.4%) is also possible. | "Off-target or outside the core aperture" is what the evidence supports. Naming a particular star would need a direction check, which the dossier does not provide (no position angles or TPF overlay). The wording slightly overstates what is known. |
| minor | `target.json` `fp_reason` is "artifact TIC 158916429 close by", which is the ExoFOP *Comments* field. TIC 158916429 (5.3 arcsec, Tmag 16.3) has TIC disposition ARTIFACT (`data/manifest.json` neighbours), meaning it is a spurious catalogue entry. | The FP basis recorded here is mislabelled; the dispositions are TESS "EB" and TFOPWG "FP". Ignoring the ARTIFACT entry in nearby_contamination is correct. |
| minor | The report's Signal table prints the epochs as `2.45939e+06` and `2.45977e+06`. The export sheet takes its period from the search (5.8924981) but its epoch and period_err from the global linear ephemeris (period 5.8924727). | The epoch cannot be compared at that precision. I checked it by hand: the found t0 2459393.81334 plus 63 × P gives 2459765.0407, against the published 2459765.0399, a difference of about 1.3 min, so it is the right signal. The export mixes values from two fits. |
| minor | The box duration is 2.2 h against a published 3.134 h. `plots/phase.png` shows a dip about 3.2 h wide with a rounded or V-like bottom about 3800 ppm deep, against a 3214 ppm box. | The box underestimates both duration and depth. Plausibility (duration ratio 0.35) is still passed. There is no shape test, so a V-shape cannot be examined. |

## Checks with no objection
- **Integrity:**
  - `uv run --frozen refute check-dossier <dossier>` returns `OK: manifest intact`.
  - In `integrity.json`, the locked and current claim SHA-256 (`c9f341d2…`) and code SHA-256 (`2cd8b5c1…`) match, status PASS, and all six attachments match the lock.
  - `claim.lock.json` has `git_dirty: false` at commit e176ac3; the run commit is cc9d104.
  - I did not run `check-dossier --against`, because that needs a network re-run.
- **Target and data:**
  - TIC 158916431 matches the ExoFOP TOI 2146.01 row (retrieved 2026-10-09).
  - The product is SPOC 2-min PDCSAP for sectors 40, 52 and 53 (2021 and 2022), with TPFs for the same sectors and file hashes in `data/manifest.json`.
  - ExoFOP sector 26 has no SPOC 2-min product (QLP FFI only), so it is not missing data (`target.json` mast block).
  - Stellar parameters come from the TIC: R 2.127 ± 0.081, M 1.64, Tmag 9.91, matching ExoFOP. The star is not saturated and CROWDSAP is 0.97.
  - The found period 5.8924981 is within 2.1e-6 relative of the published 5.8924856.
- **Centroid and aperture FAILs are supported:**
  - Every sector shows a significant offset (total chi2 674 on 6 dof).
  - Depth rises from the core to the larger aperture: 2595 ± 68 to 3513 ± 90 ppm, 8.2 sigma.
  - Per-sector depths in the SPOC aperture vary: 2405 ppm in S52 against 3557 ppm in S53.
  - The QLP FFI depth (4530 ppm) is larger than SPOC's (3214).
  - All four observations agree with a contaminant outside the core. None of them looks like a target-hosted transit or a background artifact; `systematics` shows no background rise and SAP matches PDCSAP within 0.04 sigma.
- **Other tests:**
  - snr: 81.6.
  - odd_even: 1.11 sigma. The odd error is inflated by scatter, but even with the even-group error the difference would be about 2.4 sigma.
  - period_alias: BIC gain 5409.
  - eb_catalog: no match in 2.19 M rows. It is excluded from the "flagged" rule anyway (`claim.yaml` `flag_excluded_tests`).
  - The verdict does not depend on eb_catalog.
- **Blind holdout:**
  - All access-log reads in 2021 match the registered windows: t_pred ± half_width, baseline bands of ±0.125 d (= 1.5 × the 2.0 h train duration), and control windows at phase 0.5.
  - There are 5 of 5 predicted windows with data. The timing sigma of 0.036 d (0.86 h) is below one duration (2.0 h).
  - The windows (half-width 0.15 d) are wider than the transit only by the pre-registered 3 sigma timing allowance. The box is the train duration, placed by a single period correction.
  - The 2022 round was correctly declared INCONCLUSIVE (timing sigma 2.19 h > 2.0 h) with an empty access log.
- **Text:**
  - The report and export say that nothing is confirmed and nothing was submitted, and that this is an already-catalogued calibration target.
  - Nothing is described as a discovery.

## Assessment: OBJECTIONS
