"""Write the README shown on the package index from README.md (the maintainer's decisions D5 and
F2, #218 comments 7207651312 and 7218843893). The repository's README.md does not change.

    python scripts/make_pypi_readme.py [--check]

It reads README.md and writes README-pypi.md, where every relative link or image target is made
absolute on GitHub:
- a link to a file or folder: https://github.com/klucilla/refute/blob/main/<path>
  (a folder: .../tree/main/<path>);
- an image (``src=``, ``srcset=``, or a Markdown image): https://raw.githubusercontent.com/
  klucilla/refute/main/<path>, so that it renders on the index.
Fragments and absolute URLs are kept. Nothing else changes. With ``--check`` it writes nothing
and exits 1 if README-pypi.md is not what it would write (the CI check that it is up to date).
The relative targets are those of scripts/md_links.py.
"""

from __future__ import annotations

import posixpath
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import md_links  # noqa: E402

BLOB = "https://github.com/klucilla/refute/blob/main/"
TREE = "https://github.com/klucilla/refute/tree/main/"
RAW = "https://raw.githubusercontent.com/klucilla/refute/main/"
IMAGE = re.compile(r"\.(svg|png|jpe?g|gif|webp)$", re.IGNORECASE)


def absolute(target: str) -> str:
    path, rest = md_links.split_target(target)
    if not path:
        return target
    norm = posixpath.normpath(path)
    if IMAGE.search(norm):
        return RAW + norm + rest
    if (ROOT / norm).is_dir() or path.endswith("/"):
        return TREE + norm + rest
    return BLOB + norm + rest


def render() -> str:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    return md_links.map_targets(text, absolute)


def main() -> int:
    out = render()
    target = ROOT / "README-pypi.md"
    if "--check" in sys.argv:
        ok = target.is_file() and target.read_text(encoding="utf-8") == out
        print("README-pypi.md is up to date" if ok else "README-pypi.md is stale")
        return 0 if ok else 1
    target.write_text(out, encoding="utf-8", newline="\n")
    print(f"wrote README-pypi.md ({len(out)} characters)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
