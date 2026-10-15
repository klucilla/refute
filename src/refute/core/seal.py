"""Seal of a dossier's experimental core, and annexes (plan section 9.1, items 1-2).

Implements docs/validation/v0.3/wp2-acceptance.md, criteria W2.11 and W2.12.

- **Core:** every file of the dossier except ``SEAL.json`` and the ``annexes/``
  directory: the locked claims, the outputs, the logs, ``verdict.json`` and
  ``MANIFEST.sha256``. ``seal()`` writes ``SEAL.json`` with the SHA-256 of a
  deterministic archive of the core. The core never changes after the seal; a dossier
  is sealed once.
- **Archive (``refute-seal-1``):** a zip with the core files in sorted path order,
  stored without compression (compressed bytes could depend on the zlib version),
  with a fixed timestamp (1980-01-01 00:00:00), mode 0644 and Unix as the creating
  system. File contents are the raw bytes, as in ``MANIFEST.sha256``, so the archive
  does not depend on the platform; the repository's ``.gitattributes`` keeps text
  files LF on every checkout.
- **Set of dossiers:** ``combined_sha256()`` is the SHA-256 of the canonical JSON of
  the sorted ``[name, core sha256]`` pairs, an unambiguous serialization.
- **Annexes:** ``annexes/<name>/`` (a reviewer report, a ``reply`` record, the
  authors' reply), each with its own ``ANNEX.json`` manifest of raw-byte SHA-256 that
  cites the core hash. An annex is added only to a sealed, intact core and is never
  rewritten. Adding an annex never changes the core hash.
- **Paths:** symbolic links and junctions are refused anywhere in a dossier or an
  annex source, and every written path must resolve inside ``annexes/<name>/``.
"""

from __future__ import annotations

import io
import json
import os
import re
import shutil
import zipfile
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from refute.core.canonical import canonical_bytes
from refute.core.hashing import sha256_bytes, sha256_file

SEAL_NAME = "SEAL.json"
ANNEX_DIR = "annexes"
ANNEX_MANIFEST = "ANNEX.json"
SEAL_ALGORITHM = "refute-seal-1"
ANNEX_VERSION = 1
_ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
_ANNEX_NAME = re.compile(r"[a-z0-9][a-z0-9-]{0,62}")
_HEX64 = re.compile(r"[0-9a-f]{64}")
# Names that Windows reserves for devices, with or without an extension.
_RESERVED = {"con", "prn", "aux", "nul"} | {f"{p}{i}" for p in ("com", "lpt") for i in range(1, 10)}


class SealError(Exception):
    """A seal or an annex could not be written."""


def _is_link(path: Path) -> bool:
    return path.is_symlink() or path.is_junction()


def _walk(root: Path, skip_top: str | None = None) -> list[str]:
    """Relative POSIX paths of the regular files under ``root``, sorted. A symbolic
    link or a junction anywhere is an error. ``skip_top`` excludes one top-level entry
    (with its subtree) before anything below it is visited."""
    if _is_link(root):
        raise SealError(f"symbolic links and junctions are not allowed: {root}")
    out = []

    def failed(error: OSError) -> None:  # an unreadable directory is never skipped
        raise SealError(f"cannot list {error.filename}: {error.strerror}")

    for current, dirs, files in os.walk(root, onerror=failed, followlinks=False):
        here = Path(current)
        if here == root and skip_top is not None:
            dirs[:] = [d for d in dirs if d != skip_top]
            files = [f for f in files if f != skip_top]
        for name in dirs:
            if _is_link(here / name):
                raise SealError(f"symbolic links and junctions are not allowed: {here / name}")
        for name in files:
            path = here / name
            if _is_link(path):
                raise SealError(f"symbolic links and junctions are not allowed: {path}")
            if path.is_file():
                out.append(path.relative_to(root).as_posix())
    return sorted(out)


def _check_reserved_spellings(root: Path) -> None:
    """A top-level name that differs from ``annexes`` or ``SEAL.json`` only by case is
    refused: on a case-insensitive file system it is the same entry, so writing an
    annex there would change the core."""
    try:
        names = os.listdir(root)
    except OSError as exc:
        raise SealError(f"cannot list {root}: {exc.strerror}") from exc
    for name in names:
        for reserved in (ANNEX_DIR, SEAL_NAME):
            if name != reserved and name.lower() == reserved.lower():
                raise SealError(f"{name!r} differs from the reserved name {reserved!r} by case")


def core_files(dossier: Path | str) -> list[str]:
    """The paths of the core: everything except ``SEAL.json`` and ``annexes/``. The
    annexes are not visited here; they are checked on their own."""
    root = Path(dossier)
    _check_reserved_spellings(root)
    return [rel for rel in _walk(root, skip_top=ANNEX_DIR) if rel != SEAL_NAME]


