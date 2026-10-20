"""The numbers of piece 4's three numeric criteria (map Amendment 11), for the record; the
decision is the tests'. Calls the helpers of ``tests/test_holdout_replicas.py`` (the same
operation, seeds and geometry) and writes ``piece4-numbers.json`` next to this file.

Run from the worktree root with the virtual environment's Python.
"""

import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]


def _tests():
    # an importable name, so the spawned workers (which get this sys.path) can unpickle the helpers
    sys.path.insert(0, str(ROOT / "tests"))
    return importlib.import_module("test_holdout_replicas")


def main():
    t = _tests()
    white = t._pool(t._var_rep, [(s, "white", None) for s in range(3000, 3200)])
    lc0, infos0 = t._hidden_lc(3000)
    _, _, replicas0, _ = t._geometry(infos0)
    analytic = t._analytic_median(lc0, replicas0)
    white_ratios = [math.sqrt(v) / analytic for v, _ in white]

    mc = t._pool(t._var_rep, [(s, "correlated", None) for s in range(4000, 4400)])
    positions = {}
    for _, depths in mc:
        for i, d in enumerate(depths):
            if d is not None:
                positions.setdefault(i, []).append(d)
    var_mc = float(np.median([np.var(v, ddof=1) for v in positions.values() if len(v) > 1]))
    ar1 = t._pool(t._var_rep, [(s, "correlated", None) for s in range(3000, 3200)])
    ar1_ratios = [v / var_mc for v, _ in ar1]

    pulls = np.asarray(
        t._pool(t._pull, [(s, "correlated", None) for s in range(3200, 3400)]), dtype=float
    )
    out = {
        "white": {"n": len(white_ratios), "median_ratio": float(np.median(white_ratios))},
        "ar1": {
            "n": len(ar1_ratios),
            "median_ratio": float(np.median(ar1_ratios)),
            "var_mc": var_mc,
            "n_replicas": len(replicas0),
        },
        "pulls": {
            "n": int(pulls.size),
            "frac_le_1": float(np.mean(np.abs(pulls) <= 1.0)),
            "frac_le_2": float(np.mean(np.abs(pulls) <= 2.0)),
            "median": float(np.median(pulls)),
        },
        "platform": sys.platform,
        "numpy": np.__version__,
    }
    (HERE / "piece4-numbers.json").write_text(
        json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
