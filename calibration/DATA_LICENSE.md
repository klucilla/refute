# Data license of third-party content not covered by a phase record

The code of Refute is licensed under Apache-2.0. Some third-party content in this repository had
no DATA_LICENSE until 2026-11-06: the pool snapshots of the v0.1 and v0.2 calibrations (tables
retrieved from ExoFOP and from the NASA Exoplanet Archive; the v0.2 record,
[v0.2/eb_snapshot/DATA_LICENSE.md](v0.2/eb_snapshot/DATA_LICENSE.md), covers the
eclipsing-binary catalogs only), and the third-party content of the v0.3 records. These gaps were
found by the inventory of the whole tree ([docs/third-party-data.md](../docs/third-party-data.md))
and are covered by this new record, on the maintainer's decision of 2026-11-06 (#199). They are
not code, and each component keeps its own terms, listed below.

These files have been in the repository since their phases were frozen, and in the releases made
since then (from v0.2.0 on, each archived on Zenodo); they stay in the repository and in later release
archives, each component with its terms here. Sources, with literal excerpts and the date read:
[docs/sources/third-party-data-2026-11-06.md](../docs/sources/third-party-data-2026-11-06.md)
(T1 to T7) and [v0.4/sources/data-licenses-2026-11-01.md](v0.4/sources/data-licenses-2026-11-01.md)
(L5, L7). Nothing here is legal advice.

**There is no single license for these files.** Each component's terms apply to that component
only. This record is an internal rule of this project; it grants no right that the sources do not
grant.

## Components

| Component | Where it appears | Terms | Credit required |
|---|---|---|---|
| The ExoFOP-TESS TOI table | `calibration/pool_snapshot/exofop_toi.csv` (v0.1, retrieved 2026-10-07) and `calibration/v0.2/pool_snapshot/exofop_toi.csv` (v0.2, retrieved 2026-10-09); URL, time and SHA-256 of each in the `retrieval.json` beside it | **Acknowledgment and citation; no formal license stated** (L7, T1). Each file is the whole TOI table of its date, reproduced unchanged; its `Comments` column is text written on ExoFOP by its authors and remains theirs (T1; who writes it: **unconfirmed** by an ExoFOP page, T2). Values that come from journal articles are to be cited through those articles (T1). The maintainer's acceptance of 2026-11-01, extended on 2026-11-06 to the whole TOI table (#199) | ExoFOP's standard acknowledgment, with DOI 10.26134/ExoFOP5 (L7, T1) |
| The NASA Exoplanet Archive's `pscomppars` table: the planet pool | `calibration/pool_snapshot/pscomppars_planet_pool.csv` (v0.1, retrieved 2026-10-07) and `calibration/v0.2/pool_snapshot/pscomppars_planet_pool.csv` (v0.2, retrieved 2026-10-09); query, time and SHA-256 in each `retrieval.json` | **Acknowledgment; no formal license stated on the acknowledgment page** (T3). These queries selected the reference columns (`pl_orbper_reflink`, `pl_tranmid_reflink`, `pl_trandep_reflink`, `pl_trandur_reflink`), so each row carries the literature reference of its period, epoch, depth and duration (T4); the v0.1 and v0.2 targets keep them in `targets.yaml` | the archive's acknowledgment (T3); cite Christiansen et al. (2025), doi:10.3847/PSJ/ade3c2 (T3); the literature reference of each value used |
| The NASA Exoplanet Archive's `pscomppars` table: host TIC numbers | `calibration/pool_snapshot/pscomppars_host_tic_ids.csv` and `calibration/v0.2/pool_snapshot/pscomppars_host_tic_ids.csv` (the distinct TIC numbers of the table's hosts; same `retrieval.json`) | identifiers only; the archive's terms as above (T3) | the archive's acknowledgment (T3) |
| Values quoted from the tables above | `calibration/targets.yaml`, `calibration/selection_log.md`, `calibration/results/`, and the same files of `calibration/v0.2/`; `docs/validation/v0.2.1/reopen/stage-1/real-controls/` | the terms of the table each value comes from (rows above; TIC values: MAST, L5) | as in the rows above |
| arXiv metadata of the papers drawn in v0.3 (identifiers, titles, abstracts, categories) | the walk and draw files of `calibration/v0.3/` | **CC0 1.0**, arXiv's terms for descriptive metadata, which include the abstract (T7) | none required by CC0; the papers are cited by their arXiv identifiers |
| Patches to the code of the papers examined in v0.3 | `calibration/v0.3/main/claims/*/claim/*.patch` | **not reviewed here**: by the maintainer's rule, no v0.3 work is done before 2026-11-18. Each patch modifies code under the license of the repository it patches; the licenses that each v0.3 claim records are in its `claim.yaml` and in `calibration/v0.3/main/sources/`, not re-checked on 2026-11-06 | as each repository's license requires |

## Changes made to third-party data

None. The snapshots are byte copies of the retrievals recorded in each `retrieval.json`. The v0.3
files are described here as they are; their content was not re-examined on 2026-11-06.
