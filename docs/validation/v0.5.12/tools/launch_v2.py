"""The metered launcher of v0.5.12, version 2: the fixes of the meter's demonstration, approved by
the maintainer's decision recorded at 19:15 local on 2026-11-25 (#218, comment 7174740316),
item 1 (``docs/validation/v0.5.12/step0/demo-findings.md``).

    .venv/Scripts/python.exe -I -B docs/validation/v0.5.12/tools/launch_v2.py <unit spec>
        [--label L] [--approval URL] [-- extra arguments]

It runs ``launch_v1.py`` unchanged (rule (c): a new file, nothing edited), with three changes:
- **a) The container's temporary folder.** Windows points ``TEMP`` and ``TMP`` of an AppContainer
  process to ``Packages/<container>/AC/Temp`` under the local application-data folder its
  environment names. This version creates that folder in the run's private folder before the
  start, points ``TEMP`` and ``TMP`` there, and passes ``USERNAME`` into the container's
  environment (``scripts/commit_checked.py``'s privacy check uses it).
- **b) A listener outside the container.** For a unit whose spec says ``"listener": true``, the
  launcher opens a TCP listener on 127.0.0.1 in its own process, outside the container, passes its
  port as ``REFUTE_LISTENER_PORT``, and records in the ``after`` entry the number of connections
  it accepted while the unit ran (``listener_accepted``; the expected value is 0).
- **c) The container's virtual environment.** ``{python}`` is ``.cache/v0512/cvenv/Scripts/
  python.exe``, built by ``cvenv_setup.py`` from local copies, so that ``sys.prefix`` differs from
  ``sys.base_prefix`` as ``commit_checked.py`` requires.

Every ``before`` entry names this launcher and carries the SHA-256 of this file and of
``launch_v1.py``.
"""

from __future__ import annotations

import importlib.util
import json
import os
import socket
import sys
import threading
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, _HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


v1 = _load("launch_v1")
ROOT = v1.ROOT
CVENV_PY = ROOT / ".cache" / "v0512" / "cvenv" / "Scripts" / "python.exe"
LISTENER = {"port": None, "accepted": []}


def _listen() -> None:
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind(("127.0.0.1", 0))
    srv.listen(16)
    LISTENER["port"] = srv.getsockname()[1]
    LISTENER["socket"] = srv

    def loop() -> None:
        while True:
            try:
                conn, _addr = srv.accept()
            except OSError:
                return
            LISTENER["accepted"].append(time.time())
            conn.close()

    threading.Thread(target=loop, daemon=True).start()


def main() -> int:
    spec_path = next((a for a in sys.argv[1:] if not a.startswith("-")), None)
    if spec_path is None:
        raise SystemExit("usage: launch_v2.py <unit spec> [...]")
    spec = json.loads((ROOT / spec_path).read_text(encoding="utf-8"))
    me = Path(__file__).resolve().relative_to(ROOT).as_posix()
    v1_rel = (_HERE / "launch_v1.py").relative_to(ROOT).as_posix()
    shas = {me: v1.committed_sha256(me), v1_rel: v1.committed_sha256(v1_rel)}
    if spec.get("listener"):
        _listen()
    v1.CPY = CVENV_PY
    original_env = v1.private_env

    def private_env(run_dir: Path) -> dict[str, str]:
        env = original_env(run_dir)
        temp = Path(env["LOCAL" + "APP" + "DATA"]) / "Packages" / v1.CONTAINER / "AC" / "Temp"
        temp.mkdir(parents=True, exist_ok=True)
        env["TEMP"] = env["TMP"] = str(temp)
        env["USERNAME"] = os.environ.get("USERNAME", "")
        if LISTENER["port"] is not None:
            env["REFUTE_LISTENER_PORT"] = str(LISTENER["port"])
        return env

    v1.private_env = private_env
    outer = v1.append_log

    def tagged(entry: dict) -> None:
        entry = dict(entry)
        if entry.get("event") == "before":
            entry["launcher"] = "launch_v2.py"
            entry["identity_sha256"] = {**shas, **entry.get("identity_sha256", {})}
            entry["python"] = CVENV_PY.relative_to(ROOT).as_posix()
            if LISTENER["port"] is not None:
                entry["listener"] = {"host": "127.0.0.1", "outside_the_container": True}
        elif entry.get("event") == "after" and LISTENER["port"] is not None:
            time.sleep(1.0)
            entry["listener_accepted"] = len(LISTENER["accepted"])
        outer(entry)

    v1.append_log = tagged
    return v1.main()


if __name__ == "__main__":
    sys.exit(main())
