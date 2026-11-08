# Third-party data in this repository: an inventory

The Zenodo archive of each release is the whole repository. This inventory lists every
third-party data file in the tree, in all phases, and the record that states its terms. It was
made on 2026-11-06 (the maintainer's decision of 2026-11-06, #199): every file tracked at commit
`4016fd9`, except Python source, was scanned by content (third-party host names and catalog
column names in its first 256 KiB), not by extension, and each candidate was then checked by
hand. The files added on 2026-11-06 with this inventory (the two `inputs-references/` records
and the DATA_LICENSE records) are listed as well.
Sources of the terms: the records linked from each DATA_LICENSE, and
[sources/third-party-data-2026-11-06.md](sources/third-party-data-2026-11-06.md) (T1 to T7).
Nothing here is legal advice.

**There is no single license for the repository's data.** The code is licensed under Apache-2.0;
each data component keeps its own terms, stated in the record named below.

## The records

| Record | Covers |
|---|---|
| [calibration/DATA_LICENSE.md](../calibration/DATA_LICENSE.md) (2026-11-06) | content no phase record covered: the v0.1 and v0.2 pool snapshots (ExoFOP TOI table, NASA Exoplanet Archive `pscomppars`) and the values quoted from them; the arXiv metadata and the code patches of v0.3 |
| [calibration/v0.2/eb_snapshot/DATA_LICENSE.md](../calibration/v0.2/eb_snapshot/DATA_LICENSE.md) (2026-10-08, with corrections) | the eclipsing-binary catalogs of v0.2: Gaia DR3 rows, the TESS-EB references and the record of the TESS-EB search |
| [calibration/v0.4/DATA_LICENSE.md](../calibration/v0.4/DATA_LICENSE.md) (2026-11-01, published) | the v0.4 pilot's dossiers and its two reproduction archives (on Zenodo) |
| [calibration/v0.4/DATA_LICENSE-addendum-2026-11-06.md](../calibration/v0.4/DATA_LICENSE-addendum-2026-11-06.md) | the v0.4 files kept in the repository: frozen inputs, the catalog attachment, the references of the known-planet control's values and the values quoted from them |
| [calibration/v0.5/DATA_LICENSE.md](../calibration/v0.5/DATA_LICENSE.md) (2026-11-05/06) | the v0.5 frozen inputs, the catalog attachment, the references of the C3 planets' values and the values quoted from them |
| [docs/validation/v0.5.2/stage2/DATA_LICENSE.md](validation/v0.5.2/stage2/DATA_LICENSE.md) (2026-11-08) | the T10K download of v0.5.2: hashes and counts only, its terms unconfirmed |

## Third-party data files

| File | Content and origin | Retrieved | Record |
|---|---|---|---|
| `calibration/pool_snapshot/exofop_toi.csv` | ExoFOP-TESS TOI table, whole | 2026-10-07 | calibration/DATA_LICENSE.md |
| `calibration/pool_snapshot/pscomppars_planet_pool.csv` | NASA Exoplanet Archive `pscomppars`, a filtered query with reference columns | 2026-10-07 | calibration/DATA_LICENSE.md |
| `calibration/pool_snapshot/pscomppars_host_tic_ids.csv` | NASA Exoplanet Archive `pscomppars`, host TIC numbers only | 2026-10-07 | calibration/DATA_LICENSE.md |
| `calibration/v0.2/pool_snapshot/exofop_toi.csv` | ExoFOP-TESS TOI table, whole | 2026-10-09 | calibration/DATA_LICENSE.md |
| `calibration/v0.2/pool_snapshot/pscomppars_planet_pool.csv` | as the v0.1 pool, re-retrieved | 2026-10-09 | calibration/DATA_LICENSE.md |
| `calibration/v0.2/pool_snapshot/pscomppars_host_tic_ids.csv` | as the v0.1 list, re-retrieved | 2026-10-09 | calibration/DATA_LICENSE.md |
| `calibration/v0.2/eb_catalog.csv` | 1 Gaia DR3 row; 4 TESS-EB references (TIC numbers only) | written by the v0.2 selection | v0.2/eb_snapshot/DATA_LICENSE.md |
| `calibration/v0.2/audit/tess-eb-search/` | the record of the search for TESS-EB values (the values it matched) | 2026-10-11 | v0.2/eb_snapshot/DATA_LICENSE.md ("Search record") |
| `calibration/v0.4/inputs/toi.csv` | ExoFOP-TESS TOI table, whole | 2026-10-29 | v0.4 addendum |
| `calibration/v0.4/inputs/ctoi.csv` | ExoFOP-TESS community candidate table (CTOI), whole | 2026-10-29 | v0.4 addendum |
| `calibration/v0.4/inputs/pscomppars.csv` | NASA Exoplanet Archive `pscomppars` (13 columns, no reference columns) | 2026-10-29 | v0.4 addendum |
| `calibration/v0.4/inputs/target_lists.html` | TESS target lists page (MIT), a copy | 2026-10-29 | v0.4 addendum |
| `calibration/v0.4/inputs-references/pscomppars-references.csv` | NASA Exoplanet Archive `pscomppars`: the known-planet control's used values with their reference columns | 2026-11-06 | v0.4 addendum |
| `calibration/v0.4/eb_catalog.csv` | 4 Gaia DR3 rows; 1 TESS-EB reference (TIC number only) | written by the v0.4 selection | v0.4 addendum |
| `calibration/v0.5/inputs/toi.csv` | ExoFOP-TESS TOI table, whole | 2026-11-04 | v0.5 DATA_LICENSE |
| `calibration/v0.5/inputs/pscomppars.csv` | NASA Exoplanet Archive `pscomppars` (byte-identical to the v0.4 copy) | 2026-11-04 | v0.5 DATA_LICENSE |
| `calibration/v0.5/inputs/target_lists.html` | TESS target lists page (MIT), a copy | 2026-11-04 | v0.5 DATA_LICENSE |
| `calibration/v0.5/inputs-references/pscomppars-references.csv` | NASA Exoplanet Archive `pscomppars`: the 11 C3 planets' used values with their reference columns | 2026-11-06 | v0.5 DATA_LICENSE |
| `calibration/v0.5/eb_catalog.csv` | 3 Gaia DR3 rows; 14 TESS-EB references (TIC numbers only) | written by the v0.5 selection | v0.5 DATA_LICENSE |

## Files that quote third-party values

Refute's own records repeat values taken from the tables above, for example a target's published
period, a TOI disposition or a TIC stellar radius, and catalog matches. Each value keeps the terms
of the table it comes from, as the record of its phase states:

| Where | Record |
|---|---|
| `calibration/targets.yaml`, `selection_log.md`, `results/`, and the same files of `calibration/v0.2/`; `docs/validation/v0.2.1/reopen/stage-1/real-controls/` | calibration/DATA_LICENSE.md |
| `calibration/v0.2/` reviews and dossier records that quote the four TESS-EB periods | v0.2/eb_snapshot/DATA_LICENSE.md |
| `calibration/v0.4/selection/`, `claim.yaml`, `inputs.json`, `runs/`, `results/` | v0.4 addendum |
| `calibration/v0.5/selection/`, `claim-targets.yaml`, `runs/`, `reviews/`, `gate/`, `results/` | v0.5 DATA_LICENSE |

Numbers and plots that Refute derives from TESS light curves and pixel files (MAST) appear in the
run records of every phase; no raw MAST file is in the repository. MAST: "Most data hosted at MAST
are in the public domain" (v0.4 record L5); acknowledge the TESS mission and MAST.

## Other third-party content (not data tables)

| Where | Content | Terms | Record |
|---|---|---|---|
| `calibration/v0.3/` (walk and draw files) | arXiv metadata of the papers drawn (identifiers, titles, abstracts, categories) | CC0 1.0, arXiv's terms for descriptive metadata (T7) | calibration/DATA_LICENSE.md |
| `calibration/v0.3/main/claims/*/claim/*.patch` | small patches to the code of the papers examined in v0.3 | **not reviewed**: by the maintainer's rule, no v0.3 work is done before 2026-11-18 | calibration/DATA_LICENSE.md |
| `sources/` records (`docs/sources/`, `calibration/*/sources/`) | short literal excerpts of the pages cited | quotations, kept to check each statement (#34) | the record that cites them |
| `uv.lock`, the `requirements.lock` files of v0.3 | names, versions and hashes of software packages | identifiers of the packages; each package has its own license | none needed (no data) |

## Kept out of the repository

These third-party data are used by Refute but are **not** in the repository or its release
archives: the TESS-EB table (downloaded from VizieR and checked by its content SHA-256 on every
run, #33); the Gaia DR3 snapshot (a release asset of v0.2.0, under CC BY-NC 3.0 IGO); the
TESS Ten Thousand Catalog of v0.5.2 (Tables 3 and 4 of the article, internal use, terms
unconfirmed; only TIC identifiers may enter a record); the
per-sector TESS target lists and the v0.4 sampling frame built from them; and every MAST light
curve and pixel file. Their URLs and SHA-256 are recorded in the `inputs.json` or
`retrieval.json` of each phase.
