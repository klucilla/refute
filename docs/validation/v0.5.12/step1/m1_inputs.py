"""#222, M1's input identity, before any F1 call (charter, section 4; Codex's round 2, item 4):
freeze the batch's realized-input hashes and recipe, and check them against prior records.

    launch_v2 unit m1-inputs: {python} -I -B docs/validation/v0.5.12/step1/m1_inputs.py

- **The batch:** the seven families and seeds 1 to 3000 (``m1_common.py``), 21,000 cases. Each
  case's identity is the SHA-256 of its time, flux and ``flux_err`` arrays as little-endian
  float64.
- **The prior records:** v0.5.11's ``step1/f1-calibration.json`` holds no input hashes, so its 400
  cases' inputs are regenerated from its recorded recipe (``make_lightcurve(PLANET, seed=s)``,
  white and with ``CORRELATED_PROFILE``, seeds 1 to 200) and hashed. This regenerates inputs only:
  no F1 runs, so it is not a rerun. There is no earlier batch of this phase.
- **The check:** no M1 identity may equal a prior one, and no two M1 cases may share one. Any match,
  or any unresolved identity, fails the unit, and the work stops.

It writes ``m1-inputs.json``: the recipe, the per-family list of the 3,000 hashes in seed order,
the 400 prior hashes, and the result. The launcher copies it to ``step1/``.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m1_common as mc  # noqa: E402

SEEDS = range(1, 3001)


def main() -> int:
    # imported here: ruff sorts refute differently inside and outside the container
    from refute.packs.tess.synthetic import CORRELATED_PROFILE, PLANET, make_lightcurve

    g = mc.geometry()
    batch = {}
    for fam in mc.FAMILIES:
        batch[fam] = [mc.input_sha256(*mc.curve(g, fam, s)) for s in SEEDS]
    prior = []
    for kwargs in ({}, dict(CORRELATED_PROFILE)):
        for s in range(1, 201):
            lc, _ = make_lightcurve(PLANET, seed=s, **kwargs)
            t, f, e = (np.asarray(x, dtype=float) for x in (lc.time, lc.flux, lc.flux_err))
            prior.append(mc.input_sha256(t, f, e))
    every = [h for hs in batch.values() for h in hs]
    clash_prior = sorted(set(every) & set(prior))
    duplicates = len(every) - len(set(every))
    ok = not clash_prior and duplicates == 0 and len(every) == 7 * len(SEEDS)
    here = Path(__file__).resolve().parent
    doc = {
        "schema": "refute-v0512-m1-inputs-1",
        "labels": ["exploratory", "method_status: not_validated"],
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "recipe": {
            "common_sha256": hashlib.sha256((here / "m1_common.py").read_bytes()).hexdigest(),
            "families": list(mc.FAMILIES),
            "seeds": [SEEDS.start, SEEDS.stop - 1],
            "stream": mc.STREAM,
            "numpy": np.__version__,
            "cadences": {"T": g["t_idx"], "B": g["b_idx"], "N": int(g["t"].size)},
        },
        "batch_sha256": batch,
        "prior_v0511_f1_calibration_sha256": prior,
        "clashes_with_prior": clash_prior,
        "duplicates_in_batch": duplicates,
        "passed": ok,
    }
    out = Path(os.environ["REFUTE_RUN_OUT"]) / "m1-inputs.json"
    out.write_text(json.dumps(doc, indent=0) + "\n", encoding="utf-8", newline="\n")
    summary = {"passed": ok, "cases": len(every), "clashes": len(clash_prior)}
    summary["duplicates"] = duplicates
    print(json.dumps(summary))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
