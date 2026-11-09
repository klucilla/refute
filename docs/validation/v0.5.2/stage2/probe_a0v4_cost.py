"""v0.5.2 stage 2: the CPU per unit of A0 version 4, by section and sector count, measured at the
acceptance's own placement (12 workers, one per physical core), on development seeds, and the
projection of the acceptance at ``T`` = 9,000 from the plasmode's schedule. It decides nothing by
itself (the design's section 8); ``method_status: not_validated``.

Usage: ``scripts/launch_affinity.ps1 -Script <this file> -Log .cache/v052/s2/probe-a0v4-cost``;
writes ``probe-a0v4-cost.json``.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import pickle
import shutil
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))
import a0v4  # noqa: E402
import driver  # noqa: E402

TABLE = ROOT / ".cache/v052/s2/plasmode/components.pkl"
OUT = ROOT / ".cache/v052/s2/probe-a0v4-cost-run"
LABEL = "refute-v052-dev:a0v4-cost"
TARGET = 9000
PER_CELL = 48
PER_SHARD = 6
WORKERS = 12
PIN = list(range(8, 32, 2))
SECTION_OF = {"a01": "a01", "a02": "a02", "a04": "a04", "a05": "a05", "a07": "a07", "a08e": "a08",
              "a08g": "a08"}  # fmt: skip
CELLS = [
    (name, sectors)
    for name in SECTION_OF
    for sectors in ((2,) if name in ("a01", "a08e") else (2, 3, 4))
]


def seed_of(key: str) -> int:
    return int(hashlib.sha256(f"{LABEL}:{key}".encode()).hexdigest()[:16], 16)


def arg_of(name, sectors, i, rng):
    """One unit drawn over the section's cells of ``v3.schedule``, with a development seed (that
    schedule's own acceptance seeds are refused before a freeze, and never used)."""
    v3 = a0v4.v3
    noises, kinds = tuple(v3.c.NOISES_A0), tuple(v3.KINDS)
    section = SECTION_OF[name]
    shape = {"a08e": "event", "a08g": "group"}.get(name)
    seed = seed_of(f"{name}/{sectors}/{i}")

    def pick(values):
        return values[int(rng.integers(len(values)))]

    if section == "a01":
        return (pick(noises), pick(kinds), i, seed)
    if section in ("a02", "a04"):
        return (section, pick(noises), pick(kinds), sectors, i, seed)
    if section == "a07":
        return ("a07", "hetero", "mixed", sectors, i, seed)
    if section == "a05":
        pattern = pick(("p1", "p2", "p3"))
        kind = "minimal" if pattern == "p3" else pick(kinds)
        return (pattern, pick(v3.SPACINGS), pick(("equal", "trend_one")), pick(noises), kind,
                sectors, i, seed)  # fmt: skip
    if shape == "group" and i % 8 == 0:
        return ("hetero", "hetero", "mixed", sectors, pick(v3.DEPTHS), i, seed)
    return (shape, pick(noises), pick(kinds), sectors, pick(v3.DEPTHS), i, seed)


def shard(spec) -> bytes:
    name, sectors, start = spec
    rng = np.random.default_rng(seed_of(f"pick/{name}/{sectors}/{start}"))
    fn = a0v4.UNIT_OF[SECTION_OF[name]]
    cpu = []
    for i in range(start, start + PER_SHARD):
        before = os.times()
        fn(arg_of(name, sectors, i, rng))
        after = os.times()
        cpu.append((after.user - before.user) + (after.system - before.system))
    return json.dumps(cpu).encode() + b"\n"


def main() -> None:
    with TABLE.open("rb") as fh:
        table = pickle.load(fh)  # noqa: S301 - written by plasmode.py, in the local cache
    if OUT.exists():
        if OUT.resolve().parent != (ROOT / ".cache/v052/s2").resolve():
            raise SystemExit("refused: outside the probe's folder")
        shutil.rmtree(OUT)
    shards = [
        (f"{name}-{sectors}-{start:04d}", (name, sectors, start))
        for name, sectors in CELLS
        for start in range(0, PER_CELL, PER_SHARD)
    ]
    run = driver.Run(OUT, shard, shards, "a0v4-cost", 10.0, WORKERS, pin=PIN)
    state = run.execute()
    if state != "complete":
        raise SystemExit(state)
    per: dict[str, list] = {}
    for sid, (name, sectors, _) in shards:
        per.setdefault(f"{name}/{sectors}", []).extend(
            json.loads((OUT / "shards" / f"{sid}.bin").read_text("utf-8"))
        )
    means = {k: float(np.mean(v)) for k, v in per.items()}
    hours: dict = {}
    curves: dict = {}
    for comp in table:
        factor = TARGET / comp["min_g"]
        for item in comp["runs"]:
            key = item["key"]
            section = key[0]
            units = int(math.ceil(item["n"].shape[0] * factor))
            sectors = next((k for k in key if isinstance(k, int)), 2)
            label = f"{section}/{sectors}" if f"{section}/{sectors}" in means else f"{section}/2"
            curves[section] = curves.get(section, 0) + units
            hours[section] = hours.get(section, 0.0) + units * means[label] / 3600.0
    total = float(sum(hours.values()))
    out = {
        "label": "the CPU per unit of A0 version 4 and a projection; it decides nothing",
        "method_status": "not_validated",
        "target": TARGET,
        "workers": WORKERS,
        "cpu_seconds_per_unit": means,
        "curves": curves,
        "cpu_hours_by_section": hours,
        "cpu_hours_total": total,
        "wall_hours_at_12_workers": total / WORKERS,
    }
    (HERE / "probe-a0v4-cost.json").write_text(
        json.dumps(out, indent=1, sort_keys=True) + "\n", "utf-8"
    )
    print({k: round(v, 1) for k, v in hours.items()}, round(total, 1), flush=True)


if __name__ == "__main__":
    main()
