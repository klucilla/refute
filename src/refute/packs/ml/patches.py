"""The allowed patches of a claim, parsed and applied by Refute's own code (WP3 W3.9a,
docs/validation/v0.3/wp3-allowed-patches-acceptance.md).

A patch is a unified diff in the git form, read by a small closed grammar on bytes:
modifications and creations of text files only, hunks applied at their exact stated
lines (no fuzz, no search at another position), nothing normalized. ``parse`` reads one
patch; ``apply_text`` applies a file's hunks to its bytes in memory; ``plan`` checks a
claim's patches together (order, limits, one file in one patch). Writing the result into
a tree is ``write_tree`` (Linux, relative to open folders). Any refusal raises
``PatchError``.
"""

from __future__ import annotations

import errno
import hashlib
import os
import re
import shutil
import stat
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any

MAX_PATCH_BYTES = 1 << 20
MAX_PATCH_FILES = 50
MAX_PATCH_HUNKS = 500
MAX_CLAIM_BYTES = 4 << 20
MAX_CLAIM_FILES = 100
MAX_CLAIM_HUNKS = 1000
MAX_FILE_BYTES = 16 << 20

_PATH = re.compile(r"^[!-~]+$")  # printable ASCII without space
_FORBIDDEN = set("\"'\\")
_HUNK = re.compile(rb"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(?: .*)?$")
_INDEX = re.compile(rb"^index [0-9a-f]{7,64}\.\.[0-9a-f]{7,64}(?: (100644|100755))?$")
NO_NEWLINE = b"\\ No newline at end of file"


class PatchError(ValueError):
    """The patch is refused: nothing is applied."""


@dataclass
class Hunk:
    a: int
    b: int
    c: int
    d: int
    old: list[bytes] = field(default_factory=list)  # context and removed lines, in order
    new: list[bytes] = field(default_factory=list)  # context and added lines, in order


@dataclass
class FilePatch:
    path: str
    create: bool
    mode: str | None  # the mode of the index line, if any
    hunks: list[Hunk]


def check_path(path: str) -> str:
    """A relative POSIX path of printable ASCII with no space, quote or backslash, no
    ``..``, ``.`` or empty component, not under ``.git`` or ``.refute``."""
    if not path or not _PATH.match(path) or _FORBIDDEN & set(path):
        raise PatchError(f"path {path!r} is outside the grammar")
    parts = path.split("/")
    if path.startswith("/") or any(p in ("", ".", "..") for p in parts):
        raise PatchError(f"path {path!r} is not a plain relative path")
    if parts[0] in (".git", ".refute"):
        raise PatchError(f"path {path!r} is under {parts[0]}")
    return path


def _lines(data: bytes) -> list[bytes]:
    """Lines split on LF only, each keeping its LF (a CR stays a byte of its line)."""
    out, start = [], 0
    while start < len(data):
        end = data.find(b"\n", start)
        if end < 0:
            out.append(data[start:])
            break
        out.append(data[start : end + 1])
        start = end + 1
    return out


def _strip_lf(line: bytes) -> bytes:
    return line[:-1] if line.endswith(b"\n") else line


def parse(data: bytes) -> list[FilePatch]:
    if len(data) > MAX_PATCH_BYTES:
        raise PatchError(f"a patch of {len(data)} bytes is over {MAX_PATCH_BYTES}")
    if not data.endswith(b"\n"):
        raise PatchError("a patch ends with a newline")
    lines = [_strip_lf(x) for x in _lines(data)]
    files: list[FilePatch] = []
    seen: set[str] = set()
    i = 0
    while i < len(lines):
        header = lines[i]
        m = re.match(rb"^diff --git a/(\S+) b/(\S+)$", header)
        if m is None or m.group(1) != m.group(2):
            raise PatchError(f"line {i + 1}: expected 'diff --git a/<p> b/<p>'")
        path = check_path(m.group(1).decode("ascii"))
        if path in seen:
            raise PatchError(f"{path}: two blocks for one file")
        seen.add(path)
        i += 1
        create = False
        if i < len(lines) and lines[i] == b"new file mode 100644":
            create, i = True, i + 1
        mode = None
        if i < len(lines) and lines[i].startswith(b"index "):
            im = _INDEX.match(lines[i])
            if im is None:
                raise PatchError(f"line {i + 1}: an index line outside the grammar")
            mode = im.group(1).decode() if im.group(1) else None
            if create and mode not in (None, "100644"):
                raise PatchError(f"{path}: a created file is 100644")
            i += 1
        old = b"--- /dev/null" if create else b"--- a/" + path.encode()
        if i + 1 >= len(lines) or lines[i] != old or lines[i + 1] != b"+++ b/" + path.encode():
            raise PatchError(f"line {i + 1}: expected the --- and +++ lines of {path}")
        i += 2
        hunks: list[Hunk] = []
        while i < len(lines) and not lines[i].startswith(b"diff --git "):
            hunk, i = _hunk(lines, i, path)
            hunks.append(hunk)
        if not hunks:
            raise PatchError(f"{path}: no hunk")
        _check_order(hunks, path, create)
        files.append(FilePatch(path, create, mode, hunks))
    if not files:
        raise PatchError("an empty patch")
    if len(files) > MAX_PATCH_FILES:
        raise PatchError(f"{len(files)} files in one patch, over {MAX_PATCH_FILES}")
    if sum(len(f.hunks) for f in files) > MAX_PATCH_HUNKS:
        raise PatchError(f"over {MAX_PATCH_HUNKS} hunks in one patch")
    return files


