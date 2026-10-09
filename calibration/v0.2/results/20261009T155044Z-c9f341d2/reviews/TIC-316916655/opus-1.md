## Summary
The dossier for TIC 316916655 (TOI-441.01, a TFOPWG false positive with comment "retired as NEB") is intact, and its `REFUTED` verdict rests on two independent fatal failures from analysing the signal: odd_even at 5.84 sigma and centroid_shift at 7.4 sigma. A third fatal failure, eb_catalog, is a catalogue lookup. I found no objection that would change the verdict. The remaining objections are about how far the evidence goes: which star produces the signal, and how significant the centroid result really is.

## Objections

| Severity | Evidence | Why it matters |
|---|---|---|
| minor | `target.json` `fp_reason`: "SG1 check if the target is 316916663; possible odd-even; retired as NEB". `data/manifest.json` neighbors: TIC 316916663 is at 46.7 arcsec with Tmag 13.55. `nearby_contamination` only looks within `max_separation_arcsec: 21.0`, so it lists 671417918 and 316916657 but never considers 316916663. A Tmag difference of 4.35 gives a flux ratio of about 0.018, so 316916663 would need an eclipse about 10% deep, which is viable under the `max_eclipse_depth: 1.0` rule. | The neighbor that TFOP actually named as the suspect is outside what the gauntlet tests. The warning-level result points to a different star (316916657). This does not change the verdict, but nothing here identifies which star produces the signal. |
| minor | `battery.py::source_offset` (commit e176ac3) uses s = c_out − dc(1−d)/d with the flux-weighted centroid inside the SPOC aperture. This assumes all of the eclipsing source's light falls inside the aperture. A source about 2.2 px away (316916663), only partly inside, would be placed too close to the target. | The reported "0.89 px" is a lower bound on the separation, not a position. It cannot tell 316916657 (15.7 arcsec, about 0.75 px) apart from 316916663 (about 2.2 px). The message "the signal comes from another star" is supported, but no particular star is. |
| minor | `centroid_shift.metrics.sectors`: the sigmas are statistical only (sigma_x = 0.060 and 0.136 px), with no systematic floor. Offsets are in pixel-array coordinates. The manifest records only neighbor separations, with no RA/Dec and no position angles. The two sectors give nearly the same offset in the pixel frame: (0.197, −0.916) and (0.198, −0.765). | From the dossier alone I cannot check whether the offset direction points at a catalogued neighbor, or whether a pixel-frame systematic produced the agreement. A floor of about 0.1–0.2 px would lower the 7.4 sigma, but at a 0.89 px offset the test would very likely still fail. The verdict also stands on odd_even alone. |
| minor | The `eb_catalog` match is `matched_by: tic_id` against TESS-EB (Prsa et al. 2022), period 2.8747759 d. That differs from the found 2.8743675 d by 1.4e-4 in relative terms, roughly 0.37 d of drift over the ~890 cycles of the baseline. It passes only because of the 1% tolerance. | TESS-EB was built from TESS photometry of this same signal, so it is not independent evidence, and the tolerance is loose. The claim already excludes eb_catalog from "flagged" (`pass_criteria.flag_excluded_tests: [eb_catalog]`). Without it, odd_even and centroid_shift still give REFUTED, so this has no effect on the calibration count. |
| minor | `global_ephemeris.chi2_reduced` = 24.9 (20 transits). Individual transit times scatter about 5x more than their errors. Errors are inflated by sqrt(chi2_red) (`ephemeris.py` line 133), so the export's period_err is handled correctly. No odd-versus-even timing check is reported. | It shows red noise in timing, or an odd/even timing offset (for example an eccentric EB at 2P = 5.7487 d). Either reading is consistent with the verdict. It is listed for completeness. |
| minor | The found depth is 1800 ppm; the published (QLP) depth is 2490 ppm, 28% deeper. This is not discussed in the report. | It is probably a difference between pipelines (QLP vs SPOC PDCSAP, CROWDSAP 0.971). If the deeper depth were used, plausibility would still pass (about 0.72 R_Jup), and no other test result would change. |

