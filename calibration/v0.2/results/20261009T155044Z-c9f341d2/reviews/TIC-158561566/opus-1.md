## Summary
The dossier is intact and the verdict follows the locked rules, but `REFUTED` rests on one thing only: a TIC-ID lookup in the TESS-EB catalog (`eb_catalog`). Every fatal test that looks at the data for an eclipsing-binary signature passed, and the catalog period is this target's own transit period. On the dossier's evidence, the fatal failure comes from an external catalog listing. Nothing in this target's light curve or pixels shows an eclipsing binary.

## Objections

| # | Severity | Evidence | Why it matters |
|---|---|---|---|
| 1 | critical | `verdict.json` `verdict_reason`: "fatal failure in: eb_catalog". `eb_catalog.metrics.matches`: `matched_by: tic_id`, TESS-EB row "TIC 158561566 (1)", P = 6.7899645 d. The local snapshot `.cache/eb_snapshot_v02/tess_ebs_prsa2022.tsv` line 1174 has the same row. All data-based eclipsing-binary discriminators pass: `odd_even` 0.78 sigma; `secondary_eclipse` 0.90 sigma, depth ratio 0.017; `aperture_depth` ratio 0.87 (depth does not grow with the aperture); `holdout_by_year` 5/5. `targets.yaml` records the target as kind `planet` (NASA Exoplanet Archive pscomppars, `tran_flag` 1, Buchhave et al. 2011). The catalog period equals the found period to a relative 2.4e-5 (factor 1). | The catalog row almost certainly describes the same transit signal, not a separate eclipsing-binary detection. The test failed because of an external classification, not because the data showed anything. The verdict is mechanically correct under `definitions.refuted_planet` (PROTOCOL.md lines 445-446), but REFUTED here does not reflect any eclipsing-binary evidence in the data. It also uses up the claim's budget of at most 1 refuted planet. |
| 2 | important | The match was known before the lock. `attachments/targets.yaml` and `eb_catalog_scan.json` record `TIC-158561566: tess_eb: 1` from selection (selection_log generated 2026-10-09T15:18:54Z). The claim was locked at 15:29:55Z (`claim.lock.json` `locked_at_utc`). | Under the locked rule, this planet's REFUTED was effectively decided by a lookup before any analysis, as long as the period matched. For this target the calibration measures catalog contamination, not Refute's analysis. Anyone interpreting the calibration result needs to know this. |
| 3 | minor | `centroid_shift` PASS says "consistent with the target", yet `offset_sigma` is 4.79 (`offset_chi2` 76.1 on 26 dof). It passes only because `mean_offset_pixels` 0.154 < `min_offset_pixels` 0.5. That mean is a weighted average of per-sector offset magnitudes (`battery.py` lines 283-284), so noise pushes it upward. Per-sector offsets change sign (S14 x = -0.22, S80 x = +0.33, S81 y = -0.25), and S82 has sigma 0.68/0.85 px. | The message overstates: the data are statistically inconsistent with zero offset and fall below the materiality floor. The most likely cause is underestimated per-sector errors or systematics, but the text should not say "consistent". |
| 4 | minor | In every holdout round, `depth_consistency_sigma` is 7.5-10.0, and the train depths of 1045-1081 ppm are about half of the hidden depths (1877-2289 ppm) and the global depth (2076 ppm). Cause in the code: the train candidate comes from a search on an unmasked detrend (`holdout.py` lines 332-333) with a 1.0 d window against a 5.4 h transit. That `train.depth` is then the depth of the transit-timing template (line 351). The train ephemeris `chi2_reduced` is 44-72; it is rescaled (`ephemeris.py` line 133). | This does not affect the verdict, since rounds are judged on SNR (16.8-22.0 against 5.0). But the reported diagnostic is misleading and the timing template depth is off by about 2x. |
| 5 | minor | Unresolved dilution is not tested. From `targets.yaml`, pl_rade 12.733 Re and st_rad 2.048 Rsun give Rp/R* = 0.057, an undiluted depth of about 3250 ppm. The archive Kepler depth is 2252 ppm and the TESS PDCSAP depth is 2076 ppm. `plausibility` derives 0.887 RJ. `nearby_contamination` sees only TIC 1717102144 (Tmag 18.9, 5.5"). | The numbers imply roughly 30% extra light in the aperture that the TIC does not account for, which fits a companion closer than one pixel. No gauntlet test checks which star hosts the transit. This does not support REFUTED, but it is an alternative the gauntlet leaves untested. The cited reference (Buchhave et al. 2011) is the place to check whether a close companion is known; the dossier does not record one. |
| 6 | minor | `plausibility` is INCONCLUSIVE because the TIC mass is null, yet `targets.yaml` carries `st_mass` 1.512 from the archive. | The duration check never ran. It is warning severity, so the verdict is unchanged. |
| 7 | minor | `period_alias` FAIL (warning): 6.790 d is within 1% of 6.85 d, so the tolerance covers 6.78-6.92 d. `box_delta_bic` = 3443.7 strongly favors a transit over a sinusoid. | False alarm from a coarse tolerance. No effect on the verdict. |
| 8 | minor | The report's Signal table shows the epochs as 2.45869e+06 and 2.45497e+06 (6 significant digits, different reference epochs), with no propagated comparison. My own calculation: 547 cycles, residual 1.07 min, against a 3.4 min propagated period uncertainty. | Readers may take the two epochs as a mismatch when they in fact agree closely. |

## Checks with no objection
- **Integrity:**
  - `uv run --frozen refute check-dossier <dossier>` printed "OK: manifest intact" and exited 0.
  - `integrity.json` status is PASS: claim `c9f341d2...` and code `2cd8b5c1...` equal the locked values, and all 6 attachment hashes match.
  - The SHA-256 of every dossier attachment and of `claim.yaml` equals `git show e176ac3:calibration/v0.2/<file>`. `claim.lock.json` is byte-identical to the one at commit cc9d104.
  - `src/` is identical between cc9d104 and HEAD.
  - Timing: lock at 15:29:55Z, stellar parameters retrieved at 15:35:32Z, run at 15:50:44Z.
- **Data:**
  - Right target: all 13 LC files are `...-0000000158561566-...`.
  - The sectors [14, 15, 26, 40, 41, 53, 54, 55, 74, 75, 80, 81, 82] match the selection-time MAST record (5 years, 1850 d span). 214581 cadences were used.
  - Tmag 11.636 equals the archive `sy_tmag`. TIC R = 2.001 ± 0.103 Rsun against the archive's 2.048.
  - Found period relative error is 2.7e-7, and the epoch agrees to 1.07 min (see objection 8).
  - Median CROWDSAP is 0.95. No sector is missing or skipped (`skipped_sectors: {}`).
- **Tests:**
  - SNR 64.3 over 44 transits.
  - odd/even depths 2103 and 2011 ppm (0.78 sigma). The 26/16 split between odd and even is lopsided but has enough of each.
  - The secondary eclipse search covered 47 windows: 35 ± 38 ppm.
  - Aperture depths: core 1978 ppm, large 1715 ppm, which fits a source on the target.
  - Systematics: SAP and PDCSAP agree at 0.008 sigma (SAP depth equals the expected crowding-corrected value), the background is flat, and only 1 of 44 transits is near a momentum dump.
  - The phase, odd/even and secondary plots show a clean flat-bottomed dip of about 2000 ppm and nothing at phase 0.5.
- **Blind holdout:**
  - I matched every `access_log` entry in all 5 rounds programmatically: each window and baseline read corresponds to a registered predicted window or control window (0 unmatched).
  - Windows are 1.04-1.14x the train duration (0.225 d), which is shorter than the published 6.22 h transit, so no round was decided with windows wider than the transit. Maximum timing sigma per round is 0.03-0.13 h.
  - Control SNRs at phase 0.5 are -0.9 to 1.9.
  - No leakage: the train candidates' SDE traces only to training sectors (9.85 is S82 when 2024 is training; 6.06 is S55 when 2024 is hidden).
- **Text:** the report carries the "nothing here is a confirmed discovery" disclaimer and the scope statement. It does not call the signal a discovery or confirmed, and the verdict reason names the failing test plainly.

## Assessment: SERIOUS OBJECTIONS
The dossier's integrity and mechanics are sound, and the verdict was applied as the locked rules require. The serious objection concerns what REFUTED means here: it rests only on a catalog listing at the target's own transit period, and every data-based test in the dossier contradicts the eclipsing-binary interpretation (objections 1 and 2).
