"""Archive the complete records of the R_min study to the Drive (CLAUDE.md, "Project folder
hygiene"; the maintainer's decision of 2026-10-19: the complete records on the Drive with a
SHA-256 manifest, the digests in the repository). Nothing is deleted anywhere.

1. Build a zip (stored, no compression; members in sorted order) of the run folder and of the
   study's launch script and logs, under .cache/merge-v021/rmin/archive/.
2. Write MANIFEST.sha256 (sha256 and path of every member, then of the zip itself).
3. Copy the zip, the manifest and this script to the Drive folder.
4. Check: the zip read back from the Drive has the same SHA-256; every member read back from
   the Drive's zip has the SHA-256 of its source file; the Drive's manifest equals the local one.

Usage: <python> archive.py
"""

import hashlib
import shutil
import sys
import zipfile
from pathlib import Path

WT = Path("C:/Projetos/refute/.cache/wt-v021")
RUN = WT / ".cache/v021/rmin-study-run"
EXTRA = [
    WT / ".cache/v021/rmin" / n
    for n in ("launch-study.ps1", "study-run.log", "study-run.err.log", "study-run.pid")
]
LOCAL = Path("C:/Projetos/refute/.cache/merge-v021/rmin/archive")
DRIVE = Path("K:/Meu Drive/Pessoal/Projetos/refute/arquivo-v0.2.1-rmin-study")
ZIP_NAME = "rmin-study-run-2e4ff99.zip"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    if DRIVE.exists():
        raise SystemExit(f"{DRIVE} exists; not replaced")
    LOCAL.mkdir(parents=True, exist_ok=False)
    members = sorted(
        [
            (f"rmin-study-run/{p.relative_to(RUN).as_posix()}", p)
            for p in RUN.rglob("*")
            if p.is_file()
        ]
        + [(f"launch/{p.name}", p) for p in EXTRA]
    )
    source = {}
    zip_path = LOCAL / ZIP_NAME
    with zipfile.ZipFile(zip_path, "x", compression=zipfile.ZIP_STORED) as zf:
        for name, path in members:
            data = path.read_bytes()
            source[name] = hashlib.sha256(data).hexdigest()
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 21, 0, 0, 0))
            zf.writestr(info, data)
    zip_sha = sha(zip_path)
    lines = [f"{source[n]}  {n}" for n, _ in members] + [f"{zip_sha}  {ZIP_NAME}"]
    manifest = LOCAL / "MANIFEST.sha256"
    manifest.write_text(
        "# code: claude/v0-2-1-reopen 2e4ff998ca1596c281abf915222714e1276173f3\n"
        + "\n".join(lines)
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    DRIVE.mkdir(parents=True)
    for p in (zip_path, manifest, Path(__file__)):
        shutil.copyfile(p, DRIVE / p.name)
    # the check, from the Drive's copies
    problems = []
    if sha(DRIVE / ZIP_NAME) != zip_sha:
        problems.append("the zip's SHA-256 on the Drive differs")
    if (DRIVE / "MANIFEST.sha256").read_bytes() != manifest.read_bytes():
        problems.append("the manifest on the Drive differs")
    with zipfile.ZipFile(DRIVE / ZIP_NAME) as zf:
        names = zf.namelist()
        if sorted(names) != sorted(source):
            problems.append("the members on the Drive are not the source files")
        for name in names:
            if hashlib.sha256(zf.read(name)).hexdigest() != source.get(name):
                problems.append(f"member differs: {name}")
    for name, path in members:  # the sources did not change meanwhile
        if sha(path) != source[name]:
            problems.append(f"source changed: {name}")
    print(f"members {len(members)} zip {zip_sha} bytes {zip_path.stat().st_size}")
    print(f"manifest {sha(manifest)}")
    print("problems:", problems or "none")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
