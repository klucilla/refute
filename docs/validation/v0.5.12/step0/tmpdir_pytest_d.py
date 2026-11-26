"""The temporary-folder fixture's part (ii) again, once, through the subst drive (option (d) of the
maintainer's decision of #218 comment 7191720023, item 3). ``tmpdir_fixture.py`` is not edited
(rule (c)).

Run in the AppContainer with the cvenv (its sitecustomize installed). It reads the letter from
``step0/subst.json`` and runs the minimal pytest case ``tmpdir_case.py`` by the path
``<letter>:\\docs\\validation\\v0.5.12\\step0\\tmpdir_case.py``, with ``<letter>:\\`` as the
working folder. The folder above every test-file folder is then the drive's root, the project
itself. It passes only if the JUnit XML counts 1 test, 0 failures, 0 errors and 0 skipped. The
record ``tmpdir-pytest-d.json`` goes to the run's out folder (copied to ``step0/``); the JUnit
file stays in the run folder, with its SHA-256 and counts in the record.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> int:
    letter = json.loads((HERE / "subst.json").read_text(encoding="utf-8"))["letter"]
    drive = f"{letter}:\\"
    case = drive + "docs\\validation\\v0.5.12\\step0\\tmpdir_case.py"
    out = Path(os.environ["REFUTE_RUN_OUT"])
    junit = out / "tmpdir-pytest-d.xml"
    argv = [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider"]
    argv += [f"--junitxml={junit}", case]
    run = subprocess.run(argv, capture_output=True, text=True, cwd=drive)
    counts = {"tests": None}
    if junit.exists():
        cases = list(ET.parse(junit).getroot().iter("testcase"))
        counts = {
            "tests": len(cases),
            "failures": sum(c.find("failure") is not None for c in cases),
            "errors": sum(c.find("error") is not None for c in cases),
            "skipped": sum(c.find("skipped") is not None for c in cases),
        }
    ok = counts == {"tests": 1, "failures": 0, "errors": 0, "skipped": 0}
    junit_sha = hashlib.sha256(junit.read_bytes()).hexdigest() if junit.exists() else None
    doc = {
        "schema": "refute-v0512-tmpdir-pytest-d-1",
        "decision": "#218 comment 7191720023, item 3",
        "letter": letter,
        "case_path": case,
        "exit_code": run.returncode,
        "junit": counts,
        "junit_sha256": junit_sha,
        "junit_note": "the JUnit file stays in the run folder (it names the machine); its "
        "SHA-256 and counts are here",
        "output_tail": (run.stdout + run.stderr)[-800:],
        "passed": ok,
    }
    (out / "tmpdir-pytest-d.json").write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"passed": ok, "junit": counts}))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
