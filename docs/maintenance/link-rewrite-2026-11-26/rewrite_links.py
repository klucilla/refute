"""Re-prefix the moved relative links of one Markdown file, and nothing else (the maintainer's
decision of 2026-11-26, item M2; #218, comment 7204660147).

    .venv/Scripts/python.exe -B docs/maintenance/link-rewrite-2026-11-26/rewrite_links.py \
        FILE --after "MARKER LINE" [--from-dir DIR]

- The **moved block** is every line after the first line equal to ``MARKER LINE``. The lines up to
  and including it (the file's own header, already written for its folder) are not touched.
- In the moved block, every relative link target (``scripts/md_links.py``: Markdown links and
  images, HTML ``src``, ``href`` and ``srcset``; fenced code left alone) was written for the folder
  ``--from-dir`` (default: the repository root). It is rewritten so that it reaches the same path
  from the file's own folder; its fragment or query is kept.
- Nothing else changes: no text, no spacing, no line ending (the file is read and written as bytes
  decoded as UTF-8, with its line endings kept).

It prints how many targets changed. The moved-text checker (``scripts/check_moved_text.py
--normalize-links``) confirms afterwards that only link targets changed.
"""

from __future__ import annotations

import argparse
import posixpath
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import md_links  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--after", required=True)
    ap.add_argument("--from-dir", default="")
    a = ap.parse_args(argv)
    path = (ROOT / a.file).resolve()
    if ROOT not in path.parents:
        raise SystemExit(f"refused: {path} is outside the repository")
    rel_dir = posixpath.dirname(path.relative_to(ROOT).as_posix())
    data = path.read_bytes().decode("utf-8")
    lines = data.split("\n")
    marks = [i for i, line in enumerate(lines) if line.rstrip("\r") == a.after]
    if len(marks) != 1:
        raise SystemExit(f"refused: the marker line occurs {len(marks)} times, not once")
    changed = []

    def fix(t: str) -> str:
        new = md_links.from_root(md_links.to_root(t, a.from_dir), rel_dir)
        if new != t:
            changed.append((t, new))
        return new

    out = md_links.map_targets(data, fix, start_line=marks[0] + 1)
    path.write_bytes(out.encode("utf-8"))
    print(f"{a.file}: {len(changed)} targets re-prefixed from '{a.from_dir or '.'}' to '{rel_dir}'")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
