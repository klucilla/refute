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
  system. A text file (valid UTF-8 without NUL) has CRLF normalized to LF, as for the
  lock attachments, so a Windows and a Linux checkout give the same archive; binary
  content is stored as it is.
- **Set of dossiers:** ``combined_sha256()`` hashes the lines
  ``<core sha256>  <dossier name>`` sorted by name.
- **Annexes:** ``annexes/<name>/`` (a reviewer report, a ``reply`` record, the
  authors' reply), each with its own ``ANNEX.json`` manifest that cites the core hash.
  An annex is added only to a sealed, intact core. Adding an annex never changes the
  core hash.
"""

from __future__ import annotations

import io
import json
import re
import shutil
import zipfile
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from refute.core.hashing import is_text, normalize_newlines, sha256_bytes

SEAL_NAME = "SEAL.json"
ANNEX_DIR = "annexes"
ANNEX_MANIFEST = "ANNEX.json"
SEAL_ALGORITHM = "refute-seal-1"
ANNEX_VERSION = 1
_ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
_ANNEX_NAME = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")


class SealError(Exception):
    """A seal or an annex could not be written."""


def _relative_files(root: Path) -> list[str]:
    out = []
    for path in root.rglob("*"):
        if path.is_symlink():
            raise SealError(f"symbolic links are not allowed in a dossier: {path}")
        if path.is_file():
            out.append(path.relative_to(root).as_posix())
    return sorted(out)


def core_files(dossier: Path | str) -> list[str]:
    """The paths of the core: everything except ``SEAL.json`` and ``annexes/``."""
    root = Path(dossier)
    return [
        rel
        for rel in _relative_files(root)
        if rel != SEAL_NAME and rel != ANNEX_DIR and not rel.startswith(f"{ANNEX_DIR}/")
    ]


def _content(path: Path) -> bytes:
    data = path.read_bytes()
    return normalize_newlines(data) if is_text(data) else data


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
            archive.writestr(info, _content(root / rel))
    return buffer.getvalue()


def core_sha256(dossier: Path | str) -> str:
    return sha256_bytes(core_archive(dossier))


def _file_list(root: Path, rels: list[str]) -> list[dict[str, str]]:
    return [{"path": rel, "sha256": sha256_bytes(_content(root / rel))} for rel in rels]


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
    if (root / SEAL_NAME).exists():
        raise SealError(f"{root} is already sealed; the core never changes after the seal")
    if (root / ANNEX_DIR).exists():
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
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SealError(f"{SEAL_NAME} unreadable: {exc}") from exc
    if not isinstance(record, dict) or not isinstance(record.get("core_sha256"), str):
        raise SealError(f"{SEAL_NAME} has no core_sha256")
    return record


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
    except SealError as exc:
        return [str(exc)]
    if current == record["core_sha256"]:
        return []
    problems = [f"core archive {current} differs from the seal {record['core_sha256']}"]
    sealed = {f.get("path"): f.get("sha256") for f in record.get("files", [])}
    for rel in sorted(set(sealed) | set(files)):
        if rel not in files:
            problems.append(f"core file missing: {rel}")
        elif rel not in sealed:
            problems.append(f"core file added: {rel}")
        elif files[rel] != sealed[rel]:
            problems.append(f"core file modified: {rel}")
    return problems


def combined_sha256(cores: Mapping[str, str]) -> str:
    """One hash for a set of sealed dossiers: ``{dossier name: core sha256}``."""
    lines = "".join(f"{cores[name]}  {name}\n" for name in sorted(cores))
    return sha256_bytes(lines.encode("utf-8"))


def add_annex(dossier: Path | str, name: str, source: Path | str) -> dict[str, Any]:
    """Copy the files of ``source`` into ``annexes/<name>/`` with an ``ANNEX.json`` that
    cites the core hash. Refused unless the core is sealed and intact."""
    root = Path(dossier)
    if not _ANNEX_NAME.match(name):
        raise SealError(f"invalid annex name {name!r} (lowercase letters, digits, '-')")
    problems = verify_seal(root)
    if problems:
        raise SealError("an annex needs a sealed, intact core: " + "; ".join(problems))
    source = Path(source)
    if not source.is_dir():
        raise SealError(f"annex source is not a directory: {source}")
    rels = _relative_files(source)
    if not rels:
        raise SealError(f"annex source is empty: {source}")
    if ANNEX_MANIFEST in rels:
        raise SealError(f"the annex source must not contain {ANNEX_MANIFEST}")
    target = root / ANNEX_DIR / name
    if target.exists():
        raise SealError(f"annex {name} already exists; an annex is never rewritten")
    target.mkdir(parents=True)
    for rel in rels:
        (target / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / rel, target / rel)
    record = {
        "annex_version": ANNEX_VERSION,
        "name": name,
        "core_sha256": read_seal(root)["core_sha256"],
        "files": _file_list(target, rels),
    }
    _write_json(target / ANNEX_MANIFEST, record)
    return record


def verify_annex(dossier: Path | str, name: str) -> list[str]:
    """Problems of one annex against its own manifest and the seal (empty = intact)."""
    root = Path(dossier)
    target = root / ANNEX_DIR / name
    try:
        record = json.loads((target / ANNEX_MANIFEST).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"{ANNEX_MANIFEST} unreadable: {exc}"]
    problems = []
    if record.get("annex_version") != ANNEX_VERSION or record.get("name") != name:
        problems.append(f"{ANNEX_MANIFEST} does not describe annex {name}")
    try:
        sealed = read_seal(root)["core_sha256"]
    except SealError as exc:
        sealed = None
        problems.append(str(exc))
    if sealed is not None and record.get("core_sha256") != sealed:
        problems.append("the annex cites another core hash than the seal")
    try:
        present = [rel for rel in _relative_files(target) if rel != ANNEX_MANIFEST]
    except SealError as exc:
        return [*problems, str(exc)]
    listed = {f.get("path"): f.get("sha256") for f in record.get("files", [])}
    current = {f["path"]: f["sha256"] for f in _file_list(target, present)}
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

    @property
    def ok(self) -> bool:
        return not self.core_problems and not any(self.annexes.values())


def check_sealed(dossier: Path | str) -> SealCheck:
    """The core against its seal and each annex against its manifest, separately."""
    root = Path(dossier)
    result = SealCheck(core_problems=verify_seal(root))
    annex_root = root / ANNEX_DIR
    if annex_root.is_dir():
        for entry in sorted(annex_root.iterdir()):
            if entry.is_dir() and not entry.is_symlink():
                result.annexes[entry.name] = verify_annex(root, entry.name)
            else:
                result.annexes[entry.name] = [f"not an annex directory: {entry.name}"]
    return result
