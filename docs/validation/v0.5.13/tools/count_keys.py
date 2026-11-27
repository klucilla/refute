"""The explicit list of exact integer keys of the comparator's schema, from source only (v0.5.13,
the maintainer's decision T2(1), #218 comment 7227882370). It opens no golden file.

    unit count-keys:  {python} -I -B docs/validation/v0.5.13/tools/count_keys.py <out.json>

**The modules** are those of ``l4/schema-keys.json`` (I2's inventory: the import closure of the
golden path). A listed file that does not exist is a failure.

A JSON key is an **exact integer key** (a count, ID, version, index or integer flag: its number is
compared byte for byte, and a change of notation such as ``4`` against ``4.0`` fails) when, in the
source of those modules:
1. it is the string key of a dict literal entry, of a subscript assignment ``d["key"] = value``,
   or the keyword of a ``dict(...)`` call, whose value is an integer: an ``int`` literal (not a
   ``bool``), a negated ``int`` literal, or a call to ``int``, ``len`` or one-argument ``round``;
2. it is a field of a class annotated ``int``, ``int | None``, ``Optional[int]``, ``list[int]``,
   ``tuple[int, ...]`` or ``set[int]``.

The rules over-include on purpose: a float measurement that shares a name with an integer key
becomes exact, which can only make the comparator fail, never pass. The tool lists each key with
its sources, and it reports which of these keys are also a measurement output name or a field D1a
found to differ (``schema-keys.json``); any such key is a conflict, listed for review, and the tool
exits 1.
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
KEYS = "docs/validation/v0.5.13/l4/schema-keys.json"
INT_CALLS = {"int", "len"}


def is_int_value(node: ast.AST) -> bool:
    if isinstance(node, ast.Constant):
        return type(node.value) is int
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return is_int_value(node.operand)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        if node.func.id in INT_CALLS:
            return True
        if node.func.id == "round" and len(node.args) == 1 and not node.keywords:
            return True
    return False


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


def scan(rel: str, found: dict[str, list[str]]) -> None:
    tree = ast.parse((ROOT / rel).read_text(encoding="utf-8"))

    def add(key: str, node: ast.AST) -> None:
        found.setdefault(key, []).append(f"{rel}:{node.lineno}")

    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for k, v in zip(node.keys, node.values, strict=True):
                if isinstance(k, ast.Constant) and isinstance(k.value, str) and is_int_value(v):
                    add(k.value, k)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if (
                    isinstance(target, ast.Subscript)
                    and isinstance(target.slice, ast.Constant)
                    and isinstance(target.slice.value, str)
                    and is_int_value(node.value)
                ):
                    add(target.slice.value, target)
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == "dict":
                for kw in node.keywords:
                    if kw.arg is not None and is_int_value(kw.value):
                        add(kw.arg, kw)
        elif isinstance(node, ast.ClassDef):
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
    found: dict[str, list[str]] = {}
    for rel in modules:
        scan(rel, found)
    found = {k: sorted(set(v)) for k, v in sorted(found.items())}
    measured = set(keys["measurement_output_names"]) | set(keys["d1a_differing_fields"])
    conflicts = sorted(k for k in found if k in measured)
    out = {
        "rule": "see the tool's docstring: int literals, int/len/one-argument round calls, and "
        "int-annotated class fields, over the modules of schema-keys.json",
        "modules": len(modules),
        "exact_integer_keys": found,
        "conflicts_with_measurement_names": conflicts,
    }
    Path(sys.argv[1]).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"keys": len(found), "conflicts": conflicts}))
    return 1 if conflicts else 0


if __name__ == "__main__":
    raise SystemExit(main())