def _hunk(lines: list[bytes], i: int, path: str) -> tuple[Hunk, int]:
    m = _HUNK.match(lines[i])
    if m is None:
        raise PatchError(f"line {i + 1}: expected a hunk header of {path}")
    a, c = int(m.group(1)), int(m.group(3))
    b = 1 if m.group(2) is None else int(m.group(2))
    d = 1 if m.group(4) is None else int(m.group(4))
    hunk = Hunk(a, b, c, d)
    i += 1
    old_done = new_done = False  # a "No newline" marker closed that side
    while len(hunk.old) < b or len(hunk.new) < d:
        if i >= len(lines):
            raise PatchError(f"{path}: a hunk is cut short")
        line, tag = lines[i], lines[i][:1]
        body = line[1:] + b"\n"
        if tag == b" ":
            if old_done or new_done:
                raise PatchError(f"line {i + 1}: a line after 'No newline'")
            hunk.old.append(body)
            hunk.new.append(body)
            last = "both"
        elif tag == b"-":
            if old_done:
                raise PatchError(f"line {i + 1}: a line after 'No newline'")
            hunk.old.append(body)
            last = "old"
        elif tag == b"+":
            if new_done:
                raise PatchError(f"line {i + 1}: a line after 'No newline'")
            hunk.new.append(body)
            last = "new"
        else:
            raise PatchError(f"line {i + 1}: neither context, removed nor added")
        i += 1
        if i < len(lines) and lines[i] == NO_NEWLINE:
            # the line just read has no final newline: it must be the last of its side(s)
            if last in ("old", "both"):
                hunk.old[-1] = hunk.old[-1][:-1]
                old_done = True
            if last in ("new", "both"):
                hunk.new[-1] = hunk.new[-1][:-1]
                new_done = True
            i += 1
        if len(hunk.old) > b or len(hunk.new) > d:
            raise PatchError(f"{path}: a hunk holds more lines than its counts")
    if old_done and len(hunk.old) != b or new_done and len(hunk.new) != d:
        raise PatchError(f"{path}: 'No newline' before the last line of its side")
    if i < len(lines) and lines[i] == NO_NEWLINE:
        raise PatchError(f"line {i + 1}: a misplaced 'No newline'")
    return hunk, i


def _check_order(hunks: list[Hunk], path: str, create: bool) -> None:
    delta, end = 0, 0
    for h in hunks:
        if create and not (h.a == 0 and h.b == 0 and h.c == 1 and len(hunks) == 1):
            raise PatchError(f"{path}: a creation is one hunk @@ -0,0 +1,N @@")
        start = h.a if h.b > 0 else h.a + 1  # the first original line the hunk covers
        if start <= end and not (create and h.a == 0):
            raise PatchError(f"{path}: hunks out of order or overlapping")
        expected_c = start + delta - (1 if h.d == 0 else 0)
        if h.c != expected_c:
            raise PatchError(f"{path}: hunk at -{h.a} has +{h.c}, expected +{expected_c}")
        delta += h.d - h.b
        end = h.a + h.b - 1 if h.b > 0 else h.a


