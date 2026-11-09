"""v0.5.2 stage 2: the A0 units of battery version 4, on development seeds.

The units of the v0.5.1 runner (``docs/validation/v0.5.1/acceptance/a0.py``, which is not changed
and whose curves, kinds and helpers are reused) with version 4's measurement: the mask-aware
preprocessing of ``detrend_fast.MaskAwareDetrender``, each pseudo-window measured under its own
comb (``a0_v4``), the noise model of ``rednoise_fast``, the additive path of ``a0_v4.a0_depth``,
and the box statistics of the odd/even family (``matched_*`` left the family). A real event's
series is the pipeline's: the transit-masked detrending of the raw curve.
``method_status: not_validated``.
"""

from __future__ import annotations

import math
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "docs/validation/v0.5.1/acceptance"))
import a0 as v3  # noqa: E402

c = v3.c
_plan = v3._plan
# A0.8's median error inflation is a reported diagnostic with no criterion: one unit in this many
INFLATION_EVERY = 16


def prepare(raw, cand, plan, reuse=None, changed=None):
    """The pipeline's own preprocessing (``a0_v4.prepare``); this runner's plan has no corrections,
    so no global components."""
    from refute.packs.tess import a0_v4

    if plan.gauntlet.corrections.active:
        raise ValueError("this runner's plan has no active corrections")
    return a0_v4.prepare(raw, cand, plan, reuse=reuse, changed=changed)


def events_of(flat, cand, plan, phase=0.0):
    from refute.packs.tess.events import per_event_depths
    from refute.packs.tess.rednoise_fast import event_noise

    noise = event_noise(flat, None, cand.period, cand.t0, cand.duration, plan)
    return per_event_depths(
        flat, cand.period, cand.t0, cand.duration, c.CADENCE, plan.gauntlet.events, phase, None,
        noise,
    )  # fmt: skip


def measure_of(p, cand, plan):
    from refute.packs.tess import a0_v4

    return a0_v4.comb_measure(
        p.preprocess, p.raw.time, p.flat, cand.duration, p.half, plan.gauntlet.events, c.CADENCE
    )


def measured_of(p, cand, plan, events=None, exclude=False):
    from refute.packs.tess import a0_v4

    events = events_of(p.flat, cand, plan) if events is None else events
    measured, windows, details = a0_v4.empirical_events(
        p.flat, cand, events, plan.gauntlet.events, c.CADENCE, measure_of(p, cand, plan), exclude
    )
    return events, measured, windows, details


def unit_a01(arg):
    noise, kind, _i, seed = arg
    plan = _plan()
    lc, _ = c.noise_curve(seed, noise, 2)
    cand = v3._candidate(lc.time, np.random.default_rng([seed, 1]))
    p = prepare(v3._apply_kind(lc, cand, plan, kind), cand, plan)
    events, measured, windows, details = measured_of(p, cand, plan)
    metas = v3._metas(p.flat, cand, measured, plan)
    pulls = [
        (m.stratum, float(d) / float(e))
        for m, d, e in zip(metas, measured.depths, measured.errors, strict=True)
    ]
    return {
        "noise": noise,
        "kind": kind,
        "period": cand.period,
        "pulls": pulls,
        "n_events": len(events),
        "not_measured": int(measured.dropped.get("a0_not_measured", 0)),
        "a03": v3._a03(p.flat, cand, windows, measured, details, plan, False),
        "missing_lags": v3._missing_lags(details),
    }


def pixel_stats(lc, cand, plan, seed):
    """``v3._pixel_stats`` through ``a0_v4.a0_depth``: the same pixels and SAP, the same seeds."""
    from refute.packs.tess import a0_v4, power
    from refute.packs.tess import battery_v51_diff as v51d
    from refute.packs.tess import synthetic as syn
    from refute.packs.tess.battery import _dilate, aperture_series, core_aperture

    rng = np.random.default_rng([seed, 11])
    scene = syn.Scene()
    params = plan.gauntlet.aperture_depth
    out = {}
    ts, diffs, secs = [], [], []
    for s in np.unique(lc.sector):
        sel = lc.sector == s
        px = syn.render_pixels(int(s), lc.time[sel], lc.flux[sel], scene, rng)
        core = core_aperture(px, params.core_radius_pixels)
        large = _dilate(px.aperture, params.dilation_pixels) & np.isfinite(px.flux).all(axis=0)
        t_c, f_c, _, _ = aperture_series(px, core)
        t_l, f_l, _, _ = aperture_series(px, large)
        common, i_c, i_l = np.intersect1d(t_c, t_l, return_indices=True)
        ts.append(common)
        diffs.append(f_l[i_l] / np.median(f_l[i_l]) - f_c[i_c] / np.median(f_c[i_c]))
        secs.append(np.full(common.size, int(s)))
    seed_ap = power.candidate_seed("aperture_depth", cand)
    g = a0_v4.a0_depth(
        np.concatenate(ts), np.concatenate(diffs), np.concatenate(secs), cand, plan, seed_ap + 2
    )
    if g is not None:
        out["large_minus_core"] = (g.mean, g.error)
    sigma = float(np.median(lc.flux_err))
    aux = syn.make_sector_aux(lc, syn.crowding(scene), rng)
    aux = [replace(a, sap_flux=a.sap_flux + rng.normal(0.0, sigma, a.sap_flux.size)) for a in aux]
    usable = [a for a in aux if v51d.sap_applicability(a)[0]]
    if usable:
        t_u = np.concatenate([a.time for a in usable])
        s_u = np.concatenate([np.full(a.time.size, a.sector) for a in usable])
        r = np.concatenate(
            [
                v51d._normalized(a.sap_flux) - a.crowdsap * v51d._normalized(a.pdcsap_flux)
                for a in usable
            ]
        )
        seed_sy = power.candidate_seed("systematics", cand)
        g = a0_v4.a0_depth(t_u, r, s_u, cand, plan, seed_sy + 1)
        if g is not None:
            out["sap_minus_expected"] = (g.mean, g.error)
    return out, len(usable)


