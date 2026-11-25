"""The cleanup of v0.5.11's working folder at the phase's close (the maintainer's decision received
on 2026-11-25 at 11:53 local, #218 comment 7165994585, item 4).

    .venv/Scripts/python.exe -I -B docs/maintenance/cleanup-2026-11-25-v0511-close/cleanup.py

Everything under .cache/v0511 fell out of use when the phase closed. That covers the Codex rounds'
raw events, the JUnit files, the golden outputs, the tag verification, the downloaded papers, the
comment drafts, the ad hoc tools, the run outputs, the site test logs and the gate files, which
are stored in docs/gates/. Two things are kept: the launcher's lock file, and this unit's own run
folder (runs/cleanup-close__*), which the launcher is still writing.

Every file is hashed, copied to the Drive
(K:/Meu Drive/Pessoal/Projetos/refute/cache-archive-2026-11-25-v0511-close/...) and checked
there. Only if every copy matches are the files deleted, by literal path, under a guard that
refuses anything outside .cache/v0511 and any link or junction. The emptied folders are then
removed, deepest first. Writes record.json here.
"""

import hashlib
import json
import os
import shutil
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CACHE = ROOT / ".cache"
BASE = CACHE / "v0511"
DRIVE = Path("K:/Meu Drive/Pessoal/Projetos/refute/cache-archive-2026-11-25-v0511-close")
OUT = Path(__file__).resolve().parent / "record.json"


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def guarded(p: Path) -> Path:
    p = Path(os.path.abspath(p))
    if Path(os.path.abspath(BASE)) not in p.parents:
        raise SystemExit(f"refused: {p} is outside .cache/v0511")
    q = p
    while q != CACHE:
        if q.is_symlink() or q.is_junction():
            raise SystemExit(f"refused: a link or junction on {p}")
        q = q.parent
    return p


def kept(rel: str) -> bool:
    return rel == "v0511/launcher.lock" or rel.startswith("v0511/runs/cleanup-close__")


def main() -> int:
    if CACHE.is_symlink() or CACHE.is_junction() or BASE.is_symlink() or BASE.is_junction():
        raise SystemExit("refused: .cache or .cache/v0511 is a link or a junction")
    files = sorted(p for p in BASE.rglob("*") if p.is_file() or p.is_symlink())
    rows, skipped = [], []
    for p in files:
        rel = p.relative_to(CACHE).as_posix()
        if kept(rel):
            skipped.append(rel)
            continue
        src = guarded(p)
        dst = DRIVE / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        a, b = sha(src), sha(dst)
        rows.append({"path": ".cache/" + rel, "bytes": src.stat().st_size, "sha256": a,
                     "destination_sha256": b, "match": a == b})  # fmt: skip
    if not rows or not all(r["match"] for r in rows):
        raise SystemExit("refused: nothing to delete, or a Drive copy does not match")
    for r in rows:
        p = guarded(ROOT / r["path"])
        if sha(p) != r["sha256"]:
            raise SystemExit(f"refused: {r['path']} changed")
        p.unlink()
        r["status"] = "deleted, archived"
    removed = []
    for d in sorted((p for p in BASE.rglob("*") if p.is_dir()), key=lambda p: -len(p.parts)):
        d = guarded(d)
        if not any(d.iterdir()):
            d.rmdir()
            removed.append(d.relative_to(ROOT).as_posix() + "/")
    doc = {
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "decision": "#218, comment 7165994585, item 4",
        "drive": DRIVE.as_posix(),
        "files": len(rows),
        "bytes": sum(r["bytes"] for r in rows),
        "all_match": all(r["match"] for r in rows),
        "kept": skipped,
        "folders_removed": removed,
        "rows": rows,
    }
    OUT.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    (DRIVE / "MANIFEST-sha256.json").write_text(json.dumps(doc, indent=1) + "\n", "utf-8")
    shutil.copyfile(Path(__file__), DRIVE / "cleanup.py")
    print(json.dumps({k: doc[k] for k in ("files", "bytes", "all_match", "kept")}))
    print("folders removed:", len(removed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
