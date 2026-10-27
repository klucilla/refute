"""The whole difference between two uv.lock files, package by package: added, removed, and for
each package present in both, every changed field (version, source, sdist, wheels, dependencies,
optional dependencies, metadata), plus the lock's own top-level fields. Usage:
lock_diff.py <before> <after> <out.json> (this copy reformatted by ruff format for the line limit;
otherwise as run)."""

import json
import sys
import tomllib
from pathlib import Path

NUMERIC = {
    "numpy", "scipy", "astropy", "astropy-iers-data", "pyerfa", "lightkurve", "astroquery",
    "pandas", "matplotlib", "scikit-learn", "threadpoolctl", "joblib", "contourpy", "kiwisolver",
    "fonttools", "numba", "llvmlite", "memoization", "pyvo", "python-dateutil", "pytz", "tzdata",
}  # fmt: skip


def load(path):
    data = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    packages = {}
    for p in data.get("package", []):
        packages[(p["name"], p.get("version"))] = p
    top = {k: v for k, v in data.items() if k != "package"}
    return top, packages


def by_name(packages):
    out = {}
    for (name, _), p in packages.items():
        out.setdefault(name, []).append(p)
    return out


before_top, before = load(sys.argv[1])
after_top, after = load(sys.argv[2])
b, a = by_name(before), by_name(after)
report = {"top_level_changes": {}, "added": [], "removed": [], "changed": {}}
for key in sorted(set(before_top) | set(after_top)):
    if before_top.get(key) != after_top.get(key):
        report["top_level_changes"][key] = {
            "before": before_top.get(key),
            "after": after_top.get(key),
        }
for name in sorted(set(a) - set(b)):
    report["added"].append({"name": name, "versions": [p.get("version") for p in a[name]]})
for name in sorted(set(b) - set(a)):
    report["removed"].append({"name": name, "versions": [p.get("version") for p in b[name]]})
for name in sorted(set(a) & set(b)):
    pb = sorted(b[name], key=lambda p: str(p.get("version")))
    pa = sorted(a[name], key=lambda p: str(p.get("version")))
    if pb == pa:
        continue
    fields = {}
    for x, y in zip(pb, pa, strict=False):
        for key in sorted(set(x) | set(y)):
            if x.get(key) != y.get(key):
                fields[key] = (
                    {"before": x.get(key), "after": y.get(key)}
                    if key in ("version", "source")
                    else "changed"
                )
    if len(pb) != len(pa):
        fields["entries"] = {"before": len(pb), "after": len(pa)}
    report["changed"][name] = {
        "versions": {
            "before": [p.get("version") for p in pb],
            "after": [p.get("version") for p in pa],
        },
        "fields": fields,
        "numeric_stack": name in NUMERIC,
    }
report["packages_before"] = len(before)
report["packages_after"] = len(after)
report["numeric_stack_changed"] = sorted(
    n
    for n in list(report["changed"]) + [x["name"] for x in report["added"] + report["removed"]]
    if n in NUMERIC
)
Path(sys.argv[3]).write_text(json.dumps(report, indent=1, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({"changed": sorted(report["changed"]), "added": report["added"],
                  "removed": report["removed"], "top": sorted(report["top_level_changes"]),
                  "numeric_stack_changed": report["numeric_stack_changed"],
                  "packages": [report["packages_before"], report["packages_after"]]}))  # fmt: skip
