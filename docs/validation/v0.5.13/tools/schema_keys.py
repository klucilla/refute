"""The exact keys of the comparator's schema, from source only (v0.5.13, the maintainer's decision
L4(b), #218 comment 7223634913). It opens no golden file.

    unit schema-keys:  {python} -I -B docs/validation/v0.5.13/tools/schema_keys.py <out.json>

A JSON key is an **exact key** (a threshold or configuration value, compared byte for byte by the
comparator even under a measurement pattern) when, in the source at HEAD:
1. it is the name of a field of a pydantic model in ``src/refute/packs/tess/params.py`` (an
   annotated name in the body of a class), that is, a configuration field of the test plan; or
2. it is a string key of a dict literal given as the ``thresholds`` argument of a call, or
   assigned to a name ``thresholds``, in a module of the golden path (``MODULES``).

The rule over-includes on purpose: a measurement key that shares a name with a configuration
field becomes exact, which can only make the comparator fail, never pass. The tool also reports
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
    fields = plan_fields()
    thresholds = threshold_keys()
    exact = sorted(fields | set(thresholds))
    d1a = json.loads((ROOT / D1A).read_text(encoding="utf-8"))
    differing = sorted(
        {f for s in d1a["settings"].values() for f in s["differing_fields_max_rel_diff"]}
    )
    conflicts = sorted(set(differing) & set(exact))
    out = {
        "rule": "plan model fields of params.py, and keys of thresholds dicts on the golden path",
        "modules": MODULES,
        "plan_fields": sorted(fields),
        "threshold_keys": thresholds,
        "exact_keys": exact,
        "d1a_differing_fields": differing,
        "d1a_conflicts": conflicts,
    }
    Path(sys.argv[1]).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"exact_keys": len(exact), "plan_fields": len(fields),
                      "threshold_keys": len(thresholds), "d1a_conflicts": conflicts}))  # fmt: skip
    return 0 if not conflicts else 1


if __name__ == "__main__":
    raise SystemExit(main())
