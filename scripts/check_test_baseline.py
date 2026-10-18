"""Check a test run against the v0.2.1 baseline of passing tests (ROADMAP.md, v0.2.1, Exit
criteria: "No synthetic test that passes at the start of v0.2.1 fails at its end without a
justification written before.").

The baseline is ``docs/validation/v0.2.1/baseline/v0.2.0-passing-tests.txt``: the pytest
node IDs that pass at tag ``v0.2.0``. The run is a JUnit XML file (``pytest --junitxml``);
counts come from it, never from the console (CLAUDE.md).

Every baseline node ID gets one outcome in the run: ``passed``, ``failed`` (a failure or an
error), ``skipped`` (an xfail counts as skipped: the test no longer passes), or ``missing``
(not in the run: removed, renamed or not collected). Anything but ``passed`` is a
**regression** unless the justifications file names that node ID. The justifications file
has one line per node ID, ``<node id> | <reference>``, where the reference names the
document, committed before the change, that justifies it; blank lines and lines starting
with ``#`` are ignored. Whether each justification was committed *before* the change is
checked with git history, not by this script.

Usage:
    uv run python scripts/check_test_baseline.py <junit.xml> [--baseline <file>]
        [--justifications <file>] [--json <out.json>]

Exit code 0 when there is no unjustified regression, 1 otherwise, 2 on a usage error.
"""

from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASELINE = ROOT / "docs" / "validation" / "v0.2.1" / "baseline" / "v0.2.0-passing-tests.txt"


def read_baseline(path: Path) -> list[str]:
    ids = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    ids = [i for i in ids if i]
    if len(set(ids)) != len(ids):
        raise ValueError(f"duplicate node IDs in {path}")
    return ids


def read_justifications(path: Path | None) -> dict[str, str]:
    if path is None:
        return {}
    out: dict[str, str] = {}
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        node, sep, reference = line.partition("|")
        node, reference = node.strip(), reference.strip()
        if not sep or not node or not reference:
            raise ValueError(f"{path}:{number}: expected '<node id> | <reference>'")
        if node in out:
            raise ValueError(f"{path}:{number}: {node} is justified twice")
        out[node] = reference
    return out


def _case_outcome(case: ET.Element) -> str:
    kinds = {child.tag for child in case}
    if kinds & {"failure", "error"}:
        return "failed"
    if "skipped" in kinds:
        return "skipped"
    return "passed"


def _candidate_ids(classname: str, name: str) -> list[str]:
    """Node IDs a JUnit test case can stand for: the class name is the module path with
    dots, possibly followed by test classes, so every split point is a candidate."""
    parts = [p for p in classname.split(".") if p]
    out = []
    for k in range(len(parts)):
        file = "/".join(parts[: k + 1]) + ".py"
        out.append("::".join([file, *parts[k + 1 :], name]))
    return out


def run_outcomes(junit: Path) -> dict[str, str]:
    """Outcome per node ID candidate; a node ID seen twice keeps its worst outcome."""
    rank = {"passed": 0, "skipped": 1, "failed": 2}
    out: dict[str, str] = {}
    for case in ET.parse(junit).getroot().iter("testcase"):
        outcome = _case_outcome(case)
        for node in _candidate_ids(case.get("classname", ""), case.get("name", "")):
            if node not in out or rank[outcome] > rank[out[node]]:
                out[node] = outcome
    return out


def check(baseline: list[str], outcomes: dict[str, str], justified: dict[str, str]) -> dict:
    per_test = {node: outcomes.get(node, "missing") for node in baseline}
    regressions = [n for n, o in per_test.items() if o != "passed"]
    unjustified = [n for n in regressions if n not in justified]
    unused = sorted(set(justified) - set(regressions))
    totals: dict[str, int] = {}
    for outcome in per_test.values():
        totals[outcome] = totals.get(outcome, 0) + 1
    return {
        "baseline": len(baseline),
        "totals": dict(sorted(totals.items())),
        "regressions": [
            {"node": n, "outcome": per_test[n], "justification": justified.get(n)}
            for n in regressions
        ],
        "unjustified": unjustified,
        "unused_justifications": unused,
        "ok": not unjustified,
    }


def main(argv: list[str]) -> int:
    if not argv or argv[0].startswith("--"):
        print(__doc__)
        return 2
    junit, rest = Path(argv[0]), argv[1:]
    options = {"--baseline": str(BASELINE), "--justifications": None, "--json": None}
    while rest:
        if rest[0] not in options or len(rest) < 2:
            print(__doc__)
            return 2
        options[rest[0]] = rest[1]
        rest = rest[2:]
    if not junit.is_file():
        print(f"no JUnit file at {junit}")
        return 1
    baseline = read_baseline(Path(options["--baseline"]))
    justifications = options["--justifications"]
    justified = read_justifications(Path(justifications) if justifications else None)
    result = check(baseline, run_outcomes(junit), justified)
    totals = " ".join(f"{k}={v}" for k, v in result["totals"].items())
    print(f"baseline={result['baseline']} {totals}")
    for row in result["regressions"]:
        note = f"justified: {row['justification']}" if row["justification"] else "UNJUSTIFIED"
        print(f"{row['outcome']} {row['node']} ({note})")
    for node in result["unused_justifications"]:
        print(f"unused justification: {node}")
    if options["--json"]:
        Path(options["--json"]).write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    print("ok" if result["ok"] else f"unjustified regressions: {len(result['unjustified'])}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
