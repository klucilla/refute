"""v0.5.12 step 2 (#223): the branch inventory of version 5's screen, by a STATIC reading of
``src/refute/packs/tess/screen_d5.py`` at the approval commit (the charter, step 2: "a committed
script lists, by a static reading of screen_d5.py at the approval commit, every branch that ends
in a not_assessed core test or an unavailable report-only record, by entry point and by record,
with its reason string"). It imports nothing from ``src/`` and runs no screen code.

    launch_v3 unit step2-inventory:
        {python} -I -B docs/validation/v0.5.12/step2/inventory.py

**A branch** is one site that produces a ``not_assessed`` F1 record or an ``unavailable``
report-only record, for one record name:
- ``_core("not_assessed", reason, ...)``;
- ``_unavailable(record, reason, ...)``, a literal record or the loop variable of a comprehension
  over every record;
- ``both(reason, ...)`` in ``_f2_u1``, one branch for F2 and one for U1;
- ``_guard(records, fn)``, one branch per record named, with the reason
  ``numerical failure: <exception>``;
- the ``except`` of ``f1_box``.

A reason that is an f-string is kept as its template; the parity templates give one branch per
parity value. **The entry points** of a site are the public functions (``f1_box``,
``report_only``, ``compute_screen``) whose static call graph reaches the site's function. **The
causes** are the ``return None`` sites of the helpers, listed apart: they are not branches, they
are what a branch's witness must trigger.

It writes ``inventory.json`` (copied to ``step2/``).
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
APPROVAL = "f18d6f8"
SRC = "src/refute/packs/tess/screen_d5.py"
ENTRY = ("f1_box", "report_only", "compute_screen")
RECORDS = ("F1_trap", "F2", "F3", "F4", "U1")
PARITY = ("odd", "even")
NUMFAIL = "numerical failure: {type(exc).__name__}"


def source() -> tuple[str, str]:
    full = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", APPROVAL], check=True, capture_output=True, text=True
    ).stdout.strip()
    blob = subprocess.run(
        ["git", "-C", str(ROOT), "show", f"{full}:{SRC}"], check=True, capture_output=True
    ).stdout
    return full, blob.decode("utf-8")


def reason_of(node: ast.AST) -> tuple[str, str]:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return "literal", node.value
    if isinstance(node, ast.JoinedStr):
        return "template", ast.unparse(node)
    return "expression", ast.unparse(node)


def calls_in(fn: ast.AST) -> set[str]:
    return {
        n.func.id for n in ast.walk(fn) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
    }


def main() -> int:
    commit, text = source()
    tree = ast.parse(text)
    funcs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    graph = {name: calls_in(fn) & set(funcs) for name, fn in funcs.items()}

    def reach(start: str) -> set[str]:
        seen, todo = set(), [start]
        while todo:
            f = todo.pop()
            if f not in seen:
                seen.add(f)
                todo.extend(graph.get(f, ()))
        return seen

    reached = {e: reach(e) for e in ENTRY}
    branches, causes = [], []

    def add(fn_name, node, record, state, kind, reason):
        variants = [reason]
        if kind == "template" and "name" in reason and fn_name == "_f1_box":
            variants = [reason.replace("{name}", p) for p in PARITY]
        for r in variants:
            branches.append(
                {
                    "function": fn_name,
                    "line": node.lineno,
                    "record": record,
                    "state": state,
                    "reason_kind": kind,
                    "reason": r,
                    "entry_points": [e for e in ENTRY if fn_name in reached[e]],
                }
            )

    for name, fn in funcs.items():
        if name in ("_unavailable", "_ro", "_core", "_guard"):
            continue
        for node in ast.walk(fn):
            if isinstance(node, ast.Return) and isinstance(node.value, ast.Constant):
                if node.value.value is None:
                    causes.append({"function": name, "line": node.lineno, "returns": "None"})
            if isinstance(node, ast.Return) and isinstance(node.value, ast.Tuple):
                first = node.value.elts[0] if node.value.elts else None
                if isinstance(first, ast.Constant) and first.value is None:
                    causes.append({"function": name, "line": node.lineno, "returns": "None,..."})
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
                continue
            callee, args = node.func.id, node.args
            if callee == "_core" and args and isinstance(args[0], ast.Constant):
                if args[0].value == "not_assessed":
                    add(name, node, "F1", "not_assessed", *reason_of(args[1]))
            elif callee == "_unavailable" and len(args) >= 2:
                rec = args[0]
                kind, reason = reason_of(args[1])
                if kind == "expression" and reason == "reason":
                    continue  # the body of _f2_u1's helper ``both``: its call sites are branches
                if isinstance(rec, ast.Constant):
                    add(name, node, rec.value, "unavailable", kind, reason)
                else:
                    for r in RECORDS:
                        add(name, node, r, "unavailable", kind, reason)
            elif callee == "both" and args:
                for r in ("F2", "U1"):
                    add(name, node, r, "unavailable", *reason_of(args[0]))
            elif callee == "_guard" and args and isinstance(args[0], ast.Tuple):
                for e in args[0].elts:
                    add(name, node, e.value, "unavailable", "template", NUMFAIL)
        for node in ast.walk(fn):
            if isinstance(node, ast.ExceptHandler) and name == "f1_box":
                add(name, node, "F1", "not_assessed", "template", NUMFAIL)

    # the comprehensions over every record call _unavailable once per site: deduplicate
    seen, unique = set(), []
    for b in branches:
        key = (b["function"], b["line"], b["record"], b["reason"])
        if key not in seen:
            seen.add(key)
            unique.append(b)
    for i, b in enumerate(unique, 1):
        b["id"] = f"B{i:02d}"
    doc = {
        "schema": "refute-v0512-step2-inventory",
        "labels": ["exploratory", "method_status: not_validated"],
        "decision": "#218 comment 7197519001, item 3; the charter, step 2",
        "source": {
            "commit": commit,
            "path": SRC,
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        },
        "entry_points": list(ENTRY),
        "branch_count": len(unique),
        "by_record": {r: sum(b["record"] == r for b in unique) for r in ("F1", *RECORDS)},
        "branches": [{"id": b.pop("id"), **b} for b in unique],
        "causes": causes,
    }
    out = Path(os.environ["REFUTE_RUN_OUT"]) / "inventory.json"
    out.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"branches": len(unique), "by_record": doc["by_record"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
