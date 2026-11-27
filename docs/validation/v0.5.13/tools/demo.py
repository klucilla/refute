"""The meter's demonstration fixtures (v0.5.13 charter, section 8, Codex r1's caps wording: "Before
using the meter, demonstrate descendant CPU accounting, transfer byte accounting, and a disk bound
that includes a file created and deleted during a unit and a file retained across units").

    launch_v1 unit demo-<mode>:  {python} -I -B docs/validation/v0.5.13/tools/demo.py <mode>

Modes (harmless; they emit no case value and touch no record):
- ``cpu-child``: burns about 3 s of CPU in this process and about 3 s in a child process; the
  child's CPU must appear in the unit's job total.
- ``create-delete``: writes a 64 MiB file under .cache/v0513/demo/ and deletes it; the job's
  written bytes must cover it, though nothing remains.
- ``retain-write``: writes a 32 MiB file .cache/v0513/demo/retained.bin and keeps it.
- ``retain-check``: checks that the retained file is still there (the next unit's O_start must
  carry it); writes nothing.
- ``net-bytes``: reads one public GitHub API resource with ``gh api`` and counts the bytes of the
  response it received (``out/transfer.json``): the network units' measured inbound bytes.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
DEMO = Path(os.environ.get("REFUTE_DEMO_DIR", ROOT / ".cache" / "v0513" / "demo"))
OUT = Path(os.environ["REFUTE_RUN_OUT"])


def burn(seconds: float) -> int:
    end = time.process_time() + seconds
    x = 0
    while time.process_time() < end:
        x = (x * 1103515245 + 12345) % 2**31
    return x


def main() -> int:
    mode = sys.argv[1]
    result: dict = {"mode": mode}
    if mode == "cpu-child":
        if len(sys.argv) > 2 and sys.argv[2] == "--child":
            burn(3.0)
            return 0
        burn(3.0)
        subprocess.run([sys.executable, "-I", "-B", __file__, "cpu-child", "--child"], check=True)
        result["expected_cpu_s_at_least"] = 6.0
    elif mode == "create-delete":
        DEMO.mkdir(parents=True, exist_ok=True)
        p = DEMO / "transient.bin"
        with p.open("wb") as f:
            for _ in range(64):
                f.write(os.urandom(1 << 20))
        p.unlink()
        result["written_and_deleted_bytes"] = 64 << 20
    elif mode == "retain-write":
        DEMO.mkdir(parents=True, exist_ok=True)
        with (DEMO / "retained.bin").open("wb") as f:
            for _ in range(32):
                f.write(os.urandom(1 << 20))
        result["retained_bytes"] = 32 << 20
    elif mode == "retain-check":
        p = DEMO / "retained.bin"
        result["retained_present"] = p.is_file()
        result["retained_bytes"] = p.stat().st_size if p.is_file() else 0
        if not p.is_file():
            print(json.dumps(result))
            return 1
    elif mode == "net-bytes":
        body = subprocess.run(["gh", "api", "repos/klucilla/refute/commits/main"],
                              capture_output=True, check=True).stdout  # fmt: skip
        result["inbound_bytes"] = len(body)
        (OUT / "transfer.json").write_text(json.dumps({"inbound_bytes": len(body),
            "basis": "the bytes of the gh api response body received by the unit"}),
            encoding="utf-8")  # fmt: skip
    else:
        raise SystemExit(f"unknown mode {mode}")
    (OUT / "demo.json").write_text(json.dumps(result) + "\n", encoding="utf-8")
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
