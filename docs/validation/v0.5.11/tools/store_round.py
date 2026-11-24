"""Store review files byte for byte in docs/plans/v0.5.11-consensus/ (the consensus record).

    .venv/Scripts/python.exe -I -B docs/validation/v0.5.11/tools/store_round.py SRC=NAME ...

Each SRC is a file under .cache/v0511/; NAME is the file name in the consensus folder. It refuses
an existing destination, copies the bytes, checks the SHA-256 of the copy against the source,
and prints one JSON line per file (name, bytes, SHA-256, match, CR count, BOM).
"""

import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SRC_ROOT = (ROOT / ".cache" / "v0511").resolve()
DST = ROOT / "docs" / "plans" / "v0.5.11-consensus"


def main() -> int:
    ok = True
    for pair in sys.argv[1:]:
        src_rel, name = pair.split("=", 1)
        src = (ROOT / src_rel).resolve()
        if SRC_ROOT not in src.parents or "/" in name or "\\" in name:
            raise SystemExit(f"refused: {pair}")
        dst = DST / name
        if dst.exists():
            raise SystemExit(f"refused: {dst} exists")
        shutil.copyfile(src, dst)
        b = src.read_bytes()
        a, c = hashlib.sha256(b).hexdigest(), hashlib.sha256(dst.read_bytes()).hexdigest()
        ok = ok and a == c
        row = {
            "file": name,
            "bytes": len(b),
            "sha256": a,
            "match": a == c,
            "cr": b.count(b"\r"),
            "bom": b.startswith(b"\xef\xbb\xbf"),
        }
        print(json.dumps(row))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
