"""Item 3 (c) of the maintainer's decision of 2026-11-08 (#208): the size left in the real pools
and how many confirmations they can sustain. It reads recorded files only (the frozen v0.5 pool
inputs and the v0.5 selection record); nothing is downloaded, and no seed or drand round is used.
It decides nothing.

The pools are rebuilt with the frozen code (``calib05.c3select.read_pools``) on the frozen inputs
of v0.5 (retrieved for its protocol; the catalogs have grown since, so a new confirmation would
rebuild them: a stop). Excluded, besides what v0.5 excluded (v0.1 to v0.4): every star v0.5's
selection walked (accepted, or rejected on its ordered walk) and, as the favourable variant, only
its accepted stars. A confirmation of the v0.5 design (8 stars + 3 ordered reserves per pool)
consumes one acceptance-walk: its size in the walk is ``(8 + 3) / acceptance rate``, the rate
measured on v0.5's walk. The TESS-EB rows are never printed or copied: only counts leave this
script (the license: calibration/v0.5/DATA_LICENSE.md).

Usage (from the project root): ``.venv/Scripts/python.exe <this file>``; writes ``pools.json``.
"""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
SELECTION = ROOT / "calibration/v0.5/selection/selection.json"
INPUTS = ROOT / "calibration/v0.5/inputs.json"
CACHE_CANDIDATES = (ROOT / ".cache/v05/inputs-attempts/attempt-01",)
NEED = 8 + 3


def main():
    from refute.packs.tess.calib05 import c3select

    selection = json.loads(SELECTION.read_text("utf-8"))
    inputs = json.loads(INPUTS.read_text("utf-8"))
    inputs_dir = next(p for p in CACHE_CANDIDATES if (p / "toi.csv").exists())
    built, known = c3select.read_pools(ROOT, inputs_dir, inputs)
    out = {
        "label": "development reading; it decides nothing",
        "source": "calibration/v0.5/selection/selection.json and the frozen v0.5 pool inputs",
        "known_targets_excluded_in_v05": len(known),
    }
    for kind, rows in built.items():
        p = selection["pools"][kind]
        walk = p["walk"]
        walked = {int(d["tic_id"]) for d in walk["decisions"]}
        accepted = {int(t) for t in walk["accepted"]}
        pool = {r.tic_id for r in rows}
        rate = len(accepted) / len(walked)
        left_all = len(pool - walked)
        left_accepted_only = len(pool - accepted)
        per_conf = NEED / rate
        reasons = Counter(
            str(d.get("reason"))[:48] for d in walk["decisions"] if int(d["tic_id"]) not in accepted
        )
        out[kind] = {
            "rejection_reasons_on_the_v05_walk": dict(sorted(reasons.items())),
            "pool_size_at_v05": len(pool),
            "recorded_pool_size": p["pool_size"],
            "walked_in_v05": len(walked),
            "accepted_in_v05": len(accepted),
            "acceptance_rate_on_the_v05_walk": rate,
            "left_excluding_every_walked_star": left_all,
            "left_excluding_only_the_accepted_stars": left_accepted_only,
            "stars_walked_per_confirmation_at_that_rate": per_conf,
            "confirmations_sustained_excluding_walked": math.floor(left_all / per_conf),
            "confirmations_sustained_excluding_accepted_only": math.floor(
                left_accepted_only / per_conf
            ),
        }
    (HERE / "pools.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", "utf-8")
    print(json.dumps(out, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
