"""A0, battery version 4 (v0.5.2): the pseudo-event windows measured under the same mask as the
real events (docs/plans/v0.5.2-stage2-design.md, section 3).

A real event is measured on the preprocessing that masks the real events. A pseudo-window is
measured on the preprocessing that masks the real events and the windows of its own **comb**:
the grid positions ``g`` of a sector with ``g % J == j`` (``J = 4``), each masked to one duration
each side of its centre (the half-width of the real events' mask). A pseudo-window therefore never
contributes to the trend under it, as a real event does not.

Everything else is A0 of ``a0.py``: the grid, the windows kept, the strata, the per-event error, the
group rule and the shortcut, called unchanged. ``Preprocess`` is the contract of section 3: given
further cadences to mask (an array over the preprocessing's original cadences), it returns the
series as the production path builds it. Masks, clipping, the trend fit, normalization and the
alignment to the cadence index all stay inside it. Versions 3 and earlier never import this module.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from refute.packs.tess import a0

J = 4

Preprocess = Callable[[np.ndarray | None], object]


@dataclass
class Measurement:
    """A curve's real-mask series and the preprocessing that produced it."""

    raw: object
    flat: object
    preprocess: Preprocess
    half: float
    detrender: object = None


def prepare(lc, candidate, plan, components=None, reuse=None, changed=None) -> Measurement:
    """The preprocessing of the A0-dependent measurements, the one construction shared by the
    pipeline and the acceptance runner: the real events of ``candidate`` masked (its final
    ephemeris), and, given further cadences to mask, every mask-dependent step again under the
    combined mask. With global components (``components``, the corrections) that includes their
    refit and subtraction, so that a pseudo-window cannot influence the model removed under it;
    without them the fits of knots that lose no cadence are reused. ``reuse`` (a ``Measurement``
    of the same cadences and candidate) with ``changed`` (the cadences whose flux differs) takes
    its fits where no changed cadence is in the knot's window."""
    from refute.packs.tess import detrend_fast as df
    from refute.packs.tess.pipeline import _minus, refit, transit_mask

    half = plan.detrend.transit_mask_half_width_durations * candidate.duration
    mask = transit_mask(lc.time, candidate.period, candidate.t0, half)
    detrender = None
    if components:

        def preprocess(extra):
            whole = mask if extra is None else mask | extra
            fitted = refit(lc, components, whole, plan)
            curve = _minus(lc, fitted.model) if fitted.reason is None else lc
            return df.detrend(curve, plan.detrend, mask=whole)

    else:
        detrender = df.MaskAwareDetrender(
            lc,
            plan.detrend,
            mask,
            reuse=None if reuse is None else reuse.detrender,
            changed=changed,
        )
        preprocess = detrender.flat
    return Measurement(lc, preprocess(None), preprocess, half, detrender)


def grid(time: np.ndarray, sector: np.ndarray, h: float) -> dict[int, tuple[float, int]]:
    """Per sector, the first cadence and the number of grid positions of ``a0.pseudo_windows``."""
    out = {}
    for s in np.unique(sector):
        ts = time[sector == s]
        out[int(s)] = (float(ts.min()), int(math.floor((ts.max() - ts.min()) / (2.0 * h))) + 1)
    return out


def comb_masks(
    original_time: np.ndarray, layout: dict[int, tuple[float, int]], h: float, half: float
) -> np.ndarray:
    """``J`` masks over the original cadences, one per comb, by a cumulative count per tooth."""
    masks = np.zeros((J, original_time.size), dtype=bool)
    for first, n in layout.values():
        centres = first + h + 2.0 * np.arange(n) * h
        lo = np.searchsorted(original_time, centres - half, side="left")
        hi = np.searchsorted(original_time, centres + half, side="right")
        for g, (a, b) in enumerate(zip(lo.tolist(), hi.tolist(), strict=True)):
            masks[g % J, a:b] = True
    return masks


def comb_measure(
    preprocess: Preprocess,
    original_time: np.ndarray,
    series,
    duration: float,
    half: float,
    event_params,
    cadence_days: float,
) -> Callable[[float], tuple[float, float] | None]:
    """``measure(centre)`` for ``a0.pseudo_windows``: the box of the window's own comb.

    ``series`` is the real-mask series, whose cadences anchor the grid. Each comb's preprocessing
    runs once, when a window of that comb is first measured."""
    h = a0.half_width(duration, event_params.baseline_outer_durations)
    layout = grid(series.time, series.sector, h)
    masks = comb_masks(original_time, layout, h, half)
    measures: dict[int, Callable] = {}

    def box(j: int):
        if j not in measures:
            flat = preprocess(masks[j])
            measures[j] = a0.box_measure(
                flat.time,
                flat.flux,
                duration,
                event_params.baseline_gap_durations,
                event_params.baseline_outer_durations,
                event_params.min_coverage,
                cadence_days,
            )
        return measures[j]

    def measure(centre: float):
        s = a0.sector_of(series.time, series.sector, centre)
        return box(int(round((centre - layout[s][0] - h) / (2.0 * h))) % J)(centre)

    return measure