def apply_text(original: bytes | None, fp: FilePatch) -> bytes:
    """The file's bytes after its hunks, each at its exact stated line."""
    if fp.create:
        if original is not None:
            raise PatchError(f"{fp.path}: a creation of an existing file")
        result = b"".join(fp.hunks[0].new)
    else:
        if original is None:
            raise PatchError(f"{fp.path}: a modification of a missing file")
        _check_text(original, fp.path, "before")
        src = _lines(original)
        out: list[bytes] = []
        pos = 0  # index in src of the next line not yet copied
        for h in fp.hunks:
            start = h.a - 1 if h.b > 0 else h.a
            if start < pos or start + h.b > len(src):
                raise PatchError(f"{fp.path}: hunk at -{h.a} outside the file")
            if src[start : start + h.b] != h.old:
                raise PatchError(f"{fp.path}: hunk at -{h.a} does not match at its line")
            out.extend(src[pos:start])
            out.extend(h.new)
            pos = start + h.b
        out.extend(src[pos:])
        result = b"".join(out)
    _check_text(result, fp.path, "after")
    return result


def _check_text(data: bytes, path: str, when: str) -> None:
    if len(data) > MAX_FILE_BYTES:
        raise PatchError(f"{path}: over {MAX_FILE_BYTES} bytes {when} the patch")
    if b"\x00" in data:
        raise PatchError(f"{path}: a NUL byte {when} the patch")
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        raise PatchError(f"{path}: not UTF-8 {when} the patch") from None


def plan(patches: list[tuple[str, bytes]], data_paths: list[str]) -> list[list[FilePatch]]:
    """A claim's patches parsed together, in their listed order: the limits of the claim,
    one file in one patch only, and no data path, path under one or folder above one."""
    total = sum(len(b) for _, b in patches)
    if total > MAX_CLAIM_BYTES:
        raise PatchError(f"the claim's patches hold {total} bytes, over {MAX_CLAIM_BYTES}")
    parsed = [parse(b) for _, b in patches]
    files = [fp for p in parsed for fp in p]
    if len(files) > MAX_CLAIM_FILES:
        raise PatchError(f"{len(files)} files in the claim's patches, over {MAX_CLAIM_FILES}")
    if sum(len(fp.hunks) for fp in files) > MAX_CLAIM_HUNKS:
        raise PatchError(f"over {MAX_CLAIM_HUNKS} hunks in the claim's patches")
    paths = [fp.path for fp in files]
    if len(set(paths)) != len(paths):
        raise PatchError("one file is touched by two patches")
    lowered = [p.lower() for p in paths]
    if len(set(lowered)) != len(lowered):
        raise PatchError("two patched paths differ by case only")
    data = [PurePosixPath(d).parts for d in data_paths]
    for p in paths:
        parts = PurePosixPath(p).parts
        for d in data:
            n = min(len(parts), len(d))
            if parts[:n] == d[:n]:
                raise PatchError(f"{p} is a data path, under one, or a folder above one")
    return parsed


# ---- the tree: anchor on the commit, manifests, writing (Linux) -------------------------------

TEMP_PREFIX = ".refute-patch-"


def blob_sha1(data: bytes) -> str:
    """Git's object id of a blob."""
    return hashlib.sha1(b"blob %d\x00" % len(data) + data, usedforsecurity=False).hexdigest()


def commit_entries(git_ls_tree_z: str) -> dict[str, tuple[str, str]]:
    """``git ls-tree -r -z --full-tree <commit>`` output -> {path: (mode, blob id)}. A
    submodule or any entry that is not a blob is refused."""
    out: dict[str, tuple[str, str]] = {}
    for record in git_ls_tree_z.split("\x00"):
        if not record:
            continue
        meta, path = record.split("\t", 1)
        mode, kind, oid = meta.split(" ")
        if kind != "blob" or mode not in ("100644", "100755", "120000"):
            raise PatchError(f"{path}: a {kind} of mode {mode} is not supported in the tree")
        out[path] = (mode, oid)
    return out


def _walk(root: Path) -> list[tuple[str, os.stat_result]]:
    """Every entry under ``root`` but ``.git``, without following links."""
    out = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        rel_dir = Path(dirpath).relative_to(root)
        if rel_dir == Path("."):
            dirnames[:] = [d for d in dirnames if d != ".git"]
        for name in [*dirnames, *filenames]:
            p = Path(dirpath) / name
            out.append(((rel_dir / name).as_posix(), os.lstat(p)))
    return sorted(out)


