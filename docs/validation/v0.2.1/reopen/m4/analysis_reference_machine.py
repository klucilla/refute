"""A supplementary record of the machine of ``analysis-reference.json`` (map Amendments 15 and 17;
the maintainer's item 7 of 2026-10-18): the reference itself records the commit, the platform and
numpy; this records, on the same machine and with the same environment, the interpreter and the CPU
features numpy enables (which select its SIMD code paths and so the digests). Reconstructed on
2026-10-18; it does not edit the reference.

Run from the worktree root with the virtual environment's Python; writes
``analysis-reference-machine.json`` next to this file.
"""

import json
import platform
import sys
from pathlib import Path

import numpy as np
from numpy._core._multiarray_umath import __cpu_baseline__, __cpu_dispatch__, __cpu_features__

HERE = Path(__file__).resolve().parent

record = {
    "reference": "analysis-reference.json",
    "reconstructed_utc_date": "2026-10-18",
    "platform": sys.platform,
    "python": platform.python_version(),
    "implementation": platform.python_implementation(),
    "numpy": np.__version__,
    "cpu_features_enabled": sorted(k for k, v in __cpu_features__.items() if v),
    "cpu_baseline": list(__cpu_baseline__),
    "cpu_dispatch": list(__cpu_dispatch__),
    "machine": platform.machine(),
}
(HERE / "analysis-reference-machine.json").write_text(
    json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
)
print(json.dumps(record, indent=2, sort_keys=True))
