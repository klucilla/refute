# Lock history

Append-only record of every `refute lock` performed on the claims in this
directory, including forced re-locks. Entries are written by `refute lock`.
Never edit or delete an entry: `refute verify` checks that a claim's lock is the
latest entry recorded here, and the git history of this file is the evidence of
when each lock happened.

## 2026-10-19T14:42:38Z | claim.yaml

- action: lock
- claim_id: v0.3-main-2502.16782
- claim_sha256: 3e59b8353da037e57d03b68817c7b01c947e06ef113555c8b79f4ec842b857ab
- previous_claim_sha256: none
- attachments: inventory.json=17999ce8fe04ef21df0179302d0d60b2b5e158e085d2700eb90c175da0a9a3e9, draw.json=0f0b4eee99e55363e947839efc5961db0fe8abdba2363dc4e76eefe68e039780
- code_sha256: 3165e1417ebe1f9474145076000f14f3b561b2cdd55f8c2b6b36ffde26e17322
- git_commit: a27fd3c50dd647594858a8e9547194a6c3334b55
- git_dirty: false
- refute_version: 0.2.0
- reason: initial lock
