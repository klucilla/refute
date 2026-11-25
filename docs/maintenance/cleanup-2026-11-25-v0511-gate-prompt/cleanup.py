"""The cleanup of the full gate prompt's source copy (the maintainer's decision recorded on
2026-11-25 at 14:02 local, #218 comment 7168908914, item 2).

    .venv/Scripts/python.exe -I -B docs/maintenance/cleanup-2026-11-25-v0511-gate-prompt/cleanup.py

The file .cache/v0511/gate-prompt-full/v0.5.11-gate-prompt-full.txt is stored unchanged in git as
docs/gates/v0.5.11-gate-prompt-full.txt, so it is already integrated: it is deleted without
being archived. Before deleting, this script checks three things:
- the source file has the maintainer's SHA-256;
- the blob of that path in HEAD has the same SHA-256;
- no link or junction lies on the path, and the path is inside .cache/v0511/gate-prompt-full.

It then deletes the file by its literal path, removes the emptied folder, and writes record.json
here.
"""

import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CACHE = ROOT / ".cache"
BASE = CACHE / "v0511" / "gate-prompt-full"
SOURCE = BASE / "v0.5.11-gate-prompt-full.txt"
STORED = "docs/gates/v0.5.11-gate-prompt-full.txt"
EXPECTED = "25f0f6a302deac2bcbd824f3f3af153bb6182dca93e896f344c6ac99fee5a5cc"
OUT = Path(__file__).resolve().parent / "record.json"


def guarded(p: Path) -> Path:
    p = Path(os.path.abspath(p))
    if Path(os.path.abspath(BASE)) not in p.parents and p != Path(os.path.abspath(BASE)):
        raise SystemExit(f"refused: {p} is outside .cache/v0511/gate-prompt-full")
    q = p
    while q != CACHE:
        if q.is_symlink() or q.is_junction():
            raise SystemExit(f"refused: a link or junction on {p}")
        q = q.parent
    return p


def main() -> int:
    if CACHE.is_symlink() or CACHE.is_junction():
        raise SystemExit("refused: .cache is a link or a junction")
    src = guarded(SOURCE)
    data = src.read_bytes()
    source_sha = hashlib.sha256(data).hexdigest()
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                          check=True, text=True).stdout.strip()  # fmt: skip
    blob = subprocess.run(["git", "cat-file", "blob", f"HEAD:{STORED}"], cwd=ROOT,
                          capture_output=True, check=True).stdout  # fmt: skip
    blob_sha = hashlib.sha256(blob).hexdigest()
    if source_sha != EXPECTED or blob_sha != EXPECTED:
        raise SystemExit(f"refused: source {source_sha}, HEAD blob {blob_sha}, expected {EXPECTED}")
    others = [p for p in BASE.rglob("*") if p != src]
    if others:
        raise SystemExit(f"refused: unexpected entries under {BASE}: {others}")
    src.unlink()
    base = guarded(BASE)
    base.rmdir()
    doc = {
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "decision": "#218, comment 7168908914, item 2",
        "head": head,
        "stored_as": STORED,
        "rows": [
            {
                "path": SOURCE.relative_to(ROOT).as_posix(),
                "bytes": len(data),
                "sha256": source_sha,
                "head_blob_sha256": blob_sha,
                "match": True,
                "status": "deleted; integrated in git, not archived",
            }
        ],
        "folders_removed": [BASE.relative_to(ROOT).as_posix() + "/"],
    }
    OUT.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"files": 1, "bytes": len(data), "match": True, "head": head}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
