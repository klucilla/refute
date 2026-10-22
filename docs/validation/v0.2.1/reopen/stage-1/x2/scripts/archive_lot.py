"""Archive X2's lot records to the Drive (CLAUDE.md, "Project folder hygiene"; the maintainer's
decision after X2, item 6). Nothing is deleted here.

1. Check the run folder's records against the committed digests
   (docs/validation/v0.2.1/reopen/stage-1/x2/lot-record-digests.json).
2. Build a zip (stored, members in sorted order, a fixed date) of the run folder and the run's log,
   under .cache/merge-v021/x2/archive/.
3. Write MANIFEST.sha256 (every member, then the zip).
4. Copy the zip, the manifest and this script to the Drive folder (never replaced).
5. Check from the Drive's copies: the zip's SHA-256, the manifest, every member against its source.

Usage: <python> archive_lot.py
"""

import hashlib
import json
import shutil
import sys
import zipfile
from pathlib import Path

WT = Path("C:/Projetos/refute/.cache/wt-merge-check")
RUN = WT / ".cache/x2-lot/20261022T110605Z"
DIGESTS = WT / "docs/validation/v0.2.1/reopen/stage-1/x2/lot-record-digests.json"
EXTRA = [Path("C:/Projetos/refute/.cache/merge-v021/x2/lot-run.log")]
LOCAL = Path("C:/Projetos/refute/.cache/merge-v021/x2/archive")
DRIVE = Path("K:/Meu Drive/Pessoal/Projetos/refute/arquivo-v0.2.1-x2-lot")
ZIP_NAME = "x2-lot-20261022T110605Z-8b54384.zip"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    if DRIVE.exists():
        raise SystemExit(f"{DRIVE} exists; not replaced")
    committed = json.loads(DIGESTS.read_text(encoding="utf-8"))
    records = {
        p.relative_to(RUN).as_posix(): p
        for p in (RUN / "records").rglob("*.json")
        if not p.name.startswith(".")
    }
    if {k: sha(p) for k, p in records.items()} != committed:
        raise SystemExit("the run folder's records differ from the committed digests")
    LOCAL.mkdir(parents=True, exist_ok=False)
    members = sorted(
        [(f"x2-lot/{p.relative_to(RUN).as_posix()}", p) for p in RUN.rglob("*") if p.is_file()]
        + [(f"launch/{p.name}", p) for p in EXTRA]
    )
    source = {}
    zip_path = LOCAL / ZIP_NAME
    with zipfile.ZipFile(zip_path, "x", compression=zipfile.ZIP_STORED) as zf:
        for name, path in members:
            data = path.read_bytes()
            source[name] = hashlib.sha256(data).hexdigest()
            zf.writestr(zipfile.ZipInfo(name, date_time=(2026, 10, 22, 0, 0, 0)), data)
    zip_sha = sha(zip_path)
    lines = [f"{source[n]}  {n}" for n, _ in members] + [f"{zip_sha}  {ZIP_NAME}"]
    manifest = LOCAL / "MANIFEST.sha256"
    manifest.write_text(
        "# code: main 8b54384d800fc99beb29c3a51e83fa5ba0f95544; results 2593bfa\n"
        + "\n".join(lines)
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    DRIVE.mkdir(parents=True)
    for p in (zip_path, manifest, Path(__file__)):
        shutil.copyfile(p, DRIVE / p.name)
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
    for name, path in members:
        if sha(path) != source[name]:
            problems.append(f"source changed: {name}")
    print(f"members {len(members)} zip {zip_sha} bytes {zip_path.stat().st_size}")
    print(f"manifest {sha(manifest)}")
    print("problems:", problems or "none")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
