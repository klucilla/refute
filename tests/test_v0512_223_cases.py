"""#223's suite (v0.5.12, the charter's step 2): every case of the committed case record
``docs/validation/v0.5.12/step2/cases.json`` on the screen of ``src/``, through the evaluator
shared with the standalone probe (``tests/v0512_case_eval.py``). Exploratory,
``method_status: not_validated``.

- F1's expectations are those of correction 2 revision 1 (adopted at SHA-256 c24e7fd9...); the
  report-only expectations are those of the frozen section 5.
- **Strict expected failures,** only for the failures the case record documented before the
  probe (Codex's round 2, item 3): N07 and N14, F1's reason on the approval code. Each is
  ``xfail(strict=True, raises=AssertionError)``; any other failure raises ``RuntimeError``, which
  the marker does not accept. The ``src/`` change removes both markers.
- The repeated probe (``step2/probe-result-2.json``) passed with exactly these two failures.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v0512_case_eval as ev  # noqa: E402

DOC = ev.load()
BY_ID = {c["id"]: c for c in DOC["cases"]}
UNREACHABLE = {"B07", "B18", "B19", "B23"}  # proofs in cases.json; issue #225; not tested
XFAIL = {
    "N07": "approval code: a constant baseline gives sigma_w = 0 and _pink returns None "
    "(line 245); correction 2 revision 1: s2 = 0, noise unavailable",
    "N14": "approval code: sigma_w rounds to 0 and _pink returns None (line 245); correction 2 "
    "revision 1: both variances round to 0, the denominator is not positive",
}


def _param(case):
    marks = []
    if case["id"] in XFAIL:
        marks.append(
            pytest.mark.xfail(strict=True, raises=AssertionError, reason=XFAIL[case["id"]])
        )
    return pytest.param(case, id=case["id"], marks=marks)


@pytest.mark.parametrize("case", [_param(c) for c in DOC["cases"]])
def test_case(case):
    outcomes = ev.evaluate(case, BY_ID)
    assert outcomes, "a case with no assertion"
    failed = [o for o in outcomes if not o["ok"]]
    undocumented = [o for o in failed if not ev.documented_match(case, o)]
    if undocumented:
        raise RuntimeError(f"undocumented failures: {undocumented}")
    assert not failed, failed


def test_every_reachable_branch_has_a_case():
    import json

    inv = json.loads((ev.CASES.parent / "inventory.json").read_text(encoding="utf-8"))
    ids = {b["id"] for b in inv["branches"]}
    covered = {b for c in DOC["cases"] for b in c["branches"]}
    assert ids - UNREACHABLE <= covered, sorted(ids - UNREACHABLE - covered)


def test_both_parities_of_the_parity_templates_are_witnessed():
    reasons = {c["expect"].get("F1", {}).get("reason") for c in DOC["cases"]}
    for p in ("odd", "even"):
        assert f"too few in-transit points for the {p} parity" in reasons
        assert f"depth or pink noise unavailable for the {p} parity" in reasons


def test_each_report_only_record_has_a_computed_witness_with_values():
    seen = set()
    for c in DOC["cases"]:
        for name, exp in c["expect"].items():
            if isinstance(exp, dict) and exp.get("state") == "computed" and exp.get("values"):
                seen.add(name)
    assert {"F1_trap", "F2", "F3", "F4", "U1"} <= seen


def test_the_documented_failures_are_those_of_the_case_record():
    documented = {c["id"] for c in DOC["cases"] if c["documented"]}
    assert documented == set(XFAIL)
