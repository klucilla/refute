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
4. **A license in every record.** Zenodo requires one for every public file (S2). **Synthetic
   datasets: CC-BY-4.0** (Zenodo's default, S5; approved by the maintainer on 2026-10-24); any
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

## The drafts are made through Zenodo's API (decided on 2026-10-24)

The agent creates each draft and uploads its files and metadata with Zenodo's deposit API,
using a personal token of the maintainer with the scope `deposit:write` only (no
`deposit:actions`, so the token cannot publish; no `user:email`).

- **Where it is:** a local file of the maintainer, outside the repository.
- **How it is used:** read from that file only inside the Python process that makes the call to
  Zenodo's API, at the moment of the call, and passed only in the authorization header. It is
  never printed, logged, written to another file, copied into the repository or `.cache/`,
  given as a command-line argument (visible in the process list) or kept in a persistent
  environment variable. The agent never changes, moves or deletes that file.
- **Before the first real use:** the agent confirms only that the file exists and that its
  line holds a value, showing the token's length, never its value.
- **Publishing:** never by the agent (the token does not allow it); the maintainer publishes
  each record from Zenodo's web page.
- **Revoking:** the maintainer revokes the token on Zenodo's **Applications** page (account
  settings, personal access tokens); a new token, if any, follows the same rules.

## Separate: the archive of each release

The Zenodo–GitHub integration archives **each new release** of an enabled repository
automatically (S6). That is the software's archive, made by Zenodo from a GitHub release; it is
separate from the datasets above, which are deposited one by one as drafts and published by the
maintainer.

**The integration is active for this repository:** release v0.2.0 was archived, with version
DOI `10.5281/zenodo.23301001` and concept DOI `10.5281/zenodo.23301000` (issue #53). **Before
the next release**, the `.zenodo.json` of #53 must be on `main`: when present it replaces the
metadata Zenodo takes from `CITATION.cff`, so that each release's record carries the data terms
of each component.
