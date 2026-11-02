# Data license of the v0.4 pilot's dossiers and archives

The code of Refute is licensed under Apache-2.0. The data in the v0.4 pilot's dossiers and in its
two reproduction archives are not code, and each component keeps its own terms, listed below.
This file sits **outside the sealed bytes**: it does not change any dossier or archive, and it
travels with each copy that is published (the repository, each Zenodo record). Sources, with
literal excerpts and the date read: [sources/data-licenses-2026-11-01.md](sources/data-licenses-2026-11-01.md).

**There is no single license for the whole package.** Each component's terms apply to that
component only, and none of them can be chosen for the package as a whole.

**An exception, restricted to v0.4.** Rule 3 of [docs/data-publication.md](../../docs/data-publication.md)
keeps Gaia DR3 and TESS-EB rows off Zenodo, and the maintainer decided on 2026-10-08/10 not to
redistribute TESS-EB rows. For the v0.4 dossiers and archives only, the maintainer made an
explicit exception on 2026-11-01, recorded in that file and in issue #177. The exception is an
internal rule of this project; it grants no right that the sources do not grant.

## Components

| Component | Where it appears | Terms | Credit required |
|---|---|---|---|
| Gaia DR3 rows (`gaiadr3.vari_eclipsing_binary` with `gaia_source` coordinates: source_id, RA, Dec, period) | `attachments/eb_catalog.csv` of the stage-2 dossiers (rows near the target, where any); quoted in some review annexes (`annexes/review-opus-1/review.md`) | **CC BY-NC 3.0 IGO** (https://creativecommons.org/licenses/by-nc/3.0/igo/), L1, L3. **Non-commercial use only**; commercial use needs a prior request to ESA (L2) | "Credit: ESA, Gaia DPAC" (L2) |
| TESS-EB records (Prša et al. 2022), obtained through VizieR | catalog matches recorded by the `eb_catalog` test (`verdict.json`, `report.md`, the case and reproduction annexes) of the dossiers where a match occurred; elsewhere only as reference rows (catalog and identifier, no values) | **CC BY 4.0** (https://creativecommons.org/licenses/by/4.0/), L4; the CC BY 4.0 terms convey with the data (L5) | Prša et al. 2022, ApJS 258, 16, doi:10.3847/1538-4365/ac324a; MAST HLSP doi:10.17909/t9-9gm4-fx30 (L4) |
| VizieR (CDS), the service the TESS-EB table was retrieved from | the retrieval records (`attachments/inputs.json`, `attachments/eb_catalog_scan.json`) | **Unconfirmed as of 2026-11-01**: the rules page could not be re-read (L6); last read 2026-10-17: free of usage in a scientific context, copyrights depend on the data origin | acknowledge VizieR (CDS, Strasbourg) |
| TOI values from ExoFOP (the controls' published period and its uncertainty) | `annexes/measurements/cross_match.json`, the case annexes, `export*/candidate_parameters.*` of the control dossiers | **No license stated; permission to redistribute not confirmed** (L7). Acknowledgment and citation do not replace a permission | "This research has made use of the Exoplanet Follow-up Observation Program (ExoFOP; DOI: 10.26134/ExoFOP5) website, which is operated by the California Institute of Technology, under contract with the National Aeronautics and Space Administration under the Exoplanet Exploration Program." (L7) |
| TESS data (MAST): numbers and plots derived by Refute from TESS light curves and pixel files | throughout the dossiers; **no raw MAST file** is in the dossiers or archives | MAST: "Most data hosted at MAST are in the public domain" (L5); this is not a statement about every product | acknowledge the TESS mission and MAST |
| Refute's own content: verdicts, test records, reports, plots, case files, the ledger, reviews and annexes, except the components above | everything else | **decided by the maintainer** in each published record; not implied by the Apache-2.0 license of the code | as the record states |

## Changes made to third-party data

None of the values above is changed. The TESS-EB table was checked by its content SHA-256 after
download, and four header metadata lines of the raw file were restored to the frozen values before
its raw SHA-256 was checked (`calibration/v0.4/reproduce_inputs.py`); the catalog content is never
adjusted.
