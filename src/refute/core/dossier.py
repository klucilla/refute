"""Evidence dossiers: writing, manifest, integrity checks, comparison and archives.

A dossier is a directory. ``MANIFEST.sha256`` lists the SHA-256 of every other
file in it (``<sha256>  <relative path>``, sorted by path). See ``docs/dossier.md``.

Pack-agnostic conventions used for reproduction checks:

- ``verdict.json`` has top-level ``verdict``, ``status``, ``tests`` (list of
  ``{name, status}``) and ``key_values`` (numbers compared with a relative
  tolerance);
- ``data/manifest.json`` has ``files``: a list of ``{name, sha256}``.
"""

from __future__ import annotations

import math
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from refute.core.hashing import sha256_bytes, sha256_file
from refute.core.io import read_json, write_json, write_text

REVIEW_DIR = "review"

MANIFEST_NAME = "MANIFEST.sha256"
DEFAULT_RELATIVE_TOLERANCE = 1e-6
_ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


class DossierWriter:
    """Writes files into one dossier directory."""

    def __init__(self, root: Path | str):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def path(self, relative: str) -> Path:
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        return target

    def write_text(self, relative: str, text: str) -> Path:
        return write_text(self.path(relative), text)

    def write_json(self, relative: str, value: Any) -> Path:
        return write_json(self.path(relative), value)

    def write_bytes(self, relative: str, data: bytes) -> Path:
        target = self.path(relative)
        target.write_bytes(data)
        return target

    def finalize(self) -> Path:
        return write_manifest(self.root)


def _dossier_files(root: Path, recorded: set[str] | None = None) -> list[str]:
    """Files covered by ``MANIFEST.sha256``: every file except the manifest itself and,
    from v0.3, the seal record and the annexes (``refute.core.seal``), which are added
    after the core is sealed and have their own manifests. A path of those two kinds
    that an existing manifest already lists (``recorded``) stays covered, so an older
    manifest keeps its meaning."""
    from refute.core.seal import ANNEX_DIR, SEAL_NAME

    recorded = recorded or set()
    out = []
    for p in root.rglob("*"):
        rel = p.relative_to(root).as_posix()
        if not p.is_file() or rel == MANIFEST_NAME:
            continue
        sealed_layout = rel == SEAL_NAME or rel.startswith(f"{ANNEX_DIR}/")
        if sealed_layout and rel not in recorded:
            continue
        out.append(rel)
    return sorted(out)


def write_manifest(root: Path | str) -> Path:
    root = Path(root)
    lines = [f"{sha256_file(root / rel)}  {rel}\n" for rel in _dossier_files(root)]
    return write_text(root / MANIFEST_NAME, "".join(lines))


def read_manifest(root: Path | str) -> dict[str, str]:
    manifest = Path(root) / MANIFEST_NAME
    entries: dict[str, str] = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, _, rel = line.partition("  ")
        entries[rel] = digest
    return entries


def verify_manifest(root: Path | str) -> list[str]:
    """Problems found when recomputing the manifest (empty list = intact)."""
    root = Path(root)
    if not (root / MANIFEST_NAME).is_file():
        return [f"{MANIFEST_NAME} is missing"]
    recorded = read_manifest(root)
    present = set(_dossier_files(root, set(recorded)))
    problems = []
    for rel, digest in sorted(recorded.items()):
        if rel not in present:
            problems.append(f"missing file: {rel}")
        elif sha256_file(root / rel) != digest:
            problems.append(f"modified file: {rel}")
    for rel in sorted(present - set(recorded)):
        problems.append(f"file not in manifest: {rel}")
    return problems


def _close(a: Any, b: Any, rel_tol: float) -> bool:
    if a is None or b is None:
        return a is b
    if isinstance(a, bool) or isinstance(b, bool):
        return a == b
    if isinstance(a, int | float) and isinstance(b, int | float):
        return math.isclose(float(a), float(b), rel_tol=rel_tol, abs_tol=1e-12)
    return a == b


def compare_dossiers(
    new: Path | str, original: Path | str, rel_tol: float = DEFAULT_RELATIVE_TOLERANCE
) -> list[str]:
    """Differences between the key results of two dossiers (empty list = reproduced)."""
    new, original = Path(new), Path(original)
    differences = []
    try:
        a = read_json(new / "verdict.json")
        b = read_json(original / "verdict.json")
    except (OSError, ValueError) as exc:
        return [f"cannot read verdict.json: {exc}"]
    for key in ("verdict", "status"):
        if a.get(key) != b.get(key):
            differences.append(f"{key}: {a.get(key)} != original {b.get(key)}")
    tests_a = {t["name"]: t["status"] for t in a.get("tests", [])}
    tests_b = {t["name"]: t["status"] for t in b.get("tests", [])}
    if tests_a != tests_b:
        differences.append(f"test statuses differ: {tests_a} != original {tests_b}")
    values_a, values_b = a.get("key_values", {}), b.get("key_values", {})
    for key in sorted(set(values_a) | set(values_b)):
        if not _close(values_a.get(key), values_b.get(key), rel_tol):
            differences.append(f"{key}: {values_a.get(key)} != original {values_b.get(key)}")
    try:
        files_a = {f["name"]: f["sha256"] for f in read_json(new / "data/manifest.json")["files"]}
        files_b = {
            f["name"]: f["sha256"] for f in read_json(original / "data/manifest.json")["files"]
        }
    except (OSError, ValueError, KeyError) as exc:
        differences.append(f"cannot compare data manifests: {exc}")
    else:
        if files_a != files_b:
            differences.append("input data hashes differ from the original dossier")
    return differences


