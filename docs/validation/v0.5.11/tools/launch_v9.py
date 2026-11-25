"""The metered launcher of v0.5.11, version 9: the ledger writer fixed, by the maintainer's
decision received on 2026-11-25 at 00:04 local (#218, comment 7151559282), item 5.

    .venv/Scripts/python.exe -I -B docs/validation/v0.5.11/tools/launch_v9.py <unit spec>
        [--label L] [--approval URL] [-- extra arguments]

**The defect** (errata entry 9). The ledger is rewritten from the journal at the end of every
unit, by the launcher that ran it.
- A unit run by version 7 used launch_v2's charging rule. That rule does not know amendment 2's
  information role, so it charged against the 10 GB ceiling the machine counter of the units
  that amendment 2 frees (R1' and R2').
- Version 8 had the right rule, but only for the units it ran.

**The fix:**
- **One rule for every write.** Every unit, whatever its spec, writes the ledger with the
  information-aware charging rule of launch_v8 (``charge``). Its transfer is never charged for
  an attempt whose ``before`` entry says ``transfer_role: information``.
- **Amendment 2's rule** applies to a unit whose spec says ``"network": false`` and reserves 0
  transfer: the four units that the amendment names. Such a unit gets:
  - ``UV_OFFLINE=1``;
  - no stop by the machine counter;
  - the counter recorded as information.
- **Every other unit** keeps version 7's rule: a counter stop at its reservation, and its
  transfer charged.

The SHA-256 of launch_v2.py, launch_v4.py, launch_v5.py, launch_v6.py, launch_v7.py,
launch_v8.py and of this file are in every attempt's identity.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, _HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


v8 = _load("launch_v8")
v7, base = v8.v7, v8.base
INFO = v8.INFO


def main() -> int:
    spec_path = next((a for a in sys.argv[1:] if not a.startswith("-")), None)
    if spec_path is None:
        raise SystemExit("usage: launch_v9.py <unit spec> [...]")
    spec = json.loads((base.ROOT / spec_path).read_text(encoding="utf-8"))
    amended = spec.get("network") is False and spec["reserve"]["transfer_bytes"] == 0
    v9_rel = Path(__file__).resolve().relative_to(base.ROOT).as_posix()
    v8_rel = (_HERE / "launch_v8.py").relative_to(base.ROOT).as_posix()
    shas = {v9_rel: base.committed_sha256(v9_rel), v8_rel: base.committed_sha256(v8_rel)}
    base.charge = v8.charge  # the information-aware rule, for every ledger write
    if amended:
        os.environ["UV_OFFLINE"] = "1"
        stop_level = base.stop_level
        base.stop_level = lambda r, m: float("inf") if r == 0 else stop_level(r, m)
    outer = base.append_log

    def tagged(entry: dict) -> None:
        entry = dict(entry)
        if entry.get("event") == "before":
            entry["launcher_version"] = "launch_v9.py"
            entry["identity_sha256"] = {**shas, **entry.get("identity_sha256", {})}
            entry["network"] = spec.get("network")
            if amended:
                entry["transfer_role"] = INFO
                entry["network_control"] = "UV_OFFLINE=1; tests: --disable-socket"
        elif entry.get("event") == "after" and amended:
            entry["transfer_role"] = INFO
            entry["overrun"] = [o for o in entry.get("overrun", []) if o != "transfer"]
        outer(entry)

    base.append_log = tagged
    return v7.main()


if __name__ == "__main__":
    sys.exit(main())
