# Lock history

Append-only record of every `refute lock` performed on the claims in this
directory, including forced re-locks. Entries are written by `refute lock`.
Never edit or delete an entry: `refute verify` checks that a claim's lock is the
latest entry recorded here, and the git history of this file is the evidence of
when each lock happened.

## 2026-10-07T21:42:15Z | self_claim.yaml

- action: lock
- claim_id: tess-calibration-v0.1
- claim_sha256: 5701c54cb088f1d33895f73d98244d0ea214ddb3f861340d8261b817e189a53f
- previous_claim_sha256: none
- attachments: targets.yaml=1d0fdcd006f3bea2b1608e1ea5f7dc847704194cbfba92e67bf2c4ff31dc6883, PROTOCOL.md=876b022429bc2b6443e7db5ef0c86f13750ffb21d5769e5899d7bd46041b685b, selection_log.md=4394e36506dc9776d3694d22957b03217e638033fed8fcf12200239eacc35819, pool_snapshot/retrieval.json=01e48d7ece0d9197fc665376780690c18749f3eca0963b6dbd0b45b7d1a99302
- code_sha256: 624f5f900334abcdc614a679a3fdc4ce9c9e8a465f2d3e553d71b24c199f4cfa
- git_commit: 5214f2e29de98803aafff3094733ca424ae3dbde
- git_dirty: false
- refute_version: 0.1.0
- reason: initial lock
