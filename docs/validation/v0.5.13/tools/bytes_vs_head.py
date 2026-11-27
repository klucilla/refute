"""Compare the working-tree bytes of tracked files with their blobs at HEAD (v0.5.13; the unit
``bytes-vs-head``). Read only; it prints no content.

    unit bytes-vs-head:  {python} -I -B docs/validation/v0.5.13/tools/bytes_vs_head.py <paths>

For each path: the size and SHA-256 of the working-tree file, read as raw bytes, and of the blob
``HEAD:<path>`` (``git cat-file blob``, no filter), and whether they are equal. Exit 1 if any
differs. It answers the maintainer's decision L5a (#218 comment 7223634913) after
``git update-index --refresh`` still reported the files as needing an update.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]


def main() -> int:
    rows = []
    for rel in sys.argv[1:]:
        work = (ROOT / rel).read_bytes()
        blob = subprocess.run(["git", "cat-file", "blob", f"HEAD:{rel}"], cwd=ROOT,
                              capture_output=True, check=True).stdout  # fmt: skip
        rows.append({
            "path": rel,
            "work_size": len(work), "work_sha256": hashlib.sha256(work).hexdigest(),
            "head_size": len(blob), "head_sha256": hashlib.sha256(blob).hexdigest(),
            "equal": work == blob,
        })  # fmt: skip
    print(json.dumps(rows, indent=1))
    return 0 if all(r["equal"] for r in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
