"""Read-only survey of the five .cache folders named by the decision of 2026-11-24 (05:07),
item 4: per second-level folder, the file count and bytes; the whole list with SHA-256 goes to
.cache/v059/cleanup2/survey.json."""

import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FOLDERS = ["v052", "v053", "maint1120", "v05", "v055"]
OUT = ROOT / ".cache/v059/cleanup2/survey.json"


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main() -> None:
    with_hash = "--hash" in sys.argv
    files, groups, links = [], defaultdict(lambda: [0, 0]), []
    for name in FOLDERS:
        base = ROOT / ".cache" / name
        for p in base.rglob("*"):
            if p.is_symlink() or p.is_junction():
                links.append(p.relative_to(ROOT).as_posix())
                continue
            if not p.is_file():
                continue
            rel = p.relative_to(ROOT).as_posix()
            parts = p.relative_to(base).parts
            g = f"{name}/{parts[0]}" + ("/" + parts[1] if len(parts) > 2 else "")
            size = p.stat().st_size
            groups[g][0] += 1
            groups[g][1] += size
            files.append({"path": rel, "bytes": size, **({"sha256": sha(p)} if with_hash else {})})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"files": files, "links": links}, indent=1), "utf-8")
    for g, (n, b) in sorted(groups.items()):
        print(f"{g:60s} {n:7d} {b / 1e6:10.1f} MB")
    print("links:", links)
    print("total", len(files), sum(f["bytes"] for f in files) / 1e9, "GB")


main()
