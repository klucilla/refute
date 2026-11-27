"""The metered launcher of v0.5.13, version 4: launch_v2.py, unchanged, with two more named
network kinds.

    .venv/Scripts/python.exe -I -B docs/validation/v0.5.13/tools/launch_v4.py <unit spec> [...]

``launch_v3.py`` added ``testpypi``. The maintainer's decision F3 (#218, comment 7218843893;
confirmed by G1, comment 7219180143) approves one download of the two files published on PyPI,
counted by the meter. This version names ``testpypi`` and ``pypi`` (endpoint ``pypi.org`` and its
file host). It touches nothing else: how a unit runs, how it is metered and the version-2 order
proof are those of ``launch_v2.py``. Every ``before`` entry names this launcher and carries its
SHA-256.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("launch_v2", _HERE / "launch_v2.py")
v2 = importlib.util.module_from_spec(_spec)
sys.modules["launch_v2"] = v2
_spec.loader.exec_module(v2)
v1 = v2.v1


def main() -> int:
    v1.NETWORK_KINDS = (*v1.NETWORK_KINDS, "testpypi", "pypi")
    me = Path(__file__).resolve().relative_to(v1.ROOT).as_posix()
    my_sha = v1.committed_sha256(me)
    inner = v1.append_log

    def tagged(entry: dict) -> None:
        if entry.get("event") == "before":
            entry = dict(entry)
            entry["launcher"] = "launch_v4.py"
            entry["identity_sha256"] = {me: my_sha, **entry.get("identity_sha256", {})}
        inner(entry)

    v1.append_log = tagged
    return v2.main()


if __name__ == "__main__":
    sys.exit(main())
