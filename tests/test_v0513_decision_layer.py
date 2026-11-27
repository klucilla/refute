"""The decision-layer extractor of v0.5.13 (amendment 2, revision 6, section 4), on synthetic
source snippets only. It opens no golden file and reads no source of the project."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "v0513_decision_layer", ROOT / "docs/validation/v0.5.13/tools/decision_layer.py"
)
dl = importlib.util.module_from_spec(spec)
sys.modules["v0513_decision_layer"] = dl
spec.loader.exec_module(dl)

SOURCE = """
import math


def entry(d):
    return check(d)


def check(d):
    attenuated = math.isfinite(d.s) and d.a + 3 * d.s < 0.5 * d.depth
    if d.n < 3:
        return TestResult(status=TestStatus.INCONCLUSIVE)
    mask = d.t > 0.2
    y = d.f[mask]
    can_fail = attenuated and d.k > 1
    if can_fail:
        return TestResult(status=TestStatus.FAIL)
    if other(d):
        return TestResult(status=TestStatus.FAIL)
    if d.kind == "eb":
        return TestResult(status=TestStatus.FAIL)
    return TestResult(status=TestStatus.PASS, metrics={"eligible": d.e >= 2, "v": d.x * (d.y > 1)})


def other(d):
    return d.q > 5


def unreachable(d):
    if d.z > 1:
        return TestResult()
"""


def _rows():
    out = dl.analyze({"mod.py": SOURCE}, entries=[("mod.py", "entry")])
    return out, {r["expression"]: r for r in out["rows"]}


def test_reachability_by_name():
    out, _ = _rows()
    assert "mod.py:unreachable" not in out["reachable"]
    assert {"mod.py:entry", "mod.py:check", "mod.py:other"} <= set(out["reachable"])


def test_named_boolean_chain_and_finiteness():
    _, rows = _rows()
    assert rows["math.isfinite(d.s)"]["kind"] == "finiteness"
    assert rows["d.a + 3 * d.s < 0.5 * d.depth"]["kind"] == "numeric"
    assert rows["d.k > 1"]["kind"] == "numeric"


def test_branch_with_a_sink_and_its_guards():
    _, rows = _rows()
    assert "branch test" in rows["d.n < 3"]["contexts"]
    assert rows["d.n < 3"]["guards"] == []


def test_returned_decision_of_a_called_function():
    out, rows = _rows()
    assert "mod.py:other" in out["returning"]
    assert "returned decision" in rows["d.q > 5"]["contexts"]


def test_serialized_flag_and_non_numeric():
    _, rows = _rows()
    assert "serialized flag" in rows["d.e >= 2"]["contexts"]
    assert rows['d.kind == "eb"']["kind"] == "non-numeric"


def test_selection_arithmetic_and_unreachable_are_left_out():
    _, rows = _rows()
    assert "d.t > 0.2" not in rows
    assert "d.y > 1" not in rows
    assert "d.z > 1" not in rows


def test_bare_flags_used_as_truth_values_are_non_numeric_rows():
    _, rows = _rows()
    assert rows["can_fail"]["kind"] == "non-numeric"
    assert rows["can_fail"]["operators"] == ["name"]
    assert rows["other(d)"]["operators"] == ["call"]
    assert "mask" not in rows


def test_a_mutated_decision_list_is_an_effect():
    src = "def entry(xs, t):\n    flagged = []\n    for x in xs:\n        if x.s > t:\n"
    src += "            flagged.append(x)\n"
    src += "    return TestResult(status=TestStatus.FAIL if flagged else None)\n"
    out = dl.analyze({"m.py": src}, entries=[("m.py", "entry")])
    assert "x.s > t" in {r["expression"] for r in out["rows"]}


def test_calls_resolve_through_imports():
    sources = {
        "src/a.py": "from b import check\n\ndef entry(d):\n    return check(d)\n",
        "src/b.py": "def check(d):\n    if d.x > 1:\n        return TestResult()\n",
        "src/c.py": "def check(d):\n    if d.y > 1:\n        return TestResult()\n",
    }
    out = dl.analyze(sources, entries=[("src/a.py", "entry")])
    exprs = {r["expression"] for r in out["rows"]}
    assert "d.x > 1" in exprs
    assert "d.y > 1" not in exprs


def test_configuration_guards_prune_per_version():
    src = (
        "def entry(plan, d):\n"
        "    if plan.is_v051:\n"
        "        return new(d)\n"
        "    if d.a > 2:\n"
        "        return TestResult()\n"
        "    return old(d)\n\n"
        "def new(d):\n    if d.n > 1:\n        return TestResult()\n\n"
        "def old(d):\n    if d.o > 1:\n        return TestResult()\n"
    )
    v1 = dl.analyze({"m.py": src}, entries=[("m.py", "entry")], version="v1")
    v3 = dl.analyze({"m.py": src}, entries=[("m.py", "entry")], version="v3")
    rows1 = {r["expression"] for r in v1["rows"]}
    rows3 = {r["expression"] for r in v3["rows"]}
    assert "d.n > 1" not in rows1 and "d.o > 1" in rows1
    assert "d.n > 1" in rows3
    assert dl.guard_value(dl.ast.parse("plan.v05 and x", mode="eval").body, "v1") is False
    assert dl.guard_value(dl.ast.parse("plan.v05 and x", mode="eval").body, "v2") is None


def test_early_exits_are_recorded():
    _, rows = _rows()
    exits = rows["d.k > 1"]["early_exits_before"]
    assert any("d.n < 3" in e for e in exits)
