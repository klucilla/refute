"""v0.5.1 acceptance run of A0, the empirical error of an event measurement (docs/plans/
v0.5.1-acceptance.md, section A0; the design in a0-design.md next to this file, reviewed by Codex,
docs/plans/v0.5.1-consensus/a0-runner-round-*-answer.md). Run once, on frozen code
(``common.check_freeze`` before any unit is built); each section projected from its first 5 % and
stopped at 1.5 times (plan, amendment 10).

Every measurement is the battery's own: the per-event box depths of ``events.per_event_depths``
with the red-noise model errors (``rednoise.event_noise``), A0's errors (``a0.empirical_events``),
A0's group rule (``a0.group_variance`` with ``a0.shortcut``), the version-3 ``odd_even``
(``battery_v51.check_odd_even``, the matched trapezoid), ``battery_v51_diff.a0_depth`` on the
large-minus-core and the SAP-minus-expected series (the measurements of ``aperture_depth`` and of
``systematics``' SAP sub-check, without their test gates), and
``battery_v5.check_secondary_two_sided`` for A0.8's branch, called as ``pipeline.v05_tests`` calls
them. Transit-free curves (truth 0) unless a row injects a signal; pull = (value - truth) / error;
the truth of an injected signal is its noise-free measurement by the same estimator.

**Coverage kinds.** The partial and minimal strata need windows cut by gaps; a TESS-like sector
has four segment edges, so a random ephemeris almost never gives them ``n_eff >= 10``. Each curve
therefore has a declared kind: ``full`` (no cut), ``partial`` or ``minimal`` (the first 20 % or
40 % of the in-event core removed from every pseudo-window grid position and every event of the
ephemeris: coverage 0.8 or 0.6), ``mixed`` (A0.7: the odd grid positions and the odd epochs cut to
0.8, the rest full) and ``p3`` (A0.5: the first sector cut to 0.6, the others full). The strata
used in the evaluation are the ones the code computes, never the kind.

Sections (``run <section>``): ``a01`` A0.1 (and A0.3); ``a02`` A0.2 (and A0.3); ``a04``; ``a05``;
``a06``; ``a07`` (rule and forced pooling); ``a08``; ``sabotage``.

**The series measured (second run, #208).** Every per-event measurement receives the series the
pipeline gives it, ``_flat`` (``pipeline.attack_candidate``'s masked detrending for the
candidate); the first run passed the raw curve, the defect recorded on #208.
``tests/test_v051_accept_a0_series.py`` checks, byte for byte, that the series A0 receives here is
the pipeline's.

Usage: scripts/launch_affinity.ps1 -Script docs/validation/v0.5.1/acceptance/a0.py
       -Arguments 'run,a01' -Log .cache/v051/accept/a0r2-a01.log
"""

from __future__ import annotations

import math
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as c  # noqa: E402

c.env_threads()
STRATA = ("full", "partial", "minimal")
KINDS = {"full": 0.0, "partial": 0.2, "minimal": 0.4}
UNITS = {"a01": 200, "group": 700, "a05": 400, "a06": 400, "a08_event": 100, "a08_group": 700}
SPACINGS = (1.0, 3.0, 10.0)
DEPTHS = (2.5, 3.0, 4.0)
PRIMARY_SNR = 20.0
INGRESS = 0.1
# The second A0 run (#208, the maintainer's decision of 2026-11-08): the runner aligned with the
# pipeline (``_flat``), new seeds by this fixed label, its own output folders
# (``.cache/v051/accept/a0r2-<section>/``) and result file (``a0r2-result.json``). The first run's
# records and seeds decide nothing.
RUN = "a0r2"
SEED_LABEL = "refute-v051-accept-r2"


# --- shared measurement -------------------------------------------------------------------------


def _plan():
    from refute.packs.tess.params import TessTestPlan
    from refute.packs.tess.synthetic import discovery_v051_plan_dict

    return TessTestPlan.model_validate(discovery_v051_plan_dict())


def _candidate(t, rng, period=None, depth=0.0):
    from refute.packs.tess.types import Candidate

    p = float(period) if period else float(math.exp(rng.uniform(math.log(1.0), math.log(10.0))))
    return Candidate(
        period=p,
        t0=float(t.min() + rng.uniform(0.0, p)),
        duration=0.10,
        depth=max(depth, 1e-4),
        depth_err=1e-4,
        snr=10.0,
        log_likelihood=0.0,
        sde=0.0,
        n_transits=0,
    )


def _h(cand, plan):
    from refute.packs.tess import a0

    return a0.half_width(cand.duration, plan.gauntlet.events.baseline_outer_durations)


def _grid(lc, cand, plan):
    """(sector, grid position, centre) of every pseudo-window grid position, as
    ``a0.pseudo_windows`` builds the grid (2 h apart from each sector's first cadence)."""
    h = _h(cand, plan)
    out = []
    for s in np.unique(lc.sector):
        ts = lc.time[lc.sector == s]
        n = int(math.floor((ts.max() - ts.min()) / (2.0 * h))) + 1
        out += [(int(s), g, float(ts.min() + h + 2.0 * g * h)) for g in range(n)]
    return out


def _cut(lc, keep):
    from refute.packs.tess.types import LightCurveData

    return LightCurveData(
        lc.time[keep], lc.flux[keep], lc.flux_err[keep], lc.sector[keep], lc.year[keep]
    )


def _apply_kind(lc, cand, plan, kind):
    """The coverage kind of the module docstring: the first part of the in-event core removed
    from the chosen grid positions and events; a sector's first cadence is never removed (the
    grid stays anchored where it was)."""
    from refute.packs.tess import a0

    if kind == "full":
        return lc
    half = cand.duration / 2.0
    first = int(lc.sector.min())

    def fraction(sector, g, epoch):
        if kind in KINDS:
            return KINDS[kind]
        if kind == "mixed":
            odd = (g % 2 != 0) if g is not None else (epoch % 2 != 0)
            return 0.2 if odd else 0.0
        if kind == "p3":
            return 0.4 if sector == first else 0.0
        raise ValueError(kind)

    t = lc.time
    cuts = [(ctr, fraction(s, g, None)) for s, g, ctr in _grid(lc, cand, plan)]
    for e in np.unique(np.round((t - cand.t0) / cand.period)).astype(int):
        ctr = cand.t0 + e * cand.period
        cuts.append((ctr, fraction(a0.sector_of(t, lc.sector, ctr), None, int(e))))
    keep = np.ones(t.size, dtype=bool)
    for ctr, f in cuts:
        if f > 0:
            keep &= ~((t >= ctr - half) & (t < ctr - half + f * cand.duration))
    for s in np.unique(lc.sector):
        keep[int(np.argmax(lc.sector == s))] = True
    return _cut(lc, keep)


