"""The metered launcher of v0.5.11, version 7: version 6 under the charter's amendment of
2026-11-25 (section 14; #218, comment 7149572045).

    .venv/Scripts/python.exe -I -B docs/validation/v0.5.11/tools/launch_v7.py <unit spec>
        [--label L] [--approval URL] [-- extra arguments]

The only change: the phase's transfer ceiling is **10 GB** (it was 5 GB). It is set in the
shared ``CAPS`` of launch_v2.py, which every admission check and the ledger read. The other
ceilings are unchanged (10 CPU-h, 10 GB of peak disk).

The 0.1 GB reservation of a unit without network is written in that unit's spec under
``docs/validation/v0.5.11/units/``.

Everything else is version 6's: the 64-bit transfer counters, version 5's scan, and versions 4
and 2 behind them. The SHA-256 of launch_v2.py, launch_v4.py, launch_v5.py, launch_v6.py and of
this file are in every attempt's identity.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
TRANSFER_CAP_BYTES = 10_000_000_000  # the amendment of 2026-11-25


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, _HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


v6 = _load("launch_v6")
base = v6.base


def main() -> int:
    base.CAPS["transfer_bytes"] = TRANSFER_CAP_BYTES  # the shared dict, read by every check
    v7_rel = Path(__file__).resolve().relative_to(base.ROOT).as_posix()
    v7_sha = base.committed_sha256(v7_rel)  # refuses an uncommitted or changed launcher
    outer = base.append_log

    def tagged(entry: dict) -> None:
        # version 6's main wraps append_log again (launcher, its own hashes); this layer adds
        # this file's hash, its version and the amended ceiling to every "before" entry
        if entry.get("event") == "before":
            entry = dict(entry, launcher_version="launch_v7.py")
            entry["identity_sha256"] = {v7_rel: v7_sha, **entry.get("identity_sha256", {})}
            entry["transfer_cap_bytes"] = TRANSFER_CAP_BYTES
        outer(entry)

    base.append_log = tagged
    return v6.main()


if __name__ == "__main__":
    sys.exit(main())
