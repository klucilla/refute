"""M2's and the sensitivity control's input identity, before any F1 call (charter, section 4;
Codex's round 2, item 4; step 4, items 6 and 7; #218 comment 7199254242, item 3a).

    launch_v3 unit m2-inputs: {python} -I -B docs/validation/v0.5.12/step4/m2_inputs.py

- **The batches** (``step1/m1_common.py``, unchanged since M1's inputs were frozen):
  - M2: the seven families, seeds 100001 to 103000 (21,000 cases);
  - the control: the seven families, seeds 200001 to 200300 (2,100 cases), the odd box depth
    increased by ``5 * sqrt(1/sum(w_odd) + 1/sum(w_even))`` with ``w = 1/sigma^2`` over each
    parity's in-transit cadences (the charter's step 4, item 7).
- **The prior records and earlier phase batches:**
  - v0.5.11's step 1 calibration (400 cases, regenerated from its recipe, inputs only);
  - M1's 21,000 frozen hashes (``step1/m1-inputs.json``);
  - the exploratory checks' curves of the same recipe, regenerated (inputs only): check 1 (null
    500001 to 501000, sensitivity 600001 to 600300), check 2 (700001 to 701000, 800001 to
    800300), and check 3's cells without red noise for M1's seven families (null 20263001 to
    20264000, sensitivity 20268001 to 20268300).
- **The check:** no M2 or control identity equals a prior one, and none repeats inside or across
  the two batches. Any match or unresolved identity fails the unit, and the work stops.

It writes ``m2-inputs.json`` (the recipe, the per-family hashes of both batches in seed order,
the control's added depth per family, the prior counts and the result), copied to ``step4/``.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "step1"))
import m1_common as mc  # noqa: E402

M2_SEEDS = range(100001, 103001)
CONTROL_SEEDS = range(200001, 200301)


def control_extra(g: dict, fam: str) -> float:
    k = np.floor((g["t"] - mc.T0) / mc.P + 0.5)
    odd_in = g["intr"] & (np.mod(k, 2) == 1)
    even_in = g["intr"] & (np.mod(k, 2) == 0)
    w = 1.0 / mc.sigmas(g, fam) ** 2
    return 5.0 * math.sqrt(1.0 / w[odd_in].sum() + 1.0 / w[even_in].sum())


def main() -> int:
    # imported here: ruff sorts refute differently inside and outside the container
    from refute.packs.tess.synthetic import CORRELATED_PROFILE, PLANET, make_lightcurve

    g = mc.geometry()
    extra = {fam: control_extra(g, fam) for fam in mc.FAMILIES}
    m2 = {fam: [mc.input_sha256(*mc.curve(g, fam, s)) for s in M2_SEEDS] for fam in mc.FAMILIES}
    control = {
        fam: [
            mc.input_sha256(*mc.curve(g, fam, s, depth_odd_extra=extra[fam])) for s in CONTROL_SEEDS
        ]
        for fam in mc.FAMILIES
    }
    prior = set()
    for kwargs in ({}, dict(CORRELATED_PROFILE)):
        for s in range(1, 201):
            lc, _ = make_lightcurve(PLANET, seed=s, **kwargs)
            t, f, e = (np.asarray(x, dtype=float) for x in (lc.time, lc.flux, lc.flux_err))
            prior.add(mc.input_sha256(t, f, e))
    n_v0511 = len(prior)
    m1 = json.loads((HERE.parent / "step1" / "m1-inputs.json").read_text(encoding="utf-8"))
    m1_hashes = {h for hs in m1["batch_sha256"].values() for h in hs}
    prior |= m1_hashes
    checks = 0
    for null, sens in (
        (range(500001, 501001), range(600001, 600301)),
        (range(700001, 701001), range(800001, 800301)),
        (range(20263001, 20264001), range(20268001, 20268301)),
    ):
        for fam in mc.FAMILIES:
            for s in null:
                prior.add(mc.input_sha256(*mc.curve(g, fam, s)))
                checks += 1
            for s in sens:
                prior.add(mc.input_sha256(*mc.curve(g, fam, s, depth_odd_extra=extra[fam])))
                checks += 1
    every = [h for hs in m2.values() for h in hs] + [h for hs in control.values() for h in hs]
    clashes = sorted(set(every) & prior)
    duplicates = len(every) - len(set(every))
    expected = 7 * (len(M2_SEEDS) + len(CONTROL_SEEDS))
    ok = not clashes and duplicates == 0 and len(every) == expected
    doc = {
        "schema": "refute-v0512-m2-inputs-1",
        "labels": ["exploratory", "method_status: not_validated"],
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "recipe": {
            "common_sha256": hashlib.sha256(
                (HERE.parent / "step1" / "m1_common.py").read_bytes()
            ).hexdigest(),
            "families": list(mc.FAMILIES),
            "m2_seeds": [M2_SEEDS.start, M2_SEEDS.stop - 1],
            "control_seeds": [CONTROL_SEEDS.start, CONTROL_SEEDS.stop - 1],
            "control_odd_depth_extra": extra,
            "stream": mc.STREAM,
            "numpy": np.__version__,
        },
        "m2_sha256": m2,
        "control_sha256": control,
        "prior_counts": {
            "v0511_f1_calibration": n_v0511,
            "m1": len(m1_hashes),
            "exploratory_checks_regenerated": checks,
        },
        "clashes_with_prior": clashes,
        "duplicates_in_batches": duplicates,
        "passed": ok,
    }
    out = Path(os.environ["REFUTE_RUN_OUT"]) / "m2-inputs.json"
    out.write_text(json.dumps(doc, indent=0) + "\n", encoding="utf-8", newline="\n")
    brief = {"passed": ok, "cases": len(every), "clashes": len(clashes)}
    brief.update({"duplicates": duplicates, "prior": doc["prior_counts"]})
    print(json.dumps(brief))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
