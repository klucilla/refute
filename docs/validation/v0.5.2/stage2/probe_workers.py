"""v0.5.2 stage 2: the CPU per A0 version-4 unit at 1, 12 (one per physical core) and 22 workers,
on one development sample, through the batch driver. The design's section 8, route (1). It decides
nothing by itself. ``method_status: not_validated``.

Usage: ``scripts/launch_affinity.ps1 -Script <this file> -Log .cache/v052/s2/probe-workers``;
writes ``probe-workers.json``.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))
import a0v4  # noqa: E402
import driver  # noqa: E402

LABEL = "refute-v052-dev:a0v4-workers"
OUT = ROOT / ".cache/v052/s2/probe-workers"
if os.environ.get("REFUTE_PROBE_CHUNK"):
    from refute.packs.tess import detrend_fast

    detrend_fast.CHUNK_ROWS = int(os.environ["REFUTE_PROBE_CHUNK"])
SHARDS = int(os.environ.get("REFUTE_PROBE_SHARDS", "176"))  # more shards: less start-up weight
PER_SHARD = 4
SETTINGS = {1: None, 12: list(range(8, 32, 2)), 22: None}
if os.environ.get("REFUTE_PROBE_ONLY"):
    SETTINGS = {12: list(range(8, 32, 2))}
# The maintainer's decision of 2026-11-09 (1b): 12 pinned against 22, off business hours, in a
# separate record so that the first one (probe-workers.json) stays as it was.
RECORD = "probe-workers.json"
if os.environ.get("REFUTE_PROBE_12_22"):
    SETTINGS = {12: list(range(8, 32, 2)), 22: None}
    RECORD = "probe-workers-12-22.json"
# (section, shape, sectors, weight): roughly the acceptance's hours
MIX = (
    ("a08", "group", 2, 1), ("a08", "group", 3, 2), ("a08", "group", 4, 3),
    ("a08", "event", 2, 1), ("a05", None, 2, 1), ("a05", None, 3, 1), ("a05", None, 4, 1),
    ("a02", None, 3, 1),
)  # fmt: skip


def seed_of(key: str) -> int:
    return int(hashlib.sha256(f"{LABEL}:{key}".encode()).hexdigest()[:16], 16)


def args_of(index: int):
    v3 = a0v4.v3
    rng = np.random.default_rng(seed_of(f"pick:{index}"))
    noises, kinds = tuple(v3.c.NOISES_A0), tuple(v3.KINDS)
    table = [m for m in MIX for _ in range(m[3])]
    section, shape, sectors, _ = table[index % len(table)]
    seed = seed_of(f"unit:{index}")

    def pick(values):
        return values[int(rng.integers(len(values)))]

    if section == "a05":
        pattern = pick(("p1", "p2", "p3"))
        kind = "minimal" if pattern == "p3" else pick(kinds)
        arg = (pattern, pick(v3.SPACINGS), pick(("equal", "trend_one")), pick(noises), kind,
               sectors, index, seed)  # fmt: skip
    elif section == "a02":
        arg = ("a02", pick(noises), pick(kinds), sectors, index, seed)
    else:
        arg = (shape, pick(noises), pick(kinds), sectors, pick(v3.DEPTHS), index, seed)
    return section, arg


def shard(start: int) -> bytes:
    cpu = []
    for index in range(start, start + PER_SHARD):
        section, arg = args_of(index)
        before = os.times()
        a0v4.UNIT_OF[section](arg)
        after = os.times()
        cpu.append([after.user - before.user, after.system - before.system])
    return json.dumps(cpu).encode() + b"\n"


def measure(workers: int, pin) -> dict:
    out = OUT / f"w{workers}"
    if out.exists():
        if OUT.resolve() not in out.resolve().parents:
            raise SystemExit("refused: outside the probe's folder")
        shutil.rmtree(out)
    shards = [(f"s{i:04d}", i * PER_SHARD) for i in range(SHARDS)]
    started = time.monotonic()
    run = driver.Run(out, shard, shards, f"workers-{workers}", 10.0, workers, pin=pin,
                     batch_seconds=1800.0, max_shard_seconds=600.0)  # fmt: skip
    state = run.execute()
    if state != "complete":
        raise SystemExit(f"{workers} workers: {state}")
    wall = time.monotonic() - started
    cpu = []
    for sid, _ in shards:
        cpu += json.loads((out / "shards" / f"{sid}.bin").read_text("utf-8"))
    return {
        "workers": workers,
        "units": len(cpu),
        "cpu_seconds_per_unit": float(np.sum(cpu, axis=1).mean()),
        "user_seconds_per_unit": float(np.mean(cpu, axis=0)[0]),
        "kernel_seconds_per_unit": float(np.mean(cpu, axis=0)[1]),
        "wall_seconds": wall,
        "units_per_hour": len(cpu) / wall * 3600.0,
    }


def main() -> None:
    results = [measure(w, pin) for w, pin in SETTINGS.items()]
    base = results[0]["cpu_seconds_per_unit"]
    for r in results:
        r[f"cpu_ratio_to_{results[0]['workers']}_workers"] = r["cpu_seconds_per_unit"] / base
        print(r, flush=True)
    out = {
        "label": "CPU per unit by worker count; it decides nothing",
        "method_status": "not_validated",
        "results": results,
    }
    (HERE / RECORD).write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", "utf-8")


if __name__ == "__main__":
    main()
