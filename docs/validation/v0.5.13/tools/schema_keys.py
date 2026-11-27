"""The exact keys of the comparator's schema, from source only (v0.5.13, the maintainer's decisions
L4(b) and M3, #218 comments 7223634913 and 7224251159). It opens no golden file.

    unit schema-keys:  {python} -I -B docs/validation/v0.5.13/tools/schema_keys.py <out.json>

**The modules** are the 73 files of I2's inventory (``module_files`` of
``docs/validation/v0.5.13/i2/predicate-inventory.json``), the import closure of the golden path.
A listed file that does not exist is a failure.

A JSON key is an **exact key** (a threshold or configuration value, compared byte for byte by the
comparator even under a measurement pattern) when, in the source of those modules:
1. it is the name of a field of a pydantic model in ``src/refute/packs/tess/params.py`` (an
   annotated name in the body of a class), that is, a configuration field of the test plan, and
   is not a measurement output name (below);
2. it is a key of a ``thresholds`` mapping: a string key of a dict literal, or a keyword of a
   ``dict(...)`` call, given as the ``thresholds`` argument of a call, assigned to a name
   ``thresholds``, added by ``thresholds["key"] = ...`` or by ``thresholds.update({...})``. A
   ``thresholds`` argument that is a name is resolved through the dict literal assigned to that
   name in the same function. Every ``thresholds`` argument it cannot resolve is listed;
3. it is a key of a ``metrics``, ``inputs`` or ``sensitivity`` mapping (the same forms as rule 2)
   whose value echoes configuration: an attribute whose last name is a plan field, an all-caps
   name, a numeric literal, or one of these inside ``float(...)``, ``int(...)`` or ``bool(...)``.

A **measurement output name** is a field of the dataclasses ``Candidate`` (``types.py``) and
``Ephemeris`` (``ephemeris.py``), a key their ``to_dict`` adds, or a literal key of ``key_values``
in ``pipeline.build_result`` (with ``t_ref_bjd``, which ``build_result`` adds to the ephemeris).
Those are what the search and the ephemeris fit measure; a plan field of the same name (a
published or injected value) is a different quantity. Only rule 1 leaves them out.

The rules over-include on purpose: a measurement key that shares a name with a configuration
value becomes exact, which can only make the comparator fail, never pass. The tool also reports
which of the fields D1a found to differ (``step1/diag-golden-diff.json``, already exposed) are
exact keys; any such field is a conflict, and the tool exits 1.
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
TESS = "src/refute/packs/tess/"
INVENTORY = "docs/validation/v0.5.13/i2/predicate-inventory.json"
D1A = "docs/validation/v0.5.13/step1/diag-golden-diff.json"
CONTAINERS = {"metrics", "inputs", "sensitivity"}


def modules() -> list[str]:
    listed = json.loads((ROOT / INVENTORY).read_text(encoding="utf-8"))["module_files"]
    missing = [m for m in listed if not (ROOT / m).is_file()]
    if missing:
        raise SystemExit(f"modules listed by I2's inventory are missing: {missing}")
    return listed


def plan_fields() -> set[str]:
    tree = ast.parse((ROOT / TESS / "params.py").read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    names.add(item.target.id)
    return names


def measurement_names() -> set[str]:
    names = {"t_ref_bjd"}
    for rel, cls in ((TESS + "types.py", "Candidate"), (TESS + "ephemeris.py", "Ephemeris")):
        tree = ast.parse((ROOT / rel).read_text(encoding="utf-8"))
        node = next(n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == cls)
        for item in node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                names.add(item.target.id)
            if isinstance(item, ast.FunctionDef) and item.name == "to_dict":
                for sub in ast.walk(item):
                    if isinstance(sub, ast.Subscript) and isinstance(sub.slice, ast.Constant):
                        names.add(sub.slice.value)
                    if isinstance(sub, ast.Dict):
                        names |= {k.value for k in sub.keys if isinstance(k, ast.Constant)}
    tree = ast.parse((ROOT / TESS / "pipeline.py").read_text(encoding="utf-8"))
    build = next(
        n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "build_result"
    )
    for sub in ast.walk(build):
        if (
            isinstance(sub, ast.Call)
            and isinstance(sub.func, ast.Attribute)
            and sub.func.attr == "update"
            and isinstance(sub.func.value, ast.Name)
            and sub.func.value.id == "key_values"
            and sub.args
            and isinstance(sub.args[0], ast.Dict)
        ):
            names |= {k.value for k in sub.args[0].keys if isinstance(k, ast.Constant)}
    return names


def _entries(node: ast.AST) -> list[tuple[str, ast.AST, int]]:
    """(key, value, line) of a dict literal or a dict(...) call; [] for anything else."""
    if isinstance(node, ast.Dict):
        return [
            (k.value, v, k.lineno)
            for k, v in zip(node.keys, node.values, strict=True)
            if isinstance(k, ast.Constant) and isinstance(k.value, str)
        ]
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "dict":
        return [(kw.arg, kw.value, kw.value.lineno) for kw in node.keywords if kw.arg]
    return []


def _mappings(tree: ast.AST, names: set[str]):
    """Every (container name, key, value, line) written to a mapping called by one of ``names``,
    and every argument of that name that is not a literal mapping (``unresolved``)."""
    found, unresolved = [], []
    for func in [
        n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef)
    ] + [tree]:
        local = {}
        for node in ast.walk(func):
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                t = node.targets[0]
                if isinstance(t, ast.Name):
                    local.setdefault(t.id, node.value)
        for node in ast.walk(func):
            if isinstance(node, ast.Call):
                for kw in node.keywords:
                    if kw.arg in names:
                        value = kw.value
                        if isinstance(value, ast.Name) and value.id in local:
                            value = local[value.id]
                        items = _entries(value)
                        if items:
                            found += [(kw.arg, k, v, line) for k, v, line in items]
                        elif not (isinstance(value, ast.Constant) and value.value is None):
                            unresolved.append((kw.arg, kw.value.lineno, ast.unparse(kw.value)))
                if (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr == "update"
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id in names
                    and node.args
                ):
                    found += [
                        (node.func.value.id, k, v, line) for k, v, line in _entries(node.args[0])
                    ]
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name) and t.id in names:
                        found += [(t.id, k, v, line) for k, v, line in _entries(node.value)]
                    if (
                        isinstance(t, ast.Subscript)
                        and isinstance(t.value, ast.Name)
                        and t.value.id in names
                        and isinstance(t.slice, ast.Constant)
                        and isinstance(t.slice.value, str)
                    ):
                        found.append((t.value.id, t.slice.value, node.value, node.lineno))
    return found, unresolved


def echoes_config(value: ast.AST, fields: set[str]) -> bool:
    if isinstance(value, ast.Call) and isinstance(value.func, ast.Name):
        if value.func.id in {"float", "int", "bool"} and len(value.args) == 1:
            return echoes_config(value.args[0], fields)
    if isinstance(value, ast.Attribute):
        return value.attr in fields
    if isinstance(value, ast.Name):
        return value.id.isupper()
    if isinstance(value, ast.Constant):
        return isinstance(value.value, int | float) and not isinstance(value.value, bool)
    return False


def main() -> int:
    mods = modules()
    measured = measurement_names()
    fields = plan_fields()
    thresholds: dict[str, set[str]] = {}
    echoes: dict[str, set[str]] = {}
    unresolved = []
    seen = set()
    for rel in mods:
        tree = ast.parse((ROOT / rel).read_text(encoding="utf-8"))
        found, missed = _mappings(tree, {"thresholds"} | CONTAINERS)
        for container, key, value, line in found:
            if (rel, container, key, line) in seen:
                continue
            seen.add((rel, container, key, line))
            if container == "thresholds":
                thresholds.setdefault(key, set()).add(f"{rel}:{line}")
            elif echoes_config(value, fields):
                echoes.setdefault(key, set()).add(f"{rel}:{line} {container}: {ast.unparse(value)}")
        for container, line, text in missed:
            if container == "thresholds" and (rel, line, text) not in {
                (u["file"], u["line"], u["expression"]) for u in unresolved
            }:
                unresolved.append({"file": rel, "line": line, "expression": text})
    exact = sorted((fields - measured) | set(thresholds) | set(echoes))
    d1a = json.loads((ROOT / D1A).read_text(encoding="utf-8"))
    differing = sorted(
        {f for s in d1a["settings"].values() for f in s["differing_fields_max_rel_diff"]}
    )
    conflicts = sorted(set(differing) & set(exact))
    out = {
        "rule": "see the tool's docstring: rule 1 plan fields less measurement output names; "
        "rule 2 thresholds keys; rule 3 configuration echoed in metrics, inputs or sensitivity",
        "modules": mods,
        "measurement_output_names": sorted(measured),
        "plan_fields_left_out": sorted(fields & measured),
        "plan_fields": sorted(fields),
        "threshold_keys": {k: sorted(v) for k, v in sorted(thresholds.items())},
        "unresolved_thresholds_arguments": sorted(unresolved, key=lambda u: (u["file"], u["line"])),
        "config_echo_keys": {k: sorted(v) for k, v in sorted(echoes.items())},
        "exact_keys": exact,
        "d1a_differing_fields": differing,
        "d1a_conflicts": conflicts,
    }
    Path(sys.argv[1]).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"modules": len(mods), "exact_keys": len(exact), "plan_fields": len(fields),
                      "left_out": sorted(fields & measured), "threshold_keys": len(thresholds),
                      "unresolved_thresholds": len(unresolved), "config_echo_keys": len(echoes),
                      "echo_and_measured": sorted(measured & set(echoes)),
                      "d1a_conflicts": conflicts}))  # fmt: skip
    return 0 if not conflicts else 1


if __name__ == "__main__":
    raise SystemExit(main())
