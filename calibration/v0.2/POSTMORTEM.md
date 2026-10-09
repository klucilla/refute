# Post-mortem: v0.2 self-claim (FAIL)

> **Draft, to be completed after the reviewer draw of 2026-10-11.** Committed before
> the reviews of the 3 drawn planets, so that git records that the observations and
> hypotheses below were written before those reviews.

**The pre-registered v0.2 self-claim failed.** Refute recovered the periods of all
10 known planets and flagged 7 of 10 known false positives, but it gave the verdict
REFUTED to **4 of 10** known planets (at most 1 was allowed).

Nothing was changed to make the claim pass: thresholds, targets, data and code are
exactly as locked. The result files are in
[`results/20261009T155044Z-c9f341d2/`](results/20261009T155044Z-c9f341d2/)
([summary](results/20261009T155044Z-c9f341d2/summary.md),
[run log](RUNS.md), [reviews](results/20261009T155044Z-c9f341d2/reviews/)).

> **How to read this document.**
> - Sections and columns marked *Fact (dossier)* only restate what the locked code
>   produced. They come from `verdict.json`, from the summary and from the committed
>   selection files.
> - Columns marked *Reviewer* restate what an independent reviewer wrote in its
>   report. They are observations by a model, with the evidence the reviewer cited.
>   They were not recomputed for this document, and they do not change any verdict.
> - Sections marked **post-hoc hypothesis** were written after the run, while
>   looking at the results and the reviews. They are ideas to be tested in a later,
>   separately locked claim. None of them was pre-registered or implemented.
>
> Dossier paths such as `TIC-118327550/verdict.json` are relative to the run
> directory `dossiers/20261009T155044Z-c9f341d2/`. That directory is not in git; it
> will be published as the dossier archive. Review reports are in git, under
> `results/20261009T155044Z-c9f341d2/reviews/<target>/opus-1.md`.

## The claim

> Refute recovers at least 9 of 10 known TESS planets (period within 0.1% of the
> published value), flags at least 6 of 10 known false positives by analyzing
> their signals, and gives the verdict REFUTED to at most 1 of the 10 known
> planets.

- Claim `tess-calibration-v0.2`, claim SHA-256
  `c9f341d29bea4ec0d125adf3f0822fae4b593beabbdd19aeb339613e7a6b34a8`.
- Code SHA-256 `2cd8b5c16c9ded3e32335cd95d8b68f46e0676d5183f3129a6cef4e8dfbd1752`.
- Locked from commit `e176ac3` at 2026-10-09T15:29:55Z. The lock was committed and
  pushed in `cc9d104` before the run, and `refute verify` returned PASS before and
  after the run.
- Targets: drawn by [PROTOCOL.md](PROTOCOL.md) with the seed from drand round
  6537566. The 14 v0.1 targets were excluded. The regime is the same easy regime as
  v0.1.
- *Flagged* means a known false positive whose verdict, recomputed without
  `eb_catalog`, is REFUTED. The summary reports that recomputed value as the
  "signal verdict".

## Result (Fact, dossier)

| Criterion | Value | Requirement | Result |
|---|---|---|---|
| Recovered planets | 10 of 10 | ≥ 9 | pass |
| Flagged false positives (without `eb_catalog`) | 7 of 10 | ≥ 6 | pass |
| Refuted planets (degeneracy guard, every test) | 4 of 10 | ≤ 1 | **fail** |

Information, not a criterion: with every test counted, including `eb_catalog`,
8 of 10 false positives are REFUTED.

