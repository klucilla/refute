"""The cleanup of .cache/r1124f (the maintainer's instruction of 2026-11-24 with the approval of
the v0.5.11 charter, #218 comment 7146858167): the working folder of the stop that proposed the
charter (commit messages, comment drafts, helper scripts).

    .venv/Scripts/python.exe -I -B docs/maintenance/cleanup-2026-11-25-r1124f/cleanup.py

Every file is hashed, copied to the Drive
(K:/Meu Drive/Pessoal/Projetos/refute/cache-archive-2026-11-25-r1124f/r1124f/...) and checked
there. Only if every copy matches are the files deleted, by literal path, with a guard that
refuses anything outside the folder and any link or junction from .cache down; then the empty
folders are removed. Writes record.json here.
"""

import hashlib
import json
import os
import shutil
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CACHE = ROOT / ".cache"
FOLDER = "r1124f"
DRIVE = Path("K:/Meu Drive/Pessoal/Projetos/refute/cache-archive-2026-11-25-r1124f")
OUT = Path(__file__).resolve().parent / "record.json"


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
        "decision": "#218, comment 7146858167 (the instruction with the charter's approval)",
        "drive": DRIVE.as_posix(),
        "files": len(rows),
        "bytes": sum(r["bytes"] for r in rows),
        "all_match": all(r["match"] for r in rows),
        "folders_removed": removed,
        "rows": rows,
    }
    OUT.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    (DRIVE / "MANIFEST-sha256.json").write_text(json.dumps(doc, indent=1) + "\n", "utf-8")
    shutil.copyfile(Path(__file__), DRIVE / "cleanup.py")
    print(json.dumps({k: doc[k] for k in ("files", "bytes", "all_match", "folders_removed")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
