"""Option (d) of the maintainer's decision of #218 comment 7191720023, item 3: map a FREE drive
letter to the project with ``subst``, so that the folder above a test file seen through that
letter is the drive's root, which is the project itself.

    v0.5.11's bootstrap-v0512 unit (a job outside the container, no network):
        {python} -I -B docs/validation/v0.5.12/tools/subst_map.py

- **The free letter** is the highest of Z to H that Windows' logical-drive mask does not show and
  whose root does not exist. It is checked before the mapping.
- **The mapping:** ``subst <letter>: C:\\Projetos\\refute``. No file is created, changed or deleted.
  The mapping lives in this user's logon session and is undone with ``subst <letter>: /D`` at the
  phase's close (and at a long stop), with a record.
- **The check:** ``<letter>:\\pyproject.toml`` is readable and has the project's SHA-256.

The record is ``docs/validation/v0.5.12/step0/subst.json``. Exit code 0 only if the check holds.
"""

from __future__ import annotations

import ctypes
import hashlib
import json
import os
import string
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "docs" / "validation" / "v0.5.12" / "step0" / "subst.json"


def main() -> int:
    if OUT.exists():
        raise SystemExit(f"refused: {OUT} exists already (one mapping only)")
    mask = ctypes.windll.kernel32.GetLogicalDrives()
    used = {string.ascii_uppercase[i] for i in range(26) if mask >> i & 1}
    free = [c for c in reversed("HIJKLMNOPQRSTUVWXYZ") if c not in used]
    free = [c for c in free if not os.path.exists(f"{c}:\\")]
    if not free:
        raise SystemExit("refused: no free drive letter from H to Z")
    letter = free[0]
    target = str(ROOT)
    run = subprocess.run(["subst", f"{letter}:", target], capture_output=True, text=True)
    mapped = Path(f"{letter}:\\") / "pyproject.toml"
    a = hashlib.sha256((ROOT / "pyproject.toml").read_bytes()).hexdigest()
    b = hashlib.sha256(mapped.read_bytes()).hexdigest() if mapped.exists() else None
    ok = run.returncode == 0 and a == b
    doc = {
        "schema": "refute-v0512-subst-1",
        "decision": "#218 comment 7191720023, item 3",
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "letters_in_use_before": sorted(used),
        "letter": letter,
        "target": "the project folder",
        "subst_exit_code": run.returncode,
        "subst_output": (run.stdout + run.stderr).strip()[-300:],
        "pyproject_sha256_via_letter": b,
        "pyproject_sha256": a,
        "undo": f"subst {letter}: /D, at the phase's close or a long stop, with a record",
        "passed": ok,
    }
    OUT.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"passed": ok, "letter": letter}))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
