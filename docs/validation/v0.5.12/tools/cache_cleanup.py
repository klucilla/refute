"""Delete files of ``.cache/v0512/`` that are already integrated in the repository, with a record.

    launch_v3 unit cache-cleanup:
        {python} -I -B docs/validation/v0.5.12/tools/cache_cleanup.py <folder> <cache>=<kept> ...

Each pair names a cache file and its committed copy. A file is deleted only when:
- its literal path is inside ``.cache/v0512/`` (the prefix guard) and inside the named folder;
- its kept copy is committed at HEAD, byte for byte equal (the same SHA-256).

When every file of the folder has been deleted, the empty folder is removed by its literal path.
Nothing is deleted if any check fails. The record (``cache-cleanup.json``, in the run's out folder)
lists every deleted path, its bytes and its SHA-256.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
GUARD = (ROOT / ".cache" / "v0512").resolve()


def committed(rel: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(ROOT), "show", f"HEAD:{rel}"], check=True, capture_output=True
    ).stdout


def main() -> int:
    folder = (ROOT / sys.argv[1]).resolve()
    if GUARD not in folder.parents:
        raise SystemExit(f"refused: {folder} is not inside .cache/v0512")
    plan = []
    for pair in sys.argv[2:]:
        cache_rel, kept_rel = pair.split("=", 1)
        cache = (ROOT / cache_rel).resolve()
        if folder not in cache.parents or not cache.is_file():
            raise SystemExit(f"refused: {cache_rel} is not a file of {sys.argv[1]}")
        data = cache.read_bytes()
        kept = committed(Path(kept_rel).as_posix())
        sha = hashlib.sha256(data).hexdigest()
        if sha != hashlib.sha256(kept).hexdigest():
            raise SystemExit(f"refused: {cache_rel} differs from the committed {kept_rel}")
        plan.append((cache, cache_rel, kept_rel, len(data), sha))
    rest = {p.resolve() for p in folder.iterdir()} - {c for c, *_ in plan}
    deleted = []
    for cache, cache_rel, kept_rel, size, sha in plan:
        cache.unlink()
        deleted.append({"path": cache_rel, "bytes": size, "sha256": sha, "kept_as": kept_rel})
    removed_folder = False
    if not rest and not any(folder.iterdir()):
        folder.rmdir()
        removed_folder = True
    record = {
        "schema": "refute-v0512-cache-cleanup",
        "folder": sys.argv[1],
        "deleted": deleted,
        "folder_removed": removed_folder,
        "left_in_folder": sorted(p.name for p in rest),
    }
    out = Path(os.environ["REFUTE_RUN_OUT"]) / "cache-cleanup.json"
    out.write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(record))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