def unit_group(arg):
    """A0.2 (with pixels), A0.4, A0.7: (row, noise, kind, sectors, i, seed)."""
    row, noise, kind, sectors, _i, seed = arg
    plan = _plan()
    rng = np.random.default_rng([seed, 1])
    if row == "a07":
        lc, cand = v3._hetero_curve(seed, sectors, plan)
    else:
        lc, _ = c.noise_curve(
            seed, noise, sectors, trend_sectors=(1,) if row in ("a04", "a04b") else None
        )
        cand = v3._candidate(lc.time, rng)
        lc = v3._apply_kind(lc, cand, plan, kind)
    p = prepare(lc, cand, plan)
    events, measured, windows, details = measured_of(p, cand, plan)
    metas = v3._metas(p.flat, cand, measured, plan)
    stats, pooled = v3._box_groups(p.flat, cand, measured, windows, plan)
    rec = {
        "row": row,
        "noise": noise,
        "kind": kind,
        "sectors": sectors,
        "period": cand.period,
        "stratum": v3._lowest([m.stratum for m in metas]),
        "n_events": len(measured),
        "not_measured": int(measured.dropped.get("a0_not_measured", 0)),
        "strata_of_events": sorted({m.stratum for m in metas}),
        "shortcut": {str(k): bool(v) for k, v in pooled.items()},
        "pulls": v3._pulls(stats),
    }
    if row == "a02":
        pix, n_usable = pixel_stats(p.raw, cand, plan, seed)
        rec["pulls"].update(v3._pulls(pix))
        rec["sap_usable_sectors"] = n_usable
        rec["a03"] = v3._a03(p.flat, cand, windows, measured, details, plan, False)
    if row == "a07":
        forced, _ = v3._box_groups(p.flat, cand, measured, windows, plan, pooled_all=True)
        rec["pulls_forced_pooling"] = v3._pulls(forced)
        rec["r_diff"] = v3._r_diffs(windows)
    return rec


def unit_a05(arg):
    pattern, spacing, combo, noise, kind, sectors, _i, seed = arg
    plan = _plan()
    lc, _ = c.noise_curve(
        seed, noise, sectors, trend_sectors=(1,) if combo == "trend_one" else None
    )
    cand = v3._candidate(lc.time, np.random.default_rng([seed, 1]), period=spacing)
    lc = v3._apply_kind(lc, cand, plan, "p3" if pattern == "p3" else kind)
    if pattern == "p1":
        lc = v3._cut_one_odd(lc, cand, plan)
    p = prepare(lc, cand, plan)
    events, measured, windows, _ = measured_of(p, cand, plan)
    metas = v3._metas(p.flat, cand, measured, plan)
    idx = list(range(len(measured)))
    if pattern == "p2":
        idx = v3._two_against_three(measured)
    if pattern == "p3":
        first = int(p.flat.sector.min())
        mine = [j for j in idx if metas[j].sector == first]
        others = [j for j in idx if metas[j].sector != first][: len(mine)]
        idx = sorted(mine + others) if mine and len(others) == len(mine) else []
    stats = v3._box_groups(p.flat, cand, measured, windows, plan, idx=idx)[0] if idx else {}
    return {
        "pattern": pattern,
        "spacing": spacing,
        "combo": combo,
        "noise": noise,
        "kind": kind,
        "sectors": sectors,
        "stratum": v3._lowest([metas[j].stratum for j in idx]) if idx else None,
        "n_group": len(idx),
        "n_events": len(events),
        "not_measured": int(measured.dropped.get("a0_not_measured", 0)),
        "pulls": v3._pulls(stats),
    }


