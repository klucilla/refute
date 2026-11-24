"""The isolation test of part (f), recorded before any tool runs on a TOI.

The maintainer's decision of 2026-11-24 (#218, comment 7140572901): before running the tools,
prove with a recorded test that the worker in the AppContainer opens no network connection and
can read and write only where it should.

The driver:
1. opens a TCP listener on 127.0.0.1 (a local target that must be refused);
2. runs ``isolation_probe.py`` in **control** mode outside the sandbox, with the project's
   Python: the network checks there show that the network is reachable without the sandbox;
3. runs the same probe in the AppContainer, with the engines' Python, granted read on the
   engines and the data, and write on its own run folder only;
4. compares each observation with its expectation and writes isolation-test.json.

The test passes only if every expectation holds. Paths in the record are relative to the project.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sandbox  # noqa: E402

PROJECT = sandbox.PROJECT
CACHE = sandbox.CACHE_ROOT
OUT = HERE / "isolation-test.json"

EXPECT_SANDBOX = {
    "network": {
        "tcp_loopback_listener": "fail",
        "tcp_1.1.1.1_443": "fail",
        "tcp_pypi.org_443": "fail",
        "dns_getaddrinfo_pypi.org": "fail",
        "udp_dns_1.1.1.1_53": "fail",
    },
    "read": {
        "data_light_curve": "ok",
        "engines_python": "ok",
        "project_pyproject": "fail",
        "project_venv_cfg": "fail",
        "cache_outside_grants": "fail",
    },
    "write": {
        "own_run_folder": "ok",
        "data_folder": "fail",
        "engines_folder": "fail",
        "cache_not_granted": "fail",
    },
    "imports": {
        m: "ok"
        for m in (
            "numpy",
            "astropy",
            "numba",
            "lightkurve",
            "exovetter",
            "wotan",
            "transitleastsquares",
        )
    },
}
EXPECT_CONTROL = {"tcp_loopback_listener": "ok", "tcp_1.1.1.1_443": "ok"}


def listener() -> tuple[socket.socket, int, list]:
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind(("127.0.0.1", 0))
    srv.listen(8)
    accepted: list = []

    def loop():
        while True:
            try:
                c, addr = srv.accept()
            except OSError:
                return
            accepted.append(time.time())
            c.close()

    threading.Thread(target=loop, daemon=True).start()
    return srv, srv.getsockname()[1], accepted


def rel(p: Path) -> str:
    return Path(p).resolve().relative_to(PROJECT).as_posix()


def main() -> int:
    workers = CACHE / "workers"
    workers.mkdir(parents=True, exist_ok=True)
    probe_src = HERE / "isolation_probe.py"
    probe = workers / "isolation_probe.py"
    shutil.copyfile(probe_src, probe)
    (CACHE / "not-granted").mkdir(exist_ok=True)
    profile = sandbox.ensure_profile()
    _, sid = sandbox.container_sid()
    sandbox.grant(CACHE / "engines")
    sandbox.grant(CACHE / "data")
    sandbox.grant(workers)
    run_dir = CACHE / "runs" / "isolation-test"
    run_dir.mkdir(parents=True, exist_ok=True)
    sandbox.grant(run_dir, write=True)

    srv, port, accepted = listener()
    control_out = CACHE / "runs" / "isolation-control.json"
    subprocess.run(
        [sys.executable, "-I", str(probe), str(control_out), str(port), str(PROJECT), "control"],
        check=True,
        timeout=120,
    )
    control = json.loads(control_out.read_text(encoding="utf-8"))
    accepted_after_control = len(accepted)

    sand_out = run_dir / "probe.json"
    py = CACHE / "engines" / "venv" / "Scripts" / "python.exe"
    rec = sandbox.run(
        [str(py), "-I", str(probe), str(sand_out), str(port), str(PROJECT), "sandbox"],
        cwd=run_dir,
        run_dir=run_dir,
        workers=1,
        timeout_s=600,
    )
    time.sleep(1)
    accepted_by_sandbox = len(accepted) - accepted_after_control
    srv.close()
    observed = json.loads(sand_out.read_text(encoding="utf-8")) if sand_out.exists() else {}

    checks = []
    for group, exp in EXPECT_SANDBOX.items():
        for name, want in exp.items():
            got = observed.get(group, {}).get(name, "missing")
            holds = (got == "ok") if want == "ok" else (got not in ("ok", "missing"))
            checks.append(
                {
                    "where": "sandbox",
                    "check": f"{group}.{name}",
                    "expected": want,
                    "observed": got,
                    "holds": holds,
                }
            )
    for name, want in EXPECT_CONTROL.items():
        got = control["network"].get(name, "missing")
        checks.append(
            {
                "where": "control",
                "check": f"network.{name}",
                "expected": want,
                "observed": got,
                "holds": got == "ok",
            }
        )
    checks.append(
        {
            "where": "listener",
            "check": "connections accepted from the sandboxed run",
            "expected": 0,
            "observed": accepted_by_sandbox,
            "holds": accepted_by_sandbox == 0,
        }
    )
    passed = all(c["holds"] for c in checks) and rec["exit_code"] == 0
    doc = {
        "schema": "refute-v0510-isolation-test-1",
        "mode": "exploratory",
        "decision": "#218 comment 7140572901",
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "appcontainer": {
            "name": sandbox.CONTAINER_NAME,
            "sid": sid,
            "capabilities": [],
            "profile": profile,
            "created_outside_the_project": [
                "HKCU registry key: Software/Classes/Local Settings/Software/Microsoft/Windows/"
                "CurrentVersion/AppContainer/Mappings/" + sid,
                "folder: <local application-data folder>/Packages/" + sandbox.CONTAINER_NAME,
            ],
            "removal": "the maintainer's, with delete_profile.py; the session never deletes it",
        },
        "grants": {
            "read": [rel(CACHE / "engines"), rel(CACHE / "data"), rel(workers)],
            "write": [rel(run_dir)],
        },
        "probe_sha256": hashlib.sha256(probe.read_bytes()).hexdigest(),
        "sandboxed_run": {k: v for k, v in rec.items() if k != "container_sid"},
        "control": control,
        "observed": observed,
        "checks": checks,
        "passed": passed,
    }
    OUT.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    for c in checks:
        print(("ok  " if c["holds"] else "FAIL"), c["where"], c["check"], "->", c["observed"])
    print("isolation test passed:", passed)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
