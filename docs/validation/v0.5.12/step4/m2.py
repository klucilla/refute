"""#222, the measurement M2 and the sensitivity control (v0.5.12 charter, step 4, items 6 and 7;
#218 comment 7199254242, item 3a), on the corrected F1 of the ``src/`` commit 6f83a91.

    launch_v3 unit m2:       {python} -I -B docs/validation/v0.5.12/step4/m2.py m2
    launch_v3 unit m2-control: {python} -I -B docs/validation/v0.5.12/step4/m2.py control

- **The cases:** ``step1/m1_common.py`` (M1's recipe, unchanged), the seven families.
  - M2: seeds 100001 to 103000.
  - The control: seeds 200001 to 200300, the odd box depth increased by the per-family value
    frozen in ``step4/m2-inputs.json``.
  Before any F1 call, every case's input is rebuilt and its SHA-256 must equal the frozen hash in
  ``step4/m2-inputs.json`` (committed before this run); any mismatch stops the unit before F1.
- **The call:** ``refute.packs.tess.screen_d5.f1_box(time, flux, flux_err, 3.7, 1326.3, 2.5/24)``.
- **The rules, per family, unchanged:**
  - M2 (step 1's rule): pass if 0 ``not_assessed`` and the 95 % Wilson score upper bound of the
    fail rate is at most 1 % (at most 19 ``fail`` of 3000);
  - the control: pass if 0 ``not_assessed`` and at least 281 ``fail`` of 300.
  Every family must pass. M1's results are kept and reported beside M2's.
- **Workers:** a process pool of at most 10 workers (business hours), inside the launcher's job
  (processors 8 to 31).

Outputs, copied by the launcher to ``step4/``: ``<batch>-summary.json`` and
``<batch>-<family>.json`` (per seed: the state and OE_box). Labels: exploratory,
``method_status: not_validated``.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "step1"))
import m1_common as mc  # noqa: E402

Z = 1.959963984540054
WORKERS = 10
BATCHES = {
    "m2": {"seeds": range(100001, 103001), "key": "m2_sha256"},
    "control": {"seeds": range(200001, 200301), "key": "control_sha256"},
}


def wilson(k: int, n: int) -> tuple[float, float]:
    p = k / n
    den = 1 + Z * Z / n
    centre = p + Z * Z / (2 * n)
    half = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n))
    return (centre - half) / den, (centre + half) / den


def work(task):
    from refute.packs.tess.screen_d5 import f1_box

    family, seeds, frozen, extra = task
    g = mc.geometry()
    out = []
    for seed, want in zip(seeds, frozen, strict=True):
        t, f, s = mc.curve(g, family, seed, depth_odd_extra=extra)
        if mc.input_sha256(t, f, s) != want:
            raise SystemExit(f"refused: the input of {family} seed {seed} is not the frozen one")
        r = f1_box(t, f, s, mc.P, mc.T0, mc.T)
        out.append((seed, r["state"], r["metrics"].get("oe_box"), r["reason"]))
    return out


def main() -> int:
    batch = sys.argv[1]
    spec = BATCHES[batch]
    frozen_doc = json.loads((HERE / "m2-inputs.json").read_text(encoding="utf-8"))
    if not frozen_doc["passed"]:
        raise SystemExit("refused: the frozen inputs did not pass their identity check")
    common = hashlib.sha256((HERE.parent / "step1" / "m1_common.py").read_bytes()).hexdigest()
    if frozen_doc["recipe"]["common_sha256"] != common:
        raise SystemExit("refused: m1_common.py differs from the one the inputs were frozen with")
    seeds = list(spec["seeds"])
    tasks = []
    for fam in mc.FAMILIES:
        hashes = frozen_doc[spec["key"]][fam]
        extra = frozen_doc["recipe"]["control_odd_depth_extra"][fam] if batch == "control" else None
        for i in range(0, len(seeds), 300):
            tasks.append((fam, seeds[i : i + 300], hashes[i : i + 300], extra))
    t0 = time.time()
    results = {fam: [] for fam in mc.FAMILIES}
    with ProcessPoolExecutor(max_workers=WORKERS) as pool:
        for task, rows in zip(tasks, pool.map(work, tasks), strict=True):
            results[task[0]].extend(rows)
    out_dir = Path(os.environ["REFUTE_RUN_OUT"])
    summary = {}
    for fam in mc.FAMILIES:
        rows = sorted(results[fam])
        n = len(rows)
        fails = sum(r[1] == "fail" for r in rows)
        unassessed = sum(r[1] == "not_assessed" for r in rows)
        lo, hi = wilson(fails, n)
        entry = {
            "n": n,
            "pass": sum(r[1] == "pass" for r in rows),
            "fail": fails,
            "not_assessed": unassessed,
            "oe_box_over_2": sum(r[2] is not None and r[2] > 2 for r in rows),
            "wilson_95": [lo, hi],
        }
        if batch == "m2":
            entry["family_passes"] = unassessed == 0 and hi <= 0.01 and n == len(seeds)
        else:
            entry["family_passes"] = unassessed == 0 and fails >= 281 and n == len(seeds)
        summary[fam] = entry
        reasons = sorted({r[3] for r in rows if r[1] == "not_assessed"})
        doc = {
            "family": fam,
            "batch": batch,
            "labels": ["exploratory", "method_status: not_validated"],
        }
        doc["not_assessed_reasons"] = reasons
        doc["cases"] = [{"seed": r[0], "state": r[1], "oe_box": r[2]} for r in rows]
        (out_dir / f"{batch}-{fam}.json").write_text(json.dumps(doc) + "\n", encoding="utf-8")
    passed = all(v["family_passes"] for v in summary.values())
    rule = (
        "per family: 0 not_assessed and the 95% Wilson upper bound of the fail rate <= 1% (at most "
        "19 fail of 3000)"
        if batch == "m2"
        else "per family: 0 not_assessed and at least 281 fail of 300"
    )
    doc = {
        "schema": f"refute-v0512-{batch}-1",
        "labels": ["exploratory", "method_status: not_validated"],
        "src_commit": "6f83a91",
        "rule": rule + "; it passes if every family passes",
        "families": summary,
        "passed": passed,
        "wall_s": round(time.time() - t0, 1),
        "workers": WORKERS,
    }
    text = json.dumps(doc, indent=1) + "\n"
    (out_dir / f"{batch}-summary.json").write_text(text, encoding="utf-8", newline="\n")
    brief = {fam: (v["fail"], v["not_assessed"]) for fam, v in summary.items()}
    print(json.dumps({"batch": batch, "passed": passed, "fail_notassessed": brief}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
