"""Two-stage Box Least Squares (BLS) period search.

A single BLS over a multi-year baseline needs an extremely fine frequency grid,
so the search is hierarchical:

**Stage 1 (per sector).** Light curves are binned to ``bin_minutes``. For each
sector, astropy's ``BoxLeastSquares.autopower`` grid covers
``[period_min, min(period_max, sector span / 2)]`` and the ``peaks_per_sector``
strongest distinct peaks are kept, each with its signal detection efficiency
(SDE, peak power in units of the periodogram's standard deviation).

**Clustering.** Peaks from all sectors whose periods agree within
``cluster_tolerance`` are merged. Clusters are ranked by summed SDE and the
``max_clusters`` best are refined, each at P, 2P and P/2.

**Stage 2 (hierarchical refinement).** Starting from the cluster's strongest
sector, data are added in growing time spans: the sector, its contiguous block
of sectors, then other blocks in order of distance in time. At each level the
grid spacing is ``duration * P / (refine_samples_per_width * span)`` and the grid
half-width is ``refine_width_factor * duration * P / previous span``, so the
cycle count across gaps is decided by the data. The refined candidate with the
highest log-likelihood on the full binned data wins.

**Final.** The winner is re-evaluated on the unbinned data with a fine duration
grid, giving the reported period, epoch, duration, depth and SNR.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
from astropy.timeseries import BoxLeastSquares

from refute.packs.tess.events import event_epochs, per_point_sigma
from refute.packs.tess.params import SearchParams
from refute.packs.tess.types import Candidate, LightCurveData

_MAX_GRID = 50_000


@dataclass
class SearchResult:
    candidate: Candidate | None
    diagnostics: dict[str, Any] = field(default_factory=dict)


def bin_lightcurve(lc: LightCurveData, bin_minutes: float) -> LightCurveData:
    """Mean-bin each sector on a fixed grid starting at the sector's first cadence."""
    width = bin_minutes / 1440.0
    parts = []
    for sector in lc.sectors:
        sel = lc.sector == sector
        t, f = lc.time[sel], lc.flux[sel]
        if t.size == 0:
            continue
        index = np.floor((t - t[0]) / width).astype(np.int64)
        _, inverse, counts = np.unique(index, return_inverse=True, return_counts=True)
        tb = np.bincount(inverse, weights=t) / counts
        fb = np.bincount(inverse, weights=f) / counts
        good = counts >= 2
        parts.append(
            (
                tb[good],
                fb[good],
                np.full(good.sum(), sector),
                np.full(good.sum(), int(lc.year[sel][0])),
            )
        )
    if not parts:
        return LightCurveData(np.zeros(0), np.zeros(0), np.zeros(0), np.zeros(0), np.zeros(0))
    time = np.concatenate([p[0] for p in parts])
    flux = np.concatenate([p[1] for p in parts])
    sector_arr = np.concatenate([p[2] for p in parts])
    year_arr = np.concatenate([p[3] for p in parts])
    # Per-bin error: per-sector robust scatter of the binned flux.
    binned = LightCurveData(time, flux, np.ones_like(flux), sector_arr, year_arr)
    err = per_point_sigma(binned)
    return LightCurveData(binned.time, binned.flux, err, binned.sector, binned.year)


def _bls(lc: LightCurveData) -> BoxLeastSquares:
    return BoxLeastSquares(lc.time, lc.flux, dy=lc.flux_err)


def _top_peaks(periods: np.ndarray, power: np.ndarray, k: int, tolerance: float) -> list[int]:
    chosen: list[int] = []
    for index in np.argsort(-power, kind="stable"):
        if not np.isfinite(power[index]):
            continue
        period = periods[index]
        if all(abs(period - periods[j]) / periods[j] > tolerance for j in chosen):
            chosen.append(int(index))
            if len(chosen) == k:
                break
    return chosen


def _blocks(lc: LightCurveData, gap_days: float) -> list[list[int]]:
    spans = sorted(
        (float(lc.time[lc.sector == s].min()), float(lc.time[lc.sector == s].max()), s)
        for s in lc.sectors
    )
    blocks: list[list[int]] = []
    last_end = None
    for start, end, sector in spans:
        if last_end is None or start - last_end > gap_days:
            blocks.append([sector])
        else:
            blocks[-1].append(sector)
        last_end = end if last_end is None else max(last_end, end)
    return blocks


