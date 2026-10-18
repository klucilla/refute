# Sources for the issue #33 evaluation (TESS-EB redistribution)

Every source was read on **2026-10-17** (UTC date of the retrieval). Each excerpt is literal
and short; it is stored so that the statement can be checked if the page changes (CLAUDE.md,
rule of issue #34). Nothing here is legal advice.

## S1. Crossref metadata of the article (version of record)

- URL: https://api.crossref.org/works/10.3847/1538-4365/ac324a
- Article: Prša et al. 2022, ApJS 258, 16, doi:10.3847/1538-4365/ac324a.
- Excerpt (JSON, `license`, first entry): `"content-version":"vor"`,
  `"URL":"http:\/\/creativecommons.org\/licenses\/by\/4.0\/"`, start `2022-01-12`.
- Excerpt (`assertion`): "© 2022. The Author(s). Published by the American Astronomical
  Society."; date accepted `2021-10-20`.
- Excerpt (`relation`): `"is-supplemented-by"` the DOI `10.17909/t9-9gm4-fx30`.
- Excerpt (`abstract`): "The catalog is available from http://tessEBs.villanova.edu and from
  MAST."

## S2. The article page (IOPscience)

- URL: https://iopscience.iop.org/article/10.3847/1538-4365/ac324a
- Excerpt: "Original content from this work may be used under the terms of the Creative
  Commons Attribution 4.0 licence."

## S3. AAS journals, licensing

- URL: https://journals.aas.org/article-charges-and-copyright/ (redirected from
  http://journals.aas.org/authors/apc.html#Copyright, the link given by the CDS page, S4)
- Excerpt: "Authors of all AAS Journal articles accepted after 11 October 2021 will retain
  copyright in the published article"
- Excerpt: "all gold OA articles ... are published under a CC-BY 4.0 license"

## S4. CDS, rules of usage of VizieR data

- URL: https://cds.unistra.fr/vizier-org/licences_vizier.html
- Excerpt: "The data retrieved with VizieR are free of usage in a scientific context"
- Excerpt: "The Information system including the metadata is private and reserved to the
  CDS."
- Excerpt: "The copyrights of a catalogue depend on the data origin."
- Excerpt (for J/AJ, J/ApJ, J/ApJS): the AAS page of S3.

## S5. MAST, the DOI of the catalog (high-level science product)

- URL: https://doi.org/10.17909/t9-9gm4-fx30 (resolves to
  https://archive.stsci.edu/doi/resolve/resolve.html?doi=10.17909/t9-9gm4-fx30)
- Excerpt: "TESS Eclipsing Binaries (\"TESS-EBs\")"; date 2022-06-29.
- Excerpt: "The catalog will continue to be updated with new sectors of data as they become
  available."
- Not found on this page: a license statement for the data files (see S6, the product's own
  page, which has one).

## S6. MAST, the product page of TESS-EBs (added after the end-of-stage review)

- URL: https://archive.stsci.edu/hlsp/tess-ebs (read on 2026-10-17)
- Excerpt: "These HLSP data products are licensed for use under CC BY 4.0."
- Excerpt: "The current version on MAST (v1.0) contains about 4580 eclipsing binary stars"
- Excerpt: the catalog file of v1.0 is named
  `hlsp_tess-ebs_tess_lcf-ffi_s0001-s0026_tess_v1.0_cat.csv` (download link of the page); the
  page says the name "will change in future data releases" following a pattern with the
  version.

## S7. The v1.0 file and its readme (downloaded 2026-10-17, about 21:55 UTC-3)

- URL: https://archive.stsci.edu/hlsps/tess-ebs/hlsp_tess-ebs_tess_lcf-ffi_s0001-s0026_tess_v1.0_cat.csv
  (1898138 bytes, SHA-256 `97e81f6c01716a431379ab6bd37d1182b611a485107110e0eba830f817ba7a8f`)
- URL: https://archive.stsci.edu/hlsps/tess-ebs/hlsp_tess-ebs_tess_lcf-ffi_s0001-s0026_tess_v1.0_readme.txt
  (6214 bytes, SHA-256 `79c7731810ed86f169e295733be480f66649cb40e1c435c76ca9c5e4aaf07377`)
- Excerpt (readme): "tess_id: (int) TESS input catalog (TIC) identification number"
- Excerpt (readme): "ra: (float) Right ascension of the target, in decimal degrees (epoch J2000,
  equinox J2000)"
- Excerpt (readme): "period: (float) binary star orbital period (days)"
- Note: the readme gives the v1.0 file name as `hlsp_tess-ebs_tess_lcf_s0001-s0026_tess_v1.0_cat.csv`
  (without `-ffi`); the product page (S6) links the file with `lcf-ffi`, and that is the file
  retrieved and hashed here.
