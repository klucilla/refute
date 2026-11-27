# Amendment 2, revision 7: the diff from revision 6 and the reason of each hunk

The maintainer's decision P1 (#218, comment 7225754254). Labels: `exploratory`,
`method_status: not_validated`. **PROPOSED, not approved.** A third blind review comes before the
maintainer's adoption by SHA-256. Nothing runs on goldens before revision 7 is adopted.

| File | SHA-256 |
| --- | --- |
| Revision 6, [`../v0.5.13-charter-amendment-2-rev6.md`](../v0.5.13-charter-amendment-2-rev6.md) (commit `c6236e91a6bbb108b06e731c2d272ce6b9bd2a57`, adopted in L1) | `86a3853e3d052e5f65c2b3049e58f913abb105997109d362f07056801e235b7c` |
| Revision 7, [`../v0.5.13-charter-amendment-2-rev7.md`](../v0.5.13-charter-amendment-2-rev7.md) | `eb320426b194da7195b9e5131ead295940d11ea06dcc5265ff8645d74393a5b5` |
| [rev6-to-rev7.patch](rev6-to-rev7.patch) | `0f91ab0c68ea576b18b57bf4fc8b30b7653e77d5522aecdb5978e88c8f3a0667` |

The committed unit `rev-diff` wrote the patch (7 hunks) and checked [hunk-map.json](hunk-map.json):
7 of 7 hunks labelled, no unknown label, no extra hunk. Every hunk is tied to P1.

| Hunk | Revision 6 → 7 lines | What changes | P1 item |
| --- | --- | --- | --- |
| 1 | 1-34 → 1-26 | The title says revision 7. The header names P1 and how revision 7 is adopted (a third blind review, then the maintainer's approval by SHA-256). It names revision 6 by commit and SHA-256, the direction, and what changed. | P1 |
| 2 | 51-57 → 43-49 | The marks list adds "P1(x)". | P1 |
| 3 | 115-120 → 107-132 | The end of section 1 states what was known when revision 7 was written: the frozen manifest and its counts, the reach rule changed after zero coverage was seen, and Codex's answer with N3: yes. | P1(e) |
| 4 | 139-145 → 151-161 | Section 3's first sentence drops "together with the margin check of section 4", with a line saying so. | P1(a), P1(b) |
| 5 | 211-218 → 227-252 | Section 4 opens with the rule that the margin check does not apply to versions 1 to 4. It gives the declared limit, its reason, and the two preserved records, cited by SHA-256. It says what freeze still holds for versions 1 to 4, and that the rest of section 4 applies from version 5. | P1(a) |
| 6 | 319-341 → 353-381 | Section 5 adds the design requirement for v0.5.14's charter (P1(d)). Section 6's criteria become byte identity, NR-A1 decision identity and NR-A2 decision identity; an NR-A2 that fails leaves #226 unmet (P1(b)). The label names the new limit (P1(c)). | P1(b), P1(c), P1(d) |
| 7 | 378-380 → 418-431 | Section 7 adds the open items under revision 7, consistent with P1(a): the comparator exists and is corrected under P2, the revision-6 freeze is a record, and a new freeze precedes any golden read. | P1(a) |

Nothing else changes from revision 6.
