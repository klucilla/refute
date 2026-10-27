# The real controls' availability, checked early: the result (gate 3b)

The check declared in [README.md](README.md) (committed and pushed in `ece59fa`, before any query),
run once on 2026-10-27 from 04:04 to 04:38 UTC at that commit, with the environment of the
dependency update `cf63c4d`. Script: [scripts/real_controls_check.py](scripts/real_controls_check.py);
its output: [result.json](result.json).

## Outcome: **short**. The minimum is not reached; X2f stays blocked

| Class | Candidates after the exclusions | Inside the domain by metadata | Minimum |
| --- | ---: | ---: | ---: |
| Confirmed planets | 464 | **11** | 20 |
| Known false positives | 447 | **0** | 20 |

No search failed (0 search errors, 0 unexpected errors): 911 TICs searched, every one classified.
As the plan fixes (section 5), **X2f stays blocked and the decision goes back to the maintainer;
the domain is not widened**, and no filter is relaxed.

## Where the candidates fall (the first condition failing)

| Class | D1 (not three years) | D2 (three years, not three sectors) | D3 products | D5 (separations) | Inside |
| --- | ---: | ---: | ---: | ---: | ---: |
| Confirmed planets | 364 | 59 | 0 | 30 | 11 |
| Known false positives | 395 | 39 | 0 | 13 | 0 |

A descriptive breakdown of the same rows ([breakdown.json](breakdown.json),
[scripts/breakdown.py](scripts/breakdown.py); it recomputes the classification from the recorded
rows and finds the same counts):

- **Distinct years** of SPOC 120-s light-curve sectors per TIC. Planets: 0 years 13, 1 year 57,
  2 years 129, 3 years 100, 4 to 7 years 165. False positives: 0 years 97, 1 year 174, 2 years 91,
  3 years 52, 4 to 7 years 33.
- **Three years and exactly three sectors:** 41 planets and 13 false positives; of these, 30 planets
  and all 13 false positives fail D5. Most D5 failures have both separations near two years, or a
  separation of about three to five years (the separations are listed in `breakdown.json`).

## Information only (not searched, not counted)

The same classes without the period, depth, magnitude and multiplicity filters, after the
exclusions, counted from the catalogues: 3666 confirmed-planet TICs and 1302 false-positive TICs.

## Sources (as recorded in `result.json`)

- NASA Exoplanet Archive `pscomppars` (TAP), read 2026-10-27 04:04:05 UTC, 505 319 bytes, SHA-256
  `055b9ca07f2fedfdbf92714f06cee51f983e45ba77fe09be578860cc07f73518`.
- ExoFOP-TESS TOI table, read 2026-10-27 04:04:35 UTC, 3 813 611 bytes, SHA-256
  `79ee6e0d9c11a6d04f8bf21c5e40cdb95cdb84a030ccb0c24386e82311d51f57`.
- MAST (`https://mast.stsci.edu`, lightkurve 2.6.0, astroquery 0.4.11), searched from 04:04:42 to
  04:36:49 UTC; the rows returned for each TIC are in `.cache/real-controls/mast-rows.json`
  (2 621 842 bytes, SHA-256 `57fb8a014e8aacc5c0de5fc30dcbf46f6bd8315b30c5642281381fdfd46567c2`),
  kept outside git with the two catalogue snapshots, as declared.

The exclusions: the 35 TICs of the declared inventory (`result.json`, `exclusions`).

## What this shows, and what it does not

It shows availability only, from metadata: D3's measured intervals and D4, and D1 and D5 as the
domain computes them from the first kept cadence, were not checked, so the 11 planets inside by
metadata are candidates, not calibration targets. No light curve was downloaded or analysed, no
output of the engine was read, and nothing here is a selection: the eligible list in `result.json`
is a record of availability, and any draw is gate 13's.
