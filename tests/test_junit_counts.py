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
