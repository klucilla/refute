"""The worker side of the isolation test of part (f). Standard library first, engines last.

Usage: python -I isolation_probe.py OUT_JSON LOOPBACK_PORT PROJECT_ROOT sandbox|control
The control mode (outside the sandbox) runs the network checks only.
Each check records "ok" (the operation succeeded) or the exception's type and errno. The
expectations are stated by the driver (isolation_test.py), not here.
"""

from __future__ import annotations

import json
import socket
import sys
from pathlib import Path


def attempt(fn):
    try:
        fn()
        return "ok"
    except Exception as e:  # the failure is the observation
        return f"{type(e).__name__} errno={getattr(e, 'errno', None)}"


def tcp(host: str, port: int):
    def f():
        s = socket.create_connection((host, port), timeout=5)
        s.close()

    return f


def udp_dns():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(3)
    query = b"\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x04pypi\x03org\x00\x00\x01\x00\x01"
    s.sendto(query, ("1.1.1.1", 53))
    s.recvfrom(512)
    s.close()


def read(path: Path):
    def f():
        with open(path, "rb") as fh:
            fh.read(16)

    return f


def write(path: Path):
    def f():
        with open(path, "wb") as fh:
            fh.write(b"isolation probe")

    return f


def main() -> int:
    out = Path(sys.argv[1])
    port = int(sys.argv[2])
    root = Path(sys.argv[3])
    cache = root / ".cache" / "v0510"
    data_file = next(iter(sorted((cache / "data").rglob("*_lc.fits"))))
    res: dict = {"network": {}, "read": {}, "write": {}, "imports": {}}
    res["network"]["tcp_loopback_listener"] = attempt(tcp("127.0.0.1", port))
    res["network"]["tcp_1.1.1.1_443"] = attempt(tcp("1.1.1.1", 443))
    res["network"]["tcp_pypi.org_443"] = attempt(tcp("pypi.org", 443))
    res["network"]["dns_getaddrinfo_pypi.org"] = attempt(
        lambda: socket.getaddrinfo("pypi.org", 443)
    )
    res["network"]["udp_dns_1.1.1.1_53"] = attempt(udp_dns)
    if sys.argv[4] == "control":
        out.write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
        return 0
    res["read"]["data_light_curve"] = attempt(read(data_file))
    res["read"]["engines_python"] = attempt(read(cache / "engines" / "venv" / "pyvenv.cfg"))
    res["read"]["project_pyproject"] = attempt(read(root / "pyproject.toml"))
    res["read"]["project_venv_cfg"] = attempt(read(root / ".venv" / "pyvenv.cfg"))
    res["read"]["cache_outside_grants"] = attempt(
        read(root / ".cache" / "v0510" / "fetch-data.out")
    )
    res["write"]["own_run_folder"] = attempt(write(out.parent / "probe-write.txt"))
    res["write"]["data_folder"] = attempt(write(data_file.parent / "probe-write.txt"))
    res["write"]["engines_folder"] = attempt(write(cache / "engines" / "probe-write.txt"))
    res["write"]["cache_not_granted"] = attempt(write(cache / "not-granted" / "probe-write.txt"))
    for mod in ("numpy", "astropy", "numba", "lightkurve", "exovetter", "wotan"):
        res["imports"][mod] = attempt(lambda m=mod: __import__(m))
    res["imports"]["transitleastsquares"] = attempt(lambda: __import__("transitleastsquares"))
    res["python"] = {"version": sys.version, "isolated_flag": sys.flags.isolated}
    out.write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
