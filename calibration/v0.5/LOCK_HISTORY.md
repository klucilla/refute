# Lock history

Append-only record of every `refute lock` performed on the claims in this
directory, including forced re-locks. Entries are written by `refute lock`.
Never edit or delete an entry: `refute verify` checks that a claim's lock is the
latest entry recorded here, and the git history of this file is the evidence of
when each lock happened.

## 2026-11-04T21:47:09Z | claim.yaml

- action: lock
- claim_id: tess-calibration-v0.5-c3
- claim_sha256: 48acfe245a7231c35353319212324574d408be493c3c53d062ea02adfbd00210
- previous_claim_sha256: none
- attachments: claim-targets.yaml=06013508cf511bf5453a37345b3e75c943bd72489826095f7beed40c63edaa00, selection/targets.yaml=dac40e09a6d261585bc4e9d14e97a79795e9f9287b661d71160871a903837e69, PROTOCOL.md=d1ee49f801bbae432ce01f673b4a5230b25309d81c51bd3b23e6902769759dad, inputs.json=8404740f73a2974862c9fba8040f7171ccb1b62e92543853274d2268f0f64f96, selection/selection.json=65805d9b5ef02298607827bec48a0aff6a52bff96eab8fbf88d829c05064146e, eb_catalog.csv=24fb8427c5cca78f10fc7e386ecab35a847f2851ea86856508aba29e082cc7f2, eb_catalog_scan.json=452e1525232b948200ad974b094b9003d9c0015bd542a6b01b7f2798f24e40b7
- code_sha256: 15a9c256b5aa8f6b6f1eb9db511420ee1efca15b95edd9343322d7c3bb52bf8e
- git_commit: dbc67a14724f290562d3c040f0c96a71480066e0
- git_dirty: false
- refute_version: 0.4.0
- reason: initial lock
