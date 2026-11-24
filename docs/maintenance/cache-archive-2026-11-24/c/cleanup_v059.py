"""The cleanup of .cache/v059 after v0.5.9 closed (the maintainer's decision of 2026-11-24 on the
v0.5.9 gate, #218 comment 7130900283, item 6), recorded as the gate review's finding 1 asked
(issue #220). Run from the project's virtual environment, pinned to processors 8 to 31:

    .venv/Scripts/python.exe docs/maintenance/cache-archive-2026-11-24/c/cleanup_v059.py <step>

Steps, in order; each refuses if the one before it did not complete:

- ``survey``: every file under .cache/v059 with its size and SHA-256, and its citations in the
  git-tracked files at HEAD: by SHA-256, by path (the file or a folder above it), and tracked files
  with the same bytes (a stored copy). Writes ``citations-c.json`` here. Read-only otherwise.
- ``archive``: every surveyed file is copied to the Drive
  (K:/Meu Drive/Pessoal/Projetos/refute/cache-archive-2026-11-24c/<path below .cache/v059>), with
  the SHA-256 of source and destination checked. The manifest goes here (``manifest-c.json``) and
  to the Drive (``MANIFEST-sha256.json``), and this script is copied next to it. So everything with
  value is either in the repository or on the Drive, with a manifest.
- ``clean``: only if every row of the manifest matches and the Drive copy of the manifest equals
  this one. Each file is hashed again (it must still be the archived bytes) and deleted by literal
  path, with a guard that it is inside .cache/v059 and that no component from .cache down is a
  link or a junction. Empty folders are then removed, and .cache/v059 itself if it is empty. Every
  deleted path is logged with its SHA-256 (``deletion-log-c.json``).
"""

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
CACHE = ROOT / ".cache"
BASE = CACHE / "v059"
DRIVE = Path("K:/Meu Drive/Pessoal/Projetos/refute/cache-archive-2026-11-24c")
CITATIONS = HERE / "citations-c.json"
MANIFEST = HERE / "manifest-c.json"
LOG = HERE / "deletion-log-c.json"
EMPTY = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
HEX_RE = re.compile(r"(?<![0-9a-fA-F])[0-9a-fA-F]{64}(?![0-9a-fA-F])")
PATH_RE = re.compile(r"\.cache[/\\]v059(?=[/\\\s`'\")\],;:]|$)([^\s`'\")\],;]*)")


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def write(path: Path, doc) -> None:
    path.write_text(json.dumps(doc, indent=1) + "\n", "utf-8", newline="\n")


def guarded(rel: str) -> Path:
    """The literal path, inside .cache/v059, with no link or junction from .cache down to it."""
    p = Path(os.path.abspath(ROOT / rel))
    if Path(os.path.abspath(BASE)) not in p.parents:
        raise SystemExit(f"refused: {rel} is not inside .cache/v059")
    q = p
    while q != CACHE:
        if q.is_symlink() or q.is_junction():
            raise SystemExit(f"refused: a link or junction on {rel}")
        q = q.parent
    return p


def listing() -> list[str]:
    out = []
    for p in BASE.rglob("*"):
        rel = p.relative_to(ROOT).as_posix()
        if p.is_symlink() or p.is_junction():
            raise SystemExit(f"refused: a link or junction at {rel}")
        if p.is_file():
            out.append(rel)
    return sorted(out)


