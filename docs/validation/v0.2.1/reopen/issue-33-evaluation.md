# Issue #33: can the TESS-EB snapshot be redistributed? (evaluation, 2026-10-17)

Status: **evaluation for the maintainer's decision.** It changes no file of the v0.2
calibration, no lock and no retrieval procedure. Sources, with URL, date and literal
excerpts: [`sources/issue-33-sources.md`](sources/issue-33-sources.md) (S1 to S6; S6 and the
corrections marked below were added after the end-of-stage Codex review of 2026-10-17). Nothing
here is legal advice.

## The question

The v0.2 calibration does not redistribute the TESS-EB catalog (Prša et al. 2022, ApJS 258,
16): every run downloads it from VizieR (table `J/ApJS/258/16/tess-ebs`) and checks its
content SHA-256 (`calibration/v0.2/eb_snapshot/DATA_LICENSE.md`). The original reason was
withdrawn (erratum E1); the decision for v0.2.0 kept it as a precaution. Issue #33 asks
whether a snapshot can be redistributed, from VizieR or from another source.

## What the sources say

1. **The article is CC BY 4.0.** Crossref gives the version of record the CC BY 4.0 license
   from 2022-01-12 (S1), and the article page says its original content may be used under
   CC BY 4.0 (S2). It was accepted on 2021-10-20 (S1), after the date from which AAS authors
   keep the copyright and grant a CC BY license (S3).
2. **VizieR adds its own terms.** The CDS says the data are free of usage in a scientific
   context, that the copyright of a catalogue depends on the data origin (for AAS journals,
   the AAS page of S3), and that its information system, including the metadata, is private
   and reserved to the CDS (S4). A file downloaded from VizieR can therefore carry CDS
   metadata (column descriptions, the ReadMe) whose redistribution those terms do not grant.
3. **The catalog has other homes.** The abstract points to tessEBs.villanova.edu and MAST
   (S1), and MAST holds it as a high-level science product with the DOI
   10.17909/t9-9gm4-fx30, which Crossref records as a supplement of the article (S1, S5).
   *(Corrected after the end-of-stage review.)* The product page of MAST states that its data
   products are licensed under **CC BY 4.0**, and it serves a versioned file, v1.0
   (`hlsp_tess-ebs_tess_lcf-ffi_s0001-s0026_tess_v1.0_cat.csv`), whose name changes with
   each future release (S6). The narrower DOI page (S5) shows no license; the product page
   does. MAST says the catalog will continue to be updated (S5, S6): a later release is a new
   file, so a snapshot must name its version and its SHA-256.
4. **Not checked:** whether the article itself carries a machine-readable table of the
   catalog (the page read did not show one); the terms of tessEBs.villanova.edu; whether the
   VizieR table `J/ApJS/258/16/tess-ebs` used by v0.2 has the same rows and values as MAST
   v1.0; and from which file VizieR built its table (so this evaluation does not say that the
   VizieR values come from the CC BY article).

## Options

| Option | What it means | Open points |
|---|---|---|
| A. Keep as in v0.2 | download from VizieR on every run and check the SHA-256; redistribute only identifiers in the claim's files, as v0.2 did (the four matched records published in the v0.2 dossiers and the values of the published search record stay as they are, `calibration/v0.2/eb_snapshot/DATA_LICENSE.md`) | none new; reproduction depends on VizieR staying online with the same content |
| B. Redistribute only the rows a calibration uses | the few rows matched to the targets, with citation | whether those rows, taken from a VizieR file, carry CDS metadata; their provenance from the article is not shown (point 4) |
| C. Take the table from MAST v1.0 and redistribute it | the v1.0 CSV of S6, under CC BY 4.0 with attribution, pinned by its file name and SHA-256, with a new retrieval and hash procedure for the claim's attachment | the attribution text; whether v1.0 matches what the gauntlet expects (columns, the TIC key, the period); the change of source changes the v0.2.1 claim's attachments, so it is decided before the protocol |

## Recommendation

For the v0.2.1 calibration, the choice is between **A** (no change, no new statement) and
**C** (MAST v1.0 under CC BY 4.0, now sourced in S6, which would let the snapshot be
redistributed and the dossiers be reproduced without VizieR). C needs a small plan of its
own (retrieval, hash, attribution, a check that the gauntlet reads it as it reads the VizieR
table) and has to be decided **before** the v0.2.1 protocol, because it changes the claim's
attachments and their hashes. The v0.2 lock and its files do not change in either option.

Decision: the maintainer's (a license statement and public files). Until then, nothing
changes.
