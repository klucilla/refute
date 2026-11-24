# v0.5.8 on Zenodo: the published record

- **The DOI:** [10.5281/zenodo.24485272](https://doi.org/10.5281/zenodo.24485272); the DOI of all
  versions is 10.5281/zenodo.24485271. Record: https://zenodo.org/records/24485272.
- **Who published it, and when:**
  - published by the maintainer on 2026-11-23 local time; Zenodo records the publication date as
    2026-11-24 (UTC);
  - the draft was created on 2026-11-23 by the maintainer's adviser's script below, which never
    publishes;
  - stored here by the maintainer's decision of 2026-11-24 (#218, comment 7122240195).
- **What the record holds** (11 files):
  - the nine v0.5.8 data and script files, byte-identical to `docs/validation/v0.5.8/` at commit
    `bbfdecc6eac3dfbd3e532cf83cbb006d22c136e5`:
    - `stability-records.json`, `stability-ledger.json`, `stability-report.json`,
      `stability-report.md`;
    - `stage0-records.json`, `stage1-set.json`;
    - the scripts `stability_run.py`, `stability_report.py` and `stage0_records.py`;
  - the root `LICENSE` (Apache-2.0, from the same commit), for the scripts;
  - `MANIFEST-sha256.json`, with each file's SHA-256, size, repository path and commit.
  - No TESS light curve or pixel file is in it; they are available from MAST at STScI.
- **The licences** (sourced in
  [docs/sources/zenodo-record-v058-2026-11-24.md](../../../sources/zenodo-record-v058-2026-11-24.md),
  read on 2026-11-24):
  - CC BY 4.0 for Refute's original dataset content (the record's licence field);
  - Apache-2.0 for the bundled scripts;
  - third-party catalogue values keep their sources' terms, with the acknowledgment and citation
    requirements those sources state.
- **The check of 2026-11-24:** Zenodo's public API gives an MD5 for each of the 11 published files;
  all 11 equal the MD5 of the local files that were uploaded.
  - The script: [`../zenodo_check.py`](../zenodo_check.py), SHA-256
    `a6886afedba74cd19fd6ad274acd4162c9a2c99382009bee37f8ed03e2b1d98e`.
  - Its output: [`zenodo-check.json`](zenodo-check.json), `"all_match": true`, 11 files.

The record cites the repository commit and the manifest; this folder and the v0.5.8 README give
the DOI (rule 7 of [docs/data-publication.md](../../../data-publication.md)).

## The files here, stored unchanged

Each file was copied from the maintainer's local package and its SHA-256 checked against the
original before the commit. Git stores them byte for byte (`.gitattributes`, `-text`).

| File | What it is | Source | SHA-256 |
|---|---|---|---|
| [metadata.json](metadata.json) | The record's metadata as uploaded (title, licence, description, related identifiers) | `.cache/v058/zenodo-v2/metadata.json` | `55f60a93327ac139800080e6ceaf56ac3d7c16c5005421795ba8f3d73ed74a4a` |
| [MANIFEST-sha256.json](MANIFEST-sha256.json) | The record's manifest (also one of its 11 files) | `.cache/v058/zenodo-v2/record/MANIFEST-sha256.json` | `e67a27353434f21b1cd6d81c361f974ab3f53e4987766adaf406438640755753` |
| [zenodo-v2-build.py](zenodo-v2-build.py) | The script that built the package after Codex's review | `.cache/v058/zenodo-v2-build.py` | `75bde6a10bc78b7d57a53936306556b42c98acf1b0579d50e799b1ffc9a08f01` |
| [zenodo-v2-draft.py](zenodo-v2-draft.py) | The script that created the draft (it reads a token file only in its own process; it never publishes) | `.cache/v058/zenodo-v2-draft.py` | `5c9ae50fc9c83e8dfcf67d3d87b7f22873be90efcd38b2ca67923a0848e178c7` |
| [draft.json](draft.json) | The draft's id and link | `.cache/v058/zenodo-v2/draft.json` | `840f4403f344bb662be2b1362e148b276c1ec8d1855292929a1b13a78abde532` |
| [zenodo-v2-draft.log](zenodo-v2-draft.log) | The draft script's log: 11 uploads, each checksum checked, the draft unsubmitted | `.cache/v058/zenodo-v2-draft.log` | `3c0f2bebb3952a9145d06dbbc4c3216dfe563f4124421c9de741264d5c75eb79` |
| [codex-review-prompt.md](codex-review-prompt.md) | The prompt of Codex's review of the first package | `.cache/v058/zenodo-review/codex-prompt.md` | `b2f1ed9a2ba31cc9a9a2f2836dc135a788014ef3ba1cfddcb2318c22a2add2df` |
| [codex-review-answer.md](codex-review-answer.md) | Codex's answer: **OVERALL: REFUTED** on the first package (licence field, description, manifest location); the second package applies it | `.cache/v058/zenodo-review/codex-answer.md` | `99db22c510dfd9d3ccf7e2c8a1a39452cc938e2574a9e3cefca25444aca05cfd` |
| [zenodo-check.json](zenodo-check.json) | The MD5 check against Zenodo's public API, 2026-11-24 | written by `../zenodo_check.py` | `84fd946c83e08c751d0c6d159ea814d219d2594ffd11f7258db09fd720a59272` |

**Codex's review:** one round, Codex CLI 0.167.0-alpha.3.2, model gpt-6.2-sol, effort high. It used
817,428 input tokens (732,160 cached) and 10,396 output tokens: **95,664** review tokens.

**Not stored here:** the nine payload files themselves are already in this repository at
`bbfdecc6` (`docs/validation/v0.5.8/`), and the root `LICENSE` is at the repository's root.
