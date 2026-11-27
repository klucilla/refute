"""Compare identity records with ID-BEFORE (v0.5.13 charter, step 1 NR-A1, and step 5 ID-AFTER).

    unit compare-identity:  {python} -I -B docs/validation/v0.5.13/tools/compare_identity.py <set>

``<set>`` is ``nr-a1`` (the three settings nr-a1-default, nr-a1-t1 and nr-a1-t4, in
``step1/``) or ``after`` (``step5/``). For each record it compares, byte for byte, the protected
payload with ID-BEFORE's (``step0/golden-before.json`` and ``step0/claim-hashes-before.json``):
- the golden payload: every output file's SHA-256 and the list of error outputs;
- the claim payload: every claim's resolved hash.
Provenance (HEAD, versions, the BLAS record) is compared separately and reported, never as a
pass or fail of identity.

**The pin is verified** for a setting that pins the threads (t1, t4) only if every BLAS library
in the record's child-process ``threadpool_info`` reports that many threads.

**The outcome** (Codex r1, item 1, as written in the charter): a byte mismatch, a missing output or
an unverified pin stops Part A. A pin may be proposed only after all comparisons pass; its exact
diff then needs approval before any commit. The result goes to ``out/comparison-<set>.json``.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
V = ROOT / "docs" / "validation" / "v0.5.13"
SETTINGS = {"nr-a1-default": None, "nr-a1-t1": 1, "nr-a1-t4": 4}


def load(p: Path):
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None


def diff_map(a: dict, b: dict) -> dict:
    keys = sorted(set(a) | set(b))
    return {
        "missing": [k for k in keys if k not in b],
        "extra": [k for k in keys if k not in a],
        "differ": [k for k in keys if k in a and k in b and a[k] != b[k]],
    }


def compare(label: str, folder: Path, threads: int | None) -> dict:
    gb, cb = load(V / "step0/golden-before.json"), load(V / "step0/claim-hashes-before.json")
    g, c = load(folder / f"golden-{label}.json"), load(folder / f"claim-hashes-{label}.json")
    row: dict = {"label": label, "records_present": bool(g and c and gb and cb)}
    if not row["records_present"]:
        row["identity_equal"] = False
        return row
    gd = diff_map(gb["payload"]["files_sha256"], g["payload"]["files_sha256"])
    cd = diff_map(cb["payload"]["claims"], c["payload"]["claims"])
    row["golden"] = gd
    row["golden_error_outputs_equal"] = (
        gb["payload"]["error_outputs"] == g["payload"]["error_outputs"]
    )
    row["claims"] = cd
    row["identity_equal"] = (
        not any(gd.values()) and row["golden_error_outputs_equal"] and not any(cd.values())
    )
    blas = g["provenance"].get("blas", {})
    libs = blas.get("child_threadpool_info", [])
    row["blas"] = blas
    if threads is None:
        row["pin_verified"] = None
    else:
        row["pin_verified"] = bool(libs) and all(x.get("num_threads") == threads for x in libs)
    row["provenance_head"] = {"before": gb["provenance"]["head"], "this": g["provenance"]["head"]}
    return row


def main() -> int:
    which = sys.argv[1]
    if which == "nr-a1":
        rows = [compare(lab, V / "step1", t) for lab, t in SETTINGS.items()]
    elif which == "after":
        rows = [compare("after", V / "step5", None)]
    else:
        raise SystemExit("set must be nr-a1 or after")
    passed = all(r["identity_equal"] for r in rows) and all(
        r.get("pin_verified") in (None, True) for r in rows
    )
    doc = {
        "set": which,
        "labels": ["exploratory", "method_status: not_validated"],
        "rows": rows,
        "all_identity_equal_and_pins_verified": passed,
        "outcome": "every comparison passed: a pin may be proposed, its exact diff for approval"
        if passed
        else "STOP: a byte mismatch, a missing output or an unverified pin stops Part A",
    }
    out = Path(os.environ["REFUTE_RUN_OUT"])
    (out / f"comparison-{which}.json").write_text(json.dumps(doc, indent=1) + "\n", "utf-8")
    keys = ("label", "identity_equal", "pin_verified")
    print(json.dumps({"passed": passed, "rows": [{k: r.get(k) for k in keys} for r in rows]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
