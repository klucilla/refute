"""Commit only when ruff passes on the staged Python files, as they will be committed.

CLAUDE.md: ruff runs before each commit, and the commit runs only if ruff exits with code 0.
The command guard (.claude/hooks/command_guard.py) refuses a direct ``git commit``; this
script is the way to commit.

Usage: python scripts/commit_checked.py [-q] (-m MESSAGE | -F FILE) [--no-edit]
       python scripts/commit_checked.py [-q] --no-edit        (a merge prepared with --no-commit)

1. The script must run from a virtual environment; when the repository has a ``uv.lock``,
   the version of ``python -m ruff`` must be the locked one.
2. The staged tree is written (``git write-tree``) and the staged Python files (``.py``,
   ``.pyi``, ``.ipynb``; added, copied, modified, renamed or with a changed type) are listed
   with their blobs (``git ls-files -s``; an unresolved conflict is refused).
3. Ruff reads the **staged blobs** themselves (``git cat-file blob``), on its standard input
   with ``--stdin-filename``: the bytes ruff checks are the bytes git commits, whatever the
   work tree holds and whatever filters the repository defines. A partial commit is fine.
4. Ruff finds its configuration in the work tree, so every ruff configuration file that can
   apply (``pyproject.toml``, ``ruff.toml``, ``.ruff.toml`` in each file's folder and every
   parent folder up to the root, and every file they name with ``extend``, followed
   recursively) must hold the same content in the work tree and in the index, or be absent
   from both (line endings are not compared). An ``extend`` outside the repository, or
   with ``~`` or ``$``, is refused.
5. ``ruff check`` and ``ruff format --check`` run on each staged file, with the folders CI
   excludes (``--force-exclude``). If any run exits with a code other than 0, nothing is
   committed and the script exits with that code. The output says how many staged files
   ruff checked and how many fall in the excluded folders.
6. Just before the commit, the staged tree, the list and the configuration are read again;
   any change refuses the commit.
7. ``git commit`` runs with the given options. **Limit:** between step 6 and the moment
   git writes the commit, another process or a git hook could still change the index; this
   is not prevented. Afterwards the tree of the new commit is compared with the checked
   tree, and a difference is reported (exit 1): that detects it, it does not undo it.

Only the options above are accepted. ``-a``/``--all``, ``--include``, ``--only``, pathspecs
and any other option are refused (exit 2) before anything runs, because they would commit
content that ruff did not check, or change what is committed.
"""

from __future__ import annotations

import posixpath
import subprocess
import sys
import tomllib

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


class RefusedError(Exception):
    """A reason not to commit."""


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


def git(root: str, *args: str) -> str:
    out = subprocess.run(
        ["git", "-C", root, *args], capture_output=True, text=True, encoding="utf-8"
    )
    if out.returncode != 0:
        raise RefusedError(f"git {args[0]} failed: {out.stderr.strip()}")
    return out.stdout


def blob(root: str, sha: str) -> bytes:
    out = subprocess.run(["git", "-C", root, "cat-file", "blob", sha], capture_output=True)
    if out.returncode != 0:
        raise RefusedError(f"cannot read the blob {sha}")
    return out.stdout


def index_blobs(root: str, paths: list[str]) -> dict[str, str]:
    """The blob of each path in the index (stage 0); a path not in the index is left out."""
    if not paths:
        return {}
    blobs: dict[str, str] = {}
    for entry in git(root, "ls-files", "-s", "-z", "--", *paths).split("\0"):
        if not entry:
            continue
        meta, path = entry.split("\t", 1)
        _mode, sha, stage = meta.split()
        if stage != "0":
            raise RefusedError(f"{path} has an unresolved conflict")
        blobs[path] = sha
    return blobs


def ruff_version_check(root: str) -> None:
    """With a uv.lock, the ruff this interpreter runs must be the locked version."""
    lock = posixpath.join(root, "uv.lock")
    if not posixpath.isfile(lock):
        return
    with open(lock, "rb") as handle:
        packages = tomllib.load(handle).get("package", [])
    locked = {p.get("version") for p in packages if p.get("name") == "ruff"}
    out = subprocess.run(
        [sys.executable, "-m", "ruff", "--version"], capture_output=True, text=True
    )
    running = out.stdout.split()[-1] if out.returncode == 0 and out.stdout.split() else ""
    if locked and running not in locked:
        raise RefusedError(
            f"ruff {running or '(not found)'} is not the version in uv.lock {locked}"
        )


