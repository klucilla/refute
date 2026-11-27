"""A feasibility count of the decision-layer predicates of versions 1 to 4, from source only (the
maintainer's decision J1(b), #218 comment 7222879969). It opens no golden.

    unit decision-count:  {python} -I -B docs/validation/v0.5.13/tools/decision_count.py

**The rule (mechanical, stated so that it can be checked).** In the decision modules below, a
*decision site* is the test of an ``if``, an ``elif`` or a conditional expression whose branch
directly sets a serialized decision. That is, the branch, at its own level, holds one of:
- a call of ``TestResult``, ``_inconclusive``, ``_not_run`` or ``not_applicable_block``;
- a reference to ``TestStatus.<x>``;
- an assignment to, or an ``append`` on, a name in ``DECISION_NAMES``.

Its *predicates* are the atoms of the test after splitting ``and``/``or`` and removing ``not``:
each comparison, call or name counts one.

**The groups of modules by version** follow the dispatch of ``pipeline.attack_candidate``:
- version 1 runs ``battery_tests``;
- version 2 adds ``v05_tests``;
- version 3 adds its ``is_v051`` branches and ``classify_v051``;
- version 4 runs ``pipeline_v52.v052_tests``, which also uses the version-3 modules.

A module is counted whole in the first version that uses it. So this is a **feasibility count by
module group**, not the manifest. The manifest attributes each row to its fixture. It writes
``out/decision-count.json``.
"""

from __future__ import annotations

import ast
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
T = "src/refute/packs/tess"
GROUPS = {
    "v1": [f"{T}/pipeline.py", f"{T}/battery.py", f"{T}/gauntlet.py", "src/refute/core/verdict.py",
           f"{T}/ebcatalog.py", f"{T}/holdout.py"],
    "v2": [f"{T}/battery_v5.py", f"{T}/power.py", "src/refute/core/sensitivity.py",
           f"{T}/centroid_v5.py"],
    "v3": [f"{T}/battery_v51.py", f"{T}/battery_v51_diff.py", f"{T}/a0.py",
           "src/refute/core/inconclusive.py", f"{T}/duration.py"],
    "v4": [f"{T}/pipeline_v52.py", f"{T}/battery_v52.py", f"{T}/a0_v4.py"],
}  # fmt: skip
CALLS = {"TestResult", "_inconclusive", "_not_run", "not_applicable_block"}
DECISION_NAMES = {"status", "verdict", "inconclusive_class", "reason", "eligible", "can_fail",
                  "fail_allowed", "flagged", "decisive", "failing", "passed"}  # fmt: skip


def marks(nodes: list[ast.AST]) -> bool:
    for top in nodes:
        for node in ast.walk(top):
            if isinstance(node, ast.FunctionDef | ast.Lambda):
                continue
            if isinstance(node, ast.Call):
                f = node.func
                name = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", None)
                if name in CALLS:
                    return True
                if name == "append" and isinstance(f, ast.Attribute):
                    if getattr(f.value, "id", None) in DECISION_NAMES:
                        return True
            if isinstance(node, ast.Attribute) and getattr(node.value, "id", None) == "TestStatus":
                return True
            if isinstance(node, ast.Assign | ast.AnnAssign | ast.AugAssign):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for t in targets:
                    key = getattr(t, "id", None) or getattr(t, "attr", None)
                    if isinstance(t, ast.Subscript) and isinstance(t.slice, ast.Constant):
                        key = t.slice.value
                    if key in DECISION_NAMES:
                        return True
    return False


def atoms(test: ast.AST) -> list[ast.AST]:
    if isinstance(test, ast.BoolOp):
        return [a for v in test.values for a in atoms(v)]
    if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
        return atoms(test.operand)
    return [test]


def main() -> int:
    per_module, per_version, rows = {}, {}, []
    for version, files in GROUPS.items():
        total = 0
        for rel in files:
            text = (ROOT / rel).read_text(encoding="utf-8")
            tree = ast.parse(text)
            n = 0
            for node in ast.walk(tree):
                if isinstance(node, ast.If) and marks(node.body + node.orelse):
                    test = node.test
                elif isinstance(node, ast.IfExp) and marks([node.body, node.orelse]):
                    test = node.test
                else:
                    continue
                for a in atoms(test):
                    n += 1
                    rows.append({"version_group": version, "file": rel, "line": a.lineno,
                                 "atom": " ".join((ast.get_source_segment(text, a) or
                                                   ast.unparse(a)).split())})  # fmt: skip
            per_module[rel] = n
            total += n
        per_version[version] = total
    cumulative, running = {}, 0
    for version in GROUPS:
        running += per_version[version]
        cumulative[version] = running
    report = {
        "rule": "see the tool's docstring",
        "groups": GROUPS,
        "per_module": per_module,
        "new_in_version": per_version,
        "cumulative_by_version": cumulative,
        "rows": rows,
    }
    out = Path(os.environ.get("REFUTE_RUN_OUT", "."))
    text = json.dumps(report, indent=1) + "\n"
    (out / "decision-count.json").write_text(text, encoding="utf-8", newline="\n")
    print(json.dumps({"new_in_version": per_version, "cumulative_by_version": cumulative}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
