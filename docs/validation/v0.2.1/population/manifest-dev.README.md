# The frozen manifest of the development population

`manifest-dev.json` (SHA-256 `cbfc19c4d70a810f265265c35af6c190826675faaa6b265ae93cc49123352450`, format `refute-population-manifest/2`) is the scientific
manifest of set 1 of development campaign 1 (`campaigns/dev-campaign-1/`, declaration SHA-256
`da54ed16f30a85fc7d75f1c341240a0659e3b1066393d6d3541e4e87837d822d`), accepted by `check-set` on
2026-10-13 and frozen here byte for byte. It is never updated (Amendment 1, item a; Amendment
4, item 12): a regeneration that differs from it stops for investigation.

- **Population:** `dev`, 5200 cases, seed prefix
  `refute-v0.2.1-population-dev`.
- **Harness:** `population_v2.py` `8b3b6ad6aca6e713636b04e40db5a7d253c05458c8b143c38d984100072c1f82`; generator at tag
  `v0.2.0` (the environment of `.worktrees/v0.2.0`).
- **Set 1, K = 3 generations**, each a new main process with new workers, hash only, with
  affinity 8 to 31, started 2026-10-13 at 19:04:39 UTC:

| Generation | Workers | Order | Wall time | Manifest SHA-256 | Block index SHA-256 | Execution record SHA-256 |
|---|---|---|---|---|---|---|
| 1 | 24 | index | 335.3 s | `cbfc19c4d70a810f265265c35af6c190826675faaa6b265ae93cc49123352450` | `d9c55154adb41409b3e9ae661b7e9fda317b1c538702da390a8b1375bf3d6f0b` | `7121d18cd5f6d4c11134aff8321b109c77951f3d616aa3d64d7a0404fe4f2880` |
| 2 | 12 | shuffle:20261013 | 316.0 s | `cbfc19c4d70a810f265265c35af6c190826675faaa6b265ae93cc49123352450` | `d9c55154adb41409b3e9ae661b7e9fda317b1c538702da390a8b1375bf3d6f0b` | `d1f4388cbc5a56b06ae072d264e9c6efa733a1f7e8add3eed5767920bc9f5ab9` |
| 3 | 24 | shuffle:31 | 343.5 s | `cbfc19c4d70a810f265265c35af6c190826675faaa6b265ae93cc49123352450` | `d9c55154adb41409b3e9ae661b7e9fda317b1c538702da390a8b1375bf3d6f0b` | `8b94cf858d9fbd115af1f3a7c8ce29f847c88d1bad5046d64af9500a3021b43b` |

  The three manifests and block indexes are byte-identical.
- **Blocking comparisons** (`check-set`, report `set-1-check-20261013T192114879285Z-8336-b4ca6bec.json`, SHA-256 `da55f5ead28bbf429cbdb527d3090e0b67110116aa24d96d5dbbe1d9722ee0cd`): none
  found. With manifest B (`4073d96a0bce901a31241d5c2dd3d7b46192a4731a4ec3996ea1077039b833e9`,
  the value repeated by the v1 generations B, A2, A3, B2 and D, published in
  `v1-dev-attempt/manifest-b.json`): the same 5200 case ids and, for every case, the same
  whole-blob SHA-256 (also recomputed independently from the two files: 0 cases differ).
  There is no other set in the campaign.
- **Not committed yet:** the campaign journal, the block index (about
  37 MB) and the execution records
  stay on disk until the maintainer commits them; until then they are the accepted risk of
  Amendment 4, item 5.
