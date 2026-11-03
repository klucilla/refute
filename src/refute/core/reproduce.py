"""The inputs a clone lacks, declared by a claim and checked before a run (v0.5 WP8; issues #189
and #195; docs/plans/v0.5-acceptance.md, cases 8.1 and 8.2).

A claim may declare inputs that are not in the repository (a frozen catalog edition, a
published archive of earlier results), each with its SHA-256, the URL it is fetched from and
its destination inside the checkout. ``check`` refuses a run when a declared input is missing
or has other bytes, so a reproduction can never skip one silently; ``prepare`` fetches and
verifies them (``refute prepare-inputs``), and the dossier's ``REPRODUCE.md`` lists them.

Safety (Codex's design review of 2026-11-03):
- a destination is a relative path inside ``.cache/frozen/`` (a dedicated input area that the
  hygiene rule never deletes), with plain components only: no traversal, no drive, no UNC path,
  no backslash, no ``:`` (alternate data streams), no Windows device name, no component ending
  in a dot (Windows drops it, so ``name.`` would alias ``name``), no duplicate under
  case-insensitive comparison; no link or junction may lie on the way;
- ``install`` validates the destination itself, then checks each existing ancestor and creates
  the missing ones one level at a time, refusing a link or a junction at each level, before
  anything is written (Codex's end-of-round review of round 3);
- a file is installed without clobbering: written to an exclusive temporary file, verified,
  then hard-linked to the destination (which fails if the destination appeared meanwhile);
- the checks are made before the writes; a hostile process that replaces an ancestor with a
  junction between the check and the write is outside this guarantee (no anchored directory
  handles are used);
- fetching uses https only, with a timeout, a size bound, and redirects that must stay https;
  ``file:`` URLs are accepted only under an explicit fixture root (the offline tests).
"""

from __future__ import annotations

import hashlib
import os
import urllib.parse
import urllib.request
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath

AREA = (".cache", "frozen")
MAX_BYTES = 2_000_000_000
TIMEOUT_SECONDS = 120
_DEVICES = {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10))}
_DEVICES |= {f"lpt{i}" for i in range(1, 10)}


class InputError(Exception):
    """A declared input cannot be checked, fetched or installed."""


@dataclass(frozen=True)
class InputSpec:
    name: str
    sha256: str
    url: str
    dest: str  # relative POSIX path inside the checkout, under .cache/frozen/

    def to_dict(self) -> dict[str, str]:
        return {"name": self.name, "sha256": self.sha256, "url": self.url, "dest": self.dest}


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def dest_problem(dest: str) -> str | None:
    """Why ``dest`` is not an acceptable destination (None when it is)."""
    if not isinstance(dest, str) or not dest:
        return "empty destination"
    if "\\" in dest or ":" in dest or dest.startswith("/"):
        return "not a relative POSIX path"
    if PureWindowsPath(dest).drive or dest.startswith("//"):
        return "a drive or UNC path"
    parts = dest.split("/")
    if tuple(parts[: len(AREA)]) != AREA or len(parts) <= len(AREA):
        return "not inside .cache/frozen/"
    for part in parts:
        if part in ("", ".", ".."):
            return "an empty, '.' or '..' component"
        if not all(c.isalnum() or c in "-_." for c in part):
            return f"a component with other characters: {part!r}"
        if part.endswith("."):
            return f"a component ending in a dot (a Windows alias): {part!r}"
        if part.split(".")[0].lower() in _DEVICES:
            return f"a Windows device name: {part!r}"
    return None


def specs_problems(specs: Sequence[InputSpec]) -> list[str]:
    """Problems of a declaration (refused before anything is read or fetched)."""
    problems = []
    seen: set[str] = set()
    for spec in specs:
        if len(spec.sha256) != 64 or any(c not in "0123456789abcdef" for c in spec.sha256):
            problems.append(f"{spec.name}: not a lowercase SHA-256")
        why = dest_problem(spec.dest)
        if why:
            problems.append(f"{spec.name}: {why}")
        folded = spec.dest.casefold()
        if folded in seen:
            problems.append(f"{spec.name}: duplicate destination")
        seen.add(folded)
    return problems


def _path(root: Path, spec: InputSpec) -> Path:
    return Path(root).joinpath(*spec.dest.split("/"))


def _no_link(path: Path, root: Path) -> None:
    for part in [path, *path.parents]:
        if part.is_symlink() or (part.exists() and part.is_junction()):
            raise InputError(f"{part} is a link or a junction")
        if part == root:
            return
    raise InputError(f"{path} is not inside {root}")


