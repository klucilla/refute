## Summary
The dossier for TIC 374200604 (TOI-4838.01, calibration role `false_positive`) is intact. Its `INCONCLUSIVE` verdict follows mechanically from `holdout_by_year`, where both rounds stopped before any hidden-year read. The evidence does not support every PASS equally: the dossier contains a strong grazing / stellar-density mismatch signature, and the target's recorded reason for being a false positive is an unresolved hierarchical eclipsing binary. No test in the gauntlet can address either one, so the PASS rows say nothing about the main alternative.

## Objections

| # | Severity | Evidence | Why it matters |
|---|---|---|---|
| 1 | important | `verdict.json` → `tests[plausibility].metrics`: `duration_ratio` 0.252, `max_duration_hours` 2.98, `radius_ratio` 0.0387; star R = 1.66 Rsun, M = 1.01 Msun. From these, a/R* ≈ 2.12. A 0.75 h duration then needs an impact parameter b ≈ 1.00–1.01, a grazing geometry. At that b, a body with k = 0.039 covers less than half its disk and cannot make the 1498 ppm depth (k² = 1498 ppm assumes a full transit). `plots/phase.png` shows a V-shaped binned profile, not a box. The message still says "duration ratio 0.25 [is] plausible". | `check_plausibility` only rejects durations that are too long (`max_duration_ratio` 1.5). A very short duration gives one of two readings, and the data cannot tell them apart: (a) a grazing geometry that needs a larger, possibly stellar, eclipser, or (b) an eclipsed body around a denser star than the target. Both point toward an eclipsing binary, and `target.json` → `fp_reason` records exactly that: "v-shaped; possible triple-star system; ... hierarchical eclipsing binary". The PASS is mechanically correct, but the word "plausible" overstates it. There is also no shape (V vs U) test. |
| 2 | important | `fp_reason` (above). `data/manifest.json` → `neighbors`: 0 TIC sources within 21″, nearest at 42.7″. `centroid_shift` offset 0.27 px. `eb_catalog`: no catalog entry (`eb_catalog_scan.json` → `TIC-374200604`: gaia 0, tess_eb 0). | The recorded alternative is a stellar companion closer than one pixel, physically bound or not. The tests that passed cannot probe it: centroid, aperture depth, TIC neighbors and EB catalogs. These PASS rows are uninformative about the documented false-positive mechanism, and the report does not say that this alternative is untested. For the calibration, this target will count as not flagged because of a limit in the gauntlet's coverage, not because of a data problem. |
| 3 | minor | `tests[centroid_shift].metrics`: `offset_sigma` 3.505 (> `max_sigma` 3.0), `mean_offset_pixels` 0.271 (< `min_offset_pixels` 0.5). The per-sector y-offsets are −0.253, −0.240 and −0.192 px, each about 2–2.8σ and with the same sign in all three sectors. The x-offsets are +0.24, +0.01 and +0.08 px. | The offset is statistically significant but passes on the size floor. 0.27 px is about 5.7″ and no catalogued source lies there, so this is most likely a systematic effect (for example, PRF truncation in the SPOC aperture, or pull from the 42.7″ neighbor). The error model has no systematic floor. The message "consistent with the target" hides the fact that the sigma criterion was exceeded. |
| 4 | minor | `nearby_contamination` checks only within 21″ (`max_separation_arcsec`). Neighbor TIC 374200603 is Tmag 12.67 at 42.7″, about 0.48 of the target's flux. Median CROWDSAP is 0.93. | With about 7% contaminating light, an eclipse of roughly 2% on that neighbor could reproduce the signal. The message "none could produce the signal" covers only the 21″ radius. In this dossier, `aperture_depth` and `centroid_shift` independently argue against the neighbor (see the checks below), so the outcome is not affected. |
| 5 | minor | `export/candidate_parameters.md` takes `period_days` 0.7600161 from the BLS candidate, but `period_err_days` 1.93e-6 and `epoch_bjd_tdb` 2459775.84083 from `global_ephemeris`, whose period is 0.7600173. | The sheet mixes two solutions. The difference is 1.2e-6 d (0.6σ), which is small but inconsistent. |
| 6 | minor | Found depth 1498 ± 72 ppm against published 1866 ± 138 ppm, a 2.4σ difference. Box duration is 0.75 h, while the binned dip in `plots/phase.png` runs from about −0.5 to +0.6 h. | The box model under-fits a V-shaped dip, which biases depth and duration low. It does not change any test result, but the 0.25 duration ratio in objection 1 is partly a product of this fit. Even with a duration of about 1.1 h, b stays at about 0.97, which is still grazing. |