def unit_a08(arg):
    """A0.8: (shape, noise, kind, sectors, multiple, i, seed)."""
    from refute.core.verdict import TestStatus
    from refute.packs.tess import a0, power
    from refute.packs.tess import battery_v5 as v5
    from refute.packs.tess import detrend_fast as df
    from refute.packs.tess import pipeline as pl
    from refute.packs.tess import synthetic as syn
    from refute.packs.tess.events import group_mean
    from refute.packs.tess.types import LightCurveData

    shape, noise, kind, sectors, multiple, i, seed = arg
    plan = _plan()
    ev = plan.gauntlet.events
    if shape == "hetero":
        base, cand = v3._hetero_curve(seed, sectors, plan)
    else:
        base, _ = c.noise_curve(seed, noise, sectors)
        cand = v3._candidate(base.time, np.random.default_rng([seed, 1]))
        base = v3._apply_kind(base, cand, plan, kind)
    t = base.time
    sigma = float(np.median(base.flux_err))
    dt = np.mod(t - cand.t0 + 0.5 * cand.period, cand.period) - 0.5 * cand.period
    n_in = int(np.sum(np.abs(dt) <= cand.duration / 2.0))
    depth = v3.PRIMARY_SNR * sigma / math.sqrt(max(n_in, 1))
    cand = replace(cand, depth=depth)
    primary = syn.trapezoid(t, cand.period, cand.t0, depth, cand.duration, v3.INGRESS)
    with_primary = LightCurveData(t, base.flux - primary, base.flux_err, base.sector, base.year)
    first = prepare(with_primary, cand, plan)
    half0 = events_of(first.flat, cand, plan, phase=0.5)
    if len(half0) == 0:
        return {"shape": shape, "noise": noise, "kind": kind, "no_phase_half_data": True}
    e0 = group_mean(half0.depths, half0.errors).error
    secondary = syn.trapezoid(
        t, cand.period, cand.t0, multiple * e0, cand.duration, v3.INGRESS, phase=0.5
    )
    p = prepare(
        LightCurveData(t, with_primary.flux - secondary, base.flux_err, base.sector, base.year),
        cand,
        plan,
        reuse=first,
        changed=secondary != 0.0,
    )
    events = events_of(p.flat, cand, plan)
    events_half = events_of(p.flat, cand, plan, phase=0.5)
    sec = v5.check_secondary_two_sided(
        events, events_half, plan.gauntlet.secondary_eclipse, plan.stronger,
        power.candidate_seed("secondary_eclipse", cand),
    )  # fmt: skip
    exclude = sec.status is TestStatus.FAIL
    _, measured, windows, _ = measured_of(p, cand, plan, events=events, exclude=exclude)
    ref = measured_of(first, cand, plan)[1] if i % INFLATION_EVERY == 0 else None
    # the truth: the noise-free curve through the production preprocessing itself (Codex's
    # end-of-round review: a shortcut here changed which windows are measurable)
    clean = df.MaskAwareDetrender(
        LightCurveData(t, 1.0 - primary - secondary, base.flux_err, base.sector, base.year),
        plan.detrend,
        pl.transit_mask(t, cand.period, cand.t0, p.half),
    ).flat()
    noise_free = a0.box_measure(
        clean.time, clean.flux, cand.duration, ev.baseline_gap_durations,
        ev.baseline_outer_durations, ev.min_coverage, c.CADENCE,
    )  # fmt: skip
    truths = np.array([(noise_free(x) or (np.nan,))[0] for x in measured.centers.tolist()])
    metas = v3._metas(p.flat, cand, measured, plan)
    rec = {
        "shape": shape,
        "noise": noise,
        "kind": kind,
        "sectors": sectors,
        "multiple": multiple,
        "reference_error": e0,
        "secondary_status": sec.status.value,
        "branch": "excluded" if exclude else "included",
        "secondary_sigma": (sec.metrics or {}).get("secondary_sigma"),
        "n_events": len(measured),
        "n_reference_events": None if ref is None else len(ref),
    }
    if shape == "event":
        rec["pulls"] = [
            (m.stratum, (float(d) - tr) / float(e))
            for m, d, e, tr in zip(metas, measured.depths, measured.errors, truths, strict=True)
        ]
    else:
        rec["stratum"] = v3._lowest([m.stratum for m in metas])
        stats, _ = v3._box_groups(p.flat, cand, measured, windows, plan, truths=truths)
        rec["pulls"] = v3._pulls(stats)
    if ref is not None and len(measured) and len(ref):
        rec["error_inflation"] = float(np.median(measured.errors) / np.median(ref.errors))
    return rec


UNIT_OF = {
    "a01": unit_a01,
    "a02": unit_group,
    "a04": unit_group,
    "a07": unit_group,
    "a05": unit_a05,
    "a08": unit_a08,
}