def _levels(lc: LightCurveData, ref_sector: int, gap_days: float) -> list[np.ndarray]:
    blocks = _blocks(lc, gap_days)
    ref_block = next(b for b in blocks if ref_sector in b)

    def mid(block: list[int]) -> float:
        sel = np.isin(lc.sector, block)
        return float(0.5 * (lc.time[sel].min() + lc.time[sel].max()))

    others = sorted(
        (b for b in blocks if b is not ref_block), key=lambda b: abs(mid(b) - mid(ref_block))
    )
    levels = [lc.sector == ref_sector]
    included = list(ref_block)
    if len(ref_block) > 1:
        levels.append(np.isin(lc.sector, included))
    for block in others:
        included.extend(block)
        levels.append(np.isin(lc.sector, included))
    return levels


def _valid_durations(durations: np.ndarray, min_period: float) -> np.ndarray:
    return durations[durations < 0.9 * min_period]


def _refine(
    binned: LightCurveData,
    seed_period: float,
    seed_duration: float,
    ref_sector: int,
    durations: np.ndarray,
    params: SearchParams,
) -> tuple[float, float]:
    period, duration = seed_period, seed_duration
    previous_span: float | None = None
    for level in _levels(binned, ref_sector, params.block_gap_days):
        data = binned.select(level)
        span = data.span
        if span <= 0:
            continue
        if previous_span is not None and span <= previous_span * 1.0001:
            continue
        if previous_span is None:
            half_width = 2.0 * params.refine_width_factor * duration * period / span
        else:
            half_width = params.refine_width_factor * duration * period / previous_span
        step = duration * period / (params.refine_samples_per_width * span)
        n = int(min(np.ceil(half_width / step), _MAX_GRID))
        grid = period + step * np.arange(-n, n + 1)
        grid = grid[(grid >= params.period_min_days) & (grid <= params.period_max_days)]
        if grid.size == 0:
            break
        near = durations[(durations >= 0.5 * duration) & (durations <= 2.0 * duration)]
        near = _valid_durations(near if near.size else durations, grid.min())
        if near.size == 0:
            break
        result = _bls(data).power(grid, near, objective="likelihood")
        best = int(np.nanargmax(result.power))
        period, duration = float(grid[best]), float(result.duration[best])
        previous_span = span
    return period, duration


def count_transits(lc: LightCurveData, period: float, t0: float, duration: float) -> int:
    count = 0
    for epoch in event_epochs(lc.time, period, t0):
        center = t0 + epoch * period
        lo = np.searchsorted(lc.time, center - duration / 2, side="left")
        hi = np.searchsorted(lc.time, center + duration / 2, side="right")
        count += hi > lo
    return int(count)


def finalize_candidate(
    lc: LightCurveData,
    period: float,
    duration_hint: float,
    params: SearchParams,
    sde: float,
    sigma: np.ndarray | None = None,
) -> Candidate:
    """Evaluate one period on unbinned data with a fine duration grid."""
    if sigma is None:
        sigma = per_point_sigma(lc)
    fine = duration_hint * np.linspace(0.5, 1.5, params.final_duration_steps)
    fine = fine[(fine < 0.9 * period) & (fine > 3.0 / 1440.0)]
    if fine.size == 0:
        fine = np.array([min(duration_hint, 0.5 * period)])
    model = BoxLeastSquares(lc.time, lc.flux, dy=sigma)
    # Fine period scan: +-1 refinement step, at one tenth of the step.
    span = lc.span if lc.span > 0 else period
    step = duration_hint * period / (params.refine_samples_per_width * span)
    periods = period + step * np.linspace(-1.0, 1.0, 21)
    result = model.power(periods, fine, objective="likelihood", oversample=params.final_oversample)
    best = int(np.nanargmax(result.power))
    best_period = float(periods[best])
    t0 = float(result.transit_time[best])
    duration = float(result.duration[best])
    return Candidate(
        period=best_period,
        t0=t0,
        duration=duration,
        depth=float(result.depth[best]),
        depth_err=float(result.depth_err[best]),
        snr=float(result.depth_snr[best]),
        log_likelihood=float(result.log_likelihood[best]),
        sde=float(sde),
        n_transits=count_transits(lc, best_period, t0, duration),
    )


