"""scripts/run_tests_affinity.ps1 takes -Junit and -Out relative to the project root or
absolute (issue #59; Codex review of the previews of 2026-10-17): before, an absolute
-Junit was joined to the root and GetFullPath failed.

Each case runs the script on a one-test file in tmp_path. The script pins the process to
threads 8 to 31 (mask 0xFFFFFF00), so it runs only on Windows with at least 32 logical
CPUs (the maintainer's machine), and is skipped elsewhere, the CI runners included."""

import os
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "run_tests_affinity.ps1"

pytestmark = pytest.mark.skipif(
    sys.platform != "win32" or (os.cpu_count() or 0) < 32,
    reason="the script runs on Windows and pins threads 8 to 31",
)


def _run(tmp_path: Path, *args: str) -> subprocess.CompletedProcess:
    probe = tmp_path / "test_probe.py"
    probe.write_text("def test_probe():\n    assert True\n", encoding="utf-8")
    command = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(SCRIPT),
        *args,
        "-Tests",
        str(probe),
    ]
    return subprocess.run(command, capture_output=True, text=True, timeout=300)


def test_an_absolute_junit_path_and_the_output_next_to_it(tmp_path):
    junit = tmp_path / "abs" / "junit.xml"
    done = _run(tmp_path, "-Junit", str(junit))
    assert "pytest exit=0" in done.stdout, done.stdout + done.stderr
    assert junit.is_file()
    assert (tmp_path / "abs" / "junit.out.txt").is_file()


def test_an_absolute_out_path(tmp_path):
    junit = tmp_path / "junit.xml"
    out = tmp_path / "elsewhere" / "out.txt"
    done = _run(tmp_path, "-Junit", str(junit), "-Out", str(out))
    assert "pytest exit=0" in done.stdout, done.stdout + done.stderr
    assert junit.is_file() and out.is_file()


def test_a_relative_junit_path_is_taken_from_the_project_root(tmp_path):
    relative = f".cache/test-run-tests-affinity/{uuid.uuid4().hex}/junit.xml"
    done = _run(tmp_path, "-Junit", relative)
    assert "pytest exit=0" in done.stdout, done.stdout + done.stderr
    assert (ROOT / relative).is_file()
    assert (ROOT / relative).with_suffix(".out.txt").is_file()
