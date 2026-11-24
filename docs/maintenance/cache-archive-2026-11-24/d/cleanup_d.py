"""The cleanup of the .cache folders that fell out of use (the maintainer's decision of
2026-11-24 received at 11:09 local, #218 comment 7133936093, item 4), recorded as the rule of
#220's finding asks. Part D of docs/maintenance/cache-archive-2026-11-24/; the same steps as part
C's cleanup_v059.py, over the folders of FOLDERS. Run from the project's virtual environment,
pinned to processors 8 to 31:

    .venv/Scripts/python.exe docs/maintenance/cache-archive-2026-11-24/d/cleanup_d.py <step>

Steps, in order; each refuses if the one before it did not complete:

- ``survey``: every file under the folders of FOLDERS with its size and SHA-256, and its
  citations in the git-tracked files at HEAD: by SHA-256, by path (the file or a folder above
  it), and tracked files with the same bytes (a stored copy). Writes ``citations-d.json`` here.
  Read-only otherwise.
- ``archive``: every surveyed file is copied to the Drive
  (K:/Meu Drive/Pessoal/Projetos/refute/cache-archive-2026-11-24d/<path below .cache>), with
  the SHA-256 of source and destination checked. The manifest goes here (``manifest-d.json``) and
  to the Drive (``MANIFEST-sha256.json``), and this script is copied next to it. So everything
  with value is either in the repository or on the Drive, with a manifest.
- ``clean``: only if every row of the manifest matches and the Drive copy of the manifest equals
  this one. Each file is hashed again (it must still be the archived bytes) and deleted by literal
  path, with a guard that it is inside one of the folders and that no component from .cache down
  is a link or a junction. Empty folders are then removed, and each folder itself if it is
  empty. Every deleted path is logged with its SHA-256 (``deletion-log-d.json``).
"""

import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
CACHE = ROOT / ".cache"
# out of use after the round of 2026-11-24 (the list is in README.md, with the reason of each)
FOLDERS = (
    "codex",
    "data",
    "proposta-v04",
    "pub1119",
    "seal",
    "tb",
    "v051",
    "v054",
    "v056",
    "v057",
    "v058",
    "v059-closing",
)
BASES = tuple(CACHE / f for f in FOLDERS)
DRIVE = Path("K:/Meu Drive/Pessoal/Projetos/refute/cache-archive-2026-11-24d")
CITATIONS = HERE / "citations-d.json"
MANIFEST = HERE / "manifest-d.json"
LOG = HERE / "deletion-log-d.json"
EMPTY = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
HEX_RE = re.compile(r"(?<![0-9a-fA-F])[0-9a-fA-F]{64}(?![0-9a-fA-F])")
PATH_RE = re.compile(
    r"\.cache[/\\](" + "|".join(re.escape(f) for f in FOLDERS) + r")(?=[/\\\s`'\")\],;:]|$)"
    r"([^\s`'\")\],;]*)"
)


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def write(path: Path, doc) -> None:
    """JSON with the top-level fields indented and each item of a list field ``rows`` or
    ``entries`` on one line (so the manifest and the log stay under 5 MB in git)."""
    big = {k: doc[k] for k in ("rows", "entries") if k in doc}
    head = {k: v for k, v in doc.items() if k not in big}
    text = json.dumps(head, indent=1)[:-2]
    for k, items in big.items():
        body = ",\n".join(json.dumps(x, separators=(",", ":")) for x in items)
        text += f',\n "{k}": [\n' + body + "\n ]"
    text += "\n}\n"
    if json.loads(text) != doc:
        raise SystemExit(f"refused: {path.name} does not round-trip")
    path.write_text(text, "utf-8", newline="\n")


def guarded(rel: str) -> Path:
    """The literal path, inside one of the folders, with no link or junction from .cache down."""
    p = Path(os.path.abspath(ROOT / rel))
    if not any(Path(os.path.abspath(b)) in p.parents for b in BASES):
        raise SystemExit(f"refused: {rel} is not inside the folders")
    q = p
    while q != CACHE:
        if q.is_symlink() or q.is_junction():
            raise SystemExit(f"refused: a link or junction on {rel}")
        q = q.parent
    return p


