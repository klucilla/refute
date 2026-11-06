# Sources for the v0.5 data license statements

Every page below was read by the agent on **2026-11-05** (UTC date; live fetch through
Firecrawl, HTTP 200) unless stated otherwise. Each excerpt is literal and short, so that each
statement in [../DATA_LICENSE.md](../DATA_LICENSE.md) and in the v0.5 exception of
[docs/data-publication.md](../../../docs/data-publication.md) can be checked if the page changes
(CLAUDE.md, the rule of issue #34). Nothing here is legal advice. The v0.4 record of the same
sources, read on 2026-11-01 and 2026-11-02, is
[calibration/v0.4/sources/data-licenses-2026-11-01.md](../../v0.4/sources/data-licenses-2026-11-01.md).

## D1. Gaia data license (ESA)

- URL: https://www.cosmos.esa.int/web/gaia-users/license
- Excerpt: "Gaia data are distributed under the CC BY-NC 3.0 IGO license."

## D2. ESA space science archives (ESDC), terms and conditions

- URL: https://www.cosmos.esa.int/web/esdc/terms-and-conditions
- Excerpt: "Data hosted in the ESA Space Science Archives are distributed under the CC BY-NC 3.0
  IGO licence."
- Excerpt: "Prior to any commercial use by the User of any Data or Data Product" (a request for
  authorisation or licence is needed first).
- Excerpt (credit line, Gaia, all instruments): "Credit: ESA, Gaia DPAC".

## D3. CC BY-NC 3.0 IGO, legal code

- URL: https://creativecommons.org/licenses/by-nc/3.0/igo/legalcode.en
- Excerpt (section 3): "the Licensor hereby grants You a worldwide, royalty-free, non-exclusive
  license to exercise the rights in the Work"
- Excerpt (section 4(a)): "You must include a copy of, or the Uniform Resource Identifier (URI)
  for, this License"
- Excerpt (section 4(b)): "primarily intended for or directed toward commercial advantage or
  private monetary compensation" (the use that is not granted).
- Excerpt (section 4(c)): "keep intact all copyright notices for the Work"

## D4. ExoFOP data use and professional conduct policy

- URL: https://exofop.ipac.caltech.edu/tess/pcp.php ("Updated: 27 March 2023", as on 2026-11-01)
- No license is stated on the page.
- Excerpt: "Please include the following standard acknowledgment in any published material that
  makes use of ExoFOP services" (the acknowledgment cites DOI 10.26134/ExoFOP5).
- Excerpt: "The use for publication of any data on ExoFOP that have appeared in journals should be
  accompanied by a citation to the respective article(s)."

## D5. NASA Exoplanet Archive, acknowledging the archive

- URL: https://exoplanetarchive.ipac.caltech.edu/docs/acknowledge.html ("Last updated: 13 August
  2025")
- No license is stated on the page.
- Excerpt: "This research has made use of the NASA Exoplanet Archive, which is operated by the
  California Institute of Technology, under contract with the National Aeronautics and Space
  Administration under the Exoplanet Exploration Program."
- Excerpt: "if you use data from a specific literature reference, please acknowledge that
  reference directly."
- The page asks to cite Christiansen et al. (2025), *Planetary Science Journal*
  (https://iopscience.iop.org/article/10.3847/PSJ/ade3c2), and gives the archive service's DOI
  10.26133/NEA45.
- **Unconfirmed:** whether the archive states a formal license elsewhere; the agent did not find
  one on this page and did not search further.

## D6. MAST data use policy

- URL: https://archive.stsci.edu/publishing/data-use
- Excerpt: "Most data hosted at MAST are in the public domain"
- Excerpt (licensed HLSPs): "If a user obtains such data from MAST and subsequently provides the
  data to a third party, the terms of the CC BY 4.0 license convey with the data."

## D8. TESS target lists page (MIT): **terms unconfirmed**

- URL: https://tess.mit.edu/public/target_lists/target_lists.html (a copy is the frozen input
  `calibration/v0.5/inputs/target_lists.html`, retrieved 2026-11-04T13:07:18Z, which fixed S_max)
- Read on 2026-11-05: no copyright notice, license or terms of use is shown on the page (the
  committed copy holds none of the words "copyright", "license" or "terms" either). Whether the
  TESS Science Office or MIT states terms elsewhere is **unconfirmed**.

## D7. VizieR (CDS), rules of usage: **unconfirmed as of 2026-11-05**

- URL: https://cds.unistra.fr/vizier-org/licences_vizier.html
- Not re-read: the CDS servers did not answer on 2026-11-05 (the cybersecurity incident announced
  by the CDS on 2026-10-28; [cds-incident-2026-11-05.md](cds-incident-2026-11-05.md)).
- Last reading, recorded in v0.4 (L9 of the v0.4 record: an archived capture of 2026-10-25, read
  2026-11-02, the same content as the live reading of 2026-10-17): "The data retrieved with VizieR
  are free of usage in a scientific context"; "The copyrights of a catalogue depend on the data
  origin."
- In v0.5 no TESS-EB value retrieved through VizieR is in the repository: `eb_catalog.csv` holds
  TESS-EB references only (catalog name and TIC number), and the table itself stays in `.cache`
  (#33). VizieR's terms matter here only for the retrieval itself.