def _flat(raw, cand, plan):
    """The series the pipeline hands to every per-event measurement of this candidate, line for
    line as ``pipeline.attack_candidate`` builds it (second A0 run, #208, the maintainer's
    decision of 2026-11-08): the candidate's transits masked (half-width
    ``transit_mask_half_width_durations`` durations), the global components of the corrections
    refitted on the raw curve with that mask and subtracted first when the corrections are active
    (never with this runner's plan), then the plan's detrending with the mask. The runner's first
    A0 run passed ``raw`` itself: the defect of #208. Coverage cuts and injected signals are
    applied to the raw curve before this; the pixels of ``_pixel_stats`` stay raw, as the
    pipeline renders them from the raw data."""
    from refute.packs.tess import pipeline as pl
    from refute.packs.tess import synthetic as syn

    pw = None
    if plan.gauntlet.corrections.active:
        pw, _ = pl.global_prewhitening(syn.make_data(raw, [], None), plan)
    mask_half = plan.detrend.transit_mask_half_width_durations * cand.duration
    mask = pl.transit_mask(raw.time, cand.period, cand.t0, mask_half)
    curve = raw
    if pw is not None and pw.components:
        fitted = pl.refit(raw, pw.components, mask, plan)
        if fitted.reason is None:
            curve = pl._minus(raw, fitted.model)
    return pl.detrend(curve, plan.detrend, mask=mask)


def _events(lc, cand, plan, phase=0.0):
    from refute.packs.tess.events import per_event_depths
    from refute.packs.tess.rednoise import event_noise

    noise = event_noise(lc, None, cand.period, cand.t0, cand.duration, plan)
    return per_event_depths(
        lc, cand.period, cand.t0, cand.duration, c.CADENCE, plan.gauntlet.events, phase, None, noise
    )


def _measured(lc, cand, plan, exclude=False):
    from refute.packs.tess import a0

    events = _events(lc, cand, plan)
    measured, windows, details = a0.empirical_events(
        lc, cand, events, plan.gauntlet.events, c.CADENCE, exclude_phase_half=exclude
    )
    return events, measured, windows, details


def _metas(lc, cand, measured, plan):
    from refute.packs.tess import a0

    expected_in = cand.duration / c.CADENCE
    return [
        a0.event_meta(lc.time, lc.sector, ctr, n / expected_in, plan.gauntlet.events.min_coverage)
        for ctr, n in zip(measured.centers.tolist(), measured.n_in.tolist(), strict=True)
    ]


def _lowest(strata):
    order = {s: i for i, s in enumerate(STRATA)}
    return max(strata, key=lambda s: order[s]) if strata else None


def _box_groups(lc, cand, measured, windows, plan, idx=None, truths=None, pooled_all=None):
    """The box odd, even and odd-minus-even statistics with A0's group rule, as
    ``(value - truth, error)``; the shortcut seeded as ``a0_depth`` seeds it."""
    from refute.packs.tess import a0, power

    metas = _metas(lc, cand, measured, plan)
    idx = list(range(len(measured))) if idx is None else list(idx)
    truths = np.zeros(len(measured)) if truths is None else np.asarray(truths, dtype=float)
    seed = power.candidate_seed("odd_even", cand)
    pooled = {
        s: (pooled_all if pooled_all is not None else a0.shortcut(windows, s, seed + s))
        for s in {metas[i].sector for i in idx}
    }
    h = _h(cand, plan)
    errors = measured.errors
    odd = [i for i in idx if int(measured.epochs[i]) % 2 != 0]
    even = [i for i in idx if int(measured.epochs[i]) % 2 == 0]

    def combo(wmap):
        keys = list(wmap)
        var = a0.group_variance(
            [wmap[i] for i in keys], [float(errors[i]) for i in keys], [metas[i] for i in keys],
            windows, h, pooled,
        )  # fmt: skip
        value = float(sum(wmap[i] * (float(measured.depths[i]) - truths[i]) for i in keys))
        return value, (math.sqrt(var) if var else None)

    def weights(group):
        inv = np.array([1.0 / float(errors[i]) ** 2 for i in group])
        return dict(zip(group, (inv / inv.sum()).tolist(), strict=True))

    out = {}
    if odd:
        out["box_odd"] = combo(weights(odd))
    if even:
        out["box_even"] = combo(weights(even))
    if odd and even:
        out["box_diff"] = combo({**weights(odd), **{i: -v for i, v in weights(even).items()}})
    return out, pooled


def _matched_groups(lc, cand, plan, exclude=False):
    """The version-3 odd_even's own statistics (the matched trapezoid), as the pipeline calls it;
    the odd-minus-even error is |difference| / difference_sigma."""
    from refute.core.verdict import TestStatus
    from refute.packs.tess import battery_v51 as v51
    from refute.packs.tess import power

    seed = power.candidate_seed("odd_even", cand)
    r = v51.check_odd_even(lc, cand, plan.gauntlet, plan.stronger, c.CADENCE, exclude, seed)
    if r.status is TestStatus.INCONCLUSIVE:
        return {}, r.metrics.get("inconclusive_class")
    m = r.metrics
    out = {}
    if m.get("depth_odd_err_ppm"):
        out["matched_odd"] = (m["depth_odd_ppm"] * 1e-6, m["depth_odd_err_ppm"] * 1e-6)
    if m.get("depth_even_err_ppm"):
        out["matched_even"] = (m["depth_even_ppm"] * 1e-6, m["depth_even_err_ppm"] * 1e-6)
    diff = (m["depth_odd_ppm"] - m["depth_even_ppm"]) * 1e-6
    z = m.get("difference_sigma")
    if z and z > 0:
        out["matched_diff"] = (diff, abs(diff) / z)
    return out, None