| Target | Name | Kind | Verdict | Signal verdict | Reason (from the locked tests) |
|---|---|---|---|---|---|
| TIC 118327550 | TOI-244 b | planet | **REFUTED** | REFUTED | `holdout_by_year` failed for hidden year 2023 |
| TIC 48506505 | Kepler-447 b | planet | **REFUTED** | REFUTED | `holdout_by_year` failed for hidden year 2024 |
| TIC 19028197 | GJ 3470 b | planet | SURVIVED | SURVIVED | every test passed |
| TIC 158561566 | Kepler-14 b | planet | **REFUTED** | INCONCLUSIVE | `eb_catalog` (TESS-EB, 1 x the found period) |
| TIC 139528693 | WASP-78 b | planet | WEAKENED | WEAKENED | `secondary_eclipse` (warning) |
| TIC 151825527 | TOI-672 b | planet | SURVIVED | SURVIVED | every test passed |
| TIC 231670397 | WASP-73 b | planet | SURVIVED | SURVIVED | every test passed |
| TIC 193754373 | TOI-4487 A b | planet | WEAKENED | WEAKENED | `nearby_contamination` (warning) |
| TIC 194736418 | TOI-6038 A b | planet | **REFUTED** | REFUTED | `holdout_by_year` failed for hidden year 2019 |
| TIC 158588995 | TOI-674 b | planet | SURVIVED | SURVIVED | every test passed |
| TIC 33153766 | TOI-653.01 | false positive | REFUTED | REFUTED | `centroid_shift`, `aperture_depth` |
| TIC 197650870 | TOI-1481.01 | false positive | REFUTED | REFUTED | `plausibility`, `period_alias` |
| TIC 374200604 | TOI-4838.01 | false positive | INCONCLUSIVE | INCONCLUSIVE | `holdout_by_year`: no hidden year could be tested |
| TIC 350445771 | TOI-258.01 | false positive | REFUTED | REFUTED | `secondary_eclipse`, `eb_catalog` |
| TIC 317507345 | TOI-1615.01 | false positive | REFUTED | WEAKENED | `eb_catalog` |
| TIC 158916431 | TOI-2146.01 | false positive | REFUTED | REFUTED | `centroid_shift`, `aperture_depth` |
| TIC 316916655 | TOI-441.01 | false positive | REFUTED | REFUTED | `odd_even`, `centroid_shift`, `eb_catalog` |
| TIC 154459165 | TOI-611.01 | false positive | REFUTED | REFUTED | `centroid_shift`, `holdout_by_year` |
| TIC 294179389 | TOI-1310.01 | false positive | WEAKENED | WEAKENED | `nearby_contamination` (warning) |
| TIC 315755496 | TOI-2053.01 | false positive | REFUTED | REFUTED | `holdout_by_year` failed for hidden year 2024 |

Every planet's period was found within the tolerance, all at the published period
and none at an alias. Relative errors range from 2.7e-7 (Kepler-447 b) to 2.0e-5
(WASP-73 b). Nine of the 10 false positives were found at their catalogued period.
For TOI-1481.01 the period found, 1.6773662 d, differs from the catalogued 2.1853174 d
by a relative 0.23 and is not an alias of it.

## Reviews (Fact)

The 10 false positives and the 4 refuted planets were reviewed on 2026-10-09 by
fresh Claude Opus 5.5 sessions, one per dossier, following
`docs/reviewer-protocol.md` (details and times in [RUNS.md](RUNS.md)). No verdict
changed. The second reviewer, Codex, was left out because its connection was not
available.

| Assessment | Dossiers |
|---|---|
| SERIOUS OBJECTIONS | TOI-244 b, Kepler-447 b, Kepler-14 b, TOI-6038 A b, TOI-1481.01, TOI-1310.01, TOI-2053.01 |
| OBJECTIONS | TOI-653.01, TOI-4838.01, TOI-258.01, TOI-1615.01, TOI-2146.01, TOI-441.01, TOI-611.01 |
| NO OBJECTION | none |

The 3 planets drawn with drand round 6542966 are reviewed later (see the last
section).

## Observations by test

### `holdout_by_year`

It is a fatal test. It failed for 5 targets, and the verdict depended on it alone
for 4 of them: TOI-244 b, Kepler-447 b, TOI-6038 A b and TOI-2053.01.

