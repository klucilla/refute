# Lock history

Append-only record of every `refute lock` performed on the claims in this
directory, including forced re-locks. Entries are written by `refute lock`.
Never edit or delete an entry: `refute verify` checks that a claim's lock is the
latest entry recorded here, and the git history of this file is the evidence of
when each lock happened.

## 2026-10-19T14:07:09Z | claim.yaml

- action: lock
- claim_id: v0.3-main-2309.15704
- claim_sha256: 598543893374b9c4742d44f25bbaf7fa89cbc3f2faf7f4e857c2359a91b34957
- previous_claim_sha256: none
- attachments: inventory.json=3f48f1003dbfd0991e802c20de0f9479b43e6484de3ca0db0efc0c3d40fd7cb7, draw.json=407daecb228a061e1fa683d5f022ae8c5bca6a0840df9ecbdcd158dc7b54ccda, 2309-uci-files.patch=05413b6a4bd65cf26cc79c69dc0a9c1f5e7e5d0d4ee8a0d028f8e4c6e30c4a8f
- code_sha256: 3165e1417ebe1f9474145076000f14f3b561b2cdd55f8c2b6b36ffde26e17322
- git_commit: 4b35d35232725063c0a611851ba3561a4a6e19c2
- git_dirty: false
- refute_version: 0.2.0
- reason: initial lock
