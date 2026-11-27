"""The exact keys of the comparator's schema, from source only (v0.5.13, the maintainer's decision
L4(b), #218 comment 7223634913). It opens no golden file.

    unit schema-keys:  {python} -I -B docs/validation/v0.5.13/tools/schema_keys.py <out.json>

A JSON key is an **exact key** (a threshold or configuration value, compared byte for byte by the
comparator even under a measurement pattern) when, in the source at HEAD:
1. it is the name of a field of a pydantic model in ``src/refute/packs/tess/params.py`` (an
   annotated name in the body of a class), that is, a configuration field of the test plan; or
2. it is a string key of a dict literal given as the ``thresholds`` argument of a call, or
   assigned to a name ``thresholds``, in a module of the golden path (``MODULES``).

Rule 1 does not take a **measurement output name**: a field of the dataclasses ``Candidate``
(``types.py``) and ``Ephemeris`` (``ephemeris.py``), a key their ``to_dict`` adds, or a literal key
of ``key_values`` in ``pipeline.build_result`` (with ``t_ref_bjd``, which ``build_result`` adds to
the ephemeris). Those names are what the search and the ephemeris fit measure; a plan field of the
same name (for example a published or injected value) is a different quantity. Rule 2 takes every
key it finds, measurement output name or not.

Otherwise the rule over-includes on purpose: a measurement key that shares a name with a
configuration field becomes exact, which can only make the comparator fail, never pass. The tool
also reports
which of the fields D1a found to differ (``step1/diag-golden-diff.json``, already exposed) are
exact keys; any such field is a conflict to be resolved before the freeze.
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
TESS = "src/refute/packs/tess/"
MODULES = (
    [
        TESS + m + ".py"
        for m in (
            "pipeline battery gauntlet ebcatalog holdout battery_v5 power centroid_v5 battery_v51 "
            "battery_v51_diff a0 duration pipeline_v52 battery_v52 a0_v4 report search detrend "
            "detrend_fast prewhiten rednoise rednoise_fast ephemeris events timing inconclusive"
        ).split()
    ]
    + [TESS + "discover/measure.py"]
    + [f"src/refute/core/{m}.py" for m in ("verdict", "sensitivity", "inconclusive")]
)
D1A = "docs/validation/v0.5.13/step1/diag-golden-diff.json"


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


def threshold_keys() -> dict[str, list[str]]:
    found: dict[str, set[str]] = {}

    def take(d: ast.AST, rel: str) -> None:
        if isinstance(d, ast.Dict):
            for k in d.keys:
                if isinstance(k, ast.Constant) and isinstance(k.value, str):
                    found.setdefault(k.value, set()).add(f"{rel}:{k.lineno}")

    for rel in MODULES:
        path = ROOT / rel
        if not path.is_file():
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                for kw in node.keywords:
                    if kw.arg == "thresholds":
                        take(kw.value, rel)
            if isinstance(node, ast.Assign):
                if any(isinstance(t, ast.Name) and t.id == "thresholds" for t in node.targets):
                    take(node.value, rel)
    return {k: sorted(v) for k, v in sorted(found.items())}


def main() -> int:
    measured = measurement_names()
    fields = plan_fields()
    thresholds = threshold_keys()
    exact = sorted((fields - measured) | set(thresholds))
    d1a = json.loads((ROOT / D1A).read_text(encoding="utf-8"))
    differing = sorted(
        {f for s in d1a["settings"].values() for f in s["differing_fields_max_rel_diff"]}
    )
    conflicts = sorted(set(differing) & set(exact))
    out = {
        "rule": "plan model fields of params.py that are not measurement output names, and keys "
        "of thresholds dicts on the golden path",
        "modules": MODULES,
        "measurement_output_names": sorted(measured),
        "plan_fields_left_out": sorted(fields & measured),
        "plan_fields": sorted(fields),
        "threshold_keys": thresholds,
        "exact_keys": exact,
        "d1a_differing_fields": differing,
        "d1a_conflicts": conflicts,
    }
    Path(sys.argv[1]).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"exact_keys": len(exact), "plan_fields": len(fields),
                      "left_out": sorted(fields & measured), "threshold_keys": len(thresholds),
                      "measured_and_threshold": sorted(measured & set(thresholds)),
                      "d1a_conflicts": conflicts}))  # fmt: skip
    return 0 if not conflicts else 1


if __name__ == "__main__":
    raise SystemExit(main())