def listing() -> list[str]:
    out = []
    for base in BASES:
        if base.is_symlink() or base.is_junction():
            raise SystemExit(f"refused: {base} is a link or a junction")
        for p in base.rglob("*"):
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
            cited = (".cache/" + m.group(1) + m.group(2).replace("\\", "/")).rstrip("./")
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
    # compact (under 5 MB in git): every citing or same-bytes file is an index into "records"
    records = sorted(
        {x for r in rows for x in r["cited_by_hash"]}
        | {x for r in rows for v in r["cited_by_path"].values() for x in v}
        | {x for r in rows for x in r["same_bytes_tracked"]}
    )
    idx = {x: i for i, x in enumerate(records)}
    compact = [
        {
            "path": r["path"],
            "bytes": r["bytes"],
            "sha256": r["sha256"],
            "hash": [idx[x] for x in r["cited_by_hash"]],
            "by_path": {c: [idx[x] for x in v] for c, v in r["cited_by_path"].items()},
            "same": [idx[x] for x in r["same_bytes_tracked"]],
        }
        for r in rows
    ]
    head_doc = {
        "utc": now(),
        "head": head,
        "note": "Citations of each file of the folders in the git-tracked files at head: by "
        "SHA-256 (hash), by path, the file or a folder above it (by_path), and tracked files "
        "with the same bytes (same); every one is an index into records. The empty file's hash "
        "is not searched. Computed before the archive and the deletion.",
        "files": len(rows),
        "bytes": sum(r["bytes"] for r in rows),
        "cited_by_hash": sum(bool(r["cited_by_hash"]) for r in rows),
        "cited_by_hash_or_path": sum(bool(r["cited_by_hash"] or r["cited_by_path"]) for r in rows),
        "stored_in_repository": sum(bool(r["same_bytes_tracked"]) for r in rows),
        "records": records,
    }
    body = ",\n".join(json.dumps(r, separators=(",", ":")) for r in compact)
    text = json.dumps(head_doc, indent=1)[:-2] + ',\n "rows": [\n' + body + "\n ]\n}\n"
    json.loads(text)
    CITATIONS.write_text(text, "utf-8", newline="\n")
    print(json.dumps({"files": len(rows), "bytes": sum(r["bytes"] for r in rows)}))


def archive() -> None:
    surveyed = json.loads(CITATIONS.read_text("utf-8"))
    current = listing()
    if current != [r["path"] for r in surveyed["rows"]]:
        raise SystemExit("refused: the folders changed since the survey; survey again")
    rows = []
    for r in surveyed["rows"]:
        src = guarded(r["path"])
        dst = DRIVE / r["path"].removeprefix(".cache/")
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
        "decision": "#218, comment 7133936093, item 4",
        "folders": list(FOLDERS),
        "files": len(rows),
        "bytes": sum(r["bytes"] for r in rows),
        "all_match": all(r["match"] for r in rows),
        "rows": rows,
    }
    write(MANIFEST, doc)
    write(DRIVE / "MANIFEST-sha256.json", doc)
    shutil.copyfile(Path(__file__), DRIVE / "cleanup_d.py")
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
    # A first attempt of 2026-11-24 stopped at a read-only file (a git pack in .cache/tb) before
    # writing its log. Each file it deleted had been hashed and matched the archive first; the
    # archived files that are no longer present are logged as deleted by that attempt.
    entries, freed = [], 0
    for rel in sorted(set(archived) - set(current)):
        r = archived[rel]
        entries.append(
            {
                "path": rel,
                "bytes": r["bytes"],
                "sha256": r["source_sha256"],
                "status": "deleted by the interrupted first attempt",
            }
        )
        freed += r["bytes"]
    for rel in current:
        p = guarded(rel)
        r = archived[rel]
        digest = sha(p)
        if digest != r["source_sha256"] or digest != r["destination_sha256"]:
            raise SystemExit(f"refused: {rel} changed since it was archived")
        size = p.stat().st_size
        if not os.access(p, os.W_OK):
            os.chmod(p, stat.S_IREAD | stat.S_IWRITE)  # a read-only file (git objects)
        p.unlink()
        freed += size
        entries.append({"path": rel, "bytes": size, "sha256": digest, "status": "deleted"})
    removed = []
    dirs = sorted(
        (d for b in BASES for d in b.rglob("*") if d.is_dir()), key=lambda d: -len(d.parts)
    )
    for d in [*dirs, *BASES]:
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
