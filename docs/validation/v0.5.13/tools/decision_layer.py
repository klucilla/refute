"""The candidate predicates of the decision layer, from source only (v0.5.13, the maintainer's
decisions L4(a) and M3, #218 comments 7223634913 and 7224251159). It opens no golden file.

    unit decision-layer:  {python} -I -B docs/validation/v0.5.13/tools/decision_layer.py <out.json>

It applies the first paragraph of section 4 of amendment 2, revision 6, mechanically, and
**includes when in doubt**: a missing predicate voids the margin result, an extra one costs a
recorded reason. Its output is a working list for the manifest, not the manifest.

**Scope.** The modules are the 73 files of I2's inventory. A function is *reachable* when a chain
of calls, resolved by name, leads to it from the golden path's entry points (``ENTRIES``, the calls
of ``tests/baseline_code_v0511.py::_compute``). Calls and references are resolved through each
module's imports (``Resolver``); a method call on an object of unknown type goes to every method
of that name (over-inclusive on purpose).

**Fixtures** (the maintainer's decisions N2 and N4, #218 comment 7224847166). Each version's
verdict (its verdict, error and report entries) and each version's ``chain`` (stage 1) is its own
fixture. In a fixture, a call or a row that a configuration guard keeps from running there
(``GUARD_TABLE``, each guard with its source) is pruned and listed with that guard; a guard the
table does not hold keeps the call (inclusive). Each row lists the fixtures it is on.

**Sinks** (a serialized test status, class, eligibility flag, reason code or verdict):
- a call of ``TestResult``, ``_inconclusive``, ``_not_run`` or ``not_applicable_block``;
- a reference to ``TestStatus.<x>``;
- an assignment to a name, attribute or string subscript in ``DECISION_NAMES``, or a call of
  ``append``, ``extend``, ``add``, ``insert`` or ``update`` on such a name (``flagged.append``).

A function that holds a sink is a **decision function**.

**Decision contexts** (where a boolean reaches a sink):
1. the test of an ``if``, ``elif``, conditional expression or ``while`` whose branch (at any depth,
   not into nested functions) holds a sink, a ``return``, ``break``, ``continue`` or ``raise``
   in a decision function, or an assignment to, or a mutating call on, a decision variable;
2. the value assigned to a decision variable or to a name in ``DECISION_NAMES``;
3. the value of a ``return`` in a decision function, or in a function whose call sits in a
   decision context (a *returning decision function*);
4. an argument of a sink call, and a value of a dict literal given to a sink call or assigned to
   a name in ``CONTAINERS`` (a serialized flag).

Inside a decision context the walk goes through ``and``/``or``/``not``, the test of a conditional
expression, ``bool``, ``any``, ``all`` and a generator or comprehension's element (inclusive for
``any``/``all``). It **collects** every comparison and every call of ``isfinite``/``isnan``/
``isinf`` (each one a candidate row), and, where the expression is used as a truth value (a
test, or under ``and``/``or``/``not``/``bool``/``any``/``all``), every bare name, attribute,
subscript or other call as a non-numeric row (a flag). It marks every name it meets as a decision
variable of its function, and every function it calls as a returning decision function. It
**stops**, recording the reason, at arithmetic (``BinOp``), at a subscript or call that is not
used as a truth value (a selection, or a value), and at other nodes. The whole is repeated until
nothing changes.

**Reachability** follows calls and also references: a name or attribute that names a function
(a check passed in a list, a callback) makes it reachable.

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


MUTATORS = {"append", "extend", "add", "insert", "update"}


def _mutated(node: ast.AST) -> str | None:
    """The name a call such as ``flagged.append(x)`` mutates, if any."""
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in MUTATORS
        and isinstance(node.func.value, ast.Name)
    ):
        return node.func.value.id
    return None


def is_sink(node: ast.AST) -> bool:
    if isinstance(node, ast.Call) and _name(node.func) in SINK_CALLS:
        return True
    if _mutated(node) in DECISION_NAMES:
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


def module_of(rel: str) -> str:
    parts = rel[len("src/") : -len(".py")].split("/")
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _is_method(f: Func) -> bool:
    return any(part[:1].isupper() for part in f.qual.split(".")[:-1])


class Resolver:
    """Calls and references resolved through each module's imports.

    - A bare name ``f`` is a function of the same module named ``f`` (not a method), or the
      function a ``from <module> import f`` of that module names.
    - ``alias.f``, where ``alias`` is a module imported by ``from <package> import <module>`` or
      ``import <module> as alias``, is that module's top-level ``f``; ``Name.f``, where ``Name``
      is an imported or local class, is its method ``f``.
    - Any other ``obj.f`` is every method named ``f`` (inclusive: the object's type is unknown).
    Anything else (a builtin, a third-party name) resolves to nothing."""

    def __init__(self, sources: dict[str, str], funcs: list[Func]):
        self.mods = {module_of(rel): rel for rel in sources}
        self.top = {(f.rel, f.qual): f for f in funcs}
        self.plain: dict[tuple[str, str], list[Func]] = {}
        self.methods: dict[str, list[Func]] = {}
        for f in funcs:
            if _is_method(f):
                self.methods.setdefault(f.short, []).append(f)
            else:
                self.plain.setdefault((f.rel, f.short), []).append(f)
        self.names: dict[str, dict[str, tuple[str, str]]] = {}
        self.aliases: dict[str, dict[str, str]] = {}
        for rel, text in sources.items():
            names, aliases = {}, {}
            for node in ast.walk(ast.parse(text)):
                if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                    for a in node.names:
                        sub = f"{node.module}.{a.name}"
                        if sub in self.mods:
                            aliases[a.asname or a.name] = self.mods[sub]
                        elif node.module in self.mods:
                            names[a.asname or a.name] = (self.mods[node.module], a.name)
                elif isinstance(node, ast.Import):
                    for a in node.names:
                        if a.name in self.mods and a.asname:
                            aliases[a.asname] = self.mods[a.name]
            self.names[rel], self.aliases[rel] = names, aliases

    def resolve(self, f: Func, node: ast.AST) -> list[Func]:
        rel = f.rel
        if isinstance(node, ast.Name):
            found = self.plain.get((rel, node.id), [])
            if found:
                return found
            if node.id in self.names[rel]:
                mrel, orig = self.names[rel][node.id]
                return self.plain.get((mrel, orig), [])
            return []
        if isinstance(node, ast.Attribute):
            v = node.value
            if isinstance(v, ast.Name):
                if v.id in self.aliases[rel]:
                    g = self.top.get((self.aliases[rel][v.id], node.attr))
                    return [g] if g else []
                if v.id in self.names[rel]:
                    mrel, orig = self.names[rel][v.id]
                    g = self.top.get((mrel, f"{orig}.{node.attr}"))
                    if g:
                        return [g]
                g = self.top.get((rel, f"{v.id}.{node.attr}"))
                if g:
                    return [g]
            return list(self.methods.get(node.attr, []))
        return []


# The configuration guards, evaluated on each fixture's plan taken from source. Each entry is the
# guard as written (``ast.unparse``) and the versions where it is true. Sources:
# - plan.v05 / plan.is_v051 / plan.is_v052: src/refute/packs/tess/params.py:582-596, with the plans
#   of src/refute/packs/tess/synthetic.py:749-783 (v1: no ``stronger``; v2 and v2-eb: ``stronger``;
#   v3: also ``v051``; v4: also ``v052``);
# - corrections.active: params.py:252-255 with CorrectionsParams' defaults version 1, enabled False
#   (params.py:225-226); no synthetic plan sets them;
# - catalogs and stage: tests/baseline_code_v0511.py:84-92 (``analyze_data(data, plan, stage=2)``
#   and ``chain(..., plan, 1)``, with no catalogs);
# - plan.discovery: every synthetic plan has a discovery section (synthetic.py:749-783);
# - is_v5(plan): pipeline.py:580-582, discovery version 5; the fixtures are versions 1 to 4.
VERSIONS = ("v1", "v2", "v2-eb", "v3", "v4")
ALL = set(VERSIONS)
GUARD_TABLE = {
    "plan.v05": {"v2", "v2-eb", "v3", "v4"},
    "plan.is_v051": {"v3", "v4"},
    "plan.is_v052": {"v4"},
    "gp.corrections.active": set(),
    "plan.gauntlet.corrections.active": set(),
    "catalogs is not None": set(),
    "catalogs is None": ALL,
    "plan.discovery is not None": ALL,
    "plan.discovery is None": set(),
    # ``discovery = plan.discovery`` before the test (discover/measure.py:47-48,
    # pipeline.py:599-601)
    "discovery is not None": ALL,
    "discovery is None": set(),
    "plan is None": set(),
    "plan is not None": ALL,
    "is_v5(plan)": set(),
    "stage is None": set(),
}


def guard_value(test: ast.AST, version: str) -> bool | None:
    if isinstance(test, ast.BoolOp):
        vals = [guard_value(v, version) for v in test.values]
        if isinstance(test.op, ast.And):
            if False in vals:
                return False
            return True if all(v is True for v in vals) else None
        if True in vals:
            return True
        return False if all(v is False for v in vals) else None
    if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
        v = guard_value(test.operand, version)
        return None if v is None else not v
    key = ast.unparse(test)
    return (version in GUARD_TABLE[key]) if key in GUARD_TABLE else None


def _parents(f: Func) -> dict:
    if not hasattr(f, "_parents"):
        parents = {}
        for n in ast.walk(f.node):
            for c in ast.iter_child_nodes(n):
                parents[c] = n
        f._parents = parents
    return f._parents


def pruned_by(f: Func, node: ast.AST, version: str | None) -> str | None:
    """The configuration guard that keeps ``node`` from running in ``version``, if any."""
    if version is None:
        return None
    parents, child = _parents(f), node
    while child in parents and child is not f.node:
        p = parents[child]
        branch = None
        if isinstance(p, ast.If | ast.IfExp):
            body = p.body if isinstance(p.body, list) else [p.body]
            orelse = p.orelse if isinstance(p.orelse, list) else [p.orelse]
            if any(child is b for b in body):
                branch = True
            elif any(child is b for b in orelse):
                branch = False
        if branch is not None:
            v = guard_value(p.test, version)
            if v is not None and v != branch:
                return ("" if branch else "not ") + ast.unparse(p.test)
        child = p
    return None


def analyze(sources: dict[str, str], entries=ENTRIES, version: str | None = None) -> dict:
    """The candidate rows. With ``version``, calls and rows that a configuration guard keeps
    from running in that fixture are pruned (``GUARD_TABLE``)."""
    funcs = collect_functions(sources)
    resolver = Resolver(sources, funcs)
    edges: dict[str, set[str]] = {}
    for f in funcs:
        out = set()
        for n in f.walk():
            target = None
            if isinstance(n, ast.Call):
                target = n.func
            elif isinstance(n, ast.Name | ast.Attribute) and isinstance(n.ctx, ast.Load):
                # a function passed by reference (a list of checks, a callback) is reachable too
                target = n
            if target is None or pruned_by(f, n, version):
                continue
            out |= {g.key for g in resolver.resolve(f, target)}
        edges[f.key] = out
    by_key = {f.key: f for f in funcs}
    reach: set[str] = set()
    todo = [f.key for f in funcs if (f.rel, f.qual) in set(entries)]
    while todo:
        k = todo.pop()
        if k in reach:
            continue
        reach.add(k)
        todo += [g for g in edges[k] if g not in reach]
    live = [by_key[k] for k in sorted(reach)]
    deciding = {f.key for f in live if any(is_sink(n) for n in f.walk())}
    rows: dict[tuple, dict] = {}
    stops: dict[str, int] = {}
    returning: set[str] = set()

    def bare(f: Func, n: ast.AST, ctx: str, what: str) -> bool:
        """A name, attribute, subscript or call used as a boolean: a non-numeric row."""
        key = (f.rel, n.lineno, n.col_offset)
        new = key not in rows
        if new:
            rows[key] = {"file": f.rel, "line": n.lineno, "end_line": n.end_lineno,
                         "function": f.qual, "expression": _src(f.text, n),
                         "operators": [what], "kind": "non-numeric", "contexts": set(),
                         "node": n, "func": f}  # fmt: skip
        rows[key]["contexts"].add(ctx)
        return new

    def walk_ctx(f: Func, expr: ast.AST, ctx: str, boolean: bool = False) -> bool:
        """Walk a decision context; True when it changed the state. ``boolean`` says that the
        expression is used as a truth value (a test, or under ``and``/``or``/``not``)."""
        changed = False
        stack = [(expr, boolean)]
        while stack:
            n, is_bool = stack.pop()
            if isinstance(n, ast.BoolOp):
                stack += [(v, True) for v in n.values]
            elif isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.Not):
                stack.append((n.operand, True))
            elif isinstance(n, ast.IfExp):
                stack += [(n.test, True), (n.body, is_bool), (n.orelse, is_bool)]
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
                    stack += [(a, True) for a in n.args]
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
                    for g in resolver.resolve(f, n.func):
                        if g.key in reach and g.key not in returning:
                            returning.add(g.key)
                            changed = True
                    if is_bool:
                        changed |= bare(f, n, ctx, "call")
                    else:
                        stops["call"] = stops.get("call", 0) + 1
            elif isinstance(n, ast.GeneratorExp | ast.ListComp | ast.SetComp):
                stack.append((n.elt, is_bool))
            elif isinstance(n, ast.Name):
                if n.id not in f.dvars:
                    f.dvars.add(n.id)
                    changed = True
                if is_bool:
                    changed |= bare(f, n, ctx, "name")
            elif isinstance(n, ast.BinOp):
                stops["arithmetic"] = stops.get("arithmetic", 0) + 1
            elif isinstance(n, ast.Subscript):
                if is_bool:
                    changed |= bare(f, n, ctx, "subscript")
                else:
                    stops["subscript"] = stops.get("subscript", 0) + 1
            elif isinstance(n, ast.Attribute):
                if is_bool:
                    changed |= bare(f, n, ctx, "attribute")
            elif isinstance(n, ast.Constant):
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
            if _mutated(n) in f.dvars:
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
                    changed |= walk_ctx(f, n.test, "branch test", True)
                elif isinstance(n, ast.IfExp) and effect(f, [n.body, n.orelse]):
                    changed |= walk_ctx(f, n.test, "conditional expression", True)
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
    out_rows, pruned_rows = [], []
    for row in sorted(rows.values(), key=lambda r: (r["file"], r["line"], r["node"].col_offset)):
        f, node = row.pop("func"), row.pop("node")
        row["contexts"] = sorted(row["contexts"])
        row["col"] = node.col_offset
        row["guards"] = _guards(f, node)
        row["early_exits_before"] = _early_exits(f, node)
        guard = pruned_by(f, node, version)
        if guard:
            pruned_rows.append({**row, "pruned_by": guard})
        else:
            out_rows.append(row)
    return {
        "functions": len(funcs),
        "reachable": sorted(reach),
        "deciding": sorted(deciding),
        "returning": sorted(returning),
        "stops": dict(sorted(stops.items())),
        "rows": out_rows,
        "pruned_rows": pruned_rows,
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
    funcs = collect_functions(sources)
    reach = set(result["reachable"])

    def where(rel: str, line: int) -> str:
        inner = [f for f in funcs if f.rel == rel and f.node.lineno <= line <= f.node.end_lineno]
        if not inner:
            return "module level"
        f = max(inner, key=lambda g: g.node.lineno)
        return f"{f.qual} ({'reachable' if f.key in reach else 'not reachable'})"

    j1_missing = [
        f"{a['file']}:{a['line']} {a['atom']} [in {where(a['file'], a['line'])}]"
        for a in j1
        if (a["file"], a["line"]) not in lines
    ]
    # the disposition of the other I2 sites in reachable functions: not in a decision context
    row_sites = {(r["file"], r["line"]) for r in rows}
    left: dict[str, int] = {}
    for site in inv["rows"]:
        f = where(site["file"], site["line"])
        if "(reachable)" in f and (site["file"], site["line"]) not in row_sites:
            left[site["file"]] = left.get(site["file"], 0) + 1
    # the two evaluations: the rows reached from chain (stage 1) and from the verdict's entries
    # the fixtures: each version's verdict (with its error and report) and its chain (stage 1)
    membership: dict[tuple, list[str]] = {}
    per_fixture: dict[str, dict] = {}
    pruned_list = []
    for v in VERSIONS:
        for label, entries in (
            (v, [e for e in ENTRIES if e[1] != "chain"]),
            (f"chain-{v}", [e for e in ENTRIES if e[1] == "chain"]),
        ):
            part = analyze(sources, entries, v)
            keys = {(r["file"], r["line"], r["expression"]) for r in part["rows"]}
            for k in keys:
                membership.setdefault(k, []).append(label)
            per_fixture[label] = {
                "rows": len(keys),
                "numeric": sum(1 for r in part["rows"] if r["kind"] == "numeric"),
                "finiteness": sum(1 for r in part["rows"] if r["kind"] == "finiteness"),
                "pruned_by_configuration": len(part["pruned_rows"]),
            }
            pruned_list += [
                f"{label}: {p['file']}:{p['line']} {p['expression']} [{p['pruned_by']}]"
                for p in part["pruned_rows"]
            ]
    for r in rows:
        r["fixtures"] = sorted(membership.get((r["file"], r["line"], r["expression"]), []))
    on_none = [f"{r['file']}:{r['line']} {r['expression']}" for r in rows if not r["fixtures"]]
    chain_rows = {
        k for k, labels in membership.items() if any(x.startswith("chain-") for x in labels)
    }
    verdict_rows = {
        k for k, labels in membership.items() if any(not x.startswith("chain-") for x in labels)
    }
    both = chain_rows & verdict_rows
    by_entry = {"chain": chain_rows, "verdict": verdict_rows}
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
        "j1_atoms_not_found_in_reachable_functions": sum(
            1 for m in j1_missing if "(reachable)" in m
        ),
        "named": named,
        "i2_sites_in_reachable_functions_not_rows": sum(left.values()),
        "rows_from_chain_entry": len(by_entry["chain"]),
        "rows_from_verdict_entries": len(by_entry["verdict"]),
        "rows_from_both": len(both),
        "rows_on_no_fixture_after_pruning": len(on_none),
        "per_fixture": per_fixture,
        "stops": result["stops"],
    }
    summary["i2_sites_left_per_file"] = dict(sorted(left.items()))
    out = {"rule": "see the tool's docstring", "guard_table": {k: sorted(v) for k, v in
           GUARD_TABLE.items()}, "summary": summary, "j1_missing": j1_missing,
           "rows_not_i2_sites": not_i2, "rows_on_no_fixture": on_none,
           "pruned_by_configuration": pruned_list, **result}  # fmt: skip
    Path(sys.argv[1]).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
