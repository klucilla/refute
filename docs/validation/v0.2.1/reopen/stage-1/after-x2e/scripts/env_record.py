"""The environment record (the maintainer's decisions of 2026-10-22, item 5): the effective
interpreter (its path, version and implementation), the platform, every installed distribution's
name and version, and the SHA-256 of `uv.lock` and `pyproject.toml` at the repository root. Written
before a lot and kept beside its manifest; compared after the lot, unchanged. No network.

  python env_record.py <out.json>
"""

import hashlib
import importlib.metadata as md
import json
import platform
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[7]


def normalized(name: str) -> str:
    """PEP 503's normalized name: each run of ``-``, ``_`` or ``.`` becomes one ``-``."""
    return re.sub(r"[-_.]+", "-", name).lower()


def main() -> int:
    seen: dict[str, str] = {}
    problems = []
    for d in md.distributions():
        name, version = d.metadata["Name"], d.version
        if not name or not version:  # unreadable metadata is refused, never recorded as empty
            problems.append(f"incomplete metadata at {d._path}")  # noqa: SLF001
            continue
        key = normalized(name)
        if key in seen:
            problems.append(f"{key} installed twice ({seen[key]} and {version})")
        seen[key] = version
    if problems:
        print("the environment record is refused:", "; ".join(problems))
        return 1
    dists = sorted(seen.items())
    record = {
        "interpreter": {
            "executable": Path(sys.executable).as_posix(),
            "version": sys.version,
            "implementation": platform.python_implementation(),
            "prefix": Path(sys.prefix).as_posix(),
        },
        "platform": {"system": platform.system(), "machine": platform.machine()},
        "lock_files": {
            name: hashlib.sha256((REPO / name).read_bytes()).hexdigest()
            for name in ("uv.lock", "pyproject.toml")
        },
        "distributions": dict(dists),
    }
    Path(sys.argv[1]).write_text(
        json.dumps(record, indent=1) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps({k: record[k] for k in ("interpreter", "lock_files")}, indent=1))
    print(len(dists), "distributions")
    return 0


if __name__ == "__main__":
    sys.exit(main())
