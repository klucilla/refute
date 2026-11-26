"""v0.5.12, the golden record of versions 1 to 4 (charter, steps 0 and 5; criterion 4): the outputs
of versions 1 to 4 on the synthetic fixtures (``tests/baseline_code_v0511.py``, ``outputs()``),
"before" at the approval commit's ``src/`` and "after" at the seal. A new copy of v0.5.11's
``golden_local.py`` (rule (c)); identity verification, not a rerun (charter, section 4).

    launch_v2 unit golden-local:
        {python} -I -B docs/validation/v0.5.12/tools/golden_local.py <label>

It runs in the AppContainer. Each output goes under ``.cache/v0512/golden/<label>/`` (out of git:
the bytes do not travel between machines). The record ``golden-<label>.json`` goes to the run's
out folder, and the launcher copies it to ``docs/validation/v0.5.12/step0/``. The record holds each
file's SHA-256 and the outputs that are errors (the payload), plus HEAD and the machine's versions
(provenance). "after" is compared with "before" on the payload, byte for byte.
"""

from __future__ import annotations

import hashlib
import json
import os
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

    folder = ROOT / ".cache" / "v0512" / "golden" / label
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
        "payload": {"files_sha256": files, "error_outputs": errors},
        "provenance": {
            "head": head,
            "python": platform.python_version(),
            "numpy": numpy.__version__,
            "scipy": scipy.__version__,
            "system": platform.system(),
            "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
    }
    out = Path(os.environ["REFUTE_RUN_OUT"]) / f"golden-{label}.json"
    out.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"files": len(files), "errors": errors}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