def _pixel_stats(lc, cand, plan, seed):
    """The large-minus-core series of ``aperture_depth`` (pixels rendered from the target's
    series, default ``Scene``) and the SAP-minus-expected series of ``systematics`` (SAP = the
    affine SAP of ``make_sector_aux`` plus independent white noise of the PDCSAP white level, row
    3a.6's second case, so that ``sap_applicability`` holds), each through ``a0_depth`` with the
    seeds the tests use."""
    from refute.packs.tess import battery_v51_diff as v51d
    from refute.packs.tess import power
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
    g = v51d.a0_depth(
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
        g = v51d.a0_depth(t_u, r, s_u, cand, plan, seed_sy + 1)
        if g is not None:
            out["sap_minus_expected"] = (g.mean, g.error)
    return out, len(usable)


def _pulls(stats):
    return {k: (v / e if e and e > 0 else None) for k, (v, e) in stats.items()}


# --- A0.3: the window structure, by cadence index sets ---------------------------------------


def _a03(lc, cand, windows, measured, details, plan, exclude):
    from refute.packs.tess import a0

    h = _h(cand, plan)
    t = lc.time

    def idx(centre):
        lo = np.searchsorted(t, centre - h, side="left")
        hi = np.searchsorted(t, centre + h, side="left")
        return set(range(int(lo), int(hi)))

    sets = [idx(w.centre) for w in windows]
    disjoint = all(
        not (sets[i] & sets[j]) for i in range(len(sets)) for j in range(i + 1, len(sets))
    )
    epochs = np.unique(np.round((t - cand.t0) / cand.period))
    real = set().union(*(idx(cand.t0 + e * cand.period) for e in epochs)) if epochs.size else set()
    half = (
        set().union(*(idx(cand.t0 + (e + 0.5) * cand.period) for e in epochs))
        if epochs.size
        else set()
    )
    no_event = all(not (s & real) for s in sets)
    half_rule = all(not (s & half) for s in sets) if exclude else True
    grid = True
    for w in windows:
        ts = t[lc.sector == w.sector]
        g = (w.centre - ts.min() - h) / (2 * h)
        grid = grid and abs(g - round(g)) < 1e-9 and int(round(g)) == w.index
    # n_eff by the formula, recomputed here from the per-stratum lag correlations
    neff_ok = True
    for info in details.values():
        n, rk = info["n"], info["r_k"]
        total = sum(
            (1 - k / n) * max(0.0, rk[k - 1])
            for k in range(1, min(a0.MAX_LAG, n - 1) + 1)
            if rk[k - 1] is not None
        )
        neff_ok = neff_ok and (n < 2 or abs(n / (1 + 2 * total) - info["n_eff"]) < 1e-9)
    # an event is measured exactly when its sector and stratum have n_eff >= 10 (and a variance)
    metas = _metas(lc, cand, measured, plan)
    kept = {f"{m.sector}:{m.stratum}" for m in metas}
    drop_ok = all(info["n_eff"] >= a0.MIN_EFFECTIVE for key, info in details.items() if key in kept)
    return {
        "disjoint": bool(disjoint),
        "no_event_overlap": bool(no_event),
        "phase_half_rule": bool(half_rule),
        "grid": bool(grid),
        "n_eff_formula": bool(neff_ok),
        "not_measured_rule": bool(drop_ok),
    }


def _missing_lags(details):
    """Per stratum: (events' sector-strata whose n_eff used a lag with no pair, all of them)."""
    out = {}
    for key, info in details.items():
        st = key.split(":")[1]
        need = min(5, max(info.get("n", 0) - 1, 0))
        out.setdefault(st, []).append(any(r is None for r in (info.get("r_k") or [])[:need]))
    return {k: (sum(v), len(v)) for k, v in out.items()}


# --- units ------------------------------------------------------------------------------------


def unit_a01(arg):
    noise, kind, i, seed = arg
    plan = _plan()
    lc, _ = c.noise_curve(seed, noise, 2)
    cand = _candidate(lc.time, np.random.default_rng([seed, 1]))
    lc = _flat(_apply_kind(lc, cand, plan, kind), cand, plan)
    events, measured, windows, details = _measured(lc, cand, plan)
    metas = _metas(lc, cand, measured, plan)
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
        "a03": _a03(lc, cand, windows, measured, details, plan, False),
        "missing_lags": _missing_lags(details),
    }


def unit_group(arg):
    """A0.2 (with pixels), A0.4, A0.7, or a sabotage's box-only group ('a02b' as A0.2, 'a04b'
    as A0.4):
    (row, noise, kind, sectors, i, seed)."""
    row, noise, kind, sectors, i, seed = arg
    plan = _plan()
    rng = np.random.default_rng([seed, 1])
    if row == "a07":
        lc, cand = _hetero_curve(seed, sectors, plan)
    else:
        lc, _ = c.noise_curve(
            seed, noise, sectors, trend_sectors=(1,) if row in ("a04", "a04b") else None
        )
        cand = _candidate(lc.time, rng)
        lc = _apply_kind(lc, cand, plan, kind)
    raw, lc = lc, _flat(lc, cand, plan)
    events, measured, windows, details = _measured(lc, cand, plan)
    metas = _metas(lc, cand, measured, plan)
    stats, pooled = _box_groups(lc, cand, measured, windows, plan)
    rec = {
        "row": row,
        "noise": noise,
        "kind": kind,
        "sectors": sectors,
        "period": cand.period,
        "stratum": _lowest([m.stratum for m in metas]),
        "n_events": len(measured),
        "not_measured": int(measured.dropped.get("a0_not_measured", 0)),
        "strata_of_events": sorted({m.stratum for m in metas}),
        "shortcut": {str(k): bool(v) for k, v in pooled.items()},
    }
    if row not in ("a02b", "a04b"):
        matched, matched_class = _matched_groups(lc, cand, plan)
        stats.update(matched)
        rec["matched_inconclusive"] = matched_class
    rec["pulls"] = _pulls(stats)
    if row == "a02":
        pix, n_usable = _pixel_stats(raw, cand, plan, seed)
        rec["pulls"].update(_pulls(pix))
        rec["sap_usable_sectors"] = n_usable
        rec["a03"] = _a03(lc, cand, windows, measured, details, plan, False)
    if row == "a07":
        forced, _ = _box_groups(lc, cand, measured, windows, plan, pooled_all=True)
        rec["pulls_forced_pooling"] = _pulls(forced)
        rec["r_diff"] = _r_diffs(windows)
    return rec


