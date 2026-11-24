"""The cleanup of .cache/v0510 at the end of v0.5.10 (the maintainer's decision of 2026-11-24,
#218 comment 7139692729, item 4): delete .cache/v0510/ (the engines' environment, the downloaded
light curves and pixel files, the query caches), with a committed record, after keeping what has
value. Run from the project's virtual environment, pinned to processors 8 to 31:

    .venv/Scripts/python.exe docs/validation/v0.5.10/cleanup/cleanup_v0510.py <step>

Steps, in order; each refuses if the one before it did not complete:

- ``survey``: every file under .cache/v0510 with its size and SHA-256, and whether it is kept on
  the Drive (KEEP) or deleted without archive as regenerable (the rest). Writes survey.json here.
- ``archive``: the files under the KEEP folders are copied to the Drive
  (K:/Meu Drive/Pessoal/Projetos/refute/cache-archive-2026-11-24-v0510/<path below .cache>), with
  the SHA-256 of source and destination checked. The manifest goes here (manifest.json) and to the
  Drive (MANIFEST-sha256.json), and this script is copied next to it.
- ``clean``: only if every row of the manifest matches and the Drive copy of the manifest equals
  this one. Every surveyed file is hashed again (it must still be the surveyed bytes) and deleted by
  literal path, with a guard that it is inside .cache/v0510 and that no component from .cache down
  is a link or a junction. Empty folders are then removed, .cache/v0510 itself last. Every deleted
  path is logged with its SHA-256 (deletion-log.json).

What is kept and why:
- KEEP (to the Drive): census and route-e (the per-target census tables and the cached catalog
  answers behind parts (b) to (d)), meta, codex (the Codex round's working files), runs (each
  engine run's job, stdout, stderr and result; the private caches inside are excluded), workers and
  workers_gpl (the workers that ran, including the GPL ones, which never enter the repository),
  tools, probe, synthetic.
- Deleted without archive, regenerable: engines (the environment: wheelhouse-manifest.json and the
  scripts rebuild it), data (the MAST files: data-check.json gives their URLs and SHA-256), staged
  (the TIC and Gaia tables: stage_catalogs.py queries them again; Gaia rows are not archived),
  not-granted, and the private caches of the runs.

Nothing outside .cache/v0510 is touched. The AppContainer profile is not deleted here: its removal
is the maintainer's (engines/delete_profile.py).
"""

import hashlib
import json
import os
import shutil
import stat
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
CACHE = ROOT / ".cache"
BASE = CACHE / "v0510"
KEEP = ("census", "route-e", "meta", "codex", "runs", "workers", "workers_gpl", "tools", "probe",
        "synthetic")  # fmt: skip
DRIVE = Path("K:/Meu Drive/Pessoal/Projetos/refute/cache-archive-2026-11-24-v0510")
SURVEY = HERE / "survey.json"
MANIFEST = HERE / "manifest.json"
LOG = HERE / "deletion-log.json"


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def write(path: Path, doc) -> None:
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
    p = Path(os.path.abspath(ROOT / rel))
    if Path(os.path.abspath(BASE)) not in p.parents:
        raise SystemExit(f"refused: {rel} is not inside .cache/v0510")
    q = p
    while q != CACHE:
        if q.is_symlink() or q.is_junction():
            raise SystemExit(f"refused: a link or junction on {rel}")
        q = q.parent
    return p


def kept(rel: str) -> bool:
    parts = rel.split("/")
    if len(parts) < 4 or parts[2] not in KEEP:
        return False
    return not (parts[2] == "runs" and "private" in parts)


GROUPED = (".cache/v0510/engines/venv/", ".cache/v0510/engines/base/")


def group_of(rel: str) -> str | None:
    """The environment's files are recorded per package folder (the record stays under 5 MB)."""
    if not rel.startswith(GROUPED):
        return None
    parts = rel.split("/")
    depth = 7 if "/Lib/site-packages/" in rel else 5
    return "/".join(parts[:depth]) + "/" if len(parts) > depth else "/".join(parts[:-1]) + "/"


