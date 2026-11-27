"""The diff from amendment 2's revision 3 to revision 4, with each hunk tied to its reason (the
maintainer's decision H2, #218 comment 7219469262).

    unit rev-diff:  {python} -I -B docs/validation/v0.5.13/tools/rev_diff.py diff <old> <new> <out>
                    {python} -I -B docs/validation/v0.5.13/tools/rev_diff.py check <patch> <map>

- ``diff``: a unified diff (3 lines of context) of the committed ``<old>`` at ``HEAD`` against the
  working-tree ``<new>``, written to ``<out>``. Hunks are numbered from 1. It prints each hunk's
  number and header, and the SHA-256 of both files and of the patch.
- ``check``: reads the patch and the map (JSON: ``{"<hunk number>": ["B1", ..., "a", ...]}``).
  It requires that every hunk has at least one label, that every label is a blocking item
  ``B1`` to ``B6`` of the blind review or one of the maintainer's decisions ``a`` to ``k``, and
  that the map names no hunk the patch does not have.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
LABELS = {f"B{i}" for i in range(1, 7)} | set("abcdefghijk")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    mode = sys.argv[1]
    if mode == "diff":
        old, new, out = sys.argv[2], sys.argv[3], ROOT / sys.argv[4]
        a = subprocess.run(["git", "show", f"HEAD:{old}"], cwd=ROOT, capture_output=True,
                           check=True).stdout  # fmt: skip
        b = (ROOT / new).read_bytes()
        lines = list(difflib.unified_diff(a.decode("utf-8").splitlines(True),
                                          b.decode("utf-8").splitlines(True),
                                          f"a/{old}", f"b/{new}", n=3))  # fmt: skip
        text = "".join(lines)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(text.encode("utf-8"))
        hunks = [ln for ln in lines if ln.startswith("@@")]
        for i, h in enumerate(hunks, 1):
            print(f"hunk {i}: {h.strip()}")
        summary = {"old_sha256": sha(a), "new_sha256": sha(b),
                   "patch_sha256": sha(text.encode("utf-8")), "hunks": len(hunks)}  # fmt: skip
        print(json.dumps(summary))
        return 0
    if mode == "check":
        patch = (ROOT / sys.argv[2]).read_text(encoding="utf-8")
        mapping = json.loads((ROOT / sys.argv[3]).read_text(encoding="utf-8"))
        n = len(re.findall(r"^@@ ", patch, flags=re.MULTILINE))
        problems = []
        for i in range(1, n + 1):
            labels = mapping.get(str(i), [])
            if not labels:
                problems.append(f"hunk {i} has no label")
            problems += [f"hunk {i}: unknown label {x!r}" for x in labels if x not in LABELS]
        problems += [f"the map names hunk {k}, which the patch does not have"
                     for k in mapping if not k.isdigit() or not 1 <= int(k) <= n]  # fmt: skip
        print(json.dumps({"hunks": n, "labelled": sum(1 for i in range(1, n + 1)
                          if mapping.get(str(i))), "problems": problems}))  # fmt: skip
        return 0 if not problems else 1
    raise SystemExit("mode must be diff or check")


if __name__ == "__main__":
    raise SystemExit(main())