def search_period(lc: LightCurveData, params: SearchParams) -> SearchResult:
    """Find the strongest periodic box signal in a detrended light curve."""
    durations = np.asarray(params.durations_hours, dtype=float) / 24.0
    binned = bin_lightcurve(lc, params.bin_minutes)
    diagnostics: dict[str, Any] = {"stage1": [], "clusters": [], "refined": []}
    if len(binned) < 10:
        diagnostics["reason"] = "too few binned points"
        return SearchResult(None, diagnostics)

    peaks = []
    for sector in binned.sectors:
        data = binned.select(binned.sector == sector)
        max_period = min(params.period_max_days, data.span / 2.0)
        if max_period <= params.period_min_days or len(data) < 20:
            continue
        valid = _valid_durations(durations, params.period_min_days)
        model = _bls(data)
        periods = model.autoperiod(
            valid,
            minimum_period=params.period_min_days,
            maximum_period=max_period,
            minimum_n_transit=2,
            frequency_factor=params.frequency_factor,
        )
        result = model.power(periods, valid, objective="likelihood")
        power = np.asarray(result.power, dtype=float)
        finite = np.isfinite(power)
        if finite.sum() < 10:
            continue
        mean, std = float(power[finite].mean()), float(power[finite].std())
        for index in _top_peaks(periods, power, params.peaks_per_sector, params.cluster_tolerance):
            sde = (power[index] - mean) / std if std > 0 else 0.0
            peaks.append(
                {
                    "sector": int(sector),
                    "period": float(periods[index]),
                    "duration": float(result.duration[index]),
                    "sde": float(sde),
                }
            )
    diagnostics["stage1"] = peaks
    if not peaks:
        diagnostics["reason"] = "no sector long enough for stage 1"
        return SearchResult(None, diagnostics)

    clusters: list[dict[str, Any]] = []
    for peak in sorted(peaks, key=lambda p: (-p["sde"], p["period"])):
        for cluster in clusters:
            if (
                abs(peak["period"] - cluster["period"]) / cluster["period"]
                <= params.cluster_tolerance
            ):
                cluster["members"].append(peak)
                cluster["score"] += peak["sde"]
                break
        else:
            clusters.append({"period": peak["period"], "members": [peak], "score": peak["sde"]})
    clusters.sort(key=lambda c: (-c["score"], c["period"]))
    clusters = clusters[: params.max_clusters]
    diagnostics["clusters"] = [
        {"period": c["period"], "score": c["score"], "n_members": len(c["members"])}
        for c in clusters
    ]

    all_durations = _valid_durations(durations, params.period_min_days)
    full_model = _bls(binned)
    best: tuple[float, float, float, float] | None = None  # (loglike, period, duration, sde)
    for cluster in clusters:
        seed = cluster["members"][0]
        for factor in (1.0, 2.0, 0.5):
            start = seed["period"] * factor
            if not params.period_min_days <= start <= params.period_max_days:
                continue
            period, duration = _refine(
                binned, start, seed["duration"], seed["sector"], durations, params
            )
            usable = _valid_durations(all_durations, period)
            if usable.size == 0:
                continue
            evaluation = full_model.power(np.array([period]), usable, objective="likelihood")
            loglike = float(evaluation.power[0])
            diagnostics["refined"].append(
                {
                    "seed_period": seed["period"],
                    "factor": factor,
                    "period": period,
                    "duration": float(evaluation.duration[0]),
                    "log_likelihood": loglike,
                }
            )
            if best is None or loglike > best[0]:
                best = (loglike, period, float(evaluation.duration[0]), seed["sde"])
    if best is None:
        diagnostics["reason"] = "no refinement succeeded"
        return SearchResult(None, diagnostics)
    _, period, duration, sde = best
    candidate = finalize_candidate(lc, period, duration, params, sde)
    return SearchResult(candidate, diagnostics)
