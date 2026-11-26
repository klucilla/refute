"""The temporary-folder fixture (v0.5.12, step 0; the maintainer's decision of #218 comment
7190662570, item 2), run once in the AppContainer with the cvenv's interpreter, after the
sitecustomize is installed. It must show, inside the container:

- **(i)** ``tempfile.mkdtemp``: a write, a read (also from a child process, which writes a second
  file there, as ``tests/baseline_code_v0511.py`` does), and the folder's removal;
- **(ii)** a minimal pytest test with ``tmp_path`` (``tmpdir_case.py``), passing, counted from its
  JUnit XML file (1 test, 0 failures, 0 errors, 0 skipped);
- **(iii)** the ACL of a folder made by ``tempfile.mkdtemp``: its entries must be exactly those of
  this interpreter's ``os.mkdir(0o700)`` ACL, read from the DLL,
  ``D:P(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)(A;OICI;FA;;;OW)``, plus one entry for the container's
  SID, and no other SID.

The record ``tmpdir-fixture.json`` goes to the run's out folder (copied to ``step0/``). Exit code 0
only if every part holds.
"""

from __future__ import annotations

import ctypes
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from ctypes import wintypes
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE_ACES = {"(A;OICI;FA;;;SY)", "(A;OICI;FA;;;BA)", "(A;OICI;FA;;;OW)"}


def dacl_sddl(path: str) -> str:
    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    advapi32.GetNamedSecurityInfoW.argtypes = [
        ctypes.c_wchar_p,
        ctypes.c_int,
        wintypes.DWORD,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
    ]
    advapi32.ConvertSecurityDescriptorToStringSecurityDescriptorW.argtypes = [
        ctypes.c_void_p,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.c_void_p,
        ctypes.c_void_p,
    ]
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    psd = ctypes.c_void_p()
    rc = advapi32.GetNamedSecurityInfoW(path, 1, 4, None, None, None, None, ctypes.byref(psd))
    if rc != 0:
        raise OSError(rc, "GetNamedSecurityInfoW failed")
    s = ctypes.c_wchar_p()
    ok = advapi32.ConvertSecurityDescriptorToStringSecurityDescriptorW(
        psd, 1, 4, ctypes.byref(s), None
    )
    kernel32.LocalFree(psd)
    if not ok:
        raise ctypes.WinError(ctypes.get_last_error())
    text = s.value
    kernel32.LocalFree(ctypes.cast(s, ctypes.c_void_p))
    return text


def main() -> int:
    doc = {"schema": "refute-v0512-tmpdir-fixture-1", "decision": "#218 comment 7190662570"}
    sid = getattr(os, "refute_v0512_container_sid", None)
    doc["sitecustomize_active"] = sid is not None
    doc["container_sid"] = sid
    parts = {}

    # (i) mkdtemp, write, read, a child's write, removal
    try:
        d = tempfile.mkdtemp()
        p = Path(d) / "a.txt"
        p.write_text("one", encoding="utf-8")
        read_back = p.read_text(encoding="utf-8") == "one"
        code = "import pathlib, sys; pathlib.Path(sys.argv[1], 'b.txt').write_text('two')"
        child = subprocess.run([sys.executable, "-I", "-B", "-c", code, d], capture_output=True)
        child_ok = child.returncode == 0 and (Path(d) / "b.txt").read_text() == "two"
        sddl = dacl_sddl(d)
        shutil.rmtree(d)
        parts["i"] = {
            "write_read": read_back,
            "child_write_read": child_ok,
            "removed": not Path(d).exists(),
        }
        parts["i"]["holds"] = all(parts["i"].values())
    except OSError as exc:
        sddl = None
        parts["i"] = {"holds": False, "error": f"{type(exc).__name__}: {exc}"}

    # (ii) a minimal pytest test with tmp_path, counted from its JUnit XML file
    junit = Path(os.environ["REFUTE_RUN_OUT"]) / "tmpdir-pytest.xml"
    argv = [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider"]
    argv += [f"--junitxml={junit}", str(HERE / "tmpdir_case.py")]
    run = subprocess.run(argv, capture_output=True, text=True, cwd=str(HERE))
    counts = {"tests": None}
    if junit.exists():
        root = ET.parse(junit).getroot()
        cases = list(root.iter("testcase"))
        counts = {
            "tests": len(cases),
            "failures": sum(c.find("failure") is not None for c in cases),
            "errors": sum(c.find("error") is not None for c in cases),
            "skipped": sum(c.find("skipped") is not None for c in cases),
        }
    holds = counts == {"tests": 1, "failures": 0, "errors": 0, "skipped": 0}
    parts["ii"] = {"exit_code": run.returncode, "junit": counts, "holds": holds}
    parts["ii"]["output_tail"] = (run.stdout + run.stderr)[-800:]

    # (iii) the ACL: exactly the interpreter's 0o700 entries plus the container's SID
    aces = set(re.findall(r"\([^()]*\)", sddl or ""))
    expected = BASE_ACES | ({f"(A;OICI;FA;;;{sid})"} if sid else set())
    parts["iii"] = {
        "sddl": sddl,
        "protected": bool(sddl and sddl.startswith("D:P")),
        "extra_aces": sorted(aces - expected),
        "missing_aces": sorted(expected - aces),
    }
    parts["iii"]["holds"] = bool(
        sid and parts["iii"]["protected"] and aces == expected and len(aces) == 4
    )
    doc["parts"] = parts
    doc["passed"] = all(v["holds"] for v in parts.values()) and doc["sitecustomize_active"]
    out = Path(os.environ["REFUTE_RUN_OUT"]) / "tmpdir-fixture.json"
    out.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"passed": doc["passed"], **{k: v["holds"] for k, v in parts.items()}}))
    return 0 if doc["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
