"""v0.5.2 stage 2: the CPU per unit of A0 version 4, by section and sector count, on development
seeds, and the projection of the acceptance at ``T`` = 9,000 from the plasmode's schedule. It
decides nothing by itself (the design's section 8); ``method_status: not_validated``.

Usage: ``scripts/launch_affinity.ps1 -Script <this file> -Log .cache/v052/s2/probe-a0v4-cost``;
writes ``probe-a0v4-cost.json``.
"""

from __future__ import annotations

import hashlib
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
sys.path.insert(0, str(HERE))
import a0v4  # noqa: E402

TABLE = ROOT / ".cache/v052/s2/plasmode/components.pkl"
LABEL = "refute-v052-dev:a0v4-cost"
TARGET = 9000
PER_CELL = 24
SECTION_OF = {"a01": "a01", "a02": "a02", "a04": "a04", "a05": "a05", "a07": "a07", "a08e": "a08",
              "a08g": "a08"}  # fmt: skip


def seed_of(key: str) -> int:
    return int(hashlib.sha256(f"{LABEL}:{key}".encode()).hexdigest()[:16], 16)


def sample(section, shape, sectors, rng):
    """``PER_CELL`` units drawn over the section's cells of ``v3.schedule``, with development
    seeds (that schedule's own acceptance seeds are refused before a freeze, and never used)."""
    v3 = a0v4.v3
    noises, kinds = tuple(v3.c.NOISES_A0), tuple(v3.KINDS)

    def pick(values):
        return values[int(rng.integers(len(values)))]

    out = []
    for i in range(PER_CELL):
        key = f"{section}/{shape}/{sectors}/{i}"
        seed = seed_of(key)
        if section == "a01":
            arg = (pick(noises), pick(kinds), i, seed)
        elif section in ("a02", "a04"):
            arg = (section, pick(noises), pick(kinds), sectors, i, seed)
        elif section == "a07":
            arg = ("a07", "hetero", "mixed", sectors, i, seed)
        elif section == "a05":
            pattern = pick(("p1", "p2", "p3"))
            kind = "minimal" if pattern == "p3" else pick(kinds)
            arg = (pattern, pick(v3.SPACINGS), pick(("equal", "trend_one")), pick(noises), kind,
                   sectors, i, seed)  # fmt: skip
        elif shape == "group" and i % 8 == 0:
            arg = ("hetero", "hetero", "mixed", sectors, pick(v3.DEPTHS), i, seed)
        else:
            arg = (shape, pick(noises), pick(kinds), sectors, pick(v3.DEPTHS), i, seed)
        out.append((key, arg))
    return out


def cost(section, items):
    fn = a0v4.UNIT_OF[section]
    started = time.process_time()
    for _, arg in items:
        fn(arg)
    return (time.process_time() - started) / len(items)


def main() -> None:
    with TABLE.open("rb") as fh:
        table = pickle.load(fh)  # noqa: S301 - written by plasmode.py, in the local cache
    rng = np.random.default_rng(20261108)
    a0v4.v3._plan()
    per = {}
    for name in ("a01", "a02", "a04", "a05", "a07", "a08e", "a08g"):
        section = SECTION_OF[name]
        shape = {"a08e": "event", "a08g": "group"}.get(name)
        for sectors in (2,) if name in ("a01", "a08e") else (2, 3, 4):
            per[f"{name}/{sectors}"] = cost(section, sample(section, shape, sectors, rng))
            print(name, sectors, round(per[f"{name}/{sectors}"], 4), flush=True)
    hours: dict = {}
    curves: dict = {}
    for comp in table:
        factor = TARGET / comp["min_g"]
        for run in comp["runs"]:
            key = run["key"]
            section = key[0]
            units = int(math.ceil(run["n"].shape[0] * factor))
            sectors = next((k for k in key if isinstance(k, int)), 2)
            label = f"{section}/{sectors}" if f"{section}/{sectors}" in per else f"{section}/2"
            curves[section] = curves.get(section, 0) + units
            hours[section] = hours.get(section, 0.0) + units * per[label] / 3600.0
    out = {
        "label": "the CPU per unit of A0 version 4 and a projection; it decides nothing",
        "method_status": "not_validated",
        "target": TARGET,
        "cpu_seconds_per_unit_one_worker": per,
        "curves": curves,
        "cpu_hours_by_section": hours,
        "cpu_hours_total": float(sum(hours.values())),
        "workers": 1,
    }
    (HERE / "probe-a0v4-cost.json").write_text(
        json.dumps(out, indent=1, sort_keys=True) + "\n", "utf-8"
    )
    print({k: round(v, 1) for k, v in hours.items()}, round(out["cpu_hours_total"], 1), flush=True)


if __name__ == "__main__":
    main()
