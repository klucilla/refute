"""Cleanup of what was left in .cache/v0512 and of the A4/A3 build artifacts (the maintainer's
decision of 2026-11-26, #218, comment 7203695669, item A6).

    .venv/Scripts/python.exe -B docs/maintenance/cleanup-2026-11-26-v0512-rest/cleanup.py

- **Archived, then deleted:** every file under .cache/v0512. These are the close maintenance's
  run logs (journaled in docs/validation/v0.5.12/log.jsonl by their hashes), comment and
  commit-message drafts, the launcher's lock file and three site JUnit files. They are logs with
  value, so each is hashed, copied to the Drive
  (K:/Meu Drive/Pessoal/Projetos/refute/cache-archive-2026-11-26-v0512-rest/...) and checked
  there. Nothing is deleted unless every copy matches.
- **Regenerable, deleted without archiving:**
  - .cache/v0513prep/dist/, the A4 wheel and sdist; their hashes and contents are in
    docs/maintenance/package-check-2026-11-26/;
  - .cache/v0513prep/clean-clone/, A3's clean clone with its virtual environment; its timing is
    in docs/STATUS-quickstart-timing.json on the README draft branch.

Deletion is by literal path, under a guard that refuses anything outside those three roots and
any junction. Read-only files (git's objects) are made writable first. The emptied folders are
removed, deepest first. It writes record.json beside this file, and the manifest and this script
to the Drive.
"""

import hashlib
import json
import os
import shutil
import stat
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CACHE = ROOT / ".cache"
ARCHIVE_ROOT = CACHE / "v0512"
REGENERABLE_ROOTS = (CACHE / "v0513prep" / "dist", CACHE / "v0513prep" / "clean-clone")
DRIVE = Path("K:/Meu Drive/Pessoal/Projetos/refute/cache-archive-2026-11-26-v0512-rest")
OUT = Path(__file__).resolve().parent / "record.json"


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def guarded(p: Path) -> Path:
    p = Path(os.path.abspath(p))
    roots = [Path(os.path.abspath(r)) for r in (ARCHIVE_ROOT, *REGENERABLE_ROOTS)]
    if not any(r == p or r in p.parents for r in roots):
        raise SystemExit(f"refused: {p} is outside the three cleanup roots")
    q = p.parent
    while q != CACHE:
        if q.is_symlink() or q.is_junction():
            raise SystemExit(f"refused: a link or junction above {p}")
        q = q.parent
    return p


def files_under(root: Path) -> list[Path]:
    if root.is_symlink() or root.is_junction():
        raise SystemExit(f"refused: {root} is a link or a junction")
    for d in root.rglob("*"):
        if d.is_dir() and d.is_junction():
            raise SystemExit(f"refused: a junction inside {root}: {d}")
    return sorted(p for p in root.rglob("*") if p.is_file() or p.is_symlink())


def remove(p: Path) -> None:
    p = guarded(p)
    if not p.is_symlink() and not os.access(p, os.W_OK):
        os.chmod(p, stat.S_IWRITE | stat.S_IREAD)
    p.unlink()


def main() -> int:
    if CACHE.is_symlink() or CACHE.is_junction():
        raise SystemExit("refused: .cache is a link or a junction")
    archived = []
    for p in files_under(ARCHIVE_ROOT):
        src = guarded(p)
        rel = p.relative_to(CACHE).as_posix()
        dst = DRIVE / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        a, b = sha(src), sha(dst)
        archived.append({"path": ".cache/" + rel, "bytes": src.stat().st_size, "sha256": a,
                         "destination_sha256": b, "match": a == b})  # fmt: skip
    if not archived or not all(r["match"] for r in archived):
        raise SystemExit("refused: nothing to archive, or a Drive copy does not match")
    dropped = []
    for root in REGENERABLE_ROOTS:
        if root.exists():
            for p in files_under(root):
                dropped.append({"path": p.relative_to(ROOT).as_posix(), "bytes": p.lstat().st_size})
    for r in archived:
        p = guarded(ROOT / r["path"])
        if sha(p) != r["sha256"]:
            raise SystemExit(f"refused: {r['path']} changed")
        remove(p)
        r["status"] = "deleted, archived"
    for r in dropped:
        remove(ROOT / r["path"])
    removed = []
    for root in (ARCHIVE_ROOT, *REGENERABLE_ROOTS):
        if not root.exists():
            continue
        dirs = sorted((p for p in root.rglob("*") if p.is_dir()), key=lambda p: -len(p.parts))
        for d in [*dirs, root]:
            d = guarded(d)
            if not any(d.iterdir()):
                d.rmdir()
                removed.append(d.relative_to(ROOT).as_posix() + "/")
    by_root: dict[str, list[int]] = {}
    for r in dropped:
        key = "/".join(r["path"].split("/")[:3])
        by_root.setdefault(key, [0, 0])
        by_root[key][0] += 1
        by_root[key][1] += r["bytes"]
    doc = {
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "decision": "#218, comment 7203695669, item A6",
        "drive": DRIVE.as_posix(),
        "archived_files": len(archived),
        "archived_bytes": sum(r["bytes"] for r in archived),
        "all_match": all(r["match"] for r in archived),
        "regenerable_deleted": {k: {"files": v[0], "bytes": v[1]} for k, v in by_root.items()},
        "folders_removed": len(removed),
        "archived": archived,
    }
    OUT.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    (DRIVE / "MANIFEST-sha256.json").write_text(json.dumps(doc, indent=1) + "\n", "utf-8")
    shutil.copyfile(Path(__file__), DRIVE / "cleanup.py")
    keys = ("archived_files", "archived_bytes", "all_match", "regenerable_deleted")
    print(json.dumps({k: doc[k] for k in keys}))
    print("folders removed:", len(removed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
