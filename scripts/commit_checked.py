"""Commit only when ruff passes on the staged Python files, as they are staged.

CLAUDE.md: ruff runs before each commit, and the commit runs only if ruff exits with code 0.
The command guard (.claude/hooks/command_guard.py) refuses a direct ``git commit``; this
script is the way to commit.

Usage: python scripts/commit_checked.py [-q] (-m MESSAGE | -F FILE) [--no-edit]
       python scripts/commit_checked.py [-q] --no-edit        (a merge prepared with --no-commit)

1. The script must run from a virtual environment (the project's ``.venv``), so that ruff is
   the locked one; it runs ``python -m ruff`` with that interpreter.
2. The staged tree is written (``git write-tree``) and the staged Python files (``.py``,
   ``.pyi``, ``.ipynb``; added, copied, modified, renamed or with a changed type) are listed
   from the index.
3. Ruff reads files from the work tree, so the work tree must hold exactly the staged bytes:
   for every staged Python file, and for every ruff configuration file (``pyproject.toml``,
   ``ruff.toml``, ``.ruff.toml``) in its folder or a parent folder up to the repository root,
   the blob in the index and the blob of the work-tree file (``git hash-object``) must be the
   same, or both absent. Any difference is refused: stage the change, or set it aside, and
   run again. (A partial commit of a Python file, with other changes left unstaged, is
   therefore not possible through this script.)
4. ``ruff check`` and ``ruff format --check`` run on those files, with the folders CI
   excludes (``--force-exclude``). If either exits with a code other than 0, nothing is
   committed and the script exits with that code. The output says how many staged files
   ruff checked and how many fall in the excluded folders.
5. The staged tree is written again and step 3 is repeated; if anything changed while ruff
   ran, nothing is committed.
6. ``git commit`` runs with the given options. Afterwards the tree of the new commit is
   compared with the tree checked in step 2; a difference is reported (exit 1). With no
   staged Python file, ruff is not needed and the commit runs.

Only the options above are accepted. ``-a``/``--all``, ``--include``, ``--only``, pathspecs
and any other option are refused (exit 2) before anything runs, because they would commit
content that ruff did not check, or change what is committed.
"""

from __future__ import annotations

import posixpath
import subprocess
import sys

# the folders CI never lints (.github/workflows/ci.yml, CLAUDE.md): published records
EXCLUDE = (
    "calibration/*/audit",
    "docs/validation/v0.2.1/pre-document-runs",
    "docs/validation/v0.2.1/population",
)
PYTHON_SUFFIXES = (".py", ".pyi", ".ipynb")
CONFIG_NAMES = ("pyproject.toml", "ruff.toml", ".ruff.toml")
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


def git(root: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", root, *args], capture_output=True, text=True, encoding="utf-8"
    )


def config_paths(files: list[str]) -> list[str]:
    """The ruff configuration files that can apply to the files: in each file's folder and
    in every parent folder up to the repository root (repository-relative, with '/')."""
    found: set[str] = set()
    for f in files:
        folder = posixpath.dirname(f)
        while True:
            for name in CONFIG_NAMES:
                found.add(posixpath.join(folder, name) if folder else name)
            if not folder:
                break
            folder = posixpath.dirname(folder)
    return sorted(found)


def index_blobs(root: str, paths: list[str]) -> dict[str, str]:
    """The blob of each path in the index (stage 0); a path not in the index is left out."""
    out = git(root, "ls-files", "-s", "-z", "--", *paths)
    if out.returncode != 0:
        raise RuntimeError(f"cannot read the index: {out.stderr.strip()}")
    blobs: dict[str, str] = {}
    for entry in out.stdout.split("\0"):
        if not entry:
            continue
        meta, path = entry.split("\t", 1)
        _mode, blob, stage = meta.split()
        if stage != "0":
            raise RuntimeError(f"{path} has an unresolved conflict")
        blobs[path] = blob
    return blobs


