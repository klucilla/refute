"""The reference of case B2 of package 25 (map Amendment 25): the holdout rounds of the strong case
(seed 3500, the two-by-two layout, the M4 path with the default pair), computed with the code of
the commit before the package (4a26df7), so that B2 compares the package's default pair with the
code before it. Run with that commit's ``src`` first on the path (``PYTHONPATH`` set to a
checkout of 4a26df7's ``src``), with the virtual environment's Python, from the repository root.

Writes ``strong-rounds-4a26df7.json`` next to this file, with the machine it was computed on (the
round records' floats are bound to the platform, numpy and the CPU's SIMD features).
"""

import json
import sys
from pathlib import Path

import numpy as np

from refute.core.io import dumps_json, to_jsonable
from refute.packs.tess import synthetic
from refute.packs.tess.holdout import run_holdout
from refute.packs.tess.params import TessTestPlan

HERE = Path(__file__).resolve().parent


def _cpu_features():
    try:
        from numpy._core._multiarray_umath import __cpu_features__
    except ImportError:
        return []
    return sorted(k for k, v in __cpu_features__.items() if v)


def main():
    import refute

    plan = synthetic.fast_plan_dict()
    plan["gauntlet"] = {"corrections": {"version": 2, "enabled": True}}
    spec = synthetic.SignalSpec(
        period=synthetic.PLANET.period,
        t0=synthetic.PLANET.t0,
        depth=0.002,
        duration=synthetic.PLANET.duration,
    )
    lc, sectors = synthetic.make_lightcurve(
        spec, sector_starts=(1325.0, 1353.0, 2061.0, 2089.0), seed=3500
    )
    outcome = run_holdout(lc, sectors, TessTestPlan.model_validate(plan))
    rounds = json.loads(dumps_json(to_jsonable([r.to_dict() for r in outcome.rounds])))
    out = {
        "note": "the rounds of case B2 with the code of 4a26df7 (before package 25)",
        "code": str(Path(refute.__file__).resolve().parents[1]).replace(str(Path.home()), "~"),
        "platform": sys.platform,
        "numpy": np.__version__,
        "python": list(sys.version_info[:2]),
        "cpu_features": _cpu_features(),
        "rounds": rounds,
    }
    path = HERE / "strong-rounds-4a26df7.json"
    path.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(path)


if __name__ == "__main__":
    main()