def grouped(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    single, groups = [], {}
    for r in rows:
        g = group_of(r["path"])
        if g is None:
            single.append(r)
            continue
        d = groups.setdefault(g, {"group": g, "files": 0, "bytes": 0, "lines": []})
        d["files"] += 1
        d["bytes"] += r["bytes"]
        d["lines"].append(f"{r['path']}\t{r['sha256']}\n")
    out = []
    for g in sorted(groups):
        d = groups[g]
        digest = hashlib.sha256("".join(sorted(d["lines"])).encode("utf-8")).hexdigest()
        out.append({"group": g, "files": d["files"], "bytes": d["bytes"], "list_sha256": digest})
    return single, out


def listing() -> list[str]:
    if BASE.is_symlink() or BASE.is_junction():
        raise SystemExit("refused: .cache/v0510 is a link or a junction")
    out = []
    for p in BASE.rglob("*"):
        rel = p.relative_to(ROOT).as_posix()
        if p.is_symlink() or p.is_junction():
            raise SystemExit(f"refused: a link or junction at {rel}")
        if p.is_file():
            out.append(rel)
    return sorted(out)


def survey() -> None:
    rows = []
    for rel in listing():
        p = guarded(rel)
        rows.append({"path": rel, "bytes": p.stat().st_size, "sha256": sha(p), "keep": kept(rel)})
    single, groups = grouped(rows)
    doc = {
        "utc": now(),
        "decision": "#218, comment 7139692729, item 4",
        "keep_folders": list(KEEP),
        "note": "files under engines/venv and engines/base are recorded per package folder: the "
        "count, the bytes and the SHA-256 of the sorted lines 'path TAB sha256'",
        "files": len(rows),
        "bytes": sum(r["bytes"] for r in rows),
        "kept_files": sum(r["keep"] for r in rows),
        "kept_bytes": sum(r["bytes"] for r in rows if r["keep"]),
        "groups": groups,
        "rows": single,
    }
    write(SURVEY, doc)
    print(json.dumps({k: doc[k] for k in ("files", "bytes", "kept_files", "kept_bytes")}))


def archive() -> None:
    s = json.loads(SURVEY.read_text("utf-8"))
    if sum(1 for _ in listing()) != s["files"]:
        raise SystemExit("refused: .cache/v0510 changed since the survey; survey again")
    rows = []
    for r in s["rows"]:
        if not r["keep"]:
            continue
        src = guarded(r["path"])
        dst = DRIVE / r["path"].removeprefix(".cache/")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        a, b = sha(src), sha(dst)
        rows.append(
            {
                "source": r["path"],
                "bytes": r["bytes"],
                "source_sha256": a,
                "surveyed_sha256": r["sha256"],
                "destination": dst.as_posix(),
                "destination_sha256": b,
                "match": a == b == r["sha256"],
            }
        )
    doc = {
        "utc": now(),
        "decision": "#218, comment 7139692729, item 4",
        "files": len(rows),
        "bytes": sum(r["bytes"] for r in rows),
        "all_match": all(r["match"] for r in rows),
        "rows": rows,
    }
    write(MANIFEST, doc)
    write(DRIVE / "MANIFEST-sha256.json", doc)
    shutil.copyfile(Path(__file__), DRIVE / "cleanup_v0510.py")
    print(json.dumps({k: doc[k] for k in ("files", "bytes", "all_match")}))


def clean() -> None:
    m = json.loads(MANIFEST.read_text("utf-8"))
    if not m["all_match"]:
        raise SystemExit("refused: the archive manifest does not match")
    if json.loads((DRIVE / "MANIFEST-sha256.json").read_text("utf-8")) != m:
        raise SystemExit("refused: the Drive manifest differs from the local one")
    s = json.loads(SURVEY.read_text("utf-8"))
    current = listing()
    if len(current) != s["files"]:
        raise SystemExit("refused: the number of files changed since the survey")
    rows = []
    for rel in current:
        p = guarded(rel)
        rows.append({"path": rel, "bytes": p.stat().st_size, "sha256": sha(p), "keep": kept(rel)})
    single, groups = grouped(rows)
    if single != s["rows"] or groups != s["groups"]:
        raise SystemExit("refused: the files differ from the survey")
    archived = {r["source"] for r in m["rows"]}
    if archived != {r["path"] for r in rows if r["keep"]}:
        raise SystemExit("refused: the kept files differ from the archive")
    freed = 0
    for r in rows:
        p = guarded(r["path"])
        if not os.access(p, os.W_OK):
            os.chmod(p, stat.S_IREAD | stat.S_IWRITE)
        p.unlink()
        freed += r["bytes"]
    removed = []
    dirs = sorted((d for d in BASE.rglob("*") if d.is_dir()), key=lambda d: -len(d.parts))
    for d in [*dirs, BASE]:
        if d.is_symlink() or d.is_junction():
            raise SystemExit(f"refused: a link or junction at {d}")
        if d.exists() and not any(d.iterdir()):
            d.rmdir()
            removed.append(d.relative_to(ROOT).as_posix() + "/")
    entries = [
        {
            "path": r["path"],
            "bytes": r["bytes"],
            "sha256": r["sha256"],
            "status": "deleted, archived" if r["keep"] else "deleted, regenerable",
        }
        for r in single
    ]
    write(
        LOG,
        {
            "utc": now(),
            "files_deleted": len(rows),
            "bytes_deleted": freed,
            "groups_deleted": groups,
            "folders_removed": len(removed),
            "base_removed": not BASE.exists(),
            "entries": entries,
        },
    )
    print(json.dumps({"files_deleted": len(rows), "bytes": freed, "folders": len(removed)}))


if __name__ == "__main__":
    {"survey": survey, "archive": archive, "clean": clean}[sys.argv[1]]()
