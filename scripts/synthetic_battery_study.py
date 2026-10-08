"""Synthetic study of the v0.2 battery thresholds (no network, no real data).

Draws random synthetic cases with a fixed seed and runs the v0.2 battery with the
default thresholds against the injected (true) ephemeris:

- planet: a transit on the target, with random depth, noise, period, duration,
  stellar variability (sometimes at the planet's period) and an optional bright
  neighbor that carries no signal. Every battery failure here is a false alarm;
- blend: the signal is an eclipse on a neighbor 1.5 to 3 pixels away; the light
  curve is the crowding-corrected aperture photometry. A centroid or aperture
  failure is a detection;
- sinusoid: a pure sinusoid at the candidate period. A period-alias failure is a
  detection.

Usage (from the repository root):

    uv run python scripts/synthetic_battery_study.py --cases 200 --workers 30

It prints a Markdown table, written to docs/gauntlet-tess-v0.2-synthetic.md.
"""

from __future__ import annotations

import argparse
import os
import sys
from collections import Counter
from concurrent.futures import ProcessPoolExecutor

import numpy as np

SEED = 20261008
KINDS = ("planet", "blend", "sinusoid")
BATTERY = (
    "centroid_shift",
    "aperture_depth",
    "nearby_contamination",
    "period_alias",
    "systematics",
)


def run_case(args: tuple[str, int]) -> tuple[str, dict[str, str], dict[str, float]]:
    from refute.packs.tess.params import TessTestPlan
    from refute.packs.tess.pipeline import battery_tests
    from refute.packs.tess.synthetic import (
        TWO_YEARS,
        Scene,
        SignalSpec,
        make_aux,
        make_blend,
        make_data,
        make_lightcurve,
        make_star,
    )
    from refute.packs.tess.types import Candidate, LightCurveData, Neighbor

    kind, index = args
    rng = np.random.default_rng([SEED, KINDS.index(kind), index])
    period = float(rng.uniform(0.8, 9.0))
    duration = float(rng.uniform(1.0, 4.0)) / 24
    t0 = 1325.5 + float(rng.uniform(0, period))
    depth = float(10 ** rng.uniform(3, 4)) * 1e-6
    noise = float(rng.uniform(300, 1500))
    variability = float(rng.uniform(0, 0.003))
    var_period = period if rng.random() < 0.25 else float(rng.uniform(1, 10))
    seed = int(rng.integers(0, 2**31))
    star = make_star()
    info: dict[str, float] = {"depth_ppm": depth * 1e6, "noise_ppm": noise, "period": period}

    if kind == "planet":
        spec = SignalSpec(period, t0, depth, duration)
        lc, sectors = make_lightcurve(
            spec,
            noise_ppm=noise,
            trend_amplitude=variability,
            trend_period_days=var_period,
            seed=seed,
        )
        scene = Scene()
        neighbors = []
        if rng.random() < 0.5:
            sep = float(rng.uniform(1.5, 4.0))
            ratio = float(rng.uniform(0.05, 0.5))
            scene = Scene(neighbor_xy=(5.0 + sep, 5.0), neighbor_ratio=ratio)
            neighbors = [Neighbor(2, 10.0 - 2.5 * np.log10(ratio), sep * 21.0)]
        data = make_data(lc, sectors, star, aux=make_aux(lc, scene=scene, neighbors=neighbors))
    elif kind == "blend":
        sep = float(rng.uniform(1.5, 3.0))
        ratio = float(rng.uniform(0.1, 0.5))
        scene = Scene(neighbor_xy=(5.0 + sep, 5.0), neighbor_ratio=ratio)
        from refute.packs.tess.synthetic import crowding, psf_image, scene_aperture

        aperture = scene_aperture(scene)
        captured_t = float(psf_image(scene, scene.target_xy)[aperture].sum())
        captured_n = ratio * float(psf_image(scene, scene.neighbor_xy)[aperture].sum())
        eclipse = min(0.9, depth * crowding(scene) * (captured_t + captured_n) / captured_n)
        lc, sectors, aux = make_blend(
            SignalSpec(period, t0, eclipse, duration),
            scene=scene,
            sector_starts=TWO_YEARS,
            noise_ppm=noise,
            trend_amplitude=variability,
            seed=seed,
        )
        data = make_data(lc, sectors, star, aux=aux)
        info["eclipse_on_neighbor"] = eclipse
    else:
        lc, sectors = make_lightcurve(None, noise_ppm=noise, seed=seed)
        amplitude = depth
        wave = amplitude * np.sin(2 * np.pi * (lc.time - t0) / period + np.pi / 2)
        lc = LightCurveData(lc.time, lc.flux - wave, lc.flux_err, lc.sector, lc.year)
        duration = min(period / 4, 8 / 24)
        data = make_data(lc, sectors, star, aux=make_aux(lc, seed=seed))
    candidate = Candidate(period, t0, duration, depth, depth / 30, 30.0, 1.0, 10.0, 10)
    tests = battery_tests(data, candidate, TessTestPlan())
    return kind, {t.name: f"{t.status.value}/{t.severity.value}" for t in tests}, info


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--cases", type=int, default=200, help="cases per kind")
    parser.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    args = parser.parse_args()
    jobs = [(kind, i) for kind in KINDS for i in range(args.cases)]
    counts: dict[str, Counter] = {kind: Counter() for kind in KINDS}
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for kind, statuses, _info in pool.map(run_case, jobs, chunksize=4):
            for name, status in statuses.items():
                counts[kind][(name, status)] += 1
    lines = [
        "| Case | Test | PASS | FAIL fatal | FAIL warning | INCONCLUSIVE |",
        "|---|---|---|---|---|---|",
    ]
    for kind in KINDS:
        for name in BATTERY:
            c = counts[kind]
            fail_fatal = c[(name, "FAIL/fatal")]
            fail_warn = c[(name, "FAIL/warning")]
            inc = c[(name, "INCONCLUSIVE/fatal")] + c[(name, "INCONCLUSIVE/warning")]
            passed = c[(name, "PASS/fatal")] + c[(name, "PASS/warning")]
            lines.append(f"| {kind} | {name} | {passed} | {fail_fatal} | {fail_warn} | {inc} |")
    print(f"Seed {SEED}, {args.cases} cases per kind.\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
