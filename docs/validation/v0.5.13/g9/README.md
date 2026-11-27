# G9: the sweep of recorded SHA-256 against the HEAD blobs (read only), and a proposal

The maintainer's decision G9 (#218, comment 7219469262). Labels: `exploratory`,
`method_status: not_validated`. **Nothing is corrected here.**

## The sweep

The committed unit `hash-sweep` (`docs/validation/v0.5.13/tools/hash_sweep.py`) ran at HEAD
`3dbb713c7fa40960d8f7941826e0a9c91a4b1b74` and wrote [hash-sweep.json](hash-sweep.json): the full
list, each entry with the recording file, where the hash is recorded, the file and both values.

| Count | Value |
| --- | --- |
| Files scanned (`docs/validation/v0.5.13/`, `docs/plans/v0.5.13-*`, packages included) | 181 |
| Recorded SHA-256 paired with a tracked file | 268 |
| Equal to the HEAD blob | 146 |
| **Divergent** | **122** |
| Hashes not paired (several or no paths in their context), not compared | 1,544 |

**The divergences, by kind** (the tool's classification):
- **`crlf-of-head`: 12.** The recorded value is the SHA-256 of the HEAD blob with LF turned into
  CRLF. All 12 are in the journal (`log.jsonl`).
  - **11 are records that a tool wrote in text mode on Windows (CRLF).** The launcher copied them
    into the repository and recorded the hash of those CRLF bytes; git stores them as LF
    (`eol=lf`). The records:
    - `d4/check-m45-files.json`;
    - `d4/check-m45-uvlock.json`;
    - `d5/testpypi-fetch.json`;
    - `e5/testpypi-fetch.json`;
    - `f2/check-f2.json`;
    - `g1/g1-prepare.json`;
    - `g2/g2-normalize.json`;
    - `g7/check-f2-g7.json`;
    - `step0/demo-check.json`;
    - `step1/comparison-nr-a1.json`;
    - `step1/diag-golden-diff.json`.
  - **1 is `src/refute/packs/tess/a0.py`,** hashed while its working copy had CRLF (before G8).
- **`earlier-version`: 34.** The recorded value is an earlier committed version of a file that has
  changed since: the ledger, the exceptions, the errata, ROADMAP, `.zenodo.json`, `pyproject.toml`
  and a tool. These are expected for records made at the time.
- **`no-match`: 76.** Counted by file from [hash-sweep.json](hash-sweep.json):
  - **40:** a claim's resolved canonical hash, in the four `claim-hashes-*.json` records (10 claims
    each), paired with its claim file. That hash is of the canonical JSON, not of the file bytes,
    so the pairing is false.
  - **21:** the journal's own hash, recorded in the journal at a moment when it held only part of
    its lines (it is append-only).
  - **8:** journal entries for tool versions hashed before their commit, when they were run as
    arguments of a lint unit:
    - `check_f2.py`;
    - `compare_identity.py`;
    - `diag_golden_diff.py` (2);
    - `g2_normalize.py`;
    - `g7_prepare.py`;
    - `make_patch.py`;
    - `rev_diff.py`.
  - **3:** `tests/test_pypi_readme.py` as copied in G1 and G7 (`b9b2793c…`, in `g1/`, `g7/` and the
    journal). It was then changed by one line before the F2 commit.
  - **1:** the r2 test patch before its regeneration (`b5ed4d34…`).
  - **1:** the ledger at a moment between two commits.
  - **2:** `docs/plans/v0.5.13-charter-prep/exposure-check.json`, for
    `docs/validation/v0.5.10/cleanup/manifest.json`. They were not examined further.

  `no-match` means only that neither of the two other kinds applies.

**What it means.** The recorded hash differs from the committed bytes for:
- the CRLF copies of 11 records (`crlf-of-head`);
- the files that changed since or were never committed in that form (the other kinds).

No locked claim, tag, dossier or verdict is among the divergent files. Each claim-hash record
compares canonical hashes, which do not depend on line endings.

## The proposal: tools that write text with CRLF (not applied; correcting them is a stop)

Each tool below writes a record with `Path.write_text(...)` without `newline="\n"`. On Windows it
writes CRLF, which is the source of the `crlf-of-head` entries. **The proposed change:** add
`newline="\n"` to each call that writes a record, or write bytes, `.write_bytes(text.encode("utf-8"))`.
The tools already written that way (`identity.py`, `launch_v1.py`, `make_patch.py`, `g7_prepare.py`,
`g8_restore.py`, `hash_sweep.py`) need nothing.

| Tool (`docs/validation/v0.5.13/tools/`) | Line(s) | Record |
| --- | --- | --- |
| `check_f2.py` | 112 | `check-f2.json` |
| `check_m45.py` | 122 | `check-m45-*.json` |
| `compare_identity.py` | 95 | `comparison-*.json` |
| `demo.py` | 76, 81 | `transfer.json`, `demo.json` |
| `demo_check.py` | 63 | `demo-check.json` |
| `diag_golden_diff.py` | 90 | `diag-golden-diff.json` |
| `g1_prepare.py` | 116 | `g1-prepare.json` |
| `g2_normalize.py` | 83 | `g2-normalize.json` |
| `identity.py` | 133 | `case-outputs.json` (line 131 is already LF) |
| `order_proof.py`, `order_proof_v2.py` | 90, 94; 96, 105 | receipts and `transfer.json` |
| `pypi_fetch.py`, `testpypi_fetch.py` | 56-57; 53-54 | `*-fetch.json`, `transfer.json` |

**Also proposed:** when the launcher copies a unit's `outputs` into the repository, it could record
the SHA-256 of the bytes as git will store them (LF), or refuse a CRLF output. The launcher change
is a separate decision.

Each change is a tool change, committed before the tool's next run; the past records keep their
recorded hashes, and this list is their correction.
