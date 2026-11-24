"""Item 5 of the maintainer's decision of 2026-11-24 (#218): archive what has value and is not in
the repository, then delete the named paths inside .cache, by literal path with a prefix guard
that refuses links and junctions. Steps: ``archive`` (copy + SHA-256 manifest, checked), then
``clean`` (only if the archive manifest matches). Every deleted file is logged with its SHA-256.
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
DRIVE = Path("K:/Meu Drive/Pessoal/Projetos/refute/cache-archive-2026-11-24")
LOG = CACHE / "v059/cleanup-2026-11-24.json"
MANIFEST = CACHE / "v059/archive-2026-11-24-manifest.json"

# value, not in the repository: Codex's raw events of four rounds, and the first Zenodo package
ARCHIVE = [
    ".cache/v059/plan-review/codex-events.jsonl",
    ".cache/v059/research/codex-events.jsonl",
    ".cache/v059/diet2/codex-events.jsonl",
    ".cache/v058/zenodo-review/codex-events.jsonl",
    ".cache/v058/zenodo/metadata.json",
    ".cache/v058/zenodo/record/MANIFEST-sha256.json",
]
# the decision's named paths
DELETE = [
    ".cache/v059/plan-review",
    ".cache/v059/research",
    ".cache/v059/diet2",
    ".cache/v058/zenodo",
    ".cache/v058/zenodo-v2",
    ".cache/v058/zenodo-review",
    ".cache/v058/zenodo-v2-build.py",
    ".cache/v058/zenodo-v2-draft.py",
    ".cache/v058/zenodo-v2-draft.log",
    ".cache/v058/zenodo-v2-draft.log.err",
]


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def guarded(rel: str) -> Path:
    """The literal path, inside .cache, with no link or junction from .cache down to it."""
    p = Path(os.path.abspath(ROOT / rel))
    if Path(os.path.abspath(CACHE)) not in p.parents:
        raise SystemExit(f"refused: {rel} is not inside .cache")
    q = p
    while q != CACHE:
        if q.is_symlink() or q.is_junction():
            raise SystemExit(f"refused: a link or junction on {rel}")
        q = q.parent
    return p


def archive() -> None:
    rows = []
    for rel in ARCHIVE:
        src = guarded(rel)
        dst = DRIVE / rel.removeprefix(".cache/")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        a, b = sha(src), sha(dst)
        rows.append({"source": rel, "destination": dst.as_posix(), "bytes": src.stat().st_size,
                     "source_sha256": a, "destination_sha256": b, "match": a == b})
    doc = {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "files": rows,
           "all_match": all(r["match"] for r in rows)}
    text = json.dumps(doc, indent=1) + "\n"
    MANIFEST.write_text(text, "utf-8", newline="\n")
    (DRIVE / "MANIFEST-sha256.json").write_text(text, "utf-8", newline="\n")
    print(json.dumps({"all_match": doc["all_match"], "files": len(rows)}))


def clean() -> None:
    m = json.loads(MANIFEST.read_text("utf-8"))
    if not m["all_match"]:
        raise SystemExit("refused: the archive manifest does not match")
    deleted, freed = [], 0
    for rel in DELETE:
        p = guarded(rel)
        if not p.exists():
            deleted.append({"path": rel, "status": "absent"})
            continue
        files = [p] if p.is_file() else sorted(x for x in p.rglob("*") if x.is_file())
        for f in files:
            if f.is_symlink() or f.is_junction():
                raise SystemExit(f"refused: a link inside {rel}")
            digest, size = sha(f), f.stat().st_size
            f.unlink()
            freed += size
            deleted.append({"path": Path(os.path.relpath(f, ROOT)).as_posix(), "bytes": size,
                            "sha256": digest, "status": "deleted"})
        if p.is_dir():
            for d in sorted((x for x in p.rglob("*") if x.is_dir()), key=lambda x: -len(x.parts)):
                d.rmdir()
            p.rmdir()
            deleted.append({"path": rel, "status": "folder removed"})
    LOG.write_text(json.dumps({"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                               "bytes_deleted": freed, "entries": deleted}, indent=1) + "\n",
                   "utf-8", newline="\n")
    print(json.dumps({"files_deleted": sum(e["status"] == "deleted" for e in deleted),
                      "bytes": freed}))


if __name__ == "__main__":
    {"archive": archive, "clean": clean}[sys.argv[1]]()
