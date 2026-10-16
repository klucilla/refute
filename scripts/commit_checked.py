"""Commit only when ruff passes on the staged Python files.

CLAUDE.md: ruff runs before each commit, and the commit runs only if ruff exits with code 0.
The command guard (.claude/hooks/command_guard.py) refuses a direct ``git commit``; this
script is the way to commit.

Usage: python scripts/commit_checked.py [-q] (-m MESSAGE | -F FILE) [--no-edit]
       python scripts/commit_checked.py [-q] --no-edit        (a merge prepared with --no-commit)

1. The staged Python files (added, copied, modified or renamed) are listed from the index.
2. ``ruff check`` and ``ruff format --check`` run on them, with the repository's
   configuration and the folders CI excludes (``--force-exclude``). If either exits with a
   code other than 0, nothing is committed and the script exits with that code.
3. Otherwise ``git commit`` runs with the given options, and the script exits with git's
   code. With no staged Python file, ruff is not needed and the commit runs.

Only the options above are accepted. ``-a``/``--all``, ``--include``, ``--only``, pathspecs
and any other option are refused (exit 2) before anything runs, because they would commit
content that ruff did not check, or change what is committed.
"""

from __future__ import annotations

import subprocess
import sys

# the folders CI never lints (.github/workflows/ci.yml, CLAUDE.md): published records
EXCLUDE = (
    "calibration/*/audit",
    "docs/validation/v0.2.1/pre-document-runs",
    "docs/validation/v0.2.1/population",
)
VALUE_OPTIONS = {"-m", "--message", "-F", "--file"}
FLAG_OPTIONS = {"-q", "--quiet", "--no-edit"}


def parse(args: list[str]) -> tuple[list[str] | None, str]:
    """The git commit options, or None and the reason they are refused."""
    out: list[str] = []
    message = False
    k = 0
    while k < len(args):
        arg = args[k]
        name = arg.split("=", 1)[0] if arg.startswith("--") else arg
        if name in VALUE_OPTIONS:
            if "=" in arg and arg.startswith("--"):
                out.append(arg)
            else:
                if k + 1 >= len(args):
                    return None, f"{arg} needs a value"
                out += [arg, args[k + 1]]
                k += 1
            message = True
        elif arg in FLAG_OPTIONS:
            out.append(arg)
        else:
            return None, f"'{arg}' is not accepted (it could commit unchecked content)"
        k += 1
    if not message and "--no-edit" not in out:
        return None, "give a message (-m or -F), or --no-edit for a prepared merge"
    return out, ""


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8")


def main(argv: list[str]) -> int:
    options, reason = parse(argv)
    if options is None:
        print(f"commit_checked: {reason}; nothing was committed", file=sys.stderr)
        return 2
    top = git("rev-parse", "--show-toplevel")
    if top.returncode != 0:
        print("commit_checked: not inside a git repository", file=sys.stderr)
        return 2
    root = top.stdout.strip()
    staged = git("-C", root, "diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z")
    if staged.returncode != 0:
        print(f"commit_checked: cannot list the staged files: {staged.stderr}", file=sys.stderr)
        return 2
    files = [f for f in staged.stdout.split("\0") if f.endswith(".py")]
    if files:
        excludes = [x for e in EXCLUDE for x in ("--extend-exclude", e)]
        for step in (["check"], ["format", "--check"]):
            cmd = [sys.executable, "-m", "ruff", *step, "--force-exclude", *excludes, "--", *files]
            ruff = subprocess.run(cmd, cwd=root)
            if ruff.returncode != 0:
                print(
                    f"commit_checked: ruff {' '.join(step)} exited with {ruff.returncode}; "
                    "nothing was committed",
                    file=sys.stderr,
                )
                return ruff.returncode
        print(f"commit_checked: ruff passed on {len(files)} staged Python file(s)")
    commit = subprocess.run(["git", "-C", root, "commit", *options])
    return commit.returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
