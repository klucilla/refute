"""v0.5.12 step 3 (F-1): the cause of version 3's process-state dependence (the charter, step 3;
#218 comment 7199254242, item 3c). Exploratory and post hoc; it replaces nothing.

    launch_v3 unit f1: {python} -I -B docs/validation/v0.5.12/step3/f1_driver.py

Frozen before the first run (this file, ``f1_probe.py`` and the unit, committed together):
- **The source:** the commit the unit runs at (the journal's ``before`` entry records it); the
  environment is the project's ``.venv`` through ``launch_v3`` (processors 8 to 31, the job).
- **The seed check first:** ``git grep -w 2026112601`` over the tracked files, outside step 3's
  own files, must find nothing; otherwise the unit stops before any probe.
- **The factors, one at a time,** each with THREE fresh-process A/B pairs, A = ``none`` and B =
  the factor: ``workload`` (the conditioning workload), ``threads1`` (the thread counts),
  ``import_order``, ``misalign`` (the memory alignment of the arrays), ``random_state`` (the
  global random state). The floating-point control state is excluded (not settable from Python
  without third-party code). A factor is added only by a logged entry before its run.
- **"Found"** (the charter): the factor changes ``amplitude_snr`` in all three pairs, and the
  first differing stage (``f1_probe.py``'s stages 1 to 8) is the same in all three pairs: the
  first differing operation. Otherwise: "cause not found", with what was excluded.
- **The cap:** 0.8 CPU-h for the step (the unit's reservation is smaller).

It writes ``f1-result.json`` (every run's stages, every pair's differing stages, and the
outcome), copied to ``step3/``.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PROBE = "docs/validation/v0.5.12/step3/f1_probe.py"
FACTORS = ("workload", "threads1", "import_order", "misalign", "random_state")
PAIRS = 3


def seed_absent() -> list[str]:
    r = subprocess.run(
        ["git", "-C", str(ROOT), "grep", "-l", "-w", "2026112601"], capture_output=True, text=True
    )
    own = ("docs/validation/v0.5.12/step3/", "docs/validation/v0.5.12/units/f1")
    return [p for p in r.stdout.splitlines() if not p.startswith(own)]


def probe(cond: str, out_dir: Path, tag: str) -> dict:
    out = out_dir / f"{tag}.json"
    r = subprocess.run(
        [sys.executable, "-I", "-B", PROBE, cond, str(out)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        return {"condition": cond, "error": r.stderr[-2000:]}
    return json.loads(out.read_text(encoding="utf-8"))


def differing(a: dict, b: dict) -> list[str]:
    return [k for k in a["stages"] if a["stages"][k] != b["stages"].get(k)]


def main() -> int:
    found_elsewhere = seed_absent()
    if found_elsewhere:
        print(json.dumps({"refused": "the seed is in the repository", "files": found_elsewhere}))
        return 1
    out_dir = Path(os.environ["REFUTE_RUN_OUT"])
    runs, factors = [], {}
    t0 = time.time()
    for factor in FACTORS:
        pairs = []
        for i in range(PAIRS):
            a = probe("none", out_dir, f"{factor}-{i}-A")
            b = probe(factor, out_dir, f"{factor}-{i}-B")
            runs += [a, b]
            if "error" in a or "error" in b:
                pairs.append({"error": [a.get("error"), b.get("error")]})
                continue
            diff = differing(a, b)
            pairs.append(
                {
                    "differing_stages": diff,
                    "first_differing": diff[0] if diff else None,
                    "amplitude_snr": [a["amplitude_snr"], b["amplitude_snr"]],
                    "amplitude_snr_differs": a["amplitude_snr"] != b["amplitude_snr"],
                    "x_address_mod_64": [a["x_address_mod_64"], b["x_address_mod_64"]],
                }
            )
        firsts = {p.get("first_differing") for p in pairs}
        toggles = all(p.get("amplitude_snr_differs") for p in pairs)
        factors[factor] = {
            "pairs": pairs,
            "found": bool(toggles and len(firsts) == 1 and None not in firsts),
        }
    refs = [r for r in runs if r.get("condition") == "none" and "stages" in r]
    ref_consistent = all(r["stages"] == refs[0]["stages"] for r in refs) if refs else None
    found = [f for f, v in factors.items() if v["found"]]
    doc = {
        "schema": "refute-v0512-f1-1",
        "labels": ["exploratory", "post hoc", "method_status: not_validated"],
        "decision": "#218 comment 7199254242, item 3c; the charter, step 3",
        "seed": 2026112601,
        "excluded": ["the floating-point control state (not settable without third-party code)"],
        "reference_runs_identical": ref_consistent,
        "factors": factors,
        "outcome": f"found: {found}" if found else "cause not found",
        "wall_s": round(time.time() - t0, 1),
        "runs": runs,
    }
    (out_dir / "f1-result.json").write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"outcome": doc["outcome"], "reference_identical": ref_consistent}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
