"""Check that a text moved between files lost nothing and changed nothing.

The maintainer's decisions of 2026-11-26 (#218, comment 7203695669, items A1, A2 and A3)
move parts of ``ROADMAP.md``, ``CLAUDE.md`` and ``README.md`` *literally* to other files.
This script checks such a move: every unit of the old file must appear in the new files,
as many times as it appeared before, byte for byte after the normalisation stated below.

Two units are available:

- ``lines`` (the default): each non-blank line, with trailing white space removed. The
  old file's lines are a multiset; the new files' lines are pooled into one multiset; a
  line of the old file that the pool does not cover (as many times) is **missing**.
- ``sentences``: each file is cut into chunks (a blank line, a heading line, a table row
  and the start of a list item each start a new chunk), the lines of a chunk are joined
  with single spaces, white space is collapsed, and the chunk is cut into sentences after
  ``.``, ``!``, ``?`` or ``:`` followed by white space. The multiset comparison is the same.
  This unit is insensitive to line wrapping, and still sees any changed word.

What the new files hold beyond the old file (new headings, a table, the triggers that
point to a moved section) is reported as **added**, so that a reader sees exactly what is
new. The check passes (exit 0) when nothing is missing; it fails (exit 1) otherwise.

With ``--normalize-links`` (the maintainer's decision of 2026-11-26, item M2), every relative link
target of the old and the new texts is first put in its repository-root form
(``scripts/md_links.py``), each from its own folder: the old file's (``--old-dir``, by default the
folder of ``--old``) and each new file's (``--location NEW=FOLDER``, by default its own folder).
A move that only re-prefixed links then compares equal; any other change still shows.

The old file is read from git (``--old-rev REV --old PATH``, through ``git show``) or from
disk (``--old-file PATH``); the new files are read from disk. Nothing is written except the
optional JSON report (``--report``). No network.

Usage::

    python scripts/check_moved_text.py --old-rev 02b6ddf --old ROADMAP.md \
        --new ROADMAP.md --new docs/history/roadmap-archive.md --unit lines
"""

from __future__ import annotations

import argparse
import json
import posixpath
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

_CHUNK_START = re.compile(r"^(#{1,6}\s|\||\s*[-*+]\s|\s*\d+[.)]\s)")
_SENTENCE_END = re.compile(r"(?<=[.!?:])\s+")


def lines_of(text: str) -> list[str]:
    """The non-blank lines of ``text``, trailing white space removed."""
    return [line.rstrip() for line in text.splitlines() if line.strip()]


def chunks_of(text: str) -> list[str]:
    """The chunks of ``text``: paragraphs, cut again at headings, table rows and list items."""
    chunks: list[list[str]] = []
    current: list[str] = []
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip():
            if current:
                chunks.append(current)
            current = []
            continue
        if current and _CHUNK_START.match(line):
            chunks.append(current)
            current = []
        current.append(line.strip())
    if current:
        chunks.append(current)
    return [" ".join(" ".join(chunk).split()) for chunk in chunks]


def sentences_of(text: str) -> list[str]:
    """The sentences of ``text`` (see the module's docstring)."""
    found: list[str] = []
    for chunk in chunks_of(text):
        found.extend(part for part in _SENTENCE_END.split(chunk) if part)
    return found


UNITS = {"lines": lines_of, "sentences": sentences_of}


def compare(old_text: str, new_texts: dict[str, str], unit: str) -> dict:
    """The comparison of the old text with the pooled new texts, as a JSON-ready dict."""
    split = UNITS[unit]
    old = Counter(split(old_text))
    pooled: Counter[str] = Counter()
    per_file: dict[str, Counter[str]] = {}
    for name, text in new_texts.items():
        per_file[name] = Counter(split(text))
        pooled.update(per_file[name])
    missing = old - pooled
    added = pooled - old
    where_added = {name: sorted((counts - old).elements()) for name, counts in per_file.items()}
    return {
        "unit": unit,
        "old_units": sum(old.values()),
        "new_units": sum(pooled.values()),
        "missing_count": sum(missing.values()),
        "added_count": sum(added.values()),
        "missing": sorted(missing.elements()),
        "added_by_file": {k: v for k, v in where_added.items() if v},
        "passed": not missing,
    }


def normalized(text: str, file_dir: str) -> str:
    """``text`` with its relative link targets in repository-root form (``md_links``), so that a
    move that only re-prefixed links compares equal (the maintainer's decision of 2026-11-26,
    item M2)."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import md_links

    return md_links.normalize(text, file_dir)


def location(name: str, declared: dict[str, str]) -> str:
    """The repository folder a new file lives in: declared with ``--location``, or its own."""
    return declared.get(name, posixpath.dirname(Path(name).as_posix()))


def read_old(rev: str | None, path: str | None, file: str | None) -> tuple[str, str]:
    """The old text and a label for it."""
    if file:
        return Path(file).read_text(encoding="utf-8"), file
    if not (rev and path):
        raise SystemExit("give --old-file, or both --old-rev and --old")
    out = subprocess.run(
        ["git", "show", f"{rev}:{path}"], capture_output=True, check=True
    ).stdout.decode("utf-8")
    return out, f"{rev}:{path}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--old-rev")
    parser.add_argument("--old")
    parser.add_argument("--old-file")
    parser.add_argument("--new", action="append", required=True)
    parser.add_argument("--unit", choices=sorted(UNITS), default="lines")
    parser.add_argument("--report")
    parser.add_argument("--normalize-links", action="store_true")
    parser.add_argument("--old-dir", default=None, help="the old file's repository folder")
    parser.add_argument(
        "--location", action="append", default=[], help="NEW=FOLDER: a new file's repository folder"
    )
    args = parser.parse_args(argv)
    old_text, label = read_old(args.old_rev, args.old, args.old_file)
    new_texts = {name: Path(name).read_text(encoding="utf-8") for name in args.new}
    if args.normalize_links:
        declared = dict(item.split("=", 1) for item in args.location)
        old_dir = args.old_dir
        if old_dir is None:
            old_dir = posixpath.dirname(Path(args.old).as_posix()) if args.old else ""
        old_text = normalized(old_text, old_dir)
        new_texts = {n: normalized(t, location(n, declared)) for n, t in new_texts.items()}
    result = {"old": label, "new": args.new, **compare(old_text, new_texts, args.unit)}
    result["links_normalized"] = args.normalize_links
    if args.report:
        Path(args.report).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"old: {label} ({result['old_units']} {args.unit})")
    print(f"new: {', '.join(args.new)} ({result['new_units']} {args.unit})")
    print(f"missing: {result['missing_count']}")
    for item in result["missing"]:
        print(f"  - {item}")
    print(f"added: {result['added_count']}")
    for name, items in result["added_by_file"].items():
        print(f"  {name}:")
        for item in items:
            print(f"    + {item}")
    print("PASS" if result["passed"] else "FAIL")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