## Checks with no objection

- **Integrity.**
  - `uv run --frozen refute check-dossier <dossier>` returned "OK: manifest intact".
  - `integrity.json`: status PASS. Claim `c9f341d2…` and code `2cd8b5c1…` hashes equal the locked values, all 6 attachment hashes match, and `tampered_components` is empty.
  - `claim.lock.json`: `git_dirty` false, lock commit `e176ac3`.
  - The `MANIFEST.sha256` entries for `environment/uv.lock` and the locked `uv.lock` are the same hash (`2309a1f5…`).
- **Target and data.**
  - TIC 374200604 is the same in `target.json` (ExoFOP row, retrieved 2026-10-09T15:01:37Z) and in the data file names.
  - TIC v8 stellar values (R = 1.660 ± 0.100, M = 1.01, logg 4.0, Tmag 11.869) match the ExoFOP row.
  - Product is SPOC 120-s PDCSAP for sectors 45, 46 and 72, with LC and TPF hashes in `data/manifest.json`.
  - ExoFOP also lists sector 35, but the MAST check at selection (`target.json` → `mast`) found SPOC 2-min data only for 45, 46 and 72. Leaving it out is consistent with the protocol.
- **Signal.**
  - Period 0.7600161 against published 0.7600190 ± 9.6e-6: relative error 3.8e-6, so P is recovered and is not an alias.
  - Found epoch 2459527.31734 is published epoch + 2P, off by about 2.7 min. The global ephemeris at t_ref 2459775.84 lands within about 1.3 min of the published ephemeris after 329 cycles.
- **odd_even.** 1554 ± 118 vs 1423 ± 127 ppm, 0.76σ, with 43 odd and 41 even transits. `plots/odd_even.png` agrees.
- **secondary_eclipse.** 18.6 ± 86.6 ppm at phase 0.5 (0.21σ, 84 windows). `plots/secondary.png` is flat.
- **aperture_depth.** Large/core ratio is 0.66 (−3.75σ), and the transit is detected at 17.4σ in the core. A falling depth is what a source on the target looks like when the dilated aperture takes in the 42.7″ Tmag 12.67 neighbor; the expected dilution is about 1/(1+0.48) ≈ 0.68. This argues against the neighbor as the source.
- **systematics.**
  - SAP depth 1390 ppm against an expected 1380 ppm after the crowding correction (0.08σ).
  - Background rise 0.34σ.
  - 1 of 85 transits falls near a momentum dump.
- **period_alias.** Box ΔBIC is 307 over sine-only. P = 0.76 d is not near any listed systematic period.
- **Blind holdout.**
  - Both rounds returned INCONCLUSIVE because of the train-only timing uncertainty check: 3.95 h against 0.70 h when 2021 was hidden, and 0.89 h against 0.60 h when 2023 was hidden.
  - At the lock commit, `holdout.py` makes this check (line 379) before `HiddenYear` is built (line 396).
  - `access_log` and `windows` are empty in both rounds, so no hidden-year data were read and no round was decided with windows wider than the transit.
  - The INCONCLUSIVE result is structural: the per-transit SNR is about 20.7/√85 ≈ 2.2, the train ephemeris reduced chi² is about 50, and the covariance is inflated by chi²_red (`ephemeris.py` line 133).
- **Verdict logic.** All fatal tests are PASS except `holdout_by_year`, which is INCONCLUSIVE with coverage 0. The verdict is therefore INCONCLUSIVE, as `verdict_reason` states.
- **Text.**
  - `report.md` and the export sheet say that nothing is a confirmed discovery and nothing was submitted.
  - The export sheet says "Calibration target: already catalogued; it is not a new candidate."
  - The scope disclaimer is present.
  - The only wording issue is "plausible" in objection 1.

## Assessment
OBJECTIONS
