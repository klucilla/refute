"""Per-event measurements: transit masks and local box depths of individual events.

An *event* is one predicted transit (or one phase-0.5 window). Its depth is the
mean flux of a local baseline band minus the mean flux inside the event, so slow
residual trends cancel. Group means use the larger of the white-noise error and
the empirical scatter of the individual depths, which absorbs red noise and real
event-to-event variation.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from refute.packs.tess.detrend import robust_sigma
from refute.packs.tess.params import EventParams
from refute.packs.tess.types import LightCurveData


def phase_offset_days(time: np.ndarray, period: float, t0: float) -> np.ndarray:
    """Signed time from the nearest transit center, in days (range [-P/2, P/2))."""
    return np.mod(time - t0 + 0.5 * period, period) - 0.5 * period


def transit_mask(time: np.ndarray, period: float, t0: float, half_width: float) -> np.ndarray:
    return np.abs(phase_offset_days(np.asarray(time, dtype=float), period, t0)) <= half_width


def event_epochs(time: np.ndarray, period: float, t0: float, phase: float = 0.0) -> np.ndarray:
    if time.size == 0:
        return np.zeros(0, dtype=int)
    first = int(np.floor((time.min() - t0) / period - phase)) - 1
    last = int(np.ceil((time.max() - t0) / period - phase)) + 1
    return np.arange(first, last + 1)


def per_point_sigma(lc: LightCurveData, exclude: np.ndarray | None = None) -> np.ndarray:
    """Robust per-sector noise estimate assigned to every point."""
    sigma = np.empty(len(lc))
    exclude = np.zeros(len(lc), dtype=bool) if exclude is None else exclude
    for sector in np.unique(lc.sector):
        sel = lc.sector == sector
        ref = sel & ~exclude
        value = robust_sigma(lc.flux[ref] if np.any(ref) else lc.flux[sel])
        if not np.isfinite(value) or value <= 0:
            value = float(np.nanmedian(lc.flux_err[sel])) if np.any(sel) else 1e-3
        sigma[sel] = value
    return sigma


@dataclass
class EventDepths:
    epochs: np.ndarray
    centers: np.ndarray
    depths: np.ndarray
    errors: np.ndarray
    n_in: np.ndarray

    def __len__(self) -> int:
        return int(self.epochs.size)

    def subset(self, mask: np.ndarray) -> EventDepths:
        return EventDepths(
            self.epochs[mask],
            self.centers[mask],
            self.depths[mask],
            self.errors[mask],
            self.n_in[mask],
        )


def per_event_depths(
    lc: LightCurveData,
    period: float,
    t0: float,
    duration: float,
    cadence_days: float,
    params: EventParams,
    phase: float = 0.0,
    sigma: np.ndarray | None = None,
) -> EventDepths:
    """Local box depth of every event with enough in-event and baseline coverage."""
    if sigma is None:
        sigma = per_point_sigma(lc, transit_mask(lc.time, period, t0, duration))
    half = duration / 2.0
    inner = half + params.baseline_gap_durations * duration
    outer = half + params.baseline_outer_durations * duration
    expected_in = 2.0 * half / cadence_days
    expected_base = 2.0 * (outer - inner) / cadence_days
    rows = []
    for epoch in event_epochs(lc.time, period, t0, phase):
        center = t0 + (epoch + phase) * period
        lo = np.searchsorted(lc.time, center - outer, side="left")
        hi = np.searchsorted(lc.time, center + outer, side="right")
        if hi <= lo:
            continue
        dt = np.abs(lc.time[lo:hi] - center)
        flux = lc.flux[lo:hi]
        sig = sigma[lo:hi]
        in_event = dt <= half
        base = dt > inner
        n_in, n_base = int(in_event.sum()), int(base.sum())
        if n_in < params.min_coverage * expected_in or n_base < params.min_coverage * expected_base:
            continue
        depth = float(flux[base].mean() - flux[in_event].mean())
        err = float(
            np.sqrt(np.sum(sig[in_event] ** 2) / n_in**2 + np.sum(sig[base] ** 2) / n_base**2)
        )
        rows.append((int(epoch), center, depth, err, n_in))
    if not rows:
        empty = np.zeros(0)
        return EventDepths(np.zeros(0, dtype=int), empty, empty, empty, np.zeros(0, dtype=int))
    arr = list(zip(*rows, strict=True))
    return EventDepths(
        np.asarray(arr[0], dtype=int),
        np.asarray(arr[1], dtype=float),
        np.asarray(arr[2], dtype=float),
        np.asarray(arr[3], dtype=float),
        np.asarray(arr[4], dtype=int),
    )


@dataclass(frozen=True)
class GroupMean:
    mean: float
    error: float
    n: int
    white_error: float
    scatter_error: float | None

    def to_dict(self) -> dict:
        return {
            "mean": self.mean,
            "error": self.error,
            "n": self.n,
            "white_error": self.white_error,
            "scatter_error": self.scatter_error,
        }


def group_mean(depths: np.ndarray, errors: np.ndarray) -> GroupMean:
    """Weighted mean with error = max(white-noise error, scatter / sqrt(n)) when n >= 3."""
    n = int(depths.size)
    if n == 0:
        return GroupMean(float("nan"), float("nan"), 0, float("nan"), None)
    weights = 1.0 / np.square(errors)
    mean = float(np.sum(weights * depths) / np.sum(weights))
    white = float(1.0 / np.sqrt(np.sum(weights)))
    scatter = float(np.std(depths, ddof=1) / np.sqrt(n)) if n >= 3 else None
    error = max(white, scatter) if scatter is not None else white
    return GroupMean(mean, error, n, white, scatter)
