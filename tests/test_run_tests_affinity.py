"""scripts/run_tests_affinity.ps1 takes -Junit and -Out relative to the project root or
absolute (issue #59; Codex review of the previews of 2026-10-17): before, an absolute
-Junit was joined to the root and GetFullPath failed.

Each case runs the script, from a working directory outside the project, on a one-test
file in tmp_path, and checks the exit code, that the JUnit file records exactly that one
passing test, and where the output and the error output went. The script pins the process
to threads 8 to 31 (mask 0xFFFFFF00), so it runs only on Windows with at least 32 logical
CPUs (the maintainer's machine), and is skipped elsewhere, the CI runners included."""

import os
import subprocess
import sys
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "run_tests_affinity.ps1"

pytestmark = pytest.mark.skipif(
    sys.platform != "win32" or (os.cpu_count() or 0) < 32,
    reason="the script runs on Windows and pins threads 8 to 31",
)


def _run(
    tmp_path: Path, *args: str, body: str = "    assert True\n"
) -> subprocess.CompletedProcess:
    probe = tmp_path / "test_probe.py"
    probe.write_text("def test_probe():\n" + body, encoding="utf-8")
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
    return subprocess.run(command, capture_output=True, text=True, timeout=300, cwd=tmp_path)


def _check(done: subprocess.CompletedProcess, junit: Path, out: Path) -> None:
    text = done.stdout + done.stderr
    assert done.returncode == 0, text
    assert "pytest exit=0" in done.stdout, text
    root = ET.parse(junit).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    keys = ("tests", "failures", "errors", "skipped")
    counts = {k: sum(int(s.get(k, 0)) for s in suites) for k in keys}
    assert counts == {"tests": 1, "failures": 0, "errors": 0, "skipped": 0}, counts
    assert [c.get("name") for c in root.iter("testcase")] == ["test_probe"]
    assert out.is_file()
    assert out.with_suffix(".err.txt").is_file()


def test_an_absolute_junit_path_and_the_output_next_to_it(tmp_path):
    junit = tmp_path / "abs" / "junit.xml"
    done = _run(tmp_path, "-Junit", str(junit))
    _check(done, junit, tmp_path / "abs" / "junit.out.txt")


def test_an_absolute_out_path(tmp_path):
    junit = tmp_path / "junit.xml"
    out = tmp_path / "elsewhere" / "out.txt"
    done = _run(tmp_path, "-Junit", str(junit), "-Out", str(out))
    _check(done, junit, out)


def test_a_relative_junit_path_is_taken_from_the_project_root(tmp_path):
    relative = f".cache/test-run-tests-affinity/{uuid.uuid4().hex}/junit.xml"
    done = _run(tmp_path, "-Junit", relative)
    _check(done, ROOT / relative, (ROOT / relative).with_suffix(".out.txt"))


def test_another_thread_range_and_a_worker_count(tmp_path):
    # -Threads 0-7 pins the run to 8 logical processors and -Workers 6 sets REFUTE_WORKERS
    # (the v0.2.1 range while v0.3 runs on 8 to 31); the probe checks both from inside.
    junit = tmp_path / "junit.xml"
    body = (
        "    import os\n"
        "    from refute.core.runner import default_workers, usable_cpus\n"
        "    assert usable_cpus() == 8\n"
        "    assert os.environ['REFUTE_WORKERS'] == '6'\n"
        "    assert default_workers() == 6\n"
    )
    done = _run(tmp_path, "-Junit", str(junit), "-Threads", "0-7", "-Workers", "6", body=body)
    _check(done, junit, tmp_path / "junit.out.txt")


def test_the_default_range_is_8_to_31(tmp_path):
    junit = tmp_path / "junit.xml"
    body = "    from refute.core.runner import usable_cpus\n    assert usable_cpus() == 24\n"
    done = _run(tmp_path, "-Junit", str(junit), body=body)
    _check(done, junit, tmp_path / "junit.out.txt")


def test_a_thread_range_outside_the_machine_is_refused(tmp_path):
    done = _run(tmp_path, "-Junit", str(tmp_path / "junit.xml"), "-Threads", "0-4096")
    assert done.returncode != 0
    assert "pytest exit=" not in done.stdout


def test_a_relative_out_path_is_taken_from_the_project_root(tmp_path):
    junit = tmp_path / "junit.xml"
    relative = f".cache/test-run-tests-affinity/{uuid.uuid4().hex}/out.txt"
    done = _run(tmp_path, "-Junit", str(junit), "-Out", relative)
    _check(done, junit, ROOT / relative)
    assert not (tmp_path / relative).exists()
