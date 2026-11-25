"""The meter's demonstration fixtures (v0.5.12, charter step 0). Harmless; one mode per unit.

    demo.py cpu         burn about 2 CPU-s here and about 3 CPU-s in a child process
    demo.py transient   write a 50 MB file under TEMP and delete it
    demo.py retain      write a 30 MB file under the run's out folder and keep it
    demo.py network     try the network from this process and from a child; every try must fail

Each mode prints one JSON line. The ``network`` mode exits 1 if any attempt succeeds.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path


def burn(seconds: float) -> float:
    t0 = time.process_time()
    x = 0
    while time.process_time() - t0 < seconds:
        x += 1
    return time.process_time() - t0


def try_net() -> dict:
    out = {}
    for name, fn in (
        ("tcp_1.1.1.1_443", lambda: socket.create_connection(("1.1.1.1", 443), timeout=5)),
        ("dns_pypi.org", lambda: socket.getaddrinfo("pypi.org", 443)),
        ("tcp_github.com_443", lambda: socket.create_connection(("github.com", 443), timeout=5)),
    ):
        try:
            r = fn()
            if hasattr(r, "close"):
                r.close()
            out[name] = "ok"
        except OSError as exc:
            out[name] = f"fail: {type(exc).__name__} {getattr(exc, 'winerror', '')}".strip()
    srv = None
    try:
        srv = socket.socket()
        srv.bind(("127.0.0.1", 0))
        srv.listen(1)
        port = srv.getsockname()[1]
        c = socket.create_connection(("127.0.0.1", port), timeout=5)
        c.close()
        out["tcp_loopback"] = "ok"
    except OSError as exc:
        out["tcp_loopback"] = f"fail: {type(exc).__name__}"
    finally:
        if srv is not None:
            srv.close()
    return out


def main() -> int:
    mode = sys.argv[1]
    if mode == "cpu":
        child = subprocess.run(
            [sys.executable, "-I", "-B", __file__, "cpu-child"], capture_output=True, text=True
        )
        mine = burn(2.0)
        print(json.dumps({"mode": mode, "own_cpu_s": mine, "child": child.stdout.strip()}))
        return 0
    if mode == "cpu-child":
        print(json.dumps({"child_cpu_s": burn(3.0)}))
        return 0
    if mode == "transient":
        p = Path(os.environ["TEMP"]) / "transient.bin"
        with p.open("wb") as f:
            for _ in range(50):
                f.write(os.urandom(1 << 20))
        size = p.stat().st_size
        p.unlink()
        print(json.dumps({"mode": mode, "written_then_deleted": size}))
        return 0
    if mode == "retain":
        p = Path(os.environ["REFUTE_RUN_OUT"]) / "retained.bin"
        with p.open("wb") as f:
            for _ in range(30):
                f.write(os.urandom(1 << 20))
        print(json.dumps({"mode": mode, "retained": p.stat().st_size}))
        return 0
    if mode == "network":
        mine = try_net()
        child = subprocess.run(
            [sys.executable, "-I", "-B", __file__, "network-child"], capture_output=True, text=True
        )
        theirs = json.loads(child.stdout.strip() or "{}")
        ok = [k for k, v in {**mine, **theirs}.items() if v == "ok"]
        print(json.dumps({"mode": mode, "process": mine, "child": theirs, "succeeded": ok}))
        return 1 if ok or not theirs else 0
    if mode == "network-child":
        print(json.dumps({f"child_{k}": v for k, v in try_net().items()}))
        return 0
    raise SystemExit(f"unknown mode {mode}")


if __name__ == "__main__":
    raise SystemExit(main())
