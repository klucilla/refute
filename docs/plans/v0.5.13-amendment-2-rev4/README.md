# Amendment 2, revision 4: the diff from revision 3 and the reason of each hunk

The maintainer's decision H2 (#218, comment 7219469262). Labels: `exploratory`,
`method_status: not_validated`.

| File | SHA-256 |
| --- | --- |
| Revision 3, [`../v0.5.13-charter-amendment-2-rev3.md`](../v0.5.13-charter-amendment-2-rev3.md) (commit `c92ff9777824d6facc65d6ddc781c6492b4b9387`) | `f5598f0050ada236e3944b623ee42b46888e0f1bc8c9b564ab67b529fffcdc38` |
| Revision 4, [`../v0.5.13-charter-amendment-2-rev4.md`](../v0.5.13-charter-amendment-2-rev4.md) | `7d96726de18157ccd4d20f494a9efcef076107efda9337179b1f5f67870d8d4e` |
| [rev3-to-rev4.patch](rev3-to-rev4.patch) | `f4619f12c87a1e6523e448c0763f6c46c2f4dd10d74d5c2465bb0c837c7ac165` |

The committed unit `rev-diff` (`docs/validation/v0.5.13/tools/rev_diff.py`) works in two modes.
- `diff` wrote the patch: a unified diff with 3 lines of context, of revision 3 at `HEAD` against
  revision 4. It has 8 hunks.
- `check` read [hunk-map.json](hunk-map.json) and found every hunk labelled, every label known,
  and no extra hunk.

The labels are:
- `B1` to `B6`: the blocking items of the blind review
  ([answer.md](../v0.5.13-amendment-2-blind-review-result/answer.md));
- `a` to `k`: the maintainer's decisions of H2;
- `H2`: the identification of revision 4 itself.

## Each hunk and its reason

| Hunk | Revision 3 → 4 lines | What changes | Labels |
| --- | --- | --- | --- |
| 1 | 1-14 → 1-24 | Title and status: revision 4, written under H2. Revision 3 is named by full commit and SHA-256. The full SHA-256 of the charter replaces the mistyped abbreviation `2832dc48…c230c813`. Amendment 1 by full commit and SHA-256, with the approval comment 7207651312, item D2. | H2, k, i |
| 2 | 68-114 → 78-156 | §2: item 5's replacement text, and the companion-process note on thread counts (h, item 11). §3: NR-A2 at 2 threads (a). §3.1: "the payload recorded for that same setting", the payload per setting, the raw goldens in git before the freeze, and the 5 MB rule (b). The nonfinite-token rule (c). The ten tag checks not run at 1, 2 or 4 threads (g). The baseline exception's record and hash (h, item 10). | B5, h, a, b, c, g |
| 3 | 138-149 → 180-193 | §4: item 4's freeze in one order-proof commit, and the review and approval of the manifest's completeness. | B4 |
| 4 | 151-198 → 195-242 | §4: item 2's definition of `x` and `t`, and item 1's classification and serialization bound. Integer and configuration predicates: same outcome only (d). Item 3's coverage and approval of the limits. The examples corrected against the source by file and line (e, items 5 and 6). Item 6's label of the check as exploratory and post hoc. | B2, B1, d, B3, e, B6 |
| 5 | 202-208 → 246-254 | §5: the four `THREAD_VARIABLES`, with source lines, and the three that ID-BEFORE and NR-A1 record (e, item 7). | e |
| 6 | 216-221 → 262-271 | §5: the suggested rule for version 5 onward (f, item 8). | f |
| 7 | 224-238 → 274-289 | §6, criterion 1: (b) adds NR-A2 (a) and drops the tag evidence (g). (c) takes item 3's text. Item 6's label is inserted inside the block. | a, g, B3, B6 |
| 8 | 242-269 → 293-321 | §6: item 5's ID-AFTER provenance rule. NR-A2 runs once after the freeze and the adoption, in place of the alternate-setting tag checks (a, g). Stop 2's pin clause and risk 1 are listed as replaced (j). §7: the open items (a, b). | B5, a, g, j, b |

**No hunk carries only the label `H2`.** Hunk 1 changes the header, which every revision carries.
It is labelled `H2` together with `k` and `i`, the decisions it implements there.

**Not done** (stops of H2): no Codex round, and no adoption. The maintainer adopts by SHA-256 after
the adviser's check. Nothing of the amendment runs:
- the freeze;
- the commit of the raw goldens;
- the manifest;
- the margins;
- NR-A2;
- the sidecar.
