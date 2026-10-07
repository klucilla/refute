# Calibration summary: tess-calibration-v0.1

## Self-claim result: **FAIL**

> Refute recovers at least 9 of 10 known TESS planets (period within 0.1% of the published value), flags at least 2 of 3 known false positives, and gives the verdict REFUTED to at most 1 of the 10 known planets.

at least one criterion failed.

| Criterion | Value | Requirement | Passed |
|---|---|---|---|
| recovered planets | 10 of 10 | >= 9 | yes |
| flagged false positives | 0 of 3 | >= 2 | no |
| refuted planets (degeneracy guard) | 1 of 10 | <= 1 | yes |

> **Scope.** Refute v0.1 is calibrated only in an easy regime defined by pre-registered selection filters (calibration/PROTOCOL.md): confirmed planets with orbital periods between 0.5 and 10 days, transit depths of at least 1000 ppm, TESS magnitude 12 or brighter, a single known planet in the system, and SPOC 2-minute data in at least two calendar years; false positives with the same period, depth and magnitude limits. The calibration says nothing about longer periods, shallower transits, fainter stars, multi-planet systems or other data products.

## Targets

| Target | Name | Kind | Published P (d) | Found P (d) | Rel. error | Alias | Recovered | Verdict | snr | odd_even | secondary | plausibility | holdout |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| TIC-207141131 | HD 18599 b | planet | 4.137435 | 4.137437 | 3.69e-07 | P | yes | SURVIVED | PASS | PASS | PASS | PASS | PASS |
| TIC-138819293 | GJ 436 b | planet | 2.643883 | 2.643898 | 5.53e-06 | P | yes | SURVIVED | PASS | PASS | PASS | PASS | PASS |
| TIC-77031414 | WASP-173 A b | planet | 1.386653 | 1.386653 | 3.14e-07 | P | yes | SURVIVED | PASS | PASS | PASS | PASS | PASS |
| TIC-440872576 | TOI-3160 A b | planet | 3.971281 | 3.971283 | 5.89e-07 | P | yes | REFUTED | PASS | PASS | PASS | PASS | FAIL |
| TIC-36592530 | WASP-75 b | planet | 2.484193 | 2.484197 | 1.71e-06 | P | yes | SURVIVED | PASS | PASS | PASS | PASS | PASS |
| TIC-369327947 | LHS 475 b | planet | 2.029088 | 2.029107 | 9.13e-06 | P | yes | SURVIVED | PASS | PASS | PASS | PASS | PASS |
| TIC-398572544 | WASP-28 b | planet | 3.408835 | 3.408836 | 3.80e-07 | P | yes | SURVIVED | PASS | PASS | PASS | PASS | PASS |
| TIC-283621618 | TOI-5806 b | planet | 3.185638 | 3.185641 | 9.07e-07 | P | yes | SURVIVED | PASS | PASS | PASS | PASS | PASS |
| TIC-374530847 | WASP-2 b | planet | 2.152175 | 2.152218 | 2.01e-05 | P | yes | SURVIVED | PASS | PASS | PASS | PASS | PASS |
| TIC-36452991 | TOI-2969 b | planet | 1.823715 | 1.823715 | 1.51e-07 | P | yes | SURVIVED | PASS | PASS | PASS | PASS | PASS |
| TIC-285524410 | TOI-2848.01 | false_positive | 3.024422 | 3.024947 | 1.74e-04 | P | - | INCONCLUSIVE | PASS | PASS | PASS | INCONCLUSIVE | PASS |
| TIC-404610583 | TOI-5966.01 | false_positive | 3.538232 | 3.538227 | 1.39e-06 | P | - | SURVIVED | PASS | PASS | PASS | PASS | PASS |
| TIC-95129101 | TOI-1704.01 | false_positive | 3.929983 | 3.929970 | 3.42e-06 | P | - | SURVIVED | PASS | PASS | PASS | PASS | PASS |

## Diagnostics (not part of the claim)

- Planets with verdict SURVIVED: 9
- Holdout test statuses: {'PASS': 12, 'FAIL': 1}
- Verdicts by kind: {'false_positive:INCONCLUSIVE': 1, 'false_positive:SURVIVED': 2, 'planet:REFUTED': 1, 'planet:SURVIVED': 9}
- Analysis errors: none
- TIC-285524410 INCONCLUSIVE: plausibility: no TIC stellar radius available

## Run

- Run id: `20261007T221214Z-5701c54c`
- Started / finished (UTC): 2026-10-07T22:12:12+00:00 / 2026-10-07T22:15:02+00:00
- Workers: 30, offline: true
- Claim SHA-256: `5701c54cb088f1d33895f73d98244d0ea214ddb3f861340d8261b817e189a53f`
- Code SHA-256: `624f5f900334abcdc614a679a3fdc4ce9c9e8a465f2d3e553d71b24c199f4cfa`
- Lock commit: `5214f2e29de98803aafff3094733ca424ae3dbde`; run commit: `821b0d791c81d0c3c61d333d93b286b78321dba3` (dirty: False)
- Python 3.13.5 on Windows-11-10.0.26300-SP0
