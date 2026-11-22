# Lock history

Append-only record of every `refute lock` performed on the claims in this
directory, including forced re-locks. Entries are written by `refute lock`.
Never edit or delete an entry: `refute verify` checks that a claim's lock is the
latest entry recorded here, and the git history of this file is the evidence of
when each lock happened.

## 2026-11-22T23:56:07Z | claim.yaml

- action: lock
- claim_id: tess-v0.5.6-part-b-fp-agreement
- claim_sha256: d451e995eae3f12afda0e5d807f5c5516c16c8bc1094b6d72c1623e5528b749f
- previous_claim_sha256: none
- attachments: pool-targets.yaml=5b30f4418e140339e3b0bdd4512fe33f8ca732acc4c3e251ffbb917c121235c3, part_b_claim.py=8517d12b2a87c02da1bc57bbf7c3ed74cc129789c3d7c019e438aff37e91d6f4, part_b_draw.py=70ee3eb97700976031e495d2a43a074d621c9c12a46f726a6c5f6e1aba6748c6, part_b_run.py=247c93439a4839310e3bf628b8dd50691973cb039e99a918fbf485ae44f016fe, part_b_run.diff=35b4a96bd5091c31907b242497f82f455d1bdeb0a9fcc45a3968351b3c283da1, part_b_evaluate.py=663d1770719e82aff8c81b7d133aaf87a8160209aa0f501f6a1e9c1342251964
- code_sha256: e1a89af9784a51baad9479044c0c678664104e571e4434e287519cc1e08d0cab
- git_commit: fd62b0aba9a0be7e2dd7fbe49dac483b4bc05732
- git_dirty: false
- refute_version: 0.5.0
- reason: initial lock
