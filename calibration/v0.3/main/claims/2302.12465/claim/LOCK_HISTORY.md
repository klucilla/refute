# Lock history

Append-only record of every `refute lock` performed on the claims in this
directory, including forced re-locks. Entries are written by `refute lock`.
Never edit or delete an entry: `refute verify` checks that a claim's lock is the
latest entry recorded here, and the git history of this file is the evidence of
when each lock happened.

## 2026-10-19T13:31:04Z | claim.yaml

- action: lock
- claim_id: v0.3-main-2302.12465
- claim_sha256: cb7720a2fd3dc4d95315bc2ea04829c10060992f1f3c6739d30ce24e614cd6c6
- previous_claim_sha256: none
- attachments: inventory.json=29d29fa1775fb0cb41e741795557758bc1dbfc3b09f6c96f9970bd77b06663ff, draw.json=960f947b1f97cfc08afcf612230ed7ebe4608854371e0f595c96127820a76f3e, 2302.12465-errata-2.json=e2d82493c7434e869e803888c82e2d1605178590267ac57443ec68366994b841, 2302-torch-dgl.patch=4d8563a7ffbafd74acb12e19eba4eff0a3143ac55329472e667e723057c097f8, 2302-population-size.patch=9741191e660dfcef11c975c5971c13aedeb7adaf10986faac3fc734d7a469151, population_count.py=edae1ced3336732c2173554019c5219c2aa7dfa46b9f7beefb2d16e824d44ee6, population_count_record.json=ec018a6f6b98e166091ac64134672bc7f6853cd04cf8ea037c2e06f8976fea4c, population_count_comparison.py=edae1ced3336732c2173554019c5219c2aa7dfa46b9f7beefb2d16e824d44ee6, population_count_record_comparison.json=548bf2bfb49627db1e6d935a8d0789b4b4ae78e30a66fff3354ac454b8b08758
- code_sha256: 3165e1417ebe1f9474145076000f14f3b561b2cdd55f8c2b6b36ffde26e17322
- git_commit: 408a1d724ed7332ed78079eaa1a765449b4d3f68
- git_dirty: false
- refute_version: 0.2.0
- reason: initial lock
