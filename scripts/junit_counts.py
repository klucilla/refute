"""Print the test counts of a JUnit XML file (pytest --junitxml), and the outcome of every
test whose name contains a given text, with the properties the test recorded
(pytest ``record_property``), so that a passing test can leave its evidence in the CI log.

The house rule (CLAUDE.md) takes test counts from a JUnit file, never from the console
summary; the CI prints them with this script after the test step.

A run that left no JUnit file (or an unreadable one) is reported as incomplete, with no
counts, never invented ones; with --trace, the tests the trace of tests/conftest.py shows
as started and not ended are named (the test that was running when the process ended).
The exit code is then 1.

Usage: python scripts/junit_counts.py <junit.xml> [--trace <trace.txt>] [--show <text>]...
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def counts(path: Path) -> dict[str, int]:
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    total = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    for suite in suites:
        for key in total:
            total[key] += int(suite.get(key, 0))
    return total


def outcomes(path: Path, text: str) -> list[str]:
    out = []
    for case in ET.parse(path).getroot().iter("testcase"):
        name = f"{case.get('classname', '')}::{case.get('name', '')}"
        if text not in name:
            continue
        kinds = [child.tag for child in case if child.tag in ("failure", "error", "skipped")]
        out.append(f"{kinds[0] if kinds else 'passed'} {name}")
        for prop in case.iter("property"):
            out.append(f"    {prop.get('name', '')}={prop.get('value', '')}")
    return out


def unfinished(trace: Path) -> list[str]:
    """The tests the trace shows as started and not ended, in the order they started."""
    open_tests: dict[str, None] = {}
    for line in trace.read_text(encoding="utf-8", errors="replace").splitlines():
        kind, _, nodeid = line.partition(" ")
        if kind == "start":
            open_tests[nodeid] = None
        elif kind == "end":
            open_tests.pop(nodeid, None)
    return list(open_tests)


def incomplete(path: Path, why: str, trace: Path | None) -> int:
    print(f"incomplete run: {why} ({path}); no test counts")
    if trace is None:
        return 1
    if not trace.is_file():
        print(f"no test trace at {trace}")
        return 1
    running = unfinished(trace)
    if running:
        for nodeid in running:
            print(f"started and not ended: {nodeid}")
    else:
        print("every test in the trace ended")
    return 1


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    path, shows, trace = Path(argv[0]), [], None
    rest = argv[1:]
    while rest:
        if rest[0] not in ("--show", "--trace") or len(rest) < 2:
            print(__doc__)
            return 2
        if rest[0] == "--show":
            shows.append(rest[1])
        else:
            trace = Path(rest[1])
        rest = rest[2:]
    if not path.is_file():
        return incomplete(path, "no JUnit file", trace)
    try:
        c = counts(path)
    except ET.ParseError:
        return incomplete(path, "the JUnit file cannot be read", trace)
    print(" ".join(f"{k}={v}" for k, v in c.items()))
    for text in shows:
        for line in outcomes(path, text):
            print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
