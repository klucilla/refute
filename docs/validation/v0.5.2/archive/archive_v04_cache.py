"""Dispose of what fell out of use in ``.cache/v04``, by the maintainer's decision of 2026-11-08
(#216).

The list is ``docs/validation/v0.5.2/stage1/cache-v04-disposition.json``, one disposition per path,
and nothing else is touched. KEEP entries are never read here.

- ``check``: re-walks every entry and stops if its size or file count differs from the list, or if
  an entry to be archived holds a link, a junction, a key-like file or a TESS-EB or T10K file. It
  then compares every file of ``.cache/v04/inputs-archive`` with its Drive copy
  ``arquivo-v0.4-inputs``, path by path, by SHA-256, and writes
  ``manifest-inputs-archive-check.json``. A file only on the Drive (the folder also holds the script
  that made it) does not stop the check and is listed in that manifest.
- ``archive``: copies the ARCHIVE_THEN_DELETE entries to ``K:/Meu
  Drive/Pessoal/Projetos/refute/v0.4-cache-closing-2026-11-08/``, hashes source and destination, and
  writes ``manifest-v04-cache-2026-11-08.json`` to the Drive and next to this script. A difference
  stops the script with nothing deleted.
- ``delete``: re-hashes every archived copy and every Drive copy of the inputs against the
  manifests, and only then deletes each entry by its literal path, refusing anything outside
  ``.cache/v04``, and links and junctions on the way or inside.

Usage (from the project root): ``.venv/Scripts/python.exe <this file> check|archive|delete``.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SRC = ROOT / ".cache" / "v04"
DISPOSITION = HERE.parent / "stage1" / "cache-v04-disposition.json"
DRIVE_ROOT = Path("K:/Meu Drive/Pessoal/Projetos/refute")
DRIVE = DRIVE_ROOT / "v0.4-cache-closing-2026-11-08"
DRIVE_INPUTS = DRIVE_ROOT / "arquivo-v0.4-inputs"
INPUTS = SRC / "inputs-archive"
MANIFEST = HERE / "manifest-v04-cache-2026-11-08.json"
INPUTS_MANIFEST = HERE / "manifest-inputs-archive-check.json"
REFUSED_WORDS = ("tess-eb", "tess_eb", "t10k", "keyring", "id_rsa", "id_ed25519", "private")
REFUSED_SUFFIXES = (".key", ".pem", ".gpg", ".pfx", ".p12")
# read on 2026-11-08: a draft comment about the frozen path, with no line of the catalog
NAME_ONLY_MATCHES = {"issue-tess-eb-frozen.md": 1516}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def guard(path: Path) -> Path:
    """The path, refused if it is a link or junction, or not strictly inside ``.cache/v04``."""
    base = SRC.resolve()
    for part in [path, *path.parents]:
        if part.is_symlink() or part.is_junction():
            raise SystemExit(f"refused: a link or junction at {part.relative_to(ROOT).as_posix()}")
        if part == ROOT:
            break
    resolved = path.resolve()
    if resolved == base or not resolved.is_relative_to(base):
        raise SystemExit(f"refused: {path.name} is not strictly inside .cache/v04")
    return resolved


def walk(path: Path) -> list[Path]:
    """Every regular file of an entry; a link or junction inside stops the script."""
    if path.is_file():
        return [path]
    files = []
    for base, dirs, names in os.walk(path):
        for name in [*dirs, *names]:
            p = Path(base, name)
            if p.is_symlink() or p.is_junction():
                raise SystemExit(f"refused: a link or junction inside {path.name}")
        files += [Path(base, n) for n in names]
    return sorted(files)


def entries(disposition: str) -> list[dict]:
    doc = json.loads(DISPOSITION.read_text("utf-8"))
    return [e for e in doc["entries"] if e["disposition"] == disposition]


def checked_files() -> list[Path]:
    """The files to archive, after the entries are found to be what the list says."""
    out = []
    for entry in [*entries("ARCHIVE_THEN_DELETE"), *entries("CHECK_THEN_DELETE")]:
        path = guard(ROOT / entry["path"])
        files = walk(path)
        size = sum(f.stat().st_size for f in files)
        if size != entry["bytes"] or len(files) != entry["files"]:
            raise SystemExit(f"{entry['path']} differs from the list: nothing done")
        if entry["disposition"] == "ARCHIVE_THEN_DELETE":
            for f in files:
                low = f.name.lower()
                if NAME_ONLY_MATCHES.get(f.name) == f.stat().st_size:
                    continue
                if low.endswith(REFUSED_SUFFIXES) or any(w in low for w in REFUSED_WORDS):
                    raise SystemExit(f"refused for generic archiving: a file in {entry['path']}")
            out += files
    return out


def check() -> None:
    files = checked_files()
    print("entries match the list; files to archive:", len(files))
    local = {p.relative_to(INPUTS).as_posix(): p for p in walk(INPUTS)}
    drive = {p.relative_to(DRIVE_INPUTS).as_posix(): p for p in walk(DRIVE_INPUTS)}
    missing = set(local) - set(drive)
    if missing:
        raise SystemExit(f"{len(missing)} local paths of inputs-archive are not on the Drive")
    rows = []
    for rel in sorted(local):
        a, b = sha256(local[rel]), sha256(drive[rel])
        if a != b:
            raise SystemExit(f"inputs-archive differs from the Drive copy at {rel}")
        rows.append({"path": rel, "bytes": local[rel].stat().st_size, "sha256": a})
    doc = {
        "label": ".cache/v04/inputs-archive checked against its Drive copy before deletion (#216)",
        "created_utc": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "destination": "Drive: Pessoal/Projetos/refute/arquivo-v0.4-inputs",
        "only_on_the_drive": sorted(set(drive) - set(local)),
        "files": len(rows),
        "bytes": sum(r["bytes"] for r in rows),
        "entries": rows,
    }
    INPUTS_MANIFEST.write_text(json.dumps(doc, indent=1) + "\n", "utf-8")
    print("inputs-archive equals its Drive copy:", doc["files"], "files", doc["bytes"], "bytes")


def archive() -> None:
    rows = []
    for src in checked_files():
        rel = src.relative_to(SRC).as_posix()
        dst = DRIVE / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        before = sha256(src)
        shutil.copyfile(src, dst)
        if before != sha256(dst):
            raise SystemExit(f"mismatch at {rel}: nothing deleted")
        rows.append({"path": rel, "bytes": src.stat().st_size, "sha256": before})
    doc = {
        "label": "the v0.4 cache archived by the maintainer's decision of 2026-11-08 (#216)",
        "created_utc": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "destination": "Drive: Pessoal/Projetos/refute/v0.4-cache-closing-2026-11-08",
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
        dst = DRIVE / row["path"]
        if not dst.is_file() or sha256(dst) != row["sha256"]:
            raise SystemExit(f"the archived copy of {row['path']} does not match: nothing deleted")
    print("destination re-checked", doc["files"], "files")
    inputs = json.loads(INPUTS_MANIFEST.read_text("utf-8"))
    for row in inputs["entries"]:
        dst = DRIVE_INPUTS / row["path"]
        if not dst.is_file() or sha256(dst) != row["sha256"]:
            raise SystemExit(f"the Drive inputs at {row['path']} do not match: nothing deleted")
    print("Drive inputs re-checked", inputs["files"], "files")
    checked_files()
    for entry in [*entries("ARCHIVE_THEN_DELETE"), *entries("CHECK_THEN_DELETE")]:
        target = guard(ROOT / entry["path"])
        walk(target)
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
        print("deleted", entry["path"], entry["bytes"], "bytes", entry["files"], "files")


if __name__ == "__main__":
    actions = {"check": check, "archive": archive, "delete": delete}
    if len(sys.argv) != 2 or sys.argv[1] not in actions:
        raise SystemExit("usage: archive_v04_cache.py check|archive|delete")
    actions[sys.argv[1]]()