def survey() -> None:
    names = (
        subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True)
        .stdout.decode("utf-8")
        .split("\0")
    )
    hex_refs, path_refs, by_bytes = defaultdict(set), defaultdict(set), defaultdict(list)
    for rel in names:
        if not rel:
            continue
        try:
            data = (ROOT / rel).read_bytes()
        except OSError:
            continue
        by_bytes[hashlib.sha256(data).hexdigest()].append(rel)
        if b"\0" in data[:8192]:
            continue
        text = data.decode("utf-8", errors="replace")
        for m in HEX_RE.finditer(text):
            hex_refs[m.group(0).lower()].add(rel)
        for m in PATH_RE.finditer(text):
            cited = (".cache/v059" + m.group(1).replace("\\", "/")).rstrip("./")
            path_refs[cited].add(rel)
    rows = []
    for rel in listing():
        p = guarded(rel)
        digest = sha(p)
        under = sorted(c for c in path_refs if rel == c or rel.startswith(c + "/"))
        rows.append(
            {
                "path": rel,
                "bytes": p.stat().st_size,
                "sha256": digest,
                "cited_by_hash": [] if digest == EMPTY else sorted(hex_refs.get(digest, ())),
                "cited_by_path": {c: sorted(path_refs[c]) for c in under},
                "same_bytes_tracked": [] if digest == EMPTY else sorted(by_bytes.get(digest, ())),
            }
        )
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, check=True, text=True
    ).stdout.strip()
    write(
        CITATIONS,
        {
            "utc": now(),
            "head": head,
            "note": "Citations of each file of .cache/v059 in the git-tracked files at head: by "
            "SHA-256, by path (the file or a folder above it), and tracked files with the same "
            "bytes. The empty file's hash is not searched. Computed before the archive and the "
            "deletion.",
            "files": len(rows),
            "bytes": sum(r["bytes"] for r in rows),
            "cited": sum(bool(r["cited_by_hash"] or r["cited_by_path"]) for r in rows),
            "stored_in_repository": sum(bool(r["same_bytes_tracked"]) for r in rows),
            "rows": rows,
        },
    )
    print(json.dumps({"files": len(rows), "bytes": sum(r["bytes"] for r in rows)}))


def archive() -> None:
    surveyed = json.loads(CITATIONS.read_text("utf-8"))
    current = listing()
    if current != [r["path"] for r in surveyed["rows"]]:
        raise SystemExit("refused: .cache/v059 changed since the survey; survey again")
    rows = []
    for r in surveyed["rows"]:
        src = guarded(r["path"])
        dst = DRIVE / r["path"].removeprefix(".cache/v059/")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        a, b = sha(src), sha(dst)
        rows.append(
            {
                "source": r["path"],
                "bytes": src.stat().st_size,
                "source_sha256": a,
                "surveyed_sha256": r["sha256"],
                "destination": dst.as_posix(),
                "destination_sha256": b,
                "match": a == b == r["sha256"],
            }
        )
    doc = {
        "utc": now(),
        "decision": "#218, comment 7130900283, item 6",
        "files": len(rows),
        "bytes": sum(r["bytes"] for r in rows),
        "all_match": all(r["match"] for r in rows),
        "rows": rows,
    }
    write(MANIFEST, doc)
    write(DRIVE / "MANIFEST-sha256.json", doc)
    shutil.copyfile(Path(__file__), DRIVE / "cleanup_v059.py")
    print(json.dumps({k: doc[k] for k in ("files", "bytes", "all_match")}))


def clean() -> None:
    m = json.loads(MANIFEST.read_text("utf-8"))
    if not m["all_match"]:
        raise SystemExit("refused: the archive manifest does not match")
    if json.loads((DRIVE / "MANIFEST-sha256.json").read_text("utf-8")) != m:
        raise SystemExit("refused: the Drive manifest differs from the local one")
    archived = {r["source"]: r for r in m["rows"]}
    current = listing()
    extra = sorted(set(current) - set(archived))
    if extra:
        raise SystemExit(f"refused: {len(extra)} files are not in the archive, e.g. {extra[:3]}")
    entries, freed = [], 0
    for rel in current:
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
    dirs = sorted((d for d in BASE.rglob("*") if d.is_dir()), key=lambda d: -len(d.parts))
    for d in [*dirs, BASE]:
        if d.is_symlink() or d.is_junction():
            raise SystemExit(f"refused: a link or junction at {d}")
        if d.exists() and not any(d.iterdir()):
            d.rmdir()
            removed.append(d.relative_to(ROOT).as_posix() + "/")
    write(
        LOG,
        {
            "utc": now(),
            "files_deleted": len(entries),
            "bytes_deleted": freed,
            "folders_removed": removed,
            "entries": entries,
        },
    )
    print(json.dumps({"files_deleted": len(entries), "bytes": freed, "folders": len(removed)}))


if __name__ == "__main__":
    {"survey": survey, "archive": archive, "clean": clean}[sys.argv[1]]()