def _r_diffs(windows):
    from refute.packs.tess import a0

    out = {}
    for s in {w.sector for w in windows}:
        sub = [w for w in windows if w.sector == s]
        for k in range(1, a0.MAX_LAG + 1):
            r_all = a0.lag_correlation(sub, k, None, None)[0]
            for a in STRATA:
                for b in STRATA:
                    r_ab, _ = a0.lag_correlation(sub, k, a, b)
                    if r_ab is not None and r_all is not None:
                        out.setdefault(f"{k}:{a}:{b}", []).append(r_ab - r_all)
    return {k: float(np.mean(v)) for k, v in out.items()}


def _hetero_curve(seed, sectors, plan):
    """A0.7: the ``mixed`` kind on a white curve, and the correlated noise defined by coverage: on
    the cadences of every window (grid position or event) whose coverage is below 0.9, two
    independent AR(1) series (tau 1 h and 0.5 d, each of variance sigma_r^2 / 2); elsewhere one
    AR(1) (tau 1 h, variance sigma_r^2); sigma_r half the white level."""
    from refute.packs.tess import a0
    from refute.packs.tess import synthetic as syn
    from refute.packs.tess.types import LightCurveData

    base, _ = c.noise_curve(seed, "white", sectors)
    cand = _candidate(base.time, np.random.default_rng([seed, 1]))
    base = _apply_kind(base, cand, plan, "mixed")
    t = base.time
    ev = plan.gauntlet.events
    probe = a0.box_measure(t, np.ones_like(t), cand.duration, ev.baseline_gap_durations,
                           ev.baseline_outer_durations, ev.min_coverage, c.CADENCE)  # fmt: skip
    h = _h(cand, plan)
    centres = [ctr for _, _, ctr in _grid(base, cand, plan)]
    centres += [cand.t0 + e * cand.period for e in np.unique(np.round((t - cand.t0) / cand.period))]
    partial = np.zeros(t.size, dtype=bool)
    for ctr in centres:
        got = probe(ctr)
        if got is not None and got[1] < 0.9:
            partial |= (t >= ctr - h) & (t < ctr + h)
    rng = np.random.default_rng([seed, 9])
    sigma_r = 0.5 * float(np.median(base.flux_err))
    red = np.zeros(t.size)
    for s in np.unique(base.sector):
        sel = base.sector == s
        one = syn.ar1_series(t[sel], sigma_r, 1.0 / 24.0, rng)
        a = syn.ar1_series(t[sel], sigma_r / math.sqrt(2.0), 1.0 / 24.0, rng)
        b = syn.ar1_series(t[sel], sigma_r / math.sqrt(2.0), 0.5, rng)
        red[sel] = np.where(partial[sel], a + b, one)
    return LightCurveData(t, base.flux + red, base.flux_err, base.sector, base.year), cand


def unit_a05(arg):
    pattern, spacing, combo, noise, kind, sectors, i, seed = arg
    plan = _plan()
    lc, _ = c.noise_curve(
        seed, noise, sectors, trend_sectors=(1,) if combo == "trend_one" else None
    )
    cand = _candidate(lc.time, np.random.default_rng([seed, 1]), period=spacing)
    lc = _apply_kind(lc, cand, plan, "p3" if pattern == "p3" else kind)
    if pattern == "p1":
        lc = _cut_one_odd(lc, cand, plan)
    lc = _flat(lc, cand, plan)
    events, measured, windows, details = _measured(lc, cand, plan)
    metas = _metas(lc, cand, measured, plan)
    idx = list(range(len(measured)))
    if pattern == "p2":
        idx = _two_against_three(measured)
    if pattern == "p3":
        first = int(lc.sector.min())
        mine = [j for j in idx if metas[j].sector == first]
        others = [j for j in idx if metas[j].sector != first][: len(mine)]
        idx = sorted(mine + others) if mine and len(others) == len(mine) else []
    stats = _box_groups(lc, cand, measured, windows, plan, idx=idx)[0] if idx else {}
    return {
        "pattern": pattern,
        "spacing": spacing,
        "combo": combo,
        "noise": noise,
        "kind": kind,
        "sectors": sectors,
        "stratum": _lowest([metas[j].stratum for j in idx]) if idx else None,
        "n_group": len(idx),
        "n_events": len(events),
        "not_measured": int(measured.dropped.get("a0_not_measured", 0)),
        "pulls": _pulls(stats),
    }