def anchor(root: Path, entries: dict[str, tuple[str, str]]) -> None:
    """The content tree under ``root`` (without ``.git``) is exactly the commit's tree:
    the same files and links, modes and blobs, and no other file."""
    files = {}
    for rel, st in _walk(root):
        if stat.S_ISDIR(st.st_mode):
            continue
        files[rel] = st
    extra = sorted(set(files) - set(entries))
    missing = sorted(set(entries) - set(files))
    if extra or missing:
        raise PatchError(f"the clone is not the commit's tree: extra {extra}, missing {missing}")
    for rel, (mode, oid) in entries.items():
        st, p = files[rel], root / rel
        if mode == "120000":
            if not stat.S_ISLNK(st.st_mode) or blob_sha1(os.readlink(p).encode()) != oid:
                raise PatchError(f"{rel}: not the commit's link")
            continue
        if not stat.S_ISREG(st.st_mode) or blob_sha1(p.read_bytes()) != oid:
            raise PatchError(f"{rel}: not the commit's file")
        if (mode == "100755") != bool(st.st_mode & 0o100):
            raise PatchError(f"{rel}: its executable bit is not the commit's")


def manifest(root: Path) -> dict[str, dict[str, Any]]:
    """Content manifest: path -> type, mode, size and SHA-256 (a link: its target, never
    followed; a folder: its mode). ``.git`` is left out."""
    out: dict[str, dict[str, Any]] = {}
    for rel, st in _walk(root):
        mode = stat.S_IMODE(st.st_mode)
        if stat.S_ISLNK(st.st_mode):
            out[rel] = {"type": "link", "target": os.readlink(root / rel)}
        elif stat.S_ISDIR(st.st_mode):
            out[rel] = {"type": "dir", "mode": mode}
        elif stat.S_ISREG(st.st_mode):
            data = (root / rel).read_bytes()
            out[rel] = {
                "type": "file",
                "mode": mode,
                "size": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        else:
            raise PatchError(f"{rel}: a special file")
    return out


_DIR_FLAGS = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)


def _open_dir(name: str, dir_fd: int | None, create: bool) -> int:
    try:
        st = os.stat(name, dir_fd=dir_fd, follow_symlinks=False)
    except FileNotFoundError:
        if not create:
            raise PatchError(f"folder {name!r} is missing") from None
        os.mkdir(name, 0o755, dir_fd=dir_fd)
        st = os.stat(name, dir_fd=dir_fd, follow_symlinks=False)
    if not stat.S_ISDIR(st.st_mode):
        raise PatchError(f"{name!r} is not a real folder (a link or a file)")
    return os.open(name, _DIR_FLAGS, dir_fd=dir_fd)


def _case_collision(dir_fd: int, name: str) -> None:
    clash = [n for n in os.listdir(dir_fd) if n.lower() == name.lower() and n != name]
    if clash:
        raise PatchError(f"{name!r} collides by case with {clash}")


def write_tree(root: Path, parsed: list[list[FilePatch]]) -> dict[str, dict[str, Any]]:
    """Applies the planned patches to the tree at ``root`` (a private copy), relative to
    open folders, each result through an exclusive temporary file renamed in its folder.
    Returns, for each touched file, its SHA-256 before (``None`` for a creation) and
    after. Linux only: without ``dir_fd`` support it refuses to write."""
    if os.open not in os.supports_dir_fd or os.stat not in os.supports_dir_fd:
        raise PatchError("this platform cannot write relative to open folders")
    touched: dict[str, dict[str, Any]] = {}
    root_fd = _open_dir(str(root), None, False)
    try:
        for fp in (fp for p in parsed for fp in p):
            parts = fp.path.split("/")
            fds = [root_fd]
            try:
                for part in parts[:-1]:
                    _case_collision(fds[-1], part)
                    fds.append(_open_dir(part, fds[-1], fp.create))
                touched[fp.path] = _write_file(fds[-1], parts[-1], fp)
            finally:
                for fd in fds[1:]:
                    os.close(fd)
        _check_no_temp(root)
    finally:
        os.close(root_fd)
    return touched


