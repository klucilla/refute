"""The v0.5 baseline for exit criterion 2: the pytest node IDs that pass at the start of v0.5
(tag v0.4.0, commit ad5fd5c), from the JUnit XML of the full suite run in a worktree of that
commit. A node ID is the candidate (scripts/check_test_baseline.py) whose file exists in that
worktree. Usage: make_baseline.py <junit.xml> <worktree> <out.txt>"""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

junit, tree, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
ids = []
for case in ET.parse(junit).getroot().iter("testcase"):
    if {c.tag for c in case} & {"failure", "error", "skipped"}:
        continue
    parts = [p for p in case.get("classname", "").split(".") if p]
    found = None
    for k in range(len(parts)):
        file = "/".join(parts[: k + 1]) + ".py"
        if (tree / file).is_file():
            found = "::".join([file, *parts[k + 1 :], case.get("name", "")])
            break
    if found is None:
        sys.exit(f"no file for {case.get('classname')}::{case.get('name')}")
    ids.append(found)
if len(set(ids)) != len(ids):
    dup = len(ids) - len(set(ids))
    print(f"note: {dup} duplicate node IDs collapsed", file=sys.stderr)
ids = sorted(set(ids))
out.write_text("\n".join(ids) + "\n", encoding="utf-8", newline="\n")
print(len(ids), "passing node IDs")
