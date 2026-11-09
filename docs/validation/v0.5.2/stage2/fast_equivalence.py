"""v0.5.2 stage 2: the faster code against the reference code, under the criteria frozen in
``fast-detrend-equivalence.md`` (revision 3, its single third run). Development seeds;
``method_status: not_validated``.

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
LABEL = "refute-v052-dev:fast-equivalence-r3"
NOISES = ("white", "correlated", "long", "correlated_trend")
SECTORS = (2, 3, 4)
KINDS = ("full", "partial")
PER_CELL = 50
END_TO_END = 15
FLUX_TOLERANCE = 1e-11
NOISE_TOLERANCE = 1e-11
MEASURE_TOLERANCE = 1e-9
METRIC_TOLERANCE = 1e-7
PULL_DECISION = 3.0
WORKERS = 12
SCENARIO_SEEDS = (13, 14)
# the three runs where revision 2 failed: regression cases, reported apart, not fresh evidence
REGRESSION = (("eb_equal", 4, False), ("single_year", 4, False), ("blend", 3, False))
WITH_CORRECTIONS = ("planet", "sinusoid")


def seed_of(noise, kind, sectors, i) -> int:
    text = f"{LABEL}:{noise}:{kind}:{sectors}:{i}"
    return int(hashlib.sha256(text.encode()).hexdigest()[:16], 16)


class Tally:
    """The largest absolute difference, refusing to absorb a non-finite value."""

    def __init__(self):
        self.worst = 0.0
        self.finite_same = True

    def add(self, a, b):
        a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
        fa, fb = np.isfinite(a), np.isfinite(b)
        if a.shape != b.shape or not np.array_equal(fa, fb):
            self.finite_same = False
            return
        if fa.any():
            self.worst = max(self.worst, float(np.max(np.abs(a[fa] - b[fb]))))


def _compare_flat(ref, fast, tally: Tally) -> bool:
    if ref.time.size != fast.time.size or not np.array_equal(ref.time, fast.time):
        tally.finite_same = False
        return False
    tally.add(ref.flux, fast.flux)
    tally.add(ref.flux_err, fast.flux_err)
    return True


def _compare_noise(flat, mask, cand, plan, tally: Tally):
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
    for x, y in ((a.box, b.box), (a.base, b.base)):
        for s, u in x.sectors.items():
            v = y.sectors[s]
            flags_same &= u.excluded == v.excluded and u.n_bins == v.n_bins
            for name in ("sigma_w", "sigma_n", "sigma_r2", "beta"):
                tally.add(getattr(u, name), getattr(v, name))
    return same_runs, flags_same


def _a0_side(flat, measure, cand, plan, exclude, noise_fn):
    from refute.packs.tess import a0_v4
    from refute.packs.tess.events import per_event_depths

    ev = plan.gauntlet.events
    noise = noise_fn(flat, None, cand.period, cand.t0, cand.duration, plan)
    events = per_event_depths(
        flat, cand.period, cand.t0, cand.duration, c.CADENCE, ev, 0.0, None, noise
    )
    measured, windows, _ = a0_v4.empirical_events(
        flat, cand, events, ev, c.CADENCE, measure, exclude
    )
    stats, pooled = ({}, {})
    if len(measured):
        stats, pooled = v3._box_groups(flat, cand, measured, windows, plan)
    return measured, windows, stats, pooled


def _end_to_end(raw, cand, plan, prepared, ref_flat, exclude, tally):
    """A0 through the reference code and through the fast code, compared."""
    from refute.packs.tess import a0_v4
    from refute.packs.tess import pipeline as pl
    from refute.packs.tess.rednoise import event_noise as reference_noise
    from refute.packs.tess.rednoise_fast import event_noise as fast_noise

    ev = plan.gauntlet.events
    mask = pl.transit_mask(raw.time, cand.period, cand.t0, prepared.half)

    def reference_flat(extra):
        return pl.detrend(raw, plan.detrend, mask=mask | extra)

    ref_measure = a0_v4.comb_measure(
        reference_flat, raw.time, ref_flat, cand.duration, prepared.half, ev, c.CADENCE
    )
    fast_measure = a0_v4.comb_measure(
        prepared.preprocess, raw.time, prepared.flat, cand.duration, prepared.half, ev, c.CADENCE
    )
    ref = _a0_side(ref_flat, ref_measure, cand, plan, exclude, reference_noise)
    fast = _a0_side(prepared.flat, fast_measure, cand, plan, exclude, fast_noise)
    out = {"availability": True, "branches": True, "validity": True, "decisions": True}
    key = lambda w: (w.sector, w.index)  # noqa: E731 - local sort key
    a, b = sorted(ref[1], key=key), sorted(fast[1], key=key)
    if [key(w) for w in a] != [key(w) for w in b]:
        out["availability"] = False
    else:
        for u, v in zip(a, b, strict=True):
            out["branches"] &= u.stratum == v.stratum and u.segment == v.segment
            tally.add(u.value, v.value)
    if ref[0].epochs.tolist() != fast[0].epochs.tolist():
        out["availability"] = False
        return out
    tally.add(ref[0].depths, fast[0].depths)
    tally.add(ref[0].errors, fast[0].errors)
    out["branches"] &= ref[3] == fast[3]
    out["availability"] &= set(ref[2]) == set(fast[2])
    for name in set(ref[2]) & set(fast[2]):
        (ra, re), (fa, fe) = ref[2][name], fast[2][name]
        out["validity"] &= (re is None) == (fe is None)
        if re is None or fe is None:
            continue
        tally.add([ra, re], [fa, fe])
        out["decisions"] &= (abs(ra / re) >= PULL_DECISION) == (abs(fa / fe) >= PULL_DECISION)
    return out


class ReferenceAdditive:
    """``detrend_fast.AdditiveDetrender``'s interface over ``battery.additive_residuals``."""

    def __init__(self, time, values, sector, params, base_mask):
        self.time, self.values, self.sector = time, values, sector
        self.base = base_mask

        class Plan:
            detrend = params

        self.plan = Plan

    def residuals(self, extra=None):
        from refute.packs.tess.battery import additive_residuals

        mask = self.base if extra is None else self.base | extra
        return additive_residuals(self.time, self.values, self.sector, mask, self.plan)

    def flat(self, extra=None):
        from refute.packs.tess.types import LightCurveData

        resid = self.residuals(extra)
        ok = np.isfinite(resid)
        count = int(ok.sum())
        return LightCurveData(
            self.time[ok], 1.0 + resid[ok], np.ones(count), self.sector[ok], np.zeros(count)
        )


