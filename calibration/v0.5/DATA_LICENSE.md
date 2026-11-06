# Data license of the v0.5 calibration's third-party files

The code of Refute is licensed under Apache-2.0. Four files of the v0.5 calibration hold data
from third parties, and a fifth, added on 2026-11-06, gives the literature reference of the
`pscomppars` values used by the C3 planets; the selection and run files quote values from them.
They are not code, and each component keeps its own terms, listed below.
Sources, with literal excerpts and the date read: [sources/data-licenses-2026-11-05.md](sources/data-licenses-2026-11-05.md)
(D1 to D8, read on 2026-11-05) and [docs/sources/third-party-data-2026-11-06.md](../../docs/sources/third-party-data-2026-11-06.md)
(T1 to T7, read on 2026-11-06). Every third-party data file of the repository, in all phases, is
listed with the record that covers it in [docs/third-party-data.md](../../docs/third-party-data.md).

**There is no single license for the whole package.** Each component's terms apply to that
component only, and none of them can be chosen for the package as a whole.

**An exception, restricted to v0.5.** Rule 3 of [docs/data-publication.md](../../docs/data-publication.md)
keeps Gaia DR3 rows off Zenodo. For the files below only, the maintainer made an explicit
exception on 2026-11-05, recorded in that file and in issue #199: they stay in the repository and
in the release's Zenodo archive, each component with its terms here. No v0.5 data record is
published on Zenodo. The exception is an internal rule of this project; it is not a general change
of the rule, and it grants no right that the sources do not grant.

## Components