def _cut_one_odd(lc, cand, plan):
    """(p1): the cadences of one odd event's whole window removed (an event lost in a gap)."""
    h = _h(cand, plan)
    epochs = np.unique(np.round((lc.time - cand.t0) / cand.period)).astype(int)
    odd = [e for e in epochs if e % 2 != 0]
    if not odd:
        return lc
    ctr = cand.t0 + odd[len(odd) // 2] * cand.period
    return _cut(lc, ~((lc.time >= ctr - h) & (lc.time < ctr + h)))


def _two_against_three(measured):
    """(p2): the first five consecutive measured events (time order) with 2 of one parity and 3
    of the other."""
    ep = [int(e) for e in measured.epochs]
    for j in range(len(ep) - 4):
        odd = sum(1 for e in ep[j : j + 5] if e % 2 != 0)
        if odd in (2, 3):
            return list(range(j, j + 5))
    return []


def unit_a06(arg):
    """A0.6: (noise, kind, period, i, seed); the candidate has the scheduled period (1, 3 or 10 d,
    Codex's round 3), the lags 6 to 10 and the grid lag of that period."""
    from refute.packs.tess import a0

    noise, kind, period, i, seed = arg
    plan = _plan()
    lc, _ = c.noise_curve(seed, noise, 2)
    cand = _candidate(lc.time, np.random.default_rng([seed, 1]), period=period)
    lc = _flat(_apply_kind(lc, cand, plan, kind), cand, plan)
    _, _, windows, _ = _measured(lc, cand, plan)
    h = _h(cand, plan)
    period_lag = int(round(period / (2 * h)))
    lags = sorted(set(range(6, 11)) | {period_lag})
    out = {}
    for st in STRATA:
        sub = [w for w in windows if w.stratum == st]
        if sub:
            out[st] = {str(k): list(a0.lag_correlation(sub, k, st, st, min_pairs=2)) for k in lags}
    return {"noise": noise, "kind": kind, "period": period, "period_lag": period_lag, "lags": out}


def unit_a08(arg):
    """A0.8: (shape, noise, kind, sectors, multiple, i, seed); shape 'event' (A0.1's curves),
    'group' (A0.2's) or 'hetero' (A0.7's)."""
    from refute.core.verdict import TestStatus
    from refute.packs.tess import a0, power
    from refute.packs.tess import battery_v5 as v5
    from refute.packs.tess import synthetic as syn
    from refute.packs.tess.events import group_mean
    from refute.packs.tess.types import LightCurveData

    shape, noise, kind, sectors, multiple, i, seed = arg
    plan = _plan()
    ev = plan.gauntlet.events
    if shape == "hetero":
        base, cand = _hetero_curve(seed, sectors, plan)
    else:
        base, _ = c.noise_curve(seed, noise, sectors)
        cand = _candidate(base.time, np.random.default_rng([seed, 1]))
        base = _apply_kind(base, cand, plan, kind)
    t = base.time
    sigma = float(np.median(base.flux_err))
    dt = np.mod(t - cand.t0 + 0.5 * cand.period, cand.period) - 0.5 * cand.period
    n_in = int(np.sum(np.abs(dt) <= cand.duration / 2.0))
    depth = PRIMARY_SNR * sigma / math.sqrt(max(n_in, 1))
    cand = replace(cand, depth=depth)
    primary = syn.trapezoid(t, cand.period, cand.t0, depth, cand.duration, INGRESS)
    with_primary = LightCurveData(t, base.flux - primary, base.flux_err, base.sector, base.year)
    flat_primary = _flat(with_primary, cand, plan)
    half0 = _events(flat_primary, cand, plan, phase=0.5)
    if len(half0) == 0:
        return {"shape": shape, "noise": noise, "kind": kind, "no_phase_half_data": True}
    e0 = group_mean(half0.depths, half0.errors).error
    secondary = syn.trapezoid(
        t, cand.period, cand.t0, multiple * e0, cand.duration, INGRESS, phase=0.5
    )
    lc = _flat(
        LightCurveData(t, with_primary.flux - secondary, base.flux_err, base.sector, base.year),
        cand,
        plan,
    )
    events = _events(lc, cand, plan)
    events_half = _events(lc, cand, plan, phase=0.5)
    sec = v5.check_secondary_two_sided(
        events, events_half, plan.gauntlet.secondary_eclipse, plan.stronger,
        power.candidate_seed("secondary_eclipse", cand),
    )  # fmt: skip
    exclude = sec.status is TestStatus.FAIL
    measured, windows, _ = a0.empirical_events(
        lc, cand, events, ev, c.CADENCE, exclude_phase_half=exclude
    )
    ref, _, _ = a0.empirical_events(
        flat_primary, cand, _events(flat_primary, cand, plan), ev, c.CADENCE
    )
    # the truth of each event: the noise-free curve through the same path (the pipeline's
    # flattening, then the same box estimator)
    clean = _flat(
        LightCurveData(t, 1.0 - primary - secondary, base.flux_err, base.sector, base.year),
        cand,
        plan,
    )
    noise_free = a0.box_measure(
        clean.time, clean.flux, cand.duration, ev.baseline_gap_durations,
        ev.baseline_outer_durations, ev.min_coverage, c.CADENCE,
    )  # fmt: skip
    truths = np.array([(noise_free(x) or (np.nan,))[0] for x in measured.centers.tolist()])
    metas = _metas(lc, cand, measured, plan)
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
        "n_reference_events": len(ref),
    }
    if shape == "event":
        rec["pulls"] = [
            (m.stratum, (float(d) - tr) / float(e))
            for m, d, e, tr in zip(metas, measured.depths, measured.errors, truths, strict=True)
        ]
    else:
        rec["stratum"] = _lowest([m.stratum for m in metas])
        stats, _ = _box_groups(lc, cand, measured, windows, plan, truths=truths)
        rec["pulls"] = _pulls(stats)
    if len(measured) and len(ref):
        rec["error_inflation"] = float(np.median(measured.errors) / np.median(ref.errors))
    return rec


# --- sabotage ---------------------------------------------------------------------------------


def _patch(name):
    """One sabotage, applied to the ``a0`` module inside this worker process only."""
    from refute.packs.tess import a0

    if name == "model_errors_alone":
        a0.stratum_error = lambda windows, sector, st: (1e-30, {"n": 0, "n_eff": 0.0, "r_k": []})
    elif name == "neff_equals_n":
        a0.effective_count = lambda n, r: float(n)
    elif name == "rho_zero":

        def diagonal(weights, sigmas, events, windows, h, pooled):
            var = float(sum((w * s) ** 2 for w, s in zip(weights, sigmas, strict=True)))
            return var if var > 0 else None

        a0.group_variance = diagonal
    elif name == "share_event_cadences":
        real = a0.pseudo_windows

        def leaky(
            time, sector, period, t0, duration, outer, min_cov, measure, exclude_phase_half=True
        ):
            return real(
                time, sector, period * 1e9, t0 + 1e6, duration, outer, min_cov, measure, False
            )

        a0.pseudo_windows = leaky
    elif name == "pool_sectors":
        real_se = a0.stratum_error

        def pooled(windows, sector, st):
            return real_se([replace(w, sector=sector) for w in windows], sector, st)

        a0.stratum_error = pooled
    elif name == "force_phase_half":
        real_ee = a0.empirical_events

        def included(flat, cand, events, params, cadence, exclude_phase_half=False):
            return real_ee(flat, cand, events, params, cadence, exclude_phase_half=False)

        a0.empirical_events = included
    else:
        raise ValueError(name)


