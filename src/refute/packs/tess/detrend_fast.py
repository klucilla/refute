"""The detrending of ``detrend.py``, batched per segment, for battery version 4 (v0.5.2).

The same operations and conventions as the reference (the knots, the windows, the clipping loop,
its stopping rules, the blend between knots, the upper clip), with the knots of a segment solved
together: the 3x3 normal equations in place of ``lstsq``, and sorted arrays in place of one median
call per knot. The system is solved in the time rescaled to [-1, 1] over the kept cadences of each
knot. A knot leaves the batch and goes to the reference ``detrend._fit_quadratic`` whenever the
batch could differ in a decision or lose accuracy: a non-finite flux, a poorly conditioned system,
a median absolute deviation at rounding level (a noise-free or constant flux, whose later upper
clip depends on the rounding), or a residual within ``BOUNDARY_TOLERANCE`` of the clipping
threshold. A cadence within that tolerance of the final upper clip sends the whole curve to the
reference detrending. Knots are solved in blocks of ``CHUNK_ROWS``, so that the arrays stay small.
Equivalence with the reference is a measured property, not an exact one, and it is tested under
tolerances frozen before the evaluation (docs/validation/v0.5.2/stage2/fast-detrend-equivalence.md).

``MaskAwareDetrender`` is the mask-aware preprocessing of A0 version 4: a detrending under a base
mask, then detrendings under the base mask plus further cadences. A knot whose window lost no
cadence to the further mask holds the same data as under the base mask, so its fit is reused.

Battery versions 3 and earlier never import this module.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from refute.packs.tess.detrend import _fit_quadratic, robust_sigma, segment_slices
from refute.packs.tess.detrend import detrend as _reference_detrend
from refute.packs.tess.params import DetrendParams
from refute.packs.tess.types import LightCurveData

BOUNDARY_TOLERANCE = 1e-9
BOUNDARY_FLOOR = 1e-13
CONDITION_LIMIT = 2e4
ROUNDING_SPREAD = 1e-12
CHUNK_ROWS = 24


@dataclass
class _KnotFits:
    """The fits of one segment under one mask, knot by knot."""

    knots: np.ndarray
    counts: np.ndarray
    coef: np.ndarray
    has: np.ndarray


def _near(values: np.ndarray, limit: np.ndarray) -> np.ndarray:
    """Whether each value is within the tolerance of its limit."""
    return np.abs(values - limit) <= np.maximum(BOUNDARY_TOLERANCE * np.abs(limit), BOUNDARY_FLOOR)


def _condition_bound(n, s1, s2, s3, s4) -> np.ndarray:
    """An upper bound of the 2-norm condition number of each normal matrix: the Frobenius
    condition number, in closed form through the adjugate of the matrix divided by ``n``."""
    b, c, e, f = s1 / n, s2 / n, s3 / n, s4 / n
    a00, a01, a02 = c * f - e * e, c * e - b * f, b * e - c * c
    a11, a12, a22 = f - c * c, b * c - e, c - b * b
    det = a00 + b * a01 + c * a02
    size = 1.0 + 2.0 * b * b + 3.0 * c * c + 2.0 * e * e + f * f
    inverse = a00 * a00 + 2.0 * a01 * a01 + 2.0 * a02 * a02
    inverse += a11 * a11 + 2.0 * a12 * a12 + a22 * a22
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.sqrt(size * inverse) / np.abs(det)


def _middle(ordered: np.ndarray, count: np.ndarray) -> np.ndarray:
    """The median of each row of ``ordered`` (ascending, NaN last), of ``count`` real values."""
    rows = np.arange(ordered.shape[0])
    return 0.5 * (ordered[rows, (count - 1) // 2] + ordered[rows, count // 2])


def _fit_batch(
    x: np.ndarray, y: np.ndarray, valid: np.ndarray, params: DetrendParams
) -> tuple[np.ndarray, np.ndarray]:
    """The robust quadratic of every row: (coefficients, whether the row has them)."""
    size = x.shape[0]
    coef = np.full((size, 3), np.nan)
    has = np.zeros(size, dtype=bool)
    keep = valid.copy()
    send_back = np.any(valid & ~np.isfinite(y), axis=1)
    active = np.flatnonzero(~send_back)
    floor = max(params.min_points_per_knot, 3)
    for _ in range(params.clip_iterations + 1):
        if active.size == 0:
            break
        w = keep[active]
        n = np.count_nonzero(w, axis=1)
        enough = n >= floor
        active, w, n = active[enough], w[enough], n[enough]
        if active.size == 0:
            break
        xa, ya = x[active], y[active]
        top, bottom = np.where(w, xa, -np.inf).max(axis=1), np.where(w, xa, np.inf).min(axis=1)
        centre_x, scale = 0.5 * (top + bottom), 0.5 * (top - bottom)
        spread_out = scale > 0
        if not spread_out.all():
            send_back[active[~spread_out]] = True
            active, w, n, xa, ya = (
                active[spread_out], w[spread_out], n[spread_out], xa[spread_out], ya[spread_out]
            )  # fmt: skip
            centre_x, scale = centre_x[spread_out], scale[spread_out]
            if active.size == 0:
                break
        u = (xa - centre_x[:, None]) / scale[:, None]
        u2 = u * u
        xw, x2w = u * w, u2 * w
        s1, s2 = xw.sum(axis=1), x2w.sum(axis=1)
        s3, s4 = (x2w * u).sum(axis=1), (x2w * u2).sum(axis=1)
        matrix = np.empty((active.size, 3, 3))
        matrix[:, 0, 0], matrix[:, 0, 1], matrix[:, 0, 2] = n, s1, s2
        matrix[:, 1, 0], matrix[:, 1, 1], matrix[:, 1, 2] = s1, s2, s3
        matrix[:, 2, 0], matrix[:, 2, 1], matrix[:, 2, 2] = s2, s3, s4
        rhs = np.column_stack([(ya * w).sum(axis=1), (ya * xw).sum(axis=1), (ya * x2w).sum(axis=1)])
        good = _condition_bound(n, s1, s2, s3, s4) <= CONDITION_LIMIT
        if not good.all():
            send_back[active[~good]] = True
            active, w, n, u, u2, ya = active[good], w[good], n[good], u[good], u2[good], ya[good]
            centre_x, scale, matrix, rhs = centre_x[good], scale[good], matrix[good], rhs[good]
            if active.size == 0:
                break
        solved = np.linalg.solve(matrix, rhs[..., None])[..., 0]
        resid = ya - (solved[:, 0, None] + solved[:, 1, None] * u + solved[:, 2, None] * u2)
        in_use = np.where(w, resid, np.nan)
        centre = _middle(np.sort(in_use, axis=1), n)
        spread = _middle(np.sort(np.abs(in_use - centre[:, None]), axis=1), n)
        a, b, d = solved[:, 0], solved[:, 1], solved[:, 2]
        coef[active, 0] = a - b * centre_x / scale + d * (centre_x / scale) ** 2
        coef[active, 1] = b / scale - 2.0 * d * centre_x / scale**2
        coef[active, 2] = d / scale**2
        has[active] = True
        degenerate = ~(np.isfinite(spread) & (spread > ROUNDING_SPREAD))
        limit = params.clip_sigma * 1.4826 * spread
        with np.errstate(invalid="ignore"):
            size_r = np.abs(resid)
            near = np.any(w & _near(size_r, limit[:, None]), axis=1)
            stays = w & (size_r <= limit[:, None])
        unsafe = degenerate | near
        send_back[active[unsafe]] = True
        keep[active] = stays
        moved = np.any(stays != w, axis=1)
        active = active[moved & ~unsafe]
    for row in np.flatnonzero(send_back):
        own = valid[row]
        fit = _fit_quadratic(x[row, own], y[row, own], params)
        has[row] = fit is not None
        coef[row] = np.nan if fit is None else fit
    return coef, has


def _fits(
    time: np.ndarray,
    flux: np.ndarray,
    keep: np.ndarray,
    params: DetrendParams,
    base: _KnotFits | None,
) -> _KnotFits:
    """Every knot's fit in one segment; a knot with the base's cadences reuses the base's fit."""
    good_t, good_f = time[keep], flux[keep]
    half = params.window_days / 2.0
    knots = np.arange(time[0], time[-1] + params.knot_spacing_days, params.knot_spacing_days)
    lo = np.searchsorted(good_t, knots - half, side="left")
    hi = np.searchsorted(good_t, knots + half, side="right")
    counts = hi - lo
    coef = np.full((knots.size, 3), np.nan)
    has = np.zeros(knots.size, dtype=bool)
    todo = counts >= params.min_points_per_knot
    if base is not None:
        same = counts == base.counts
        coef[same] = base.coef[same]
        has[same] = base.has[same]
        todo &= ~same
    pending = np.flatnonzero(todo)
    for start in range(0, pending.size, CHUNK_ROWS):
        rows = pending[start : start + CHUNK_ROWS]
        widest = int(counts[rows].max())
        offsets = np.arange(widest)
        valid = offsets[None, :] < counts[rows, None]
        picks = np.minimum(lo[rows, None] + offsets[None, :], good_t.size - 1)
        x = np.where(valid, good_t[picks] - knots[rows, None], 0.0)
        y = np.where(valid, good_f[picks], 0.0)
        coef[rows], has[rows] = _fit_batch(x, y, valid, params)
    return _KnotFits(knots, counts, coef, has)


