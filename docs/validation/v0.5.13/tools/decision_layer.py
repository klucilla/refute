"""The candidate predicates of the decision layer, from source only (v0.5.13, the maintainer's
decisions L4(a) and M3, #218 comments 7223634913 and 7224251159). It opens no golden file.

    unit decision-layer:  {python} -I -B docs/validation/v0.5.13/tools/decision_layer.py <out.json>

It applies the first paragraph of section 4 of amendment 2, revision 6, mechanically, and
**includes when in doubt**: a missing predicate voids the margin result, an extra one costs a
recorded reason. Its output is a working list for the manifest, not the manifest.

**Scope.** The modules are the 73 files of I2's inventory. A function is *reachable* when a chain
of calls, resolved by name, leads to it from the golden path's entry points (``ENTRIES``, the calls
of ``tests/baseline_code_v0511.py::_compute``). A call ``f(...)`` or ``x.f(...)`` is resolved to
every function named ``f`` in the modules (over-inclusive on purpose).

**Sinks** (a serialized test status, class, eligibility flag, reason code or verdict):
- a call of ``TestResult``, ``_inconclusive``, ``_not_run`` or ``not_applicable_block``;
- a reference to ``TestStatus.<x>``;
- an assignment to a name, attribute or string subscript in ``DECISION_NAMES``.

A function that holds a sink is a **decision function**.

**Decision contexts** (where a boolean reaches a sink):
1. the test of an ``if``, ``elif``, conditional expression or ``while`` whose branch (at any depth,
   not into nested functions) holds a sink, a ``return``, ``break``, ``continue`` or ``raise``
   in a decision function, or an assignment to a decision variable;
2. the value assigned to a decision variable or to a name in ``DECISION_NAMES``;
3. the value of a ``return`` in a decision function, or in a function whose call sits in a
   decision context (a *returning decision function*);
4. an argument of a sink call, and a value of a dict literal given to a sink call or assigned to
   a name in ``CONTAINERS`` (a serialized flag).

Inside a decision context the walk goes through ``and``/``or``/``not``, the test of a conditional
expression, ``bool``, ``any``, ``all`` and a generator or comprehension's element (inclusive for
``any``/``all``). It **collects** every comparison and every call of ``isfinite``/``isnan``/
``isinf`` (each one a candidate row), marks every name it meets as a decision variable of its
function, and every function it calls as a returning decision function. It **stops**, recording
the reason, at arithmetic (``BinOp``), at a subscript (selection by index or mask), and at any
other call. The whole is repeated until nothing changes.

**Each row** gives the file, line, function, the comparison as written, its operators, a kind
(``numeric``: an ordering ``<``, ``<=``, ``>``, ``>=``, or ``==``/``!=`` with a numeric operand;
``finiteness``; ``non-numeric``: identity, membership, string or enum equality, or anything
else), the contexts that reached it, and the tests of the ``if`` statements that enclose it in
its function (its guards, to count rows behind a data-dependent early exit).

**Cross-checks** printed: J1's 173 atoms found or not; whether every row is an I2 site; whether
the named sites ``battery_v52.py:338-340`` (``attenuated``) and functions of ``power``, ``a0``,
``a0_v4`` and ``core/inconclusive`` appear.
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
INVENTORY = "docs/validation/v0.5.13/i2/predicate-inventory.json"
J1 = "docs/validation/v0.5.13/j1/decision-count.json"
ENTRIES = [
    ("src/refute/packs/tess/pipeline.py", "analyze_data"),
    ("src/refute/packs/tess/pipeline.py", "build_result"),
    ("src/refute/packs/tess/pipeline.py", "TessAnalyzer.error_result"),
    ("src/refute/packs/tess/discover/measure.py", "chain"),
    ("src/refute/packs/tess/report.py", "render_report"),
]
SINK_CALLS = {"TestResult", "_inconclusive", "_not_run", "not_applicable_block"}
DECISION_NAMES = {
    "status", "verdict", "inconclusive_class", "reason", "eligible", "can_fail", "fail_allowed",
    "flagged", "decisive", "failing", "passed", "verdict_reason", "gate_passed",
    "inconclusive_condition", "inconclusive_detail", "state",
}  # fmt: skip
CONTAINERS = {"metrics", "inputs", "sensitivity"}
PASS_CALLS = {"bool", "any", "all"}
ATOM_CALLS = {"isfinite", "isnan", "isinf"}
ORDER = (ast.Lt, ast.LtE, ast.Gt, ast.GtE)


def _name(func: ast.AST) -> str | None:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


class Func:
    def __init__(self, rel: str, qual: str, node: ast.AST, text: str):
        self.rel, self.qual, self.node, self.text = rel, qual, node, text
        self.key = f"{rel}:{qual}"
        self.short = qual.rsplit(".", 1)[-1]
        self.dvars: set[str] = set()
        self.returning = False
        self.calls: set[str] = set()

    def walk(self):
        """The nodes of this function, not of the functions nested in it."""
        stack = list(ast.iter_child_nodes(self.node))
        while stack:
            n = stack.pop()
            yield n
            if not isinstance(
                n, ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda | ast.ClassDef
            ):
                stack.extend(ast.iter_child_nodes(n))


def collect_functions(sources: dict[str, str]) -> list[Func]:
    funcs = []
    for rel, text in sources.items():
        tree = ast.parse(text)

        def visit(node, prefix, rel=rel, text=text):
            for child in ast.iter_child_nodes(node):
                if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
                    qual = f"{prefix}{child.name}"
                    funcs.append(Func(rel, qual, child, text))
                    visit(child, qual + ".", rel, text)
                elif isinstance(child, ast.ClassDef):
                    visit(child, f"{prefix}{child.name}.", rel, text)

        visit(tree, "")
    return funcs


def is_sink(node: ast.AST) -> bool:
    if isinstance(node, ast.Call) and _name(node.func) in SINK_CALLS:
        return True
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
        return node.value.id == "TestStatus"
    if isinstance(node, ast.Assign | ast.AnnAssign | ast.AugAssign):
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        return any(_target_name(t) in DECISION_NAMES for t in targets)
    return False


def _target_name(t: ast.AST) -> str | None:
    if isinstance(t, ast.Name):
        return t.id
    if isinstance(t, ast.Attribute):
        return t.attr
    if isinstance(t, ast.Subscript) and isinstance(t.slice, ast.Constant):
        return t.slice.value if isinstance(t.slice.value, str) else None
    return None


def _branch_nodes(stmts):
    stack = list(stmts)
    while stack:
        n = stack.pop()
        yield n
        if not isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda | ast.ClassDef):
            stack.extend(ast.iter_child_nodes(n))


def analyze(sources: dict[str, str], entries=ENTRIES) -> dict:
    funcs = collect_functions(sources)
    by_short: dict[str, list[Func]] = {}
    for f in funcs:
        by_short.setdefault(f.short, []).append(f)
        for n in f.walk():
            if isinstance(n, ast.Call) and _name(n.func):
                f.calls.add(_name(n.func))
    # reachability by name
    reach: set[str] = set()
    todo = [f for f in funcs if (f.rel, f.qual) in set(entries)]
    while todo:
        f = todo.pop()
        if f.key in reach:
            continue
        reach.add(f.key)
        for c in f.calls:
            todo += [g for g in by_short.get(c, []) if g.key not in reach]
    live = [f for f in funcs if f.key in reach]
    deciding = {f.key for f in live if any(is_sink(n) for n in f.walk())}
    rows: dict[tuple, dict] = {}
    stops: dict[str, int] = {}
    returning: set[str] = set()

    def walk_ctx(f: Func, expr: ast.AST, ctx: str) -> bool:
        """Walk a decision context; True when it changed the state."""
        changed = False
        stack = [expr]
        while stack:
            n = stack.pop()
            if isinstance(n, ast.BoolOp):
                stack += n.values
            elif isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.Not):
                stack.append(n.operand)
            elif isinstance(n, ast.IfExp):
                stack += [n.test, n.body, n.orelse]
            elif isinstance(n, ast.Compare):
                key = (f.rel, n.lineno, n.col_offset)
                if key not in rows:
                    rows[key] = {"file": f.rel, "line": n.lineno, "end_line": n.end_lineno,
                                 "function": f.qual, "expression": _src(f.text, n),
                                 "operators": [type(o).__name__ for o in n.ops],
                                 "kind": _kind(n), "contexts": set(),
                                 "node": n, "func": f}  # fmt: skip
                    changed = True
                rows[key]["contexts"].add(ctx)
            elif isinstance(n, ast.Call):
                name = _name(n.func)
                if name in PASS_CALLS:
                    stack += n.args
                elif name in ATOM_CALLS:
                    key = (f.rel, n.lineno, n.col_offset)
                    if key not in rows:
                        rows[key] = {"file": f.rel, "line": n.lineno, "end_line": n.end_lineno,
                                     "function": f.qual, "expression": _src(f.text, n),
                                     "operators": [name], "kind": "finiteness",
                                     "contexts": set(), "node": n, "func": f}  # fmt: skip
                        changed = True
                    rows[key]["contexts"].add(ctx)
                else:
                    for g in by_short.get(name or "", []):
                        if g.key in reach and g.key not in returning:
                            returning.add(g.key)
                            changed = True
                    stops["call"] = stops.get("call", 0) + 1
            elif isinstance(n, ast.GeneratorExp | ast.ListComp | ast.SetComp):
                stack.append(n.elt)
            elif isinstance(n, ast.Name):
                if n.id not in f.dvars:
                    f.dvars.add(n.id)
                    changed = True
            elif isinstance(n, ast.BinOp):
                stops["arithmetic"] = stops.get("arithmetic", 0) + 1
            elif isinstance(n, ast.Subscript):
                stops["subscript"] = stops.get("subscript", 0) + 1
            elif isinstance(n, ast.Attribute | ast.Constant):
                pass
            else:
                stops[type(n).__name__] = stops.get(type(n).__name__, 0) + 1
        return changed

    def effect(f: Func, stmts) -> bool:
        dec = f.key in deciding or f.key in returning
        for n in _branch_nodes(stmts):
            if is_sink(n):
                return True
            if dec and isinstance(n, ast.Return | ast.Break | ast.Continue | ast.Raise):
                return True
            if isinstance(n, ast.Assign | ast.AugAssign | ast.AnnAssign):
                targets = n.targets if isinstance(n, ast.Assign) else [n.target]
                if any(isinstance(t, ast.Name) and t.id in f.dvars for t in targets):
                    return True
        return False

    changed = True
    while changed:
        changed = False
        for f in live:
            dec = f.key in deciding or f.key in returning
            for n in f.walk():
                if isinstance(n, ast.If | ast.While) and effect(f, n.body + n.orelse):
                    changed |= walk_ctx(f, n.test, "branch test")
                elif isinstance(n, ast.IfExp) and effect(f, [n.body, n.orelse]):
                    changed |= walk_ctx(f, n.test, "conditional expression")
                elif isinstance(n, ast.Assign | ast.AnnAssign | ast.AugAssign) and n.value:
                    targets = n.targets if isinstance(n, ast.Assign) else [n.target]
                    names = [_target_name(t) for t in targets]
                    if any(x in DECISION_NAMES or x in f.dvars for x in names if x):
                        changed |= walk_ctx(f, n.value, "assignment to a decision variable")
                    if any(isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name)
                           and t.value.id in CONTAINERS for t in targets):  # fmt: skip
                        if _boolish(n.value):
                            changed |= walk_ctx(f, n.value, "serialized flag")
                    if any(isinstance(t, ast.Name) and t.id in CONTAINERS for t in targets):
                        for v in _dict_values(n.value):
                            if _boolish(v):
                                changed |= walk_ctx(f, v, "serialized flag")
                elif isinstance(n, ast.Return) and n.value is not None and dec:
                    changed |= walk_ctx(f, n.value, "returned decision")
                elif isinstance(n, ast.Call) and _name(n.func) in SINK_CALLS:
                    for a in list(n.args) + [k.value for k in n.keywords]:
                        if _boolish(a):
                            changed |= walk_ctx(f, a, "sink argument")
                        for v in _dict_values(a):
                            if _boolish(v):
                                changed |= walk_ctx(f, v, "serialized flag")
    out_rows = []
    for row in sorted(rows.values(), key=lambda r: (r["file"], r["line"], r["node"].col_offset)):
        f, node = row.pop("func"), row.pop("node")
        row["contexts"] = sorted(row["contexts"])
        row["guards"] = _guards(f, node)
        row["early_exits_before"] = _early_exits(f, node)
        out_rows.append(row)
    return {
        "functions": len(funcs),
        "reachable": sorted(reach),
        "deciding": sorted(deciding),
        "returning": sorted(returning),
        "stops": dict(sorted(stops.items())),
        "rows": out_rows,
    }


def _boolish(n: ast.AST) -> bool:
    if isinstance(n, ast.Compare | ast.BoolOp):
        return True
    if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.Not):
        return True
    if isinstance(n, ast.Call) and _name(n.func) in PASS_CALLS | ATOM_CALLS:
        return True
    return isinstance(n, ast.IfExp) and _boolish(n.test)


def _dict_values(n: ast.AST) -> list[ast.AST]:
    if isinstance(n, ast.Dict):
        return list(n.values)
    if isinstance(n, ast.Call) and _name(n.func) == "dict":
        return [k.value for k in n.keywords]
    return []


def _kind(n: ast.Compare) -> str:
    ops = n.ops
    if any(isinstance(o, ast.Is | ast.IsNot | ast.In | ast.NotIn) for o in ops):
        return "non-numeric"
    if all(isinstance(o, ORDER) for o in ops):
        return "numeric"
    operands = [n.left, *n.comparators]
    if any(isinstance(x, ast.Constant) and isinstance(x.value, str) for x in operands):
        return "non-numeric"
    if any(isinstance(x, ast.Attribute) and isinstance(x.value, ast.Name)
           and x.value.id[:1].isupper() for x in operands):  # fmt: skip
        return "non-numeric"
    if any(isinstance(o, ORDER) for o in ops):
        return "numeric"
    if any(isinstance(x, ast.Constant) and isinstance(x.value, int | float)
           and not isinstance(x.value, bool) for x in operands):  # fmt: skip
        return "numeric"
    return "non-numeric"


def _src(text: str, node: ast.AST) -> str:
    return " ".join((ast.get_source_segment(text, node) or ast.unparse(node)).split())


def _guards(f: Func, target: ast.AST) -> list[str]:
    """The tests of the ``if`` statements of ``f`` that enclose ``target``, outermost first
    (``not (...)`` for an ``else`` branch)."""
    parents = {}
    for n in ast.walk(f.node):
        for c in ast.iter_child_nodes(n):
            parents[c] = n
    out, child = [], target
    while child in parents and child is not f.node:
        p = parents[child]
        if isinstance(p, ast.If):
            test = _src(f.text, p.test)
            if child in p.body:
                out.append(test)
            elif child in p.orelse:
                out.append(f"not ({test})")
        child = p
    return list(reversed(out))


def _early_exits(f: Func, target: ast.AST) -> list[str]:
    """The tests of the ``if`` statements of ``f`` that end before ``target`` begins and whose
    branch returns or raises: a data-dependent exit may keep ``target`` from running."""
    out = []
    for n in f.walk():
        if isinstance(n, ast.If) and n.end_lineno < target.lineno:
            if any(isinstance(s, ast.Return | ast.Raise) for s in _branch_nodes(n.body + n.orelse)):
                out.append(f"{n.lineno}: {_src(f.text, n.test)}")
    return sorted(out, key=lambda s: int(s.split(":")[0]))


def main() -> int:
    inv = json.loads((ROOT / INVENTORY).read_text(encoding="utf-8"))
    sources = {rel: (ROOT / rel).read_text(encoding="utf-8") for rel in inv["module_files"]}
    result = analyze(sources)
    rows = result["rows"]
    i2 = {(r["file"], r["line"]) for r in inv["rows"]}
    not_i2 = [f"{r['file']}:{r['line']}" for r in rows if (r["file"], r["line"]) not in i2]
    j1 = json.loads((ROOT / J1).read_text(encoding="utf-8"))["rows"]
    lines = {(r["file"], ln) for r in rows for ln in range(r["line"], r["end_line"] + 1)}
    j1_missing = [
        f"{a['file']}:{a['line']} {a['atom']}" for a in j1 if (a["file"], a["line"]) not in lines
    ]
    named = {
        "battery_v52.py:338-340 (attenuated)": any(
            r["file"].endswith("battery_v52.py") and 338 <= r["line"] <= 340 for r in rows
        ),
    }
    for mod in ("power.py", "a0.py", "a0_v4.py", "core/inconclusive.py"):
        named[mod] = sum(1 for r in rows if r["file"].endswith(mod))
    kinds: dict[str, int] = {}
    for r in rows:
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
    guarded = sum(1 for r in rows if r["guards"])
    behind_exit = sum(1 for r in rows if r["early_exits_before"])
    summary = {
        "functions": result["functions"],
        "reachable": len(result["reachable"]),
        "deciding": len(result["deciding"]),
        "returning": len(result["returning"]),
        "rows": len(rows),
        "kinds": kinds,
        "rows_with_guards": guarded,
        "rows_behind_an_early_exit": behind_exit,
        "rows_not_i2_sites": len(not_i2),
        "j1_atoms": len(j1),
        "j1_atoms_not_found": len(j1_missing),
        "named": named,
        "stops": result["stops"],
    }
    out = {"rule": "see the tool's docstring", "summary": summary, "j1_missing": j1_missing,
           "rows_not_i2_sites": not_i2, **result}  # fmt: skip
    Path(sys.argv[1]).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
