# Amendment 2, revision 8: the diff from revision 7 and the reason of each hunk

The maintainer's decision Q2 (#218, comment 7226143268). Labels: `exploratory`,
`method_status: not_validated`. **PROPOSED, not approved.** The maintainer's adviser checks it by
script; the maintainer adopts it by SHA-256. Nothing runs on goldens, no new freeze is made and
NR-A2 does not run before revision 8 is adopted (Q3).

| File | SHA-256 |
| --- | --- |
| Revision 7, [`../v0.5.13-charter-amendment-2-rev7.md`](../v0.5.13-charter-amendment-2-rev7.md) (commit `09fe317ad8f3acaee63517b5603501dcc90df333`, proposed, `NOT_APPROVABLE` in blind review 3) | `eb320426b194da7195b9e5131ead295940d11ea06dcc5265ff8645d74393a5b5` |
| Revision 8, [`../v0.5.13-charter-amendment-2-rev8.md`](../v0.5.13-charter-amendment-2-rev8.md) | `08ea91d8fd406c629bb67eaa288d8380fa6b0f1deb8c3f638bb3a076a5143d66` |
| [rev7-to-rev8.patch](rev7-to-rev8.patch) | `bb09f065695817e6ac39e27e3563fc1942761dea2f16e80692687fff1db3d142` |
| The third blind review's answer, [`../v0.5.13-amendment-2-blind-review-3-result/answer.md`](../v0.5.13-amendment-2-blind-review-3-result/answer.md) | `36a47ebc53d423ff26c4db7a7d71050cbb9cdcf8a07e12d4961ca78e60bc6898` |

The committed unit `rev-diff` wrote the patch (9 hunks). [hunk-map.json](hunk-map.json) ties each
hunk to the blocking items B1 to B4 of the third blind review or the decisions a to k of Q2. The
committed unit `rev8-check` checks the replacement texts, the replaced passages, the decisions, the
patch and the map.

| Hunk | Revision 7 → 8 lines | What changes | Labels |
| --- | --- | --- | --- |
| 1 | 1-32 → 1-53 | The header. The title says revision 8. It names Q2 and how revision 8 is adopted, says revision 6 is the adopted revision, and that revision 7 is a proposed record that got `NOT_APPROVABLE`. It lists every change below by its label, and says that amendments 3 and 4 do not change (a). The title and header have no label of their own, so this hunk carries the labels of the items it lists. | B1-B4, a-k |
| 2 | 43-49 → 64-72 | The marks list adds "blind review 3, item N" and the decisions "N1(x)", "P2" and "Q2(x)". | B1-B4, b, c |
| 3 | 113-121 → 136-142 | Section 1: the frozen manifest's counts, replaced by blind review 3's text. | B4 |
| 4 | 124-131 → 145-192 | Section 1: N1(c) defined, and moot under P1 (c). What was known when revision 8 was written: decision P2 (b), and which result is foreseeable and which is unknown (d). | b, c, d |
| 5 | 207-212 → 268-278 | Section 3.1: the comparator's record reports its coverage per setting; the comparator does not yet, and is changed before the new freeze. | f |
| 6 | 230-249 → 296-319 | Section 4: the reason for P1, replaced by blind review 3's text (B4); what still holds for versions 1 to 4, replaced (B1); how the text kept from revision 6 is read, inserted after it (B3). | B1, B3, B4 |
| 7 | 354-361 → 424-438 | Section 5: "serializes in its outputs", the requirement as the default and H2(f) as the alternative (e); the reach rule fixed before a v5 manifest (i). | e, i |
| 8 | 405-413 → 482-491 | Section 7: "revisions 5 to 8", and the attribution sentence says Q2(h) corrected it. | h |
| 9 | 415-431 → 493-507 | Section 7: the list of absent operands exists only as a record (h); "the four bullets above" (h); which freeze commit is "the freeze commit of section 4", replaced by blind review 3's text (B2). | B2, h |

**Decisions that change no hunk of their own:**
- (g) is a new file outside revision 8:
  [`../../validation/v0.5.13/correction-2026-11-27-numerical-environment.md`](../../validation/v0.5.13/correction-2026-11-27-numerical-environment.md).
- (j) changes nothing; the header says so.
- (k) holds throughout: every SHA-256 is full and read from a file or a unit's output.

Nothing else changes from revision 7.
