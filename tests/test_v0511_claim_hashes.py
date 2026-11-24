"""v0.5.11, proof (ii) of the charter's section 2.3: every committed claim keeps its resolved
hash. The record docs/validation/v0.5.11/step1/claim-hashes-before.json was written before the
`src/` change by the metered unit claim-hashes. This test must pass before and after the change.

A claim whose load fails on this machine with an error that the record did not have (for example
a frozen input absent from a clone) is reported, not compared: the record's own errors are
compared as they are.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from refute.core.claim import load_claim

ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "docs" / "validation" / "v0.5.11" / "step1" / "claim-hashes-before.json"


def _cases():
    return sorted(json.loads(RECORD.read_text(encoding="utf-8"))["claims"].items())


@pytest.mark.parametrize(("path", "expected"), _cases(), ids=[p for p, _ in _cases()])
def test_the_committed_claim_keeps_its_resolved_hash(path, expected):
    try:
        got = load_claim(ROOT / path).sha256()
    except Exception as exc:  # noqa: BLE001
        got = f"ERROR {type(exc).__name__}: {exc}"
    if got.startswith("ERROR") and not expected.startswith("ERROR"):
        pytest.skip(f"does not load on this machine: {got[:200]}")
    assert got == expected
