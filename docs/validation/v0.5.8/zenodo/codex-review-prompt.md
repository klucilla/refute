You are Codex, the project's second agent for verdict and validation, in a read-only sandbox. Repository: C:\Projetos\refute at main 4a704f0f. Do not write, edit, commit or contact the network. Never open K:\Meu Drive\Pessoal\Segurança. Read any file under C:\Projetos\refute.

## Task
One review round before a Zenodo DRAFT is created (the maintainer publishes, never the agent). The package is C:\Projetos\refute\.cache\v058\zenodo\ (metadata.json and record\ with 10 files and MANIFEST-sha256.json), built from docs/validation/v0.5.8 at commit bbfdecc6. Rules: docs/data-publication.md, docs/third-party-data.md, CLAUDE.md (license statements need a sources/ record; never invent facts).

Decide, with path:line evidence:
1. LICENSE for this record: CC-BY-4.0 (proposed in metadata.json) or CC0-1.0, or another. The records hold Refute's own outputs but also third-party values (TOI identifiers, ephemerides, TFOPWG dispositions from ExoFOP, NASA Exoplanet Archive values). Check what those files actually contain, what the repository's existing DATA_LICENSE records and sources/ say about ExoFOP and NASA Exoplanet Archive terms, and whether the description must state that third-party values keep their own terms. Recommend one license and the exact wording of any terms sentence.
2. DESCRIPTION: the metadata predates the v0.5.8 gate's important finding (#219, docs/reports/v0.5.8-report-correction-2026-11-23.md) and a second correction now being written (docs/reports/v0.5.8-report.md:105 says 12 of 15 SNR changes were lower; the records give 13 lower, 2 higher). Proposed added sentence: "The rerun compares v0.5.6's search mode with the TOI-seeded mode, so a change is not attributable to the seed alone; see the dated corrections in the repository." Is it accurate and sufficient? Does any file inside the package (e.g. stability-report.md, stability-report.json) repeat the "12" or the "seed alone" reading? If so, say whether the package can still be published as bytes identical to bbfdecc6 with the description pointing to the corrections, or must change.
3. COMPLIANCE: does the package meet docs/data-publication.md (only Refute's own results or permitted content, no restricted-license data, nothing about a paper in its reply period, a license, record and repository pointing at each other, manifest)? Do the manifest SHA-256 values match the files and the files match bbfdecc6 (git show bbfdecc6:<path>)? Is anything missing (e.g. the related identifier to the corrections, the report, the stability note)?
4. Any metadata error (title, creators, keywords, related identifiers, upload type).

## Answer format (English, concise, at most ~80 lines)
- OVERALL: SURVIVED / WEAKENED / REFUTED (for publishing this draft as is).
- Decisions: license (with exact terms sentence), description (exact final text).
- BLOCKING and NON-BLOCKING items, each with evidence.
