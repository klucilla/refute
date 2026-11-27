"""The deterministic check of amendment 2, revision 8 (the maintainer's decision Q2, #218 comment
7226143268).

    unit rev8-check:  {python} -I -B docs/validation/v0.5.13/tools/rev8_check.py

It reads only committed or working-tree text files of the repository. Offline. It prints one JSON
object and exits 1 if any check fails.

1. The third blind review's answer and revision 7 have the SHA-256 the record gives them.
2. **Replacement texts.** The replacement texts are the blockquotes of section 2 of the answer
   (``## 2. Blocking items`` to ``## 3.``); there must be exactly five (item 4 has two). Each
   must appear in revision 8 word for word, after the same normalization of both texts: on every
   line, leading whitespace and quote prefixes (``>``) are removed, then all whitespace runs, line
   breaks included, become one space. Nothing else is normalized. Item 3's text is an insertion
   "after the bullets of item 1", so it must follow item 1's text directly.
3. **Replaced passages.** They are cut from revision 7 by the line ranges the answer cites
   (checked against an anchor at each range), never retyped. Each must be present in revision 7
   and absent from revision 8, under the same normalization.
4. **Cited text kept.** The strings that the replacement texts quote from the rest of the
   amendment are still in revision 8.
5. **Decisions** (a) to (k) of Q2, each by the words that carry it; (g) also reads the new
   correction file. (k): no abbreviated hash in revision 8, its README, the result README or the
   correction file: every run of 7 or more hex characters that holds both a digit and a letter a
   to f is 40 or 64 characters long. Revision 8 has one banner "PROPOSED, not approved".
6. **The diff and the map.** The committed patch equals a fresh unified diff (3 lines of context)
   of revision 7 against revision 8, byte for byte, in the format of ``rev_diff.py``. Every hunk
   has at least one label, every label is a blocking item ``B1`` to ``B4`` or a decision ``a`` to
   ``k`` of Q2, and the map names no hunk the patch does not have.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
ANSWER = "docs/plans/v0.5.13-amendment-2-blind-review-3-result/answer.md"
ANSWER_SHA = "36a47ebc53d423ff26c4db7a7d71050cbb9cdcf8a07e12d4961ca78e60bc6898"
REV7 = "docs/plans/v0.5.13-charter-amendment-2-rev7.md"
REV7_SHA = "eb320426b194da7195b9e5131ead295940d11ea06dcc5265ff8645d74393a5b5"
REV8 = "docs/plans/v0.5.13-charter-amendment-2-rev8.md"
PATCH = "docs/plans/v0.5.13-amendment-2-rev8/rev7-to-rev8.patch"
MAP = "docs/plans/v0.5.13-amendment-2-rev8/hunk-map.json"
README8 = "docs/plans/v0.5.13-amendment-2-rev8/README.md"
RESULT_README = "docs/plans/v0.5.13-amendment-2-blind-review-3-result/README.md"
CORRECTION = "docs/validation/v0.5.13/correction-2026-11-27-numerical-environment.md"
SIDECAR_SHA = "d4717097a8943c82b745613dd29b205f738d1d03f9ac2dd973ab21e1d753d485"
LABELS = {"B1", "B2", "B3", "B4"} | set("abcdefghijk")

# The answer's citations of revision 7 (1-based, inclusive), each with the start of its first
# line as an anchor.
PASSAGES = [
    ("B1", 241, 246, "- **What still holds for versions 1 to 4.**"),
    ("B2", 426, 430, "- **A freeze commit made under revision 6**"),
    ("B4", 116, 118, "  - Its counts: 2 to 9 assessable rows"),
    ("B4", 233, 235, "- **The reason.** The goldens of versions 1 to 4"),
]

# Strings that the replacement texts quote from the rest of the amendment.
CITED = [
    "The open items under revision 7",
    "Blind review, item 6, as written",
    "or assessable margin check",
    "The absent-operand allowance in §4 applies only to the margin check",
    "The independent margin check separately requires clearance from the decision cutoffs",
    "(sections 3, 4 and 6)",
]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize(text: str) -> str:
    lines = [re.sub(r"^[\s>]*", "", ln) for ln in text.split("\n")]
    return re.sub(r"\s+", " ", " ".join(lines)).strip()


def section(text: str, start: str, end: str) -> str:
    return text.split(start, 1)[1].split(end, 1)[0]


def abbreviated(text: str) -> list[str]:
    runs = re.findall(r"(?<![0-9a-fA-F])[0-9a-fA-F]{7,}(?![0-9a-fA-F])", text)
    return sorted({r for r in runs if re.search(r"\d", r) and re.search(r"[a-fA-F]", r)
                   and len(r) not in (40, 64)})  # fmt: skip


def main() -> int:
    problems: list[str] = []
    answer_b = (ROOT / ANSWER).read_bytes()
    rev7_b = (ROOT / REV7).read_bytes()
    rev8_b = (ROOT / REV8).read_bytes()
    if sha(answer_b) != ANSWER_SHA:
        problems.append("answer.md SHA-256 differs from the record")
    if sha(rev7_b) != REV7_SHA:
        problems.append("revision 7 SHA-256 differs from the record")
    answer, rev7, rev8 = (b.decode("utf-8") for b in (answer_b, rev7_b, rev8_b))
    n7, n8 = normalize(rev7), normalize(rev8)

    # 2. the replacement texts
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in section(answer, "## 2. Blocking items", "\n## 3.").split("\n"):
        if line.startswith(">"):
            current.append(line)
        elif current:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)
    if len(blocks) != 5:
        problems.append(f"expected 5 replacement blocks in the answer, found {len(blocks)}")
    norm_blocks = [normalize("\n".join(b)) for b in blocks]
    replacements = []
    for i, norm in enumerate(norm_blocks, 1):
        found = norm in n8
        replacements.append({"block": i, "first_words": norm[:60], "in_rev8": found})
        if not found:
            problems.append(f"replacement block {i} is not in revision 8 word for word")
    b3_after_b1 = len(norm_blocks) >= 3 and f"{norm_blocks[0]} {norm_blocks[2]}" in n8
    if not b3_after_b1:
        problems.append("item 3's text does not directly follow item 1's text")

    # 3. the replaced passages
    rev7_lines = rev7.split("\n")
    passages = []
    for item, first, last, anchor in PASSAGES:
        cut = rev7_lines[first - 1 : last]
        if not cut[0].startswith(anchor):
            problems.append(f"{item}: revision 7 line {first} does not start with its anchor")
        norm = normalize("\n".join(cut))
        in7, in8 = norm in n7, norm in n8
        passages.append({"item": item, "rev7_lines": f"{first}-{last}", "in_rev7": in7,
                         "in_rev8": in8})  # fmt: skip
        if not in7 or in8:
            problems.append(f"{item}: passage at revision 7 lines {first}-{last} is not replaced")

    # 4. the cited text kept
    cited = {c: c in n8 for c in CITED}
    problems += [f"cited text missing from revision 8: {c!r}" for c, ok in cited.items() if not ok]

    # 5. the decisions
    # Each section and the correction are normalized as in check 2, so a line break never matters.
    s1 = normalize(section(rev8, "\n## 1. ", "\n## 2. "))
    s31 = normalize(section(rev8, "\n### 3.1 ", "\n### 3.2 "))
    s5 = normalize(section(rev8, "\n## 5. ", "\n## 6. "))
    s7 = normalize(rev8.split("\n## 7. ", 1)[1])
    correction = normalize((ROOT / CORRECTION).read_text(encoding="utf-8"))
    decisions = {
        "a_amendments_3_4": "Amendments 3 and 4 do not change" in n8
        and "that reference is read as the adopted revision of amendment 2" in n8,
        "b_p2_described": all(
            s in s1
            for s in (
                "Decision P2: the comparator was corrected after Codex's round",
                "So the comparator before P2 was in that freeze, by hash.",
                "Codex has not reviewed them",
                "It read no golden file, before or after the correction.",
            )
        )
        and "a75e1a43d4933322f988b26b7ef7978800b899dc8cd588c00f9d5ee1e290493a" in s1,
        "c_n1c_defined": "**N1(c)** (decision Q2(c))" in s1 and "With decision P1 it has no" in s1,
        "d_in_section_1": "The result of criterion (b) is foreseeable from D1a." in s1
        and "NR-A2 (criterion (c)) is the only condition whose result is unknown." in s1,
        "e_serializes": "serializes in its outputs" in s5
        and "version 5 records, before any lock" not in n8
        and "Decision H2(f) above is the alternative" in s5,
        "f_coverage": "the files compared, the numeric tokens compared, the numeric tokens that "
        "differ, and the largest relative difference" in s31,
        "g_correction": SIDECAR_SHA in correction
        and "(amendment 2, sections 3 and 4)" in correction
        and "takes effect when the maintainer adopts amendment 2, revision 8" in correction,
        "h_outdated_gone": "They stay valid under revision 5," not in n8
        and "The two bullets above" not in n8
        and "exists only once the margin manifest is built" not in n8
        and "The four bullets above" in s7,
        "i_reach_rule": "it is fixed before that version's margin manifest is built" in s5,
        "j_marked": "(Q2(j))" in rev8,
        "one_banner": rev8.count("PROPOSED, not approved") == 1,
    }
    for mark in "abcdefghik":
        decisions[f"mark_Q2({mark})"] = f"Q2({mark})" in rev8
    short = {}
    for path in (REV8, README8, RESULT_README, CORRECTION):
        found = abbreviated((ROOT / path).read_text(encoding="utf-8"))
        if found:
            short[path] = found
    decisions["k_no_abbreviated_hash"] = not short
    problems += [f"decision check failed: {k}" for k, v in decisions.items() if not v]

    # 6. the diff and the map
    fresh = "".join(difflib.unified_diff(rev7.splitlines(True), rev8.splitlines(True),
                                         f"a/{REV7}", f"b/{REV8}", n=3))  # fmt: skip
    patch_b = (ROOT / PATCH).read_bytes()
    if patch_b != fresh.encode("utf-8"):
        problems.append("the committed patch differs from a fresh diff of revisions 7 and 8")
    patch = patch_b.decode("utf-8")
    hunks = len(re.findall(r"^@@ ", patch, flags=re.MULTILINE))
    mapping = json.loads((ROOT / MAP).read_text(encoding="utf-8"))
    for i in range(1, hunks + 1):
        labels = mapping.get(str(i), [])
        if not labels:
            problems.append(f"hunk {i} has no label")
        problems += [f"hunk {i}: label {x!r} is not B1-B4 or a-k" for x in labels
                     if x not in LABELS]  # fmt: skip
    problems += [f"the map names hunk {k}, which the patch does not have"
                 for k in mapping if not k.isdigit() or not 1 <= int(k) <= hunks]  # fmt: skip

    print(json.dumps({
        "answer_sha256": sha(answer_b), "rev7_sha256": sha(rev7_b), "rev8_sha256": sha(rev8_b),
        "patch_sha256": sha(patch_b), "hunks": hunks, "replacements": replacements,
        "b3_directly_after_b1": b3_after_b1, "passages": passages, "cited_text_kept": cited,
        "decisions": decisions, "abbreviated_hashes": short,
        "problems": problems, "result": "PASS" if not problems else "FAIL",
    }, indent=1, ensure_ascii=False))  # fmt: skip
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
