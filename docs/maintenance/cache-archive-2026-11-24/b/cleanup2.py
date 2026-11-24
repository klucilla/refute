"""Item 4 of the maintainer's decision of 2026-11-24 (received at 05:07 local; #218, comment
7125778250): the cleanup of .cache/v052, .cache/v053, .cache/maint1120, .cache/v05 and .cache/v055.

- ``archive``: every file of the five folders, except the kept paths, is copied to the Drive
  (K:/Meu Drive/Pessoal/Projetos/refute/cache-archive-2026-11-24b/<path below .cache>), with the
  SHA-256 of source and destination checked; the manifest goes to the Drive and to
  .cache/v059/cleanup2/archive-manifest.json, and this script is copied next to it. Files cited by
  a committed record (by SHA-256 or path) and files with value are all in it: nothing is deleted
  without an archived, checked copy.
- ``clean``: only if every row of the manifest matches; each archived file is hashed again (it must
  still be the archived bytes), then deleted by literal path, with a guard that it is inside one
  of the five folders and that no component from .cache down is a link or a junction. Empty
  folders are then removed, except the kept ones. Every deleted path is logged with its SHA-256.

Kept (the maintainer's rule "in doubt, keep it and tell me"): the two git worktrees of the site
repository (their admin entries live in that repository) and .cache/v055/tools (pinrun.py, which
the v0.5.9 procedure uses).
"""

import hashlib
import json
import os
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CACHE = ROOT / ".cache"
FOLDERS = ["v052", "v053", "maint1120", "v05", "v055"]
KEEP = (".cache/maint1120/site-synth/", ".cache/v055/site-pause/", ".cache/v055/tools/")
DRIVE = Path("K:/Meu Drive/Pessoal/Projetos/refute/cache-archive-2026-11-24b")
WORK = CACHE / "v059/cleanup2"
MANIFEST = WORK / "archive-manifest.json"
LOG = WORK / "cleanup-log.json"


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def guarded(rel: str) -> Path:
    """The literal path, inside one of the five folders, with no link or junction from .cache."""
    p = Path(os.path.abspath(ROOT / rel))
    roots = [Path(os.path.abspath(CACHE / f)) for f in FOLDERS]
    if not any(r in p.parents for r in roots):
        raise SystemExit(f"refused: {rel} is not inside the five folders")
    q = p
    while q != CACHE:
        if q.is_symlink() or q.is_junction():
            raise SystemExit(f"refused: a link or junction on {rel}")
        q = q.parent
    return p


def listing() -> list[str]:
    out = []
    for f in FOLDERS:
        base = CACHE / f
        for p in base.rglob("*"):
            rel = p.relative_to(ROOT).as_posix()
            if p.is_symlink() or p.is_junction():
                raise SystemExit(f"refused: a link or junction at {rel}")
            if p.is_file() and not (rel + "/").startswith(KEEP) and not rel.startswith(KEEP):
                out.append(rel)
    return sorted(out)


def archive() -> None:
    rows = []
    for rel in listing():
        src = guarded(rel)
        dst = DRIVE / rel.removeprefix(".cache/")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        a, b = sha(src), sha(dst)
        rows.append({"source": rel, "bytes": src.stat().st_size, "source_sha256": a,
                     "destination": dst.as_posix(), "destination_sha256": b, "match": a == b})
    doc = {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "decision": "#218, comment 7125778250, item 4", "kept": list(KEEP),
           "files": len(rows), "bytes": sum(r["bytes"] for r in rows),
           "all_match": all(r["match"] for r in rows), "rows": rows}
    text = json.dumps(doc, indent=1) + "\n"
    WORK.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(text, "utf-8", newline="\n")
    (DRIVE / "MANIFEST-sha256.json").write_text(text, "utf-8", newline="\n")
    shutil.copyfile(Path(__file__), DRIVE / "cleanup2.py")
    print(json.dumps({k: doc[k] for k in ("files", "bytes", "all_match")}))


def clean() -> None:
    m = json.loads(MANIFEST.read_text("utf-8"))
    if not m["all_match"]:
        raise SystemExit("refused: the archive manifest does not match")
    drive_copy = json.loads((DRIVE / "MANIFEST-sha256.json").read_text("utf-8"))
    if drive_copy != m:
        raise SystemExit("refused: the Drive manifest differs from the local one")
    now = listing()
    archived = {r["source"]: r for r in m["rows"]}
    extra = sorted(set(now) - set(archived))
    if extra:
        raise SystemExit(f"refused: {len(extra)} files are not in the archive, e.g. {extra[:3]}")
    entries, freed = [], 0
    for rel in now:
        p = guarded(rel)
        r = archived[rel]
        digest = sha(p)
        if digest != r["source_sha256"] or digest != r["destination_sha256"]:
            raise SystemExit(f"refused: {rel} changed since it was archived")
        size = p.stat().st_size
        p.unlink()
        freed += size
        entries.append({"path": rel, "bytes": size, "sha256": digest, "status": "deleted"})
    removed = []
    for f in FOLDERS:
        base = CACHE / f
        dirs = sorted((d for d in base.rglob("*") if d.is_dir()), key=lambda d: -len(d.parts))
        for d in [*dirs, base]:
            rel = d.relative_to(ROOT).as_posix() + "/"
            if any(rel.startswith(k) or k.startswith(rel) for k in KEEP):
                continue
            if d.exists() and not any(d.iterdir()):
                d.rmdir()
                removed.append(rel)
    LOG.write_text(json.dumps({"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                               "files_deleted": len(entries), "bytes_deleted": freed,
                               "folders_removed": removed, "entries": entries}, indent=1) + "\n",
                   "utf-8", newline="\n")
    print(json.dumps({"files_deleted": len(entries), "bytes": freed,
                      "folders_removed": len(removed)}))


if __name__ == "__main__":
    {"archive": archive, "clean": clean}[sys.argv[1]]()
