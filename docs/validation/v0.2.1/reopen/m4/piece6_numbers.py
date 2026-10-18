"""The numbers of piece 6's regime cases (map Amendment 21), for the record; the decision is the
tests'. Calls the helpers of ``tests/test_period_alias_rev4.py`` (the same constructions and
seeds) and writes ``piece6-numbers.json`` next to this file.

Run from the worktree root with the virtual environment's Python.
"""

import importlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
KEYS = ("z_f", "f", "g", "d_box", "d_box_err", "d_f", "beta_bar", "n_cadences", "reason")


def main():
    sys.path.insert(0, str(ROOT / "tests"))
    t = importlib.import_module("test_period_alias_rev4")
    cases = {
        "R1": lambda s, n: t._weak(s, n, 0.0),
        "R2": lambda s, n: t._weak(s, n, 0.25),
        "R3": lambda s, n: t._weak(s, n, None),
        "R4a": lambda s, n: t._box(s, n, None, t.S_STRONG),
        "R4b": lambda s, n: t._box(s, n, 0.0, t.S_STRONG),
    }
    out = {}
    for (case, noise), seed in t.SEEDS.items():
        r = t._run(cases[case](seed, noise))
        m = r.metrics
        row = {k: m.get(k) for k in KEYS}
        row.update(status=r.status.value, severity=r.severity.value, seed=seed)
        if row["d_box"] and row["d_box_err"]:
            row["s_realized"] = row["d_box"] / row["d_box_err"]
        out[f"{case}/{noise}"] = row
    path = HERE / "piece6-numbers.json"
    path.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for k, v in out.items():
        print(
            k,
            v["status"],
            {x: round(v[x], 3) for x in ("z_f", "f", "g", "beta_bar") if v[x] is not None},
        )


if __name__ == "__main__":
    main()
