> **Drafts for closing v0.2. To be applied on `main` by the release session. Do not apply from this branch.** (Written on branch `claude/v0-2-1-gauntlet-fixes-13f5e7`, 2026-10-10; nothing here changes `calibration/v0.2/` or `main`.)

# Draft correction texts (location decided 2026-10-10: applied on `main` by the session that closes v0.2)

======================================================================
(1) ERRATA FILE for the locked PROTOCOL.md (new file; PROTOCOL.md is a locked
attachment of the v0.2 claim and is NOT edited)
======================================================================

# Errata: v0.2 calibration documents

## E1 (2026-10-10): TESS-EB license statement withdrawn as unconfirmed

**Affected text.** Added in commit `16e880d` (2026-10-08):

- `calibration/v0.2/PROTOCOL.md`, section on data sources and licenses, the bullet
  "TESS-EB is not redistributed", sentence beginning "Reason: the terms differ
  between the publisher ... and the CDS ...". `PROTOCOL.md` is a locked attachment of
  the v0.2 calibration claim (role `protocol`, SHA-256
  `f7c246551bd3…` in `self_claim.lock.json`) and is **not edited**: editing it would
  make the claim TAMPERED. This erratum supersedes that sentence.
- `calibration/v0.2/eb_snapshot/DATA_LICENSE.md`, section "TESS-EB: not
  redistributed" (corrected in place, with this erratum cited).
- `README.md`, "Data and acknowledgments" and the data-terms table (corrected in
  place, with this erratum cited).

**Correction (2026-10-10).** The statement added in `16e880d` that the CDS places AAS
tables under CC-BY-NC with a link to BY-NC-ND is withdrawn as unconfirmed. The CDS
page it cited ("Rules of usage of VizieR data",
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
calibration dossiers are published with citation (see the data credits of release
v0.2.0). The download-and-hash-check procedure of runs and reproductions is
unchanged.

======================================================================
(2) DATA_LICENSE.md: replacement of the section "TESS-EB: not redistributed"
(explicit, not silent: the original reason is kept, struck through)
======================================================================

## TESS-EB: not redistributed

> **Correction (2026-10-10, erratum E1).** The reason originally given below cited a
> CDS statement that could not be confirmed and is withdrawn. The sources checked on
> 2026-10-10 do not demonstrate a conflict between the publisher's and the CDS's
> terms; see erratum E1 for the sources.

**Decision (maintainer, 2026-10-08): the rows of the TESS-EB catalog (Prsa et al.
2022, ApJS 258, 16, doi:10.3847/1538-4365/ac324a) are not redistributed, neither in
the repository nor in any release.**

**Decision for v0.2.0 (maintainer, 2026-10-10).** The full catalog is still not
redistributed, now as a precaution: a conflict between the sources' terms is not
demonstrated by the sources checked. Four TESS-EB records contained in four v0.2
calibration dossiers are published with citation in release v0.2.0, as localized
evidence of the audit; the same four periods had already been quoted in the reviews
committed in `b4be588`.

~~**Reason: the license terms differ between the sources.**~~ *(withdrawn, see the
correction above)*

- The publisher's metadata (Crossref, version of record) gives the article the
  CC BY 4.0 license (http://creativecommons.org/licenses/by/4.0/), from 2022-01-12.
  *(Confirmed on 2026-10-10.)*
- ~~The CDS page https://cds.unistra.fr/vizier-org/licences_vizier.html states that
  tabular data from AAS journals (J/ApJ, J/ApJS, J/AJ) are "under CC-BY-NC licence",
  and links to http://creativecommons.org/licenses/by-nc-nd/, which forbids
  derivatives.~~ *(Withdrawn as unconfirmed, 2026-10-10: the page says neither.)*

(The rest of the section, "What the repository keeps instead" and the procedure, is
unchanged.)

======================================================================
(3) README.md
======================================================================

(3a) Data-terms table, row "TESS-EB catalog (Prsa et al. 2022)", new "Terms" cell:

**not redistributed**, as a precaution (a conflict between the publisher's and the
CDS's terms is not demonstrated by the sources checked on 2026-10-10; an earlier
statement about the CDS terms was withdrawn as unconfirmed, see
[erratum E1](<errata path>)). The repository keeps only the download script, URL,
date and SHA-256, and identifiers in `eb_catalog.csv`; the file is downloaded and its
hash checked on every run. Four records appear, with citation, in the v0.2
calibration dossiers (release v0.2.0).

(3b) Right after the table, a dated note (so the change is not silent):

> **Correction (2026-10-10).** Until this date this table said that the CDS gives
> TESS-EB CC BY-NC terms with a link to BY-NC-ND. That statement, added in `16e880d`,
> could not be confirmed and is withdrawn; see [erratum E1](<errata path>).
