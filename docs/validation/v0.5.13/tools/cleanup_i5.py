"""Delete, inside ``.cache`` and by literal path, the working copies that G7, F2 and F3 have used
(the maintainer's decision I5, #218 comment 7222329150).

    unit cleanup-i5:  {python} -I -B docs/validation/v0.5.13/tools/cleanup_i5.py

The paths are the literals below. Each must resolve inside ``<project>/.cache/`` and be neither
the ``.cache`` folder itself nor a run folder of the meter (``.cache/v0513/runs`` is kept: the
journal cites it). A path that does not exist is listed as absent. For each one it lists the
files, their bytes and whether the path is gone, in ``out/cleanup-i5.json``.
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PATHS = (
    ".cache/v0513/g7/tree",  # G7's git-archive export, after its build and check
    ".cache/v0513/g7/dist",  # G7's built sdist and wheel, after check-f2
    ".cache/v0513/f2/dist",  # F2's first local wheel (the one with CRLF in a0.py)
    ".cache/v0513/f2/pyproject.f2.toml",  # F2's pyproject change, committed in 3dbb713c
    ".cache/v0513/f2/pyproject.applied.toml",  # its check copy
    ".cache/v0513/testpypi/0.5.12",  # the TestPyPI files, after E5 and F2's wheel check
    ".cache/v0513/pypi/0.5.12",  # the PyPI files, after F3's SHA-256 check
)


def main() -> int:
    cache = (ROOT / ".cache").resolve()
    keep = (ROOT / ".cache" / "v0513" / "runs").resolve()
    rows = []
    for rel in PATHS:
        path = (ROOT / rel).resolve()
        if not path.is_relative_to(cache) or path in (cache, keep) or path.is_relative_to(keep):
            raise SystemExit(f"refused: {rel} is outside the allowed part of .cache")
        if not path.exists():
            rows.append({"path": rel, "present": False})
            continue
        files = [path] if path.is_file() else [p for p in path.rglob("*") if p.is_file()]
        size = sum(p.stat().st_size for p in files)
        if path.is_file():
            path.unlink()
        else:
            shutil.rmtree(path)
        rows.append({"path": rel, "present": True, "files": len(files), "bytes": size,
                     "deleted": not path.exists()})  # fmt: skip
    ok = all(r.get("deleted", True) for r in rows)
    report = {"rows": rows, "bytes_freed": sum(r.get("bytes", 0) for r in rows), "all_ok": ok}
    out = Path(os.environ.get("REFUTE_RUN_OUT", "."))
    text = json.dumps(report, indent=1) + "\n"
    (out / "cleanup-i5.json").write_text(text, encoding="utf-8", newline="\n")
    print(json.dumps(report))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