def make_parents(directory: Path, root: Path) -> None:
    """Create ``directory`` under ``root`` one level at a time, refusing a link or a junction at
    every level (existing or just created) and a ``directory`` outside ``root``; nothing is
    created above a refused level."""
    root, directory = Path(root), Path(directory)
    if root.is_symlink() or (root.exists() and root.is_junction()):
        raise InputError(f"{root} is a link or a junction")
    root.mkdir(parents=True, exist_ok=True)  # the checkout itself, named by the caller
    try:
        parts = directory.relative_to(root).parts
    except ValueError as error:
        raise InputError(f"{directory} is not inside {root}") from error
    current = root
    for part in parts:
        current = current / part
        if current.is_symlink() or (current.exists() and current.is_junction()):
            raise InputError(f"{current} is a link or a junction")
        if not current.exists():
            current.mkdir()
        if current.is_symlink() or current.is_junction() or not current.is_dir():
            raise InputError(f"{current} is not a plain directory")


def check(specs: Sequence[InputSpec], root: Path) -> list[str]:
    """The declared inputs that are missing or wrong under ``root`` (empty when all are
    present, regular files, reached without a link, with their SHA-256)."""
    problems = specs_problems(specs)
    if problems:
        return problems
    root = Path(root)
    for spec in specs:
        path = _path(root, spec)
        try:
            _no_link(path, root)
        except InputError as error:
            problems.append(f"{spec.name}: {error}")
            continue
        if not path.exists():
            problems.append(f"{spec.name}: missing ({spec.dest}); run `refute prepare-inputs`")
        elif not path.is_file():
            problems.append(f"{spec.name}: {spec.dest} is not a regular file")
        elif _sha256_file(path) != spec.sha256:
            problems.append(f"{spec.name}: {spec.dest} has other bytes than the declared SHA-256")
    return problems


class _HttpsOnly(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        if urllib.parse.urlparse(newurl).scheme != "https":
            raise InputError(f"a redirect left https: {newurl}")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_bytes(url: str, file_root: Path | None = None) -> bytes:
    """The bytes of ``url``: https (redirects must stay https), or a ``file:`` URL inside
    ``file_root`` when one is given (offline fixtures); bounded in size and time."""
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme == "file":
        if file_root is None:
            raise InputError("file: URLs are accepted only under a fixture root")
        if parsed.netloc not in ("", "localhost"):
            raise InputError("a file: URL with a remote authority")
        path = Path(urllib.request.url2pathname(parsed.path)).resolve()
        base = Path(file_root).resolve()
        if not path.is_relative_to(base) or not path.is_file():
            raise InputError(f"{url} is not a file inside the fixture root")
        if path.stat().st_size > MAX_BYTES:
            raise InputError(f"{url} is larger than {MAX_BYTES} bytes")
        return path.read_bytes()
    if parsed.scheme != "https":
        raise InputError(f"only https URLs are fetched: {url}")
    opener = urllib.request.build_opener(_HttpsOnly())
    with opener.open(url, timeout=TIMEOUT_SECONDS) as response:  # noqa: S310 - https only
        data = response.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise InputError(f"{url} is larger than {MAX_BYTES} bytes")
    return data


def install(data: bytes, spec: InputSpec, root: Path) -> Path:
    """Install verified bytes at the destination without clobbering anything. The destination is
    validated here too (a direct caller may skip ``prepare``), before any directory is made."""
    problems = specs_problems([spec])
    if problems:
        raise InputError("; ".join(problems))
    if hashlib.sha256(data).hexdigest() != spec.sha256:
        raise InputError(f"{spec.name}: the fetched bytes do not have the declared SHA-256")
    path = _path(root, spec)
    make_parents(path.parent, Path(root))
    _no_link(path.parent, Path(root))
    temporary = path.with_name(path.name + f".{os.getpid()}.part")
    with open(temporary, "xb") as fh:
        fh.write(data)
    try:
        if _sha256_file(temporary) != spec.sha256:
            raise InputError(f"{spec.name}: the written bytes differ")
        os.link(temporary, path)  # fails when the destination exists: no clobbering
    finally:
        os.remove(temporary)
    return path


def prepare(
    specs: Sequence[InputSpec],
    root: Path,
    fetch: Callable[[str], bytes] = fetch_bytes,
) -> list[dict[str, str]]:
    """Fetch, verify and install every declared input that is not already present with its
    SHA-256; return one line per input (``present`` or ``installed``). A destination with other
    bytes is refused, never replaced."""
    problems = specs_problems(specs)
    if problems:
        raise InputError("; ".join(problems))
    report = []
    for spec in specs:
        path = _path(Path(root), spec)
        _no_link(path, Path(root))
        if path.exists():
            if not path.is_file() or _sha256_file(path) != spec.sha256:
                raise InputError(f"{spec.name}: {spec.dest} exists with other bytes")
            report.append({"name": spec.name, "state": "present"})
            continue
        install(fetch(spec.url), spec, Path(root))
        report.append({"name": spec.name, "state": "installed"})
    return report


def specs_from(declared: Sequence[dict]) -> list[InputSpec]:
    """InputSpecs from a claim's declaration (a list of mappings)."""
    out = []
    for item in declared:
        try:
            out.append(
                InputSpec(
                    str(item["name"]), str(item["sha256"]), str(item["url"]), str(item["dest"])
                )
            )
        except (KeyError, TypeError) as error:
            raise InputError(f"a declared input lacks {error}") from error
    return out
