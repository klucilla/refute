"""Copy the project's editable-install .pth into the container's virtual environment, from OUTSIDE
the container (v0.5.12, step 0; the maintainer's decision of #218 comment 7176253382, item 1,
fix (a)). The .venv's permissions are not changed.

    v0.5.11's bootstrap-v0512 unit (the outer meter, a job without the container):
        {python} -I -B docs/validation/v0.5.12/tools/pth_copy.py

It records the source's SHA-256 before the copy, then the source's and the copy's after it. It
refuses if the destination already exists, if a path leaves the project, or if any of the three
hashes differ. The record is ``docs/validation/v0.5.12/step0/pth-copy.json``.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
NAME = "_editable_impl_refute.pth"
SRC = ROOT / ".venv" / "Lib" / "site-packages" / NAME
DST = ROOT / ".cache" / "v0512" / "cvenv" / "Lib" / "site-packages" / NAME
OUT = ROOT / "docs" / "validation" / "v0.5.12" / "step0" / "pth-copy.json"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    for p in (SRC, DST):
        if ROOT not in p.resolve().parents:
            raise SystemExit(f"refused: {p} is outside the project")
    if DST.exists():
        raise SystemExit(f"refused: {DST} exists already")
    before = sha(SRC)
    shutil.copyfile(SRC, DST)
    after_src, after_dst = sha(SRC), sha(DST)
    ok = before == after_src == after_dst
    doc = {
        "schema": "refute-v0512-pth-copy-1",
        "decision": "#218 comment 7176253382, item 1 (fix (a))",
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": SRC.relative_to(ROOT).as_posix(),
        "destination": DST.relative_to(ROOT).as_posix(),
        "bytes": DST.stat().st_size,
        "source_sha256_before": before,
        "source_sha256_after": after_src,
        "destination_sha256": after_dst,
        "content": DST.read_text(encoding="utf-8").strip(),
        "venv_permissions_changed": False,
        "passed": ok,
    }
    OUT.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"passed": ok, "sha256": after_dst}))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
