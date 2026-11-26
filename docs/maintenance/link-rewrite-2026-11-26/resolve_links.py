"""Check that every relative link target of Markdown files resolves to an existing file or folder
(the maintainer's decision of 2026-11-26, item M2; #218, comment 7204660147).

    .venv/Scripts/python.exe -B docs/maintenance/link-rewrite-2026-11-26/resolve_links.py \
        [--as FILE=REPO_PATH ...] [--report OUT.json] FILE [FILE ...]

Each target (``scripts/md_links.py``) is resolved from the folder of the file in the repository:
its own, or the one given with ``--as`` (to check a text extracted to ``.cache`` as if it lived at
``REPO_PATH``). The path part must exist under the repository root. A fragment on a target that is a
Markdown file is also checked against that file's GitHub-style heading anchors, and reported apart
(it does not fail the check: the decision asks for existing files). Exit 0 when every path exists.
"""

from __future__ import annotations

import argparse
import json
import posixpath
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import md_links  # noqa: E402


def anchors(path: Path) -> set[str]:
    found: set[str] = set()
    seen: dict[str, int] = {}
    fenced = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            fenced = not fenced
        m = None if fenced else re.match(r"^#{1,6}\s+(.*?)\s*#*\s*$", line)
        if m:
            s = re.sub(r"[^\w\- ]", "", m.group(1).strip().lower()).replace(" ", "-")
            n = seen.get(s, 0)
            found.add(s if n == 0 else f"{s}-{n}")
            seen[s] = n + 1
    return found


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--as", dest="as_", action="append", default=[])
    ap.add_argument("--report")
    a = ap.parse_args(argv)
    declared = dict(x.split("=", 1) for x in a.as_)
    doc: dict = {"files": {}, "missing_paths": 0, "missing_anchors": 0}
    for name in a.files:
        repo_path = declared.get(name, Path(name).resolve().relative_to(ROOT).as_posix())
        file_dir = posixpath.dirname(repo_path)
        text = Path(name).read_text(encoding="utf-8")
        rows = md_links.targets(text)
        bad_paths, bad_anchors = [], []
        for line, t in rows:
            path, rest = md_links.split_target(t)
            dest = ROOT / md_links.to_root(path, file_dir) if path else ROOT / repo_path
            if not dest.exists():
                bad_paths.append({"line": line, "target": t})
            elif rest.startswith("#") and dest.suffix == ".md" and rest[1:] not in anchors(dest):
                bad_anchors.append({"line": line, "target": t})
        doc["files"][repo_path] = {
            "relative_targets": len(rows),
            "missing_paths": bad_paths,
            "missing_anchors": bad_anchors,
        }
        doc["missing_paths"] += len(bad_paths)
        doc["missing_anchors"] += len(bad_anchors)
        print(f"{repo_path}: {len(rows)} relative targets, {len(bad_paths)} missing paths, "
              f"{len(bad_anchors)} missing anchors")  # fmt: skip
        for b in bad_paths:
            print(f"  missing path  line {b['line']}: {b['target']}")
        for b in bad_anchors:
            print(f"  missing anchor line {b['line']}: {b['target']}")
    if a.report:
        Path(a.report).write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    return 0 if doc["missing_paths"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
