"""#222, the measurement M1 (v0.5.12 charter, step 1, pre-registered there at 7df389c).

    launch_v2 unit m1: {python} -I -B docs/validation/v0.5.12/step1/m1.py

With the project's code at the approval commit, it counts how often F1 gives ``fail`` on
equal-depth curves whose sigma is correct but unequal.
- **The cases:** the seven families and seeds 1 to 3000 of ``m1_common.py``. Before any F1 call,
  every case's input is rebuilt and its SHA-256 must equal the frozen hash in
  ``step1/m1-inputs.json`` (committed before this run); any mismatch stops the unit before F1.
- **The call:** ``refute.packs.tess.screen_d5.f1_box(time, flux, flux_err, 3.7, 1326.3, 2.5/24)``.
- **The rule, per family:** pass if 0 ``not_assessed`` and at most 19 ``fail`` of 3000, i.e. the
  95 % Wilson score upper bound of the rejection rate is at most 1 % (z = 1.959963984540054).
- **Workers:** a process pool of at most 10 workers (business hours), BelowNormal, inside the
  container's job (processors 8 to 31).

Outputs, copied by the launcher to ``step1/``: ``m1-summary.json`` (per family: the counts of
``pass``, ``fail`` and ``not_assessed``, of OE_box > 2, the Wilson upper bound, and the family's
outcome; the overall outcome) and ``m1-<family>.json`` (per seed: the state and OE_box). Labels:
exploratory, ``method_status: not_validated``. A rule written after this run is post hoc.
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
sys.path.insert(0, str(HERE))
import m1_common as mc  # noqa: E402

SEEDS = range(1, 3001)
Z = 1.959963984540054
LIMIT = 0.01
WORKERS = 10


def wilson_upper(k: int, n: int) -> float:
    p = k / n
    den = 1 + Z * Z / n
    centre = p + Z * Z / (2 * n)
    half = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n))
    return (centre + half) / den


def work(task: tuple[str, list[int], list[str]]) -> list[tuple[int, str, float | None, str]]:
    from refute.packs.tess.screen_d5 import f1_box

    family, seeds, frozen = task
    g = mc.geometry()
    out = []
    for seed, want in zip(seeds, frozen, strict=True):
        t, f, s = mc.curve(g, family, seed)
        if mc.input_sha256(t, f, s) != want:
            raise SystemExit(f"refused: the input of {family} seed {seed} is not the frozen one")
        r = f1_box(t, f, s, mc.P, mc.T0, mc.T)
        out.append((seed, r["state"], r["metrics"].get("oe_box"), r["reason"]))
    return out


def main() -> int:
    frozen_doc = json.loads((HERE / "m1-inputs.json").read_text(encoding="utf-8"))
    if not frozen_doc["passed"]:
        raise SystemExit("refused: the frozen inputs did not pass their identity check")
    common = hashlib.sha256((HERE / "m1_common.py").read_bytes()).hexdigest()
    if frozen_doc["recipe"]["common_sha256"] != common:
        raise SystemExit("refused: m1_common.py differs from the one the inputs were frozen with")
    tasks = []
    seeds = list(SEEDS)
    for fam in mc.FAMILIES:
        hashes = frozen_doc["batch_sha256"][fam]
        for i in range(0, len(seeds), 300):
            tasks.append((fam, seeds[i : i + 300], hashes[i : i + 300]))
    t0 = time.time()
    results: dict[str, list] = {fam: [] for fam in mc.FAMILIES}
    with ProcessPoolExecutor(max_workers=WORKERS) as pool:
        for task, rows in zip(tasks, pool.map(work, tasks), strict=True):
            results[task[0]].extend(rows)
    summary = {}
    out_dir = Path(os.environ["REFUTE_RUN_OUT"])
    for fam in mc.FAMILIES:
        rows = sorted(results[fam])
        n = len(rows)
        fails = sum(r[1] == "fail" for r in rows)
        unassessed = sum(r[1] == "not_assessed" for r in rows)
        over2 = sum(r[2] is not None and r[2] > 2 for r in rows)
        upper = wilson_upper(fails, n)
        summary[fam] = {
            "n": n,
            "pass": sum(r[1] == "pass" for r in rows),
            "fail": fails,
            "not_assessed": unassessed,
            "oe_box_over_2": over2,
            "wilson_upper_95": upper,
            "family_passes": unassessed == 0 and upper <= LIMIT and n == len(SEEDS),
        }
        per_seed = [{"seed": r[0], "state": r[1], "oe_box": r[2]} for r in rows]
        reasons = sorted({r[3] for r in rows if r[1] == "not_assessed"})
        doc = {"family": fam, "labels": ["exploratory", "method_status: not_validated"]}
        doc.update({"not_assessed_reasons": reasons, "cases": per_seed})
        (out_dir / f"m1-{fam}.json").write_text(json.dumps(doc) + "\n", encoding="utf-8")
    passed = all(v["family_passes"] for v in summary.values())
    doc = {
        "schema": "refute-v0512-m1-1",
        "labels": ["exploratory", "method_status: not_validated"],
        "rule": "per family: 0 not_assessed and the 95% Wilson upper bound of the fail rate <= 1% "
        "(at most 19 fail of 3000); M1 passes if every family passes",
        "families": summary,
        "passed": passed,
        "wall_s": round(time.time() - t0, 1),
        "workers": WORKERS,
    }
    text = json.dumps(doc, indent=1) + "\n"
    (out_dir / "m1-summary.json").write_text(text, encoding="utf-8", newline="\n")
    brief = {}
    for fam, v in summary.items():
        brief[fam] = (v["fail"], v["not_assessed"], round(v["wilson_upper_95"], 5))
    print(json.dumps({"passed": passed, "fail_notassessed_wilson": brief}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