def a0_depth(time, values, sector, candidate, plan, seed, exclude_phase_half=False):
    """``battery_v51_diff.a0_depth`` with the additive preprocessing mask-aware: the pseudo-windows
    of the series measured under their own combs."""
    from refute.packs.tess import detrend_fast as df
    from refute.packs.tess.battery_v51_diff import MIN_MEASURABLE_ERROR, A0Depth
    from refute.packs.tess.battery_v52 import GRID_SECTORS
    from refute.packs.tess.events import per_event_depths, per_point_sigma, transit_mask

    good = np.isfinite(time) & np.isfinite(values)
    time, values, sector = time[good], values[good], sector[good]
    if time.size < 10:
        return None
    order = np.argsort(time, kind="stable")
    time, values, sector = time[order], values[order], sector[order]
    half = plan.detrend.transit_mask_half_width_durations * candidate.duration
    mask = transit_mask(time, candidate.period, candidate.t0, half)
    detrender = df.AdditiveDetrender(time, values, sector, plan.detrend, mask)
    series = detrender.flat()
    ok = np.isfinite(detrender.residuals())
    sigma = per_point_sigma(series, mask[ok])
    cadence = plan.data.exptime_seconds / 86400.0
    ev = plan.gauntlet.events
    events = per_event_depths(
        series, candidate.period, candidate.t0, candidate.duration, cadence, ev, 0.0, sigma
    )
    if len(events) == 0:
        return None
    measure = comb_measure(detrender.flat, time, series, candidate.duration, half, ev, cadence)
    measured, windows, _ = empirical_events(
        series, candidate, events, ev, cadence, measure, exclude_phase_half
    )
    if len(measured) == 0:
        return None
    expected_in = candidate.duration / cadence
    metas = []
    for centre, n_in in zip(measured.centers.tolist(), measured.n_in.tolist(), strict=True):
        meta = a0.event_meta(
            series.time, series.sector, centre, n_in / expected_in, ev.min_coverage
        )
        if meta is None:
            return None
        metas.append(meta)
    if len({m.sector for m in metas}) not in GRID_SECTORS:
        return None  # the grid holds for the sectors that actually contribute to this statistic
    errors = measured.errors
    if not np.all(np.isfinite(errors) & (errors > MIN_MEASURABLE_ERROR)):
        return None
    weights = 1.0 / np.square(errors)
    weights = weights / np.sum(weights)
    pooled = {s: a0.shortcut(windows, s, seed + s) for s in {m.sector for m in metas}}
    h = a0.half_width(candidate.duration, ev.baseline_outer_durations)
    var = a0.group_variance(weights, errors.tolist(), metas, windows, h, pooled)
    if var is None:
        return None
    return A0Depth(
        float(np.sum(weights * measured.depths)),
        math.sqrt(var),
        len(measured),
        windows,
        tuple(int(e) for e in measured.epochs),
        tuple(float(d) for d in measured.depths),
        tuple(float(w) for w in weights),
        tuple(m.sector for m in metas),
    )


def empirical_events(
    flat, candidate, events, event_params, cadence_days, measure, exclude_phase_half=False
):
    """``a0.empirical_events`` with the windows measured by ``measure`` (``comb_measure``)."""
    from refute.packs.tess.events import EventDepths

    windows = a0.pseudo_windows(
        flat.time,
        flat.sector,
        candidate.period,
        candidate.t0,
        candidate.duration,
        event_params.baseline_outer_durations,
        event_params.min_coverage,
        measure,
        exclude_phase_half=exclude_phase_half,
    )
    expected_in = candidate.duration / cadence_days
    cache: dict[tuple[int, str], tuple[float | None, dict]] = {}
    keep, errors = [], []
    for i, centre in enumerate(events.centers):
        st = a0.stratum(events.n_in[i] / expected_in, event_params.min_coverage)
        sec = a0.sector_of(flat.time, flat.sector, centre)
        if st is None:
            keep.append(False)
            errors.append(float("nan"))
            continue
        if (sec, st) not in cache:
            cache[(sec, st)] = a0.stratum_error(windows, sec, st)
        emp = cache[(sec, st)][0]
        keep.append(emp is not None)
        errors.append(max(float(events.errors[i]), emp) if emp is not None else float("nan"))
    mask = np.asarray(keep, dtype=bool)
    out = EventDepths(
        events.epochs[mask],
        events.centers[mask],
        events.depths[mask],
        np.asarray(errors, dtype=float)[mask],
        events.n_in[mask],
        {**events.dropped, "a0_not_measured": int((~mask).sum())},
    )
    details = {f"{sec}:{st}": info for (sec, st), (_, info) in cache.items()}
    return out, windows, details