def core_archive(dossier: Path | str) -> bytes:
    """The deterministic archive of the core (``refute-seal-1``)."""
    root = Path(dossier)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as archive:
        for rel in core_files(root):
            info = zipfile.ZipInfo(rel, date_time=_ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = 0o644 << 16
            info.create_system = 3
            archive.writestr(info, (root / rel).read_bytes())
    return buffer.getvalue()


def core_sha256(dossier: Path | str) -> str:
    return sha256_bytes(core_archive(dossier))


def _file_list(root: Path, rels: list[str]) -> list[dict[str, str]]:
    return [{"path": rel, "sha256": sha256_file(root / rel)} for rel in rels]


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def seal(dossier: Path | str) -> dict[str, Any]:
    """Seal the core of a dossier: write ``SEAL.json``. Refused when the dossier is
    already sealed, has annexes, or its ``MANIFEST.sha256`` is not intact."""
    from refute.core.dossier import verify_manifest

    root = Path(dossier)
    if not root.is_dir():
        raise SealError(f"not a directory: {root}")
    if (root / SEAL_NAME).exists() or _is_link(root / SEAL_NAME):
        raise SealError(f"{root} is already sealed; the core never changes after the seal")
    if (root / ANNEX_DIR).exists() or _is_link(root / ANNEX_DIR):
        raise SealError(f"{root} has annexes before its seal")
    problems = verify_manifest(root)
    if problems:
        raise SealError("the manifest is not intact: " + "; ".join(problems))
    rels = core_files(root)
    record = {
        "algorithm": SEAL_ALGORITHM,
        "core_sha256": core_sha256(root),
        "files": _file_list(root, rels),
    }
    _write_json(root / SEAL_NAME, record)
    return record


def read_seal(dossier: Path | str) -> dict[str, Any]:
    path = Path(dossier) / SEAL_NAME
    if _is_link(path):
        raise SealError(f"{SEAL_NAME} is a link")
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SealError(f"{SEAL_NAME} unreadable: {exc}") from exc
    if not isinstance(record, dict) or not _is_hex64(record.get("core_sha256")):
        raise SealError(f"{SEAL_NAME} has no valid core_sha256")
    return record


def _is_hex64(value: Any) -> bool:
    return isinstance(value, str) and _HEX64.fullmatch(value) is not None


def _listed(record: Any) -> dict[str, str] | None:
    """``files`` of a seal or annex record as {path: sha256}, or None if malformed."""
    files = record.get("files") if isinstance(record, dict) else None
    if not isinstance(files, list):
        return None
    out = {}
    for item in files:
        if (
            not (
                isinstance(item, dict)
                and isinstance(item.get("path"), str)
                and _is_hex64(item.get("sha256"))
            )
            or item["path"] in out
        ):
            return None
        out[item["path"]] = item["sha256"]
    return out


def verify_seal(dossier: Path | str) -> list[str]:
    """Problems of the core against its seal (empty list = intact)."""
    root = Path(dossier)
    try:
        record = read_seal(root)
    except SealError as exc:
        return [str(exc)]
    if record.get("algorithm") != SEAL_ALGORITHM:
        return [f"unknown seal algorithm: {record.get('algorithm')!r}"]
    try:
        current = core_sha256(root)
        files = {f["path"]: f["sha256"] for f in _file_list(root, core_files(root))}
    except (SealError, OSError) as exc:
        return [str(exc)]
    if current == record["core_sha256"]:
        return []
    problems = [f"core archive {current} differs from the seal {record['core_sha256']}"]
    sealed = _listed(record) or {}
    for rel in sorted(set(sealed) | set(files)):
        if rel not in files:
            problems.append(f"core file missing: {rel}")
        elif rel not in sealed:
            problems.append(f"core file added: {rel}")
        elif files[rel] != sealed[rel]:
            problems.append(f"core file modified: {rel}")
    return problems


def _check_dossier_name(name: str) -> None:
    if not name or any(ch in name for ch in "/\\") or any(ord(ch) < 32 for ch in name):
        raise ValueError(f"invalid dossier name {name!r}")


def combined_sha256(cores: Mapping[str, str]) -> str:
    """One hash for a set of sealed dossiers, ``{dossier name: core sha256}``: the
    SHA-256 of the canonical JSON of the sorted ``[name, sha256]`` pairs."""
    pairs = []
    for name in sorted(cores):
        _check_dossier_name(name)
        if not _is_hex64(cores[name]):
            raise ValueError(f"invalid core hash for {name!r}")
        pairs.append([name, cores[name]])
    return sha256_bytes(canonical_bytes(pairs))


def _check_annex_name(name: str) -> None:
    if _ANNEX_NAME.fullmatch(name) is None or name in _RESERVED:
        raise SealError(
            f"invalid annex name {name!r} (lowercase letters, digits and '-', not a "
            "reserved device name)"
        )


_NOT_PORTABLE = set('<>:"\\|?*')


def _check_annex_files(rels: list[str]) -> None:
    """Every component of every path (directories too) must be portable: no Windows
    device name, no character Windows forbids or control character, no trailing dot
    or space, and no two components that differ only by case at the same place."""
    seen: dict[str, str] = {}
    for rel in rels:
        if rel.lower() == ANNEX_MANIFEST.lower():
            raise SealError(f"the annex source must not contain {ANNEX_MANIFEST}")
        parts = rel.split("/")
        for i, part in enumerate(parts):
            stem = part.split(".")[0].lower()
            if (
                stem in _RESERVED
                or part.endswith((".", " "))
                or any(ch in _NOT_PORTABLE or ord(ch) < 32 for ch in part)
            ):
                raise SealError(f"file name not portable across platforms: {rel}")
            prefix = "/".join(parts[: i + 1])
            if seen.setdefault(prefix.lower(), prefix) != prefix:
                raise SealError(f"names differ only by case: {seen[prefix.lower()]} and {prefix}")


def add_annex(dossier: Path | str, name: str, source: Path | str) -> dict[str, Any]:
    """Copy the files of ``source`` into ``annexes/<name>/`` with an ``ANNEX.json`` that
    cites the core hash. Refused unless the core is sealed and intact."""
    root = Path(dossier)
    _check_annex_name(name)
    problems = verify_seal(root)
    if problems:
        raise SealError("an annex needs a sealed, intact core: " + "; ".join(problems))
    source = Path(source)
    if not source.is_dir() or _is_link(source):
        raise SealError(f"annex source is not a plain directory: {source}")
    rels = _walk(source)
    if not rels:
        raise SealError(f"annex source is empty: {source}")
    _check_annex_files(rels)
    annex_root = root / ANNEX_DIR
    if _is_link(annex_root):
        raise SealError(f"{ANNEX_DIR}/ is a link")
    target = annex_root / name
    if target.exists() or _is_link(target):
        raise SealError(f"annex {name} already exists; an annex is never rewritten")
    target.mkdir(parents=True)
    allowed = target.resolve()
    for rel in rels:
        destination = target / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.parent.resolve().is_relative_to(allowed):
            raise SealError(f"annex path resolves outside the annex: {rel}")
        shutil.copyfile(source / rel, destination)
    record = {
        "annex_version": ANNEX_VERSION,
        "name": name,
        "core_sha256": read_seal(root)["core_sha256"],
        "files": _file_list(target, rels),
    }
    _write_json(target / ANNEX_MANIFEST, record)
    if verify_seal(root):  # the core must still be exactly the sealed one
        raise SealError("the core changed while the annex was written")
    return record


def verify_annex(dossier: Path | str, name: str) -> list[str]:
    """Problems of one annex against its own manifest and the seal (empty = intact)."""
    root = Path(dossier)
    target = root / ANNEX_DIR / name
    try:
        present = [rel for rel in _walk(target) if rel != ANNEX_MANIFEST]
        record = json.loads((target / ANNEX_MANIFEST).read_text(encoding="utf-8"))
    except SealError as exc:
        return [str(exc)]
    except (OSError, ValueError) as exc:
        return [f"{ANNEX_MANIFEST} unreadable: {exc}"]
    listed = _listed(record)
    if listed is None:
        return [f"{ANNEX_MANIFEST} is malformed"]
    problems = []
    if record.get("annex_version") != ANNEX_VERSION or record.get("name") != name:
        problems.append(f"{ANNEX_MANIFEST} does not describe annex {name}")
    try:
        sealed = read_seal(root)["core_sha256"]
    except SealError as exc:
        problems.append(str(exc))
    else:
        if record.get("core_sha256") != sealed:
            problems.append("the annex cites another core hash than the seal")
    try:
        current = {f["path"]: f["sha256"] for f in _file_list(target, present)}
    except OSError as exc:
        return [*problems, f"cannot read an annex file: {exc}"]
    for rel in sorted(set(listed) | set(current)):
        if rel not in current:
            problems.append(f"annex file missing: {rel}")
        elif rel not in listed:
            problems.append(f"annex file not in its manifest: {rel}")
        elif current[rel] != listed[rel]:
            problems.append(f"annex file modified: {rel}")
    return problems


@dataclass
class SealCheck:
    core_problems: list[str] = field(default_factory=list)
    annexes: dict[str, list[str]] = field(default_factory=dict)
    annex_problems: list[str] = field(default_factory=list)  # about annexes/ itself

    @property
    def ok(self) -> bool:
        return not self.core_problems and not self.annex_problems and not any(self.annexes.values())


def check_sealed(dossier: Path | str) -> SealCheck:
    """The core against its seal and each annex against its manifest, separately."""
    root = Path(dossier)
    result = SealCheck(core_problems=verify_seal(root))
    annex_root = root / ANNEX_DIR
    if _is_link(annex_root):
        result.annex_problems.append(f"{ANNEX_DIR}/ is a link")
    elif annex_root.is_dir():
        try:
            entries = sorted(annex_root.iterdir())
        except OSError as exc:
            result.annex_problems.append(f"cannot list {ANNEX_DIR}/: {exc.strerror}")
            return result
        for entry in entries:
            if entry.is_dir() and not _is_link(entry):
                result.annexes[entry.name] = verify_annex(root, entry.name)
            else:
                result.annexes[entry.name] = [f"not an annex directory: {entry.name}"]
    elif annex_root.exists():
        result.annex_problems.append(f"{ANNEX_DIR} is not a directory")
    return result
