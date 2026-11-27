"""The margin manifest of amendment 2, revision 6, section 4, with the reach rule of N1 and the
fixtures of N2 (the maintainer's decisions L4, M3, N1 to N4 and O1, #218). From source and
records only: it opens no golden file.

    unit manifest:  {python} -I -B docs/validation/v0.5.13/tools/manifest.py <out folder>

It reads ``l4/decision-layer.json`` (the candidate rows), ``l4/reach-table.json`` (the reach
class of each row in each fixture), ``l4/operand-map.json`` (the operands, written from source),
``l4/schema-keys.json`` and ``l4/comparator-schema-parts.json``, and the records of ID-BEFORE and
NR-A1 (``step0/golden-before.json``, ``step1/golden-nr-a1-*.json``). It writes:

- ``manifest.json``: every row of every fixture with its class:
  - ``non-numeric``: listed with its source location and a reason class; no margin row, not a
    declared limit, not counted as assessed (section 4, first paragraph);
  - ``reach-unknown``: a declared limit (N1(c)), counted in N;
  - ``absent``: reached-if, but an operand is absent (section 4; N2 for chain fixtures); a declared
    limit, counted in N;
  - ``assessable``: reached-if with both operands located; after the freeze it is assessed when
    the frozen reach conditions hold on the fixture's output, not reached when they fail, and its
    operands may still turn out absent through a conditional (``if_key``) location. The
    integer-or-configuration rows among them are counted apart (decision K2(f));
  then the declared limits, the first being that internal selections were not assessed for margin
  (section 4), and the counts per fixture. It fails when a reached-if numeric or finiteness row of
  some fixture has no entry in the operand map.
- ``comparator-schema.json``: the comparator's frozen schema (the draft parts, with the exact keys
  and exact subtree keys of ``schema-keys.json``).
- ``freeze.json``: the list section 4 freezes, each item with its SHA-256: the fixture list; for
  each setting, the source commit recorded in its golden record (``provenance.head``) and the git
  tree of ``src`` at that commit; the recorded SHA-256 of every golden file, plan files included,
  taken from the records, never by reading the files; the comparator, the schema and the
  manifest.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
L4 = "docs/validation/v0.5.13/l4"
RECORDS = {
    "id-before": "docs/validation/v0.5.13/step0/golden-before.json",
    "nr-a1-default": "docs/validation/v0.5.13/step1/golden-nr-a1-default.json",
    "nr-a1-t1": "docs/validation/v0.5.13/step1/golden-nr-a1-t1.json",
    "nr-a1-t4": "docs/validation/v0.5.13/step1/golden-nr-a1-t4.json",
}
CLAIM_RECORDS = {
    "id-before": "docs/validation/v0.5.13/step0/claim-hashes-before.json",
    "nr-a1-default": "docs/validation/v0.5.13/step1/claim-hashes-nr-a1-default.json",
    "nr-a1-t1": "docs/validation/v0.5.13/step1/claim-hashes-nr-a1-t1.json",
    "nr-a1-t4": "docs/validation/v0.5.13/step1/claim-hashes-nr-a1-t4.json",
}
COMPARATOR = "docs/validation/v0.5.13/tools/comparator.py"
INTERNAL_SELECTIONS = (
    "Internal selections were not assessed for margin (amendment 2, revision 6, section 4, first "
    "paragraph): comparisons whose outcome reaches the goldens only through a number or through a "
    "selection of data, cadences, peaks or models are not enumerated."
)
UNITS = {
    "src/refute/packs/tess/gauntlet.py:54:13": "SNR (dimensionless)",
    "src/refute/packs/tess/gauntlet.py:54:46": "SNR (dimensionless)",
    "src/refute/packs/tess/battery.py:835:7": "cadences",
    "src/refute/packs/tess/battery_v5.py:384:7": "days",
    "src/refute/packs/tess/battery_v5.py:523:13": "duration over period (dimensionless)",
}


def load(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def reason_class(row: dict) -> str:
    ops = row.get("operators", [])
    if any(o in ("Is", "IsNot") for o in ops):
        return "identity test"
    if any(o in ("In", "NotIn") for o in ops):
        return "membership test"
    if ops and ops[0] in ("name", "attribute", "subscript"):
        return "bare flag or truth value"
    if ops and ops[0] == "call":
        return "call used as a truth value"
    return "string or enum equality, or another non-numeric comparison"


def has_absent(loc) -> bool:
    if isinstance(loc, dict) and "if_key" in loc:
        return False
    return loc is None


def main() -> int:
    out = ROOT / sys.argv[1]
    layer = load(f"{L4}/decision-layer.json")
    reach = load(f"{L4}/reach-table.json")
    omap = load(f"{L4}/operand-map.json")
    keys = load(f"{L4}/schema-keys.json")
    parts = load(f"{L4}/comparator-schema-parts.json")
    union = {(r["file"], r["line"], r["col"]): r for r in layer["rows"]}
    missing, limits, fixtures_out, counts = [], [INTERNAL_SELECTIONS], {}, {}
    for fixture, rows in reach["fixtures"].items():
        chain = fixture.startswith("chain-")
        listed = []
        c = {"rows": 0, "non-numeric": 0, "reach-unknown": 0, "absent": 0, "assessable": 0,
             "assessable_integer_or_configuration": 0, "assessable_conditional": 0}  # fmt: skip
        for r in rows:
            key = f"{r['file']}:{r['line']}:{r['col']}"
            base = union.get((r["file"], r["line"], r["col"]), {})
            item = {"key": key, "function": r["function"], "expression": r["expression"],
                    "kind": r["kind"], "reach": r["reach"]}  # fmt: skip
            c["rows"] += 1
            if r["kind"] == "non-numeric":
                item.update({"class": "non-numeric", "reason_class": reason_class(base)})
                c["non-numeric"] += 1
            elif r["reach"] != "reached-if":
                item.update({"class": "reach-unknown", "reason": r.get("reason")})
                c["reach-unknown"] += 1
                limits.append(
                    f"{fixture}: {key} {r['expression']}: reach unknown: {r.get('reason')}"
                )
            else:
                entry = omap["rows"].get(key)
                if entry is None:
                    missing.append(f"{fixture}: {key} {r['expression']}")
                    continue
                spec = entry["fixtures"].get(fixture)
                if spec is None and chain:
                    spec = omap["chain_default"]
                if spec is None:
                    missing.append(f"{fixture}: {key} {r['expression']} (no fixture entry)")
                    continue
                item["alternatives"] = r.get("alternatives")
                if "reach_unknown" in spec:
                    item.update({"class": "reach-unknown", "reason": spec["reach_unknown"]})
                    c["reach-unknown"] += 1
                    limits.append(f"{fixture}: {key} {r['expression']}: reach unknown: "
                                  f"{spec['reach_unknown']}")  # fmt: skip
                elif "absent" in spec:
                    item.update({"class": "absent", "reason": spec["absent"]})
                    c["absent"] += 1
                    limits.append(f"{fixture}: {key} {r['expression']}: absent: {spec['absent']}")
                else:
                    item.update({
                        "class": "assessable", "row_class": entry["class"],
                        "producer": spec.get("producer"), "x": spec.get("x"), "t": spec.get("t"),
                        "units": UNITS.get(key, "counts" if entry["class"] != "finiteness"
                                           else "SNR (dimensionless)"),
                        "monotone": entry.get("monotone", "integer and configuration operands are "
                                              "not varied (decision H2(d))"),
                    })  # fmt: skip
                    c["assessable"] += 1
                    if entry["class"] == "integer-or-configuration":
                        c["assessable_integer_or_configuration"] += 1
                    if any(
                        isinstance(spec.get(k), dict) and "if_key" in spec[k] for k in ("x", "t")
                    ):
                        c["assessable_conditional"] += 1
            listed.append(item)
        fixtures_out[fixture] = listed
        counts[fixture] = c
    if missing:
        print(json.dumps({"missing_operand_entries": missing}, indent=1))
        return 1
    schema = {
        "labels": ["exploratory", "method_status: not_validated"],
        "json": parts["json"],
        "report": parts["report"],
        "exact_keys": keys["exact_keys"],
        "exact_subtree_keys": keys["exact_subtree_keys"],
    }
    manifest = {
        "labels": ["exploratory", "method_status: not_validated"],
        "rule": "see docs/validation/v0.5.13/tools/manifest.py and l4/README.md",
        "reach_rule": "docs/validation/v0.5.13/tools/reach.py (docstring); conditions output-ok, "
        "candidate-present, candidate-null, read only from each fixture's serialized "
        "non-numeric output after the freeze",
        "loop_rule": "a row inside a loop body, comprehension or generator is reach unknown in "
        "every fixture, counted once per fixture among the declared limits",
        "operand_syntax": omap["about"],
        "fixtures": fixtures_out,
        "declared_limits": limits,
        "n_declared_limits": len(limits),
        "counts": counts,
    }
    out.mkdir(parents=True, exist_ok=True)
    texts = {
        "manifest.json": json.dumps(manifest, indent=1) + "\n",
        "comparator-schema.json": json.dumps(schema, indent=1) + "\n",
    }
    for name, text in texts.items():
        (out / name).write_text(text, encoding="utf-8", newline="\n")
    settings = {}
    for label, rel in RECORDS.items():
        rec = load(rel)
        head = rec["provenance"]["head"]
        tree = subprocess.run(["git", "rev-parse", f"{head}:src"], cwd=ROOT, check=True,
                              capture_output=True, text=True).stdout.strip()  # fmt: skip
        settings[label] = {
            "record": rel,
            "record_sha256": sha((ROOT / rel).read_bytes()),
            "claim_record": CLAIM_RECORDS[label],
            "claim_record_sha256": sha((ROOT / CLAIM_RECORDS[label]).read_bytes()),
            "source_commit": head,
            "src_tree": tree,
            "files_sha256": rec["payload"]["files_sha256"],
            "error_outputs": rec["payload"]["error_outputs"],
        }
    freeze = {
        "labels": ["exploratory", "method_status: not_validated"],
        "fixtures": sorted(reach["fixtures"]),
        "settings": settings,
        "comparator": {"path": COMPARATOR, "sha256": sha((ROOT / COMPARATOR).read_bytes())},
        "schema": {"path": f"{L4}/comparator-schema.json",
                   "sha256": sha(texts["comparator-schema.json"].encode("utf-8"))},
        "manifest": {"path": f"{L4}/manifest.json",
                     "sha256": sha(texts["manifest.json"].encode("utf-8"))},
        "reach_table": {"path": f"{L4}/reach-table.json",
                        "sha256": sha((ROOT / f"{L4}/reach-table.json").read_bytes())},
        "operand_map": {"path": f"{L4}/operand-map.json",
                        "sha256": sha((ROOT / f"{L4}/operand-map.json").read_bytes())},
        "decision_layer": {"path": f"{L4}/decision-layer.json",
                           "sha256": sha((ROOT / f"{L4}/decision-layer.json").read_bytes())},
    }  # fmt: skip
    (out / "freeze.json").write_text(json.dumps(freeze, indent=1) + "\n", encoding="utf-8",
                                     newline="\n")  # fmt: skip
    print(json.dumps({"counts": counts, "n_declared_limits": len(limits),
                      "manifest_sha256": freeze["manifest"]["sha256"],
                      "schema_sha256": freeze["schema"]["sha256"]}))  # fmt: skip
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