class ReferenceDetrender:
    """``detrend_fast.MaskAwareDetrender``'s interface over the reference detrending."""

    def __init__(self, lc, params, base_mask=None):
        self.lc, self.params = lc, params
        self.base = np.zeros(len(lc), dtype=bool) if base_mask is None else base_mask

    def flat(self, extra=None):
        from refute.packs.tess import detrend as reference

        mask = self.base if extra is None else self.base | extra
        return reference.detrend(self.lc, self.params, mask=mask)


def _additive(raw, cand, plan, tally):
    from refute.packs.tess import a0_v4
    from refute.packs.tess import detrend_fast as df

    t, v, s = raw.time, raw.flux - np.median(raw.flux), raw.sector
    fast = a0_v4.a0_depth(t, v, s, cand, plan, 17)
    original = df.AdditiveDetrender
    df.AdditiveDetrender = ReferenceAdditive
    try:
        ref = a0_v4.a0_depth(t, v, s, cand, plan, 17)
    finally:
        df.AdditiveDetrender = original
    if (ref is None) != (fast is None):
        return False
    if ref is None:
        return True
    tally.add([ref.mean, ref.error], [fast.mean, fast.error])
    tally.add(ref.depths, fast.depths)
    return ref.epochs == fast.epochs and ref.n_events == fast.n_events


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
    flux = Tally()
    keeps = _compare_flat(ref_flat, prepared.flat, flux)
    h = a0.half_width(cand.duration, plan.gauntlet.events.baseline_outer_durations)
    layout = a0_v4.grid(ref_flat.time, ref_flat.sector, h)
    masks = a0_v4.comb_masks(raw.time, layout, h, prepared.half)
    for j in range(a0_v4.J):
        keeps &= _compare_flat(
            pl.detrend(raw, plan.detrend, mask=mask | masks[j]), prepared.preprocess(masks[j]), flux
        )
    noise_tally = Tally()
    flat_mask = pl.transit_mask(ref_flat.time, cand.period, cand.t0, prepared.half)
    runs_same, flags_same = _compare_noise(ref_flat, flat_mask, cand, plan, noise_tally)
    rec = {
        "keeps": bool(keeps),
        "flux_worst": flux.worst,
        "flux_finite": flux.finite_same,
        "runs_same": bool(runs_same),
        "noise_flags_same": bool(flags_same),
        "noise_worst": noise_tally.worst,
        "noise_finite": noise_tally.finite_same,
    }
    if i < END_TO_END:
        measure = Tally()
        checks = {}
        for exclude in (False, True):
            got = _end_to_end(raw, cand, plan, prepared, ref_flat, exclude, measure)
            for k, v in got.items():
                checks[k] = checks.get(k, True) and bool(v)
        checks["additive"] = bool(_additive(raw, cand, plan, measure))
        rec["end_to_end"] = checks
        rec["measure_worst"] = measure.worst
        rec["measure_finite"] = measure.finite_same
    return rec


