"""Archive the C3 dossiers (written by ``refute discover`` on the C3 claim) to the Drive as one
zip with a checked SHA-256 manifest (CLAUDE.md, "Operating rules": raw outputs larger than 5 MB
never enter git). Nothing is deleted anywhere.

1. Build a zip (stored, no compression; members in sorted order, a fixed timestamp) of the
   dossier run folder, under ``.cache/v05/archive/``.
2. Write ``MANIFEST.sha256``: the SHA-256 and path of every member, then of the zip itself.
3. Copy the zip, the manifest and this script to ``<drive>/<name>/`` (never over an existing
   folder); copy the manifest, ``summary.json`` and ``summary.md`` (small) to
   ``calibration/v0.5/runs/<name>/``.
4. Check, from the Drive's copies: the zip has the same SHA-256; every member read back has its
   source file's SHA-256; the manifest equals the local one; the sources did not change.

Run from the repository root:
``.venv/Scripts/python.exe calibration/v0.5/archive_dossiers.py <dossier-run-folder> <name>``
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import zipfile
from pathlib import Path

DRIVE = Path("K:/Meu Drive/Pessoal/Projetos/refute/arquivo-v0.5-calibration")
LOCAL = Path(".cache/v05/archive")
OUT = Path("calibration/v0.5/runs")
KEPT = ("summary.json", "summary.md")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def archive(root: Path, source: Path, name: str, drive: Path = DRIVE) -> dict:
    source = root / source
    if source.is_symlink() or not source.is_dir():
        raise ValueError(f"{source} is not a folder")
    target = drive / name
    if target.exists():
        raise ValueError(f"{target} exists; not replaced")
    paths = [p for p in source.rglob("*") if p.is_file()]
    if any(p.is_symlink() for p in paths):
        raise ValueError("a link inside the dossier folder")
    # sorted by the member string (code points), the same order on every system
    members = sorted((p.relative_to(source).as_posix(), p) for p in paths)
    local = root / LOCAL / name
    local.mkdir(parents=True, exist_ok=False)
    zip_path = local / f"{name}.zip"
    digests = {}
    with zipfile.ZipFile(zip_path, "x", compression=zipfile.ZIP_STORED) as zf:
        for member, path in members:
            data = path.read_bytes()
            digests[member] = sha256_bytes(data)
            zf.writestr(zipfile.ZipInfo(member, date_time=(2026, 11, 5, 0, 0, 0)), data)
    zip_sha = sha256(zip_path)
    lines = [f"{digests[m]}  {m}" for m, _ in members] + [f"{zip_sha}  {zip_path.name}"]
    manifest = local / "MANIFEST.sha256"
    with open(manifest, "x", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")
    out = root / OUT / name
    out.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(manifest, out / "drive-manifest.sha256")
    for kept in KEPT:
        if (source / kept).is_file():
            shutil.copyfile(source / kept, out / kept)
    target.mkdir(parents=True)
    for path in (zip_path, manifest, Path(__file__)):
        shutil.copyfile(path, target / path.name)
    problems = []
    if sha256(target / zip_path.name) != zip_sha:
        problems.append("the zip's SHA-256 on the Drive differs")
    if (target / "MANIFEST.sha256").read_bytes() != manifest.read_bytes():
        problems.append("the manifest on the Drive differs")
    with zipfile.ZipFile(target / zip_path.name) as zf:
        if sorted(zf.namelist()) != sorted(digests):
            problems.append("the members on the Drive are not the source files")
        for member in zf.namelist():
            if sha256_bytes(zf.read(member)) != digests.get(member):
                problems.append(f"member differs: {member}")
    for member, path in members:
        if sha256(path) != digests[member]:
            problems.append(f"source changed: {member}")
    return {
        "name": name,
        "members": len(members),
        "bytes": sum(p.stat().st_size for _, p in members),
        "zip_sha256": zip_sha,
        "manifest_sha256": sha256(manifest),
        "problems": problems,
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("source")
    parser.add_argument("name")
    args = parser.parse_args(argv)
    result = archive(Path.cwd(), Path(args.source), args.name)
    print(json.dumps(result, indent=2))
    return 1 if result["problems"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
