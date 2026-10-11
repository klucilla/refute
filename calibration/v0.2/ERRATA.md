# Errata: v0.2 calibration documents

## E1 (decided 2026-10-10, applied 2026-10-11): TESS-EB license statement withdrawn as unconfirmed

**Affected text.** Added in commit `16e880d` (2026-10-08):

- `calibration/v0.2/PROTOCOL.md`, section "Data credits and licenses", the bullet
  "TESS-EB is not redistributed", sentence beginning "Reason: the terms differ
  between the publisher ... and the CDS ...". `PROTOCOL.md` is a locked attachment of
  the v0.2 calibration claim (role `protocol`, SHA-256
  `f7c246551bd3…` in `self_claim.lock.json`) and is **not edited**: editing it would
  make the claim TAMPERED. This erratum supersedes that sentence.
- `calibration/v0.2/eb_snapshot/DATA_LICENSE.md`, section "TESS-EB: not
  redistributed" (corrected in place, with this erratum cited).
- `README.md`, section "License", the TESS-EB row of the data-terms table (corrected
  in place, with this erratum cited). The section "Data and acknowledgments" did not
  contain the statement.

**Correction (decided 2026-10-10, applied 2026-10-11).** The statement added in
`16e880d` that the CDS places AAS tables under CC-BY-NC with a link to BY-NC-ND is
withdrawn as unconfirmed. The CDS page it cited ("Rules of usage of VizieR data",
https://cds.unistra.fr/vizier-org/licences_vizier.html), checked on 2026-10-10,
contains no Creative Commons licence and no link to BY-NC-ND. No copy of the page as
of 2026-10-08 was kept, and no source for the statement was found.

**Sources checked on 2026-10-10:**

- CDS, https://cds.unistra.fr/vizier-org/licences_vizier.html: VizieR data are free of
  use in a scientific context with explicit citation of the original authors, the
  publication references and the publisher; commercial use depends on the origin of
  the data; for AAS-journal catalogues the page refers to the AAS copyright policy,
  section "Reproduction of copyrighted materials", as applying to tables.
- AAS, https://journals.aas.org/article-charges-and-copyright/: authors of articles
  accepted after 11 October 2021 retain copyright and grant the AAS a non-exclusive
  CC BY license; gold open-access articles are published under CC BY 4.0, which sets
  the requirements for reuse; reproduced material must cite the original publication.
- Article, https://iopscience.iop.org/article/10.3847/1538-4365/ac324a: © 2022 The
  Author(s), published by the AAS, accepted 2021 October 20; original content may be
  used under the Creative Commons Attribution 4.0 licence, with attribution.
- Crossref, https://api.crossref.org/works/10.3847/1538-4365/ac324a: license
  http://creativecommons.org/licenses/by/4.0/ for the version of record, from
  2022-01-12.
- CDS catalogue record of J/ApJS/258/16: no copyright or licence statement.

**Consequence.** The reason given for the 2026-10-08 decision (the terms differ
between the sources) is not demonstrated by the sources checked.

**Decision for v0.2.0 (maintainer, 2026-10-10).** The full TESS-EB catalog is still
not redistributed, now as a precaution: a conflict between the sources' terms is not
demonstrated by the sources checked. The four TESS-EB records contained in four v0.2
calibration dossiers were published with [release
v0.2.0](https://github.com/klucilla/refute/releases/tag/v0.2.0) on 2026-10-11, with
citation (see the data credits of that release). The download-and-hash-check
procedure of runs and reproductions is unchanged.
