"""Check the deterministic condition of the amendment of 2026-11-24 to the v0.5.10 charter.

The maintainer's decision of 2026-11-24 received at 14:46 local (#218, comment 7139692729,
item 1) approves the amendment in the commit that adds it, if the diff of the charter adds only
the dated amendment. This script checks that the charter at the given commit (default: the
working tree) is the charter at the approved commit b71fa48, byte for byte, followed only by the
appended section "## 9. Amendment of 2026-11-24", and that the section is the last one.

Usage: python check_amendment_diff.py [commit]
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

CHARTER = "docs/plans/v0.5.10-charter.md"
BASE = "b71fa48c8dd4ef176d52f0bcc8c6688156512678"
HEADING = b"\n## 9. Amendment of 2026-11-24: a named rerun in part (f)\n"


def show(commit: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{commit}:{CHARTER}"], check=True, capture_output=True
    ).stdout


def main() -> int:
    old = show(BASE)
    if len(sys.argv) > 1:
        new = show(sys.argv[1])
    else:
        new = Path(CHARTER).read_bytes()
    problems = []
    if not new.startswith(old):
        problems.append("the approved charter is not an unchanged prefix of the new one")
    added = new[len(old) :]
    if not added.startswith(HEADING):
        problems.append("the added text does not start with the amendment's heading")
    if added.count(b"\n## ") != 1:
        problems.append("the added text holds more than the one amendment section")
    print(f"base {BASE}: {len(old)} bytes; new: {len(new)} bytes; added: {len(added)} bytes")
    if problems:
        for p in problems:
            print("FAILS:", p)
        return 1
    print("condition holds: the diff adds only the dated amendment (section 9)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
