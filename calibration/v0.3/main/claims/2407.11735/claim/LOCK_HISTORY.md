# Lock history

Append-only record of every `refute lock` performed on the claims in this
directory, including forced re-locks. Entries are written by `refute lock`.
Never edit or delete an entry: `refute verify` checks that a claim's lock is the
latest entry recorded here, and the git history of this file is the evidence of
when each lock happened.

## 2026-10-19T14:24:53Z | claim.yaml

- action: lock
- claim_id: v0.3-main-2407.11735
- claim_sha256: dcea7ed105a99f336a124db706d1683d058b12fb8b1a2979bc838ede9a25a34f
- previous_claim_sha256: none
- attachments: inventory.json=a179a618902e3491f6c961304cc13320353682328fbdc1f7771bfbdb6f45d06c, draw.json=2b5d6abf7a393a9b8b35ff5b8092fcc39c472ebd8d68288f8565fe46ce0a63e9, 2407-cifar-matlab-files.patch=42c124af63e532ae8f816e2d00d2954b40d5d7c001b70749dbce9697be869a71
- code_sha256: 3165e1417ebe1f9474145076000f14f3b561b2cdd55f8c2b6b36ffde26e17322
- git_commit: 8a8c586b12c0cc799ee08197e3758fdfb2901e50
- git_dirty: false
- refute_version: 0.2.0
- reason: initial lock
