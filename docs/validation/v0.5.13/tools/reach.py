"""The reach rule of the decision layer (the maintainer's decisions N1 and O1, #218 comments
7224847166 and the block of 2026-11-27 (11)), from source only. It opens no golden file.

    unit reach:  {python} -I -B docs/validation/v0.5.13/tools/reach.py <out.json>

It classifies every candidate row of every fixture (``decision_layer.py``) before the freeze, as
**reached-if** (with the evidence conditions that prove its reach) or **reach unknown** (with the
reason). After the freeze, the margin check evaluates each condition on that fixture's serialized
non-numeric output only; a row is *reached* when one of its alternatives holds in full, *not
reached* when the output proves every alternative false, and *reach unknown* otherwise. A row
that is not reached gets no margin check and is not counted as assessed; a reach-unknown row is
not assessed and is counted among the declared limits (N1(b), N1(c)).

**The conditions** (each reads one serialized non-numeric field of the fixture's output):
- ``output-ok``: the fixture's output file is not an ``ERROR`` text (``verdict-<v>.txt`` for a
  verdict fixture, with ``error-<v>.json`` for the error entry; ``chain-<v>.json`` for a chain
  fixture);
- ``candidate-present`` / ``candidate-null``: the ``candidate`` field of that output is an object
  / is ``null`` (``pipeline.build_result``, ``discover/measure.chain``).

**Executed functions.** A fixture's entry functions are executed under ``output-ok``. A function
is executed when an executed function calls it at an **unconditional position** and the call
resolves to that one function (``decision_layer.Resolver``; a call with several or no targets
proves nothing). A position in a function is unconditional when, inside that function:
1. it is not inside a ``for``, ``while``, comprehension or generator (the loop rule, below);
2. it is not inside a ``try`` block or an ``except`` handler;
3. (no condition on ``and``/``or``: section 4 of revision 6 splits a conjunction or disjunction
   into its comparisons, each a row, and its own example, ``attenuated``, is a second conjunct;
   N1 decides on statements and exits, not on the order operands are evaluated);
4. every enclosing ``if`` or conditional expression is either a configuration guard of
   ``decision_layer.GUARD_TABLE`` or of ``LOCAL_GUARDS`` that is true for the fixture, or the guard
   ``candidate is None`` / ``candidate is not None`` in ``CANDIDATE_FUNCS``, which adds the
   condition ``candidate-null`` or ``candidate-present``;
5. no ``return``, ``raise``, ``break`` or ``continue`` of the function comes before it in the
   source, unless that exit is in a branch that a configuration guard rules out for the fixture,
   or in the branch of the opposite candidate condition.

**Rows.** A row is reached-if when its function is executed and the row is at an unconditional
position; its alternatives are the function's alternatives with the row's own conditions added.
Every other row is reach unknown, with the first reason met.

**The loop rule (O1).** A row inside a loop body, a comprehension or a generator is reach unknown
in every fixture. Its instances cannot be told apart by a serialized status or code, so none is
evaluated, and the row counts once per fixture among the declared limits.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
spec = importlib.util.spec_from_file_location(
    "decision_layer", Path(__file__).with_name("decision_layer.py")
)
dl = importlib.util.module_from_spec(spec)
sys.modules["decision_layer"] = dl
spec.loader.exec_module(dl)

INVENTORY = "docs/validation/v0.5.13/i2/predicate-inventory.json"
CANDIDATE_FUNCS = {
    "src/refute/packs/tess/pipeline.py:attack_candidate",
    "src/refute/packs/tess/pipeline.py:build_result",
    "src/refute/packs/tess/discover/measure.py:chain",
    # called with the search's final candidate (pipeline.py:271) or with None when the search
    # found none (pipeline.py:215): its ``candidate`` is None exactly when the serialized one is
    "src/refute/packs/tess/gauntlet.py:check_snr",
}
# Configuration guards on a local name, scoped to one function. ``noise`` is None unless
# ``gp.corrections.active`` (pipeline.py:259-263), which is false in every fixture.
LOCAL_GUARDS = {
    ("src/refute/packs/tess/pipeline.py:attack_candidate", "noise is None"): set(dl.VERSIONS),
    ("src/refute/packs/tess/pipeline.py:attack_candidate", "noise is not None"): set(),
}


def guard(f, test: ast.AST, version: str) -> bool | None:
    """A configuration guard's value in ``version``: the global table, or a scoped local one."""
    v = dl.guard_value(test, version)
    if v is None and (f.key, ast.unparse(test)) in LOCAL_GUARDS:
        return version in LOCAL_GUARDS[(f.key, ast.unparse(test))]
    return v


