"""The explicit list of exact integer keys of the comparator's schema, from source only (v0.5.13,
the maintainer's decision T2(1), #218 comment 7227882370). It opens no golden file.

    unit count-keys:  {python} -I -B docs/validation/v0.5.13/tools/count_keys.py <out.json>

**The modules** are those of ``l4/schema-keys.json`` (I2's inventory: the import closure of the
golden path). A listed file that does not exist is a failure.

A JSON key is an **exact integer key** (a count, ID, version, index or integer flag: its number is
compared byte for byte, and a change of notation such as ``4`` against ``4.0`` fails) when, in the
source of those modules:
1. it is the string key of a dict literal entry, of a subscript assignment ``d["key"] = value``
   (also inside a tuple assignment, ``d["a"], d["b"] = x, y``), or the keyword of a
   ``dict(...)`` call, whose value is an integer by its form (``is_int_value``): an ``int``
   literal (not a ``bool``), a negated one, a conditional expression whose branches are all
   integers, a call to ``int``, ``len`` or one-argument ``round``, ``max`` or ``min`` of
   integers, ``+ - * // %`` of integers, a local name that its function only ever assigns
   integers (``used = int(...)`` then ``"cadences_used": used``), or an attribute named after an
   int-annotated class field (``n = cp.period_alias_realizations``);
2. it is a field of a class annotated ``int``, ``int | None``, ``Optional[int]``, ``list[int]``,
   ``tuple[int, ...]`` or ``set[int]``.

The rules over-include on purpose: a float measurement that shares a name with an integer key
becomes exact, which can only make the comparator fail, never pass. The tool lists each key with
its sources. It lists for review the keys that are also a measurement output name of
``schema-keys.json`` (for example ``n_transits`` and ``n_ref``, integer fields of the candidate
and the ephemeris: integer by their annotation, so exact). A key that is also a field D1a found
to differ is a conflict, and the tool exits 1.
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
KEYS = "docs/validation/v0.5.13/l4/schema-keys.json"
INT_CALLS = {"int", "len"}


INT_OPS = (ast.Add, ast.Sub, ast.Mult, ast.FloorDiv, ast.Mod)


def is_int_value(node: ast.AST, names=frozenset(), fields=frozenset()) -> bool:
    """Whether an expression is an integer by its form: an ``int`` literal, a negated one, a
    conditional of them, a call to ``int``, ``len`` or one-argument ``round``, ``max`` or ``min``
    of integers, ``+ - * // %`` of integers, a local name assigned an integer in the same function
    (``names``), or an attribute named after an int-annotated class field (``fields``)."""

    def rec(n: ast.AST) -> bool:
        return is_int_value(n, names, fields)

    if isinstance(node, ast.Constant):
        return type(node.value) is int
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return rec(node.operand)
    if isinstance(node, ast.IfExp):  # "discovery_version": 4 if ... else 3 ...
        return rec(node.body) and rec(node.orelse)
    if isinstance(node, ast.BinOp) and isinstance(node.op, INT_OPS):
        return rec(node.left) and rec(node.right)
    if isinstance(node, ast.Name):
        return node.id in names
    if isinstance(node, ast.Attribute):
        return node.attr in fields
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        if node.func.id in INT_CALLS:
            return True
        if node.func.id == "round" and len(node.args) == 1 and not node.keywords:
            return True
        if node.func.id in {"max", "min"} and node.args and not node.keywords:
            return all(rec(a) for a in node.args)
    return False


def int_names(scope: ast.AST, fields: frozenset) -> frozenset:
    """The local names a function (or the module) assigns an integer, by ``name = value`` or a
    tuple assignment, to a fixed point; a name ever assigned a non-integer is left out."""
    assigned: dict[str, list[ast.AST]] = {}
    for node in ast.walk(scope):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assigned.setdefault(target.id, []).append(node.value)
                elif isinstance(target, ast.Tuple) and isinstance(node.value, ast.Tuple):
                    for t, v in zip(target.elts, node.value.elts, strict=False):
                        if isinstance(t, ast.Name):
                            assigned.setdefault(t.id, []).append(v)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.value:
            assigned.setdefault(node.target.id, []).append(node.value)
    names: frozenset = frozenset()
    while True:
        grown = frozenset(
            n
            for n, values in assigned.items()
            if all(is_int_value(v, names, fields) for v in values)
        )
        if grown == names:
            return names
        names = grown


def is_int_annotation(node: ast.AST | None) -> bool:
    if node is None:
        return False
    if isinstance(node, ast.Name):
        return node.id == "int"
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        sides = [node.left, node.right]
        ints = [s for s in sides if is_int_annotation(s)]
        nones = [s for s in sides if isinstance(s, ast.Constant) and s.value is None]
        return len(ints) == 1 and len(ints) + len(nones) == 2
    if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
        inner = node.slice
        if node.value.id == "Optional":
            return is_int_annotation(inner)
        if node.value.id in {"list", "set"}:
            return is_int_annotation(inner)
        if node.value.id == "tuple" and isinstance(inner, ast.Tuple):
            return (
                bool(inner.elts)
                and is_int_annotation(inner.elts[0])
                and all(
                    is_int_annotation(e) or (isinstance(e, ast.Constant) and e.value is Ellipsis)
                    for e in inner.elts
                )
            )
    return False


def key_of(target: ast.AST) -> str | None:
    if (
        isinstance(target, ast.Subscript)
        and isinstance(target.slice, ast.Constant)
        and isinstance(target.slice.value, str)
    ):
        return target.slice.value
    return None


def int_fields(rel: str) -> set[str]:
    tree = ast.parse((ROOT / rel).read_text(encoding="utf-8"))
    return {
        item.target.id
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef)
        for item in node.body
        if isinstance(item, ast.AnnAssign)
        and isinstance(item.target, ast.Name)
        and is_int_annotation(item.annotation)
    }


def scan(rel: str, found: dict[str, list[str]], fields: frozenset = frozenset()) -> None:
    tree = ast.parse((ROOT / rel).read_text(encoding="utf-8"))

    def add(key: str, node: ast.AST) -> None:
        found.setdefault(key, []).append(f"{rel}:{node.lineno}")

    scopes = [tree] + [
        n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    for scope in scopes:
        names = int_names(scope, fields)

        def is_int(v: ast.AST, names=names) -> bool:
            return is_int_value(v, names, fields)

        for node in ast.walk(scope):
            if isinstance(node, ast.Dict):
                for k, v in zip(node.keys, node.values, strict=True):
                    if isinstance(k, ast.Constant) and isinstance(k.value, str) and is_int(v):
                        add(k.value, k)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    key = key_of(target)
                    if key is not None and is_int(node.value):
                        add(key, target)
                    elif isinstance(target, ast.Tuple) and isinstance(node.value, ast.Tuple):
                        # block["failures"], block["realizations"] = failures, n
                        for t, v in zip(target.elts, node.value.elts, strict=False):
                            key = key_of(t)
                            if key is not None and is_int(v):
                                add(key, t)
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id == "dict":
                    for kw in node.keywords:
                        if kw.arg is not None and is_int(kw.value):
                            add(kw.arg, kw)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if (
                    isinstance(item, ast.AnnAssign)
                    and isinstance(item.target, ast.Name)
                    and is_int_annotation(item.annotation)
                ):
                    add(item.target.id, item)


def main() -> int:
    keys = json.loads((ROOT / KEYS).read_text(encoding="utf-8"))
    modules = keys["modules"]
    missing = [m for m in modules if not (ROOT / m).is_file()]
    if missing:
        print(json.dumps({"result": "FAIL", "missing_modules": missing}))
        return 1
    fields = frozenset(f for rel in modules for f in int_fields(rel))
    found: dict[str, list[str]] = {}
    for rel in modules:
        scan(rel, found, fields)
    found = {k: sorted(set(v)) for k, v in sorted(found.items())}
    review = sorted(k for k in found if k in set(keys["measurement_output_names"]))
    conflicts = sorted(k for k in found if k in set(keys["d1a_differing_fields"]))
    out = {
        "rule": "see the tool's docstring: integer expressions by form (literals, conditionals, "
        "int/len/round/max/min calls, integer arithmetic, local names assigned integers, "
        "attributes named after int-annotated fields), through dict entries, subscript and "
        "tuple assignments and dict() keywords, and int-annotated class fields, over the "
        "modules of schema-keys.json",
        "limit": "a source enumeration by form; it cannot be proven complete. A key it misses "
        "stays under the measurement rules where a measurement pattern covers it",
        "modules": len(modules),
        "exact_integer_keys": found,
        "also_measurement_output_names": review,
        "conflicts_with_d1a_fields": conflicts,
    }
    Path(sys.argv[1]).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"keys": len(found), "review": review, "conflicts": conflicts}))
    return 1 if conflicts else 0


if __name__ == "__main__":
    raise SystemExit(main())
