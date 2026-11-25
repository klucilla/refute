"""The meter's demonstration, the new network fixture (v0.5.12, charter step 0; approved by the
maintainer's decision of #218 comment 7174740316, item 1 b). It replaces ``demo.py network``,
whose expectation was wrong (``demo-findings.md``); ``demo.py`` is not edited.

Run in the AppContainer through ``launch_v2.py``, with ``REFUTE_LISTENER_PORT`` set: the launcher
holds that listener in its own process, OUTSIDE the container, and counts the connections it
accepts (the expected count is 0).

From this process and from one child process, it tries:
- TCP to 1.1.1.1:443, DNS for pypi.org, and TCP to github.com:443 (each must fail);
- TCP to the launcher's listener on 127.0.0.1 (must fail);
- **information only:** a loopback connection to a listener opened inside the container itself,
  which Windows allows within one AppContainer; it is recorded, never counted as a failure.

Exit code 0 when every counted attempt failed, from both processes; 1 otherwise.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys


def attempt(fn) -> str:
    try:
        r = fn()
        if hasattr(r, "close"):
            r.close()
        return "ok"
    except OSError as exc:
        return f"fail: {type(exc).__name__} {getattr(exc, 'winerror', '') or ''}".strip()


def connect(host: str, port: int):
    return lambda: socket.create_connection((host, port), timeout=5)


def try_net(prefix: str) -> tuple[dict, dict]:
    port = int(os.environ["REFUTE_LISTENER_PORT"])
    counted = {
        "tcp_1.1.1.1_443": attempt(connect("1.1.1.1", 443)),
        "dns_pypi.org": attempt(lambda: socket.getaddrinfo("pypi.org", 443)),
        "tcp_github.com_443": attempt(connect("github.com", 443)),
        "tcp_launcher_listener": attempt(connect("127.0.0.1", port)),
    }
    srv = socket.socket()
    try:
        srv.bind(("127.0.0.1", 0))
        srv.listen(1)
        own = srv.getsockname()[1]
        info = {"same_container_loopback": attempt(connect("127.0.0.1", own))}
    finally:
        srv.close()
    counted = {prefix + k: v for k, v in counted.items()}
    info = {prefix + k: v for k, v in info.items()}
    return counted, info


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "child":
        counted, info = try_net("child_")
        print(json.dumps({"counted": counted, "info": info}))
        return 0
    counted, info = try_net("")
    argv = [sys.executable, "-I", "-B", __file__, "child"]
    child = subprocess.run(argv, capture_output=True, text=True)
    theirs = json.loads(child.stdout.strip() or "{}")
    counted.update(theirs.get("counted", {}))
    info.update(theirs.get("info", {}))
    succeeded = [k for k, v in counted.items() if v == "ok"]
    print(json.dumps({"counted": counted, "information": info, "succeeded": succeeded}))
    return 1 if succeeded or len(counted) < 8 else 0


if __name__ == "__main__":
    raise SystemExit(main())
