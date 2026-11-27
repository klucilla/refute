"""Archive the Refute VM's records to the maintainer's Drive before its decommissioning (#135).

The maintainer's decision block W, item W1(g)1 (#218, recorded at comment 7229841832). It runs
without administrator rights. It copies every file it can read, then checks each copy against
its original by SHA-256. It never deletes or moves anything.

The sources:
- ``programdata``: C:/ProgramData/RefuteVm (the endpoint's Log and State; the JEA transcripts and
  RefuteVm.pssc are readable by administrators only);
- ``programdata-backup``: C:/ProgramData/RefuteVm-backup (the .reg backup of the WinRM listener;
  administrators only);
- ``cache-vm``: the project's .cache/vm, except ``ssh/`` and ``gnupg/``. A private key or a keyring
  never enters generic archiving (CLAUDE.md).

Whatever cannot be read is listed as ``needs_elevation`` and left for the maintainer. The
destination folder must not exist. It writes, in the destination:
- ``manifest.tsv``: one row per file, with its label, relative path, size, source SHA-256 and
  copy SHA-256;
- ``summary.json``: the counts, the excluded paths, the paths that need elevation, the problems,
  and the manifest's own SHA-256.

The same two files are also written to ``--record``, a folder inside the project that git tracks.
They hold relative paths and hashes only, never file contents.

Exit 0 only if there are no problems: every readable file copied, and every copy equal to its
original. Labels: exploratory, method_status: not_validated.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[4]
SOURCES = [
    ("programdata", Path("C:/ProgramData/RefuteVm"), ()),
    ("programdata-backup", Path("C:/ProgramData/RefuteVm-backup"), ()),
    ("cache-vm", PROJECT / ".cache" / "vm", ("ssh", "gnupg")),
]
DRIVE_ROOT = Path("K:/Meu Drive/Pessoal/Projetos/refute")
CHUNK = 1 << 20


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while block := fh.read(CHUNK):
            h.update(block)
    return h.hexdigest()


def walk(label: str, root: Path, excluded: tuple[str, ...]):
    """Yield ('file', rel) or ('denied', rel, reason) or ('excluded', rel), in sorted order."""
    if not root.exists():
        yield ("missing", "", "the source does not exist")
        return
    stack = [Path()]
    while stack:
        rel_dir = stack.pop()
        try:
            entries = sorted(os.scandir(root / rel_dir), key=lambda e: e.name)
        except PermissionError as exc:
            yield ("denied", rel_dir.as_posix(), f"listing: {exc.strerror}")
            continue
        for entry in entries:
            rel = rel_dir / entry.name
            if rel_dir == Path() and entry.name in excluded:
                yield (
                    "excluded",
                    rel.as_posix(),
                    "a private key or keyring: never archived generically",
                )
                continue
            if entry.is_symlink():
                yield ("denied", rel.as_posix(), "a link: not followed")
            elif entry.is_dir():
                stack.append(rel)
            else:
                yield ("file", rel.as_posix(), "")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--dest-name", required=True, help="the new subfolder under the Drive's refute folder"
    )
    ap.add_argument(
        "--record", required=True, help="a project folder for the committed copy of the manifest"
    )
    args = ap.parse_args(argv)
    if any(c in args.dest_name for c in "/\\:") or args.dest_name in ("", ".", ".."):
        print("refused: --dest-name must be one plain folder name", file=sys.stderr)
        return 2
    dest = DRIVE_ROOT / args.dest_name
    record = (PROJECT / args.record).resolve()
    if PROJECT.resolve() not in record.parents:
        print("refused: --record must be inside the project", file=sys.stderr)
        return 2
    if not DRIVE_ROOT.is_dir():
        print(f"refused: {DRIVE_ROOT} is not reachable", file=sys.stderr)
        return 2
    if dest.exists() or record.exists():
        print("refused: the destination or the record folder already exists", file=sys.stderr)
        return 2
    dest.mkdir()
    rows, denied, excluded, problems = [], [], [], []
    for label, root, skip in SOURCES:
        for kind, rel, reason in walk(label, root, skip):
            where = f"{label}/{rel}" if rel else label
            if kind == "excluded":
                excluded.append({"path": where, "reason": reason})
                continue
            if kind in ("denied", "missing"):
                denied.append(
                    {
                        "path": where,
                        "source": str(root / rel) if rel else str(root),
                        "reason": reason,
                    }
                )
                continue
            src = root / rel
            try:
                src_hash = sha256(src)
            except PermissionError as exc:
                denied.append(
                    {"path": where, "source": str(src), "reason": f"reading: {exc.strerror}"}
                )
                continue
            target = dest / label / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, target)
            copy_hash = sha256(target)
            again = sha256(src)
            row = {
                "label": label,
                "path": rel,
                "bytes": src.stat().st_size,
                "sha256_source": src_hash,
                "sha256_copy": copy_hash,
            }
            rows.append(row)
            if not (src_hash == copy_hash == again):
                problems.append({"path": where, "problem": "the copy differs from its original"})
    labels_with_files = {r["label"] for r in rows}
    for label, _, _ in SOURCES:
        if label not in labels_with_files:
            problems.append({"path": label, "problem": "no file archived from this source"})
    tsv = "label\tpath\tbytes\tsha256_source\tsha256_copy\n" + "".join(
        f"{r['label']}\t{r['path']}\t{r['bytes']}\t{r['sha256_source']}\t{r['sha256_copy']}\n"
        for r in rows
    )
    tsv_bytes = tsv.encode("utf-8")
    summary = {
        "schema": "refute-v0513-vm-archive-1",
        "labels": ["exploratory", "method_status: not_validated"],
        "decision": "#218 comment 7229841832, item W1(g)1",
        "destination": f"Drive: Projetos/refute/{args.dest_name}",
        "files": len(rows),
        "bytes": sum(r["bytes"] for r in rows),
        "manifest_sha256": hashlib.sha256(tsv_bytes).hexdigest(),
        "excluded": excluded,
        "needs_elevation": denied,
        "problems": problems,
    }
    out = json.dumps(summary, indent=1, ensure_ascii=False) + "\n"
    record.mkdir(parents=True)
    for folder in (dest, record):
        (folder / "manifest.tsv").write_bytes(tsv_bytes)
        (folder / "summary.json").write_bytes(out.encode("utf-8"))
    for folder in (dest, record):
        if (
            hashlib.sha256((folder / "manifest.tsv").read_bytes()).hexdigest()
            != summary["manifest_sha256"]
        ):
            problems.append({"path": str(folder), "problem": "the written manifest differs"})
    print(
        json.dumps(
            {k: summary[k] for k in ("files", "bytes", "manifest_sha256")}
            | {"needs_elevation": len(denied), "excluded": len(excluded), "problems": len(problems)}
        )
    )
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