def _write_file(dir_fd: int, name: str, fp: FilePatch) -> dict[str, Any]:
    _case_collision(dir_fd, name)
    try:
        st = os.stat(name, dir_fd=dir_fd, follow_symlinks=False)
    except FileNotFoundError:
        st = None
    before = None
    if st is not None:
        if not stat.S_ISREG(st.st_mode):
            raise PatchError(f"{fp.path}: not a regular file")
        if st.st_size > MAX_FILE_BYTES:
            raise PatchError(f"{fp.path}: over {MAX_FILE_BYTES} bytes before the patch")
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=dir_fd)
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                raise PatchError(f"{fp.path}: not a regular file")
            with os.fdopen(os.dup(fd), "rb") as f:
                before = f.read(MAX_FILE_BYTES + 1)
        finally:
            os.close(fd)
        executable = bool(st.st_mode & 0o100)
        if fp.mode is not None and (fp.mode == "100755") != executable:
            raise PatchError(f"{fp.path}: the index mode {fp.mode} is not the file's")
        mode = stat.S_IMODE(st.st_mode)
    else:
        mode = 0o644
    after = apply_text(before, fp)
    temp = f"{TEMP_PREFIX}{hashlib.sha256(fp.path.encode()).hexdigest()[:16]}"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    fd = os.open(temp, flags, 0o600, dir_fd=dir_fd)
    try:
        view = memoryview(after)
        while view:
            view = view[os.write(fd, view) :]
        os.fchmod(fd, mode)
        os.fsync(fd)
    finally:
        os.close(fd)
    try:
        os.rename(temp, name, src_dir_fd=dir_fd, dst_dir_fd=dir_fd)
    except OSError as exc:
        if exc.errno in (errno.EISDIR, errno.ENOTDIR):
            raise PatchError(f"{fp.path}: cannot replace it") from None
        raise
    return {
        "before": None if before is None else hashlib.sha256(before).hexdigest(),
        "after": hashlib.sha256(after).hexdigest(),
    }


def _check_no_temp(root: Path) -> None:
    left = [rel for rel, _ in _walk(root) if PurePosixPath(rel).name.startswith(TEMP_PREFIX)]
    if left:
        raise PatchError(f"temporary files left: {left}")


def expected_difference(
    clone: dict[str, dict[str, Any]],
    patched: dict[str, dict[str, Any]],
    touched: dict[str, dict[str, Any]],
) -> None:
    """The patched manifest differs from the clone's by exactly the touched files (with the
    bytes the patches gave) and the folders their creations needed."""
    for rel in sorted(set(clone) | set(patched)):
        a, b = clone.get(rel), patched.get(rel)
        if rel in touched:
            if b is None or b.get("sha256") != touched[rel]["after"]:
                raise PatchError(f"{rel}: not the bytes the patch gave")
            if a is not None and (a["type"], a.get("mode")) != (b["type"], b.get("mode")):
                raise PatchError(f"{rel}: its type or mode changed")
            continue
        if a == b:
            continue
        needed = any(t.startswith(rel + "/") and touched[t]["before"] is None for t in touched)
        if a is None and b is not None and b["type"] == "dir" and needed:
            continue
        raise PatchError(f"{rel}: differs from the clone and no patch explains it")


def prepare(
    clone: Path,
    dest: Path,
    patches: list[tuple[str, bytes]],
    data_paths: list[str],
    entries: dict[str, tuple[str, str]],
) -> dict[str, Any]:
    """The patched tree: the clone anchored on the commit's tree, copied to ``dest`` (a new
    private folder), every patch planned then written; the record for the dossier."""
    anchor(clone, entries)
    parsed = plan(patches, data_paths) if patches else []  # all checked before any write
    if dest.exists():
        raise PatchError(f"{dest} exists: a preparation starts from the clone")
    shutil.copytree(clone, dest, symlinks=True, ignore=shutil.ignore_patterns(".git"))
    clone_manifest = manifest(clone)
    touched = write_tree(dest, parsed) if parsed else {}
    patched_manifest = manifest(dest)
    expected_difference(clone_manifest, patched_manifest, touched)
    return {
        "patches": [
            {"attachment": name, "sha256": hashlib.sha256(data).hexdigest()}
            for name, data in patches
        ],
        "touched": touched,
        "clone_manifest": clone_manifest,
        "patched_manifest": patched_manifest,
    }


def verify(
    clone: Path,
    scratch: Path,
    patches: list[tuple[str, bytes]],
    data_paths: list[str],
    entries: dict[str, tuple[str, str]],
    record: dict[str, Any],
) -> list[str]:
    """The verification of a dossier's patch record: the patched tree rebuilt from the
    clone at the pinned commit and the patches, with the same refusals and without running
    any code of the paper, into ``scratch`` (a new folder); the patches (order, bytes),
    the touched files and both manifests must be the recorded ones. Returns the problems
    (empty when it holds)."""
    try:
        again = prepare(clone, scratch, patches, data_paths, entries)
    except PatchError as exc:
        return [f"the patched tree cannot be rebuilt: {exc}"]
    problems = []
    for key in ("patches", "touched", "clone_manifest", "patched_manifest"):
        if again[key] != record.get(key):
            problems.append(f"{key} differs from the record")
    return problems
