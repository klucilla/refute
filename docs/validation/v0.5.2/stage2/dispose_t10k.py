"""Record the counts of the two downloaded T10K tables and delete the copies from ``.cache``, by the
maintainer's decision of 2026-11-09 (#216, item 4): the catalog adds no star to T3b.

Each file's SHA-256 is checked against ``t10k-fetch.json`` first. Deletion is by literal path
only, inside ``.cache/v052/t10k``, and refuses links and junctions. ``t10k-disposition.json`` holds
counts, hashes, relative paths and sizes, and no line of the catalog. ``fetch_t10k.py`` can fetch
the same bytes again, checked by the SHA-256, if the frame's step ever needs them.

Usage (from the project root): ``.venv/Scripts/python.exe <this file>``.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BASE = ROOT / ".cache" / "v052" / "t10k"
FILES = {
    "table3": ".cache/v052/t10k/e197c05c167225bf9d5ca1bb3a5b9e672d76b9b938168b7a44c7382768fd0fb6/apjsade2d8t3_mrt.txt",  # noqa: E501
    "table4": ".cache/v052/t10k/f5f27c251f53216492fbe0db9c3788d7fc20752c09c9d81ab7ae9099a9331493/apjsade2d8t4_mrt.txt",  # noqa: E501
}  # fmt: skip


def guarded(path: Path) -> Path:
    """The path, if it and every parent up to the project's root are plain, inside ``BASE``."""
    if BASE not in path.parents and path != BASE:
        raise SystemExit("refused: outside the T10K folder")
    for item in (path, *path.parents):
        if item == ROOT:
            return path
        if item.is_symlink() or item.is_junction():
            raise SystemExit("refused: a link or junction on the path")
    raise SystemExit("refused: outside the project")


def main() -> None:
    fetched = json.loads((HERE / "t10k-fetch.json").read_text("utf-8"))["files"]
    rows: dict = {}
    every: set[int] = set()
    for key, rel in FILES.items():
        path = guarded(ROOT / rel)
        data = path.read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        if sha != fetched[key]["sha256"] or len(data) != fetched[key]["bytes"]:
            raise SystemExit(f"{key}: bytes differ from the fetch record")
        tics = {
            int(line[:10])
            for line in data.decode("utf-8").splitlines()
            if line[:10].strip().isdigit()
        }
        every |= tics
        rows[key] = {"path": rel, "bytes": len(data), "sha256": sha, "distinct_tic": len(tics)}
    doc = {
        "label": "T10K's tables 3 and 4: counts and hashes; the copies were deleted (#216, item 4)",
        "license_state": "unconfirmed: see docs/plans/sources/v0.5.2-t10k-2026-11-08.md",
        "distinct_tic_in_both": len(every),
        "tables": rows,
        "stars_added_to_t3b": "0: t3b-inventory.json and t3b-inventory-r2.json",
    }
    (HERE / "t10k-disposition.json").write_text(
        json.dumps(doc, indent=1, sort_keys=True) + "\n", "utf-8"
    )
    for rel in FILES.values():
        path = guarded(ROOT / rel)
        path.unlink()
        guarded(path.parent).rmdir()
        print("deleted", rel, flush=True)
    guarded(BASE).rmdir()
    print(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main()
