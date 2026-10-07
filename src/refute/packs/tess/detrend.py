"""Deterministic detrending: robust local quadratic fits on knots, blended between knots.

For each contiguous segment (split at gaps longer than ``segment_gap_days``), knots
are placed every ``knot_spacing_days``. At each knot, a quadratic in time is fitted
by least squares to the *unmasked* flux within ``window_days`` centered on the
knot, with ``clip_iterations`` rounds of symmetric ``clip_sigma`` clipping (robust
standard deviation). The trend at a cadence between knots k and k+1 is the
linear blend of the two knots' quadratics evaluated at that cadence. A quadratic
removes the curvature of stellar variability that a running median would leave
behind. Masked points (for example in-transit points) never contribute to the
trend, but are still divided by it.

After division, points more than ``upper_clip_sigma`` robust standard deviations
*above* 1 are removed (flares, cosmic rays). Points below are never clipped, so
transits and eclipses are never removed by detrending.
"""

from __future__ import annotations

import numpy as np

from refute.packs.tess.params import DetrendParams
from refute.packs.tess.types import LightCurveData


def robust_sigma(values: np.ndarray) -> float:
    """1.4826 times the median absolute deviation (falls back to the standard deviation)."""
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return float("nan")
    mad = float(np.median(np.abs(values - np.median(values))))
    if mad > 0:
        return 1.4826 * mad
    return float(np.std(values)) if values.size > 1 else float("nan")


def segment_slices(time: np.ndarray, gap_days: float) -> list[slice]:
    if time.size == 0:
        return []
    breaks = np.nonzero(np.diff(time) > gap_days)[0] + 1
    edges = [0, *breaks.tolist(), time.size]
    return [slice(edges[i], edges[i + 1]) for i in range(len(edges) - 1)]


def _fit_quadratic(x: np.ndarray, y: np.ndarray, params: DetrendParams) -> np.ndarray | None:
    """Robust quadratic fit; returns coefficients (c0, c1, c2) of c0 + c1*x + c2*x**2."""
    keep = np.ones(x.size, dtype=bool)
    coef = None
    for _ in range(params.clip_iterations + 1):
        if keep.sum() < max(params.min_points_per_knot, 3):
            return coef
        design = np.column_stack([np.ones(keep.sum()), x[keep], x[keep] ** 2])
        coef, *_ = np.linalg.lstsq(design, y[keep], rcond=None)
        resid = y - (coef[0] + coef[1] * x + coef[2] * x * x)
        sigma = robust_sigma(resid[keep])
        if not np.isfinite(sigma) or sigma <= 0:
            break
        new_keep = keep & (np.abs(resid) <= params.clip_sigma * sigma)
        if np.array_equal(new_keep, keep):
            break
        keep = new_keep
    return coef


def _segment_trend(
    time: np.ndarray, flux: np.ndarray, keep: np.ndarray, params: DetrendParams
) -> np.ndarray:
    good_t = time[keep]
    good_f = flux[keep]
    if good_t.size == 0:
        level = float(np.median(flux)) if flux.size else 1.0
        return np.full(time.size, level)
    half = params.window_days / 2.0
    knots = np.arange(time[0], time[-1] + params.knot_spacing_days, params.knot_spacing_days)
    lo_idx = np.searchsorted(good_t, knots - half, side="left")
    hi_idx = np.searchsorted(good_t, knots + half, side="right")
    knot_t, coefs = [], []
    for knot, lo, hi in zip(knots, lo_idx, hi_idx, strict=True):
        if hi - lo < params.min_points_per_knot:
            continue
        coef = _fit_quadratic(good_t[lo:hi] - knot, good_f[lo:hi], params)
        if coef is not None:
            knot_t.append(knot)
            coefs.append(coef)
    if not knot_t:
        return np.full(time.size, float(np.median(good_f)))
    kt = np.asarray(knot_t)
    cf = np.asarray(coefs)

    def evaluate(index: np.ndarray) -> np.ndarray:
        x = time - kt[index]
        return cf[index, 0] + cf[index, 1] * x + cf[index, 2] * x * x

    right = (
        np.clip(np.searchsorted(kt, time, side="right"), 1, kt.size - 1) if kt.size > 1 else None
    )
    if right is None:
        return evaluate(np.zeros(time.size, dtype=int))
    left = right - 1
    weight = np.clip((time - kt[left]) / (kt[right] - kt[left]), 0.0, 1.0)
    return (1.0 - weight) * evaluate(left) + weight * evaluate(right)


def detrend(
    lc: LightCurveData, params: DetrendParams, mask: np.ndarray | None = None
) -> LightCurveData:
    """Return a flattened copy of ``lc``. ``mask`` marks points excluded from the trend."""
    exclude = np.zeros(len(lc), dtype=bool) if mask is None else np.asarray(mask, dtype=bool)
    if exclude.shape != (len(lc),):
        raise ValueError("mask must have one entry per cadence")
    trend = np.empty(len(lc))
    for seg in segment_slices(lc.time, params.segment_gap_days):
        trend[seg] = _segment_trend(lc.time[seg], lc.flux[seg], ~exclude[seg], params)
    trend = np.where(np.isfinite(trend) & (trend > 0), trend, 1.0)
    flat = lc.flux / trend
    err = lc.flux_err / trend

    keep = np.isfinite(flat) & np.isfinite(err)
    for sector in np.unique(lc.sector):
        in_sector = lc.sector == sector
        reference = in_sector & ~exclude & keep
        if not np.any(reference):
            reference = in_sector & keep
        sigma = robust_sigma(flat[reference] - 1.0)
        if np.isfinite(sigma) and sigma > 0:
            keep &= ~(in_sector & (flat - 1.0 > params.upper_clip_sigma * sigma))
    return LightCurveData(lc.time[keep], flat[keep], err[keep], lc.sector[keep], lc.year[keep])
