"""v0.5.2 stage 2: which member failed in the nested plasmode datasets, and by how much. It redraws
each nested dataset from its own seed (the draw comes first from each component's generator, so
the data are the same bytes as in the nested run), applies the critical value that the nested run
recorded for that dataset, and reports every member that is not certified: its key, the estimates,
the half-widths and the bound it crossed. Development records only; it decides nothing.
``method_status: not_validated``. ``plasmode-diag.json`` records the run on the table of the first
evaluation, whose component order was not yet stable; the rebuilt table, sorted, has other seeds
per component, so this script reproduces that file only with that table.

Usage: ``launch_affinity.ps1 -Script <this file> -Arguments 9000:<fp>,10000:<fp>`` (``fp``: the
run's fingerprint folder).
"""

from __future__ import annotations

import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import plasmode as pm  # noqa: E402

WORKERS = 12


def inspect(arg):
    """The members of one dataset that are not certified at the recorded critical value."""
    target, rep, q = arg
    table = pm._load()
    out = []
    for c, comp in enumerate(table):
        rng = np.random.default_rng(pm.seed_of("nested", target, rep, c))
        data = pm.draw(comp, target, rng)
        ok = pm.certified(data, q, target)
        if ok.all():
            continue
        m, v, se_m2, se_v2, g = pm.estimates(pm.features(*data[:3]).sum(axis=1))
        for j in np.flatnonzero(~ok):
            half_m, half_v = q * float(np.sqrt(se_m2[j])), q * float(np.sqrt(se_v2[j]))
            out.append(
                {
                    "target": target,
                    "rep": rep,
                    "q": q,
                    "component": c,
                    "member": repr(comp["members"][j]),
                    "source_min_g": comp["min_g"],
                    "m": float(m[j]),
                    "half_m": half_m,
                    "v": float(v[j]),
                    "half_v": half_v,
                    "g": float(g[j]),
                    "crossed": [
                        name
                        for name, bad in (
                            ("g", g[j] < pm.G_MIN_FRACTION * target),
                            ("mean", abs(m[j]) + half_m >= pm.MEAN_TOL),
                            ("v_low", v[j] - half_v <= pm.LO_V),
                            ("v_high", v[j] + half_v >= pm.HI_V),
                        )
                        if bad
                    ],
                }
            )
    return out


def main() -> None:
    work = []
    for item in sys.argv[1:]:
        target, fp = item.split(":")
        folder = pm.OUT / f"nested-{target}" / fp / "shards"
        for path in sorted(folder.glob("*.bin")):
            row = json.loads(path.read_bytes())
            work.append((int(target), row["rep"], row["q"], row["fails"]))
    with ProcessPoolExecutor(WORKERS, initializer=pm._load) as pool:
        found = list(pool.map(inspect, [w[:3] for w in work]))
    for w, rows in zip(work, found, strict=True):
        if len(rows) != w[3]:
            raise SystemExit(f"redrawn {w[0]} rep {w[1]}: {len(rows)} failures, recorded {w[3]}")
    flat = [row for rows in found for row in rows]
    target = HERE / "plasmode-diag.json"
    target.write_text(json.dumps(flat, indent=1, sort_keys=True) + "\n", "utf-8")
    for row in flat:
        print(json.dumps(row, sort_keys=True), flush=True)
    print("datasets", len(work), "failing members", len(flat), flush=True)


if __name__ == "__main__":
    main()