def _config_text(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n")


def _extends(path: str, data: bytes) -> list[str]:
    """The files a ruff configuration names with ``extend``, relative to the repository."""
    try:
        document = tomllib.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
        raise RefusedError(f"{path} is not valid TOML: {error}") from error
    section = (
        document.get("tool", {}).get("ruff", {}) if path.endswith("pyproject.toml") else document
    )
    value = section.get("extend") if isinstance(section, dict) else None
    if value is None:
        return []
    if not isinstance(value, str) or "~" in value or "$" in value:
        raise RefusedError(f"{path}: extend {value!r} cannot be checked")
    target = posixpath.normpath(posixpath.join(posixpath.dirname(path), value.replace("\\", "/")))
    if posixpath.isabs(target) or ":" in target or target.startswith(".."):
        raise RefusedError(f"{path}: extend {value!r} is outside the repository")
    return [target]


def config_state(root: str, files: list[str]) -> dict[str, bytes | None]:
    """The ruff configuration files that can apply to the files, with their content; the
    work tree and the index must agree on each one."""
    pending: list[str] = []
    for f in files:
        folder = posixpath.dirname(f)
        while True:
            pending += [posixpath.join(folder, n) if folder else n for n in CONFIG_NAMES]
            if not folder:
                break
            folder = posixpath.dirname(folder)
    state: dict[str, bytes | None] = {}
    while pending:
        path = pending.pop()
        if path in state:
            continue
        staged = index_blobs(root, [path]).get(path)
        staged_data = _config_text(blob(root, staged)) if staged else None
        full = posixpath.join(root, path)
        work_data = None
        if posixpath.isfile(full):
            with open(full, "rb") as handle:
                work_data = _config_text(handle.read())
        if staged_data != work_data:
            raise RefusedError(
                f"the work tree differs from the index for {path} (a ruff configuration): "
                "stage the change or set it aside"
            )
        state[path] = staged_data
        if staged_data is not None:
            pending += _extends(path, staged_data)
    return state


def staged_state(root: str) -> tuple[str, dict[str, str], dict[str, bytes | None]]:
    """The staged tree, the staged Python files with their blobs, and the configuration."""
    tree = git(root, "write-tree").strip()
    listed = git(root, "diff", "--cached", "--name-only", "--diff-filter=ACMRT", "-z")
    files = [f for f in listed.split("\0") if f.endswith(PYTHON_SUFFIXES)]
    blobs = index_blobs(root, files)
    return tree, blobs, config_state(root, files) if files else {}


def ruff_command(*args: str) -> list[str]:
    """``python -m ruff`` with this interpreter, the CI exclusions enforced."""
    excludes = [x for e in EXCLUDE for x in ("--extend-exclude", e)]
    return [sys.executable, "-m", "ruff", *args, "--force-exclude", *excludes]


def check_staged(root: str, blobs: dict[str, str]) -> int:
    """Run ruff on the staged blobs. Returns the number of files ruff checked (the others
    are in excluded folders), or minus ruff's exit code when a check failed."""
    files = sorted(blobs)
    missing = [f for f in files if not posixpath.isfile(posixpath.join(root, f))]
    if missing:  # --show-files needs the path; a staged file deleted from the work tree
        raise RefusedError(
            "a staged Python file is missing from the work tree: " + ", ".join(missing)
        )
    shown = subprocess.run(
        [*ruff_command("check", "--show-files"), "--", *files],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if shown.returncode != 0:
        raise RefusedError(f"ruff --show-files exited with {shown.returncode}")
    checked = len([line for line in shown.stdout.splitlines() if line.strip()])
    for f in files:
        data = blob(root, blobs[f])
        for step in (["check"], ["format", "--check"]):
            command = [*ruff_command(*step, "--stdin-filename", f), "-"]
            result = subprocess.run(command, cwd=root, input=data)
            if result.returncode != 0:
                print(
                    f"commit_checked: ruff {' '.join(step)} exited with {result.returncode} "
                    f"on the staged {f}; nothing was committed",
                    file=sys.stderr,
                )
                return -result.returncode or -1
    return checked


def main(argv: list[str]) -> int:
    options, reason = parse(argv)
    if options is None:
        print(f"commit_checked: {reason}; nothing was committed", file=sys.stderr)
        return 2
    try:
        if sys.prefix == sys.base_prefix:
            raise RefusedError("run this script with the project's virtual environment (.venv)")
        top = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if top.returncode != 0:
            raise RefusedError("not inside a git repository")
        root = top.stdout.strip()
        state = staged_state(root)
        tree, blobs, _config = state
        if blobs:
            ruff_version_check(root)
            checked = check_staged(root, blobs)
            if checked < 0:
                return -checked
            if staged_state(root) != state:
                raise RefusedError("the index or the ruff configuration changed while ruff ran")
            print(
                f"commit_checked: ruff passed on {checked} of {len(blobs)} staged Python "
                f"file(s) ({len(blobs) - checked} in folders CI excludes)"
            )
    except RefusedError as error:
        print(f"commit_checked: {error}; nothing was committed", file=sys.stderr)
        return 2
    commit = subprocess.run(["git", "-C", root, "commit", *options])
    if commit.returncode != 0:
        return commit.returncode
    head_tree = git(root, "rev-parse", "HEAD^{tree}").strip()
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
