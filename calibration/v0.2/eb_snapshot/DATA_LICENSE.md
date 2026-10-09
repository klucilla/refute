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

**Decision (maintainer, 2026-10-08): the rows of the TESS-EB catalog (Prsa et al.
2022, ApJS 258, 16, doi:10.3847/1538-4365/ac324a) are not redistributed, neither in
the repository nor in any release.**

**Reason: the license terms differ between the sources.**

- The publisher's metadata (Crossref, version of record) gives the article the
  CC BY 4.0 license (http://creativecommons.org/licenses/by/4.0/), from 2022-01-12.
- The CDS page https://cds.unistra.fr/vizier-org/licences_vizier.html states that
  tabular data from AAS journals (J/ApJ, J/ApJS, J/AJ) are "under CC-BY-NC licence",
  and links to http://creativecommons.org/licenses/by-nc-nd/, which forbids
  derivatives.

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
