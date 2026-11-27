"""Delete the three untracked leftovers of amendment 2's folder, by literal path (v0.5.13; the
maintainer's decision E3, #218 comment 7216128796).

    unit delete-leftovers:  {python} -I -B docs/validation/v0.5.13/tools/delete_leftovers.py

It takes no arguments: the only paths it may delete are the three literals below.
- **Prefix guard:** each must resolve inside ``docs/plans/v0.5.13-amendment-2/`` of this
  repository, and be a regular file.
- **Untracked:** ``git ls-files --error-unmatch`` must fail for each one.
- **The committed r2 patches exist:** the four ``r2-*.patch`` files must be tracked at ``HEAD``.
If any check fails, nothing is deleted. It prints each file's size and SHA-256 before deleting it.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
FOLDER = (ROOT / "docs" / "plans" / "v0.5.13-amendment-2").resolve()
LEFTOVERS = (
    "docs/plans/v0.5.13-amendment-2/runner.patch",
    "docs/plans/v0.5.13-amendment-2/runner.diff",
    "docs/plans/v0.5.13-amendment-2/test_runner_blas_pin.diff",
)
R2 = tuple(
    f"docs/plans/v0.5.13-amendment-2/r2-{name}.patch"
    for name in ("runner", "pinned_worker", "test_runner_blas_pin", "dependency")
)


def tracked(rel: str) -> bool:
    p = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", rel], cwd=ROOT, capture_output=True
    )
    return p.returncode == 0


def at_head(rel: str) -> bool:
    p = subprocess.run(["git", "cat-file", "-e", f"HEAD:{rel}"], cwd=ROOT, capture_output=True)
    return p.returncode == 0


def main() -> int:
    if len(sys.argv) != 1:
        raise SystemExit("refused: this unit takes no arguments")
    report: dict = {"r2_tracked_at_head": {rel: at_head(rel) for rel in R2}, "leftovers": []}
    problems = [f"{rel} is not tracked at HEAD" for rel, ok in report["r2_tracked_at_head"].items()
                if not ok]  # fmt: skip
    for rel in LEFTOVERS:
        path = (ROOT / rel).resolve()
        entry = {"path": rel, "inside_prefix": path.parent == FOLDER, "is_file": path.is_file()}
        entry["tracked"] = tracked(rel)
        if entry["is_file"]:
            data = path.read_bytes()
            entry.update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
        if not entry["inside_prefix"] or not entry["is_file"] or entry["tracked"]:
            problems.append(f"{rel}: {entry}")
        report["leftovers"].append(entry)
    if problems:
        report["refused"] = problems
        print(json.dumps(report, indent=1))
        return 2
    for entry in report["leftovers"]:
        (ROOT / entry["path"]).resolve().unlink()
        entry["deleted"] = not (ROOT / entry["path"]).exists()
    print(json.dumps(report, indent=1))
    return 0 if all(e["deleted"] for e in report["leftovers"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
