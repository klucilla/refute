"""Build v0.5.12's container virtual environment from local copies only (charter, step 0; approved
by the maintainer's decision of #218 comment 7174740316, item 1 c).

    launch_v1 unit setup-cvenv: {python} -I -B docs/validation/v0.5.12/tools/cvenv_setup.py

It runs in the AppContainer, with the interpreter copy ``.cache/v0512/cpy``, and creates
``.cache/v0512/cvenv``:
- ``pyvenv.cfg``: the project's ``.venv/pyvenv.cfg``, its ``home`` line pointing to the copy;
- ``Scripts/python.exe``: the virtual-environment launcher, copied from ``.venv/Scripts``;
- ``Scripts/ruff.exe``: copied from ``.venv/Scripts``;
- ``Lib/site-packages/_refute_venv.pth``: copied from the interpreter copy's ``site-packages``,
  where ``container_setup.py`` wrote it at ``e95bd86``. It is one line that adds the project's
  ``.venv`` site-packages, so the packages and the ``refute`` editable install are the project's
  own; the ``.pth`` files of ``.venv`` are then read in place.

Every copied file's SHA-256 is checked against its source. Nothing is downloaded or installed, and
no external cache is read: every source is inside the project. It then starts the new interpreter
as a child, in the same container, and checks that ``sys.prefix`` differs from
``sys.base_prefix`` and that ``refute``, ``numpy`` and ``ruff`` resolve. The record is
``cvenv.json`` in the run's out folder; the launcher copies it to ``docs/validation/v0.5.12/``.
Any failure exits 1, and the work stops (the decision's item 1 c).
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
CPY = ROOT / ".cache" / "v0512" / "cpy"
CVENV = ROOT / ".cache" / "v0512" / "cvenv"
VENV = ROOT / ".venv"
PROBE = (
    "import sys, json, importlib.util as u; "
    "print(json.dumps({'prefix_differs': sys.prefix != sys.base_prefix, "
    "'refute': bool(u.find_spec('refute')), 'numpy': bool(u.find_spec('numpy')), "
    "'ruff': bool(u.find_spec('ruff')), 'version': sys.version.split()[0]}))"
)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def copy(src: Path, dst: Path) -> dict:
    if ROOT not in src.resolve().parents:
        raise SystemExit(f"refused: {src} is outside the project")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    a, b = sha(src), sha(dst)
    if a != b:
        raise SystemExit(f"refused: the copy of {src.name} does not match")
    rel = src.relative_to(ROOT).as_posix()
    return {"source": rel, "destination": dst.relative_to(ROOT).as_posix(), "sha256": a}


def main() -> int:
    if CVENV.exists():
        raise SystemExit(f"refused: {CVENV} exists already")
    copies = [
        copy(VENV / "Scripts" / "python.exe", CVENV / "Scripts" / "python.exe"),
        copy(VENV / "Scripts" / "ruff.exe", CVENV / "Scripts" / "ruff.exe"),
        copy(
            CPY / "Lib" / "site-packages" / "_refute_venv.pth",
            CVENV / "Lib" / "site-packages" / "_refute_venv.pth",
        ),
    ]
    lines = []
    for line in (VENV / "pyvenv.cfg").read_text(encoding="utf-8").splitlines():
        key = line.split("=", 1)[0].strip()
        lines.append(f"home = {CPY}" if key == "home" else line)
    (CVENV / "pyvenv.cfg").write_text("\n".join(lines) + "\n", encoding="utf-8")
    py = CVENV / "Scripts" / "python.exe"
    probe = subprocess.run([str(py), "-I", "-B", "-c", PROBE], capture_output=True, text=True)
    result = json.loads(probe.stdout.strip() or "{}")
    ok = probe.returncode == 0 and all(
        result.get(k) for k in ("prefix_differs", "refute", "numpy", "ruff")
    )
    doc = {
        "schema": "refute-v0512-cvenv-1",
        "decision": "#218 comment 7174740316, item 1 c",
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "copies": copies,
        "pyvenv_cfg_sha256": sha(CVENV / "pyvenv.cfg"),
        "home": CPY.relative_to(ROOT).as_posix(),
        "probe": result,
        "probe_stderr_tail": probe.stderr[-500:],
        "downloads": "none: every source is inside the project",
        "passed": ok,
    }
    out = Path(os.environ["REFUTE_RUN_OUT"]) / "cvenv.json"
    out.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"passed": ok, "probe": result}))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
