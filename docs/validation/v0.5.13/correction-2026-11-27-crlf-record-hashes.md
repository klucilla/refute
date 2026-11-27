# Correction, 2026-11-27: journal hashes of records written with CRLF

The maintainer's decision I3 (#218, comment 7222329150), from the sweep of G9
([g9/README.md](g9/README.md), [g9/hash-sweep.json](g9/hash-sweep.json), at HEAD
`3dbb713c7fa40960d8f7941826e0a9c91a4b1b74`). Labels: `exploratory`, `method_status: not_validated`.

## The error

Several of this phase's tools wrote their JSON record with `Path.write_text` and no `newline`
argument. On Windows that writes CRLF line endings.
- The launcher copied each record into the repository and recorded the SHA-256 of those CRLF
  bytes in the journal (`log.jsonl`), as `outputs_sha256` or as `extra_files_sha256` of a later
  unit.
- git stores the same records with LF (`.gitattributes`: `* text=auto eol=lf`), so the committed
  blob has another SHA-256.

The content is the same. In each case the recorded value is the SHA-256 of the blob with LF turned
into CRLF (the sweep's class `crlf-of-head`).

## Each record

| Record | Journal line(s) and field | SHA-256 recorded (CRLF bytes) | SHA-256 of the committed blob (LF) |
| --- | --- | --- | --- |
| `docs/validation/v0.5.13/d4/check-m45-files.json` | 135, `outputs_sha256` | `24a9d93dbe099fd92476c398d88d83b1d5890a098d39425d0419eecb75d0b52d` | `f7feb285f531945b5264253a14a0192253c4d68bed5c190a2dd99a23bd19f9da` |
| `docs/validation/v0.5.13/d4/check-m45-uvlock.json` | 139, `outputs_sha256` | `7f2505890530ed51a02340c5c911f49d1aa661d103579dfd1753fb4eabe04cb3` | `7efa63a16d03f24b6a25655ece370c694857892c2c1c86d5cc4a10ce9159c671` |
| `docs/validation/v0.5.13/d5/testpypi-fetch.json` | 321, `outputs_sha256`; 424, `extra_files_sha256` | `c41f95a16e74bc314ce374ecf476631a68a5a41bc0cbbf2f8f60fc412b5fe5ec` | `bca15afc39e3b0abe632f87a22c0b0a1d46f49e72c301840a910c9c950ca18d9` |
| `docs/validation/v0.5.13/e5/testpypi-fetch.json` | 324, `extra_files_sha256` | `c41f95a16e74bc314ce374ecf476631a68a5a41bc0cbbf2f8f60fc412b5fe5ec` | `bca15afc39e3b0abe632f87a22c0b0a1d46f49e72c301840a910c9c950ca18d9` |
| `docs/validation/v0.5.13/f2/check-f2.json` | 402, `extra_files_sha256` | `d6f7895b8908345ac85262726c2360e578af1f6b025b0e51f267abd01d40255c` | `de0501b2a691df627758dccb3c9180b123e905bf85f9b4de6c811639cb25c627` |
| `docs/validation/v0.5.13/g1/g1-prepare.json` | 454, `extra_files_sha256` | `80b5ca05a8137944080c958d227161fbef9a921f354b4a04e0138bfa729be96e` | `c1186077621c05bcaf685cdcf6c4e8cb8032b4b9c774d6bcb4948e627590fe4c` |
| `docs/validation/v0.5.13/g2/g2-normalize.json` | 454, `extra_files_sha256` | `facbef0603aefb85c6ab3933cb788de05f88daa29bb56374edd9fe5817b7a41f` | `9dd78eff59473ab89d08625bbb888760f718146bf4f9e10a2cfc7d94e65f2b89` |
| `docs/validation/v0.5.13/g7/check-f2-g7.json` | 485, `outputs_sha256`; 500, `extra_files_sha256` | `7b6cbd57ec098e30dc5e2948780a954b56f9ba615358e405bd3bb035899d8649` | `3b4746bd8519193b1b3d0c4a663a7964104c8a772de7e335961d310c0ea9a3c8` |
| `docs/validation/v0.5.13/step0/demo-check.json` | 13, `outputs_sha256` | `da2eae840d9768c30392f550a86a1d579d66b6e7dc349a0508f1b4a06e679021` | `6dd33cf0609582de390677b72dd822f31b9d3cff0673bf683cf4d526a85c1d16` |
| `docs/validation/v0.5.13/step1/comparison-nr-a1.json` | 101, `outputs_sha256` | `f9b0cbea8ebae5f47b22678dc88700d3fa8d0c2e83dc155f7587f07bd4e213c6` | `be824c2cdc6a79f82539daa75f5c765ddd34c236057ae609d3d469a841b76ecd` |
| `docs/validation/v0.5.13/step1/diag-golden-diff.json` | 131, `outputs_sha256` | `d62082deb2217b55b34d5b4b517bf5d5447569e8d88e6f8cb1ffc9f24e44fff6` | `d0f3ded6d6cb6b8ef7000281765abd8880c4dd1c5ca57a5171ad826f2d1a8826` |

The two `testpypi-fetch.json` rows are one record in two places, with the same bytes.

**One more `crlf-of-head` entry is not a record:** `src/refute/packs/tess/a0.py` (journal lines 394
and 396). It was hashed as an argument while its working copy still had CRLF. Recorded
`7b62f1f516183dc3a25ad814498f673b8c58ea3c82f9a6d1dc8504398771937c`; committed blob
`cf1b47a0ad94c4102b18a9dd97ae12b14db84d57bdb722e1b0fecbb6ed1ae5f1`. G8 restored the file to its
blob.

## Handling

- **No record is edited:** neither the journal, nor any listed file. This file is their
  correction.
- **The cause is fixed** in the tools, in their own commit, before their next use (decision I3).
  Each record those tools write is now LF, so its recorded SHA-256 equals its committed blob's.
- **Impact:** no result, verdict, lock or approval depends on these hashes. The record contents are
  unchanged; only the line endings of the bytes hashed differ.
