# Amendment 2, revision 5: the diff from revision 4 and the reason of each hunk

The maintainer's decision J1 (#218, comment 7222879969). Labels: `exploratory`,
`method_status: not_validated`. **PROPOSED, not approved.** No check of amendment 2 runs before
revision 5 is adopted.

| File | SHA-256 |
| --- | --- |
| Revision 4, [`../v0.5.13-charter-amendment-2-rev4.md`](../v0.5.13-charter-amendment-2-rev4.md) (commit `288d5785053ea139d23d2c5eced5ad7d1329a85b`, adopted in I1) | `7d96726de18157ccd4d20f494a9efcef076107efda9337179b1f5f67870d8d4e` |
| Revision 5, [`../v0.5.13-charter-amendment-2-rev5.md`](../v0.5.13-charter-amendment-2-rev5.md) | `c69b23e9074477bb481638f39577ac98eaed549e9e00271478900d944235518b` |
| [rev4-to-rev5.patch](rev4-to-rev5.patch) | `efec9517065b08b5ad44ad79a6f2713a64998f7b71dcae57e9f7402702b27fce` |

The committed unit `rev-diff` wrote the patch (3 hunks) and checked [hunk-map.json](hunk-map.json):
every hunk is labelled, every label is known, and there is no extra hunk.

| Hunk | Revision 4 → 5 lines | What changes | Label |
| --- | --- | --- | --- |
| 1 | 1-5 → 1-16 | The title says revision 5. A header names decision J1, revision 4 by commit and SHA-256, and what changed. Revision 4's header follows unchanged. | J1 |
| 2 | 76-81 → 87-108 | The end of section 1 states what was known when revision 5 was written: the inventory of 2,746 sites, the view of part of a verdict golden during H2, and the count of decision-layer predicates (J1(a), (b)). | J1 |
| 3 | 172-184 → 199-205 | The first paragraph of section 4, with its list, is replaced by the maintainer's text, exactly. | J1 |

Nothing else changes from revision 4.
