# Lock history

Append-only record of every `refute lock` performed on the claims in this
directory, including forced re-locks. Entries are written by `refute lock`.
Never edit or delete an entry: `refute verify` checks that a claim's lock is the
latest entry recorded here, and the git history of this file is the evidence of
when each lock happened.

## 2026-10-31T12:25:50Z | claim.yaml

- action: lock
- claim_id: tess-discover-v0.4-pilot
- claim_sha256: d2ce83808eb026189fa76b83533aeca8b98e81ad5dff92b17e4cfa7a83eb61d5
- previous_claim_sha256: none
- attachments: selection/targets.yaml=d213bd1e37d8b8d7bddc21f9a91e3b1f631e0239c8dfb511cd72d11122f6c75f, PROTOCOL.md=6b22d2b81b80fe462897dabb0a08fb328a6f0ae27f5d09cf48ffb85b6b3c3275, inputs.json=c49b3119415f5686eb91a0284e9ffdffa307e0eda2a8356b3b3d470741b080b4, selection/selection.json=19a013d36585a671f4060c08a556865d56126dea176c8597daea8b91d027daf1, eb_catalog.csv=dff46d62920ae943d6ec75e12acc17cb84f47deea9608b56d15cae112ae04f15, eb_catalog_scan.json=a63a5f1e397f272f84348a5955d60ae9b9c6e50fddae87bd24d01bd33889514c
- code_sha256: bbf52fdfa93d47b05da305359f376452cd1a8f6158fd75577237a55dc41f88dc
- git_commit: 910ada156ff57754c82df1496495afefb3020cc4
- git_dirty: false
- refute_version: 0.2.0
- reason: initial lock
