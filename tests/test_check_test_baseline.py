"""scripts/check_test_baseline.py: a run is checked against the v0.2.1 baseline of passing
tests; anything but a pass of a baseline test is a regression unless it is justified."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_test_baseline.py"
BASELINE = ROOT / "docs" / "validation" / "v0.2.1" / "baseline" / "v0.2.0-passing-tests.txt"

IDS = [
    "tests/test_a.py::test_one",
    "tests/test_a.py::test_param[2]",
    "tests/test_b.py::TestGroup::test_in_class",
    "tests/test_b.py::test_failing",
    "tests/test_b.py::test_skipped",
    "tests/test_b.py::test_removed",
]

XML = """<?xml version="1.0" encoding="utf-8"?>
<testsuites><testsuite name="pytest" tests="6" failures="1" errors="0" skipped="1">
<testcase classname="tests.test_a" name="test_one"/>
<testcase classname="tests.test_a" name="test_param[2]"/>
<testcase classname="tests.test_b.TestGroup" name="test_in_class"/>
<testcase classname="tests.test_b" name="test_failing"><failure message="x"/></testcase>
<testcase classname="tests.test_b" name="test_skipped"><skipped message="y"/></testcase>
<testcase classname="tests.test_b" name="test_new"/>
</testsuite></testsuites>
"""


def run(*args):
    return subprocess.run(
        [sys.executable, "-I", str(SCRIPT), *args], capture_output=True, text=True, check=False
    )


def write(tmp_path, justifications=None):
    junit = tmp_path / "junit.xml"
    junit.write_text(XML, encoding="utf-8")
    baseline = tmp_path / "baseline.txt"
    baseline.write_text("\n".join(IDS) + "\n", encoding="utf-8")
    args = [str(junit), "--baseline", str(baseline), "--json", str(tmp_path / "out.json")]
    if justifications is not None:
        path = tmp_path / "justified.txt"
        path.write_text(justifications, encoding="utf-8")
        args += ["--justifications", str(path)]
    return args


def test_failed_skipped_and_missing_baseline_tests_are_regressions(tmp_path):
    done = run(*write(tmp_path))
    assert done.returncode == 1, done.stdout + done.stderr
    result = json.loads((tmp_path / "out.json").read_text(encoding="utf-8"))
    assert result["totals"] == {"failed": 1, "missing": 1, "passed": 3, "skipped": 1}
    assert result["unjustified"] == [
        "tests/test_b.py::test_failing",
        "tests/test_b.py::test_skipped",
        "tests/test_b.py::test_removed",
    ]
    assert "UNJUSTIFIED" in done.stdout


def test_justified_regressions_pass_and_unused_justifications_are_listed(tmp_path):
    text = (
        "# reasons written before the change\n"
        "tests/test_b.py::test_failing | docs/x.md, Amendment 1\n"
        "tests/test_b.py::test_skipped | docs/x.md, Amendment 1\n"
        "tests/test_b.py::test_removed | docs/x.md, Amendment 2\n"
        "tests/test_a.py::test_one | docs/x.md, not needed\n"
    )
    done = run(*write(tmp_path, text))
    assert done.returncode == 0, done.stdout + done.stderr
    result = json.loads((tmp_path / "out.json").read_text(encoding="utf-8"))
    assert result["unjustified"] == []
    assert result["unused_justifications"] == ["tests/test_a.py::test_one"]


def test_a_malformed_justification_is_refused(tmp_path):
    done = run(*write(tmp_path, "tests/test_b.py::test_failing\n"))
    assert done.returncode != 0
    assert "expected '<node id> | <reference>'" in done.stderr


def test_a_missing_junit_file_is_not_a_pass(tmp_path):
    done = run(str(tmp_path / "absent.xml"))
    assert done.returncode == 1
    assert "no JUnit file" in done.stdout


def test_the_committed_baseline_has_225_distinct_node_ids():
    ids = [line for line in BASELINE.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(ids) == len(set(ids)) == 225
