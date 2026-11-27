"""The metered launcher of v0.5.13, version 3: launch_v2.py, unchanged, with one more named
network kind.

    .venv/Scripts/python.exe -I -B docs/validation/v0.5.13/tools/launch_v3.py <unit spec> [...]

The maintainer's decision D5 (#218, comment 7207651312) approves one download of the files
published on TestPyPI, counted by the meter. ``launch_v1.py`` names only ``github``, ``review`` and
``mast``; this version adds ``testpypi`` (endpoint ``test.pypi.org`` and its file host). It touches
nothing else: how a unit runs, how it is metered and the version-2 order proof are those of
``launch_v2.py``. Every ``before`` entry names this launcher and carries its SHA-256.
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
    v1.NETWORK_KINDS = (*v1.NETWORK_KINDS, "testpypi")
    me = Path(__file__).resolve().relative_to(v1.ROOT).as_posix()
    my_sha = v1.committed_sha256(me)
    inner = v1.append_log

    def tagged(entry: dict) -> None:
        if entry.get("event") == "before":
            entry = dict(entry)
            entry["launcher"] = "launch_v3.py"
            entry["identity_sha256"] = {me: my_sha, **entry.get("identity_sha256", {})}
        inner(entry)

    v1.append_log = tagged
    return v2.main()


if __name__ == "__main__":
    sys.exit(main())
