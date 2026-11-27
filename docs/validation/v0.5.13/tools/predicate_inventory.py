"""The countable inventory behind the margin manifest of amendment 2, revision 4, section 4 (the
maintainer's decision I2(c), #218 comment 7222329150). It reads source only, never a golden value.

    unit predicate-inventory:  {python} -I -B docs/validation/v0.5.13/tools/predicate_inventory.py

1. **The modules on the golden path.** It starts from the modules that
   ``tests/baseline_code_v0511.py`` imports to compute the goldens:
   - ``refute.packs.tess.pipeline``, ``refute.packs.tess.discover.measure``;
   - ``refute.packs.tess.report``, ``refute.packs.tess.params``, ``refute.packs.tess.synthetic``;
   - ``refute.core.io``.
   It follows every import of a ``refute`` module, statically, at module level and inside
   functions, until closure. Third-party code is the boundary.
2. **The source is the same where the goldens were made.** Each module's file must be identical at
   ``HEAD``, at ID-BEFORE's head ``a150096de04e4caae9ef0042e6ae4c458823ac9e`` and at NR-A1's head
   ``ce154119c7f05ee4d317e13eecc9b0fd0edb9476``. A difference is listed.
3. **The sites.** In each module, it lists:
   - every comparison (``ast.Compare``);
   - every call whose name is a selection or a guard: ``max``, ``min``, ``argmax``, ``argmin``,
     ``sorted``, ``where``, ``isfinite``, ``isnan``, ``any``, ``all``, ``clip``, ``nanmax``,
     ``nanmin``, ``maximum`` and ``minimum``.

   Each site has its file, line, kind and verbatim source expression.

It writes ``out/predicate-inventory.json``. The manifest of section 4 must give each site a row or
a written reason.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / "src"
ENTRY = (
    "refute.packs.tess.pipeline",
    "refute.packs.tess.discover.measure",
    "refute.packs.tess.report",
    "refute.packs.tess.params",
    "refute.packs.tess.synthetic",
    "refute.core.io",
)
HEADS = {
    "id_before": "a150096de04e4caae9ef0042e6ae4c458823ac9e",
    "nr_a1": "ce154119c7f05ee4d317e13eecc9b0fd0edb9476",
}
SELECT = {"max", "min", "argmax", "argmin", "sorted", "where", "isfinite", "isnan", "any", "all",
          "clip", "nanmax", "nanmin", "maximum", "minimum"}  # fmt: skip


def module_path(name: str) -> Path | None:
    base = SRC / Path(*name.split("."))
    for cand in (base.with_suffix(".py"), base / "__init__.py"):
        if cand.is_file():
            return cand
    return None


def imports(tree: ast.AST, name: str, is_pkg: bool) -> set[str]:
    out = set()
    pkg = name if is_pkg else name.rsplit(".", 1)[0]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out |= {a.name for a in node.names if a.name.startswith("refute")}
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                parts = pkg.split(".")
                base = ".".join(parts[: len(parts) - node.level + 1])
                mod = f"{base}.{node.module}" if node.module else base
            else:
                mod = node.module or ""
            if mod.startswith("refute"):
                out.add(mod)
                out |= {f"{mod}.{a.name}" for a in node.names}
    return out


def git_blob(commit: str, rel: str) -> bytes | None:
    p = subprocess.run(["git", "show", f"{commit}:{rel}"], cwd=ROOT, capture_output=True)
    return p.stdout if p.returncode == 0 else None


def call_name(node: ast.Call) -> str | None:
    f = node.func
    return f.attr if isinstance(f, ast.Attribute) else f.id if isinstance(f, ast.Name) else None


def main() -> int:
    todo, seen, modules = list(ENTRY), set(), {}
    while todo:
        name = todo.pop()
        if name in seen:
            continue
        seen.add(name)
        path = module_path(name)
        if path is None:
            continue  # a name imported from a module, not a module
        tree = ast.parse(path.read_text(encoding="utf-8"))
        modules[name] = (path, tree)
        todo += sorted(imports(tree, name, path.name == "__init__.py") - seen)
    rows, diffs = [], []
    for _name, (path, tree) in sorted(modules.items()):
        rel = path.relative_to(ROOT).as_posix()
        head = git_blob("HEAD", rel)
        for label, commit in HEADS.items():
            if git_blob(commit, rel) != head:
                diffs.append({"module": rel, "differs_at": label})
        text = path.read_text(encoding="utf-8")
        for node in ast.walk(tree):
            kind = None
            if isinstance(node, ast.Compare):
                kind = "compare"
            elif isinstance(node, ast.Call) and call_name(node) in SELECT:
                kind = f"call:{call_name(node)}"
            if kind:
                src = ast.get_source_segment(text, node) or ast.unparse(node)
                rows.append({"file": rel, "line": node.lineno, "kind": kind,
                             "expression": " ".join(src.split())})  # fmt: skip
    rows.sort(key=lambda r: (r["file"], r["line"], r["expression"]))
    kinds = sorted({r["kind"] for r in rows})
    per_file: dict[str, int] = {}
    for r in rows:
        per_file[r["file"]] = per_file.get(r["file"], 0) + 1
    report = {
        "entry_modules": list(ENTRY),
        "modules": len(modules),
        "module_files": sorted(p.relative_to(ROOT).as_posix() for p, _ in modules.values()),
        "source_differs": diffs,
        "sites": len(rows),
        "by_kind": {k: sum(r["kind"] == k for r in rows) for k in kinds},
        "per_file": per_file,
        "inventory_sha256": hashlib.sha256(json.dumps(rows).encode()).hexdigest(),
        "rows": rows,
    }
    out = Path(os.environ.get("REFUTE_RUN_OUT", "."))
    text = json.dumps(report, indent=1) + "\n"
    (out / "predicate-inventory.json").write_text(text, encoding="utf-8", newline="\n")
    print(json.dumps({k: report[k] for k in ("modules", "sites", "by_kind", "source_differs")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
