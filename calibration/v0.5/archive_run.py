"""Archive the files of one collected calibration run that stay out of git (above 5 MB) to the
Drive, with a checked SHA-256 manifest (CLAUDE.md, "Operating rules": raw outputs larger than
5 MB never enter git; they are archived to the Drive with a SHA-256 manifest of source and
destination, checked; the repository keeps the script, a summary and that manifest).

Input: ``calibration/v0.5/runs/<step>/files.json`` (written by ``collect_run.py``). For every
file listed there with ``"in_git": false``, this script:

1. checks that the run folder's file still has the SHA-256 that ``files.json`` records;
2. copies it to ``<drive>/<step>/<path>`` (never over an existing file);
3. writes ``MANIFEST.sha256`` (one line per file: SHA-256, two spaces, path) to the Drive folder
   and, byte for byte, to ``calibration/v0.5/runs/<step>/drive-manifest.sha256``;
4. copies this script to the Drive folder;
5. checks, from the Drive's copies: each file's SHA-256 equals its source's, and the Drive's
   manifest equals the repository's.

Nothing is deleted anywhere.

Run from the repository root:
``.venv/Scripts/python.exe calibration/v0.5/archive_run.py <step>``
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

DRIVE = Path("K:/Meu Drive/Pessoal/Projetos/refute/arquivo-v0.5-calibration")
OUT = Path("calibration/v0.5/runs")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def copy_new(source: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(source, "rb") as src, open(dest, "xb") as out:
        shutil.copyfileobj(src, out, 1 << 20)


def archive_run(root: Path, step: str, drive: Path = DRIVE) -> dict:
    listing = json.loads((root / OUT / step / "files.json").read_text(encoding="utf-8"))
    run = root / listing["run_folder"]
    outside = [f for f in listing["files"] if not f["in_git"]]
    if not outside:
        raise ValueError(f"{step}: no file outside git; nothing to archive")
    for record in outside:
        if sha256(run / record["path"]) != record["sha256"]:
            raise ValueError(f"{record['path']}: the run's file changed since files.json")
    target = drive / step
    if target.exists():
        raise ValueError(f"{target} exists; not replaced")
    lines = [f"{f['sha256']}  {f['path']}" for f in sorted(outside, key=lambda f: f["path"])]
    manifest = ("\n".join(lines) + "\n").encode("utf-8")
    local_manifest = root / OUT / step / "drive-manifest.sha256"
    with open(local_manifest, "xb") as handle:
        handle.write(manifest)
    for record in outside:
        copy_new(run / record["path"], target / record["path"])
    with open(target / "MANIFEST.sha256", "xb") as handle:
        handle.write(manifest)
    copy_new(Path(__file__), target / Path(__file__).name)
    problems = []
    for record in outside:
        if sha256(target / record["path"]) != record["sha256"]:
            problems.append(f"differs on the Drive: {record['path']}")
    if (target / "MANIFEST.sha256").read_bytes() != local_manifest.read_bytes():
        problems.append("the manifest on the Drive differs")
    return {
        "step": step,
        "files": [{"path": f["path"], "sha256": f["sha256"]} for f in outside],
        "manifest_sha256": sha256(local_manifest),
        "problems": problems,
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("step")
    args = parser.parse_args(argv)
    result = archive_run(Path.cwd(), args.step)
    print(json.dumps(result, indent=2))
    return 1 if result["problems"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
