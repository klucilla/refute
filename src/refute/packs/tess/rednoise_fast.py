"""The A1 noise estimate of ``rednoise.py`` with its loops over cadences replaced by array
operations, for battery version 4 (v0.5.2). The same runs, the same bins, the same estimate; the
equivalence is tested under criteria frozen before the evaluation
(docs/validation/v0.5.2/stage2/fast-detrend-equivalence.md). Versions 3 and earlier never import it.
"""

from __future__ import annotations

import numpy as np

from refute.packs.tess.detrend import robust_sigma
from refute.packs.tess.rednoise import EventNoise, NoiseEstimate, SectorNoise


def segments(
    time: np.ndarray, keep: np.ndarray, gap_split: float, cadence_days: float
) -> list[np.ndarray]:
    """``rednoise.segments``: index arrays of the runs of consecutive kept cadences."""
    index = np.flatnonzero(np.asarray(keep, dtype=bool))
    if index.size == 0:
        return []
    time = np.asarray(time, dtype=float)
    apart = (np.diff(index) != 1) | (np.diff(time[index]) > gap_split * cadence_days)
    return np.split(index, np.flatnonzero(apart) + 1)


def bin_matrix(
    time: np.ndarray, keep: np.ndarray, n: int, gap_split: float, cadence_days: float
) -> np.ndarray:
    """The complete bins of ``n`` cadences, one row each, in ``rednoise.bins``'s order."""
    if n < 1:
        raise ValueError("the bin size must be at least one cadence")
    parts = [run[: (run.size // n) * n] for run in segments(time, keep, gap_split, cadence_days)]
    joined = np.concatenate(parts) if parts else np.zeros(0, dtype=int)
    return joined.reshape(-1, n)


def estimate(
    time: np.ndarray,
    resid: np.ndarray,
    sector: np.ndarray,
    keep: np.ndarray,
    n: int,
    gap_split: float,
    cadence_days: float,
    b_min: int,
) -> NoiseEstimate:
    """``rednoise.estimate``."""
    time = np.asarray(time, dtype=float)
    resid = np.asarray(resid, dtype=float)
    sector = np.asarray(sector)
    keep = np.asarray(keep, dtype=bool) & np.isfinite(resid)
    out: dict[int, SectorNoise] = {}
    for s in np.unique(sector):
        idx = np.flatnonzero(sector == s)
        sel_keep, sel_resid = keep[idx], resid[idx]
        groups = bin_matrix(time[idx], sel_keep, n, gap_split, cadence_days)
        sigma_w = robust_sigma(sel_resid[sel_keep]) if np.any(sel_keep) else float("nan")
        n_bins = groups.shape[0]
        if n_bins < b_min or not np.isfinite(sigma_w) or sigma_w <= 0:
            reason = "few_bins" if n_bins < b_min else "no_noise_scale"
            out[int(s)] = SectorNoise(
                int(s), n, n_bins, sigma_w, float("nan"), float("nan"), float("nan"), True, reason
            )
            continue
        sigma_n = robust_sigma(sel_resid[groups].mean(axis=1))
        sigma_r2 = max(0.0, sigma_n**2 - sigma_w**2 / n)
        beta = float(np.sqrt(1.0 + n * sigma_r2 / sigma_w**2))
        out[int(s)] = SectorNoise(int(s), n, n_bins, sigma_w, sigma_n, sigma_r2, beta, False)
    return NoiseEstimate(n, out)


def event_noise(flat, mask, period: float, t0: float, duration: float, plan) -> EventNoise:
    """``rednoise.event_noise``, through ``estimate`` above."""
    from refute.packs.tess.events import transit_mask

    c = plan.gauntlet.corrections
    ev = plan.gauntlet.events
    cadence = plan.data.exptime_seconds / 86400.0
    if mask is None:
        half = plan.detrend.transit_mask_half_width_durations * duration
        mask = transit_mask(flat.time, period, t0, half)
    keep = ~np.asarray(mask, dtype=bool)
    resid = flat.flux - 1.0
    inner = duration / 2.0 + ev.baseline_gap_durations * duration
    outer = duration / 2.0 + ev.baseline_outer_durations * duration
    n_t = max(1, int(round(duration / cadence)))
    n_b = max(1, int(round(2.0 * (outer - inner) / cadence)))
    box = estimate(flat.time, resid, flat.sector, keep, n_t, c.gap_split, cadence, c.b_min)
    base = estimate(flat.time, resid, flat.sector, keep, n_b, c.gap_split, cadence, c.b_min)
    return EventNoise(box, base)