| Target | Fact (dossier: `verdict.json` → `holdout_rounds`) | Reviewer | Review |
|---|---|---|---|
| TOI-244 b | 2023 FAIL, hidden SNR 4.97 against `min_snr` 5.0, 3 windows. The other 4 rounds PASS at SNR 5.64 to 10.89. Every round's train period is 7.3972 d. | Hidden depth 998 ± 201 ppm at the predicted time, 0.79 sigma from the train depth. The error is max(white, scatter) over 3 windows; the white error alone gives SNR 6.3. There is no power check. | [TIC-118327550](results/20261009T155044Z-c9f341d2/reviews/TIC-118327550/opus-1.md) |
| Kepler-447 b | 2024 FAIL, SNR 0.21. That round's train candidate is 0.51766 d with a 10.4 h box and 259 windows. The 2021 and 2022 rounds PASS (SNR 8.64, 9.61) with a train period of 7.7943 d. | The 2024 round tested a different signal. Its train SNR (7.05) is below the 7.1 gate, its windows cover the whole hidden year, and the 7.79 d transit is present in the 2024 sectors. | [TIC-48506505](results/20261009T155044Z-c9f341d2/reviews/TIC-48506505/opus-1.md) |
| TOI-6038 A b | 2019 FAIL, SNR 4.84, train period 5.83018 d (published 5.8267311 d). 2024 INCONCLUSIVE, with no hidden read. | The train ephemeris uses 3 transits (1 degree of freedom), so its error is not inflated, and it is 13.4 sigma off. The windows sit about 1.38 d from the transits. With realistic timing errors the round would be INCONCLUSIVE. | [TIC-194736418](results/20261009T155044Z-c9f341d2/reviews/TIC-194736418/opus-1.md) |
| TOI-611.01 | 2021 FAIL, SNR −0.18, train candidate 0.52412 d with an 11.2 h box. 2025 FAIL, SNR −0.08, train candidate 0.52265 d with an 11.2 h box. 2023 FAIL, SNR 4.71, train period 3.14715 d. | 2021 and 2025 tested about 0.52 d variability: the windows cover 100% of the hidden year, so it was not detrended. 2023 lacked power: the expected SNR was about 3.4. | [TIC-154459165](results/20261009T155044Z-c9f341d2/reviews/TIC-154459165/opus-1.md) |
| TOI-2053.01 | 2024 FAIL, SNR 4.87. The other 3 rounds PASS at SNR 7.0 to 9.93. | Hidden depth 625.6 ppm against a train depth of 580.1 ppm (0.34 sigma). The white error alone gives SNR 8.6. The best period correction is at the edge of the scan. | [TIC-315755496](results/20261009T155044Z-c9f341d2/reviews/TIC-315755496/opus-1.md) |
| TOI-1481.01 | 2022 PASS, SNR 12.58, train candidate 1.67745 d with a 12.0 h box. 2024 INCONCLUSIVE. | The windows are about 2.7 times the transit, and the reads cover all of sectors 56 and 57. The round detects the minimum of the variability. | [TIC-197650870](results/20261009T155044Z-c9f341d2/reviews/TIC-197650870/opus-1.md) |
| TOI-4838.01, TOI-441.01 | Every round INCONCLUSIVE before any hidden read (empty access logs). | Not contested: the train-only timing error exceeded one duration. | [TIC-374200604](results/20261009T155044Z-c9f341d2/reviews/TIC-374200604/opus-1.md), [TIC-316916655](results/20261009T155044Z-c9f341d2/reviews/TIC-316916655/opus-1.md) |

Reviewers' other notes on the holdout:
- **Phase-0.5 control above the threshold.** The control reached `min_snr` 5.0 or
  more in TOI-2146.01 (5.54), TOI-258.01 (4 of 5 rounds), TOI-1615.01 (2024, 5.4) and
  TOI-6038 A b (5.5). The control is reported, not judged.
- **Report wording.** Five reviews state that `HiddenYear` detrends the whole hidden
  year before any logged read: TOI-653.01, TOI-258.01, TOI-1310.01, TOI-244 b and
  TOI-6038 A b. So the sentence "the hidden year is read only inside the predicted
  windows" overstates how blind the test is. No review found a logged
  transit-window read outside a registered window.

### `centroid_shift`

It is a fatal test. The test FAILs only when the offset is significant (≥ 3 sigma)
**and** at least `min_offset_pixels` 0.5.

