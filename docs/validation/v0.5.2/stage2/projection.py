"""v0.5.2 stage 2: a first projection of the acceptance's processor-hours at the plasmode's sizes.
It uses the per-curve cost measured at one worker in stage 1 (``stage1/worksheet-probe.json``), a
measured cost of one detrending, and the design's four extra detrendings per curve per sector group
(a statement about the existing code, not a probe of version 4). It decides nothing; it exists so
that a projection above the hard maximum is seen before any code is written.
``method_status: not_validated``.

Usage (from the project root): ``.venv/Scripts/python.exe <this file>``; writes ``projection.json``.
"""

from __future__ import annotations

import json
import math
import pickle
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "docs/validation/v0.5.1/acceptance"))
TABLE = ROOT / ".cache/v052/s2/plasmode/components.pkl"
PROBE = HERE.parent / "stage1/worksheet-probe.json"
TARGETS = (8000, 9000, 10000)
PROBE_KIND = {"a01": "a01", "a02": "a02", "a04": "a02", "a05": "a05", "a07": "a02", "a08e": "a08",
              "a08g": "a08"}  # fmt: skip
A0R2_RATIO = {"a04": 0.622 / 2.039, "a07": 0.825 / 2.039}
EXTRA_DETRENDS = 4


def detrend_seconds(sectors: int) -> float:
    import a0 as runner

    from refute.packs.tess import pipeline as pl

    plan = runner._plan()
    lc, _ = runner.c.noise_curve(12345, "correlated", sectors)
    started = time.process_time()
    for _ in range(5):
        pl.detrend(lc, plan.detrend)
    return (time.process_time() - started) / 5.0


def main() -> None:
    with TABLE.open("rb") as fh:
        table = pickle.load(fh)  # noqa: S301 - written by plasmode.py, in the local cache
    probe = json.loads(PROBE.read_text("utf-8"))["scan"]
    one_worker = {k: v["1"]["cpu_seconds_per_unit"] for k, v in probe.items()}
    per_detrend = {s: detrend_seconds(s) for s in (2, 3, 4)}
    print("detrend seconds", per_detrend, "per-unit", one_worker, flush=True)
    out = {
        "label": "a first projection; it decides nothing",
        "method_status": "not_validated",
        "seconds_per_detrend_by_sectors": per_detrend,
        "cpu_seconds_per_unit_one_worker": one_worker,
        "by_target": {},
    }
    for target in TARGETS:
        curves: dict = {}
        hours_base: dict = {}
        hours_comb: dict = {}
        for comp in table:
            factor = target / comp["min_g"]
            for run in comp["runs"]:
                key = run["key"]
                section = key[0]
                units = int(math.ceil(run["n"].shape[0] * factor))
                sectors = next((k for k in key if isinstance(k, int)), 2)
                base = one_worker[PROBE_KIND[section]] * A0R2_RATIO.get(section, 1.0)
                extra = EXTRA_DETRENDS * per_detrend.get(sectors, per_detrend[4])
                curves[section] = curves.get(section, 0) + units
                hours_base[section] = hours_base.get(section, 0.0) + units * base / 3600.0
                hours_comb[section] = hours_comb.get(section, 0.0) + units * extra / 3600.0
        out["by_target"][str(target)] = {
            "curves": curves,
            "base_cpu_hours": hours_base,
            "comb_cpu_hours": hours_comb,
            "total_base": float(np.sum(list(hours_base.values()))),
            "total_with_comb": float(
                np.sum(list(hours_base.values())) + np.sum(list(hours_comb.values()))
            ),  # fmt: skip
        }
        print(target, {k: round(v, 1) for k, v in hours_base.items()},
              round(out["by_target"][str(target)]["total_with_comb"], 1), flush=True)  # fmt: skip
    (HERE / "projection.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", "utf-8")


if __name__ == "__main__":
    main()