def _trend_of(time, flux, keep, fits: _KnotFits) -> np.ndarray:
    """The reference ``_segment_trend`` from the knots' fits."""
    if not np.any(keep):
        level = float(np.median(flux)) if flux.size else 1.0
        return np.full(time.size, level)
    kt, cf = fits.knots[fits.has], fits.coef[fits.has]
    if kt.size == 0:
        return np.full(time.size, float(np.median(flux[keep])))

    def evaluate(index: np.ndarray) -> np.ndarray:
        x = time - kt[index]
        return cf[index, 0] + cf[index, 1] * x + cf[index, 2] * x * x

    if kt.size == 1:
        return evaluate(np.zeros(time.size, dtype=int))
    right = np.clip(np.searchsorted(kt, time, side="right"), 1, kt.size - 1)
    left = right - 1
    weight = np.clip((time - kt[left]) / (kt[right] - kt[left]), 0.0, 1.0)
    return (1.0 - weight) * evaluate(left) + weight * evaluate(right)


class MaskAwareDetrender:
    """The detrending of ``lc`` under a base mask and under the base mask plus further cadences."""

    def __init__(
        self, lc: LightCurveData, params: DetrendParams, base_mask: np.ndarray | None = None
    ) -> None:
        self.lc = lc
        self.params = params
        self.base = (
            np.zeros(len(lc), dtype=bool)
            if base_mask is None
            else np.asarray(base_mask, dtype=bool)
        )
        if self.base.shape != (len(lc),):
            raise ValueError("mask must have one entry per cadence")
        self.segments = segment_slices(lc.time, params.segment_gap_days)
        self.base_fits = [
            _fits(lc.time[s], lc.flux[s], ~self.base[s], params, None) for s in self.segments
        ]

    def _finish(self, exclude: np.ndarray, fits: list[_KnotFits]) -> LightCurveData:
        lc, params = self.lc, self.params
        trend = np.empty(len(lc))
        for seg, fit in zip(self.segments, fits, strict=True):
            trend[seg] = _trend_of(lc.time[seg], lc.flux[seg], ~exclude[seg], fit)
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
                limit = params.upper_clip_sigma * sigma
                if np.any(_near(flat[in_sector & keep] - 1.0, np.asarray(limit))):
                    return _reference_detrend(lc, params, mask=exclude)
                keep &= ~(in_sector & (flat - 1.0 > limit))
        return LightCurveData(lc.time[keep], flat[keep], err[keep], lc.sector[keep], lc.year[keep])

    def flat(self, extra: np.ndarray | None = None) -> LightCurveData:
        """The flattened curve with ``extra`` masked besides the base mask."""
        if extra is None:
            return self._finish(self.base, self.base_fits)
        exclude = self.base | np.asarray(extra, dtype=bool)
        if exclude.shape != (len(self.lc),):
            raise ValueError("mask must have one entry per cadence")
        lc, params = self.lc, self.params
        fits = []
        for seg, base in zip(self.segments, self.base_fits, strict=True):
            changed = np.any(exclude[seg] != self.base[seg])
            fits.append(
                _fits(lc.time[seg], lc.flux[seg], ~exclude[seg], params, base) if changed else base
            )
        return self._finish(exclude, fits)


