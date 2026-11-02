# v0.4 Discover pilot: results

Published at P7 (step f of item 9) after the maintainer's approval (#177). Each file below is
published **unchanged**: its SHA-256 was committed earlier in a P5 anchor
(`calibration/v0.4/runs/p5_anchor*.json`), so anyone can check that these are the bytes the
anchors cite. `method_status: not_validated`. Refute produces candidates and verdicts only;
nothing here is a confirmed discovery.

| File | SHA-256 | Cited by |
|---|---|---|
| [report-4.md](report-4.md) | `32e9b2c1df7cc2e6b4a814fb1c81e0437bf1e393b0f96a3eb6f7c9254f84217b` | `anchor-4-detail.json` (`p5/report-4.md`) |
| [ledger.jsonl](ledger.jsonl) | `9275f993ba18d46352577a3fbc052d692cf7e60cca9ddb1f6c6f6c2d21e64663` | `ledger.file_sha256` of `p5_anchor-4.json`, `p5_anchor-5.json` and `p5_anchor-6.json` |
| [anchor-2-detail.json](anchor-2-detail.json) | `3dace2f12ff09b8cf1eb1284e244bfab1a0334e28b41158e5dfeb657eea50ca0` | `private_detail_sha256` of `p5_anchor-2.json` |
| [anchor-3-detail.json](anchor-3-detail.json) | `9ef7324435742c0c6798a33e2493bd0795f032b05435e59347383ba8b126f50e` | `private_detail_sha256` of `p5_anchor-3.json` |
| [anchor-4-detail.json](anchor-4-detail.json) | `8a5d80be4d2fdb3a6d5ee5b34a2e7bd1591c40e6c3120104692fcbfb8a8414a2` | `private_detail_sha256` of `p5_anchor-4.json` |
| [anchor-5-detail.json](anchor-5-detail.json) | `d9effaaf7d1687a3d15241652f8e98e8be600d0f5af95d1a3ca8d23d19945baf` | `private_detail_sha256` of `p5_anchor-5.json` |
| [anchor-6-detail.json](anchor-6-detail.json) | `2f16b83deb08b89c931a6a90e0902230afbd43169d43f270e2795633944b9fdf` | `private_detail_sha256` of `p5_anchor-6.json` |

The two gate reviews (P6) are in [docs/gates/v0.4-review.md](../../../docs/gates/v0.4-review.md).

## The state since report-4 was written

`report-4.md` is the report as the maintainer approved it on 2026-11-01, kept byte for byte so
that it can be checked against its anchor. Its title ("draft for the maintainer, not published")
and its reproduction section (the archives "in the maintainer's private archive") describe the
state of that day, not the current one. Since then:

- **The two reproduction archives are public**: https://doi.org/10.5281/zenodo.23874043
  (published 2026-11-02), with the SHA-256 of `calibration/v0.4/runs/reproduce_archives.json`.
- **The five stage-2 dossiers are public**, each with its core and every annex:
  https://doi.org/10.5281/zenodo.23898648 (published 2026-11-02). The data in both records keep
  their own terms: [../DATA_LICENSE.md](../DATA_LICENSE.md).
- **The reproduction instructions are the annex `reproduce-4`** (instructions version 4, at commit
  `6143c11`), which supersedes `reproduce-2` (a private `ARCHIVE`) and `reproduce-3` (a commit
  whose `prepare` asked only the CDS and the CfA mirror for the TESS-EB table). At `6143c11`,
  `prepare` asks the CDS and then VizieR's mirrors (source:
  [../sources/vizier-mirrors-2026-11-02.md](../sources/vizier-mirrors-2026-11-02.md)). A
  rehearsal of `prepare` only, with no change by hand, passed at that commit on 2026-11-02
  (`p5_anchor-6.json`). The full reproduction on record is still the one of 2026-11-01 at
  `95cd7d9` (annex `reproduction-2`); no new full reproduction was run.
- **VizieR's rules of usage** could not be re-read live: the CDS did not answer at any of the
  attempts recorded on 2026-11-01 and 2026-11-02, after its incident notice of 2026-10-28. The
  publication rests on the original sources' licenses, the
  reading of 2026-10-17 and an archived capture of 2026-10-25 (L9 of
  [../sources/data-licenses-2026-11-01.md](../sources/data-licenses-2026-11-01.md)); the live
  re-read stays open.
- **The conclusions** in `report-4.md` were approved by the maintainer on 2026-11-01. The approvals
  are ledger events 426 to 429; event 425 records the conclusion the maintainer set for one case
  (annex `case-2`). The `case` annexes inside the dossiers keep the readings as they were drafted.

## The ledger

`ledger.jsonl` holds 429 events (last hash
`ac05c07fcd1ad37029f1c9e165bff5a73b1a7a0b7a1f5ff3a7b35a595d39b99f`). Check it with
`refute.core.ledger.verify_file(path, check=refute.packs.tess.discover.case.check_event)`. It was
assembled at P5 (2026-11-01) from dated records: each event's `utc` comes from its source record,
and the hash chain shows the order in which the events were written at P5, not that they were
recorded live (`report-4.md`, Limits).

## The anchor details

Each `anchor-N-detail.json` lists the annex manifests of the stage-2 dossiers and the SHA-256 of
the private files of that round, under paths relative to the project's local `.cache/v04/`
folder. Those files are not all published: the communication drafts wait for the next step of
P7, and working files (scripts, rehearsal records, probes) stay local. Their hashes are here so
that a file published later can be checked against them.
