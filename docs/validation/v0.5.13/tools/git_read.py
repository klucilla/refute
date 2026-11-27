"""A read-only git command, metered (v0.5.13; the unit ``git-read``).

    unit git-read:  {python} -I -B docs/validation/v0.5.13/tools/git_read.py <git arguments>

It runs ``git <arguments>`` only when the subcommand reads and never writes: ``rev-parse``,
``status``, ``diff``, ``log``, ``show``, ``ls-files``, ``ls-tree``, ``merge-base``, ``cat-file``,
``branch --show-current``. ``diff`` must carry ``--quiet``, ``--stat``, ``--name-only`` or
``--name-status`` or a path, so that its output stays small. Anything else is refused.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
READ_ONLY = {
    "rev-parse",
    "status",
    "diff",
    "log",
    "show",
    "ls-files",
    "ls-tree",
    "merge-base",
    "cat-file",
}


def main() -> int:
    args = sys.argv[1:]
    if not args:
        raise SystemExit("refused: no git arguments")
    sub = args[0]
    ok = sub in READ_ONLY or args[:2] == ["branch", "--show-current"]
    if not ok:
        raise SystemExit(f"refused: git {sub} is not a read-only subcommand of this unit")
    if sub == "merge-base" and "--is-ancestor" not in args and len(args) < 3:
        raise SystemExit("refused: merge-base needs two commits or --is-ancestor")
    return subprocess.run(["git", *args], cwd=ROOT).returncode


if __name__ == "__main__":
    raise SystemExit(main())
