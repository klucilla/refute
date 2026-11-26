"""Install the cvenv's sitecustomize (v0.5.12, step 0; #218 comment 7190662570, item 1).

    launch_v2 unit sitecustomize-install:
        {python} -I -B docs/validation/v0.5.12/tools/sitecustomize_install.py

It copies the committed ``tools/cvenv_sitecustomize.py`` to
``.cache/v0512/cvenv/Lib/site-packages/sitecustomize.py`` and nowhere else; the project's
``.venv`` is not touched. It refuses if the destination exists or a path leaves
``.cache/v0512/cvenv``, and checks the SHA-256 of the source before the copy and of both after.
The record ``sitecustomize-install.json`` goes to the run's out folder (copied to ``step0/``).
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / "docs" / "validation" / "v0.5.12" / "tools" / "cvenv_sitecustomize.py"
CVENV = ROOT / ".cache" / "v0512" / "cvenv"
DST = CVENV / "Lib" / "site-packages" / "sitecustomize.py"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    if CVENV.resolve() not in DST.resolve().parents:
        raise SystemExit("refused: the destination is outside the cvenv")
    if DST.exists():
        raise SystemExit(f"refused: {DST} exists already")
    before = sha(SRC)
    shutil.copyfile(SRC, DST)
    after_src, after_dst = sha(SRC), sha(DST)
    ok = before == after_src == after_dst
    doc = {
        "schema": "refute-v0512-sitecustomize-install-1",
        "decision": "#218 comment 7190662570, item 1",
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": SRC.relative_to(ROOT).as_posix(),
        "destination": DST.relative_to(ROOT).as_posix(),
        "source_sha256_before": before,
        "source_sha256_after": after_src,
        "destination_sha256": after_dst,
        "venv_changed": False,
        "passed": ok,
    }
    out = Path(os.environ["REFUTE_RUN_OUT"]) / "sitecustomize-install.json"
    out.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"passed": ok, "sha256": after_dst}))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
