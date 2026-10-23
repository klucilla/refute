# TESS coverage by observing years: what the sources say (context only)

Asked by the maintainer on 2026-10-23 (item 2), only as context for a future scope decision; it
changes no quota, criterion or study. All pages read on **2026-10-23**. **No source found states the
fraction of TESS targets with data in two years and in three or more years**; the excerpts below are
the nearest statements found, kept short and literal.

| Source | What it gives | Excerpt (literal) |
|---|---|---|
| TESS Science Support Center (NASA HEASARC), "What is TESS?", <https://heasarc.gsfc.nasa.gov/docs/tess/what-is-tess.html> (page dated 2026-10-20) | the re-observation pattern by hemisphere and cycle; the sky fraction by the end of the second extended mission | "the Southern ecliptic hemisphere was re-observed"; "TESS would cover at least 95% of the sky" |
| Winn, "The Transiting Exoplanet Survey Satellite", arXiv:2410.12905v1, <https://arxiv.org/html/2410.12905v1> | qualitative: each hemisphere surveyed three times by the end of 2024; a star's duration of observation | "TESS will have surveyed each hemisphere three times"; "ranging from 27 days to 351 days" |
| The TESS All-Sky Rotation Survey (TARS), arXiv:2603.05586v1, <https://arxiv.org/html/2603.05586v1> | per star, sectors (not years), for stars with T < 16 within 500 pc, sectors 1 to 96 (2018 July to 2025 September) | "The median star has four sectors of TESS data"; "7,481,412 stars observed by TESS at least once" |

- **What these do not give:** sectors are not years (a star near an ecliptic pole can have many
  sectors in one year; a star elsewhere a few sectors spread over several years), and the TARS
  sample is a selection (T < 16, d < 500 pc), not the targets of a transit search.
- **How the fraction could be obtained** (not done; its own decision): from the per-star sector
  lists, for example the TARS catalog at MAST (the paper points to `https://archive.stsci.edu/hlsp/tars`)
  or the sector pointings applied to a target list, counting the distinct calendar years per star.
  That is a data download, suspended until the dependency update (the maintainer's decision of
  2026-10-22), and a choice of the target population.
