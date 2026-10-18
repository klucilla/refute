"""Read-only audit for the v0.2.1 exit criterion "No threshold is set, tuned or checked on a
known target or on real data": every numeric literal added to the TESS pack and to the
verdict rules since tag ``v0.2.0`` (the code of the v0.2 calibration lock, apart from the
version string), so that each one can be traced to the document that fixed it.

It runs ``git diff --unified=0 v0.2.0 <rev>`` on ``src/refute/packs/tess`` and
``src/refute/core/verdict.py`` and lists each added line holding a number with a decimal
point or a number other than 0, 1 and 2 (indices and small counts are left out), with its
file and new line number. Comments are kept: a threshold explained in a comment is still a
threshold. The output is a JSON file (sorted keys); the script refuses to overwrite it.

Usage: python docs/validation/v0.2.1/reopen/audit_thresholds.py <out.json> [<rev>]
(<rev> defaults to HEAD).
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BASE = "v0.2.0"
PATHS = ("src/refute/packs/tess", "src/refute/core/verdict.py")
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
NUMBER = re.compile(r"(?<![A-Za-z_0-9.])(\d+\.\d*|\d*\.\d+|\d+)(?:[eE][-+]?\d+)?(?![A-Za-z_0-9])")
TRIVIAL = {"0", "1", "2"}


def added_lines(rev: str) -> list[dict]:
    diff = subprocess.run(
        ["git", "-C", str(ROOT), "diff", "--unified=0", BASE, rev, "--", *PATHS],
        capture_output=True,
        check=True,
    ).stdout.decode("utf-8")
    out, file, line_no = [], None, 0
    for raw in diff.splitlines():
        if raw.startswith("+++ "):
            file = raw[6:] if raw.startswith("+++ b/") else None
            continue
        match = HUNK.match(raw)
        if match:
            line_no = int(match.group(1))
            continue
        if raw.startswith("+") and file is not None:
            text = raw[1:]
            numbers = [m.group(0) for m in NUMBER.finditer(text)]
            numbers = [n for n in numbers if n not in TRIVIAL]
            if numbers:
                out.append({"file": file, "line": line_no, "numbers": numbers, "text": text})
            line_no += 1
    return out


def main(argv: list[str]) -> int:
    if not 1 <= len(argv) <= 2:
        print(__doc__)
        return 2
    out_path = Path(argv[0])
    rev = argv[1] if len(argv) == 2 else "HEAD"
    if out_path.exists():
        print(f"refusing to overwrite {out_path}")
        return 1
    commit = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", rev], capture_output=True, check=True, text=True
    ).stdout.strip()
    base = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", f"{BASE}^{{commit}}"],
        capture_output=True,
        check=True,
        text=True,
    ).stdout.strip()
    rows = added_lines(rev)
    report = {"base": {"ref": BASE, "commit": base}, "rev": commit, "paths": list(PATHS)}
    report["added_lines_with_numbers"] = rows
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{len(rows)} added lines with numbers, {BASE} ({base[:7]}) to {rev} ({commit[:7]})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
