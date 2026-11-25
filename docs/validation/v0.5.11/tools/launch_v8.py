"""The metered launcher of v0.5.11, version 8: version 7 under the charter's amendment 2 of
2026-11-25 (section 15; #218, comment 7149778857). The change is only that rule, with no new
Codex round, as the amendment says.

    .venv/Scripts/python.exe -I -B docs/validation/v0.5.11/tools/launch_v8.py <unit spec>
        [--label L] [--approval URL] [-- extra arguments]

**For a unit whose spec says ``"network": false``:**
- **The ban on network is its control.**
  - The environment gets ``UV_OFFLINE=1``, so uv makes no download.
  - The tests keep pytest's ``--disable-socket`` (pyproject.toml's addopts).
  - A network attempt makes the unit fail, and the failure is the maintainer's stop.
- **Its transfer reservation must be 0.** A spec with any other value is refused.
- **The machine's transfer counter does not stop it.** The counter is still read and recorded
  in every attempt, as information (``transfer_role: information``).
- **The ledger does not charge** that information against the 10 GB ceiling, which applies to
  the units with network (charter, section 14).
- **The rest is unchanged:** a lost counter read is still lost telemetry, and the CPU and disk
  rules are as before.

**For a unit with network:** version 7, unchanged.

The SHA-256 of launch_v2.py, launch_v4.py, launch_v5.py, launch_v6.py, launch_v7.py and of this
file are in every attempt's identity.
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


v7 = _load("launch_v7")
base = v7.base
INFO = "information"


def charge(entries: list[dict]) -> dict:
    """launch_v2's charging rule, with the transfer of an information-only attempt left out."""
    befores = [e for e in entries if e["event"] == "before"]
    afters = {e.get("attempt_id") or e["instance_key"]: e for e in entries if e["event"] == "after"}
    cpu = tr = 0.0
    peak = 0
    for b in befores:
        key = b.get("attempt_id") or b["instance_key"]
        a = afters.get(key)
        res = b["reserve"]
        info = b.get("transfer_role") == INFO
        if a is not None and a.get("telemetry_complete") and "launcher" in b:
            cpu += a["cpu_s"]
            tr += 0 if info else a["transfer_bytes_upper"]
            peak = max(peak, a["disk_peak_bytes"])
        else:
            cpu += max(res["cpu_s"], (a or {}).get("cpu_s", 0.0))
            tr += (
                0 if info else max(res["transfer_bytes"], (a or {}).get("transfer_bytes_upper", 0))
            )
            peak = max(peak, res["disk_bytes"], (a or {}).get("disk_peak_bytes", 0))
    return {"cpu_s": round(cpu, 3), "transfer_bytes": int(tr), "disk_peak_bytes": int(peak)}


def main() -> int:
    spec_path = next((a for a in sys.argv[1:] if not a.startswith("-")), None)
    if spec_path is None:
        raise SystemExit("usage: launch_v8.py <unit spec> [...]")
    spec = json.loads((base.ROOT / spec_path).read_text(encoding="utf-8"))
    no_network = spec.get("network") is False
    if no_network and spec["reserve"]["transfer_bytes"] != 0:
        raise SystemExit("refused: a unit without network reserves 0 transfer (section 15)")
    v8_rel = Path(__file__).resolve().relative_to(base.ROOT).as_posix()
    v8_sha = base.committed_sha256(v8_rel)
    base.charge = charge
    if no_network:
        os.environ["UV_OFFLINE"] = "1"
        stop_level = base.stop_level
        # the only zero reservation is the transfer of a unit without network: no stop for it
        base.stop_level = lambda r, m: float("inf") if r == 0 else stop_level(r, m)
    outer = base.append_log

    def tagged(entry: dict) -> None:
        entry = dict(entry)
        if entry.get("event") == "before":
            entry["launcher_version"] = "launch_v8.py"
            entry["identity_sha256"] = {v8_rel: v8_sha, **entry.get("identity_sha256", {})}
            entry["network"] = not no_network
            if no_network:
                entry["transfer_role"] = INFO
                entry["network_control"] = "UV_OFFLINE=1; tests: --disable-socket"
        elif entry.get("event") == "after" and no_network:
            entry["transfer_role"] = INFO
            entry["overrun"] = [o for o in entry.get("overrun", []) if o != "transfer"]
        outer(entry)

    base.append_log = tagged
    return v7.main()


if __name__ == "__main__":
    sys.exit(main())
