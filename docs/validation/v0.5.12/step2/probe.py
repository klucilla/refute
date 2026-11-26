"""v0.5.12 step 2 (#223): the standalone baseline probe, outside pytest's collection (Codex's
round 2, item 3, in the charter's step 2). It evaluates every case of ``cases.json`` on the
approval code (``src/`` unchanged since ``f18d6f8``) and writes each assertion's outcome.

    launch_v3 unit step2-probe:
        {python} -I -B docs/validation/v0.5.12/step2/probe.py

A failed assertion is "documented" only if ``cases.json`` names it, with the value the approval
code was expected to give, before this probe runs. Any other failure is reported and the probe
exits 1: the work stops.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tests"))
import v0512_case_eval as ev  # noqa: E402

SRC = "src/refute/packs/tess/screen_d5.py"


def main() -> int:
    doc = ev.load()
    by_id = {c["id"]: c for c in doc["cases"]}
    head = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()
    src_sha = hashlib.sha256((ROOT / SRC).read_bytes()).hexdigest()
    rows, undocumented, documented_failed, passed = [], [], [], 0
    for case in doc["cases"]:
        for o in ev.evaluate(case, by_id):
            o = {"case": case["id"], **o}
            if o["ok"]:
                passed += 1
                o["outcome"] = "pass"
            elif ev.documented_match(case, o):
                documented_failed.append(o)
                o["outcome"] = "documented failure"
            else:
                undocumented.append(o)
                o["outcome"] = "UNDOCUMENTED FAILURE"
            rows.append(o)
    named = [(c["id"], d["assertion"]) for c in doc["cases"] for d in c["documented"]]
    seen = {(o["case"], o["assertion"]) for o in documented_failed}
    out = {
        "schema": "refute-v0512-step2-probe",
        "labels": ["exploratory", "method_status: not_validated"],
        "head": head,
        "screen_d5_sha256": src_sha,
        "cases_sha256": hashlib.sha256(ev.CASES.read_bytes()).hexdigest(),
        "assertions": len(rows),
        "passed": passed,
        "documented_failures": len(documented_failed),
        "documented_but_passed": sorted(set(named) - seen),
        "undocumented_failures": len(undocumented),
        "rows": rows,
    }
    path = Path(os.environ["REFUTE_RUN_OUT"]) / "probe-result.json"
    path.write_text(json.dumps(out, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")
    brief = {k: out[k] for k in ("assertions", "passed", "documented_failures")}
    brief["undocumented"] = [(o["case"], o["assertion"], o["got"]) for o in undocumented]
    brief["documented_but_passed"] = out["documented_but_passed"]
    print(json.dumps(brief, default=str))
    return 1 if undocumented or out["documented_but_passed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