def _numbers(a, b, path=""):
    """Every numeric leaf of two results as (path, a, b); a mismatch as (path, None, None)."""
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a) != set(b):
            yield (path + "/keys", None, None)
            return
        for k in a:
            yield from _numbers(a[k], b[k], f"{path}/{k}")
    elif isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        if len(a) != len(b):
            yield (path + "/len", None, None)
            return
        for i, (x, y) in enumerate(zip(a, b, strict=True)):
            yield from _numbers(x, y, f"{path}/{i}")
    elif isinstance(a, (bool, np.bool_)) or isinstance(b, (bool, np.bool_)):
        if bool(a) != bool(b):
            yield (path, None, None)
    elif isinstance(a, (int, float, np.integer, np.floating)) and isinstance(
        b, (int, float, np.integer, np.floating)
    ):
        yield (path, float(a), float(b))
    elif a != b:
        yield (path, None, None)


def scenario_unit(arg):
    from dataclasses import asdict

    from refute.packs.tess import detrend, detrend_fast, pipeline_v52, rednoise
    from refute.packs.tess import synthetic as syn
    from refute.packs.tess.params import TessTestPlan
    from refute.packs.tess.pipeline import analyze_data

    name, seed, corrections = arg
    raw = syn.discovery_v052_plan_dict()
    if corrections:
        raw["gauntlet"] = {"corrections": {"enabled": True, "version": 2}}
    plan = TessTestPlan.model_validate(raw)
    data = syn.scenario_data(name, seed=seed)
    fast = analyze_data(data, plan).tests
    saved = (
        detrend_fast.MaskAwareDetrender,
        detrend_fast.AdditiveDetrender,
        detrend_fast.detrend,
        pipeline_v52.event_noise,
    )
    detrend_fast.MaskAwareDetrender = ReferenceDetrender
    detrend_fast.AdditiveDetrender = ReferenceAdditive
    detrend_fast.detrend = detrend.detrend
    pipeline_v52.event_noise = rednoise.event_noise
    try:
        ref = analyze_data(data, plan).tests
    finally:
        (
            detrend_fast.MaskAwareDetrender,
            detrend_fast.AdditiveDetrender,
            detrend_fast.detrend,
            pipeline_v52.event_noise,
        ) = saved
    same_status, worst_ok, finite_ok = True, True, True
    problems = []
    if [t.name for t in ref] != [t.name for t in fast]:
        return {"scenario": f"{name}/{seed}/{corrections}", "ok": False, "problems": ["names"]}
    for a, b in zip(ref, fast, strict=True):
        if a.status != b.status or a.metrics.get("inconclusive_class") != b.metrics.get(
            "inconclusive_class"
        ):
            same_status = False
            problems.append(f"{a.name}: {a.status.value} against {b.status.value}")
        da, db = asdict(a), asdict(b)
        for key in ("metrics", "thresholds", "coverage", "sensitivity"):
            for path, x, y in _numbers(da.get(key), db.get(key), f"{a.name}/{key}"):
                if x is None:
                    finite_ok = False
                    problems.append(path)
                elif math.isfinite(x) != math.isfinite(y):
                    finite_ok = False
                    problems.append(path)
                elif math.isfinite(x) and abs(x - y) > METRIC_TOLERANCE * max(1.0, abs(x), abs(y)):
                    worst_ok = False
                    problems.append(f"{path}: {x} against {y}")
    return {
        "scenario": f"{name}/{seed}/{corrections}",
        "ok": bool(same_status and worst_ok and finite_ok),
        "status_same": bool(same_status),
        "metrics_within": bool(worst_ok),
        "finite_same": bool(finite_ok),
        "problems": problems[:12],
    }