## Checks with no objection
- **Integrity.**
  - `uv run --frozen refute check-dossier <dossier>` returns "OK: manifest intact".
  - `integrity.json` has status PASS. The locked and current claim SHA (c9f341d2…) match, the code SHA (2cd8b5c1…) matches, and all 6 attachments match the lock.
  - At lock commit e176ac3, `calibration/v0.2/` files hash the same as the dossier copies: self_claim.yaml 80a48356…, targets.yaml 5db2b047…, PROTOCOL.md f7c24655…, selection_log.md 9d49cc2c…, eb_catalog.csv 4ce34194…, eb_catalog_scan.json 70abfa45…, retrieval.json bd3bc670….
  - `git diff e176ac3 cc9d104` touches only LOCK_HISTORY.md, RUNS.md and self_claim.lock.json, so no code changed between the lock and the run. The lock is clean (`git_dirty: false`).
- **Target and data.**
  - Star coordinates RA 74.47283, Dec −13.70370 match the ExoFOP RA/Dec 04:57:53.47 / −13:42:13.35.
  - Tmag 9.199 matches.
  - Both SPOC 120-s LC and TPF files are for TIC 316916655 in sectors 5 (2018) and 98 (2025), with SHA-256 hashes and MAST URIs recorded. This matches the MAST availability check made at selection time (`target.json.mast`).
  - Stellar parameters (R = 1.466 ± 0.059, M = 1.472) are close to the ExoFOP values (1.44, 1.472). Sources and retrieval times are recorded.
  - The period matches the published value to 2.6e-6 in relative terms, so the correct signal was analysed.
- **odd_even (FAIL).**
  - Odd depth is 2055 ± 64 ppm (n = 10) and even depth is 1576 ± 52 ppm (n = 9). Errors use max(white noise, scatter/√n) (`events.py::group_mean`).
  - `plots/odd_even.png` shows the difference clearly by eye, and both groups are centred on the prediction.
  - It is not a sector artefact. Parity alternates within each sector, and the per-sector aperture depths (1772 and 1899 ppm) differ far less than 23%.
  - Parity across the 7-year gap is safe: the period error is 1.7e-6 d, about 0.002 d over ~890 cycles.
- **secondary_eclipse (PASS).** 23 phase-0.5 windows give 12 ± 36 ppm, and `plots/secondary.png` is flat. If the true period is 2P, phase 0.5 at P is not the secondary phase. This does not affect the verdict.
- **plausibility (PASS).** k = 0.042, 0.61 R_Jup, duration ratio 0.51. The inputs are consistent.
- **aperture_depth (PASS).** Depth ratio is 0.97 (core 1755 ± 308, large 1706 ± 118). This is consistent with a contaminant within about 1 px that sits inside both apertures. It is not a reason to doubt the centroid failure.
- **period_alias and systematics (PASS).**
  - The box model gains ΔBIC 4830 over a sinusoid, and the period is not near any of the listed systematic periods.
  - 1 of 20 transits falls near a momentum dump.
  - SAP and PDCSAP depths agree (0.43 sigma).
  - Background does not rise in transit (−1.58 sigma).
- **Blind holdout.**
  - Both rounds are INCONCLUSIVE before any hidden data were read: `windows: []` and `access_log: []` in both rounds. The train-only timing uncertainty (6.27 h and 6.44 h) is larger than one transit duration (1.43 h and 1.35 h), which is the pre-registered `max_timing_sigma_durations: 1.0` gate.
  - Each round's train candidate uses only the other year: t0 3989.76 for hidden 2018, and 1440.20 for hidden 2025.
  - No round was decided with wide windows.
  - Coverage is 0, so the result is INCONCLUSIVE, not PASS, as the rules require.
- **Verdict logic.** Fatal FAILs give REFUTED. With eb_catalog excluded under the claim's "flagged" definition, odd_even and centroid_shift still give REFUTED.
- **Text.**
  - `report.md` and `export/candidate_parameters.md` say "nothing here is a confirmed discovery" and "NOTHING HAS BEEN SUBMITTED". The export marks the target "already catalogued; it is not a new candidate".
  - The scope paragraph limits claims to the easy regime.
  - No text overstates beyond the centroid wording noted above.

## Assessment: OBJECTIONS
All objections are minor and none undermines `REFUTED`. They concern which neighbor is the source and how significant the centroid result is, since the gauntlet does not test 316916663 (the star TFOP named), and it does not include a systematic error floor or record neighbor positions.
