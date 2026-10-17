"""scripts/junit_counts.py: the CI prints test counts from a JUnit file (CLAUDE.md)."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "junit_counts.py"

XML = """<?xml version="1.0" encoding="utf-8"?>
<testsuites><testsuite name="pytest" tests="4" failures="1" errors="0" skipped="1">
<testcase classname="tests.test_a" name="test_one"/>
<testcase classname="tests.test_a" name="test_two"><failure message="x"/></testcase>
<testcase classname="tests.test_vm_jea_integration" name="test_three">
<skipped message="y"/></testcase>
<testcase classname="tests.test_vm_jea_integration" name="test_four">
<properties><property name="evidence" value="{&quot;a&quot;: 1}"/></properties></testcase>
</testsuite></testsuites>
"""


def run(*args):
    return subprocess.run(
        [sys.executable, "-I", str(SCRIPT), *args], capture_output=True, text=True, check=False
    )


def test_counts_and_outcomes(tmp_path):
    path = tmp_path / "junit.xml"
    path.write_text(XML, encoding="utf-8")
    out = run(str(path), "--show", "test_vm_jea_integration")
    assert out.returncode == 0
    assert out.stdout.splitlines() == [
        "tests=4 failures=1 errors=0 skipped=1",
        "skipped tests.test_vm_jea_integration::test_three",
        "passed tests.test_vm_jea_integration::test_four",
        '    evidence={"a": 1}',
    ]


def test_usage_errors(tmp_path):
    assert run().returncode == 2
    assert run(str(tmp_path / "x.xml"), "--show").returncode == 2
    assert run(str(tmp_path / "x.xml"), "--trace").returncode == 2


def test_a_missing_junit_file_is_an_incomplete_run_with_no_counts(tmp_path):
    out = run(str(tmp_path / "junit.xml"))
    assert out.returncode == 1
    assert out.stdout.startswith("incomplete run: no JUnit file")
    assert "tests=" not in out.stdout


def test_an_unreadable_junit_file_is_an_incomplete_run(tmp_path):
    path = tmp_path / "junit.xml"
    path.write_text("<testsuites><testsuite", encoding="utf-8")
    out = run(str(path))
    assert out.returncode == 1
    assert out.stdout.startswith("incomplete run: the JUnit file cannot be read")
    assert "tests=" not in out.stdout


def test_the_trace_names_the_test_that_was_running(tmp_path):
    trace = tmp_path / "trace.txt"
    trace.write_text(
        "start tests/test_a.py::test_one\n"
        "end tests/test_a.py::test_one\n"
        "start tests/test_a.py::test_two[x y]\n",
        encoding="utf-8",
    )
    out = run(str(tmp_path / "junit.xml"), "--trace", str(trace))
    assert out.returncode == 1
    assert out.stdout.splitlines()[1:] == ["started and not ended: tests/test_a.py::test_two[x y]"]
    missing = run(str(tmp_path / "junit.xml"), "--trace", str(tmp_path / "none.txt"))
    assert missing.returncode == 1 and "no test trace at" in missing.stdout


def test_a_complete_run_with_a_trace_prints_the_counts(tmp_path):
    path = tmp_path / "junit.xml"
    path.write_text(XML, encoding="utf-8")
    out = run(str(path), "--trace", str(tmp_path / "trace.txt"))
    assert out.returncode == 0
    assert out.stdout.splitlines() == ["tests=4 failures=1 errors=0 skipped=1"]


def test_the_conftest_hooks_write_the_trace(tmp_path, monkeypatch):
    """The hooks of tests/conftest.py append a start and an end line, which the script
    reads back; without REFUTE_TEST_TRACE they write nothing."""
    import conftest

    trace = tmp_path / "new" / "trace.txt"
    monkeypatch.setattr(conftest, "TRACE", str(trace))
    # the session creates the folder and starts an empty trace
    conftest.pytest_sessionstart(None)
    assert trace.read_text(encoding="utf-8") == ""
    conftest.pytest_runtest_logstart("tests/test_a.py::test_one", ("tests/test_a.py", 1, ""))
    conftest.pytest_runtest_logfinish("tests/test_a.py::test_one", ("tests/test_a.py", 1, ""))
    conftest.pytest_runtest_logstart("tests/test_a.py::test_two", ("tests/test_a.py", 5, ""))
    assert trace.read_text(encoding="utf-8").splitlines() == [
        "start tests/test_a.py::test_one",
        "end tests/test_a.py::test_one",
        "start tests/test_a.py::test_two",
    ]
    out = run(str(tmp_path / "junit.xml"), "--trace", str(trace))
    assert "started and not ended: tests/test_a.py::test_two" in out.stdout
    monkeypatch.setattr(conftest, "TRACE", "")
    conftest.pytest_runtest_logstart("tests/test_a.py::test_three", ("tests/test_a.py", 9, ""))
    assert "test_three" not in trace.read_text(encoding="utf-8")
