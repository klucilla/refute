# Calibration summary: tess-calibration-v0.2

## Self-claim result: **FAIL**

> Refute recovers at least 9 of 10 known TESS planets (period within 0.1% of the published value), flags at least 6 of 10 known false positives by analyzing their signals, and gives the verdict REFUTED to at most 1 of the 10 known planets.

at least one criterion failed.

| Criterion | Value | Requirement | Passed |
|---|---|---|---|
| recovered planets | 10 of 10 | >= 9 | yes |
| flagged false positives (without eb_catalog) | 7 of 10 | >= 6 | yes |
| refuted planets (degeneracy guard) | 4 of 10 | <= 1 | no |

> **Scope.** Refute is calibrated only in an easy regime defined by pre-registered selection filters (see the claim's protocol attachment): confirmed planets with orbital periods between 0.5 and 10 days, transit depths of at least 1000 ppm, TESS magnitude 12 or brighter, a single known planet in the system, and SPOC 2-minute data in at least two calendar years; false positives with the same period, depth and magnitude limits. The calibration says nothing about longer periods, shallower transits, fainter stars, multi-planet systems or other data products.

Information (not a criterion): 8 of 10 false positives are REFUTED when every test counts, including eb_catalog.

## Targets

| Target | Name | Kind | Published P (d) | Found P (d) | Rel. error | Alias | Recovered | Verdict | Signal verdict | Tests not passed |
|---|---|---|---|---|---|---|---|---|---|---|
| TIC-118327550 | TOI-244 b | planet | 7.397225 | 7.397246 | 2.78e-06 | P | yes | REFUTED | REFUTED | holdout_by_year FAIL |
| TIC-48506505 | Kepler-447 b | planet | 7.794301 | 7.794303 | 2.65e-07 | P | yes | REFUTED | REFUTED | nearby_contamination FAIL, holdout_by_year FAIL |
| TIC-19028197 | GJ 3470 b | planet | 3.336650 | 3.336654 | 1.22e-06 | P | yes | SURVIVED | SURVIVED | - |
| TIC-158561566 | Kepler-14 b | planet | 6.790123 | 6.790125 | 2.74e-07 | P | yes | REFUTED | INCONCLUSIVE | plausibility INCONCLUSIVE, period_alias FAIL, eb_catalog FAIL |
| TIC-139528693 | WASP-78 b | planet | 2.175180 | 2.175181 | 5.40e-07 | P | yes | WEAKENED | WEAKENED | secondary_eclipse FAIL |
| TIC-151825527 | TOI-672 b | planet | 3.633581 | 3.633583 | 5.21e-07 | P | yes | SURVIVED | SURVIVED | - |
| TIC-231670397 | WASP-73 b | planet | 4.087220 | 4.087300 | 1.97e-05 | P | yes | SURVIVED | SURVIVED | - |
| TIC-193754373 | TOI-4487 A b | planet | 3.954071 | 3.954063 | 2.03e-06 | P | yes | WEAKENED | WEAKENED | nearby_contamination FAIL |
| TIC-194736418 | TOI-6038 A b | planet | 5.826731 | 5.826749 | 3.13e-06 | P | yes | REFUTED | REFUTED | nearby_contamination FAIL, holdout_by_year FAIL |
| TIC-158588995 | TOI-674 b | planet | 1.977143 | 1.977165 | 1.09e-05 | P | yes | SURVIVED | SURVIVED | - |
| TIC-33153766 | TOI-653.01 | false_positive | 0.688310 | 0.688227 | 1.20e-04 | P | - | REFUTED | REFUTED | centroid_shift FAIL, aperture_depth FAIL, nearby_contamination FAIL |
| TIC-197650870 | TOI-1481.01 | false_positive | 2.185317 | 1.677366 | 2.32e-01 | - | - | REFUTED | REFUTED | secondary_eclipse FAIL, plausibility FAIL, nearby_contamination FAIL, period_alias FAIL |
| TIC-374200604 | TOI-4838.01 | false_positive | 0.760019 | 0.760016 | 3.82e-06 | P | - | INCONCLUSIVE | INCONCLUSIVE | holdout_by_year INCONCLUSIVE |
| TIC-350445771 | TOI-258.01 | false_positive | 3.190157 | 3.190154 | 1.05e-06 | P | - | REFUTED | REFUTED | secondary_eclipse FAIL, nearby_contamination FAIL, eb_catalog FAIL |
| TIC-317507345 | TOI-1615.01 | false_positive | 3.940179 | 3.940176 | 7.02e-07 | P | - | REFUTED | WEAKENED | secondary_eclipse FAIL, eb_catalog FAIL |
| TIC-158916431 | TOI-2146.01 | false_positive | 5.892486 | 5.892498 | 2.11e-06 | P | - | REFUTED | REFUTED | centroid_shift FAIL, aperture_depth FAIL |
| TIC-316916655 | TOI-441.01 | false_positive | 2.874360 | 2.874367 | 2.60e-06 | P | - | REFUTED | REFUTED | odd_even FAIL, centroid_shift FAIL, nearby_contamination FAIL, eb_catalog FAIL, holdout_by_year INCONCLUSIVE |
| TIC-154459165 | TOI-611.01 | false_positive | 3.147165 | 3.147138 | 8.86e-06 | P | - | REFUTED | REFUTED | centroid_shift FAIL, nearby_contamination FAIL, holdout_by_year FAIL |
| TIC-294179389 | TOI-1310.01 | false_positive | 2.679413 | 2.679421 | 3.17e-06 | P | - | WEAKENED | WEAKENED | nearby_contamination FAIL |
| TIC-315755496 | TOI-2053.01 | false_positive | 4.278080 | 4.277984 | 2.25e-05 | P | - | REFUTED | REFUTED | plausibility INCONCLUSIVE, nearby_contamination FAIL, holdout_by_year FAIL |

## Diagnostics (not part of the claim)

- Planets with verdict SURVIVED: 4
- Holdout test statuses: {'FAIL': 5, 'PASS': 13, 'INCONCLUSIVE': 2}
- Verdicts by kind: {'false_positive:INCONCLUSIVE': 1, 'false_positive:REFUTED': 8, 'false_positive:WEAKENED': 1, 'planet:REFUTED': 4, 'planet:SURVIVED': 4, 'planet:WEAKENED': 2}
- Analysis errors: none
- TIC-374200604 INCONCLUSIVE: holdout_by_year: no hidden year could be tested

## Run

- Run id: `20261009T155044Z-c9f341d2`
- Started / finished (UTC): 2026-10-09T15:50:43+00:00 / 2026-10-09T15:57:37+00:00
- Workers: 30, offline: true
- Claim SHA-256: `c9f341d29bea4ec0d125adf3f0822fae4b593beabbdd19aeb339613e7a6b34a8`
- Code SHA-256: `2cd8b5c16c9ded3e32335cd95d8b68f46e0676d5183f3129a6cef4e8dfbd1752`
- Lock commit: `e176ac3d21ca6e2efeb5085a8acb44d69624d520`; run commit: `cc9d104027edbc000f40f0e62a2a8e07da6775c7` (dirty: False)
- Python 3.13.5 on Windows-11-10.0.26300-SP0
