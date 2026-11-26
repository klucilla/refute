"""The cleanup of v0.5.12's working folder at the phase's close (the maintainer's decision recorded
in #218, comment 7202383280, item 6).

    launch_v4.py docs/validation/v0.5.12/units/cleanup-close.json

What fell out of use when the phase closed, under .cache/v0512:
- **Regenerable copies of programs, deleted without archiving** (no value beyond the installs they
  copy; container.json records their hashes): the container's CPython copy (cpy/), Git's
  mingw64/bin copy (git/), the container's venv copy (cvenv/), its git configuration (gitconfig)
  and a temporary blob (blob.tmp).
- **Everything else, archived then deleted:** the comment and commit-message drafts, the Codex
  rounds' raw events and answers, the JUnit files, the golden and tag outputs, the ad hoc
  inspection tools (diag/), the gate files (stored unchanged in docs/gates/), the site's JUnit
  files, and the run folders.

Two things are kept: the launcher's lock file, and the run folders of this unit and of every
later unit (runs/cleanup-close__* and anything newer), which the launcher is still writing.

Every archived file is hashed, copied to the Drive
(K:/Meu Drive/Pessoal/Projetos/refute/cache-archive-2026-11-26-v0512-close/...) and checked there.
Only if every copy matches is anything deleted, by literal path, under a guard that refuses anything
outside .cache/v0512 and any link or junction. The emptied folders are then removed, deepest first.
It writes record.json beside this file, and the manifest and this script to the Drive.
"""

import hashlib
import json
import os
import shutil
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CACHE = ROOT / ".cache"
BASE = CACHE / "v0512"
DRIVE = Path("K:/Meu Drive/Pessoal/Projetos/refute/cache-archive-2026-11-26-v0512-close")
OUT = Path(__file__).resolve().parent / "record.json"
REGENERABLE_DIRS = ("v0512/cpy/", "v0512/git/", "v0512/cvenv/")
REGENERABLE_FILES = ("v0512/gitconfig", "v0512/blob.tmp")


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def guarded(p: Path) -> Path:
    p = Path(os.path.abspath(p))
    if Path(os.path.abspath(BASE)) not in p.parents:
        raise SystemExit(f"refused: {p} is outside .cache/v0512")
    q = p
    while q != CACHE:
        if q.is_symlink() or q.is_junction():
            raise SystemExit(f"refused: a link or junction on {p}")
        q = q.parent
    return p


def run_folder_kept(rel: str, my_start: float) -> bool:
    """The lock, this unit's run folder, and any run folder written from this run's start on."""
    if rel == "v0512/launcher.lock":
        return True
    parts = rel.split("/")
    if len(parts) >= 3 and parts[1] == "runs":
        if parts[2].startswith("cleanup-close__"):
            return True
        folder = BASE / "runs" / parts[2]
        return folder.stat().st_mtime >= my_start
    return False


def regenerable(rel: str) -> bool:
    return rel in REGENERABLE_FILES or any(rel.startswith(d) for d in REGENERABLE_DIRS)


def main() -> int:
    start = time.time() - 120
    if CACHE.is_symlink() or CACHE.is_junction() or BASE.is_symlink() or BASE.is_junction():
        raise SystemExit("refused: .cache or .cache/v0512 is a link or a junction")
    files = sorted(p for p in BASE.rglob("*") if p.is_file() or p.is_symlink())
    archived, dropped, kept = [], [], []
    for p in files:
        rel = p.relative_to(CACHE).as_posix()
        if run_folder_kept(rel, start):
            kept.append(rel)
            continue
        src = guarded(p)
        if regenerable(rel):
            dropped.append({"path": ".cache/" + rel, "bytes": src.stat().st_size})
            continue
        dst = DRIVE / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        a, b = sha(src), sha(dst)
        archived.append({"path": ".cache/" + rel, "bytes": src.stat().st_size, "sha256": a,
                         "destination_sha256": b, "match": a == b})  # fmt: skip
    if not archived or not all(r["match"] for r in archived):
        raise SystemExit("refused: nothing to archive, or a Drive copy does not match")
    for r in archived:
        p = guarded(ROOT / r["path"])
        if sha(p) != r["sha256"]:
            raise SystemExit(f"refused: {r['path']} changed")
        p.unlink()
        r["status"] = "deleted, archived"
    for r in dropped:
        guarded(ROOT / r["path"]).unlink()
        r["status"] = "deleted, regenerable, not archived"
    removed = []
    for d in sorted((p for p in BASE.rglob("*") if p.is_dir()), key=lambda p: -len(p.parts)):
        d = guarded(d)
        if not any(d.iterdir()):
            d.rmdir()
            removed.append(d.relative_to(ROOT).as_posix() + "/")
    doc = {
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "decision": "#218, comment 7202383280, item 6",
        "drive": DRIVE.as_posix(),
        "archived_files": len(archived),
        "archived_bytes": sum(r["bytes"] for r in archived),
        "all_match": all(r["match"] for r in archived),
        "regenerable_files_deleted": len(dropped),
        "regenerable_bytes_deleted": sum(r["bytes"] for r in dropped),
        "regenerable_folders": list(REGENERABLE_DIRS) + list(REGENERABLE_FILES),
        "kept": kept,
        "folders_removed": removed,
        "archived": archived,
    }
    OUT.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    (DRIVE / "MANIFEST-sha256.json").write_text(json.dumps(doc, indent=1) + "\n", "utf-8")
    shutil.copyfile(Path(__file__), DRIVE / "cleanup.py")
    keys = ("archived_files", "archived_bytes", "all_match", "regenerable_files_deleted",
            "regenerable_bytes_deleted", "kept")  # fmt: skip
    print(json.dumps({k: doc[k] for k in keys}))
    print("folders removed:", len(removed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
