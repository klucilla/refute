# Lock history

Append-only record of every `refute lock` performed on the claims in this
directory, including forced re-locks. Entries are written by `refute lock`.
Never edit or delete an entry: `refute verify` checks that a claim's lock is the
latest entry recorded here, and the git history of this file is the evidence of
when each lock happened.

## 2026-10-09T15:29:55Z | self_claim.yaml

- action: lock
- claim_id: tess-calibration-v0.2
- claim_sha256: c9f341d29bea4ec0d125adf3f0822fae4b593beabbdd19aeb339613e7a6b34a8
- previous_claim_sha256: none
- attachments: targets.yaml=5db2b04761310817d2c47a1dcb699ad237a1a8dec3f5ad782024c8bb5ba349a2, PROTOCOL.md=f7c246551bd30a75df362053ada1e16f84a175ad91316d3124df2d615ab82cdf, selection_log.md=9d49cc2c351a4d2f8938f34f7c43a7d9014efd28cf20e558410c8c7fc827da13, pool_snapshot/retrieval.json=bd3bc6703689c0649542b51294fd96285bf2edd3c502fea8a6160b24beaa2229, eb_catalog.csv=4ce34194a988abcfbfa11565ecc86c10cd0f8cea611f283201bf024c21aab0a9, eb_catalog_scan.json=70abfa45f42fcb54bff97785986a1b77621b6f2dcdb8a09a539550e09b755794
- code_sha256: 2cd8b5c16c9ded3e32335cd95d8b68f46e0676d5183f3129a6cef4e8dfbd1752
- git_commit: e176ac3d21ca6e2efeb5085a8acb44d69624d520
- git_dirty: false
- refute_version: 0.1.0
- reason: initial lock
