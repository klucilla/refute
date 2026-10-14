# Development campaign 1: records

Campaign 1 of the development chain (`declaration.json`, SHA-256
`da54ed16f30a85fc7d75f1c341240a0659e3b1066393d6d3541e4e87837d822d`): set 1 generated and accepted on 2026-10-13
(`../../manifest-dev.json`), then measured at M0, M1, M2 and M3 in two slots by the v2
orchestrate, from 2026-10-13T19:49:34+00:00 to 2026-10-14T04:22:22+00:00 (HEAD `c16c6422686ce86f99736b10a97ca0762754c5b5`,
30766.3 s; physical memory in use on the whole machine
32.58 GB at the start, peak 44.77 GB).
No lock, no divergence: 52 lots, 208 slot comparisons, all identical. **Overall approval:
FAILS at every point** (`metrics/metrics-dev-campaign-1.md`). A development measurement, not
the validation.

Committed here (Amendment 4, item 11):

- `journal.jsonl` (hash-chained journal) and `set-1-check-*.json` (the `check-set` report);
- `generation/`: the execution records of the three generations of set 1 and the block index
  (`blocks-set1.json`, SHA-256 `d9c55154adb41409b3e9ae661b7e9fda317b1c538702da390a8b1375bf3d6f0b`); the three block indexes and the three
  manifests are byte-identical, and the manifest is `../../manifest-dev.json`;
- `records/`: per lot, records 1 (started), 2 (regenerated), 3 (results re-read: the SHA-256
  of every result record of the lot, per point and slot, the per-lot index), 3c (the
  comparison of the two slots, per point) and 4 (inputs deleted);
- `runs/<point>-slot<n>/run.json`: the run records of the eight run directories;
- `metrics/`: `metrics-dev-campaign-1.json` and `.md`.

Kept out of git for the later release asset (Amendment 4, item 11), listed with their SHA-256
in `asset-SHA256SUMS` (paths relative to the campaign's work folder): the 41600 complete
result records (2.36 GB, 57 KB per record on average),
the observations of the three generations and of the 52 regenerations, and the manifest and
block index of each of the three generations (byte-identical; one copy of each is committed); 41661 files, 2.82 GB in all.
The paths inside the records are those of the maintainer's machine; the user name is masked.

Added at the closure of the study (2026-10-14; `../../closure-record.md`), read from these
records without changing them: `diagnosis.md` (M0 and M3), `holdout-investigation.md`,
`c3-inconclusive-investigation.md` (with a dated errata) and `investigations/`, the read-only
scripts and small JSON outputs behind the three documents (its `README.md`).
