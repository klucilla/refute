"""The cleanup of .cache/r1124d (the maintainer's decision of 2026-11-24 received at 18:59 local,
#218 comment 7145663950, item 2): the working folder of the v0.5.10 closing stop (the commit
messages of the closing cleanup and of the site draft, and the two helper scripts that edited the
site's draft branch).

Run once from the project's virtual environment:

    .venv/Scripts/python.exe docs/validation/v0.5.10/cleanup/cleanup_r1124d.py

Every file is hashed, copied to the Drive
(K:/Meu Drive/Pessoal/Projetos/refute/cache-archive-2026-11-24-v0510-r1124d/r1124d/...) and checked
there. Only if every copy matches are the files deleted, by literal path, with a guard that refuses
anything outside the folder and any link or junction from .cache down; then the empty folder is
removed.

Writes r1124d-record.json here: the files with their SHA-256, the Drive copies and the deletions.
"""

import hashlib
import json
import os
import shutil
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
CACHE = ROOT / ".cache"
FOLDER = "r1124d"
DRIVE = Path("K:/Meu Drive/Pessoal/Projetos/refute/cache-archive-2026-11-24-v0510-r1124d")
OUT = Path(__file__).resolve().parent / "r1124d-record.json"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def guarded(p: Path) -> Path:
    p = Path(os.path.abspath(p))
    if Path(os.path.abspath(CACHE / FOLDER)) not in p.parents:
        raise SystemExit(f"refused: {p} is outside the folder")
    q = p
    while q != CACHE:
        if q.is_symlink() or q.is_junction():
            raise SystemExit(f"refused: a link or junction on {p}")
        q = q.parent
    return p


def main() -> int:
    if CACHE.is_symlink() or CACHE.is_junction():
        raise SystemExit("refused: .cache is a link or a junction")
    base = CACHE / FOLDER
    if base.is_symlink() or base.is_junction():
        raise SystemExit(f"refused: {base} is a link or a junction")
    rows = []
    for p in sorted(base.rglob("*")):
        if p.is_symlink() or p.is_junction():
            raise SystemExit(f"refused: a link or junction at {p}")
        if p.is_file():
            src = guarded(p)
            rel = src.relative_to(CACHE).as_posix()
            dst = DRIVE / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
            a, b = sha(src), sha(dst)
            rows.append(
                {
                    "path": ".cache/" + rel,
                    "bytes": src.stat().st_size,
                    "sha256": a,
                    "destination_sha256": b,
                    "match": a == b,
                }
            )
    if not rows:
        raise SystemExit("refused: no file found; nothing deleted")
    if not all(r["match"] for r in rows):
        raise SystemExit("refused: a Drive copy does not match; nothing deleted")
    for r in rows:
        p = guarded(ROOT / r["path"])
        if sha(p) != r["sha256"]:
            raise SystemExit(f"refused: {r['path']} changed")
        p.unlink()
        r["status"] = "deleted, archived"
    for d in sorted((d for d in base.rglob("*") if d.is_dir()), key=lambda d: -len(d.parts)):
        if not any(d.iterdir()):
            d.rmdir()
    removed = []
    if base.exists() and not any(base.iterdir()):
        base.rmdir()
        removed.append(".cache/" + FOLDER + "/")
    doc = {
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "decision": "#218, comment 7145663950, item 2",
        "drive": DRIVE.as_posix(),
        "files": len(rows),
        "bytes": sum(r["bytes"] for r in rows),
        "all_match": all(r["match"] for r in rows),
        "folders_removed": removed,
        "rows": rows,
    }
    OUT.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    (DRIVE / "MANIFEST-sha256.json").write_text(json.dumps(doc, indent=1) + "\n", "utf-8")
    shutil.copyfile(Path(__file__), DRIVE / "cleanup_r1124d.py")
    print(json.dumps({k: doc[k] for k in ("files", "bytes", "all_match", "folders_removed")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
