# Lock history

Append-only record of every `refute lock` performed on the claims in this
directory, including forced re-locks. Entries are written by `refute lock`.
Never edit or delete an entry: `refute verify` checks that a claim's lock is the
latest entry recorded here, and the git history of this file is the evidence of
when each lock happened.

## 2026-10-19T13:49:28Z | claim.yaml

- action: lock
- claim_id: v0.3-main-2305.19518
- claim_sha256: ff1ac0933507882c63178a9fa7e7d5b0c82279a7ee758b9ac6bdbec9e8403424
- previous_claim_sha256: none
- attachments: inventory.json=4735ebb57dc5c74e0903318f70bec0693180bd6c79833bb1be003e6bbaea6c6e, draw.json=6bc8dd58404507f420ac595485aff8cb32cde278abf7d9d7cefc53d7d859906e
- code_sha256: 3165e1417ebe1f9474145076000f14f3b561b2cdd55f8c2b6b36ffde26e17322
- git_commit: abdc9031f565aa445e912603dbb24b33a9e64c80
- git_dirty: false
- refute_version: 0.2.0
- reason: initial lock
