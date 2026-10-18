# Issue #33: can the TESS-EB snapshot be redistributed? (evaluation, 2026-10-17)

Status: **evaluation for the maintainer's decision.** It changes no file of the v0.2
calibration, no lock and no retrieval procedure. Sources, with URL, date and literal
excerpts: [`sources/issue-33-sources.md`](sources/issue-33-sources.md) (S1 to S5). Nothing
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
   MAST says the catalog will continue to be updated (S5), so it is not a fixed snapshot of
   the article's table. **No license statement was found on the MAST DOI page (S5):
   unconfirmed.**
4. **Not checked:** whether the article itself carries a machine-readable table of the
   catalog (the page read did not show one), and the terms of tessEBs.villanova.edu.

## Options

| Option | What it means | Open points |
|---|---|---|
| A. Keep as in v0.2 | download from VizieR on every run, check the SHA-256, redistribute nothing but the identifiers | none new; reproduction depends on VizieR staying online with the same content |
| B. Redistribute only the rows a calibration uses | the few rows matched to the targets, with citation, as the four rows already published in the v0.2 dossiers | whether those rows from a VizieR file carry CDS metadata (the values themselves come from the CC BY article) |
| C. Take the table from a CC BY source and redistribute it | a snapshot from the article's own data (if it exists) or from MAST, with a new retrieval and hash procedure | the license of the MAST product is unconfirmed; MAST's catalog is updated, so its version must be pinned; the article's machine-readable table was not found |

## Recommendation

For the v0.2.1 calibration: **option A**, unchanged. It needs no new license statement,
keeps the v0.2 procedure that the dossiers already describe, and leaves the question open
without blocking anything. Option C becomes possible if a CC BY statement for a fixed file
is found and stored as a source; it would have to be decided **before** the v0.2.1 protocol,
because it changes the claim's attachments and their hashes. The v0.2 lock and its files do
not change in any option.

Decision: the maintainer's (a license statement and public files). Until then, nothing
changes.
