"""The deterministic condition of the charter's approval (the maintainer's decision of 2026-11-24
received at 12:51 local, #218 comment 7136727624, item 2): the diff of
docs/plans/v0.5.10-charter.md from 654deda to the approved commit adds only part (f), the caps,
the corresponding exit criteria and the approval header.

Check: take the file at the new commit; remove part (f) (from its heading to the line before
"**Data rules.**") and exit criteria 9 and 10; put back the old approval-header block, the old
caps rows and the old caps sentence. The result must equal the file at 654deda byte for byte.
Any other change makes it differ. Usage:

    .venv/Scripts/python.exe docs/validation/v0.5.10/check_charter_diff.py <new commit>
"""

import subprocess
import sys

PATH = "docs/plans/v0.5.10-charter.md"
OLD = "654deda7abf6db24b6c02407d46dd426688c13ae"


def blob(commit: str) -> str:
    out = subprocess.run(["git", "show", f"{commit}:{PATH}"], capture_output=True, check=True)
    return out.stdout.decode("utf-8")


def cut(text: str, start: str, end: str) -> str:
    """Remove from the line that starts with ``start`` up to (not including) ``end``."""
    i = text.index(start)
    j = text.index(end, i)
    return text[:i] + text[j:]


def swap_block(text: str, first: str, last: str, replacement: str) -> str:
    """Replace the lines from the one starting ``first`` through the one starting ``last``."""
    i = text.index(first)
    j = text.index(last, i)
    j = text.index("\n", j) + 1
    return text[:i] + replacement + text[j:]


def main(new: str) -> int:
    old, cur = blob(OLD), blob(new)
    # the old header block (between the title and the "Exploratory" note)
    h0 = old.index("> **A proposal: not approved")
    h1 = old.index(">\n> **Exploratory from start to end.**")
    first = "> **Approved by the maintainer's decision"
    cur = swap_block(cur, first, "> before the work it covers", old[h0:h1])
    cur = cut(cur, "**(f) Engine trial**", "**Data rules.**")
    cur = cut(cur, "9. **The engine trial is run and recorded**", "At the time box's end")
    o0 = old.index("| CPU | 2 CPU-h |")
    o1 = old.index("| Time box |")
    cur = swap_block(cur, "| CPU | 6 CPU-h |", "| Disk peak | 10 GB |", old[o0:o1])
    s0 = old.index("- **Below a cap:**")
    s1 = old.index("- **Reaching a cap:**")
    cur = swap_block(cur, "- **Below a cap:**", "  and the disk peak in the phase log.", old[s0:s1])
    if cur == old:
        print(f"condition holds: {new} adds only part (f), the caps, criteria 9-10 and the header")
        return 0
    for n, (a, b) in enumerate(zip(old.splitlines(), cur.splitlines(), strict=False), 1):
        if a != b:
            print(f"first difference at line {n}:\n  old: {a!r}\n  new: {b!r}")
            break
    print("CONDITION FAILS: the diff holds another change")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
