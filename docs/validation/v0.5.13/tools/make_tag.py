"""Create one annotated tag on one commit and push that tag alone (the maintainer's decision F3,
#218 comment 7218843893: "the annotated tag v0.5.12 on that commit, one tag, alone").

    unit make-tag:  {python} -I -B docs/validation/v0.5.13/tools/make_tag.py <tag> <commit> <msg>

(``<msg>`` is the path of the tag message file.)

It refuses if the tag already exists, locally or on ``origin``. It runs
``git tag -a <tag> <commit> -F <message file>``, checks that the tag points at the full commit,
and runs ``git push origin refs/tags/<tag>`` (that ref only, never ``--tags``). It creates no
GitHub release.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)


def main() -> int:
    tag, commit, message = sys.argv[1], sys.argv[2], sys.argv[3]
    full = git("rev-parse", f"{commit}^{{commit}}").stdout.strip()
    if git("rev-parse", "-q", "--verify", f"refs/tags/{tag}").returncode == 0:
        raise SystemExit(f"refused: tag {tag} exists locally")
    remote = git("ls-remote", "--tags", "origin", f"refs/tags/{tag}")
    if remote.returncode != 0 or remote.stdout.strip():
        raise SystemExit(f"refused: tag {tag} exists on origin, or origin could not be read")
    made = git("tag", "-a", tag, full, "-F", message)
    if made.returncode != 0:
        raise SystemExit(f"refused: git tag failed: {made.stderr.strip()}")
    target = git("rev-parse", f"refs/tags/{tag}^{{commit}}").stdout.strip()
    if target != full:
        raise SystemExit(f"refused: the tag points at {target}, not {full}")
    pushed = git("push", "origin", f"refs/tags/{tag}")
    print(f"tag {tag} -> {full}; push exit {pushed.returncode}")
    print(pushed.stderr.strip())
    return pushed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
