"""v0.5.2 stage 2: the batched code that the frozen equivalence evaluation measured (commit 5b74c29)
against this tree, byte for byte, on the production path's defaults. A later change may add
options; it may not move a byte of what was evaluated. Development seeds; decides nothing else.

Usage: ``scripts/launch_affinity.ps1 -Script <this file> -Log .cache/v052/s2/fast-identity``;
writes ``fast-identity.json``. The evaluated module is read from git and loaded under its own name.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))
import a0v4  # noqa: E402

EVALUATED = "5b74c2971267dfde5ce10d27c3f310cedd38adaf"
CACHE = ROOT / ".cache/v052/s2/fast-identity"
LABEL = "refute-v052-dev:fast-identity"
NOISES = ("white", "correlated", "long", "correlated_trend")
PER_CELL = 25
WORKERS = 12


def evaluated_module():
    path = CACHE / "detrend_fast_evaluated.py"
    spec = importlib.util.spec_from_file_location("detrend_fast_evaluated", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["detrend_fast_evaluated"] = module
    spec.loader.exec_module(module)
    return module


def unit(arg):
    from refute.packs.tess import a0, a0_v4
    from refute.packs.tess import detrend_fast as now
    from refute.packs.tess import pipeline as pl

    old = evaluated_module()
    noise, sectors, i = arg
    key = f"{LABEL}:{noise}:{sectors}:{i}"
    seed = int(hashlib.sha256(key.encode()).hexdigest()[:16], 16)
    plan = a0v4._plan()
    lc, _ = a0v4.c.noise_curve(seed, noise, sectors)
    cand = a0v4.v3._candidate(lc.time, np.random.default_rng([seed, 1]))
    half = plan.detrend.transit_mask_half_width_durations * cand.duration
    mask = pl.transit_mask(lc.time, cand.period, cand.t0, half)
    a, b = (
        old.MaskAwareDetrender(lc, plan.detrend, mask),
        now.MaskAwareDetrender(lc, plan.detrend, mask),
    )
    pairs = [(a.flat(), b.flat())]
    h = a0.half_width(cand.duration, plan.gauntlet.events.baseline_outer_durations)
    layout = a0_v4.grid(pairs[0][1].time, pairs[0][1].sector, h)
    masks = a0_v4.comb_masks(lc.time, layout, h, half)
    pairs += [(a.flat(masks[j]), b.flat(masks[j])) for j in range(a0_v4.J)]
    values = lc.flux - np.median(lc.flux)
    add_a = old.AdditiveDetrender(lc.time, values, lc.sector, plan.detrend, mask)
    add_b = now.AdditiveDetrender(lc.time, values, lc.sector, plan.detrend, mask)
    same = all(
        x.time.tobytes() == y.time.tobytes()
        and x.flux.tobytes() == y.flux.tobytes()
        and x.flux_err.tobytes() == y.flux_err.tobytes()
        for x, y in pairs
    )
    return bool(same and add_a.residuals().tobytes() == add_b.residuals().tobytes())


def main() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    source = subprocess.run(
        ["git", "show", f"{EVALUATED}:src/refute/packs/tess/detrend_fast.py"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout
    (CACHE / "detrend_fast_evaluated.py").write_bytes(source)
    args = [(n, s, i) for n in NOISES for s in (2, 3, 4) for i in range(PER_CELL)]
    with ProcessPoolExecutor(max_workers=WORKERS) as pool:
        results = list(pool.map(unit, args, chunksize=4))
    out = {
        "label": "the evaluated batched code against this tree, byte for byte",
        "method_status": "not_validated",
        "evaluated_commit": EVALUATED,
        "evaluated_module_sha256": hashlib.sha256(source).hexdigest(),
        "curves": len(results),
        "identical": int(sum(results)),
        "passes": all(results),
    }
    (HERE / "fast-identity.json").write_text(
        json.dumps(out, indent=1, sort_keys=True) + "\n", "utf-8"
    )
    print(out, flush=True)


if __name__ == "__main__":
    main()