| Group | Fact (dossier: test message and metrics) |
|---|---|
| FAIL (4) | TOI-653.01 (2.35 px, 30.7 sigma), TOI-2146.01 (0.97 px, 25.4 sigma), TOI-611.01 (0.90 px, 11.6 sigma), TOI-441.01 (0.89 px, 7.4 sigma) |
| PASS with ≥ 3 sigma but under 0.5 px (12) | TOI-1310.01 (0.34 px, 35.2 sigma), TOI-674 b (0.20, 34.0), TOI-672 b (0.21, 24.8), GJ 3470 b (0.32, 24.6), WASP-78 b (0.13, 18.6), TOI-258.01 (0.24, 18.3), TOI-1615.01 (0.08, 13.3), TOI-4487 A b (0.08, 12.2), WASP-73 b (0.12, 7.6), TOI-1481.01 (0.34, 6.9), Kepler-14 b (0.15, 4.8), TOI-4838.01 (0.27, 3.5) |
| PASS under 3 sigma (4) | TOI-6038 A b (0.28 px, 2.1 sigma), TOI-2053.01 (0.32, 1.4), Kepler-447 b (0.18, 0.9), TOI-244 b (0.44, 0.0) |

Before the lock, on the v0.1 development target, the protocol recorded 0.13 px at
24.5 sigma with a PASS through the same floor (PROTOCOL.md, "Development target
observations").

| Target | Reviewer | Review |
|---|---|---|
| TOI-1310.01 | Critical. The 35-sigma offset points the same way (+y) in all 6 sectors. ExoFOP names a neighbor at 9.48″ (0.45 px) as the source. The test passed only through the 0.5 px floor, and `aperture_depth` cannot separate a source 0.45 px away. | [TIC-294179389](results/20261009T155044Z-c9f341d2/reviews/TIC-294179389/opus-1.md) |
| TOI-258.01 | Important. The test rejects zero offset at 18 sigma, yet the message reads "consistent with the target". It cannot resolve anything under about 0.5 px. | [TIC-350445771](results/20261009T155044Z-c9f341d2/reviews/TIC-350445771/opus-1.md) |
| TOI-611.01, TOI-441.01 | The error budget is statistical only, with no systematic floor. No position angles are recorded, so the direction cannot be matched to a neighbor. | see the table above |
| TOI-653.01, TOI-2146.01, TOI-441.01 | `source_offset` is the in-aperture centroid of the varying light. For a source at or beyond the aperture edge it is a lower bound, not a position. | [TIC-33153766](results/20261009T155044Z-c9f341d2/reviews/TIC-33153766/opus-1.md), [TIC-158916431](results/20261009T155044Z-c9f341d2/reviews/TIC-158916431/opus-1.md) |

### `eb_catalog`

It is a fatal test, and it is excluded from *flagged*.

| Target | Fact (dossier and committed selection files) | Reviewer | Review |
|---|---|---|---|
| Kepler-14 b (planet) | FAIL. TESS-EB row `TIC 158561566 (1)`, matched by TIC ID, period 6.78996 d = 1 x the found period. It is the only fatal failure. The match was already listed at selection (`eb_catalog_scan.json`, `tess_eb: 1`), before the lock. | Critical. REFUTED rests only on a catalog listing at the target's own transit period, while every data-based eclipsing-binary test passed. | [TIC-158561566](results/20261009T155044Z-c9f341d2/reviews/TIC-158561566/opus-1.md) |
| TOI-1615.01 | FAIL, TESS-EB by TIC ID, 1 x the found period. It is the only fatal failure, so the signal verdict is WEAKENED. | Important. The report does not state the signal-only verdict. The match cannot be checked from the dossier alone, because TESS-EB is not redistributed. | [TIC-317507345](results/20261009T155044Z-c9f341d2/reviews/TIC-317507345/opus-1.md) |
| TOI-258.01, TOI-441.01 | FAIL, TESS-EB by TIC ID, 1 x the found period. Other fatal tests also failed. | TOI-441.01: TESS-EB was built from TESS photometry of the same signal, so it is not independent evidence. | [TIC-316916655](results/20261009T155044Z-c9f341d2/reviews/TIC-316916655/opus-1.md) |
| TOI-653.01 | PASS (no entry within 21″). | The centroid points 30 to 50″ away, outside the 21″ radius, so this PASS did not look where the source is. | [TIC-33153766](results/20261009T155044Z-c9f341d2/reviews/TIC-33153766/opus-1.md) |

All 4 TESS-EB matches were known at selection: `tess_eb: 1` for these 4 TICs in
`eb_catalog_scan.json`. The single Gaia DR3 row extracted (near TOI-1481.01) was
outside 21″.

### `nearby_contamination`

It is a warning test. It FAILed for 10 targets: Kepler-447 b, TOI-4487 A b,
TOI-6038 A b, TOI-653.01, TOI-1481.01, TOI-258.01, TOI-441.01, TOI-611.01,
TOI-1310.01 and TOI-2053.01. It only considers TIC neighbors within
`max_separation_arcsec` 21″.

| Target | Reviewer (neighbors outside 21″, or the test's inputs) | Review |
|---|---|---|
| TOI-441.01 | TIC 316916663 is the star TFOP named. It is at 46.7″ and would need an eclipse of about 10%. | [TIC-316916655](results/20261009T155044Z-c9f341d2/reviews/TIC-316916655/opus-1.md) |
| TOI-2053.01 | TIC 315755491 is at 36.6″ (Tmag 13.21) and would need about 0.87%. ExoFOP notes an "ephemeris match" to it. | [TIC-315755496](results/20261009T155044Z-c9f341d2/reviews/TIC-315755496/opus-1.md) |
| TOI-4838.01 | TIC 374200603 is at 42.7″ and would need about 2%. | [TIC-374200604](results/20261009T155044Z-c9f341d2/reviews/TIC-374200604/opus-1.md) |
| TOI-653.01 | TIC 33153801 is at 50.9″ and would need about 11%. The centroid points 30 to 50″ to the north-east. | [TIC-33153766](results/20261009T155044Z-c9f341d2/reviews/TIC-33153766/opus-1.md) |
| TOI-2146.01 | TIC 158916451 (27.2″) and TIC 158916415 (59″) are possible sources outside the radius. | [TIC-158916431](results/20261009T155044Z-c9f341d2/reviews/TIC-158916431/opus-1.md) |
| TOI-1310.01 | A viable neighbor at 9.48″, named by ExoFOP as the source, leads only to a warning. | [TIC-294179389](results/20261009T155044Z-c9f341d2/reviews/TIC-294179389/opus-1.md) |
| TOI-1481.01 | The required eclipse depths were computed from an artifact depth of 61573 ppm. Scaled to the catalogued 1168 ppm, the neighbor at 12.7″ would be viable. | [TIC-197650870](results/20261009T155044Z-c9f341d2/reviews/TIC-197650870/opus-1.md) |

### `period_alias`

| Target | Fact (dossier) | Reviewer | Review |
|---|---|---|---|
| TOI-1481.01 | FAIL (fatal): adding a box improves the BIC by −10.7 < 10. | Sensible for the 1.677 d signal that was analyzed, which is not the catalogued one. | [TIC-197650870](results/20261009T155044Z-c9f341d2/reviews/TIC-197650870/opus-1.md) |
| Kepler-14 b | FAIL (warning): 6.790 d is within 1% of the listed systematic period 6.85 d. | A false alarm from a coarse tolerance; the box gains ΔBIC 3443.7 over a sinusoid. | [TIC-158561566](results/20261009T155044Z-c9f341d2/reviews/TIC-158561566/opus-1.md) |
| TOI-1310.01 | PASS. | Phase-coherent out-of-transit variability (ellipsoidal or synchronized) is not tested. | [TIC-294179389](results/20261009T155044Z-c9f341d2/reviews/TIC-294179389/opus-1.md) |

### `plausibility`

| Target | Fact (dossier) | Reviewer | Review |
|---|---|---|---|
| TOI-1481.01 | FAIL (fatal): implied companion radius 9.71 R_Jup. | The radius comes from a 6% depth created by the masked detrending. At about 1000 ppm it would be about 1.2 R_Jup. | [TIC-197650870](results/20261009T155044Z-c9f341d2/reviews/TIC-197650870/opus-1.md) |
| TOI-2053.01 | INCONCLUSIVE (fatal): the TIC radius has no uncertainty. | A 2.1 h duration at 4.28 d is 0.12 to 0.16 of the maximum for a 5.3 R_sun star. The test only rejects durations that are too long. | [TIC-315755496](results/20261009T155044Z-c9f341d2/reviews/TIC-315755496/opus-1.md) |
| TOI-4838.01 | PASS (duration ratio 0.25). | Such a short duration implies b ≈ 1.0 (grazing), or a denser host. "Plausible" overstates this. | [TIC-374200604](results/20261009T155044Z-c9f341d2/reviews/TIC-374200604/opus-1.md) |
| TOI-611.01 | PASS (duration ratio 1.34 < 1.5). | The long duration points to a larger host, which the report does not mention. | [TIC-154459165](results/20261009T155044Z-c9f341d2/reviews/TIC-154459165/opus-1.md) |
| Kepler-14 b | INCONCLUSIVE (warning): no TIC stellar mass. | `targets.yaml` carries `st_mass` 1.512 from the Archive. | [TIC-158561566](results/20261009T155044Z-c9f341d2/reviews/TIC-158561566/opus-1.md) |
| TOI-1615.01 | PASS. | The box depth and duration are biased low for a V-shaped eclipse, so the inputs understate a grazing geometry. | [TIC-317507345](results/20261009T155044Z-c9f341d2/reviews/TIC-317507345/opus-1.md) |

### `secondary_eclipse`

| Target | Fact (dossier) | Reviewer | Review |
|---|---|---|---|
| TOI-258.01 | FAIL (fatal): 13.9 sigma, depth ratio 0.206. | Decisive. The secondary is seen again in the hidden-year phase-0.5 controls. | [TIC-350445771](results/20261009T155044Z-c9f341d2/reviews/TIC-350445771/opus-1.md) |
| TOI-1615.01 | FAIL (warning): 6.5 sigma, depth ratio 0.064 < 0.1. | 775 ± 120 ppm, against an estimated maximum planetary occultation of about 225 to 300 ppm. Only a depth-ratio threshold is applied. | [TIC-317507345](results/20261009T155044Z-c9f341d2/reviews/TIC-317507345/opus-1.md) |
| TOI-1481.01 | FAIL (warning): 11.6 sigma, depth ratio 0.009. | The ratio uses the artifact primary depth. Against the real depth it would be about 0.6 to 1.0, which is fatal. | [TIC-197650870](results/20261009T155044Z-c9f341d2/reviews/TIC-197650870/opus-1.md) |
| TOI-2146.01 | PASS: 2.81 sigma, depth ratio 0.091, close to both limits. | Narrow pass. The holdout control at phase 0.5 also reached SNR 5.54. | [TIC-158916431](results/20261009T155044Z-c9f341d2/reviews/TIC-158916431/opus-1.md) |
| WASP-78 b (planet, not reviewed) | FAIL (warning): 4.0 sigma, depth ratio 0.022. | not reviewed | none |

### Observations outside the seven tests

- **Detrending artifact.** In TOI-1481.01 the reviewer found that the masked
  quadratic detrend created a dip 61573 ppm deep. The same ephemeris measures about
  600 to 1400 ppm in every other test.
- **No shape test.** Several reviews note that V-shaped eclipses are not tested:
  TOI-4838.01, TOI-1615.01, TOI-258.01, TOI-2146.01 and Kepler-447 b.
- **Parameter sheet.** In TOI-4838.01, TOI-2146.01 and TOI-1310.01 the sheet mixes
  the search period with the global ephemeris's epoch and error.
- **Report precision.** Epochs are printed with 6 significant digits in the report's
  Signal table, which hides the agreement between the found and published epochs.

## What the 7 of 10 does and does not show

The criterion "flags at least 6 of 10 known false positives" passed with 7, and that
result is locked. The table below adds no recomputation. It lists, for each flagged
false positive, the fatal failures that made the signal verdict REFUTED, and what
its reviewer wrote about them.

| False positive | Fatal failures counted (`eb_catalog` excluded) | Reviewer on those failures | Assessment |
|---|---|---|---|
| TOI-653.01 | `centroid_shift`, `aperture_depth` | "I could not refute": each failure is strongly supported, the offsets agree in sky coordinates across 4 sectors and 2 cameras. Only minor objections. | OBJECTIONS |
| TOI-1481.01 | `plausibility`, `period_alias` | Critical. The signal analyzed (1.677 d) is not the catalogued 2.185 d signal, and the `plausibility` failure comes from an artifact depth. `period_alias` is "sensible" for the analyzed signal. | SERIOUS OBJECTIONS |
| TOI-258.01 | `secondary_eclipse` | Decisive, and seen again in the hidden-year controls. The objections are about wording and blends under 0.1 px. | OBJECTIONS |
| TOI-2146.01 | `centroid_shift`, `aperture_depth` | "I found no objection that weakens the verdict." | OBJECTIONS |
| TOI-441.01 | `odd_even`, `centroid_shift` | "All objections are minor and none undermines REFUTED." | OBJECTIONS |
| TOI-611.01 | `centroid_shift`, `holdout_by_year` | The holdout failures are contested: two rounds tested a different signal and one lacked power. `centroid_shift` "looks robust", but its error budget is statistical only (important). | OBJECTIONS |
| TOI-2053.01 | `holdout_by_year` | Critical. The only fatal driver is a near-threshold miss (SNR 4.87), with the predicted dip present at the predicted depth. | SERIOUS OBJECTIONS |

Counts, from the reports:
- **2 of the 7** have serious objections to the basis of their flag:
  - TOI-1481.01 was flagged while analyzing a signal different from the catalogued
    one.
  - TOI-2053.01 was flagged only by a holdout round that its reviewer contests.
- **5 of the 7** have no serious objection: TOI-653.01, TOI-258.01, TOI-2146.01,
  TOI-441.01 and TOI-611.01.
  - In 4 of them, the reviewer did not contest any failure that made the signal
    verdict REFUTED.
  - In TOI-611.01, one of its two fatal failures (`holdout_by_year`) is contested,
    and the other (`centroid_shift`) carries an important objection.

Without the two flags that carry serious objections, 5 of 10 would remain, below
the required 6. This is not a recomputation of the locked result, which stays a
pass on this criterion; it shows how narrow that pass was.

The 3 false positives that were not flagged:
- **TOI-4838.01** is INCONCLUSIVE: no hidden year could be tested. Its reviewer
  notes that its documented mechanism, an unresolved hierarchical eclipsing binary,
  is not testable by the gauntlet.
- **TOI-1615.01** has the signal verdict WEAKENED (a `secondary_eclipse` warning) and
  is REFUTED only through `eb_catalog`.
- **TOI-1310.01** is WEAKENED by the `nearby_contamination` warning. Its reviewer
  raised a critical objection: `centroid_shift` passed at 35 sigma only because of
  the 0.5 px floor.

## What worked (Fact)

- **Period recovery:** Refute recovered the periods of all 10 known planets, each at
  the published period.
- **Complete run:** all 20 targets were analyzed, with no analysis error, and every
  dossier manifest is intact.
- **Lock:** `refute verify` returned PASS before and after the run and after the
  reviews.
- **Holdout reads:** in every reviewed dossier, the reviewer found each logged
  transit-window read equal to a registered window.
- **Planets:** 4 SURVIVED and 2 WEAKENED (both warnings).
- **False positives:** the pixel tests (`centroid_shift`, `aperture_depth`) failed
  for 4 of them (TOI-653.01, TOI-2146.01, TOI-441.01 and TOI-611.01). v0.1 had no
  pixel tests.

## Process notes (Fact)

- **MAST timeout at selection.** False-positive position 35, TIC 239638934, was
  rejected after a MAST timeout. A later check showed that the data rule would
  have rejected it too, so the selected targets are the same. The outputs were
  committed unchanged, by the maintainer's decision. Tracked in
  [#22](https://github.com/klucilla/refute/issues/22).
- **Reviews:** they were run on isolated copies of the dossiers. The second
  reviewer (Codex) was not available.

## Hypotheses for the next iteration (post-hoc hypothesis)

Everything in this section is a **post-hoc hypothesis**. It was written after
seeing the results and the reviews, and none of it is implemented. Each item would
have to be specified, validated on synthetic data, and tested by a new, separately
locked claim on new targets.

1. **Holdout power check.** A round whose expected SNR, from the train depth and the
   hidden-year noise, is near or below `min_snr` would be INCONCLUSIVE, not FAIL. A
   FAIL could also require the hidden depth to be inconsistent with the train
   prediction (TOI-244 b, TOI-2053.01, TOI-611.01).
2. **Holdout error estimate.** The window-to-window scatter over 2 to 3 windows is a
   noisy estimate. A different combination with the white error, or a minimum number
   of windows, may be needed (TOI-244 b, TOI-2053.01).
3. **Propagated timing and period uncertainty.** With 3 transit times
   (1 degree of freedom) the ephemeris error is not inflated. A floor, or an
   estimate of the per-transit timing error from other data, might have made the
   TOI-6038 A b round INCONCLUSIVE.
4. **Protection against a wrong training period.** The train candidate could be
   required to pass the SNR gate, to have a duration well below the period, and to
   give windows that do not cover the hidden year. Otherwise the round would be
   INCONCLUSIVE (Kepler-447 b, TOI-611.01).
5. **Unmasked train detrending.** The train search detrends without a transit mask,
   which biases the train depth low and makes `depth_consistency_sigma` misleading
   (TOI-6038 A b, Kepler-14 b).
6. **Detrending of strongly variable stars.** The masked quadratic detrend can
   create deep artificial dips (TOI-1481.01).
7. **Signal identity for known targets.** When the analyzed period does not match
   the catalogued one, a known false positive could be reported as "signal not
   recovered" instead of counting as flagged (TOI-1481.01).
8. **The 0.5 px floor of `centroid_shift`.** Its role, a systematic error term,
   position angles toward catalogued neighbors, and the wording of the PASS message
   could all be revisited (TOI-1310.01, TOI-258.01, TOI-611.01). The floor was set
   because of the 24.5-sigma offset of a real planet, so any change needs synthetic
   validation against that case.
9. **`eb_catalog` deciding alone.** A TIC-ID match in a catalog built from the same
   TESS photometry is not independent of the signal. It could be a warning, or count
   only together with a data-based failure (Kepler-14 b, TOI-1615.01, TOI-441.01).
10. **The 21″ search radius.** `nearby_contamination` and `eb_catalog` stop at 21″,
    while several catalogued sources of these false positives lie at 27 to 59″
    (TOI-441.01, TOI-2053.01, TOI-4838.01, TOI-653.01, TOI-2146.01).
11. **Missing tests of transit shape and geometry.** There is no V versus U shape
    test, no stellar-density or short-duration test, and no maximum planetary
    occultation depth for the secondary (TOI-4838.01, TOI-1615.01, TOI-2053.01,
    TOI-258.01).
12. **Severity of `nearby_contamination`.** A viable neighbor inside the centroid
    floor only leads to a warning (TOI-1310.01).
13. **Smaller items.**
    - `period_alias` uses a 1% tolerance around systematic periods (Kepler-14 b).
    - `plausibility` does not use the Archive stellar mass when the TIC mass is
      missing (Kepler-14 b).
    - The parameter sheet mixes estimators.
    - The report rounds epochs and words the holdout's blindness too strongly.

## The 3 planets drawn for review (placeholder)

To be filled after drand round 6542966 (2026-10-11T12:00:00Z):
`select_reviews.py` draws 3 of the 6 planets whose verdict is not REFUTED: GJ 3470 b,
WASP-78 b, TOI-672 b, WASP-73 b, TOI-4487 A b and TOI-674 b.

| Target | Name | Verdict | Assessment | Main objections | Review |
|---|---|---|---|---|---|
| _pending_ | | | | | |
| _pending_ | | | | | |
| _pending_ | | | | | |

## Rules for the next calibration

1. **The 20 v0.2 calibration targets and the v0.2 development target (WASP-93 b) are
   now a known set**, like the 14 v0.1 targets. Their results have been seen, so
   they cannot be used to validate any change, including the hypotheses above. They
   may be used for debugging only, and any such use must be declared.
2. **The next calibration needs a new draw**, with a new seed defined and locked
   before any analysis of its targets. The draw excludes every known target.
3. **The v0.2 claim is never re-locked or re-run to make it pass.** This failure stays
   published as it is.
