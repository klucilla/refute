"""The reach rule of v0.5.13's decision layer (N1, O1), on synthetic source snippets only. It
opens no golden file and reads no source of the project."""

from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "v0513_reach", ROOT / "docs/validation/v0.5.13/tools/reach.py"
)
reach = importlib.util.module_from_spec(spec)
sys.modules["v0513_reach"] = reach
spec.loader.exec_module(reach)
dl = reach.dl

PIPE = "src/refute/packs/tess/pipeline.py"
SRC = """
def attack_candidate(plan, candidate, d):
    if candidate is None:
        return TestResult()
    if plan.is_v051:
        newer(d)
    else:
        older(d)
    for e in d.events:
        if e.x > 1:
            return TestResult()
    if d.y > 2 and d.z < 3:
        return TestResult()
    if d.w > 4:
        return TestResult()
    return TestResult()


def newer(d):
    if d.n > 1:
        return TestResult()


def older(d):
    if d.o > 1:
        return TestResult()
"""


def _func(qual):
    funcs = dl.collect_functions({PIPE: SRC})
    return next(f for f in funcs if f.qual == qual), funcs


def _compare(f, text):
    return next(n for n in f.walk() if isinstance(n, ast.Compare) and ast.unparse(n) == text)


def test_loop_rule():
    f, _ = _func("attack_candidate")
    assert reach.position(f, _compare(f, "e.x > 1"), "v3") == (
        "unknown",
        "inside a loop (the loop rule)",
    )


def test_candidate_guard_adds_a_condition_and_exits_follow():
    f, _ = _func("attack_candidate")
    status, conds = reach.position(f, _compare(f, "d.y > 2"), "v3")
    assert status == "unknown" and "exit" in conds
    status, conds = reach.position(f, _compare(f, "candidate is None"), "v3")
    assert status == "ok" and conds == set()


def test_no_short_circuit_condition_and_a_second_conjunct_shares_its_statement():
    f, _ = _func("attack_candidate")
    first = reach.position(f, _compare(f, "d.y > 2"), "v3")
    second = reach.position(f, _compare(f, "d.z < 3"), "v3")
    assert first == second


def test_scoped_local_guard():
    src = (
        "def attack_candidate(gp, final, d):\n"
        "    noise = None\n"
        "    if gp.corrections.active:\n"
        "        noise = make(d)\n"
        "    if noise is None:\n"
        "        x = d.a > 1\n"
    )
    f = next(g for g in dl.collect_functions({PIPE: src}) if g.qual == "attack_candidate")
    node = next(n for n in f.walk() if isinstance(n, ast.Compare) and ast.unparse(n) == "d.a > 1")
    assert reach.position(f, node, "v1") == ("ok", set())


def test_configuration_guard_and_execution_chain():
    f, funcs = _func("attack_candidate")
    resolver = dl.Resolver({PIPE: SRC}, funcs)
    alts3 = reach.executed(funcs, resolver, [(PIPE, "attack_candidate")], "v3")
    alts1 = reach.executed(funcs, resolver, [(PIPE, "attack_candidate")], "v1")
    assert f"{PIPE}:newer" in alts3 and f"{PIPE}:older" not in alts3
    assert f"{PIPE}:older" in alts1 and f"{PIPE}:newer" not in alts1
    assert alts3[f"{PIPE}:newer"] == [frozenset({"output-ok", "candidate-present"})]
