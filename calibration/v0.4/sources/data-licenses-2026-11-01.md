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