@dataclass
class CheckResult:
    path: str
    integrity_problems: list[str] = field(default_factory=list)
    differences: list[str] = field(default_factory=list)
    compared_with: str | None = None
    seal: Any = None  # refute.core.seal.SealCheck when the dossier is sealed

    @property
    def ok(self) -> bool:
        sealed_ok = self.seal is None or self.seal.ok
        return not self.integrity_problems and not self.differences and sealed_ok


def _sealed_layout(root: Path) -> bool:
    """True for a dossier with the v0.3 seal layout: ``SEAL.json`` or ``annexes/``
    present and not covered by its ``MANIFEST.sha256``. An older manifest that lists
    such paths marks a legacy dossier, checked by its manifest only."""
    import json

    from refute.core.seal import ANNEX_DIR, SEAL_ALGORITHM, SEAL_NAME

    def there(path: Path) -> bool:  # a broken link counts as present
        return path.exists() or path.is_symlink() or path.is_junction()

    seal_path = root / SEAL_NAME
    if not there(seal_path) and not there(root / ANNEX_DIR):
        return False
    if seal_path.is_symlink() or seal_path.is_junction():
        return True  # refused by the seal check
    try:
        if json.loads(seal_path.read_text(encoding="utf-8")).get("algorithm") == SEAL_ALGORITHM:
            return True  # a v0.3 seal is always checked, even if a manifest lists it
    except (OSError, ValueError, AttributeError):
        pass
    try:
        recorded = read_manifest(root)
    except OSError:
        return True
    legacy = SEAL_NAME in recorded or any(r.startswith(f"{ANNEX_DIR}/") for r in recorded)
    return not legacy


def check_dossier(path: Path | str, against: Path | str | None = None) -> CheckResult:
    root = Path(path)
    result = CheckResult(path=root.as_posix())
    if not root.is_dir():
        result.integrity_problems.append(f"not a directory: {root}")
        return result
    result.integrity_problems = verify_manifest(root)
    from refute.core.seal import check_sealed

    if _sealed_layout(root):
        result.seal = check_sealed(root)
    if (root / REVIEW_DIR / "index.json").is_file():
        from refute.core.review import verify_reviews

        result.integrity_problems.extend(verify_reviews(root))
    if against is not None:
        original = Path(against)
        result.compared_with = original.as_posix()
        problems = verify_manifest(original)
        if _sealed_layout(original):
            sealed = check_sealed(original)
            problems += [f"core: {p}" for p in sealed.core_problems]
            problems += sealed.annex_problems
            for name, annex_problems in sealed.annexes.items():
                problems += [f"annex {name}: {p}" for p in annex_problems]
        result.integrity_problems.extend(f"original: {p}" for p in problems)
        result.differences = compare_dossiers(root, original)
    return result


def write_archive(run_dir: Path | str, out_zip: Path | str) -> tuple[Path, str]:
    """Deterministic zip of a run directory: sorted entries, fixed timestamps and modes.

    Returns the zip path and its SHA-256, which is also written next to it as
    ``<zip>.sha256``.
    """
    run_dir = Path(run_dir)
    out_zip = Path(out_zip)
    if not run_dir.is_dir():
        raise FileNotFoundError(f"run directory not found: {run_dir}")
    out_zip.parent.mkdir(parents=True, exist_ok=True)
    files = sorted(
        (p for p in run_dir.rglob("*") if p.is_file()),
        key=lambda p: p.relative_to(run_dir).as_posix(),
    )
    prefix = run_dir.name
    with zipfile.ZipFile(out_zip, "w") as archive:
        for path in files:
            info = zipfile.ZipInfo(f"{prefix}/{path.relative_to(run_dir).as_posix()}")
            info.date_time = _ZIP_TIMESTAMP
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            info.create_system = 3
            archive.writestr(info, path.read_bytes(), compresslevel=9)
    digest = sha256_bytes(out_zip.read_bytes())
    write_text(out_zip.with_name(out_zip.name + ".sha256"), f"{digest}  {out_zip.name}\n")
    return out_zip, digest
