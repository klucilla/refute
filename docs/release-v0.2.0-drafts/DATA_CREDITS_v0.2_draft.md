> **Drafts for closing v0.2. To be applied on `main` by the release session. Do not apply from this branch.** (Written on branch `claude/v0-2-1-gauntlet-fixes-13f5e7`, 2026-10-10; nothing here changes `calibration/v0.2/` or `main`.)

# Data credits and third-party data: v0.2 calibration dossiers

This file accompanies `refute-v0.2-calibration.zip`. The Apache-2.0 license covers
the code of Refute only. It does **not** apply to any third-party data in this
archive: each source keeps its own terms, described below.

## TESS-EB records in four dossiers

Four dossiers contain one record each of the TESS-EB catalog, in
`verdict.json`, test `eb_catalog`, `metrics.matches` (the catalog entry the test
matched under the target's TIC ID):

| Dossier | Target | TIC | TESS-EB identifier | Period (d) |
|---|---|---|---|---|
| `TIC-158561566` | Kepler-14 b | 158561566 | `TIC 158561566 (1)` | 6.7899645 |
| `TIC-316916655` | TOI-441.01 | 316916655 | `TIC 316916655 (1)` | 2.8747759 |
| `TIC-317507345` | TOI-1615.01 | 317507345 | `TIC 317507345 (1)` | 3.9400619 |
| `TIC-350445771` | TOI-258.01 | 350445771 | `TIC 350445771 (1)` | 3.1904288 |

**Source.** Prša et al. 2022, ApJS 258, 16, doi:10.3847/1538-4365/ac324a; table
J/ApJS/258/16/tess-ebs, obtained through the VizieR catalogue access tool, CDS,
Strasbourg (doi:10.26093/cds/vizier; table doi:10.26093/cds/vizier.22580016).
Snapshot used: the VizieR ASU TSV of that table retrieved 2026-10-09T02:44:20Z,
4584 rows, canonical-content SHA-256
`a31936ce4dc1bfbb27c4e372b145653ef1d97df250df8d1b0fadaa3f0f1b949c`, recorded in
`calibration/v0.2/eb_snapshot/retrieval.json` of the repository.

**Credit.** Cite the paper above and acknowledge VizieR as the CDS requests.

**These records are not licensed under Apache-2.0.** They keep the terms of their
sources.

**The full catalog is still not redistributed** (as a precaution; see below). No
snapshot, table or row of TESS-EB other than the four records above is in this
archive, in the repository or in any release. Runs and reproductions download the table from VizieR and check its
content SHA-256 before any analysis.

**Why these four records appear.** They are localized evidence of the audit: each is
the catalog entry that the `eb_catalog` test of that dossier matched, and the
dossier cannot be changed without breaking its integrity manifest and the lock of
the calibration claim.

## Terms of the sources (checked 2026-10-10)

- **The article.** Prša et al. 2022 is published by the American Astronomical
  Society, © 2022 The Author(s), accepted 2021 October 20, and its original content
  may be used under the Creative Commons Attribution 4.0 licence, keeping attribution
  to the authors, title, journal citation and DOI
  (https://iopscience.iop.org/article/10.3847/1538-4365/ac324a). Crossref records the
  same license for the version of record, from 2022-01-12
  (https://api.crossref.org/works/10.3847/1538-4365/ac324a).
- **The AAS policy.** Authors of AAS Journal articles accepted after 11 October 2021
  retain copyright and grant the AAS a non-exclusive CC BY license. Its section
  "Reproduction of Copyrighted Materials" encourages the reuse of tables in scholarly
  work, states that gold open-access articles are published under CC BY 4.0, which
  sets the requirements for reuse, and requires reproduced material to cite the
  original publication (https://journals.aas.org/article-charges-and-copyright/).
- **The CDS** ("Rules of usage of VizieR data",
  https://cds.unistra.fr/vizier-org/licences_vizier.html): VizieR data are free of
  use in a scientific context, with explicit citation of the original authors, the
  publication references and the publisher; commercial use depends on the origin of
  the data; copyright depends on the origin and the catalogue's ReadMe; for catalogues
  from AAS journals the page refers to the AAS copyright policy, section "Reproduction
  of copyrighted materials", as applying to tables. An acknowledgement of VizieR is
  appreciated.
- **The catalogue record** of J/ApJS/258/16 at the CDS shows no copyright or licence
  statement.

**Withdrawn as unconfirmed.** Text in the repository since commit `16e880d`
(2026-10-08: `calibration/v0.2/eb_snapshot/DATA_LICENSE.md`, `PROTOCOL.md`,
`README.md`) said that this CDS page puts AAS tables "under CC-BY-NC licence" and
links to CC BY-NC-ND. The page as checked on 2026-10-10 says neither, no copy of the
page as of 2026-10-08 was kept, and no source for that statement could be found. It is
not used here.

## The 2026-10-08 decision, its reason, and its scope for v0.2.0

The decision recorded in `calibration/v0.2/eb_snapshot/DATA_LICENSE.md` reads:

> **Decision (maintainer, 2026-10-08): the rows of the TESS-EB catalog (Prsa et al.
> 2022, ApJS 258, 16, doi:10.3847/1538-4365/ac324a) are not redistributed, neither
> in the repository nor in any release.**

Its stated reason was that the terms of the publisher and of the CDS differ. Half of
that reason was the CDS statement withdrawn above; **the conflict is not demonstrated
by the sources checked on 2026-10-10.**

**Decision for v0.2.0 (maintainer, 2026-10-10).**

- The **full catalog is still not redistributed**, now **as a precaution**, with the
  reason rewritten: a conflict between the sources' terms is not demonstrated by the
  sources checked. (Whether to redistribute the snapshot, possibly from the
  publisher's table rather than VizieR, is a separate question for a later version.)
- The **four records** listed above **are published, with citation**, inside the four
  v0.2 calibration dossiers, as localized evidence of the audit. This is an explicit
  update of the decision's scope, not a reading of the original text, which did not
  provide for it.

**Already in the repository before this update.** The same four periods appear in the
independent reviews committed on 2026-10-09 (commit `b4be588`,
`calibration/v0.2/results/20261009T155044Z-c9f341d2/reviews/<target>/opus-1.md`), which
quote the dossiers. No decision covered them at that time; this update covers them.

## If a record must be withheld later

If any of these records must be withheld in the future, the affected targets stay
identified in the archive's index and in the calibration summary (`summary.json`,
`summary.md`), with the restriction explained in this file.

## Other third-party data in this archive

- **Gaia DR3** rows in each dossier's `attachments/eb_catalog.csv`: CC BY-NC 3.0 IGO,
  with credit to ESA/Gaia/DPAC (see `calibration/v0.2/eb_snapshot/DATA_LICENSE.md`
  and the README, "Data and acknowledgments").
- **TESS data products** (MAST) are not in this archive: each dossier lists the files
  it used, with URLs and SHA-256, in `data/manifest.json`. The plots are derived from
  them. Acknowledgements as in the README.
- **NASA Exoplanet Archive**: `attachments/pool_snapshot/retrieval.json` records the
  queries used for the selection (URL, retrieval time, SHA-256), not the extracts
  themselves; the published parameters of each target are in `target.json`.
  Acknowledgements as in the README.
