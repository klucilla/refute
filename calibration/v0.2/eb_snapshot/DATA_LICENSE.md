# Data license of the eclipsing-binary snapshots

The code of Refute is licensed under Apache-2.0. The catalog data used by the v0.2
`eb_catalog` test are not code and keep the terms of their sources. Checked on
2026-10-08.

## Gaia DR3: redistributed under its own license

`gaiadr3.vari_eclipsing_binary` with `gaiadr3.gaia_source` coordinates is distributed
under **CC BY-NC 3.0 IGO** (https://creativecommons.org/licenses/by-nc/3.0/igo/), as
stated at https://www.cosmos.esa.int/web/gaia-users/license: non-commercial use, with
credit to ESA/Gaia/DPAC. Acknowledgement and citations: README, "Data and
acknowledgments".

| File | Content |
|---|---|
| `calibration/v0.2/eb_catalog.csv` (written by the v0.2 selection) | its Gaia DR3 rows near the selected targets |
| `gaia_dr3_vari_eclipsing_binary.csv` (release asset, not in git) | the Gaia DR3 snapshot (source_id, ra, dec, frequency) |

These files are under CC BY-NC 3.0 IGO, not Apache-2.0.

## TESS-EB: not redistributed

> **Correction (decided 2026-10-10, applied 2026-10-11; erratum E1).** The reason
> originally given below cited a CDS statement that could not be confirmed and is
> withdrawn. The sources checked on 2026-10-10 do not demonstrate a conflict between
> the publisher's and the CDS's terms; see erratum E1 for the sources.

**Decision (maintainer, 2026-10-08): the rows of the TESS-EB catalog (Prsa et al.
2022, ApJS 258, 16, doi:10.3847/1538-4365/ac324a) are not redistributed, neither in
the repository nor in any release.**

**Decision for v0.2.0 (maintainer, 2026-10-10).** The full catalog is still not
redistributed, now as a precaution: a conflict between the sources' terms is not
demonstrated by the sources checked. Four TESS-EB records contained in four v0.2
calibration dossiers will be published with release v0.2.0, with citation, as
localized evidence of the audit; the same four periods had already been quoted in the
reviews committed in `b4be588`.

**Search record (decided 2026-10-11).** The record of the search for TESS-EB values,
published in `calibration/v0.2/audit/tess-eb-search/`, shows the values the search
matched: the periods of the four records above; the position of TIC 158561566 (from
the TESS Input Catalog via MAST, equal to its TESS-EB position); and the TESS-EB
periods of TIC 71612483, 24450633 and 399729481, which coincide with values in the
ExoFOP-TESS pool snapshots. They are published as evidence of the check, with the
citation above. Nothing else from TESS-EB is in that folder.

~~**Reason: the license terms differ between the sources.**~~ *(withdrawn, see the
correction above)*

- The publisher's metadata (Crossref, version of record) gives the article the
  CC BY 4.0 license (http://creativecommons.org/licenses/by/4.0/), from 2022-01-12.
  *(Confirmed on 2026-10-10.)*
- ~~The CDS page https://cds.unistra.fr/vizier-org/licences_vizier.html states that
  tabular data from AAS journals (J/ApJ, J/ApJS, J/AJ) are "under CC-BY-NC licence",
  and links to http://creativecommons.org/licenses/by-nc-nd/, which forbids
  derivatives.~~ *(Withdrawn as unconfirmed, decided 2026-10-10, applied 2026-10-11:
  the page says neither.)*

What the repository keeps instead:

- the download script (`calibration/v0.2/snapshot_eb_catalogs.py`), the source URL
  (VizieR, table J/ApJS/258/16/tess-ebs), the retrieval time and the SHA-256 of the
  raw file and of its canonical content, in `eb_snapshot/retrieval.json`. The raw file
  stays in `.cache/eb_snapshot_v02/`, which git ignores;
- in `calibration/v0.2/eb_catalog.csv`, TESS-EB entries only as reference rows:
  catalog name and identifier (`TIC <tic> (<m_TIC>)`), with no coordinates and no
  period;
- in `calibration/v0.2/eb_catalog_scan.json`, the identifiers' counts per target and
  the snapshot's URL and content SHA-256, no catalog values.

On every run (and reproduction) the file is downloaded from VizieR if it is not in
the cache, and its content SHA-256 is checked before any analysis; if it does not
match, the run stops. The reference rows are then resolved locally from that
verified copy. The claim and its lock cover `eb_catalog.csv` and
`eb_catalog_scan.json`, hence the recorded hash. Cite the paper and acknowledge
VizieR as the CDS requests (README).
