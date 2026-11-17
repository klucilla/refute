# Sources for the acknowledgment and citation requests of the README (read 2026-11-16)

The root README quotes the acknowledgment or citation request of each data source and library it
uses ("Data and acknowledgments"). Those texts were copied on 2026-10-07 and 2026-10-08, before
the rule of issue #34 (a source URL, a retrieval date and a short literal excerpt in a `sources/`
record). This record adds what the rule asks, for the release of 2026-11-19 (the maintainer's
decision of 2026-11-16, item 1b; #217).

Each page was read live on 2026-11-16, between 23:49 and 23:51 UTC. A local copy was hashed
(`.cache/pub1119/ack/`, not in git). No request changed against the README's text; where a page
could not be read live, that is stated.

Requests that already have a record are not repeated here:
- **The NASA Exoplanet Archive and ExoFOP:** `third-party-data-2026-11-06.md` (T1 to T4).
- **The TIC credit:** `tic-credit-2026-11-03.md`.
- **The Gaia data license:** `calibration/v0.4/sources/data-licenses-2026-11-01.md` (L1 to L3).

## A1. TESS mission

- URL: https://heasarc.gsfc.nasa.gov/docs/tess/publications.html
- Excerpt: "This paper includes data collected by the TESS mission. Funding for the TESS mission
  is provided by the NASA's Science Mission Directorate."
- SHA-256 of the copy: `94a221545f193ecdfec46d6699e232f0f055e3f97a68f30e2c200e7063330031`

## A2. MAST, mission acknowledgments (TESS)

- URL: https://archive.stsci.edu/publishing/mission-acknowledgements
- Excerpt: "This paper includes data collected with the TESS mission, obtained from the MAST data
  archive at the Space Telescope Science Institute (STScI)."
- The page's text goes on with the funding sentence and the NASA contract NAS5–26555, as the
  README quotes it.
- SHA-256 of the copy: `4e8b8e220b76ed51e9d0343620dc61e648fb785255991e234d55c5772bc70a41`

## A3. NASA Exoplanet Archive (re-read; the record of reference is T3)

- URL: https://exoplanetarchive.ipac.caltech.edu/docs/acknowledge.html ("Last updated: 13 August
  2025")
- Excerpts: "This research has made use of the NASA Exoplanet Archive, which is operated by the
  California Institute of Technology"; "if you use data from a specific literature reference,
  please acknowledge that reference directly"; "Please cite Christiansen et al. (2025)".
- The page names the article but does not print its DOI in the text read. The DOI the README
  gives (10.3847/PSJ/ade3c2) was **not confirmed from this page** on this date.
- SHA-256 of the copy: `2592d1ca6ec4ac3631419bdaaf00967710db828e8366b705fdad715ea2fc0f16`

## A4. ExoFOP-TESS (re-read; the record of reference is T1)

- URL: https://exofop.ipac.caltech.edu/tess/
- Excerpt: "This research has made use of the Exoplanet Follow-up Observation Program (ExoFOP; DOI:
  10.26134/ExoFOP5) website, which is operated by the California Institute of Technology"
- SHA-256 of the copy: `eb5ad4a1aff55bcb76a73594d907f02bca854e5eca7bc1b8dd5342865fdffbff`

## A5. Lightkurve

- URL: https://lightkurve.github.io/lightkurve/about/citing.html
- Excerpt: "This research made use of Lightkurve, a Python package for Kepler and TESS data
  analysis (Lightkurve Collaboration, 2018)."
- The page gives the ADS entry `2018ascl.soft12013L` for that citation.
- SHA-256 of the copy: `5ca546c14979045b19c1d91624edc6dac4ae3805b193b2d67e5fab460e2d930d`

## A6. Astropy

- URL: https://www.astropy.org/acknowledging.html
- Excerpt: "This work made use of Astropy" [...] "a community-developed core Python package and an
  ecosystem of tools and resources for astronomy"
- The page's sentence carries the LaTeX citation keys `astropy:2013`, `astropy:2018` and
  `astropy:2022`, as the README quotes it.
- SHA-256 of the copy: `a52dab556bd3d27648dc24725b802f6eef60af314292f1f896e52a6fc3eb20f6`

## A7. Astroquery

- URL: https://astroquery.readthedocs.io/en/latest/
- Excerpt: "If you use astroquery, please cite the paper Ginsburg, Sipőcz, Brasseur et al 2019."
- SHA-256 of the copy: `421171cb645128b2d3efa937bb7347e206114d3a3fd334921b69571ce9dfef8c`
- Its `CITATION` file: https://github.com/astropy/astroquery/blob/main/astroquery/CITATION (read
  from the raw file). Excerpt: "doi = {10.3847/1538-3881/aafc33}", in the entry
  `2019AJ....157...98G`.
- SHA-256 of the copy: `f1ba5cfe20f48808459a94f21ebf24745cd3c6eb8b066343ad9057b348684bcf`

## A8. Gaia DR3, credit and citation instructions

- URL: https://gea.esac.esa.int/archive/documentation/GDR3/Miscellaneous/sec_credit_and_citation_instructions/
- Excerpt: "This work has made use of data from the European Space Agency (ESA) mission Gaia"
  [...] "institutions participating in the Gaia Multilateral Agreement."
- SHA-256 of the copy: `0f70c12b6bec734435c34fd369c1c57360849fea32f8b340b1b08b5e341f703c`
- The license page, https://www.cosmos.esa.int/web/gaia-users/license, was re-read the same day.
  Excerpt: "Gaia data are distributed under the CC BY-NC 3.0 IGO license."
- SHA-256 of the copy: `114ac918f86572c1e4a1ae3ab97c1ee8798b68636989b8468bba5c4434faf2f9`

## A9. VizieR (CDS), rules of usage: **the live page was not readable on 2026-11-16**

- URL: https://cds.unistra.fr/vizier-org/licences_vizier.html
- **Live read: unconfirmed.** The URL answered HTTP 404 on 2026-11-16 (the CDS incident of
  2026-10-28 is recorded in `calibration/v0.5/sources/cds-incident-2026-11-05.md`).
- Read instead: the archived capture of 2026-10-25T10:23:48Z,
  http://web.archive.org/web/20261025102348/https://cds.unistra.fr/vizier-org/licences_vizier.html
  (the capture that `calibration/v0.4/sources/data-licenses-2026-11-01.md`, L9, already cites).
- Excerpt: "This research has made use of the VizieR catalogue access tool, CDS, Strasbourg, France
  (DOI : 10.26093/cds/vizier). The original description of the VizieR service was published in
  2000, A&AS; 143, 23"
- The capture prints "A&AS;" where the README has "A&AS". The README's copy is of 2026-10-08, and
  the difference is the capture's rendering of the ampersand entity.
- SHA-256 of the copy of the capture: `d0bb90b5dbb97c1a4ef34e32e889f6adb039fb1fddef0276ba662c4290f0e7dd`

## What this record does not cover

- It records requests for credit. It states no license beyond the Gaia sentence above, which the
  earlier records already source.
- The references that the README lists by DOI next to each request (the Astropy papers, the Gaia
  papers, the TESS-EB article) were not re-read one by one on this date.