_PATCHED: set[str] = set()


def unit_sabotage(arg):
    """(name, inner kind, inner argument). A worker serves one sabotage only (``run_section``
    dispatches each sabotage as its own section), so a patch never reaches another unit."""
    name, inner, inner_arg = arg
    if _PATCHED and name not in _PATCHED:
        raise RuntimeError("two sabotages in one worker process")
    if name not in _PATCHED:
        _patch(name)
        _PATCHED.add(name)
    fn = {"a01": unit_a01, "a02b": unit_group, "a04b": unit_group, "a08": unit_a08}[inner]
    rec = fn(inner_arg)
    rec["sabotage"] = name
    return rec


SABOTAGE = {
    # name: (inner unit, (noises), (kinds), sectors, units per stratum)
    "model_errors_alone": (
        "a01",
        ("correlated", "correlated_trend"),
        tuple(KINDS),
        2,
        UNITS["a01"],
    ),
    "neff_equals_n": ("a01", ("long",), tuple(KINDS), 2, UNITS["a01"]),
    "rho_zero": ("a02b", ("long",), tuple(KINDS), 2, UNITS["group"]),
    "share_event_cadences": ("a01", ("white",), ("full",), 2, 50),
    "pool_sectors": ("a04b", c.NOISES_A0, ("full",), 2, UNITS["group"]),
    "force_phase_half": ("a08", c.NOISES_A0, tuple(KINDS), 2, UNITS["a08_event"]),
}


# --- schedules --------------------------------------------------------------------------------


def schedule(section: str) -> list[tuple[str, object]]:
    def s(case, i):
        return c.accept_seed(case, i, label=SEED_LABEL)

    n = c.NOISES_A0
    if section == "a01":
        return [
            (f"a01/{x}/{k}/{i}", (x, k, i, s(f"a0-a01-{x}-{k}", i)))
            for x in n for k in KINDS for i in range(UNITS["a01"])
        ]  # fmt: skip
    if section in ("a02", "a04"):
        return [
            (f"{section}/{x}/{k}/{m}/{i}", (section, x, k, m, i, s(f"a0-{section}-{x}-{k}-{m}", i)))
            for x in n for k in KINDS for m in (2, 3, 4) for i in range(UNITS["group"])
        ]  # fmt: skip
    if section == "a07":
        return [
            (f"a07/{m}/{i}", ("a07", "hetero", "mixed", m, i, s(f"a0-a07-{m}", i)))
            for m in (2, 3, 4) for i in range(UNITS["group"])
        ]  # fmt: skip
    if section == "a05":
        units = []
        for p in ("p1", "p2", "p3"):
            for sp in SPACINGS:
                for cb in ("equal", "trend_one"):
                    for x in n:
                        for k in ("minimal",) if p == "p3" else tuple(KINDS):
                            for m in (2, 3, 4):
                                case = f"a0-a05-{p}-{sp:g}-{cb}-{x}-{k}-{m}"
                                units += [
                                    (
                                        f"a05/{p}/{sp:g}/{cb}/{x}/{k}/{m}/{i}",
                                        (p, sp, cb, x, k, m, i, s(case, i)),
                                    )
                                    for i in range(UNITS["a05"])
                                ]
        return units
    if section == "a06":
        return [
            (f"a06/{x}/{k}/{i}", (x, k, SPACINGS[i % 3], i, s(f"a0-a06-{x}-{k}", i)))
            for x in n for k in KINDS for i in range(UNITS["a06"])
        ]  # fmt: skip
    if section == "a08":
        units = []
        for d in DEPTHS:
            for x in n:
                for k in KINDS:
                    case = f"a0-a08-event-{x}-{k}-{d:g}"
                    units += [
                        (f"a08/event/{x}/{k}/{d:g}/{i}", ("event", x, k, 2, d, i, s(case, i)))
                        for i in range(UNITS["a08_event"])
                    ]
                    for m in (2, 3, 4):
                        case = f"a0-a08-group-{x}-{k}-{m}-{d:g}"
                        units += [
                            (
                                f"a08/group/{x}/{k}/{m}/{d:g}/{i}",
                                ("group", x, k, m, d, i, s(case, i)),
                            )
                            for i in range(UNITS["a08_group"])
                        ]
            for m in (2, 3, 4):
                case = f"a0-a08-hetero-{m}-{d:g}"
                units += [
                    (
                        f"a08/hetero/{m}/{d:g}/{i}",
                        ("hetero", "hetero", "mixed", m, d, i, s(case, i)),
                    )
                    for i in range(UNITS["a08_group"])
                ]
        return units
    if section.startswith("sabotage-"):
        name = section[len("sabotage-") :]
        inner, noises, kinds, sectors, count = SABOTAGE[name]
        units = []
        for x in noises:
            for k in kinds:
                for i in range(count):
                    seed = s(f"a0-sab-{name}-{x}-{k}", i)
                    if inner == "a01":
                        arg = (x, k, i, seed)
                    elif inner in ("a02b", "a04b"):
                        arg = (inner, x, k, sectors, i, seed)
                    else:
                        arg = ("event", x, k, sectors, 4.0, i, seed)
                    units.append((f"sab/{name}/{x}/{k}/{i}", (name, inner, arg)))
        return units
    raise SystemExit(f"unknown section {section!r}")


def function_of(section: str):
    if section.startswith("sabotage-"):
        return unit_sabotage
    return {
        "a01": unit_a01, "a02": unit_group, "a04": unit_group, "a07": unit_group,
        "a05": unit_a05, "a06": unit_a06, "a08": unit_a08,
    }[section]  # fmt: skip


