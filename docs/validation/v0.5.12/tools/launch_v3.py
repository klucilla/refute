"""The metered launcher of v0.5.12, version 3: charter amendment 1 (approved by the maintainer's
decision of 2026-11-26, #218 comment 7193450494, at bb6292c).

    .venv/Scripts/python.exe -I -B docs/validation/v0.5.12/tools/launch_v3.py <unit spec>
        [--label L] [--approval URL] [-- extra arguments]

It runs ``launch_v1.py`` unchanged (rule (c)), with one change: **every unit without network
runs OUTSIDE the AppContainer**, still in the launcher's job object, so the CPU of the whole
process tree and the phase-wide disk bound still hold.
- ``{python}`` is the project's ``.venv`` interpreter.
- The unit's environment is this launcher's own, with ``UV_OFFLINE=1`` and ``REFUTE_RUN_OUT`` (the
  run's out folder) added. The pytest units carry ``--disable-socket`` in their argv.
- The network block across the process tree no longer applies to these units: a declared limit
  of exit criterion 6, which stays not met (amendment 1, item b).
- Units with network (GitHub operations, reviewers) run as before.

Every ``before`` entry names this launcher, says how the unit ran, and carries the SHA-256 of this
file and of ``launch_v1.py``.
"""

from __future__ import annotations

import importlib.util
import os
import sys
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
AMENDMENT = "docs/plans/v0.5.12-charter-amendment-1.md"
SANDBOX = "job outside the AppContainer (amendment 1); UV_OFFLINE=1"


def main() -> int:
    me = Path(__file__).resolve().relative_to(ROOT).as_posix()
    v1_rel = (_HERE / "launch_v1.py").relative_to(ROOT).as_posix()
    shas = {me: v1.committed_sha256(me), v1_rel: v1.committed_sha256(v1_rel)}
    shas[AMENDMENT] = v1.committed_sha256(AMENDMENT)
    v1.CPY = v1.VENV_PY

    def host_env(run_dir: Path) -> dict[str, str]:
        out = run_dir / "out"
        out.mkdir(parents=True, exist_ok=True)
        env = dict(os.environ)
        env["UV_OFFLINE"] = "1"
        env["REFUTE_RUN_OUT"] = str(out)
        return env

    v1.private_env = host_env
    original_run = v1.jobrun.run

    def run(*args, **kwargs):
        kwargs["container"] = None
        return original_run(*args, **kwargs)

    v1.jobrun.run = run
    outer = v1.append_log

    def tagged(entry: dict) -> None:
        entry = dict(entry)
        if entry.get("event") == "before":
            entry["launcher"] = "launch_v3.py"
            entry["identity_sha256"] = {**shas, **entry.get("identity_sha256", {})}
            if entry.get("network") is False:
                entry["sandbox"] = SANDBOX
        outer(entry)

    v1.append_log = tagged
    return v1.main()


if __name__ == "__main__":
    sys.exit(main())