| Component | Where it appears | Terms | Credit required |
|---|---|---|---|
| Gaia DR3 rows (`gaiadr3.vari_eclipsing_binary` with `gaia_source` coordinates: source_id, RA, Dec, period) | `calibration/v0.5/eb_catalog.csv`, the 3 rows whose `catalog` is `Gaia-DR3-EB` (an attachment of the locked C3 claim) | **CC BY-NC 3.0 IGO** (https://creativecommons.org/licenses/by-nc/3.0/igo/), D1, D2, D3. **Non-commercial use only**; commercial use needs a prior request to ESA (D2) | "Credit: ESA, Gaia DPAC" (D2) |
| TESS-EB references (Prša et al. 2022) | the same file, the 14 rows whose `catalog` is `TESS-EB`: the catalog name and the TIC number only, **no catalog values** (the TESS-EB table itself is never committed, #33) | identifiers only; the catalog's terms (CC BY 4.0 at MAST, v0.4 record L4) are not engaged by these rows. VizieR's rules page: **unconfirmed as of 2026-11-05** (D7) | Prša et al. 2022, ApJS 258, 16, doi:10.3847/1538-4365/ac324a (when the catalog is used) |
| The ExoFOP-TESS TOI table | `calibration/v0.5/inputs/toi.csv` (the frozen input of the C3 selection, retrieved from ExoFOP on 2026-11-04 and recorded with its SHA-256 in `calibration/v0.5/inputs.json`) | **Acknowledgment and citation; no formal license stated** (D4, T1). The file is the **whole TOI table**, reproduced unchanged as the frozen input. Its `Comments` column is text written on ExoFOP by its authors, members of the TESS Follow-up Observing Program (TFOP); the comments remain theirs (ExoFOP: data from a provider "should be considered their property", T1). That TFOP members write that column is the maintainer's statement; no ExoFOP page found on 2026-11-06 says so (**unconfirmed**, T2). Values that come from journal articles are to be cited through those articles (D4, T1). **The maintainer's acceptance of 2026-11-01, extended on 2026-11-06 to the whole TOI table** (#199), covers its redistribution with the acknowledgment; a confirmation from ExoFOP was not requested | "This research has made use of the Exoplanet Follow-up Observation Program (ExoFOP; DOI: 10.26134/ExoFOP5) website, which is operated by the California Institute of Technology, under contract with the National Aeronautics and Space Administration under the Exoplanet Exploration Program." (D4, T1) |
| The NASA Exoplanet Archive's Planetary Systems Composite Parameters table (`pscomppars`) | `calibration/v0.5/inputs/pscomppars.csv` (the frozen input of the C3 selection, retrieved on 2026-11-04 and recorded in `calibration/v0.5/inputs.json`; unchanged) | **Acknowledgment; no formal license stated on the acknowledgment page** (D5, T3; whether one exists elsewhere is unconfirmed). The archive asks that values from a specific literature reference be acknowledged through that reference (D5, T3). The frozen query did not select the reference columns; **the reference of every value of the whole table is kept by the archive**, in the table's own reference columns (T4). For the values used by the C3 planets, see the next row | "This research has made use of the NASA Exoplanet Archive, which is operated by the California Institute of Technology, under contract with the National Aeronautics and Space Administration under the Exoplanet Exploration Program." (D5, T3); cite Christiansen et al. (2025), doi:10.3847/PSJ/ade3c2 (T3); cite the literature reference of each value used |
| The literature references of the `pscomppars` values used by the C3 planets | `calibration/v0.5/inputs-references/pscomppars-references.csv`, from a new query of the same table on 2026-11-06 (the maintainer's decision, #199): for the 11 planets of the locked claim (`claim-targets.yaml`, kind `planet`), each used value with its reference column (the table has no reference column of its own for `pl_orbpererr1` or `dec`; the period's and the "RA Reference" columns are paired with them, an inference stated in T4). The query URL, the time, the SHA-256 and a value-by-value comparison with the frozen file (88 values, none changed) are in `pscomppars-references.json`; the script is `fetch_references.py` | the archive's terms, as in the row above (D5, T3, T4) | the archive's acknowledgment and Christiansen et al. (2025), as above; and the references listed in the file for the values a user takes |
| The TESS target lists page (MIT) | `calibration/v0.5/inputs/target_lists.html` (a copy of the page, the frozen input that fixed S_max; recorded in `calibration/v0.5/inputs.json`) | **Unconfirmed as of 2026-11-06**: the page shows no copyright notice, license or terms, and none was found on the mission's page (D8, T5, T6). The maintainer decided on 2026-11-06 (#199) that the copy stays in the repository and in the release archive with the credit at right; this project's exception establishes no right to redistribute it. The file has been public in this repository since commit `5f987db` (a bound input of the freeze) | the TESS Science Office (MIT) (the maintainer's decision); the page is on the mission's site, tess.mit.edu, whose Science Office "is run by MIT and the Center for Astrophysics \| Harvard & Smithsonian" (T6) |
| Values quoted from the tables above | `calibration/v0.5/selection/` (the targets, the selection and its ledger: published periods, depths, TOI dispositions and TIC values of the chosen controls), `claim-targets.yaml`, and the run records, dossier summaries, reviews and gate reports of `calibration/v0.5/` that repeat them | the terms of the table each value comes from (rows above; TIC values: MAST, D6) | as in the rows above |
| TESS data (MAST): numbers and plots derived by Refute from TESS light curves and pixel files | the run records and reports of `calibration/v0.5/`; **no raw MAST file** is in the repository | MAST: "Most data hosted at MAST are in the public domain" (D6); this is not a statement about every product | acknowledge the TESS mission and MAST |
| Refute's own content: claims, protocols, selections, run records, reports, reviews and gate reports, except the components above | everything else in `calibration/v0.5/` | the repository's license unless a published record states otherwise; **decided by the maintainer** in each published record | as the record states |

## Changes made to third-party data

None of the values above is changed. The two input tables are byte copies of the retrievals
recorded in `calibration/v0.5/inputs.json` (each with its SHA-256); the Gaia DR3 rows are copied
from the v0.2.0 release asset `gaia_dr3_vari_eclipsing_binary.csv`, checked against its SHA-256
and row count (PROTOCOL.md, section 9). The references file is the archive's answer to the query
recorded in `pscomppars-references.json`, unchanged (its SHA-256 is recorded there).
