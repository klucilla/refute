"""The deterministic check of amendment 2, revision 6 (the maintainer's decision K2, #218 comment
7223240289).

    unit rev6-check:  {python} -I -B docs/validation/v0.5.13/tools/rev6_check.py

It reads only committed or working-tree text files of the repository. Offline. It prints one JSON
object and exits 1 if any check fails.

1. The blind review's answer and revision 5 have the SHA-256 the record gives them.
2. **Replacement texts.** The replacement texts are the blockquotes of section 2 of the answer
   (``## 2. Blocking items`` to ``## 3.``); there must be exactly six. Each must appear in
   revision 6 word for word, after the same normalization of both texts: on every line, leading
   whitespace and quote prefixes (``>``) are removed, then all whitespace runs, line breaks
   included, become one space. Nothing else is normalized.
3. **Replaced passages.** They are cut from revision 5 by the line ranges the answer cites
   (checked against an anchor at each range), never retyped. Each must be present in revision 5
   and absent from revision 6, under the same normalization.
4. **Decisions.** (b) "so it is a floor" is gone and the maintainer's words "not a bound on the
   number of manifest rows in either direction" are present. (d) "PROPOSED, not approved" occurs
   once, and revision 4's header is gone. (g) "peak is None" is present. (c), (e), (f) and (g)
   each have their mark "K2(x)". (i) No abbreviated hash: every run of 7 or more hex characters
   that holds both a digit and a letter a to f is 40 or 64 characters long.
5. **The diff and the map.** The committed patch equals a fresh unified diff (3 lines of context)
   of revision 5 against revision 6, byte for byte, in the format of ``rev_diff.py``. Every hunk
   has at least one label, every label is a blocking item ``B1`` to ``B4`` or a decision ``a`` to
   ``i`` of K2, and the map names no hunk the patch does not have.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
ANSWER = "docs/plans/v0.5.13-amendment-2-blind-review-2-result/answer.md"
ANSWER_SHA = "7f71b206d7efbc1afef2ce62d14cb8483365b2ac04ed12752007c1f63f70114a"
REV5 = "docs/plans/v0.5.13-charter-amendment-2-rev5.md"
REV5_SHA = "c69b23e9074477bb481638f39577ac98eaed549e9e00271478900d944235518b"
REV6 = "docs/plans/v0.5.13-charter-amendment-2-rev6.md"
PATCH = "docs/plans/v0.5.13-amendment-2-rev6/rev5-to-rev6.patch"
MAP = "docs/plans/v0.5.13-amendment-2-rev6/hunk-map.json"
LABELS = {"B1", "B2", "B3", "B4"} | set("abcdefghi")

# The answer's citations of revision 5 (1-based, inclusive), each with the start of its first
# line as an anchor, and, for a part of a line, the substring the passage starts with and the
# one it ends with.
PASSAGES = [
    ("B1", 202, 202, "> The margin manifest covers the decision layer", None, None),
    ("B2", 230, 231, "**Examples known from the source", None, None),
    ("B2", 241, 245, "  - Whether each saved verdict records", None, None),
    ("B3", 300, 300, "> - **(c)**", "Its list of absent operands", None),
    ("B3", 304, 304, "> Wherever #226 is cited", "it carries the label", "N from the margin"),
    ("B4", 334, 340, "- None of these exists yet:", None, None),
]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize(text: str) -> str:
    lines = [re.sub(r"^[\s>]*", "", ln) for ln in text.split("\n")]
    return re.sub(r"\s+", " ", " ".join(lines)).strip()


def main() -> int:
    problems: list[str] = []
    answer_b = (ROOT / ANSWER).read_bytes()
    rev5_b = (ROOT / REV5).read_bytes()
    rev6_b = (ROOT / REV6).read_bytes()
    if sha(answer_b) != ANSWER_SHA:
        problems.append("answer.md SHA-256 differs from the record")
    if sha(rev5_b) != REV5_SHA:
        problems.append("revision 5 SHA-256 differs from the record")
    answer, rev5, rev6 = (b.decode("utf-8") for b in (answer_b, rev5_b, rev6_b))
    n5, n6 = normalize(rev5), normalize(rev6)

    # 2. the replacement texts
    section = answer.split("## 2. Blocking items", 1)[1].split("\n## 3.", 1)[0]
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in section.split("\n"):
        if line.startswith(">"):
            current.append(line)
        elif current:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)
    if len(blocks) != 6:
        problems.append(f"expected 6 replacement blocks in the answer, found {len(blocks)}")
    replacements = []
    for i, block in enumerate(blocks, 1):
        found = normalize("\n".join(block)) in n6
        replacements.append({"block": i, "first_words": normalize(block[0])[:60], "in_rev6": found})
        if not found:
            problems.append(f"replacement block {i} is not in revision 6 word for word")

    # 3. the replaced passages
    rev5_lines = rev5.split("\n")
    passages = []
    for item, first, last, anchor, start, end in PASSAGES:
        cut = rev5_lines[first - 1 : last]
        if not cut[0].startswith(anchor):
            problems.append(f"{item}: revision 5 line {first} does not start with its anchor")
        text = "\n".join(cut)
        if start is not None:
            text = text[text.index(start) :]
        if end is not None:
            text = text[: text.index(end) + len(end)]
        norm = normalize(text)
        in5, in6 = norm in n5, norm in n6
        passages.append({"item": item, "rev5_lines": f"{first}-{last}", "in_rev5": in5,
                         "in_rev6": in6})  # fmt: skip
        if not in5 or in6:
            problems.append(f"{item}: passage at revision 5 lines {first}-{last} is not replaced")

    # 4. the decisions
    decisions = {
        "b_floor_gone": "so it is a floor" not in n6,
        "b_new_words": "not a bound on the number of manifest rows in either direction" in n6,
        "d_one_banner": rev6.count("PROPOSED, not approved") == 1,
        "d_rev4_header_gone": "Revision 4's own header follows" not in rev6,
        "g_peak_is_none": "peak is None" in rev6,
    }
    for mark in ("K2(b)", "K2(c)", "K2(d)", "K2(e)", "K2(f)", "K2(g)"):
        decisions[f"mark_{mark}"] = mark in rev6
    runs = re.findall(r"(?<![0-9a-fA-F])[0-9a-fA-F]{7,}(?![0-9a-fA-F])", rev6)
    abbreviated = sorted({r for r in runs if re.search(r"\d", r) and re.search(r"[a-fA-F]", r)
                          and len(r) not in (40, 64)})  # fmt: skip
    decisions["i_no_abbreviated_hash"] = not abbreviated
    problems += [f"decision check failed: {k}" for k, v in decisions.items() if not v]

    # 5. the diff and the map
    fresh = "".join(difflib.unified_diff(rev5.splitlines(True), rev6.splitlines(True),
                                         f"a/{REV5}", f"b/{REV6}", n=3))  # fmt: skip
    patch_b = (ROOT / PATCH).read_bytes()
    if patch_b != fresh.encode("utf-8"):
        problems.append("the committed patch differs from a fresh diff of revision 5 and 6")
    patch = patch_b.decode("utf-8")
    hunks = len(re.findall(r"^@@ ", patch, flags=re.MULTILINE))
    mapping = json.loads((ROOT / MAP).read_text(encoding="utf-8"))
    for i in range(1, hunks + 1):
        labels = mapping.get(str(i), [])
        if not labels:
            problems.append(f"hunk {i} has no label")
        problems += [f"hunk {i}: label {x!r} is not B1-B4 or a-i" for x in labels
                     if x not in LABELS]  # fmt: skip
    problems += [f"the map names hunk {k}, which the patch does not have"
                 for k in mapping if not k.isdigit() or not 1 <= int(k) <= hunks]  # fmt: skip

    print(json.dumps({
        "answer_sha256": sha(answer_b), "rev5_sha256": sha(rev5_b), "rev6_sha256": sha(rev6_b),
        "patch_sha256": sha(patch_b), "hunks": hunks, "replacements": replacements,
        "passages": passages, "decisions": decisions, "abbreviated_hashes": abbreviated,
        "problems": problems, "result": "PASS" if not problems else "FAIL",
    }, indent=1))  # fmt: skip
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
