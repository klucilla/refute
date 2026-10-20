"""Reference digests of the white-noise synthetic scenarios, for G1 of
docs/validation/v0.2.1/reopen/correlated-noise-acceptance.md.

Run once with the generator **before** it gains the correlated mode; its output,
``white-reference.json`` next to this file, is committed on its own. The test of G1 imports
:func:`digest` from this file and compares the digests of the new code, in its default mode,
with the committed ones, so a change common to the old and the new white path would show.

:func:`digest` walks a value in a fixed order: dataclasses field by field (in declaration
order), lists and tuples item by item, dicts by sorted key, NumPy arrays by dtype, shape and
their bytes in C order and little-endian, and other values by their JSON form. It hashes the
walk with SHA-256.

Usage: uv run python docs/validation/v0.2.1/reopen/correlated/white_reference.py [<out.json>]
(the default output is white-reference.json next to this file; an existing file is never
overwritten).
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
SEEDS = (0, 1, 2)
EXTRA_SCENARIOS = ("fp_variability_dominates", "variability_train_only")


def _feed(h: Any, value: Any) -> None:
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        h.update(b"D" + type(value).__name__.encode() + b"(")
        for f in dataclasses.fields(value):
            h.update(f.name.encode() + b"=")
            _feed(h, getattr(value, f.name))
        h.update(b")")
    elif isinstance(value, np.ndarray):
        arr = np.ascontiguousarray(value)
        if arr.dtype.byteorder == ">":
            arr = arr.astype(arr.dtype.newbyteorder("<"))
        h.update(b"A" + str(arr.dtype).encode() + repr(arr.shape).encode())
        h.update(arr.tobytes())
    elif isinstance(value, (list, tuple)):
        h.update(b"L" + str(len(value)).encode() + b"[")
        for item in value:
            _feed(h, item)
        h.update(b"]")
    elif isinstance(value, dict):
        h.update(b"M" + str(len(value)).encode() + b"{")
        for key in sorted(value, key=str):
            h.update(str(key).encode() + b":")
            _feed(h, value[key])
        h.update(b"}")
    elif isinstance(value, np.generic):
        _feed(h, value.item())
    else:
        h.update(b"V" + json.dumps(value, sort_keys=True).encode())


def digest(value: Any) -> str:
    h = hashlib.sha256()
    _feed(h, value)
    return h.hexdigest()


def scenarios() -> tuple[str, ...]:
    from refute.packs.tess.synthetic import SCENARIOS

    return (*SCENARIOS, *EXTRA_SCENARIOS)


def main(argv: list[str]) -> int:
    from refute.packs.tess.synthetic import scenario_data

    out = Path(argv[0]) if argv else HERE / "white-reference.json"
    if out.exists():
        print(f"refusing to overwrite {out}")
        return 1
    commit = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    dirty = subprocess.run(
        ["git", "-C", str(ROOT), "status", "--porcelain", "--", "src"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    if dirty:
        print("src/ has uncommitted changes: the reference must come from committed code")
        return 1
    digests = {
        f"{name}|{seed}": digest(scenario_data(name, seed))
        for name in scenarios()
        for seed in SEEDS
    }
    record = {
        "format": "refute-white-reference-1",
        "code_commit": commit,
        "numpy": np.__version__,
        "seeds": list(SEEDS),
        "digests": digests,
    }
    text = json.dumps(record, indent=2, sort_keys=True) + "\n"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8", newline="\n")
    print(f"{len(digests)} digests at {commit[:7]} -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
