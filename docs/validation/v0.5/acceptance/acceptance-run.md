# v0.5 acceptance rate cases (accept seeds)

Synthetic data with known truth (docs/plans/v0.5-acceptance.md, revision 2). A case is decided only when every scheduled trial ran without error and met its construction; INVALID otherwise. A FAIL is a recorded result: the test is diagnostic only in v0.5; nothing is retuned. `method_status: not_validated`.

Commit 75c02e2 (dirty: False); processor time 14.67 h over 22 workers. Record: `acceptance-run.json`; every trial: `acceptance-run-detail.json` (SHA-256 9e77ccd09b9819e391c1924b4f2752ea198b08a650677b9a4df2f4d7c9cf3557).

Recorded interpretations and limits:

- WP2 depths are set in the errors the engine measures on each trial's own noise (the same seed, no signal): the cases test the engine at a fixed engine-estimated SNR, conditional on the realization, not at a fixed physical depth. The design SNR from the injected depths and the complete error vector is recorded per trial.
- WP2 construction checks are by design: the test is re-run on the injected, noise-free depths with the trial's measured errors (both WP2 sensitivity blocks are computed from observed depths). The realized block decides the status; a case below the rule by design does not guarantee that its realized block stays below it (single_event's alternative is defined at the observed total SNR). Both blocks are recorded.
- Row 2.1 for event_consistency: total SNR 12 and 'detectable by a margin' cannot both hold (per-event SNR 4.9, 2.7, 1.9 at N = 6, 20, 40); the construction checks the event count only, a FAIL is a false failure whatever the sensitivity, and the detectable null is case 1.8-event_consistency-c (total SNR 30, N = 6).
- Row 3.3: the variability has period 0.83 d (a 3-day sinusoid does not survive the 1-day detrending); the engine's box estimator on the noise-free signal gives the apparent depth (semi-amplitude / depth = 2.006); the design significance (true semi-amplitude over the fit's error at P) is recorded and must exceed 15.
- Row 1.10: 400 windows per noise model are 400 independent curves, one window decided per curve, and 400 groups (one per curve, all its windows); the pulls of every window are reported apart, not decided.
- Row 4.6: a fixture with the row's errors (0.3 px) through the production combination and heterogeneity rule; the pixel experiment is reported beside it with each sector's measured offset error.
- Row 1.11: the period_alias sensitivity simulation draws white noise internally, also in the correlated-noise trials; those trials do not validate a correlated internal simulation.
- The stellar-trend variant (a 6-day sinusoid) is not run for the sinusoid cases: it is itself the variability those cases construct or exclude.