CANDIDATE_GUARDS = {
    "candidate is None": "candidate-null",
    "candidate is not None": "candidate-present",
}
OPPOSITE = {"candidate-null": "candidate-present", "candidate-present": "candidate-null"}
LOOPS = (
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.ListComp,
    ast.SetComp,
    ast.DictComp,
    ast.GeneratorExp,
)
EXITS = (ast.Return, ast.Raise, ast.Break, ast.Continue)


def _branch(p: ast.AST, child: ast.AST) -> bool | None:
    body = p.body if isinstance(p.body, list) else [p.body]
    orelse = p.orelse if isinstance(p.orelse, list) else [p.orelse]
    if any(child is b for b in body):
        return True
    if any(child is b for b in orelse):
        return False
    return None


def position(f, node, version: str) -> tuple[str, object]:
    """('ok', conditions), ('pruned', guard) or ('unknown', reason), for ``node`` in ``f``."""
    parents = dl._parents(f)
    conds: set[str] = set()
    child = node
    while child in parents and child is not f.node:
        p = parents[child]
        if isinstance(p, LOOPS) and not (isinstance(p, ast.For | ast.AsyncFor) and child is p.iter):
            if not (isinstance(p, ast.While) and child is p.test):
                return "unknown", "inside a loop (the loop rule)"
        if isinstance(p, ast.comprehension) and child is not p.iter:
            return "unknown", "inside a loop (the loop rule)"
        if isinstance(p, ast.Try | ast.ExceptHandler):
            return "unknown", "inside a try block or handler"
        if isinstance(p, ast.If | ast.IfExp):
            branch = _branch(p, child)
            if branch is not None:
                v = guard(f, p.test, version)
                text = ast.unparse(p.test)
                if v is not None:
                    if v != branch:
                        return "pruned", ("" if branch else "not ") + text
                elif f.key in CANDIDATE_FUNCS and text in CANDIDATE_GUARDS:
                    c = CANDIDATE_GUARDS[text]
                    conds.add(c if branch else OPPOSITE[c])
                else:
                    return "unknown", f"under a data guard: {text}"
        child = p
    exits = sorted(
        (e for e in f.walk() if isinstance(e, EXITS)), key=lambda e: (e.lineno, e.col_offset)
    )
    for e in exits:
        if (e.lineno, e.col_offset) >= (node.lineno, node.col_offset):
            break
        if any(a is e for a in ast.walk(node)):
            continue
        status, other = position_no_exits(f, e, version)
        if status == "pruned":
            continue
        if status == "ok" and any(OPPOSITE[c] in conds for c in other):
            continue
        if status == "ok" and len(other) == 1 and _only_candidate_guard(f, e, version):
            # past an exit taken only when the candidate is null (or only when present), the
            # rest of the function runs only under the opposite condition
            conds.add(OPPOSITE[next(iter(other))])
            continue
        return "unknown", f"after an exit at line {e.lineno}"
    return "ok", conds


def _only_candidate_guard(f, node, version) -> bool:
    """Whether every enclosing guard of ``node`` is either a configuration guard true for the
    fixture or the candidate guard (no data guard, loop or handler), so that the exit is taken
    exactly under its candidate condition."""
    parents = dl._parents(f)
    child = node
    while child in parents and child is not f.node:
        p = parents[child]
        if isinstance(p, (*LOOPS, ast.Try, ast.ExceptHandler, ast.BoolOp)):
            return False
        if isinstance(p, ast.If | ast.IfExp) and _branch(p, child) is not None:
            text = ast.unparse(p.test)
            v = guard(f, p.test, version)
            if v is None and not (f.key in CANDIDATE_FUNCS and text in CANDIDATE_GUARDS):
                return False
        child = p
    return True