def main() -> None:
    from refute.packs.tess import synthetic as syn

    args = [(n, k, s, i) for n in NOISES for s in SECTORS for k in KINDS for i in range(PER_CELL)]
    scenarios = [(n, sd, False) for n in syn.SCENARIOS for sd in SCENARIO_SEEDS]
    scenarios += [(n, SCENARIO_SEEDS[0], True) for n in WITH_CORRECTIONS]
    with ProcessPoolExecutor(max_workers=WORKERS) as pool:
        recs = list(pool.map(unit, args, chunksize=8))
        production = list(pool.map(scenario_unit, scenarios, chunksize=1))
        regression = list(pool.map(scenario_unit, REGRESSION, chunksize=1))
    ends = [r for r in recs if "end_to_end" in r]
    out = {
        "label": "the faster code against the reference; development seeds (revision 3)",
        "method_status": "not_validated",
        "curves": len(recs),
        "curves_end_to_end": len(ends),
        "scenarios": len(production),
        "max_flux_difference": max(r["flux_worst"] for r in recs),
        "max_noise_difference": max(r["noise_worst"] for r in recs),
        "max_measurement_difference": max(r["measure_worst"] for r in ends),
        "production": production,
        "regression_cases": regression,
        "criteria": {
            "cadences_kept_identical": all(r["keeps"] for r in recs),
            "flux_within_tolerance": all(r["flux_worst"] <= FLUX_TOLERANCE for r in recs),
            "runs_and_bins_identical": all(r["runs_same"] for r in recs),
            "noise_flags_identical": all(r["noise_flags_same"] for r in recs),
            "noise_within_tolerance": all(r["noise_worst"] <= NOISE_TOLERANCE for r in recs),
            "finite_classification_identical": all(
                r["flux_finite"] and r["noise_finite"] and r.get("measure_finite", True)
                for r in recs
            ),
            "availability_identical": all(r["end_to_end"]["availability"] for r in ends),
            "branches_identical": all(r["end_to_end"]["branches"] for r in ends),
            "validity_identical": all(r["end_to_end"]["validity"] for r in ends),
            "decisions_identical": all(r["end_to_end"]["decisions"] for r in ends),
            "additive_identical": all(r["end_to_end"]["additive"] for r in ends),
            "measurements_within_tolerance": all(
                r["measure_worst"] <= MEASURE_TOLERANCE for r in ends
            ),
            "production_identical": all(p["ok"] for p in production),
            "regression_cases_identical": all(p["ok"] for p in regression),
        },
    }
    out["passes"] = all(out["criteria"].values())
    (HERE / "fast-equivalence.json").write_text(
        json.dumps(out, indent=1, sort_keys=True) + "\n", "utf-8"
    )
    print(json.dumps({k: out[k] for k in ("passes", "criteria")}, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