| Case / noise | N | PASS | FAIL | INCONCLUSIVE | Errors | Constructed | Rule | Result |
|---|---|---|---|---|---|---|---|---|
| 1.8-odd_even-a/white | 200 | 0 | 200 | 0 | 0 | 200 | FAIL >= 184 (lower 2.5 % of Bin(200, 0.95)) | **PASS** |
| 1.8-odd_even-a/red | 200 | 0 | 200 | 0 | 0 | 200 | FAIL >= 184 (lower 2.5 % of Bin(200, 0.95)) | **PASS** |
| 1.8-odd_even-a/trend | 200 | 0 | 200 | 0 | 0 | 200 | FAIL >= 184 (lower 2.5 % of Bin(200, 0.95)) | **PASS** |
| 1.8-odd_even-b/white | 200 | 0 | 43 | 157 | 0 | 200 | no PASS | **PASS** |
| 1.8-odd_even-b/red | 200 | 0 | 2 | 198 | 0 | 200 | no PASS | **PASS** |
| 1.8-odd_even-b/trend | 200 | 0 | 30 | 170 | 0 | 200 | no PASS | **PASS** |
| 1.8-odd_even-c/white | 200 | 200 | 0 | 0 | 0 | 200 | FAIL <= 2 (upper 97.5 % of Bin(200, 0.0027)) | **PASS** |
| 1.8-odd_even-c/red | 200 | 198 | 2 | 0 | 0 | 200 | FAIL <= 2 (upper 97.5 % of Bin(200, 0.0027)) | **PASS** |
| 1.8-odd_even-c/trend | 200 | 199 | 1 | 0 | 0 | 200 | FAIL <= 2 (upper 97.5 % of Bin(200, 0.0027)) | **PASS** |
| 1.8-secondary-dip-a/white | 200 | 0 | 200 | 0 | 0 | 200 | FAIL >= 184 (lower 2.5 % of Bin(200, 0.95)) | **PASS** |
| 1.8-secondary-dip-a/red | 200 | 0 | 200 | 0 | 0 | 200 | FAIL >= 184 (lower 2.5 % of Bin(200, 0.95)) | **PASS** |
| 1.8-secondary-dip-a/trend | 200 | 0 | 200 | 0 | 0 | 200 | FAIL >= 184 (lower 2.5 % of Bin(200, 0.95)) | **PASS** |
| 1.8-secondary-dip-b/white | 200 | 0 | 10 | 190 | 0 | 200 | no PASS | **PASS** |
| 1.8-secondary-dip-b/red | 200 | 0 | 0 | 200 | 0 | 200 | no PASS | **PASS** |
| 1.8-secondary-dip-b/trend | 200 | 0 | 8 | 192 | 0 | 200 | no PASS | **PASS** |
| 1.8-secondary-c/white | 200 | 200 | 0 | 0 | 0 | 200 | FAIL <= 2 (upper 97.5 % of Bin(200, 0.0027)) | **PASS** |
| 1.8-secondary-c/red | 200 | 200 | 0 | 0 | 0 | 200 | FAIL <= 2 (upper 97.5 % of Bin(200, 0.0027)) | **PASS** |
| 1.8-secondary-c/trend | 200 | 199 | 1 | 0 | 0 | 200 | FAIL <= 2 (upper 97.5 % of Bin(200, 0.0027)) | **PASS** |
| 3.1-brightening-a/white | 200 | 0 | 200 | 0 | 0 | 200 | FAIL >= 184 (lower 2.5 % of Bin(200, 0.95)) | **PASS** |
| 3.1-brightening-a/red | 200 | 0 | 200 | 0 | 0 | 200 | FAIL >= 184 (lower 2.5 % of Bin(200, 0.95)) | **PASS** |
| 3.1-brightening-a/trend | 200 | 0 | 200 | 0 | 0 | 200 | FAIL >= 184 (lower 2.5 % of Bin(200, 0.95)) | **PASS** |
| 3.1-brightening-b/white | 200 | 0 | 0 | 200 | 0 | 200 | no PASS | **PASS** |
| 3.1-brightening-b/red | 200 | 0 | 2 | 198 | 0 | 200 | no PASS | **PASS** |
| 3.1-brightening-b/trend | 200 | 0 | 0 | 200 | 0 | 200 | no PASS | **PASS** |
| 3.2-dip-ratio-0.3/white | 200 | 0 | 200 | 0 | 0 | 200 | FAIL >= 184 (lower 2.5 % of Bin(200, 0.95)) | **PASS** |
| 3.2-dip-ratio-0.3/red | 200 | 0 | 200 | 0 | 0 | 200 | FAIL >= 184 (lower 2.5 % of Bin(200, 0.95)) | **PASS** |
| 3.2-dip-ratio-0.3/trend | 200 | 0 | 200 | 0 | 0 | 200 | FAIL >= 184 (lower 2.5 % of Bin(200, 0.95)) | **PASS** |
| 3.2-dip-ratio-1.0/white | 200 | 0 | 200 | 0 | 0 | 200 | FAIL >= 184 (lower 2.5 % of Bin(200, 0.95)) | **PASS** |
| 3.2-dip-ratio-1.0/red | 200 | 0 | 200 | 0 | 0 | 200 | FAIL >= 184 (lower 2.5 % of Bin(200, 0.95)) | **PASS** |
| 3.2-dip-ratio-1.0/trend | 200 | 0 | 200 | 0 | 0 | 200 | FAIL >= 184 (lower 2.5 % of Bin(200, 0.95)) | **PASS** |
| 1.8-sinusoid-a/white | 200 | 0 | 200 | 0 | 0 | 200 | FAIL >= 184 (lower 2.5 % of Bin(200, 0.95)) | **PASS** |
| 1.8-sinusoid-a/red | 200 | 0 | 200 | 0 | 0 | 200 | FAIL >= 184 (lower 2.5 % of Bin(200, 0.95)) | **PASS** |
| 1.8-sinusoid-b/white | 200 | 0 | 0 | 200 | 0 | 200 | no PASS | **PASS** |
| 1.8-sinusoid-b/red | 200 | 0 | 0 | 200 | 0 | 200 | no PASS | **PASS** |
| 3.8-sinusoid-c/white | 200 | 200 | 0 | 0 | 0 | 200 | FAIL <= 2 (upper 97.5 % of Bin(200, 0.0027)) | **PASS** |
| 3.8-sinusoid-c/red | 200 | 200 | 0 | 0 | 0 | 200 | FAIL <= 2 (upper 97.5 % of Bin(200, 0.0027)) | **PASS** |
| 2.1-single_event-equal-6/white | 200 | 200 | 0 | 0 | 0 | 200 | FAIL <= 2 (upper 97.5 % of Bin(200, 0.0027)) | **PASS** |
| 2.1-single_event-equal-6/red | 200 | 200 | 0 | 0 | 0 | 200 | FAIL <= 2 (upper 97.5 % of Bin(200, 0.0027)) | **PASS** |
| 2.1-single_event-equal-6/trend | 200 | 200 | 0 | 0 | 0 | 200 | FAIL <= 2 (upper 97.5 % of Bin(200, 0.0027)) | **PASS** |
| 2.1-single_event-equal-20/white | 200 | 200 | 0 | 0 | 0 | 200 | FAIL <= 2 (upper 97.5 % of Bin(200, 0.0027)) | **PASS** |
| 2.1-single_event-equal-20/red | 200 | 200 | 0 | 0 | 0 | 200 | FAIL <= 2 (upper 97.5 % of Bin(200, 0.0027)) | **PASS** |
| 2.1-single_event-equal-20/trend | 200 | 200 | 0 | 0 | 0 | 200 | FAIL <= 2 (upper 97.5 % of Bin(200, 0.0027)) | **PASS** |
| 2.1-single_event-equal-40/white | 200 | 200 | 0 | 0 | 0 | 200 | FAIL <= 2 (upper 97.5 % of Bin(200, 0.0027)) | **PASS** |
| 2.1-single_event-equal-40/red | 200 | 200 | 0 | 0 | 0 | 200 | FAIL <= 2 (upper 97.5 % of Bin(200, 0.0027)) | **PASS** |
| 2.1-single_event-equal-40/trend | 200 | 200 | 0 | 0 | 0 | 200 | FAIL <= 2 (upper 97.5 % of Bin(200, 0.0027)) | **PASS** |
| 2.2-single_event-one-6/white | 200 | 0 | 200 | 0 | 0 | 200 | FAIL >= 184 (lower 2.5 % of Bin(200, 0.95)) | **PASS** |
| 2.2-single_event-one-6/red | 200 | 0 | 200 | 0 | 0 | 200 | FAIL >= 184 (lower 2.5 % of Bin(200, 0.95)) | **PASS** |
| 2.2-single_event-one-6/trend | 200 | 0 | 200 | 0 | 0 | 200 | FAIL >= 184 (lower 2.5 % of Bin(200, 0.95)) | **PASS** |
| 2.2-single_event-one-20/white | 200 | 0 | 200 | 0 | 0 | 200 | FAIL >= 184 (lower 2.5 % of Bin(200, 0.95)) | **PASS** |
| 2.2-single_event-one-20/red | 200 | 0 | 200 | 0 | 0 | 200 | FAIL >= 184 (lower 2.5 % of Bin(200, 0.95)) | **PASS** |
| 2.2-single_event-one-20/trend | 200 | 0 | 200 | 0 | 0 | 200 | FAIL >= 184 (lower 2.5 % of Bin(200, 0.95)) | **PASS** |
| 2.2-single_event-one-40/white | 200 | 0 | 200 | 0 | 0 | 200 | FAIL >= 184 (lower 2.5 % of Bin(200, 0.95)) | **PASS** |
| 2.2-single_event-one-40/red | 200 | 0 | 193 | 7 | 0 | 200 | FAIL >= 184 (lower 2.5 % of Bin(200, 0.95)) | **PASS** |
| 2.2-single_event-one-40/trend | 200 | 0 | 200 | 0 | 0 | 200 | FAIL >= 184 (lower 2.5 % of Bin(200, 0.95)) | **PASS** |
| 1.8-single_event-b/white | 200 | 8 | 117 | 75 | 0 | 200 | no PASS | **FAIL** |
| 1.8-single_event-b/red | 200 | 8 | 98 | 94 | 0 | 200 | no PASS | **FAIL** |
| 1.8-single_event-b/trend | 200 | 5 | 127 | 68 | 0 | 200 | no PASS | **FAIL** |
| 2.1-event_consistency-null-6/white | 200 | 0 | 0 | 200 | 0 | 200 | FAIL <= 2 (upper 97.5 % of Bin(200, 0.0027)) | **PASS** |
| 2.1-event_consistency-null-6/red | 200 | 1 | 22 | 177 | 0 | 200 | FAIL <= 2 (upper 97.5 % of Bin(200, 0.0027)) | **FAIL** |
| 2.1-event_consistency-null-6/trend | 200 | 0 | 2 | 198 | 0 | 200 | FAIL <= 2 (upper 97.5 % of Bin(200, 0.0027)) | **PASS** |
| 2.1-event_consistency-null-20/white | 200 | 0 | 0 | 200 | 0 | 200 | FAIL <= 2 (upper 97.5 % of Bin(200, 0.0027)) | **PASS** |
| 2.1-event_consistency-null-20/red | 200 | 0 | 30 | 170 | 0 | 200 | FAIL <= 2 (upper 97.5 % of Bin(200, 0.0027)) | **FAIL** |
| 2.1-event_consistency-null-20/trend | 200 | 0 | 1 | 199 | 0 | 200 | FAIL <= 2 (upper 97.5 % of Bin(200, 0.0027)) | **PASS** |
| 2.1-event_consistency-null-40/white | 200 | 0 | 4 | 196 | 0 | 200 | FAIL <= 2 (upper 97.5 % of Bin(200, 0.0027)) | **FAIL** |
| 2.1-event_consistency-null-40/red | 200 | 0 | 85 | 115 | 0 | 200 | FAIL <= 2 (upper 97.5 % of Bin(200, 0.0027)) | **FAIL** |
| 2.1-event_consistency-null-40/trend | 200 | 0 | 1 | 199 | 0 | 200 | FAIL <= 2 (upper 97.5 % of Bin(200, 0.0027)) | **PASS** |
| 2.3-event_consistency-deep-6/white | 200 | 0 | 200 | 0 | 0 | 200 | FAIL >= 184 (lower 2.5 % of Bin(200, 0.95)) | **PASS** |
| 2.3-event_consistency-deep-6/red | 200 | 1 | 199 | 0 | 0 | 200 | FAIL >= 184 (lower 2.5 % of Bin(200, 0.95)) | **PASS** |
| 2.3-event_consistency-deep-6/trend | 200 | 0 | 200 | 0 | 0 | 200 | FAIL >= 184 (lower 2.5 % of Bin(200, 0.95)) | **PASS** |
| 1.8-event_consistency-b/white | 200 | 0 | 1 | 199 | 0 | 200 | no PASS | **PASS** |
| 1.8-event_consistency-b/red | 200 | 0 | 24 | 176 | 0 | 200 | no PASS | **PASS** |
| 1.8-event_consistency-b/trend | 200 | 0 | 3 | 197 | 0 | 200 | no PASS | **PASS** |
| 1.8-event_consistency-c/white | 200 | 200 | 0 | 0 | 0 | 200 | FAIL <= 2 (upper 97.5 % of Bin(200, 0.0027)) | **PASS** |
| 1.8-event_consistency-c/red | 200 | 186 | 14 | 0 | 0 | 200 | FAIL <= 2 (upper 97.5 % of Bin(200, 0.0027)) | **FAIL** |
| 1.8-event_consistency-c/trend | 200 | 200 | 0 | 0 | 0 | 200 | FAIL <= 2 (upper 97.5 % of Bin(200, 0.0027)) | **PASS** |
| 2.7-event_consistency-partial-6/white | 200 | 200 | 0 | 0 | 0 | 200 | FAIL <= 2 (upper 97.5 % of Bin(200, 0.0027)) | **PASS** |
| 2.7-event_consistency-partial-6/red | 200 | 186 | 14 | 0 | 0 | 200 | FAIL <= 2 (upper 97.5 % of Bin(200, 0.0027)) | **FAIL** |
| 2.7-event_consistency-partial-6/trend | 200 | 199 | 1 | 0 | 0 | 200 | FAIL <= 2 (upper 97.5 % of Bin(200, 0.0027)) | **PASS** |
| 1.8-edge-a/white | 200 | 0 | 200 | 0 | 0 | 200 | FAIL >= 184 (lower 2.5 % of Bin(200, 0.95)) | **PASS** |
| 1.8-edge-a/red | 200 | 0 | 200 | 0 | 0 | 200 | FAIL >= 184 (lower 2.5 % of Bin(200, 0.95)) | **PASS** |
| 1.8-edge-a/trend | 200 | 0 | 200 | 0 | 0 | 200 | FAIL >= 184 (lower 2.5 % of Bin(200, 0.95)) | **PASS** |
| 1.8-edge-b/white | 200 | 0 | 0 | 200 | 0 | 200 | no PASS | **PASS** |
| 1.8-edge-b/red | 200 | 0 | 0 | 200 | 0 | 200 | no PASS | **PASS** |
| 1.8-edge-b/trend | 200 | 0 | 0 | 200 | 0 | 200 | no PASS | **PASS** |
| 2.5-edge-c/white | 200 | 198 | 2 | 0 | 0 | 200 | FAIL <= 2 (upper 97.5 % of Bin(200, 0.0027)) | **PASS** |
| 2.5-edge-c/red | 200 | 199 | 1 | 0 | 0 | 200 | FAIL <= 2 (upper 97.5 % of Bin(200, 0.0027)) | **PASS** |
| 2.5-edge-c/trend | 200 | 200 | 0 | 0 | 0 | 200 | FAIL <= 2 (upper 97.5 % of Bin(200, 0.0027)) | **PASS** |
| 2.6-edge-ramps/white | 200 | 0 | 0 | 200 | 0 | 200 | no PASS | **PASS** |
| 2.6-edge-ramps/red | 200 | 0 | 0 | 200 | 0 | 200 | no PASS | **PASS** |
| 2.6-edge-ramps/trend | 200 | 0 | 0 | 200 | 0 | 200 | no PASS | **PASS** |
| 4.1-centroid-a/white | 200 | 0 | 199 | 1 | 0 | 199 | FAIL >= 184 (lower 2.5 % of Bin(200, 0.95)) | **INVALID** |
| 4.1-centroid-a/red | 200 | 0 | 199 | 1 | 0 | 199 | FAIL >= 184 (lower 2.5 % of Bin(200, 0.95)) | **INVALID** |
| 4.1-centroid-a/trend | 200 | 0 | 200 | 0 | 0 | 200 | FAIL >= 184 (lower 2.5 % of Bin(200, 0.95)) | **PASS** |
| 1.8-centroid-b/white | 200 | 0 | 0 | 200 | 0 | 200 | no PASS | **PASS** |
| 1.8-centroid-b/red | 200 | 0 | 0 | 200 | 0 | 200 | no PASS | **PASS** |
| 1.8-centroid-b/trend | 200 | 0 | 0 | 200 | 0 | 200 | no PASS | **PASS** |
| 4.5-centroid-c/white | 200 | 200 | 0 | 0 | 0 | 200 | FAIL <= 2 (upper 97.5 % of Bin(200, 0.0027)); every other trial PASS | **PASS** |
| 4.5-centroid-c/red | 200 | 199 | 0 | 1 | 0 | 199 | FAIL <= 2 (upper 97.5 % of Bin(200, 0.0027)); every other trial PASS | **INVALID** |
| 4.5-centroid-c/trend | 200 | 200 | 0 | 0 | 0 | 200 | FAIL <= 2 (upper 97.5 % of Bin(200, 0.0027)); every other trial PASS | **PASS** |
| 4.6-centroid-opposite/none | 200 | 0 | 0 | 200 | 0 | 200 | INCONCLUSIVE 'sectors disagree' >= 184 (disagree 200) | **PASS** |
| 4.6-centroid-opposite-pixels/white | 200 | 0 | 0 | 200 | 0 | 200 | INCONCLUSIVE 'sectors disagree' >= 184 (disagree 200) | **PASS** |
| 4.6-centroid-opposite-pixels/red | 200 | 0 | 0 | 200 | 0 | 200 | INCONCLUSIVE 'sectors disagree' >= 184 (disagree 200) | **PASS** |
| 4.6-centroid-opposite-pixels/trend | 200 | 0 | 0 | 200 | 0 | 200 | INCONCLUSIVE 'sectors disagree' >= 184 (disagree 200) | **PASS** |
| 1.8-aperture-a/white | 200 | 0 | 200 | 0 | 0 | 200 | FAIL >= 184 (lower 2.5 % of Bin(200, 0.95)) | **PASS** |
| 1.8-aperture-a/red | 200 | 0 | 200 | 0 | 0 | 200 | FAIL >= 184 (lower 2.5 % of Bin(200, 0.95)) | **PASS** |
| 1.8-aperture-a/trend | 200 | 0 | 200 | 0 | 0 | 200 | FAIL >= 184 (lower 2.5 % of Bin(200, 0.95)) | **PASS** |
| 1.8-aperture-b/white | 200 | 0 | 0 | 200 | 0 | 200 | no PASS | **PASS** |
| 1.8-aperture-b/red | 200 | 0 | 0 | 200 | 0 | 200 | no PASS | **PASS** |
| 1.8-aperture-b/trend | 200 | 0 | 0 | 200 | 0 | 200 | no PASS | **PASS** |
| 1.8-aperture-c/white | 200 | 200 | 0 | 0 | 0 | 200 | FAIL <= 2 (upper 97.5 % of Bin(200, 0.0027)) | **PASS** |
| 1.8-aperture-c/red | 200 | 200 | 0 | 0 | 0 | 200 | FAIL <= 2 (upper 97.5 % of Bin(200, 0.0027)) | **PASS** |
| 1.8-aperture-c/trend | 200 | 200 | 0 | 0 | 0 | 200 | FAIL <= 2 (upper 97.5 % of Bin(200, 0.0027)) | **PASS** |
| 1.8-systematics-sap-a/white | 200 | 0 | 200 | 0 | 0 | 200 | FAIL >= 184 (lower 2.5 % of Bin(200, 0.95)) | **PASS** |
| 1.8-systematics-sap-a/red | 200 | 0 | 200 | 0 | 0 | 200 | FAIL >= 184 (lower 2.5 % of Bin(200, 0.95)) | **PASS** |
| 1.8-systematics-sap-a/trend | 200 | 0 | 200 | 0 | 0 | 200 | FAIL >= 184 (lower 2.5 % of Bin(200, 0.95)) | **PASS** |
| 1.8-systematics-sap-b/white | 200 | 0 | 0 | 200 | 0 | 200 | no PASS | **PASS** |
| 1.8-systematics-sap-b/red | 200 | 0 | 0 | 200 | 0 | 200 | no PASS | **PASS** |
| 1.8-systematics-sap-b/trend | 200 | 0 | 0 | 200 | 0 | 200 | no PASS | **PASS** |
| 1.8-systematics-bkg-a/white | 200 | 0 | 200 | 0 | 0 | 200 | FAIL >= 184 (lower 2.5 % of Bin(200, 0.95)) | **PASS** |
| 1.8-systematics-bkg-a/red | 200 | 0 | 200 | 0 | 0 | 200 | FAIL >= 184 (lower 2.5 % of Bin(200, 0.95)) | **PASS** |
| 1.8-systematics-bkg-a/trend | 200 | 0 | 200 | 0 | 0 | 200 | FAIL >= 184 (lower 2.5 % of Bin(200, 0.95)) | **PASS** |
| 1.8-systematics-bkg-b/white | 200 | 0 | 4 | 196 | 0 | 200 | no PASS | **PASS** |
| 1.8-systematics-bkg-b/red | 200 | 0 | 0 | 200 | 0 | 200 | no PASS | **PASS** |
| 1.8-systematics-bkg-b/trend | 200 | 0 | 1 | 199 | 0 | 200 | no PASS | **PASS** |
| 1.8-systematics-c/white | 200 | 200 | 0 | 0 | 0 | 200 | FAIL <= 2 (upper 97.5 % of Bin(200, 0.0027)) | **PASS** |
| 1.8-systematics-c/red | 200 | 200 | 0 | 0 | 0 | 200 | FAIL <= 2 (upper 97.5 % of Bin(200, 0.0027)) | **PASS** |
| 1.8-systematics-c/trend | 200 | 200 | 0 | 0 | 0 | 200 | FAIL <= 2 (upper 97.5 % of Bin(200, 0.0027)) | **PASS** |
| 1.10-pulls/white | 400 | 0 | 0 | 0 | 0 | 400 | one window and one group per curve: pull sd in [0.9, 1.1] and |mean| <= 0.1 (events sd 1.166, mean 0.081; groups sd 1.027, mean 0.015; floor used 238; all 7200 windows: sd 1.061, mean 0.004, not decided) | **FAIL** |
| 1.10-pulls/red | 400 | 0 | 0 | 0 | 0 | 400 | one window and one group per curve: pull sd in [0.9, 1.1] and |mean| <= 0.1 (events sd 1.348, mean 0.178; groups sd 1.074, mean -0.032; floor used 370; all 7200 windows: sd 1.350, mean -0.013, not decided) | **FAIL** |
| 1.10-pulls/trend | 400 | 0 | 0 | 0 | 0 | 400 | one window and one group per curve: pull sd in [0.9, 1.1] and |mean| <= 0.1 (events sd 1.028, mean 0.039; groups sd 1.022, mean 0.029; floor used 239; all 7200 windows: sd 1.061, mean 0.006, not decided) | **PASS** |
| 1.11-period_alias/white | 200 | 0 | 200 | 0 | 0 | 200 | deterministic; detectable in >= 95 % of trials; FAIL >= 171 among them (detectable 200, FAIL among them 200) | **PASS** |
| 1.11-period_alias/red | 200 | 19 | 181 | 0 | 0 | 200 | deterministic; detectable in >= 95 % of trials; FAIL >= 171 among them (detectable 200, FAIL among them 181) | **PASS** |
| 1.11-period_alias/trend | 200 | 0 | 200 | 0 | 0 | 200 | deterministic; detectable in >= 95 % of trials; FAIL >= 171 among them (detectable 200, FAIL among them 200) | **PASS** |
