"""Exit criterion 6 of v0.5: reproduce one C3 dossier in a clean clone from its generated
instructions alone (docs/plans/v0.5-plan.md, section 5; the dossier is the one drawn for the
stratum eb-fp-inconclusive, calibration/v0.5/reviews/RULE.md).

The script runs, literally and in order, the commands of the ``bash`` block of the dossier's
``REPRODUCE.md``; the only substitution is the one the file asks for (``<this dossier>`` by the
dossier's absolute path). ``cd`` changes the working folder of the next commands. Nothing is
placed by hand: no cache, no catalog, no environment variable of the project's own checkout
(``VIRTUAL_ENV`` and ``UV_PROJECT_ENVIRONMENT`` are removed from the environment). Each
command's exit code, start and end (UTC) and output are logged. The run stops at the first
command that fails; its log says which.

Usage, from the repository root:
``.venv/Scripts/python.exe calibration/v0.5/reviews/reproduce_c6.py <dossier> <work-folder>``
(``<work-folder>`` must not exist; it must be inside ``.cache/``).
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


def now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def commands(reproduce: str) -> list[str]:
    lines = reproduce.splitlines()
    start = lines.index("```bash") + 1
    end = lines.index("```", start)
    return [line.strip() for line in lines[start:end] if line.strip()]


def main(argv: list[str]) -> int:
    dossier = Path(argv[0]).resolve()
    work = Path(argv[1])
    cache = (Path.cwd() / ".cache").resolve()
    if not work.resolve().is_relative_to(cache) or work.exists():
        raise SystemExit(f"{work} must be a new folder inside .cache/")
    work.mkdir(parents=True)
    work = work.resolve()
    steps = commands((dossier / "REPRODUCE.md").read_text(encoding="utf-8"))
    env = {
        k: v for k, v in os.environ.items() if k not in ("VIRTUAL_ENV", "UV_PROJECT_ENVIRONMENT")
    }
    cwd = work
    log = []
    code = 0
    for line in steps:
        line = line.replace("<this dossier>", dossier.as_posix())
        argv_ = shlex.split(line, posix=True)
        entry = {"command": line, "cwd": cwd.relative_to(work).as_posix() or ".", "start": now()}
        if argv_[0] == "cd":
            cwd = (cwd / argv_[1]).resolve()
            entry.update(end=now(), exit=0)
            log.append(entry)
            continue
        out = work / f"step-{len(log) + 1:02d}.log"
        with open(out, "w", encoding="utf-8") as handle:
            proc = subprocess.run(argv_, cwd=cwd, env=env, stdout=handle, stderr=subprocess.STDOUT)
        entry.update(end=now(), exit=proc.returncode, log=out.name)
        log.append(entry)
        if proc.returncode != 0:
            code = proc.returncode
            break
    record = {"dossier": dossier.name, "steps": log, "result": "PASS" if code == 0 else "FAIL"}
    (work / "reproduce.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
