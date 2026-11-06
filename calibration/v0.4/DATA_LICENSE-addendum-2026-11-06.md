# Data license of the v0.4 repository files: an addendum (2026-11-06)

[DATA_LICENSE.md](DATA_LICENSE.md) of v0.4 (published with release v0.4.0) covers the data in the
v0.4 pilot's dossiers and its two reproduction archives. It does not cover the third-party files
that the v0.4 pilot keeps **in this repository**: its frozen inputs and its catalog attachment.
That gap, found by the inventory of the whole tree on 2026-11-06
([docs/third-party-data.md](../../docs/third-party-data.md)), is corrected by this new record, on
the maintainer's decision of 2026-11-06 (#199). The published DATA_LICENSE.md is not edited.

These files have been in the repository since the v0.4 pilot was frozen, and they were in the
release archive of v0.4.0; they stay in the repository and in later release archives, each
component with its terms here. The references file of the known-planet control
(`calibration/v0.4/inputs-references/`) was added on 2026-11-06 and joins them. Sources, with literal excerpts and the date read:
[sources/data-licenses-2026-11-01.md](sources/data-licenses-2026-11-01.md) (L1 to L9),
[../v0.5/sources/data-licenses-2026-11-05.md](../v0.5/sources/data-licenses-2026-11-05.md) (D1 to
D8) and [docs/sources/third-party-data-2026-11-06.md](../../docs/sources/third-party-data-2026-11-06.md)
(T1 to T7). Nothing here is legal advice.

**There is no single license for these files.** Each component's terms apply to that component
only. This record is an internal rule of this project; it grants no right that the sources do not
grant.

## Components

| Component | Where it appears | Terms | Credit required |
|---|---|---|---|
| The ExoFOP-TESS TOI table | `calibration/v0.4/inputs/toi.csv` (frozen input, retrieved 2026-10-29; URL and SHA-256 in `calibration/v0.4/inputs.json`) | **Acknowledgment and citation; no formal license stated** (L7, D4, T1). The whole TOI table, reproduced unchanged; its `Comments` column is text written on ExoFOP by its authors and remains theirs (T1; who writes it: **unconfirmed** by an ExoFOP page, T2). Values that come from journal articles are to be cited through those articles (D4, T1). The maintainer's acceptance of 2026-11-01, extended on 2026-11-06 to the whole TOI table (#199) | ExoFOP's standard acknowledgment, with DOI 10.26134/ExoFOP5 (L7, T1) |
| The ExoFOP-TESS community candidate table (CTOI) | `calibration/v0.4/inputs/ctoi.csv` (frozen input, retrieved 2026-10-29; URL and SHA-256 in `calibration/v0.4/inputs.json`) | **Acknowledgment and citation; no formal license stated** (T1). Community TESS Objects of Interest are submitted by community members (T2); the file is the whole table, unchanged, with the submitters' `User`, `Group`, `Paper` and `Notes` columns, which remain theirs (T1). Published candidates are to be cited through their papers (T1). The maintainer's acceptance of 2026-11-01, extended on 2026-11-06 to the whole TOI table, **also covers the whole CTOI table** since 2026-11-06, with the same terms and the same acknowledgment (#199) | ExoFOP's standard acknowledgment (T1); the paper listed for a candidate, when its values are used |
| The NASA Exoplanet Archive's `pscomppars` table | `calibration/v0.4/inputs/pscomppars.csv` (frozen input, retrieved 2026-10-29; URL and SHA-256 in `calibration/v0.4/inputs.json`; byte-identical to the v0.5 copy, SHA-256 `bb9e29d4…`) | **Acknowledgment; no formal license stated on the acknowledgment page** (D5, T3). The reference of every value is kept by the archive in the table's reference columns (T4); the frozen query did not select them. The v0.4 pilot used the table for its exclusions, its cross-match and its one known-planet control (TIC 86396382, WASP-12 b). The references of that control's values are in `calibration/v0.4/inputs-references/pscomppars-references.csv`, from a new query of the same table on 2026-11-06 (the maintainer's decision, #199); the query URL, the time, the SHA-256 and a value-by-value comparison with the frozen file (8 values, none changed) are in `pscomppars-references.json`, and the script is `fetch_references.py`. The table has no reference column of its own for `pl_orbpererr1` or `dec`; the period's and the "RA Reference" columns are paired with them, an inference stated in T4 | the archive's acknowledgment (T3); cite Christiansen et al. (2025), doi:10.3847/PSJ/ade3c2 (T3); the literature reference of each value used |
| The TESS target lists page (MIT) | `calibration/v0.4/inputs/target_lists.html` (frozen input, retrieved 2026-10-29; SHA-256 in `calibration/v0.4/inputs.json`). The per-sector lists it links are not in the repository | **Unconfirmed as of 2026-11-06**: no copyright notice, license or terms is shown on the page or on the mission's page (D8, T5, T6) | the TESS Science Office (MIT), as for v0.5 (T6) |
| Gaia DR3 rows | `calibration/v0.4/eb_catalog.csv`, the 4 rows whose `catalog` is `Gaia-DR3-EB` (an attachment of the locked v0.4 claim) | **CC BY-NC 3.0 IGO** (L1, L3, D1 to D3). **Non-commercial use only**; commercial use needs a prior request to ESA (L2, D2) | "Credit: ESA, Gaia DPAC" (L2, D2) |
| TESS-EB reference | the same file, the row whose `catalog` is `TESS-EB`: the catalog name and the TIC number only, no catalog values | identifiers only | Prša et al. 2022, doi:10.3847/1538-4365/ac324a (when the catalog is used) |
| Values quoted from the tables above | `calibration/v0.4/selection/`, `claim.yaml`, `inputs.json`, `runs/` and `results/` (for example the ledger) | the terms of the table each value comes from (rows above; TIC values: MAST, L5, D6) | as in the rows above |

## Changes made to third-party data

None. The frozen inputs are byte copies of the retrievals recorded in `calibration/v0.4/inputs.json`.
The references file is the archive's answer to the query recorded in `pscomppars-references.json`,
unchanged (its SHA-256 is recorded there).
