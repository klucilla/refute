"""The closing cleanup of v0.5.10 (the maintainer's decision of 2026-11-24 received at 17:50 local,
#218 comment 7144131066, item 6): what fell out of use in .cache during this phase, and the
branches already merged into main (CLAUDE.md, "Project folder hygiene").

Run once from the project's virtual environment:

    .venv/Scripts/python.exe docs/validation/v0.5.10/cleanup/cleanup_scratch.py

- **Folders:** .cache/r1124, .cache/r1124b and .cache/r1124c, this phase's working folders (commit
  messages, issue comment drafts, helper scripts). Every file is hashed, copied to the Drive
  (K:/Meu Drive/Pessoal/Projetos/refute/cache-archive-2026-11-24-v0510-close/<folder>/...) and
  checked there. Only if every copy matches are the files deleted, by literal path, with a guard
  that refuses anything outside the three folders and any link or junction from .cache down.
- **Branches:** each branch in BRANCHES is checked with `git merge-base --is-ancestor <branch>
  main` and then deleted with `git branch -d`, which itself refuses an unmerged branch. A branch
  that fails the check is kept and logged.

Writes scratch-record.json here: the files with their SHA-256, the Drive copies, the deletions and
the branches.
"""

import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
CACHE = ROOT / ".cache"
FOLDERS = ("r1124", "r1124b", "r1124c")
BRANCHES = ("claude/v0-2-1-integration", "claude/v0-2-1-reopen")
DRIVE = Path("K:/Meu Drive/Pessoal/Projetos/refute/cache-archive-2026-11-24-v0510-close")
OUT = Path(__file__).resolve().parent / "scratch-record.json"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def guarded(p: Path) -> Path:
    p = Path(os.path.abspath(p))
    if not any(Path(os.path.abspath(CACHE / f)) in p.parents for f in FOLDERS):
        raise SystemExit(f"refused: {p} is outside the folders")
    q = p
    while q != CACHE:
        if q.is_symlink() or q.is_junction():
            raise SystemExit(f"refused: a link or junction on {p}")
        q = q.parent
    return p


def main() -> int:
    if CACHE.is_symlink() or CACHE.is_junction():
        raise SystemExit("refused: .cache is a link or a junction")
    rows = []
    for f in FOLDERS:
        base = CACHE / f
        if base.is_symlink() or base.is_junction():
            raise SystemExit(f"refused: {base} is a link or a junction")
        for p in sorted(base.rglob("*")):
            if p.is_symlink() or p.is_junction():
                raise SystemExit(f"refused: a link or junction at {p}")
            if p.is_file():
                src = guarded(p)
                rel = src.relative_to(CACHE).as_posix()
                dst = DRIVE / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, dst)
                a, b = sha(src), sha(dst)
                rows.append(
                    {
                        "path": ".cache/" + rel,
                        "bytes": src.stat().st_size,
                        "sha256": a,
                        "destination_sha256": b,
                        "match": a == b,
                    }
                )
    if not all(r["match"] for r in rows):
        raise SystemExit("refused: a Drive copy does not match; nothing deleted")
    for r in rows:
        p = guarded(ROOT / r["path"])
        if sha(p) != r["sha256"]:
            raise SystemExit(f"refused: {r['path']} changed")
        p.unlink()
        r["status"] = "deleted, archived"
    removed = []
    for f in FOLDERS:
        base = CACHE / f
        for d in sorted((d for d in base.rglob("*") if d.is_dir()), key=lambda d: -len(d.parts)):
            if not any(d.iterdir()):
                d.rmdir()
        if base.exists() and not any(base.iterdir()):
            base.rmdir()
            removed.append(".cache/" + f + "/")
    branches = []
    for b in BRANCHES:
        ref = f"refs/heads/{b}"
        tip = subprocess.run(["git", "rev-parse", ref], cwd=ROOT, capture_output=True, text=True)
        merged = (
            subprocess.run(["git", "merge-base", "--is-ancestor", ref, "main"], cwd=ROOT).returncode
            == 0
        )
        rec = {"branch": b, "tip": tip.stdout.strip(), "merged_into_main": merged}
        if merged:
            d = subprocess.run(["git", "branch", "-d", b], cwd=ROOT, capture_output=True, text=True)
            rec["deleted"] = d.returncode == 0
        else:
            rec["deleted"] = False
        branches.append(rec)
    doc = {
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "decision": "#218, comment 7144131066, item 6",
        "drive": DRIVE.as_posix(),
        "files": len(rows),
        "bytes": sum(r["bytes"] for r in rows),
        "all_match": all(r["match"] for r in rows),
        "folders_removed": removed,
        "branches": branches,
        "rows": rows,
    }
    OUT.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    (DRIVE / "MANIFEST-sha256.json").write_text(json.dumps(doc, indent=1) + "\n", "utf-8")
    shutil.copyfile(Path(__file__), DRIVE / "cleanup_scratch.py")
    print(json.dumps({k: doc[k] for k in ("files", "bytes", "all_match", "folders_removed")}))
    print(json.dumps(branches))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