def position_no_exits(f, node, version):
    """The guard part of ``position`` only (for an exit statement)."""
    parents = dl._parents(f)
    conds: set[str] = set()
    child = node
    while child in parents and child is not f.node:
        p = parents[child]
        if isinstance(p, ast.If | ast.IfExp):
            branch = _branch(p, child)
            if branch is not None:
                v = guard(f, p.test, version)
                text = ast.unparse(p.test)
                if v is not None and v != branch:
                    return "pruned", text
                if v is None and f.key in CANDIDATE_FUNCS and text in CANDIDATE_GUARDS:
                    c = CANDIDATE_GUARDS[text]
                    conds.add(c if branch else OPPOSITE[c])
        child = p
    return "ok", conds


def executed(funcs, resolver, entries, version):
    """Function key -> list of alternative condition sets under which it is proven executed."""
    by_key = {f.key: f for f in funcs}
    alts: dict[str, list[frozenset]] = {}
    queue = [(f"{rel}:{qual}", frozenset({"output-ok"})) for rel, qual in entries]
    while queue:
        key, conds = queue.pop()
        if key not in by_key:
            continue
        known = alts.setdefault(key, [])
        if any(k <= conds for k in known):
            continue
        known.append(conds)
        f = by_key[key]
        for n in f.walk():
            if not isinstance(n, ast.Call):
                continue
            targets = resolver.resolve(f, n.func)
            if len(targets) != 1:
                continue
            status, extra = position(f, n, version)
            if status == "ok":
                queue.append((targets[0].key, conds | frozenset(extra)))
    return alts


def classify(sources, version, kind):
    entries = [e for e in dl.ENTRIES if (e[1] == "chain") == (kind == "chain")]
    part = dl.analyze(sources, entries, version)
    funcs = dl.collect_functions(sources)
    resolver = dl.Resolver(sources, funcs)
    by_key = {f.key: f for f in funcs}
    alts = executed(funcs, resolver, entries, version)
    rows = []
    for r in part["rows"]:
        key = f"{r['file']}:{r['function']}"
        f = by_key[key]
        node = next(
            n for n in f.walk() if getattr(n, "lineno", None) == r["line"]
            and getattr(n, "col_offset", None) == r["col"]
        )  # fmt: skip
        out = {k: r[k] for k in ("file", "line", "col", "function", "expression", "kind")}
        if key not in alts:
            out.update({"reach": "unknown", "reason": "its function is not proven executed"})
        else:
            status, extra = position(f, node, version)
            if status == "ok":
                out.update({"reach": "reached-if", "alternatives": sorted(
                    sorted(a | frozenset(extra)) for a in alts[key])})  # fmt: skip
            elif status == "pruned":
                out.update({"reach": "not on this fixture", "reason": f"pruned by {extra}"})
            else:
                out.update({"reach": "unknown", "reason": extra})
        rows.append(out)
    return rows


def main() -> int:
    inv = json.loads((ROOT / INVENTORY).read_text(encoding="utf-8"))
    sources = {rel: (ROOT / rel).read_text(encoding="utf-8") for rel in inv["module_files"]}
    fixtures, summary = {}, {}
    for v in dl.VERSIONS:
        for kind, label in (("verdict", v), ("chain", f"chain-{v}")):
            rows = classify(sources, v, kind)
            fixtures[label] = rows
            counts: dict[str, int] = {}
            for r in rows:
                bucket = (
                    r["reach"]
                    if r["reach"] != "unknown"
                    else "unknown: " + r["reason"].split(":")[0]
                )
                counts[f"{bucket} / {r['kind']}"] = counts.get(f"{bucket} / {r['kind']}", 0) + 1
            summary[label] = dict(sorted(counts.items()))
    out = {"rule": "see the tool's docstring", "summary": summary, "fixtures": fixtures}
    Path(sys.argv[1]).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
