"""The cleanup of what fell out of use in v0.5.11's fifth stop (the maintainer's decision received
on 2026-11-25 at 08:47 local, #218 comment 7161509920, item 4).

    .venv/Scripts/python.exe -I -B docs/maintenance/cleanup-2026-11-25-v0511-stop5/cleanup.py

The paths are literal, all under .cache/v0511:
- the screen module's draft (in src/ since a896c49);
- the intermediate diffs of the hash checks (the reviewed, adjusted and E1 diffs are committed
  under docs/validation/v0.5.11/step2/);
- the downloaded CI log of run 45514526728, summarized in the report (F-1) and the errata.

Every file is hashed, copied to the Drive
(K:/Meu Drive/Pessoal/Projetos/refute/cache-archive-2026-11-25-v0511-stop5/...) and checked
there. Only if every copy matches are the files deleted, by literal path, under a guard that
refuses anything outside .cache/v0511 and any link or junction; then the emptied draft folder is
removed. Writes record.json here.
"""

import hashlib
import json
import os
import shutil
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CACHE = ROOT / ".cache"
BASE = CACHE / "v0511"
PATHS = [
    ".cache/v0511/draft/screen_d5.py",
    ".cache/v0511/step2/check-pre-r1.diff",
    ".cache/v0511/step2/check-after-pop.diff",
    ".cache/v0511/step2/check-now.diff",
    ".cache/v0511/step2/check-pre-adjust.diff",
    ".cache/v0511/step2/check-pre-commit.diff",
    ".cache/v0511/step2/committed.diff",
    ".cache/v0511/step2/step2.diff",
    ".cache/v0511/step2/step2-r2.diff",
    ".cache/v0511/step2/step2-r3.diff",
    ".cache/v0511/ci-rest-windows.log",
]
DRIVE = Path("K:/Meu Drive/Pessoal/Projetos/refute/cache-archive-2026-11-25-v0511-stop5")
OUT = Path(__file__).resolve().parent / "record.json"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def guarded(rel: str) -> Path:
    p = Path(os.path.abspath(ROOT / rel))
    if Path(os.path.abspath(BASE)) not in p.parents:
        raise SystemExit(f"refused: {p} is outside .cache/v0511")
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
    for rel in PATHS:
        src = guarded(rel)
        if not src.is_file():
            rows.append({"path": rel, "status": "absent"})
            continue
        dst = DRIVE / Path(rel).relative_to(".cache")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        a, b = sha(src), sha(dst)
        rows.append({"path": rel, "bytes": src.stat().st_size, "sha256": a,
                     "destination_sha256": b, "match": a == b})  # fmt: skip
    present = [r for r in rows if "sha256" in r]
    if not present or not all(r["match"] for r in present):
        raise SystemExit("refused: nothing to delete, or a Drive copy does not match")
    for r in present:
        p = guarded(r["path"])
        if sha(p) != r["sha256"]:
            raise SystemExit(f"refused: {r['path']} changed")
        p.unlink()
        r["status"] = "deleted, archived"
    removed = []
    draft = guarded(".cache/v0511/draft/x").parent
    if draft.is_dir() and not any(draft.iterdir()):
        draft.rmdir()
        removed.append(".cache/v0511/draft/")
    doc = {
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "decision": "#218, comment 7161509920, item 4",
        "drive": DRIVE.as_posix(),
        "files": len(present),
        "bytes": sum(r["bytes"] for r in present),
        "all_match": all(r["match"] for r in present),
        "folders_removed": removed,
        "rows": rows,
    }
    OUT.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    (DRIVE / "MANIFEST-sha256.json").write_text(json.dumps(doc, indent=1) + "\n", "utf-8")
    shutil.copyfile(Path(__file__), DRIVE / "cleanup.py")
    print(json.dumps({k: doc[k] for k in ("files", "bytes", "all_match", "folders_removed")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