SECTIONS = ("a01", "a02", "a04", "a05", "a06", "a07", "a08", *(f"sabotage-{x}" for x in SABOTAGE))


# --- evaluation (fixed before any acceptance unit ran; Codex's round 3, objection 2) ----------

N_PULLS = 400
BOX = ("box_odd", "box_even", "box_diff")
MATCHED = ("matched_odd", "matched_even", "matched_diff")
PIXEL = ("large_minus_core", "sap_minus_expected")


def _ordered(section):
    """The section's records in schedule order (the unit order of "the first 400"), with the
    count of scheduled units, missing units and units that ended in ERROR."""
    ids = [u for u, _ in schedule(section)]
    pos = {u: i for i, u in enumerate(ids)}
    recs = [r for r in c._records(c.OUT / f"{RUN}-{section}" / "records.jsonl") if r["unit"] in pos]
    recs.sort(key=lambda r: pos[r["unit"]])
    errors = [r for r in recs if r.get("status") != "OK"]
    info = {
        "scheduled": len(ids),
        "recorded": len(recs),
        "missing": len(ids) - len(recs),
        "errors": len(errors),
        "error_reasons": sorted({str(r.get("reason"))[:120] for r in errors})[:10],
        "cpu_hours": sum(float(r.get("cpu_seconds", 0.0)) for r in recs) / 3600.0,
    }
    return [r for r in recs if r.get("status") == "OK"], info


def _band(values):
    """The first 400 finite pulls (unit order) against A0's band; fewer: NOT DECIDABLE. A unit
    with no calibrated error counts as unavailable, never as a passing observation."""
    finite = [v for v in values if v is not None and math.isfinite(v)]
    out = c.pull_band(finite[:N_PULLS], n_required=N_PULLS)
    out.update(available=len(finite), no_calibrated_error=len(values) - len(finite))
    return out


def _bands(groups):
    return {"/".join(str(x) for x in key): _band(v) for key, v in sorted(groups.items(), key=str)}


def _summary(bands):
    """The keys that FAIL and the keys that are NOT DECIDABLE (every one of them reported)."""
    return {
        "PASS": sum(1 for b in bands.values() if b["result"] == "PASS"),
        "FAIL": [k for k, b in bands.items() if b["result"] == "FAIL"],
        "NOT DECIDABLE": [k for k, b in bands.items() if b["result"] == "NOT DECIDABLE"],
    }


def _per_event_bands(recs, key_of):
    groups: dict = {}
    for r in recs:
        for st, p in r["pulls"]:
            groups.setdefault(key_of(r, st), []).append(p)
    return _bands(groups)


def _group_bands(recs, key_of, stats, field="pulls"):
    groups: dict = {}
    for r in recs:
        if r.get("stratum") is None:
            continue
        for name in stats:
            groups.setdefault((*key_of(r), name), []).append((r.get(field) or {}).get(name))
    return _bands(groups)


def _not_measured(recs, key_of):
    out: dict = {}
    for r in recs:
        k = "/".join(str(x) for x in key_of(r))
        a, b = out.get(k, (0, 0))
        out[k] = (a + int(r.get("not_measured", 0)), b + int(r.get("n_events", 0)))
    return {
        k: {"not_measured": a, "events": b, "fraction": a / b if b else None}
        for k, (a, b) in out.items()
    }


def _a03_summary(recs):
    flags: dict = {}
    for r in recs:
        for name, ok in (r.get("a03") or {}).items():
            flags.setdefault(name, [0, 0])
            flags[name][0] += 0 if ok else 1
            flags[name][1] += 1
    return {
        "violations": {k: {"units_failing": v[0], "units": v[1]} for k, v in flags.items()},
        "result": "PASS" if flags and all(v[0] == 0 for v in flags.values()) else "FAIL",
    }