class AdditiveDetrender:
    """``battery.additive_residuals`` under a base mask and under the base mask plus further
    cadences: per sector, then per segment of the sector, ``values`` minus the local trend."""

    def __init__(self, time, values, sector, params: DetrendParams, base_mask) -> None:
        self.time, self.values, self.sector = time, values, sector
        self.params = params
        self.base = np.asarray(base_mask, dtype=bool)
        self.parts = []
        for s in np.unique(sector):
            idx = np.nonzero(sector == s)[0]
            segs = segment_slices(time[idx], params.segment_gap_days)
            fits = [
                _fits(time[idx][g], values[idx][g], ~self.base[idx][g], params, None) for g in segs
            ]
            self.parts.append((idx, segs, fits))

    def residuals(self, extra: np.ndarray | None = None) -> np.ndarray:
        exclude = self.base if extra is None else self.base | np.asarray(extra, dtype=bool)
        out = np.full(self.time.size, np.nan)
        for idx, segs, base_fits in self.parts:
            t, v, m = self.time[idx], self.values[idx], exclude[idx]
            res = np.empty(t.size)
            for g, base in zip(segs, base_fits, strict=True):
                changed = extra is not None and np.any(m[g] != self.base[idx][g])
                fit = _fits(t[g], v[g], ~m[g], self.params, base) if changed else base
                res[g] = v[g] - _trend_of(t[g], v[g], ~m[g], fit)
            out[idx] = res
        return out

    def flat(self, extra: np.ndarray | None = None) -> LightCurveData:
        """The series ``1 + residual`` at the cadences where the residual is finite."""
        resid = self.residuals(extra)
        ok = np.isfinite(resid)
        count = int(ok.sum())
        return LightCurveData(
            self.time[ok], 1.0 + resid[ok], np.ones(count), self.sector[ok], np.zeros(count)
        )


def detrend(
    lc: LightCurveData, params: DetrendParams, mask: np.ndarray | None = None
) -> LightCurveData:
    """``detrend.detrend`` through the batched fits."""
    return MaskAwareDetrender(lc, params, mask).flat()
