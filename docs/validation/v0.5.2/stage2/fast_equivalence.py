"""v0.5.2 stage 2: the faster code against the reference code, under the criteria frozen in
``fast-detrend-equivalence.md``. Development seeds; ``method_status: not_validated``.

Usage: ``scripts/launch_affinity.ps1 -Script <this file> -Log .cache/v052/s2/fast-equivalence``;
writes ``fast-equivalence.json``.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))
import a0v4  # noqa: E402

v3 = a0v4.v3
c = v3.c
LABEL = "refute-v052-dev:fast-equivalence"
NOISES = ("white", "correlated", "long", "correlated_trend")
SECTORS = (2, 3, 4)
KINDS = ("full", "partial")
PER_CELL = 50
END_TO_END = 15
FLUX_TOLERANCE = 1e-11
NOISE_TOLERANCE = 1e-11
MEASURE_TOLERANCE = 1e-9
PULL_DECISION = 3.0
WORKERS = 12


def seed_of(noise, kind, sectors, i) -> int:
    text = f"{LABEL}:{noise}:{kind}:{sectors}:{i}"
    return int(hashlib.sha256(text.encode()).hexdigest()[:16], 16)


def _compare_flat(ref, fast) -> tuple[bool, float]:
    same = ref.time.size == fast.time.size and bool(np.array_equal(ref.time, fast.time))
    if not same:
        return False, float("inf")
    diff = max(
        float(np.max(np.abs(ref.flux - fast.flux), initial=0.0)),
        float(np.max(np.abs(ref.flux_err - fast.flux_err), initial=0.0)),
    )
    return True, diff


def _compare_noise(flat, mask, cand, plan):
    from refute.packs.tess import rednoise as rn
    from refute.packs.tess import rednoise_fast as rf

    same_runs = True
    keep = ~mask
    cadence = plan.data.exptime_seconds / 86400.0
    gap = plan.gauntlet.corrections.gap_split
    for s in np.unique(flat.sector):
        sel = flat.sector == s
        a = rn.segments(flat.time[sel], keep[sel], gap, cadence)
        b = rf.segments(flat.time[sel], keep[sel], gap, cadence)
        same_runs &= len(a) == len(b) and all(
            np.array_equal(x, y) for x, y in zip(a, b, strict=True)
        )
        bins_ref = rn.bins(flat.time[sel], keep[sel], 72, gap, cadence)
        bins_fast = rf.bin_matrix(flat.time[sel], keep[sel], 72, gap, cadence)
        same_runs &= len(bins_ref) == bins_fast.shape[0] and all(
            np.array_equal(x, y) for x, y in zip(bins_ref, bins_fast, strict=True)
        )
    a = rn.event_noise(flat, None, cand.period, cand.t0, cand.duration, plan)
    b = rf.event_noise(flat, None, cand.period, cand.t0, cand.duration, plan)
    flags_same = True
    worst = 0.0
    for x, y in ((a.box, b.box), (a.base, b.base)):
        for s, u in x.sectors.items():
            v = y.sectors[s]
            flags_same &= u.excluded == v.excluded and u.n_bins == v.n_bins
            for name in ("sigma_w", "sigma_n", "sigma_r2", "beta"):
                p, q = getattr(u, name), getattr(v, name)
                if math.isfinite(p) or math.isfinite(q):
                    worst = max(worst, abs(p - q))
    return same_runs, flags_same, worst


def _end_to_end(raw, cand, plan, prepared, ref_flat):
    """A0 through the reference code and through the fast code, compared."""
    from refute.packs.tess import a0_v4
    from refute.packs.tess import pipeline as pl
    from refute.packs.tess.events import per_event_depths
    from refute.packs.tess.rednoise import event_noise

    ev = plan.gauntlet.events
    mask = pl.transit_mask(raw.time, cand.period, cand.t0, prepared.half)

    def reference_flat(extra):
        return pl.detrend(raw, plan.detrend, mask=mask | extra)

    noise = event_noise(ref_flat, None, cand.period, cand.t0, cand.duration, plan)
    ref_events = per_event_depths(
        ref_flat, cand.period, cand.t0, cand.duration, c.CADENCE, ev, 0.0, None, noise
    )
    ref_measure = a0_v4.comb_measure(
        reference_flat, raw.time, ref_flat, cand.duration, prepared.half, ev, c.CADENCE
    )
    ref_measured, ref_windows, _ = a0_v4.empirical_events(
        ref_flat, cand, ref_events, ev, c.CADENCE, ref_measure, False
    )
    _, fast_measured, fast_windows, _ = a0v4.measured_of(prepared, cand, plan)
    out = {"availability": True, "branches": True, "validity": True, "decisions": True}
    worst = 0.0
    key = lambda w: (w.sector, w.index)  # noqa: E731 - local sort key
    a, b = sorted(ref_windows, key=key), sorted(fast_windows, key=key)
    if [key(w) for w in a] != [key(w) for w in b]:
        out["availability"] = False
    else:
        for u, v in zip(a, b, strict=True):
            out["branches"] &= u.stratum == v.stratum and u.segment == v.segment
            worst = max(worst, abs(u.value - v.value))
    if ref_measured.epochs.tolist() != fast_measured.epochs.tolist():
        out["availability"] = False
        return out, worst
    if len(ref_measured):
        worst = max(
            worst,
            float(np.max(np.abs(ref_measured.depths - fast_measured.depths))),
            float(np.max(np.abs(ref_measured.errors - fast_measured.errors))),
        )
    if not out["availability"] or len(ref_measured) == 0:
        return out, worst
    ref_stats, ref_pooled = v3._box_groups(ref_flat, cand, ref_measured, ref_windows, plan)
    fast_stats, fast_pooled = v3._box_groups(prepared.flat, cand, fast_measured, fast_windows, plan)
    out["branches"] &= ref_pooled == fast_pooled
    out["availability"] &= set(ref_stats) == set(fast_stats)
    for name in set(ref_stats) & set(fast_stats):
        (ra, re), (fa, fe) = ref_stats[name], fast_stats[name]
        out["validity"] &= (re is None) == (fe is None)
        if re is None or fe is None:
            continue
        worst = max(worst, abs(ra - fa), abs(re - fe))
        out["decisions"] &= (abs(ra / re) >= PULL_DECISION) == (abs(fa / fe) >= PULL_DECISION)
    return out, worst


def unit(arg):
    from refute.packs.tess import a0, a0_v4
    from refute.packs.tess import pipeline as pl

    noise, kind, sectors, i = arg
    plan = a0v4._plan()
    seed = seed_of(noise, kind, sectors, i)
    lc, _ = c.noise_curve(seed, noise, sectors)
    cand = v3._candidate(lc.time, np.random.default_rng([seed, 1]))
    raw = v3._apply_kind(lc, cand, plan, kind)
    prepared = a0v4.prepare(raw, cand, plan)
    mask = pl.transit_mask(raw.time, cand.period, cand.t0, prepared.half)
    ref_flat = pl.detrend(raw, plan.detrend, mask=mask)
    keeps, worst = _compare_flat(ref_flat, prepared.flat)
    h = a0.half_width(cand.duration, plan.gauntlet.events.baseline_outer_durations)
    layout = a0_v4.grid(ref_flat.time, ref_flat.sector, h)
    masks = a0_v4.comb_masks(raw.time, layout, h, prepared.half)
    for j in range(a0_v4.J):
        ok, diff = _compare_flat(
            pl.detrend(raw, plan.detrend, mask=mask | masks[j]), prepared.detrender.flat(masks[j])
        )
        keeps &= ok
        worst = max(worst, diff)
    flat_mask = pl.transit_mask(ref_flat.time, cand.period, cand.t0, prepared.half)
    runs_same, flags_same, noise_worst = _compare_noise(ref_flat, flat_mask, cand, plan)
    rec = {
        "keeps": bool(keeps),
        "flux_worst": worst,
        "runs_same": bool(runs_same),
        "noise_flags_same": bool(flags_same),
        "noise_worst": noise_worst,
    }
    if i < END_TO_END:
        checks, measure_worst = _end_to_end(raw, cand, plan, prepared, ref_flat)
        rec["end_to_end"] = {k: bool(v) for k, v in checks.items()}
        rec["measure_worst"] = measure_worst
    return rec


def main() -> None:
    args = [(n, k, s, i) for n in NOISES for s in SECTORS for k in KINDS for i in range(PER_CELL)]
    with ProcessPoolExecutor(max_workers=WORKERS) as pool:
        recs = list(pool.map(unit, args, chunksize=8))
    ends = [r for r in recs if "end_to_end" in r]
    out = {
        "label": "the faster code against the reference; development seeds",
        "method_status": "not_validated",
        "curves": len(recs),
        "curves_end_to_end": len(ends),
        "max_flux_difference": max(r["flux_worst"] for r in recs),
        "max_noise_difference": max(r["noise_worst"] for r in recs),
        "max_measurement_difference": max(r["measure_worst"] for r in ends),
        "criteria": {
            "cadences_kept_identical": all(r["keeps"] for r in recs),
            "flux_within_tolerance": all(r["flux_worst"] <= FLUX_TOLERANCE for r in recs),
            "runs_and_bins_identical": all(r["runs_same"] for r in recs),
            "noise_flags_identical": all(r["noise_flags_same"] for r in recs),
            "noise_within_tolerance": all(r["noise_worst"] <= NOISE_TOLERANCE for r in recs),
            "availability_identical": all(r["end_to_end"]["availability"] for r in ends),
            "branches_identical": all(r["end_to_end"]["branches"] for r in ends),
            "validity_identical": all(r["end_to_end"]["validity"] for r in ends),
            "decisions_identical": all(r["end_to_end"]["decisions"] for r in ends),
            "measurements_within_tolerance": all(
                r["measure_worst"] <= MEASURE_TOLERANCE for r in ends
            ),
        },
    }
    out["passes"] = all(out["criteria"].values())
    (HERE / "fast-equivalence.json").write_text(
        json.dumps(out, indent=1, sort_keys=True) + "\n", "utf-8"
    )
    print(json.dumps(out, indent=1, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
