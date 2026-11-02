# Sources for the v0.4 data license statements

Every source below was read on **2026-11-01** (UTC date) unless stated otherwise. Each excerpt is
literal and short, so that each statement in [../DATA_LICENSE.md](../DATA_LICENSE.md) and in the
v0.4 exception of [docs/data-publication.md](../../../docs/data-publication.md) can be checked if
the page changes (CLAUDE.md, rule of issue #34). Nothing here is legal advice.

## L1. Gaia data license (ESA)

- URL: https://www.cosmos.esa.int/web/gaia-users/license
- Excerpt: "Gaia data are distributed under the CC BY-NC 3.0 IGO license."

## L2. ESA space science archives, terms and conditions

- URL: https://www.cosmos.esa.int/web/esdc/terms-and-conditions
- Excerpt: "Prior to any commercial use by the User of any Data or Data Product" (a licence request
  is needed first).
- Excerpt (credit line for Gaia): "Credit: ESA, Gaia DPAC".

## L3. CC BY-NC 3.0 IGO, legal code

- URL: https://creativecommons.org/licenses/by-nc/3.0/igo/legalcode.en
- Excerpt (section 3): "the Licensor hereby grants You a worldwide, royalty-free, non-exclusive
  license to exercise the rights in the Work"
- Excerpt (section 4(a)): "You must include a copy of, or the Uniform Resource Identifier (URI)
  for, this License"
- Excerpt (section 4(b), what is excluded): "primarily intended for or directed toward commercial
  advantage or private monetary compensation"
- Excerpt (section 4(c)): "keep intact all copyright notices for the Work"

## L4. TESS-EBs at MAST (high-level science product)

- URL: https://archive.stsci.edu/hlsp/tess-ebs
- Excerpt: "These HLSP data products are licensed for use under CC BY 4.0."
- Excerpt: "Please remember to cite the appropriate paper(s) below and the DOI" (the DOI is
  10.17909/t9-9gm4-fx30).
- Earlier record of the article's license (CC BY 4.0, read 2026-10-17):
  [docs/validation/v0.2.1/reopen/sources/issue-33-sources.md](../../../docs/validation/v0.2.1/reopen/sources/issue-33-sources.md), S1 and S2.

## L5. MAST data use policy

- URL: https://archive.stsci.edu/publishing/data-use
- Excerpt: "Most data hosted at MAST are in the public domain"
- Excerpt (licensed HLSPs): "If a user obtains such data from MAST and subsequently provides the
  data to a third party, the terms of the CC BY 4.0 license convey with the data."

## L6. VizieR (CDS), rules of usage: NOT re-read on 2026-11-01

- URL: https://cds.unistra.fr/vizier-org/licences_vizier.html
- On 2026-11-01 the CDS servers (cds.unistra.fr, vizier.cds.unistra.fr) did not answer
  (connection refused or timed out); the CfA mirror has no copy of this page.
- Last reading, 2026-10-17 ([issue-33-sources.md](../../../docs/validation/v0.2.1/reopen/sources/issue-33-sources.md), S4):
  "The data retrieved with VizieR are free of usage in a scientific context"; "The copyrights of
  a catalogue depend on the data origin."
- The statement about VizieR is therefore **unconfirmed** as of 2026-11-01. The maintainer's
  condition: the page is re-read before anything is published.
- Superseded as a condition on 2026-11-02 by the maintainer's decision recorded in L9: the
  publication rests on the original sources' licenses (L1, L4), the reading of 2026-10-17 and an
  archived capture of 2026-10-25. The live re-read stays open until the CDS is back.

## L7. ExoFOP data use policy

- URL: https://exofop.ipac.caltech.edu/tess/pcp.php (policy updated 27 March 2023)
- No license is stated on the page.
- Excerpt: "Please include the following standard acknowledgment in any published material that
  makes use of ExoFOP services" (DOI 10.26134/ExoFOP5).
- Excerpt: "The use for publication of any data on ExoFOP that have appeared in journals should be
  accompanied by a citation to the respective article(s)."
- Decision (the maintainer, 2026-11-01): the redistribution of the TOI values is accepted on the
  basis of the acknowledgment and citation; no formal license is stated by ExoFOP.

## L8. Zenodo, licenses of a record

- URL: https://help.zenodo.org/docs/deposit/describe-records/licenses/
- Excerpt: "Mixed license uploads"; files "under different licenses" (the page shows a record
  with several licenses, and a custom license with a title, description and link).
- URL: https://inveniordm.docs.cern.ch/reference/metadata/
- Excerpt: "Rights (Licenses) (0-n)"; "It should however also be possible to provide custom
  rights statements."
- Zenodo's license vocabulary, queried through its public API on 2026-11-01
  (`https://zenodo.org/api/vocabularies/licenses/<id>`): `cc-by-4.0` exists; `cc-by-nc-3.0-igo`
  returns 404 ("The persistent identifier does not exist."); a search for "igo" finds only
  `cc-by-nc-nd-3.0-igo`.
- URL: https://developers.zenodo.org/ (scopes)
- Excerpt: "`deposit:write` | Grants write access to depositions, but does not allow publishing
  the upload."

## L9. VizieR (CDS), rules of usage: archived capture of 2026-10-25 (read 2026-11-02)

- The CDS was still unreachable on 2026-11-02 (cds.unistra.fr, vizier.cds.unistra.fr,
  cdsportal.u-strasbg.fr, vizier.u-strasbg.fr and the rules page timed out).
  The page is not served by the mirrors: it returns 404 at vizier.cfa.harvard.edu,
  vizier.idia.ac.za, vizier.nao.ac.jp and vizier.china-vo.org, and the latter two link back to the
  CDS for it.
- Official notice, CDS on Bluesky, 2026-10-28T15:38:15Z:
  https://bsky.app/profile/cdsportal.bsky.social/post/3myx3gzqoak2w
- Excerpt: "CDS is experiencing a cybersecurity incident within its network of servers located in
  Strasbourg." No date for the return is given.
- Archived capture (Wayback Machine), taken 2026-10-25T10:23:48Z, which is before the incident
  notice: http://web.archive.org/web/20261025102348/https://cds.unistra.fr/vizier-org/licences_vizier.html
- Original bytes (`id_` form):
  http://web.archive.org/web/20261025102348id_/https://cds.unistra.fr/vizier-org/licences_vizier.html
- The original bytes were downloaded on 2026-11-02, twice, and both downloads were identical.
  They are 9428 bytes, with SHA-256 `f6bab16f7060f41c98958f0044fa3a526eeeeacdd23cb2fa7a529016d2b29e9f`.
  Their SHA-1, in base32, is `ZJLLUHIVWNVX42YCEWMJNNORNOZWFFY4`, which is the content digest the
  Wayback index gives for this capture.
- Unchanged content: the Wayback index
  (http://web.archive.org/cdx/search/cdx?url=cds.unistra.fr/vizier-org/licences_vizier.html) gives
  that same digest for every capture from 2026-02-10 to 2026-10-25, a span that includes the
  reading of 2026-10-17 (L6).
- Excerpt: "The data retrieved with VizieR are free of usage in a scientific context"
- Excerpt: "The copyrights of a catalogue depend on the data origin."
- The capture's HTML also holds an older statement about tables from AAS journals (CC-BY-NC). It
  sits inside an HTML comment, so the rendered page does not show it. The rendered page points to
  the AAS copyright policy, which was read on 2026-10-17 (issue-33-sources.md, S3).
- Decision (the maintainer, 2026-11-02): the publication of v0.4 rests on the licenses of the
  original sources (TESS-EB, CC BY 4.0 at MAST, L4; Gaia DR3, CC BY-NC 3.0 IGO at ESA, L1), on the
  reading of 2026-10-17 and on this capture. The live re-read of the page stays open until the CDS
  is back. If the page then differs, everything stops and the maintainer is told. Issue #177.
