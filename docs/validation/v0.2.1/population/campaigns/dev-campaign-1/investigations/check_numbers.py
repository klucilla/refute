"""Compare the numbers of a Portuguese record and of its English translation (read-only).

Every numeric token of both Markdown files is collected as written, after these steps: in the
Portuguese file a decimal comma between two digits becomes a point (except in the notation
N(a,b) of a normal distribution, as in N(0,1)); in the English file the
text between the markers <!-- translation-note --> and <!-- /translation-note --> (added in
translation, not in the Portuguese record) is removed; in both files, SHA-256 and git hashes
(40 or 64 hexadecimal characters) are removed. A digit glued to a letter, an underscore or a
point (dev1, c3_inconclusive, T14, v0.2.1) is not a token. The two multisets must be equal.

Usage: python check_numbers.py PORTUGUESE.md ENGLISH.md
Exit status 0 if the numbers are identical, 1 otherwise; the differences are printed with the
first line where each one appears.
"""

from __future__ import annotations

import collections
import re
import sys
from pathlib import Path

NUM = re.compile(r"(?<![\w.])-?\d+(?:\.\d+)?(?:e[-+]\d+)?")
DECIMAL_COMMA = re.compile(r"(?<!N\(\d)(?<=\d),(?=\d)")
HASH = re.compile(r"\b[0-9a-f]{40}(?:[0-9a-f]{24})?\b")
NOTE = re.compile(r"<!-- translation-note -->.*?<!-- /translation-note -->", re.DOTALL)


def tokens(text: str) -> collections.Counter:
    return collections.Counter(NUM.findall(HASH.sub(" ", text)))


def where(text: str, tok: str) -> str:
    for n, line in enumerate(text.splitlines(), 1):
        if tok in NUM.findall(HASH.sub(" ", line)):
            return f"line {n}: {line.strip()[:120]}"
    return "?"


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    pt = DECIMAL_COMMA.sub(".", Path(sys.argv[1]).read_text(encoding="utf-8"))
    en_full = Path(sys.argv[2]).read_text(encoding="utf-8")
    en = NOTE.sub(" ", en_full)
    a, b = tokens(pt), tokens(en)
    print(f"tokens: Portuguese {sum(a.values())}, English {sum(b.values())}")
    print(f"translation notes removed: {len(NOTE.findall(en_full))}")
    only_pt, only_en = a - b, b - a
    for name, diff, text in (("only in Portuguese", only_pt, pt), ("only in English", only_en, en)):
        for tok, n in sorted(diff.items()):
            print(f"{name}: {tok!r} x{n} ({where(text, tok)})")
    same = not only_pt and not only_en
    print("numbers identical" if same else "numbers DIFFER")
    return 0 if same else 1


if __name__ == "__main__":
    sys.exit(main())
