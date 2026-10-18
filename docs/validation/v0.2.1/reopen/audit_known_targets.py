"""Read-only audit for the v0.2.1 exit criterion "No threshold is set, tuned or checked on a
known target or on real data; every target used in the v0.1 and v0.2 calibrations,
including development targets, is used only for declared debugging."

Known targets: every entry of ``calibration/targets.yaml`` (v0.1, with its development
target) and ``calibration/v0.2/targets.yaml`` (v0.2, with its development target), plus the
``excluded_known_targets`` of the v0.2 selection. For each one, the TIC number (as a whole
number) and its names (the entry's ``name`` and the catalog ``hostname``) are searched in
every file tracked by git outside ``calibration/``. Binary files are skipped.

The output is a JSON file (sorted keys) with, per known target, every hit (file, line
number, the kind of match) grouped by area: ``src`` and ``tests`` (code that could hold a
threshold or a check on a known target), ``scripts``, ``docs/validation/v0.2.1`` and other
files. The script reads files only; it writes only its output, whose path it refuses to
overwrite.

Usage: python docs/validation/v0.2.1/reopen/audit_known_targets.py <out.json>
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[4]
TARGET_FILES = ("calibration/targets.yaml", "calibration/v0.2/targets.yaml")


def known_targets() -> dict[int, dict]:
    out: dict[int, dict] = {}
    for rel in TARGET_FILES:
        doc = yaml.safe_load((ROOT / rel).read_text(encoding="utf-8"))
        for entry in doc.get("targets", []):
            tic = int(entry["tic_id"])
            names = {str(entry.get("name") or "").strip()}
            host = (entry.get("catalog") or {}).get("hostname")
            names.add(str(host or "").strip())
            row = out.setdefault(tic, {"names": set(), "sources": set(), "kinds": set()})
            row["names"] |= {n for n in names if n}
            row["sources"].add(rel)
            row["kinds"].add(str(entry.get("kind")))
        for tic in (doc.get("selection") or {}).get("excluded_known_targets") or []:
            row = out.setdefault(int(tic), {"names": set(), "sources": set(), "kinds": set()})
            row["sources"].add(f"{rel} (excluded_known_targets)")
    return out


def tracked_files() -> list[str]:
    done = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z"], capture_output=True, check=True
    )
    files = [f for f in done.stdout.decode("utf-8").split("\0") if f]
    return sorted(f for f in files if not f.startswith("calibration/"))


def area(path: str) -> str:
    for prefix in ("src/", "tests/", "scripts/", "docs/validation/v0.2.1/"):
        if path.startswith(prefix):
            return prefix.rstrip("/")
    return "other"


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__)
        return 2
    out_path = Path(argv[0])
    if out_path.exists():
        print(f"refusing to overwrite {out_path}")
        return 1
    targets = known_targets()
    patterns = {}
    for tic, row in targets.items():
        alternatives = [rf"(?<![0-9]){tic}(?![0-9])"]
        alternatives += [re.escape(n) for n in sorted(row["names"])]
        patterns[tic] = re.compile("|".join(alternatives))
    hits: dict[int, list[dict]] = {tic: [] for tic in targets}
    skipped_binary = 0
    files = tracked_files()
    for rel in files:
        raw = (ROOT / rel).read_bytes()
        if b"\0" in raw[:8192]:
            skipped_binary += 1
            continue
        text = raw.decode("utf-8", errors="replace")
        for number, line in enumerate(text.splitlines(), start=1):
            for tic, pattern in patterns.items():
                for match in pattern.finditer(line):
                    kind = "tic" if match.group(0) == str(tic) else "name"
                    hits[tic].append(
                        {"file": rel, "line": number, "area": area(rel), "match": kind}
                    )
    report = {
        "files_searched": len(files) - skipped_binary,
        "binary_files_skipped": skipped_binary,
        "known_targets": len(targets),
        "targets": {
            str(tic): {
                "names": sorted(row["names"]),
                "sources": sorted(row["sources"]),
                "kinds": sorted(row["kinds"]),
                "hits_by_area": {
                    a: sorted({h["file"] for h in hits[tic] if h["area"] == a})
                    for a in ("src", "tests", "scripts", "docs/validation/v0.2.1", "other")
                },
                "hits": hits[tic],
            }
            for tic, row in sorted(targets.items())
        },
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    code = sum(1 for t in report["targets"].values() if t["hits_by_area"]["src"])
    tests = sum(1 for t in report["targets"].values() if t["hits_by_area"]["tests"])
    print(f"known targets {len(targets)}; files searched {report['files_searched']}")
    print(f"targets named in src: {code}; in tests: {tests}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
