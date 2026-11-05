# S5 reviews: each objection mapped to its issue

The first gate review's finding M8 (`calibration/v0.5/gate/gate-1-report.md`): every objection of
the four review reports (`reports/`, unchanged), with its severity as the reviewer gave it, and
the issue that tracks it. `docs/reviewer-protocol.md` requires every important or critical
objection to become an issue; the minor ones are tracked too. Objections never change a verdict.

| Report | # | Severity | Objection (short) | Issue |
|---|---|---|---|---|
| TIC-280206394 | 1 | important | `sinusoid` INCONCLUSIVE by its domain limit (P ≥ 10 d), before reading data | #203; #201 (comment) |
| TIC-280206394 | 2 | minor | `nearby_contamination` FAIL decided by one neighbor at 0.988 of the depth limit, not favored by the pixel results | #205 (comment of 2026-11-05, item 4) |
| TIC-280206394 | 3 | minor | box duration and depth below the trapezoid fit; the report shows the published depth as "n/a" | #205 (body, minor list) |
| TIC-280206394 | 4 | minor | significant per-sector centroid offset (2.65 arcsec, 10.4 sigma) not explained | #205 (comment, item 1) |
| TIC-280206394 | 5 | minor | holdout window half-widths from the full-data candidate duration | #205 (comment of 2026-11-05, item 3) |
| TIC-280206394 | 6 | minor | the word "confirmed" in the holdout message | #205 (body, minor list) |
| TIC-280206394 | 7 | minor | `secondary_eclipse` covers phase 0.5 only | #181 (kept open) |
| TIC-286355915 | 1 | important | no decisive test separates a low-mass stellar companion (EBLM) from a giant planet; the `secondary_eclipse` threshold misses an M-dwarf secondary | #202 (comment) |
| TIC-286355915 | 2 | important | the `eb_catalog` own-TIC warning is guaranteed by the C3 selection | #205 (body, item 1) |
| TIC-286355915 | 3 | minor | the holdout's "depth consistency (sigma)" compares an unmasked train depth with a hidden-window depth | #205 (comment, item 2) |
| TIC-286355915 | 4 | minor | the `sinusoid` message says "no significant sinusoid" when one is significant but below the thresholds | #205 (body, minor list) |
| TIC-286355915 | 5 | minor | search duration below the trapezoid fit and the published value | #205 (body, minor list) |
| TIC-286355915 | 6 | minor | `nearby_contamination` looks only within 21 arcsec | #192 (kept open) |
| TIC-17746821 | 1 | minor | a Sector 7 anomaly never explained | #205 (comment of 2026-11-05, item 2) |
| TIC-17746821 | 2 | minor | the holdout's "depth consistency (sigma)" values without explanation | #205 (comment, item 2) |
| TIC-17746821 | 3 | minor | the transit shape not used against the 7-arcsec neighbor | #191 (moved) |
| TIC-17746821 | 4 | minor | the published depth shown as "n/a" | #205 (body, minor list) |
| TIC-101395259 | 1 | important | the `period_alias` sensitivity simulation, at a fixed threshold, refuses a PASS the data support | #204; #201 (comment) |
| TIC-101395259 | 2 | important | no decisive test addresses an on-target low-mass stellar companion (SB1) | #202 (comment) |
| TIC-101395259 | 3 | important | the report's centroid line hides a significant, consistent offset inside the blind zone | #205 (body, item 2; comment, item 1) |
| TIC-101395259 | 4 | minor | `aperture_depth`'s blind radius is about its core radius, not 10.1 arcsec | #205 (comment of 2026-11-05, item 1) |
| TIC-101395259 | 5 | minor | box depth and duration below the trapezoid fit and the published values | #205 (body, minor list) |
| TIC-101395259 | 6 | minor | the holdout's 5-sigma depth mismatch unremarked | #205 (comment, item 2) |
| TIC-101395259 | 7 | minor | global-ephemeris reduced chi-square 6.79 | #205 (comment of 2026-11-05, item 5) |

Important objections: 6 (1 + 2 + 3; TIC-17746821 had none), each with an issue. Minor: 18.
