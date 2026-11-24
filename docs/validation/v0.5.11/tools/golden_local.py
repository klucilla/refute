"""v0.5.11, proof (i), the local record: the outputs of versions 1 to 4 on this machine
(tests/baseline_code_v0511.py, outputs()), before and after the `src/` change.

    .venv/Scripts/python.exe -I -B docs/validation/v0.5.11/tools/golden_local.py <label>

It writes each output under .cache/v0511/golden/<label>/ (kept out of git: the bytes do not travel
between machines) and docs/validation/v0.5.11/step1/golden-<label>.json with each file's SHA-256,
the machine's Python, numpy and scipy versions, and HEAD. "after" is compared byte for byte with
"before" on the same machine; the differential test compares them on every machine.
"""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tests"))

import baseline_code_v0511 as bc  # noqa: E402


def main() -> int:
    label = sys.argv[1]
    if label not in ("before", "after"):
        raise SystemExit("label must be before or after")
    import numpy
    import scipy

    folder = ROOT / ".cache" / "v0511" / "golden" / label
    if folder.exists() and any(folder.iterdir()):
        raise SystemExit(f"refused: {folder} is not empty")
    folder.mkdir(parents=True, exist_ok=True)
    files, errors = {}, []
    for name, text in sorted(bc.outputs().items()):
        data = text.encode("utf-8")
        (folder / name).write_bytes(data)
        files[name] = hashlib.sha256(data).hexdigest()
        if text.startswith("ERROR"):
            errors.append(name)
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, check=True, text=True
    ).stdout.strip()
    doc = {
        "labels": ["exploratory", "method_status: not_validated"],
        "head": head,
        "machine": {
            "python": platform.python_version(),
            "numpy": numpy.__version__,
            "scipy": scipy.__version__,
            "system": platform.system(),
        },
        "files_sha256": files,
        "error_outputs": errors,
    }
    out = ROOT / "docs" / "validation" / "v0.5.11" / "step1" / f"golden-{label}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"files": len(files), "errors": errors}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
