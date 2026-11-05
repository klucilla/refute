"""The v0.5 acceptance rows, counted from a JUnit XML file (the first gate review's finding M1,
2026-11-05, #199).

The one acceptance run (2026-11-03, `acceptance.py`, README.md) recorded each of its 133 rows in
`acceptance-run.json` with a result: PASS, FAIL or INVALID. This module turns each recorded row
into one pytest case so that the counts come from a JUnit XML file, as exit criterion 1 asks: a
PASS row passes, a FAIL row fails (with its rule), an INVALID row is skipped (with its reason).
It **re-counts the recorded outcomes; it does not run the acceptance again** (a rerun of the
acceptance seeds is not allowed).

It lives outside `tests/` on purpose: its FAIL rows fail, and the suite (`testpaths = ["tests"]`)
must not collect it. Run it alone, from the repository root:
``powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_tests_affinity.ps1
-Junit <out.xml> -Tests docs/validation/v0.5/acceptance/acceptance_rows_junit.py``
Expected counts: 133 tests, 11 failures, 3 skipped (119 passed).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

RUN = Path(__file__).resolve().parent / "acceptance-run.json"
RESULTS = json.loads(RUN.read_text(encoding="utf-8"))["results"]


@pytest.mark.parametrize("row", sorted(RESULTS))
def test_acceptance_row(row: str) -> None:
    entry = RESULTS[row]
    result = entry["result"]
    if result == "PASS":
        return
    if result == "INVALID":
        pytest.skip(f"INVALID: {entry.get('rule', '')}")
    if result == "FAIL":
        pytest.fail(f"FAIL: {entry.get('rule', '')}")
    raise AssertionError(f"unknown recorded result {result!r}")
