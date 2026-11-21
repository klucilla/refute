"""Archive what fell out of use in ``.cache`` to the Drive, by the maintainer's decision of
2026-11-21 (20:00), item 3 (#218), then delete it inside ``.cache`` by literal path.

The decision named the candidates; only those that no versioned file (script, record, ledger,
manifest) and no in-use tool cites as a path are archived and deleted (the search's result is in
``citations-2026-11-21.json`` next to this script). ``.backup`` is archived and never deleted.

Scope (nothing else):
- deleted after the archive: ``.cache/proposta-v04`` (all but ``gaia-esa-nao-usado``, Gaia data
  kept in place and not copied: restricted licence), ``.cache/refute`` and
  ``.cache/issues-review-2026-11-03``;
- archived only: ``.backup``.

- ``archive``: copies them to ``K:/Meu Drive/Pessoal/Projetos/refute/cache-archive-2026-11-21/``,
  hashes source and destination (SHA-256) and writes the manifest to the Drive and next to this
  script. A difference stops the script with nothing deleted.
- ``delete``: re-reads the manifest, re-hashes each destination file and each source file against
  it, and only then deletes each top-level source entry by its literal path; it refuses a path
  outside ``.cache``, a link or a junction on the way or inside, and never touches ``.backup``.

Usage (from the project root): ``.venv/Scripts/python.exe <this file> archive`` then ``delete``.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import shutil
import stat
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
CACHE = ROOT / ".cache"
DRIVE = Path("K:/Meu Drive/Pessoal/Projetos/refute/cache-archive-2026-11-21")
HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "manifest-2026-11-21.json"
DELETED = (".cache/proposta-v04", ".cache/refute", ".cache/issues-review-2026-11-03")
ARCHIVED_ONLY = (".backup",)
EXCLUDED = {".cache/proposta-v04/gaia-esa-nao-usado"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def is_link(path: Path) -> bool:
    try:
        st = os.lstat(path)
    except FileNotFoundError:
        return False
    reparse = getattr(st, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT
    return path.is_symlink() or path.is_junction() or bool(reparse)


def guard(path: Path, base: Path) -> Path:
    """The path, refused if it or a parent up to ROOT is a link or junction, or if it is not
    strictly inside ``base``."""
    for part in [path, *path.parents]:
        if is_link(part):
            raise SystemExit(f"refused: a link or junction at {part.relative_to(ROOT).as_posix()}")
        if part == ROOT:
            break
    resolved = path.resolve()
    b = base.resolve()
    if resolved == b or not resolved.is_relative_to(b):
        raise SystemExit(f"refused: {path.as_posix()} is not strictly inside {b.name}")
    return resolved


def walk(top: Path) -> list[Path]:
    """Every regular file under ``top`` (excluded folders skipped), refusing any link inside."""
    out: list[Path] = []
    stack = [top]
    while stack:
        d = stack.pop()
        for e in sorted(os.scandir(d), key=lambda e: e.name):
            p = Path(e.path)
            rel = p.relative_to(ROOT).as_posix()
            if rel in EXCLUDED:
                continue
            if is_link(p):
                raise SystemExit(f"refused: a link or junction at {rel}")
            if e.is_dir(follow_symlinks=False):
                stack.append(p)
            elif e.is_file(follow_symlinks=False):
                out.append(p)
    return sorted(out)


def sources() -> list[tuple[str, Path]]:
    pairs = []
    for rel in DELETED:
        top = guard(ROOT / rel, CACHE)
        pairs += [(rel, f) for f in walk(top)]
    for rel in ARCHIVED_ONLY:
        top = guard(ROOT / rel, ROOT)
        pairs += [(rel, f) for f in walk(top)]
    return pairs


def archive() -> None:
    if DRIVE.exists():
        raise SystemExit(f"refused: {DRIVE} already exists")
    entries = []
    for top, src in sources():
        rel = src.relative_to(ROOT).as_posix()
        dst = DRIVE / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        a, b = sha256(src), sha256(dst)
        if a != b:
            raise SystemExit(f"stopped: {rel} differs after the copy; nothing deleted")
        entries.append({"path": rel, "top": top, "bytes": src.stat().st_size, "sha256_source": a,
                        "sha256_destination": b})  # fmt: skip
    doc = {
        "schema": "refute-cache-archive-1",
        "decision": "the maintainer's decision of 2026-11-21 (20:00), item 3 (#218)",
        "created_utc": dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "destination": DRIVE.as_posix(),
        "deleted_after_archive": list(DELETED),
        "archived_only": list(ARCHIVED_ONLY),
        "excluded_kept_in_place": sorted(EXCLUDED),
        "files": len(entries),
        "bytes": sum(e["bytes"] for e in entries),
        "entries": entries,
    }
    text = json.dumps(doc, indent=1) + "\n"
    MANIFEST.write_text(text, "utf-8", newline="\n")
    (DRIVE / MANIFEST.name).write_text(text, "utf-8", newline="\n")
    print(f"archived {len(entries)} files, {doc['bytes']} bytes; manifest written")


def check() -> dict:
    doc = json.loads(MANIFEST.read_text("utf-8"))
    by_path = {e["path"]: e for e in doc["entries"]}
    now = {src.relative_to(ROOT).as_posix() for _, src in sources()}
    if now != set(by_path):
        raise SystemExit("refused: the sources changed since the manifest was written")
    for rel, e in by_path.items():
        if (
            sha256(ROOT / rel) != e["sha256_source"]
            or sha256(DRIVE / rel) != e["sha256_destination"]
        ):
            raise SystemExit(f"refused: {rel} does not match the manifest")
    print(f"checked {len(by_path)} files: source and destination match the manifest")
    return doc


def delete() -> None:
    check()
    removed = []
    for rel in DELETED:
        top = guard(ROOT / rel, CACHE)
        walk(top)  # refuses any link inside, again
        children = sorted(top.iterdir())
        kept = [c for c in children if c.relative_to(ROOT).as_posix() in EXCLUDED]
        for child in children:
            if child in kept:
                continue
            target = guard(child, CACHE)
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
            removed.append(child.relative_to(ROOT).as_posix())
        if not kept:
            top.rmdir()
            removed.append(rel)
    print(json.dumps({"deleted": removed}, indent=1))


if __name__ == "__main__":
    {"archive": archive, "check": check, "delete": delete}[sys.argv[1]]()