def work_blobs(root: str, paths: list[str]) -> dict[str, str]:
    """The blob git would store for each work-tree file that exists (``git hash-object``,
    with the repository's filters); a path that is not a file is left out."""
    existing = [p for p in paths if posixpath.isfile(posixpath.join(root, p))]
    if not existing:
        return {}
    out = git(root, "hash-object", "--", *existing)
    if out.returncode != 0:
        raise RuntimeError(f"cannot hash the work tree: {out.stderr.strip()}")
    return dict(zip(existing, out.stdout.split(), strict=True))


def differences(root: str, paths: list[str]) -> list[str]:
    """The paths whose work-tree bytes are not the staged bytes (or exist on one side only)."""
    if not paths:
        return []
    staged, work = index_blobs(root, paths), work_blobs(root, paths)
    return [p for p in paths if staged.get(p) != work.get(p)]


def staged_state(root: str) -> tuple[str, list[str]]:
    """The staged tree and the staged Python files."""
    tree = git(root, "write-tree")
    if tree.returncode != 0:
        raise RuntimeError(f"cannot write the staged tree: {tree.stderr.strip()}")
    listed = git(root, "diff", "--cached", "--name-only", "--diff-filter=ACMRT", "-z")
    if listed.returncode != 0:
        raise RuntimeError(f"cannot list the staged files: {listed.stderr.strip()}")
    files = [f for f in listed.stdout.split("\0") if f.endswith(PYTHON_SUFFIXES)]
    return tree.stdout.strip(), files


def refuse(reason: str, code: int = 2) -> int:
    print(f"commit_checked: {reason}; nothing was committed", file=sys.stderr)
    return code


def main(argv: list[str]) -> int:
    options, reason = parse(argv)
    if options is None:
        return refuse(reason)
    if sys.prefix == sys.base_prefix:
        return refuse("run this script with the project's virtual environment (.venv)")
    top = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, encoding="utf-8"
    )
    if top.returncode != 0:
        return refuse("not inside a git repository")
    root = top.stdout.strip()
    try:
        tree, files = staged_state(root)
        diverging = differences(root, files + config_paths(files) if files else [])
    except RuntimeError as error:
        return refuse(str(error))
    if diverging:
        return refuse(
            "the work tree differs from the index for "
            + ", ".join(diverging)
            + " (ruff would not read the staged bytes): stage the change or set it aside"
        )
    if files:
        excludes = [x for e in EXCLUDE for x in ("--extend-exclude", e)]
        ruff = [sys.executable, "-m", "ruff"]
        listed = subprocess.run(
            [*ruff, "check", "--show-files", "--force-exclude", *excludes, "--", *files],
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if listed.returncode != 0:
            return refuse(f"ruff --show-files exited with {listed.returncode}", listed.returncode)
        checked = len([line for line in listed.stdout.splitlines() if line.strip()])
        for step in (["check"], ["format", "--check"]):
            cmd = [*ruff, *step, "--force-exclude", *excludes, "--", *files]
            result = subprocess.run(cmd, cwd=root)
            if result.returncode != 0:
                return refuse(
                    f"ruff {' '.join(step)} exited with {result.returncode}", result.returncode
                )
        try:
            tree_after, files_after = staged_state(root)
            diverging = differences(root, files_after + config_paths(files_after))
        except RuntimeError as error:
            return refuse(str(error))
        if tree_after != tree or files_after != files or diverging:
            return refuse("the index or the work tree changed while ruff ran")
        print(
            f"commit_checked: ruff passed on {checked} of {len(files)} staged Python file(s) "
            f"({len(files) - checked} in folders CI excludes)"
        )
    commit = subprocess.run(["git", "-C", root, "commit", *options])
    if commit.returncode != 0:
        return commit.returncode
    head_tree = git(root, "rev-parse", "HEAD^{tree}").stdout.strip()
    if head_tree != tree:
        print(
            f"commit_checked: the new commit's tree {head_tree} is not the checked tree {tree}; "
            "do not push it, and tell the maintainer",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
