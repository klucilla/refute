- Raw outputs larger than 5 MB never enter git (decided by the maintainer on 2026-10-24,
  before X2f): they are archived to the Drive with a SHA-256 manifest of source and
  destination, checked; the repository keeps the script that produced them, a summary and
  that manifest. From X2f on they are published for external reproduction on Zenodo, with a
  DOI ([docs/data-publication.md](docs/data-publication.md)): only synthetic data and Refute's
  own results, never data under a restricted license (TESS-EB, Gaia) or anything about a paper
  in its reply period; a license in every record; the agent prepares a **draft** only (files,
  SHA-256 manifest, metadata) and **never publishes a record** (the maintainer publishes).
