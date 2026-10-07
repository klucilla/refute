"""Source-tree hash (``refute-code-1``) and git state.

The code hash covers every regular file under ``src/`` (excluding ``__pycache__``
directories, compiled Python files and packaging metadata) plus ``pyproject.toml``
and ``uv.lock`` at the project root. For each file the POSIX path relative to the
project root and the file's SHA-256 (text files with CRLF normalized to LF) form a
line ``"<sha256>  <path>\\n"``. Lines are sorted by path and the SHA-256 of their
concatenation is the code hash.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from refute.core.hashing import sha256_bytes, sha256_text_normalized

CODE_ALGORITHM = "refute-code-1"
_ROOT_FILES = ("pyproject.toml", "uv.lock")
_EXCLUDED_DIR_NAMES = {"__pycache__"}
_EXCLUDED_DIR_SUFFIXES = (".egg-info", ".dist-info")
_EXCLUDED_FILE_SUFFIXES = (".pyc", ".pyo")
_EXCLUDED_FILE_NAMES = {".DS_Store", "Thumbs.db"}


class CodeHashError(Exception):
    """The project root cannot be found or read."""


@dataclass(frozen=True)
class CodeHash:
    algorithm: str
    sha256: str
    files: tuple[tuple[str, str], ...]

    def to_dict(self) -> dict:
        return {
            "algorithm": self.algorithm,
            "sha256": self.sha256,
            "files": [{"path": p, "sha256": h} for p, h in self.files],
        }


def project_root() -> Path:
    """Root of the Refute source tree that is currently running.

    Refute is installed in editable mode by ``uv sync``, so the running package is
    ``<root>/src/refute``. The root must contain ``pyproject.toml``.
    """
    import refute

    package_dir = Path(refute.__file__).resolve().parent
    candidate = package_dir.parent.parent
    if (candidate / "pyproject.toml").is_file() and (candidate / "src" / "refute").is_dir():
        return candidate
    raise CodeHashError(
        "cannot locate the Refute source tree (expected <root>/src/refute and "
        "<root>/pyproject.toml); install Refute from a source checkout with `uv sync`"
    )


def _is_excluded(relative: Path) -> bool:
    for part in relative.parts[:-1]:
        if part in _EXCLUDED_DIR_NAMES or part.endswith(_EXCLUDED_DIR_SUFFIXES):
            return True
    name = relative.name
    return name in _EXCLUDED_FILE_NAMES or name.endswith(_EXCLUDED_FILE_SUFFIXES)


def code_files(root: Path) -> list[Path]:
    """Files covered by the code hash, as absolute paths sorted by relative POSIX path."""
    root = Path(root)
    src = root / "src"
    if not src.is_dir():
        raise CodeHashError(f"no src/ directory under {root}")
    files = [
        path
        for path in src.rglob("*")
        if path.is_file() and not _is_excluded(path.relative_to(root))
    ]
    files.extend(root / name for name in _ROOT_FILES if (root / name).is_file())
    return sorted(files, key=lambda p: p.relative_to(root).as_posix())


def compute_code_hash(root: Path | None = None) -> CodeHash:
    root = project_root() if root is None else Path(root)
    entries = [
        (path.relative_to(root).as_posix(), sha256_text_normalized(path))
        for path in code_files(root)
    ]
    entries.sort(key=lambda item: item[0])
    text = "".join(f"{digest}  {rel}\n" for rel, digest in entries)
    return CodeHash(CODE_ALGORITHM, sha256_bytes(text.encode("utf-8")), tuple(entries))


def diff_code_files(locked: list[dict], current: CodeHash) -> list[str]:
    """Human-readable list of files that differ between a lock and the current tree."""
    before = {item["path"]: item["sha256"] for item in locked}
    after = dict(current.files)
    changes = []
    for path in sorted(set(before) | set(after)):
        if path not in after:
            changes.append(f"removed: {path}")
        elif path not in before:
            changes.append(f"added: {path}")
        elif before[path] != after[path]:
            changes.append(f"modified: {path}")
    return changes


@dataclass
class GitState:
    toplevel: Path | None = None
    commit: str | None = None
    dirty_paths: list[str] = field(default_factory=list)

    @property
    def is_repo(self) -> bool:
        return self.toplevel is not None

    @property
    def dirty(self) -> bool | None:
        if not self.is_repo:
            return None
        return bool(self.dirty_paths)


def _git(args: list[str], cwd: Path) -> str | None:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            capture_output=True,
            check=False,
        )
    except (FileNotFoundError, OSError):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.decode("utf-8", errors="replace")


def _parse_porcelain_z(output: str) -> list[str]:
    paths: list[str] = []
    entries = output.split("\0")
    index = 0
    while index < len(entries):
        entry = entries[index]
        index += 1
        if len(entry) < 4:
            continue
        status, path = entry[:2], entry[3:]
        paths.append(path)
        if status[0] in "RC":
            # renames and copies are followed by the original path
            if index < len(entries) and entries[index]:
                paths.append(entries[index])
            index += 1
    return paths


def git_state(path: Path) -> GitState:
    """Git commit and uncommitted changes for the repository containing ``path``."""
    directory = Path(path)
    if directory.is_file():
        directory = directory.parent
    top = _git(["rev-parse", "--show-toplevel"], directory)
    if top is None:
        return GitState()
    toplevel = Path(top.strip())
    commit_out = _git(["rev-parse", "--verify", "HEAD"], directory)
    commit = commit_out.strip() if commit_out else None
    status = _git(["status", "--porcelain=v1", "-z", "--untracked-files=all"], toplevel)
    dirty = _parse_porcelain_z(status) if status else []
    return GitState(toplevel=toplevel, commit=commit, dirty_paths=sorted(set(dirty)))


def relative_to_toplevel(state: GitState, path: Path) -> str | None:
    if state.toplevel is None:
        return None
    try:
        return Path(path).resolve().relative_to(state.toplevel.resolve()).as_posix()
    except ValueError:
        return None