def evaluate_section(section):
    recs, info = _ordered(section)
    out: dict = {"run": info}
    if section == "a01":
        b = _per_event_bands(recs, lambda r, st: (r["noise"], st))
        out.update(bands=b, summary=_summary(b), a03=_a03_summary(recs))
        out["not_measured_by_kind"] = _not_measured(recs, lambda r: (r["noise"], r["kind"]))
        lags: dict = {}
        for r in recs:
            for st, (bad, n) in (r.get("missing_lags") or {}).items():
                a, t = lags.get(st, (0, 0))
                lags[st] = (a + bad, t + n)
        out["sector_strata_with_a_lag_without_pairs"] = lags
    elif section in ("a02", "a04"):
        stats = BOX + MATCHED + (PIXEL if section == "a02" else ())
        b = _group_bands(recs, lambda r: (r["noise"], r["stratum"], r["sectors"]), stats)
        out.update(bands=b, summary=_summary(b))
        out["units_without_a_measured_event"] = sum(1 for r in recs if r.get("stratum") is None)
        classes: dict = {}
        for r in recs:
            k = str(r.get("matched_inconclusive"))
            classes[k] = classes.get(k, 0) + 1
        out["matched_odd_even_inconclusive_classes"] = classes
        if section == "a02":
            out["a03"] = _a03_summary(recs)
    elif section == "a05":

        def key05(r):
            return (
                r["pattern"],
                f"{r['spacing']:g}",
                r["combo"],
                r["noise"],
                r["stratum"],
                r["sectors"],
            )

        b = _group_bands(recs, key05, BOX)
        out.update(bands=b, summary=_summary(b))
        out["not_measured_by_kind"] = _not_measured(
            recs, lambda r: (r["pattern"], r["noise"], r["kind"])
        )
        out["units_without_a_group"] = sum(1 for r in recs if r.get("stratum") is None)
    elif section == "a06":
        acc: dict = {}
        for r in recs:
            for st, lagmap in (r.get("lags") or {}).items():
                for k, (rho, m) in lagmap.items():
                    if rho is None or not m:
                        continue
                    tag = (
                        "period"
                        if int(k) == r["period_lag"] and int(k) not in range(6, 11)
                        else "lag"
                    )
                    name = f"{r['noise']}/{st}/{tag}-{k}" + (
                        f"/P{r['period']:g}" if tag == "period" else ""
                    )
                    acc.setdefault(name, []).append((rho, m))

        def describe(v):
            outside = [abs(x) > 2 / math.sqrt(m) for x, m in v]
            return {
                "curves": len(v),
                "mean_r": float(np.mean([x for x, _ in v])),
                "fraction_outside_2_over_sqrt_m": float(np.mean(outside)),
            }

        out["autocorrelation"] = {k: describe(v) for k, v in sorted(acc.items())}
        out["note"] = "reported only; the band 2 / sqrt(m) is descriptive (A0.6)"
    elif section == "a07":
        hetero = [r for r in recs if len(r.get("strata_of_events") or []) >= 2]

        def key07(r):
            return (r["sectors"], r["stratum"])

        rule = _group_bands(hetero, key07, BOX + MATCHED)
        forced = _group_bands(hetero, key07, BOX, field="pulls_forced_pooling")
        left = {k: b for k, b in forced.items() if b["result"] != "NOT DECIDABLE"}
        taken = [any(r["shortcut"].values()) for r in recs]
        out.update(
            heterogeneous_units=len(hetero),
            rule_bands=rule,
            rule_summary=_summary(rule),
            forced_pooling_bands=forced,
            forced_pooling_leaves_sd_band=[k for k, b in left.items() if not 0.9 <= b["sd"] <= 1.1],
            shortcut_fraction=float(np.mean(taken)) if taken else None,
        )
        diffs: dict = {}
        for r in hetero:
            for k, v in (r.get("r_diff") or {}).items():
                diffs.setdefault(k, []).append(v)
        out["realized_r_kab_minus_r_k"] = {k: float(np.mean(v)) for k, v in sorted(diffs.items())}
        out["forced_pooling_shows_the_test_matters"] = bool(out["forced_pooling_leaves_sd_band"])
        out["note"] = (
            "required: the rule passes (here and in A0.2's correlated strata); forced pooling must "
            "leave [0.9, 1.1]; if it does not, the shortcut is not used anywhere (the rule only)"
        )
    elif section == "a08":
        ok = [r for r in recs if r.get("pulls") is not None]
        ev = [r for r in ok if r["shape"] == "event"]
        gr = [r for r in ok if r["shape"] != "event"]
        b_ev = _per_event_bands(
            ev, lambda r, st: (r["noise"], st, f"{r['multiple']:g}", r["branch"])
        )

        def key08(r):
            d = f"{r['multiple']:g}"
            return (r["shape"], r["noise"], r["stratum"], r["sectors"], d, r["branch"])

        b_gr = _group_bands(gr, key08, BOX)
        branch: dict = {}
        for r in ok:
            k = f"{r['shape']}/{r['noise']}/{r['kind']}/{r['sectors']}/{r['multiple']:g}"
            d = branch.setdefault(
                k, {"units": 0, "excluded": 0, "inconclusive": 0, "inflation": []}
            )
            d["units"] += 1
            d["excluded"] += r["branch"] == "excluded"
            d["inconclusive"] += r["secondary_status"] == "INCONCLUSIVE"
            if r.get("error_inflation") is not None:
                d["inflation"].append(r["error_inflation"])
        for d in branch.values():
            inf = d.pop("inflation")
            d["median_error_inflation"] = float(np.median(inf)) if inf else None
        out.update(
            event_bands=b_ev,
            event_summary=_summary(b_ev),
            group_bands=b_gr,
            group_summary=_summary(b_gr),
            branches=branch,
            units_without_phase_half_data=len(recs) - len(ok),
        )
    elif section.startswith("sabotage-"):
        name = section[len("sabotage-") :]
        if name == "share_event_cadences":
            a03 = _a03_summary(recs)
            detected = a03["violations"].get("no_event_overlap", {}).get("units_failing", 0) > 0
            out.update(a03=a03)
        else:
            if name in ("model_errors_alone", "neff_equals_n"):
                b = _per_event_bands(recs, lambda r, st: (r["noise"], st))
            elif name == "force_phase_half":
                b = _per_event_bands(recs, lambda r, st: (r["noise"], st, r["branch"]))
            else:
                b = _group_bands(recs, lambda r: (r["noise"], r["stratum"], r["sectors"]), BOX)
            out.update(bands=b, summary=_summary(b))
            detected = bool(out["summary"]["FAIL"])
            if not out["summary"]["FAIL"] and not out["summary"]["PASS"]:
                out["void"] = "every target stratum NOT DECIDABLE"
        out["sabotage_detected"] = detected
        if name == "force_phase_half" and not detected:
            out["consequence"] = (
                "A0 fails this acceptance condition and cannot proceed: reported to the maintainer"
            )
    return out


def evaluate():
    """Every section, once all are complete; writes a0r2-result.json next to the runner (once)."""
    incomplete = []
    result: dict = {"code_sha256": c.check_freeze(), "sections": {}}
    for section in SECTIONS:
        out = evaluate_section(section)
        if out["run"]["missing"]:
            incomplete.append(section)
        result["sections"][section] = out
    if incomplete:
        raise SystemExit(f"sections not complete: {incomplete}; nothing written")
    sab = {s: result["sections"][s]["sabotage_detected"] for s in SECTIONS if s.startswith("sab")}
    result["sabotage_detected"] = sab
    result["a03"] = {s: result["sections"][s]["a03"]["result"] for s in ("a01", "a02")}
    result["method_status"] = "not_validated"
    result["run"] = {"label": RUN, "seed_label": SEED_LABEL}
    print(c.write_result(RUN, result))


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "evaluate":
        evaluate()
        sys.exit(0)
    if len(sys.argv) >= 3 and sys.argv[1] == "run" and sys.argv[2] in SECTIONS:
        c.check_freeze()  # before any acceptance seed exists (Codex's objection 1)
        section = sys.argv[2]
        used = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
        others = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0
        c.run_section(f"{RUN}-{section}", schedule(section), function_of(section), used, others)
    else:
        raise SystemExit(
            f"usage: a0.py run <{'|'.join(SECTIONS)}> [used hours] [other projected hours]"
        )
