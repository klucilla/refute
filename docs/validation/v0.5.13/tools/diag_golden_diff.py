"""A new diagnostic beside NR-A1 (the maintainer's decision D1a, #218 comment 7207651312):
``exploratory``, post hoc, replacing nothing.

    unit diag-golden-diff:  {python} -I -B docs/validation/v0.5.13/tools/diag_golden_diff.py

**The question** (in the journal before it runs, through the unit's spec): where do the golden
outputs of the pinned settings (``nr-a1-t1``, ``nr-a1-t4``) differ from ID-BEFORE's, and by how
much?

**The quantity**, for each of the golden output files (``.cache/v0513/golden/before/*``
against ``.cache/v0513/golden/nr-a1-t1/*`` and ``nr-a1-t4/*``):
- the number of lines, and of lines that differ (line by line; a file of another length is
  reported);
- for each differing line: whether it differs only in numbers (both lines equal once every number
  is replaced by a placeholder), the field name (the JSON key or the word before ``:`` or ``=``),
  and the largest relative difference among its numbers, ``|a - b| / max(|a|, |b|)``;
- per file and overall: the differing fields, the count of non-numeric differing lines, and the
  largest relative difference.

**The cases:** the files of the three folders, read only; nothing is recomputed. It reads no
claim and no tag. The result goes to ``out/diag-golden-diff.json``, labelled ``exploratory``,
``post hoc``, ``method_status: not_validated``.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
G = ROOT / ".cache" / "v0513" / "golden"
NUM = re.compile(r"[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?")
FIELD = re.compile(r'^\s*"?([A-Za-z_][\w.\-]*)"?\s*[:=]')


def rel(a: float, b: float) -> float:
    m = max(abs(a), abs(b))
    return 0.0 if m == 0 else abs(a - b) / m


def compare_file(name: str, other: str) -> dict:
    a = (G / "before" / name).read_text(encoding="utf-8").splitlines()
    b = (G / other / name).read_text(encoding="utf-8").splitlines()
    row: dict = {"lines_before": len(a), "lines_other": len(b), "differing_lines": 0,
                 "non_numeric_differing_lines": 0, "fields": {}, "max_rel_diff": 0.0}  # fmt: skip
    for x, y in zip(a, b, strict=False):
        if x == y:
            continue
        row["differing_lines"] += 1
        if NUM.sub("#", x) != NUM.sub("#", y):
            row["non_numeric_differing_lines"] += 1
            continue
        xs = [float(t) for t in NUM.findall(x)]
        ys = [float(t) for t in NUM.findall(y)]
        worst = max((rel(p, q) for p, q in zip(xs, ys, strict=True)), default=0.0)
        m = FIELD.match(x)
        field = m.group(1) if m else "(unnamed)"
        row["fields"][field] = max(row["fields"].get(field, 0.0), worst)
        row["max_rel_diff"] = max(row["max_rel_diff"], worst)
    return row


def main() -> int:
    names = sorted(p.name for p in (G / "before").iterdir() if p.is_file())
    doc: dict = {
        "labels": ["exploratory", "post hoc", "method_status: not_validated"],
        "beside": "NR-A1 (step1/comparison-nr-a1.json); it replaces nothing",
        "settings": {},
    }
    for other in ("nr-a1-t1", "nr-a1-t4"):
        files = {n: compare_file(n, other) for n in names}
        changed = {n: r for n, r in files.items() if r["differing_lines"] or
                   r["lines_before"] != r["lines_other"]}  # fmt: skip
        fields: dict[str, float] = {}
        for r in changed.values():
            for f, v in r["fields"].items():
                fields[f] = max(fields.get(f, 0.0), v)
        doc["settings"][other] = {
            "files_compared": len(names),
            "files_differing": changed,
            "non_numeric_differing_lines": sum(
                r["non_numeric_differing_lines"] for r in files.values()
            ),
            "differing_fields_max_rel_diff": dict(sorted(fields.items())),
            "max_rel_diff": max((r["max_rel_diff"] for r in files.values()), default=0.0),
        }
    out = Path(os.environ["REFUTE_RUN_OUT"])
    text = json.dumps(doc, indent=1) + "\n"
    (out / "diag-golden-diff.json").write_text(text, encoding="utf-8", newline="\n")
    summary = {
        k: {
            "files": list(v["files_differing"]),
            "non_numeric": v["non_numeric_differing_lines"],
            "max_rel": v["max_rel_diff"],
        }
        for k, v in doc["settings"].items()
    }
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
