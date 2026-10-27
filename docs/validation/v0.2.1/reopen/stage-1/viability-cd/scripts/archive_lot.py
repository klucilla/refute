"""Archive the C/D viability lot to the Drive (CLAUDE.md: raw outputs larger than 5 MB never enter
git; "Project folder hygiene"). Nothing is deleted here.

``digests <out.json>``: the SHA-256 of every file of the lot folder (.cache/viability-lot), written
once (committed beside the report).

``archive``:
1. Check the lot folder's files against the committed digests (lot-file-digests.json).
2. Build a zip (stored, members in sorted order, a fixed date) under .cache/viability-archive/.
3. Write MANIFEST.sha256 (every member, then the zip).
4. Copy the zip, the manifest and this script to the Drive folder (never replaced).
5. Check from the Drive's copies: the zip's SHA-256, the manifest, every member against its source.

Usage: <python> archive_lot.py digests <out.json> | archive
"""

import hashlib
import json
import shutil
import sys
import zipfile
from pathlib import Path

WT = Path("C:/Projetos/refute/.cache/wt-merge-check")
LOT = WT / ".cache/viability-lot"
DIGESTS = WT / "docs/validation/v0.2.1/reopen/stage-1/viability-cd/lot-file-digests.json"
LOCAL = WT / ".cache/viability-archive"
DRIVE = Path("K:/Meu Drive/Pessoal/Projetos/refute/arquivo-v0.2.1-viability-cd-lot")
ZIP_NAME = "viability-cd-lot-20261027-712a98e.zip"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def files() -> dict[str, Path]:
    return {
        p.relative_to(LOT).as_posix(): p
        for p in sorted(LOT.rglob("*"))
        if p.is_file() and not p.name.startswith(".")
    }


def digests(out: Path) -> int:
    table = {name: sha(p) for name, p in files().items()}
    with open(out, "x", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(table, indent=1, sort_keys=True) + "\n")
    print(f"files {len(table)}")
    return 0


def archive() -> int:
    if DRIVE.exists():
        raise SystemExit(f"{DRIVE} exists; not replaced")
    committed = json.loads(DIGESTS.read_text(encoding="utf-8"))
    present = files()
    if {k: sha(p) for k, p in present.items()} != committed:
        raise SystemExit("the lot folder's files differ from the committed digests")
    LOCAL.mkdir(parents=True, exist_ok=False)
    members = sorted((f"viability-lot/{k}", p) for k, p in present.items())
    source = {}
    zip_path = LOCAL / ZIP_NAME
    with zipfile.ZipFile(zip_path, "x", compression=zipfile.ZIP_STORED) as zf:
        for name, path in members:
            data = path.read_bytes()
            source[name] = hashlib.sha256(data).hexdigest()
            zf.writestr(zipfile.ZipInfo(name, date_time=(2026, 10, 27, 0, 0, 0)), data)
    zip_sha = sha(zip_path)
    lines = [f"{source[n]}  {n}" for n, _ in members] + [f"{zip_sha}  {ZIP_NAME}"]
    manifest = LOCAL / "MANIFEST.sha256"
    manifest.write_text(
        "# code: main 712a98e1f79ba58e1ae9e4027b65c2fd00f1e204 (the lot's code digest unchanged"
        " since 491c955); issue #173\n" + "\n".join(lines) + "\n",
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
    if sys.argv[1] == "digests":
        sys.exit(digests(Path(sys.argv[2])))
    if sys.argv[1] == "archive":
        sys.exit(archive())
    raise SystemExit(f"unknown command {sys.argv[1]!r}")
