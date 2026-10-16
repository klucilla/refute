"""Print the test counts of a JUnit XML file (pytest --junitxml), and the outcome of every
test whose name contains a given text, with the properties the test recorded
(pytest ``record_property``), so that a passing test can leave its evidence in the CI log.

The house rule (CLAUDE.md) takes test counts from a JUnit file, never from the console
summary; the CI prints them with this script after the test step.

Usage: python scripts/junit_counts.py <junit.xml> [--show <text>]...
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


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    path, shows = Path(argv[0]), []
    rest = argv[1:]
    while rest:
        if rest[0] != "--show" or len(rest) < 2:
            print(__doc__)
            return 2
        shows.append(rest[1])
        rest = rest[2:]
    c = counts(path)
    print(" ".join(f"{k}={v}" for k, v in c.items()))
    for text in shows:
        for line in outcomes(path, text):
            print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
