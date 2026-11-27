# J5: the GitHub release v0.5.12 and its Zenodo DOI (read only)

The maintainer's decision J5 (#218, comment 7222879969). The maintainer created the release. The
agent created no release and did nothing on Zenodo; it only read.

| Item | Value | How it was read (2026-11-27) |
| --- | --- | --- |
| Release | "Refute 0.5.12", tag `v0.5.12`, published 2026-11-27T16:10:33Z, not a draft, not a prerelease: https://github.com/klucilla/refute/releases/tag/v0.5.12 | `gh api repos/klucilla/refute/releases/tags/v0.5.12` (metered unit gh2) |
| The tag it points to | `refs/tags/v0.5.12` → annotated tag object `6fcaeecb9198ece73ba80785ea94de66761b522b` → commit **`3dbb713c7fa40960d8f7941826e0a9c91a4b1b74`**, the commit published on PyPI (F3) | `gh api .../git/ref/tags/v0.5.12` and `.../git/tags/6fcaeecb…` |
| Zenodo DOI | **10.5281/zenodo.24595367**, as given by the maintainer | https://doi.org/10.5281/zenodo.24595367, read on 2026-11-27. It resolves to https://zenodo.org/records/24595367, titled "Refute: find signals, try to kill them, keep what survives", author Lucilla, Klauber, with citation DOI 10.5281/zenodo.24595367 and version 0.5.12 in its description. |

The release's `target_commitish` reads `main`. That field matters only when a release creates its
tag. Here the tag existed, and it points to `3dbb713c`.

**Not done** (public text, the maintainer's decision): adding this version DOI to `CITATION.cff`.
The file lists the concept DOI and the version DOIs of 0.4.0 and 0.5.0.
