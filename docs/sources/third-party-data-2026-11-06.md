# Sources for the third-party data statements of 2026-11-06

Every page below was read by the agent on **2026-11-06** (UTC date), with a direct HTTP request
(`curl`, HTTP 200), unless stated otherwise. Each excerpt is literal and short, so that each
statement that cites it can be checked if the page changes (CLAUDE.md, the rule of issue #34).
Nothing here is legal advice. The pages were saved by the agent while reading them; those copies
are not in the repository. The statements that cite this record are in
[docs/third-party-data.md](../third-party-data.md), [calibration/DATA_LICENSE.md](../../calibration/DATA_LICENSE.md),
[calibration/v0.4/DATA_LICENSE-addendum-2026-11-06.md](../../calibration/v0.4/DATA_LICENSE-addendum-2026-11-06.md),
[calibration/v0.5/DATA_LICENSE.md](../../calibration/v0.5/DATA_LICENSE.md) and the "License"
section of the root README. Earlier readings of the same sources:
[calibration/v0.4/sources/data-licenses-2026-11-01.md](../../calibration/v0.4/sources/data-licenses-2026-11-01.md)
(L1 to L9) and [calibration/v0.5/sources/data-licenses-2026-11-05.md](../../calibration/v0.5/sources/data-licenses-2026-11-05.md)
(D1 to D8).

## T1. ExoFOP data use and professional conduct policy

- URL: https://exofop.ipac.caltech.edu/tess/pcp.php ("Updated: 27 March 2023")
- No license is stated on the page.
- Excerpt: "Please include the following standard acknowledgment in any published material that
  makes use of ExoFOP services" (the acknowledgment cites DOI 10.26134/ExoFOP5).
- Excerpt: "any data associated with a given data provider should be considered their property
  and should not be claimed as anyone else's."
- Excerpt: "The use for publication of any data on ExoFOP that have appeared in journals should be
  accompanied by a citation to the respective article(s)."

## T2. ExoFOP help pages: TFOP and community candidates

- URL: https://exofop.ipac.caltech.edu/tess/help.php
- Excerpt: "TESS Follow-up Observing Program (TFOP) Working Group"
- URL: https://exofop.ipac.caltech.edu/tess/candidate_help.php
- Excerpt: "Community TESS Objects of Interest (cTOIs) are intended to be a mechanism for community
  members to identify planetary systems or other potentially interesting objects discovered by
  TESS but not identified as a TESS Object of Interest"
- **Unconfirmed:** no ExoFOP page read on 2026-11-06 says who writes the `Comments` field of the
  TOI table; the agent found no such statement.

## T3. NASA Exoplanet Archive, acknowledging the archive

- URL: https://exoplanetarchive.ipac.caltech.edu/docs/acknowledge.html ("Last updated: 13 August
  2025")
- No license is stated on the page.
- Excerpt: "This research has made use of the NASA Exoplanet Archive, which is operated by the
  California Institute of Technology, under contract with the National Aeronautics and Space
  Administration under the Exoplanet Exploration Program."
- Excerpt: "if you use data from a specific literature reference, please acknowledge that
  reference directly."
- Excerpt: "Please cite Christiansen et al. (2025)" (the archive's paper in the Planetary Science
  Journal, doi:10.3847/PSJ/ade3c2).

## T4. NASA Exoplanet Archive, PSCompPars column definitions

- URL: https://exoplanetarchive.ipac.caltech.edu/docs/API_PS_columns.html
- Excerpt: "This table provides a more complete, though not necessarily self-consistent, set of
  parameters." (PSCompPars)
- The page and the archive's TAP schema (query
  `select column_name, description from TAP_SCHEMA.columns where table_name like 'pscomppars'`,
  run on 2026-11-06) list the reference columns used by
  `calibration/v0.5/inputs-references/fetch_references.py` and
  `calibration/v0.4/inputs-references/fetch_references.py`: `pl_orbper_reflink` ("Orbital Period
  Reference"), `pl_tranmid_reflink`, `pl_trandep_reflink`, `pl_trandur_reflink`,
  `sy_tmag_reflink`, `ra_reflink` ("RA Reference") and `disc_refname` ("Discovery Reference").
  The schema has no reference column of its own for `pl_orbpererr1` or `dec`. For them the script
  reports the period's reference and the column described as "RA Reference"; that pairing is the
  agent's inference, not a reference the archive gives for those two columns.

## T5. TESS target lists page (MIT): **terms unconfirmed as of 2026-11-06**

- URL: https://tess.mit.edu/public/target_lists/target_lists.html
- Read on 2026-11-06 (HTTP 200, 96,379 bytes): byte-identical to the frozen input
  `calibration/v0.5/inputs/target_lists.html` (SHA-256 `8bd50089…`). Neither the page nor the
  frozen copy contains the words "copyright", "license" or "terms", or the © sign. Whether the
  TESS Science Office or MIT states terms elsewhere is **unconfirmed**.

## T6. TESS mission page (MIT)

- URL: https://tess.mit.edu/
- Excerpt: "The TESS Science Office is run by MIT and the Center for Astrophysics | Harvard &
  Smithsonian."
- No copyright notice, license or terms of use is shown on the page (none of those words occurs
  in its text).

## T7. arXiv API terms of use

- URL: https://info.arxiv.org/help/api/tou.html
- Excerpt: "You are free to use descriptive metadata about arXiv e-prints under the terms of the
  Creative Commons Universal (CC0 1.0) Public Domain Declaration."
- Excerpt (its footnote): "Descriptive metadata includes information for discovery and
  identification purposes, and includes fields such as title, abstract, authors, identifiers, and
  classification terms."
