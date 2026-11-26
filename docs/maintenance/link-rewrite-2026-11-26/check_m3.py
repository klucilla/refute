"""The deterministic check of the maintainer's decision of 2026-11-26, item M3 (#218, comment
7204660147), before PR klucilla/refute#229 is merged.

    .venv/Scripts/python.exe -B docs/maintenance/link-rewrite-2026-11-26/check_m3.py \
        --reviewed f3d1843 --tip <the PR's head SHA> [--report OUT.json]

It passes (exit 0) only if all three hold, reading git objects only:
1. ``README.md`` at the tip is byte for byte the blob the adviser reviewed (the draft commit before
   M2, ``--reviewed``).
2. The diff from the reviewed commit to the tip touches exactly one path, ``docs/STATUS.md``.
3. In ``docs/STATUS.md``, only link targets changed:
   - both versions have the same number of lines;
   - every changed line is after the heading of the moved block;
   - every changed line is equal to its old version once every relative link target is blanked
     (``scripts/md_links.py``);
   - each changed target, old and new, reaches the same repository path: the old one written for
     the root, the new one for ``docs/``.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import md_links  # noqa: E402

MARKER = "## 2. The README as it was on 2026-11-26 (moved literally)"


def git(*args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True).stdout


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reviewed", required=True)
    ap.add_argument("--tip", required=True)
    ap.add_argument("--report")
    a = ap.parse_args(argv)
    reviewed = git("rev-parse", a.reviewed).decode().strip()
    tip = git("rev-parse", a.tip).decode().strip()
    readme_old = git("show", f"{reviewed}:README.md")
    readme_new = git("show", f"{tip}:README.md")
    paths = [p for p in git("diff", "--name-only", reviewed, tip).decode().splitlines() if p]
    old = git("show", f"{reviewed}:docs/STATUS.md").decode("utf-8").split("\n")
    new = git("show", f"{tip}:docs/STATUS.md").decode("utf-8").split("\n")
    marker = old.index(MARKER) if MARKER in old else -1
    problems: list[str] = []
    changed_lines = changed_targets = 0
    if len(old) != len(new):
        problems.append(f"line count {len(old)} -> {len(new)}")
    for n, (o, w) in enumerate(zip(old, new, strict=False)):
        if o == w:
            continue
        changed_lines += 1
        if n <= marker:
            problems.append(f"line {n + 1} changed before the moved block")
            continue
        if md_links.map_targets(o, lambda t: "") != md_links.map_targets(w, lambda t: ""):
            problems.append(f"line {n + 1}: text other than link targets changed")
            continue
        ot = [t for _, t in md_links.targets(o)]
        nt = [t for _, t in md_links.targets(w)]
        if len(ot) != len(nt):
            problems.append(f"line {n + 1}: target count {len(ot)} -> {len(nt)}")
            continue
        for x, y in zip(ot, nt, strict=True):
            if x != y:
                changed_targets += 1
                if md_links.to_root(x, "") != md_links.to_root(y, "docs"):
                    problems.append(f"line {n + 1}: {x} and {y} reach different paths")
    result = {
        "reviewed": reviewed,
        "tip": tip,
        "readme_byte_equal": readme_old == readme_new,
        "readme_git_blob_id": git("rev-parse", f"{tip}:README.md").decode().strip(),
        "paths_changed": paths,
        "only_status_changed": paths == ["docs/STATUS.md"],
        "status_changed_lines": changed_lines,
        "status_changed_targets": changed_targets,
        "status_problems": problems,
    }
    result["passed"] = bool(
        result["readme_byte_equal"] and result["only_status_changed"] and not problems
    )
    if a.report:
        Path(a.report).write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=1))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
