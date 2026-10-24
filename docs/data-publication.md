# Publishing raw outputs (Zenodo)

Decided by the maintainer on 2026-10-24, in force **from X2f on**. Sources of every statement
about Zenodo: [sources/zenodo-2026-10-24.md](sources/zenodo-2026-10-24.md) (read on 2026-10-24).

## The rule

1. **Raw outputs larger than 5 MB never enter git.** They are archived to the maintainer's Drive
   with a SHA-256 manifest of source and destination, checked. The repository keeps the script
   that produced them, a summary and that manifest (CLAUDE.md, "Operating rules").
2. **For external reproduction they are published on Zenodo, with a DOI**, as datasets.
3. **What may go there:** only synthetic data and Refute's own results. **Never** data under a
   restricted license (for example the TESS Eclipsing Binary catalog or Gaia DR3 rows, see
   `calibration/v0.2/eb_snapshot/DATA_LICENSE.md`), and **nothing about a paper whose authors'
   reply period is open**.
4. **A license in every record.** Zenodo requires one for every public file (S2). Proposed, for
   the maintainer's decision: **CC-BY-4.0** for synthetic datasets (Zenodo's default, S5); any
   other content gets its license decided in its own record.
5. **Drafts only.** The agent prepares the files, their SHA-256 manifest and the record's
   metadata (title, description, creators, license, the Refute commit and the repository paths
   of the script, summary and manifest) as a **draft**. **The maintainer publishes; the agent
   never publishes a record.** A published record cannot simply be changed: its files can be
   corrected only within 30 days, and a significant change is a new version.
6. **Limits per record:** at most 50 GB and 100 files (S1, S3); more than 20 files are packed in
   a ZIP archive (S4). A larger set is split across records, each with its own manifest, or a
   higher quota is requested by the maintainer.
7. **The record and the repository point at each other:** the record cites the commit and the
   manifest's path; the repository's summary gives the DOI once the maintainer has published.

## Separate: the archive of each release

The Zenodo–GitHub integration archives **each new release** of an enabled repository
automatically (S6). That is the software's archive, made by Zenodo from a GitHub release; it is
separate from the datasets above, which are deposited one by one as drafts and published by the
maintainer.
