"""Copy one finished calibration run into ``calibration/v0.5/runs/<step>/`` for its commit
(PROTOCOL.md, section 8, step 5: each result committed; raw outputs above 5 MB archived to the
Drive with a checked SHA-256 manifest, never in git).

The run folder is ``.cache/v05/calibration/<step>`` (``refute.packs.tess.calib05.steps``). This
script only reads it, and refuses a run that is not finished: its ``running.marker`` present, or
its records not exactly its manifest's tasks with their cost lines (``runner.all_records``). It
writes, each file created exclusively (never over a file):

- ``files.json``: every file of the run folder (``owner.lock`` excluded), its size and SHA-256;
- a byte copy of ``manifest.json``, ``report.json``, ``records.jsonl`` and ``cost.jsonl`` when
  present and at most 5 MB each; a larger file is listed in ``files.json`` with ``"in_git":
  false`` and is archived to the Drive by hand with its manifest.

Run from the repository root:
``.venv/Scripts/python.exe calibration/v0.5/collect_run.py <step>``
(steps: c1-prefix, c2-prefix, c1-confirmation, c2, c3; c2-fetch, c3-fetch and budget are single
JSON files: ``--file <name>``).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

RUNS = Path(".cache/v05/calibration")
OUT = Path("calibration/v0.5/runs")
LIMIT = 5 * 1024 * 1024
COPIED = ("manifest.json", "report.json", "records.jsonl", "cost.jsonl")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def is_link(path: Path) -> bool:
    return path.is_symlink() or (path.exists() and path.is_junction())


def copy_new(source: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(source, "rb") as src, open(dest, "xb") as out:
        out.write(src.read())
    if sha256(dest) != sha256(source):
        raise ValueError(f"{dest}: the copy differs from {source}")


def collect_run(root: Path, step: str) -> dict:
    from refute.packs.tess.calib05 import runner

    run = root / RUNS / step
    if is_link(run) or not run.is_dir():
        raise ValueError(f"{run} is not a run folder")
    if (run / "running.marker").exists():
        raise ValueError(f"{run} is not finished (running.marker)")
    runner.all_records(run)  # refuses a run whose records are not exactly its tasks
    files = []
    for path in sorted(p for p in run.rglob("*") if p.is_file() and p.name != "owner.lock"):
        if is_link(path):
            raise ValueError(f"{path} is a link")
        size = path.stat().st_size
        rel = path.relative_to(run).as_posix()
        files.append({"path": rel, "bytes": size, "sha256": sha256(path), "in_git": size <= LIMIT})
    out = root / OUT / step
    for record in files:
        if record["path"] in COPIED and record["in_git"]:
            copy_new(run / record["path"], out / record["path"])
        elif record["path"] not in COPIED:
            record["in_git"] = False
    listing = {"run_folder": (RUNS / step).as_posix(), "files": files}
    with open(out / "files.json", "x", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(listing, indent=2) + "\n")
    return listing


def collect_file(root: Path, name: str) -> dict:
    source = root / RUNS / name
    if is_link(source) or not source.is_file():
        raise ValueError(f"{source} is not a file")
    if source.stat().st_size > LIMIT:
        raise ValueError(f"{source} is above 5 MB: archive it to the Drive")
    copy_new(source, root / OUT / name)
    return {"path": name, "sha256": sha256(source)}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("step", nargs="?")
    group.add_argument("--file")
    args = parser.parse_args(argv)
    root = Path.cwd()
    result = collect_file(root, args.file) if args.file else collect_run(root, args.step)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
