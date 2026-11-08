"""Archive what fell out of use in ``.cache/v051`` to the Drive, by the maintainer's decision of
2026-11-08 (#216), then delete it by literal path.

Scope (nothing else): the folders ``.cache/v051/accept`` and ``.cache/v051/item3``, and the regular
files directly inside ``.cache/v051`` (the loose logs). Every folder of ``.cache/v051`` other than
those two is left alone.

- ``archive``: copies them to ``K:/Meu Drive/Pessoal/Projetos/refute/v0.5.1-closing-2026-11-08/``,
  hashes source and destination (SHA-256) and writes the manifest to the Drive and next to this
  script. A difference stops the script with nothing deleted.
- ``delete``: re-reads the manifest, re-hashes each destination file against it, and only then
  deletes each source by its literal path; it refuses a path outside ``.cache/v051``, links and
  junctions on the way or inside.

Usage (from the project root): ``.venv/Scripts/python.exe <this file> archive`` then ``delete``.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / ".cache" / "v051"
DRIVE = Path("K:/Meu Drive/Pessoal/Projetos/refute/v0.5.1-closing-2026-11-08")
HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "manifest-2026-11-08.json"
FOLDERS = ("accept", "item3")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def guard(path: Path) -> Path:
    """The path, refused if it is a link or junction, or not strictly inside ``.cache/v051``."""
    base = SRC.resolve()
    for part in [path, *path.parents]:
        if part.is_symlink() or part.is_junction():
            raise SystemExit(f"refused: a link or junction at {part.relative_to(ROOT).as_posix()}")
        if part == ROOT:
            break
    resolved = path.resolve()
    if resolved == base or not resolved.is_relative_to(base):
        raise SystemExit(f"refused: {path.name} is not strictly inside .cache/v051")
    return resolved


def sources() -> list[Path]:
    files = [p for p in sorted(SRC.iterdir()) if p.is_file() and not p.is_symlink()]
    for folder in FOLDERS:
        base = guard(SRC / folder)
        for p in sorted(base.rglob("*")):
            if p.is_symlink() or p.is_junction():
                raise SystemExit(f"refused: a link or junction inside {folder}")
            if p.is_file():
                files.append(p)
    return files


def archive() -> None:
    rows = []
    for src in sources():
        rel = src.relative_to(SRC).as_posix()
        dst = DRIVE / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        before = sha256(src)
        shutil.copyfile(src, dst)
        after = sha256(dst)
        if before != after:
            raise SystemExit(f"mismatch at {rel}: nothing deleted")
        rows.append({"path": rel, "bytes": src.stat().st_size, "sha256": before})
    doc = {
        "label": "the v0.5.1 cache archived by the maintainer's decision of 2026-11-08 (#216)",
        "created_utc": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "destination": "Drive: Pessoal/Projetos/refute/v0.5.1-closing-2026-11-08",
        "files": len(rows),
        "bytes": sum(r["bytes"] for r in rows),
        "entries": rows,
    }
    text = json.dumps(doc, indent=1) + "\n"
    MANIFEST.write_text(text, "utf-8")
    (DRIVE / MANIFEST.name).write_text(text, "utf-8")
    print("archived", doc["files"], "files", doc["bytes"], "bytes")


def delete() -> None:
    doc = json.loads(MANIFEST.read_text("utf-8"))
    for row in doc["entries"]:
        rel = row["path"]
        dst = DRIVE / rel
        if not dst.is_file() or sha256(dst) != row["sha256"]:
            raise SystemExit(f"the archived copy of {rel} does not match: nothing deleted")
    print("destination re-checked", doc["files"], "files")
    sizes = {}
    for folder in FOLDERS:
        sizes[folder] = sum(
            r["bytes"] for r in doc["entries"] if r["path"].startswith(folder + "/")
        )
    for row in doc["entries"]:
        if "/" not in row["path"]:
            target = guard(SRC / row["path"])
            target.unlink()
    print("deleted the loose files:", sum(1 for r in doc["entries"] if "/" not in r["path"]))
    for folder in FOLDERS:
        target = guard(SRC / folder)
        for p in target.rglob("*"):
            if p.is_symlink() or p.is_junction():
                raise SystemExit(f"refused: a link or junction inside {folder}")
        shutil.rmtree(target)
        print("deleted", f".cache/v051/{folder}", sizes[folder], "bytes")


if __name__ == "__main__":
    if sys.argv[1:] == ["archive"]:
        archive()
    elif sys.argv[1:] == ["delete"]:
        delete()
    else:
        raise SystemExit("usage: archive_v051_cache.py archive|delete")
