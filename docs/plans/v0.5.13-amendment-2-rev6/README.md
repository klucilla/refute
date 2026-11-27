# Amendment 2, revision 6: the diff from revision 5, the reason of each hunk, and the check

The maintainer's decision K2 (#218, comment 7223240289). Labels: `exploratory`,
`method_status: not_validated`. **PROPOSED, not approved.** Under decision K4, nothing of
amendment 2 runs before revision 6 is adopted: not the manifest, the freeze, the checks or NR-A2.

| File | SHA-256 |
| --- | --- |
| Revision 5, [`../v0.5.13-charter-amendment-2-rev5.md`](../v0.5.13-charter-amendment-2-rev5.md) (commit `86f1f289ce0327168f9bc7437080ca2752e56a1a`) | `c69b23e9074477bb481638f39577ac98eaed549e9e00271478900d944235518b` |
| Revision 6, [`../v0.5.13-charter-amendment-2-rev6.md`](../v0.5.13-charter-amendment-2-rev6.md) | `86a3853e3d052e5f65c2b3049e58f913abb105997109d362f07056801e235b7c` |
| [rev5-to-rev6.patch](rev5-to-rev6.patch) | `37ca9bbec45150d0a18f82340c1610748a1c92707129d9760f846b3cb60a8718` |
| The second blind review's answer, [`../v0.5.13-amendment-2-blind-review-2-result/answer.md`](../v0.5.13-amendment-2-blind-review-2-result/answer.md) | `7f71b206d7efbc1afef2ce62d14cb8483365b2ac04ed12752007c1f63f70114a` |

## The map (decision K2(a))

[hunk-map.json](hunk-map.json) gives each hunk its labels. A label `B1` to `B4` is a blocking item
of the second blind review, applied with its replacement text exactly as written. A label `a` to
`i` is the maintainer's decision K2(x). Hunks that carry more than one label are broken down below.

| Hunk | Revision 5 → 6 lines | What changes | Label |
| --- | --- | --- | --- |
| 1 | 1-37 → 1-42 | The title says revision 6. The two headers of revisions 5 and 4 become one header: how revision 6 is adopted and the maintainer's reason; what it replaces, by commit and full SHA-256; what was known (the second blind review, `NOT_APPROVABLE`); what changed; what it amends. "It changes an acceptance rule" moves into that item, and the E1 heading names its comment. | d |
| 2 | 40-53 → 45-57 | Revision 4's paragraph on Codex round 3 becomes the key of the marks used in the text ("blind review", "blind review 2", "Codex round 3", decisions). Its facts are kept: round 3 was the last, and its item 4 went to #231. | d |
| 3 | 96-107 → 100-119 | Section 1: whether the `plan-` goldens were opened, the earlier search of the ID-BEFORE folder, and that both are inputs of Codex's completeness review. | c |
| | | Section 1: "so it is a floor" is replaced by the maintainer's words "not a bound on the number of manifest rows in either direction". The smallest grammatical fix: the words follow "a feasibility count," and the rule's sentence is kept after them. | b |
| 4 | 199-205 → 211-222 | Section 4: a line marking the two new paragraphs, then the first paragraph replaced by the reviewer's two paragraphs. | B1 |
| 5 | 227-248 → 244-276 | Section 4, after the quoted text: integer or configuration predicates count as assessed for the zero-coverage rule, in a separate count; non-numeric predicates still do not. | f |
| | | Section 4: the view of `verdict-v4.txt` and the earlier search are inputs of Codex's completeness review. | c |
| | | Section 4: a line marking the reviewer's texts, the examples' introduction, and the last two sub-bullets of the extra-frequency loops replaced by the reviewer's texts. | B2 |
| | | Section 4: `peak is None` is added as the loop's other stop condition. | g |
| 6 | 287-295 → 315-329 | Section 5: the decision-layer scope and its declared limit also apply from version 5 onward, unless that version's charter widens them before the evidence exists. | e |
| | | Section 6: a line marking the reviewer's texts. | B3 |
| 7 | 297-307 → 331-341 | Section 6: the last sentence of item (c) and the label sentence, replaced by the reviewer's texts. | B3 |
| 8 | 331-343 → 365-380 | Section 7: a line marking the reviewer's text, and the list of open items replaced by it. | B4 |

Decision K2(h) changes nothing. Under K2(i), every SHA-256 in revision 6 is written in full; the
check below finds no abbreviated hash.

Two of the reviewer's texts say "Under revision 5" (item 2) and "They stay valid under revision 5"
(item 4). They are kept word for word, as K2 requires, although the file is now revision 6.

## The deterministic check (decision K2)

Both runs were metered units, offline, after the tool was committed (`59e7aee6`, before its first
run). No Codex.

- **`rev-diff check`** of the patch and the map: 8 hunks, 8 labelled, no unknown label, no extra
  hunk.
- **`rev6-check`** ([`tools/rev6_check.py`](../../validation/v0.5.13/tools/rev6_check.py)):
  **PASS**, no problem.
  - **The replacement texts:** the six blockquotes of section 2 of the answer, cut from the
    committed file. Each is in revision 6 word for word, normalizing only quote prefixes and
    whitespace.
  - **The replaced passages:** six, cut from revision 5 by the answer's line ranges (202, 230-231,
    241-245, 300, 304 and 334-340), each with its anchor. Each is present in revision 5 and absent
    from revision 6.
  - **The decisions:**
    - (b): "so it is a floor" is gone and the maintainer's words are present;
    - (d): one "PROPOSED, not approved" banner, and revision 4's header is gone;
    - (g): `peak is None` is present;
    - the marks K2(b) to K2(g) are present;
    - (i): no abbreviated hash.
  - **The patch:** it equals a fresh diff of revisions 5 and 6, byte for byte, and every hunk
    carries only `B1` to `B4` or `a` to `i`.

The check shows that the texts are applied and nothing else is labelled outside K2. It does not
check the wording of decisions (b), (c), (e), (f) and (g), which is the agent's. That is for the
maintainer's adviser.
