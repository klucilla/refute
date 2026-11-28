"""Step A5 of the VM decommissioning checklist (#135): archive the administrator-only copy.

The maintainer's decision X5 (#218, block X). The maintainer ran part A as Administrator on
2026-11-27. It copied the administrator-only records into an empty staging folder
(.cache/v0513/vm-admin-copy), and listed their sources' SHA-256 in a CSV
(.cache/v0513/vm-admin-copy-source-hashes.csv, A4).

This script runs without administrator rights. It never deletes or moves anything:
1. It reads A4's CSV and maps each source path to its relative path in the staging folder:
   - C:/ProgramData/RefuteVm/Transcripts/<x> -> Transcripts/<x>;
   - C:/ProgramData/RefuteVm-backup/<x> -> RefuteVm-backup/<x>;
   - C:/ProgramData/RefuteVm/RefuteVm.pssc -> pssc/RefuteVm.pssc.
2. It hashes every file of the staging folder.
3. It copies each staged file to the Drive folder of the archive, under admin-copy/, and reads the
   copy back from the Drive.
4. It writes manifest-admin-copy.tsv and a summary, with A4's CSV copied beside them, to the Drive
   folder and to a record folder inside the project.

**Problems** (exit 1 if there is any):
- a CSV row that is a duplicate or that does not map to a source;
- a staged file without a CSV row, or a row without a staged file;
- a hash that differs between the CSV, the staging folder and the Drive copy;
- a read error;
- RefuteVm-backup or pssc without a file.

**The recorded deviation:** Transcripts may have 0 files in all three places. The maintainer
recorded on 2026-11-27 that the source folder is empty, so this is not a problem.

Labels: exploratory, method_status: not_validated.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import sys
from pathlib import Path, PureWindowsPath

PROJECT = Path(__file__).resolve().parents[4]
STAGING = PROJECT / ".cache" / "v0513" / "vm-admin-copy"
CSV = PROJECT / ".cache" / "v0513" / "vm-admin-copy-source-hashes.csv"
DRIVE_ROOT = Path("K:/Meu Drive/Pessoal/Projetos/refute")
ROOTS = [
    (PureWindowsPath(r"C:\ProgramData\RefuteVm\Transcripts"), "Transcripts"),
    (PureWindowsPath(r"C:\ProgramData\RefuteVm-backup"), "RefuteVm-backup"),
]
PSSC = PureWindowsPath(r"C:\ProgramData\RefuteVm\RefuteVm.pssc")
REQUIRED = ("RefuteVm-backup", "pssc")  # Transcripts: 0 files allowed (decision X5)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while block := fh.read(1 << 20):
            h.update(block)
    return h.hexdigest()


def relative(src: str) -> str | None:
    p = PureWindowsPath(src)
    if str(p).lower() == str(PSSC).lower():
        return "pssc/RefuteVm.pssc"
    for root, label in ROOTS:
        try:
            rest = p.relative_to(root)
        except ValueError:
            continue
        return "/".join((label, *rest.parts))
    return None


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest-name", required=True, help="the archive's existing Drive folder")
    ap.add_argument("--record", required=True, help="a project folder for the committed record")
    args = ap.parse_args(argv)
    if any(c in args.dest_name for c in "/\\:") or args.dest_name in ("", ".", ".."):
        print("refused: --dest-name must be one plain folder name", file=sys.stderr)
        return 2
    dest = DRIVE_ROOT / args.dest_name
    target = dest / "admin-copy"
    record = (PROJECT / args.record).resolve()
    if PROJECT.resolve() not in record.parents:
        print("refused: --record must be inside the project", file=sys.stderr)
        return 2
    if not dest.is_dir() or target.exists() or not record.is_dir():
        print("refused: the archive folder must exist, admin-copy must not", file=sys.stderr)
        return 2
    for name in ("manifest-admin-copy.tsv", "summary-admin-copy.json", CSV.name):
        if (record / name).exists():
            print(f"refused: {name} already exists in the record folder", file=sys.stderr)
            return 2
    problems: list[dict] = []
    expected: dict[str, str] = {}
    with CSV.open(encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            rel = relative(row["Path"])
            if rel is None:
                problems.append({"path": row["Path"], "problem": "a CSV row maps to no source"})
            elif rel in expected:
                problems.append({"path": rel, "problem": "a duplicate CSV row"})
            else:
                expected[rel] = row["Hash"].lower()
    staged = {
        p.relative_to(STAGING).as_posix(): p for p in sorted(STAGING.rglob("*")) if p.is_file()
    }
    for rel in sorted(set(expected) - set(staged)):
        problems.append({"path": rel, "problem": "a CSV row without a staged file"})
    for rel in sorted(set(staged) - set(expected)):
        problems.append({"path": rel, "problem": "a staged file without a CSV row"})
    rows = []
    target.mkdir()
    for rel in sorted(set(expected) & set(staged)):
        src = staged[rel]
        try:
            h_stage = sha256(src)
            out = target / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, out)
            h_drive = sha256(out)
        except OSError as exc:
            problems.append({"path": rel, "problem": f"read or copy error: {exc.strerror}"})
            continue
        rows.append((rel, src.stat().st_size, expected[rel], h_stage, h_drive))
        if not (expected[rel] == h_stage == h_drive):
            problems.append({"path": rel, "problem": "the hashes differ"})
    counts = {
        label: sum(1 for r in rows if r[0].split("/")[0] == label)
        for label in ("Transcripts", "RefuteVm-backup", "pssc")
    }
    for label in REQUIRED:
        if counts[label] == 0:
            problems.append({"path": label, "problem": "no file from this source"})
    head = "path\tbytes\tsha256_a4_csv\tsha256_staging\tsha256_drive\n"
    tsv = (head + "".join(f"{r[0]}\t{r[1]}\t{r[2]}\t{r[3]}\t{r[4]}\n" for r in rows)).encode()
    csv_bytes = CSV.read_bytes()
    summary = {
        "schema": "refute-v0513-vm-admin-archive-1",
        "labels": ["exploratory", "method_status: not_validated"],
        "decision": "#218, block X, item X5; checklist #135, step A5",
        "destination": f"Drive: Projetos/refute/{args.dest_name}/admin-copy",
        "files": len(rows),
        "files_per_source": counts,
        "recorded_deviation": "Transcripts is empty at its source (the maintainer, 2026-11-27); "
        "0 files there is not a problem",
        "manifest_sha256": hashlib.sha256(tsv).hexdigest(),
        "a4_csv_sha256": hashlib.sha256(csv_bytes).hexdigest(),
        "problems": problems,
    }
    out_json = (json.dumps(summary, indent=1) + "\n").encode()
    for folder in (dest, record):
        (folder / "manifest-admin-copy.tsv").write_bytes(tsv)
        (folder / "summary-admin-copy.json").write_bytes(out_json)
        (folder / CSV.name).write_bytes(csv_bytes)
    print(
        json.dumps(
            {
                "files": len(rows),
                "files_per_source": counts,
                "manifest_sha256": summary["manifest_sha256"],
                "problems": len(problems),
            }
        )
    )
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
