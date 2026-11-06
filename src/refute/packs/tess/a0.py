"""A0 of v0.5.1: the empirical error of an event measurement (docs/plans/v0.5.1-acceptance.md, A0,
revision 2 as adopted under amendment 3).

- **Pseudo-event windows.** An event's window is its in-event span with its baseline bands, of
  half-width ``h = T / 2 + baseline_outer_durations x T``. In each sector, windows are centred on a
  regular grid of spacing ``2 h`` from the sector's first cadence (so they are disjoint); a window
  is kept when it shares no cadence with the window of a real event of the candidate; the
  phase-0.5 window is excluded only when the candidate's own secondary_eclipse detects a secondary
  (amendment 5). Each kept window is measured by the caller's estimator (``measure``), the same as
  for a real event, with its coverage ``c`` (in-event cadences over a full event's); its **coverage
  stratum** is ``full`` (``c >= 0.9``), ``partial`` (``0.7 <= c < 0.9``) or ``minimal``
  (``min_coverage <= c < 0.7``).
- **Per-event error, no scaling.** For a real event of sector ``s`` and stratum ``a``, the ``n``
  pseudo-window values of the same sector and stratum give the ordinary sample variance ``s^2``,
  corrected for the dependence of neighbouring windows: ``sigma^2 = s^2 (n - 1) / (n - n / n_eff)``
  with ``n_eff = n / (1 + 2 sum_{k=1..min(5, n-1)} (1 - k / n) max(0, r_k))``, ``r_k`` the lag-``k``
  correlation of the stratum's values in their grid order within each segment (``r_{k,a,a}``). With
  ``n_eff < 10`` the event has no empirical error. The error used is ``max(model, sigma)``.
- **Group statistics.** ``var(sum w_i d_i) = sum_ij w_i w_j sigma_i sigma_j rho_ij``; for two events
  of the same segment at grid lag ``k <= 5``, of strata ``a`` (the earlier) and ``b`` (the later),
  ``rho_ij = r_{k,a,b}``, the Pearson correlation of the pooled pairs (an earlier window of stratum
  ``a``, the window ``k`` steps later of stratum ``b``), estimable with at least 20 pairs; otherwise
  ``rho_ij = 0``. A needed but non-estimable correlation, a covariance that is not positive
  semidefinite or a non-positive variance: no calibrated error (``None``).
- **The verified shortcut.** The strata of a sector are pooled (every ``r_{k,a,b}`` replaced by the
  pooled ``r_k``) only when every 95 % block-bootstrap interval of ``r_{k,a,b} - r_k`` (lags 1 to 5,
  directional pairs with at least 20 pairs; 200 replicates over the sector's segments) lies within
  ``[-0.1, 0.1]``, with at least 3 segments and at least one term.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass

import numpy as np

MAX_LAG = 5
MIN_EFFECTIVE = 10.0
MIN_PAIRS = 20
MARGIN = 0.1
BOOTSTRAP = 200
SEGMENT_GAP_DAYS = 0.5


@dataclass(frozen=True)
class Window:
    sector: int
    segment: int
    index: int  # the grid position in the sector
    centre: float
    value: float
    coverage: float
    stratum: str


def stratum(coverage: float, min_coverage: float) -> str | None:
    if coverage >= 0.9:
        return "full"
    if coverage >= 0.7:
        return "partial"
    if coverage >= min_coverage:
        return "minimal"
    return None


def half_width(duration: float, baseline_outer_durations: float) -> float:
    return duration / 2.0 + baseline_outer_durations * duration


def _segments(time: np.ndarray) -> np.ndarray:
    """A segment number per cadence: a new segment after a gap above SEGMENT_GAP_DAYS."""
    if time.size == 0:
        return np.zeros(0, dtype=int)
    return np.concatenate([[0], np.cumsum(np.diff(time) > SEGMENT_GAP_DAYS)])


def pseudo_windows(
    time: np.ndarray,
    sector: np.ndarray,
    period: float,
    t0: float,
    duration: float,
    baseline_outer_durations: float,
    min_coverage: float,
    measure: Callable[[float], tuple[float, float] | None],
    exclude_phase_half: bool = True,
) -> list[Window]:
    """The kept, measured pseudo-event windows of every sector. ``measure(centre)`` returns
    ``(value, coverage)`` or ``None`` when the window cannot be measured. ``exclude_phase_half``:
    amendment 5 makes the phase-0.5 exclusion conditional (the caller passes True only when the
    candidate's own secondary_eclipse detected a secondary)."""
    h = half_width(duration, baseline_outer_durations)
    out: list[Window] = []
    for s in np.unique(sector):
        sel = sector == s
        ts = time[sel]
        segs = _segments(ts)
        n = int(math.floor((ts.max() - ts.min()) / (2.0 * h))) + 1
        for g in range(n):
            centre = float(ts.min() + h + 2.0 * g * h)
            # a real event's or the phase-0.5 window would share cadences when centres are
            # closer than 2 h (both windows have half-width h)
            phase = (centre - t0) / period
            off_event = abs(phase - round(phase)) * period
            off_half = abs((phase - 0.5) - round(phase - 0.5)) * period
            if off_event < 2.0 * h or (exclude_phase_half and off_half < 2.0 * h):
                continue
            got = measure(centre)
            if got is None:
                continue
            value, coverage = got
            st = stratum(coverage, min_coverage)
            if st is None or not math.isfinite(value):
                continue
            k = int(np.argmin(np.abs(ts - centre)))
            out.append(Window(int(s), int(segs[k]), g, centre, float(value), coverage, st))
    return out


def _pairs(windows: Sequence[Window], k: int, a: str | None, b: str | None):
    """The (earlier, later) value pairs at grid lag ``k`` in the same sector and segment, the
    earlier of stratum ``a`` and the later of stratum ``b`` (``None``: any stratum)."""
    by_pos = {(w.sector, w.segment, w.index): w for w in windows}
    xs, ys, segs = [], [], []
    for w in windows:
        if a is not None and w.stratum != a:
            continue
        v = by_pos.get((w.sector, w.segment, w.index + k))
        if v is None or (b is not None and v.stratum != b):
            continue
        xs.append(w.value)
        ys.append(v.value)
        segs.append(w.segment)
    return np.asarray(xs), np.asarray(ys), np.asarray(segs)


def _standardized(windows: Sequence[Window]) -> list[Window]:
    """Each value standardized by its stratum's mean and standard deviation over the sector."""
    out = []
    groups: dict[tuple[int, str], list[float]] = {}
    for w in windows:
        groups.setdefault((w.sector, w.stratum), []).append(w.value)
    stats = {
        key: (float(np.mean(v)), float(np.std(v, ddof=1)) if len(v) > 1 else 0.0)
        for key, v in groups.items()
    }
    for w in windows:
        mean, sd = stats[(w.sector, w.stratum)]
        value = (w.value - mean) / sd if sd > 0 else 0.0
        out.append(Window(w.sector, w.segment, w.index, w.centre, value, w.coverage, w.stratum))
    return out


def pearson(x: np.ndarray, y: np.ndarray) -> float | None:
    if x.size < 2:
        return None
    dx, dy = x - x.mean(), y - y.mean()
    den = math.sqrt(float(np.sum(dx * dx) * np.sum(dy * dy)))
    return float(np.sum(dx * dy) / den) if den > 0 else None


def lag_correlation(
    windows: Sequence[Window], k: int, a: str | None, b: str | None, min_pairs: int = MIN_PAIRS
):
    """(r_{k,a,b}, number of pairs) on the standardized values; r is None below ``min_pairs``
    (MIN_PAIRS for the group rule's correlations; the per-stratum ``n_eff`` uses every
    available pair, Codex's end-of-round review of round 3)."""
    x, y, _ = _pairs(_standardized(windows), k, a, b)
    r = pearson(x, y) if x.size >= max(2, min_pairs) else None
    return r, int(x.size)


def effective_count(n: int, r: Sequence[float | None]) -> float:
    """``n / (1 + 2 sum_{k=1..min(5, n-1)} (1 - k / n) max(0, r_k))``; a missing r_k counts 0."""
    if n < 2:
        return float(n)
    total = 0.0
    for k in range(1, min(MAX_LAG, n - 1) + 1):
        rk = r[k - 1] if k - 1 < len(r) else None
        if rk is not None:
            total += (1.0 - k / n) * max(0.0, rk)
    return n / (1.0 + 2.0 * total)


def stratum_error(windows: Sequence[Window], sector: int, st: str) -> tuple[float | None, dict]:
    """The dependence-corrected empirical standard deviation of one sector and stratum, or None
    with ``n_eff < 10``; the diagnostics."""
    sub = [w for w in windows if w.sector == sector and w.stratum == st]
    n = len(sub)
    rk = [lag_correlation(sub, k, st, st, min_pairs=2)[0] for k in range(1, MAX_LAG + 1)]
    neff = effective_count(n, rk)
    info = {"n": n, "n_eff": neff, "r_k": rk}
    if n < 2 or neff < MIN_EFFECTIVE or n - n / neff <= 0:
        return None, info
    s2 = float(np.var([w.value for w in sub], ddof=1))
    return math.sqrt(s2 * (n - 1) / (n - n / neff)), info


@dataclass(frozen=True)
class EventMeta:
    """What the group rule needs to know of a real event."""

    centre: float
    sector: int
    segment: int
    stratum: str


def event_meta(time, sector, centre, coverage, min_coverage) -> EventMeta | None:
    st = stratum(coverage, min_coverage)
    if st is None:
        return None
    sel = sector == sector_of(time, sector, centre)
    ts = time[sel]
    segs = _segments(ts)
    k = int(np.argmin(np.abs(ts - centre)))
    return EventMeta(float(centre), int(sector_of(time, sector, centre)), int(segs[k]), st)


def sector_of(time, sector, centre) -> int:
    return int(sector[int(np.argmin(np.abs(time - centre)))])


def shortcut(windows: Sequence[Window], sector: int, seed: int) -> bool:
    """The verified pooling shortcut of one sector (the equivalence rule)."""
    sub = [w for w in windows if w.sector == sector]
    segments = sorted({w.segment for w in sub})
    if len(segments) < 3:
        return False
    strata = sorted({w.stratum for w in sub})
    terms = [
        (k, a, b)
        for k in range(1, MAX_LAG + 1)
        for a in strata
        for b in strata
        if lag_correlation(sub, k, a, b)[1] >= MIN_PAIRS
    ]
    if not terms:
        return False
    rng = np.random.default_rng(seed)
    diffs = {t: [] for t in terms}
    for _ in range(BOOTSTRAP):
        chosen = rng.choice(segments, size=len(segments), replace=True)
        sample: list[Window] = []
        for j, seg in enumerate(chosen):
            for w in sub:
                if w.segment == seg:
                    # a fresh segment number per draw keeps repeated segments apart
                    sample.append(
                        Window(w.sector, j, w.index, w.centre, w.value, w.coverage, w.stratum)
                    )
        for k, a, b in terms:
            r_ab = lag_correlation(sample, k, a, b)[0]
            r_all = lag_correlation(sample, k, None, None)[0]
            if r_ab is not None and r_all is not None:
                diffs[(k, a, b)].append(r_ab - r_all)
    for values in diffs.values():
        # every one of the BOOTSTRAP replicates must be usable (Codex's end-of-round review)
        if len(values) < BOOTSTRAP:
            return False
        lo, hi = np.percentile(values, [2.5, 97.5])
        if lo < -MARGIN or hi > MARGIN:
            return False
    return True


def group_variance(
    weights: Sequence[float],
    sigmas: Sequence[float],
    events: Sequence[EventMeta],
    windows: Sequence[Window],
    h: float,
    pooled: dict[int, bool],
) -> float | None:
    """The variance of ``sum w_i d_i`` with the A0 correlations, or None (no calibrated error)."""
    n = len(weights)
    cov = np.zeros((n, n))
    cache: dict[tuple, float | None] = {}
    for i in range(n):
        cov[i, i] = sigmas[i] ** 2
        for j in range(i + 1, n):
            ei, ej = events[i], events[j]
            if ei.centre > ej.centre:
                ei, ej = ej, ei
            if ei.sector != ej.sector or ei.segment != ej.segment:
                continue
            k = int(round(abs(ej.centre - ei.centre) / (2.0 * h)))
            if k < 1 or k > MAX_LAG:
                continue
            sub = [w for w in windows if w.sector == ei.sector]
            key = (ei.sector, k, None, None) if pooled.get(ei.sector) else (
                ei.sector, k, ei.stratum, ej.stratum
            )  # fmt: skip
            if key not in cache:
                cache[key] = lag_correlation(sub, k, key[2], key[3])[0]
            r = cache[key]
            if r is None:
                return None
            cov[i, j] = cov[j, i] = sigmas[i] * sigmas[j] * r
    eig = np.linalg.eigvalsh(cov)
    if eig.min() < -1e-12 * max(eig.max(), 0.0):
        return None
    w = np.asarray(weights, dtype=float)
    var = float(w @ cov @ w)
    return var if var > 0 else None


def box_measure(time, flux, duration, baseline_gap_durations, baseline_outer_durations,
                min_coverage, cadence_days):  # fmt: skip
    """The local box depth of ``events.per_event_depths`` at any centre: ``(depth, coverage)``,
    or None when the in-event or baseline coverage is below ``min_coverage``."""
    half = duration / 2.0
    inner = half + baseline_gap_durations * duration
    outer = half + baseline_outer_durations * duration
    expected_in = 2.0 * half / cadence_days
    expected_base = 2.0 * (outer - inner) / cadence_days

    def measure(centre: float):
        lo = np.searchsorted(time, centre - outer, side="left")
        hi = np.searchsorted(time, centre + outer, side="right")
        if hi <= lo:
            return None
        dt = np.abs(time[lo:hi] - centre)
        f = flux[lo:hi]
        in_event, base = dt <= half, dt > inner
        n_in, n_base = int(in_event.sum()), int(base.sum())
        if n_in < min_coverage * expected_in or n_base < min_coverage * expected_base:
            return None
        return float(f[base].mean() - f[in_event].mean()), n_in / expected_in

    return measure


def empirical_events(flat, candidate, events, event_params, cadence_days, exclude_phase_half=False):
    """The events of ``events`` (``EventDepths``) with A0's per-event errors: each event's error
    is ``max(model error, the corrected empirical error of its sector and coverage stratum)``;
    an event whose sector and stratum have ``n_eff < 10`` is dropped (counted in ``dropped`` as
    ``a0_not_measured``). Returns the new ``EventDepths`` and the per-(sector, stratum) details."""
    from refute.packs.tess.events import EventDepths

    measure = box_measure(
        flat.time,
        flat.flux,
        candidate.duration,
        event_params.baseline_gap_durations,
        event_params.baseline_outer_durations,
        event_params.min_coverage,
        cadence_days,
    )
    windows = pseudo_windows(
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
        st = stratum(events.n_in[i] / expected_in, event_params.min_coverage)
        sec = sector_of(flat.time, flat.sector, centre)
        if st is None:
            keep.append(False)
            errors.append(float("nan"))
            continue
        if (sec, st) not in cache:
            cache[(sec, st)] = stratum_error(windows, sec, st)
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


def matched_measure(time, flux, flux_err, shape, half_span, expected_in, min_coverage):
    """WP3 (d)'s estimator at any centre: the **weighted** least-squares amplitude of the
    unit-depth shape ``shape(dt)`` against the flattened baseline 1, with the cadence weights
    ``w = 1 / err^2``: ``sum w s (1 - f) / sum w s^2`` over the cadences within ``half_span`` of
    the centre, with its coverage (cadences where the shape is positive over ``expected_in``);
    None below ``min_coverage``. ``measure_with_info`` also returns the weighted information
    ``sum w s^2``, whose inverse root is the model error (Codex's end-of-round review)."""
    err = np.where(np.isfinite(flux_err) & (flux_err > 0), flux_err, np.nanmedian(flux_err))
    weight = 1.0 / np.square(err)

    def core(centre: float):
        lo = np.searchsorted(time, centre - half_span, side="left")
        hi = np.searchsorted(time, centre + half_span, side="right")
        if hi <= lo:
            return None
        sv = shape(time[lo:hi] - centre)
        n_in = int(np.sum(sv > 0))
        if n_in < min_coverage * expected_in:
            return None
        w = weight[lo:hi]
        info = float(np.sum(w * sv * sv))
        if not info > 0:
            return None
        amp = float(np.sum(w * sv * (1.0 - flux[lo:hi])) / info)
        return amp, n_in / expected_in, info

    def measure(centre: float):
        got = core(centre)
        return None if got is None else (got[0], got[1])

    return measure, core
