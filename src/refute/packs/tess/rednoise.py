"""Correlated noise estimated from the data by the binned rms (M4 of v0.2.1, correction A1).

Revision 3 of the corrections plan, section 2.1
(docs/validation/v0.2.1/population/corrections-plan/m4-plan-rev3.md), as amended by revision 4
(docs/validation/v0.2.1/reopen/corrections-plan-rev4.md); the map of the code is
docs/validation/v0.2.1/reopen/m4-implementation-map.md (piece 1).

- **Segments:** runs of consecutive kept cadences, split where two consecutive kept cadences are
  more than ``gap_split`` cadences apart (orbit gaps, sector boundaries, dropped cadences) and at
  every masked cadence (masked cadences are removed and split the run).
- **Bins:** each segment is cut into consecutive, non-overlapping bins of ``n`` cadences;
  incomplete bins are dropped. Bins never cross a gap or a mask.
- **Per sector** (Pont, Zucker and Queloz 2006, MNRAS 373, 217-230): ``σ_w`` the robust per-cadence
  standard deviation of the kept residuals; ``σ_n`` the robust standard deviation of the bin means;
  ``σ_r²(n) = max(0, σ_n² − σ_w² / n)``; ``β(n) = sqrt(1 + n σ_r²(n) / σ_w²)``.
- **Few bins:** a sector with fewer than ``b_min`` bins at scale ``n`` is excluded (no borrowing, no
  white-noise fallback) and reported; if no sector remains, the estimate is *undetermined* and every
  decision that needs it is INCONCLUSIVE (the caller decides).

Nothing here knows the generation of the data: it receives residuals, times, sectors and a mask.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

import numpy as np

from refute.packs.tess.detrend import robust_sigma


@dataclass(frozen=True)
class SectorNoise:
    sector: int
    n: int
    n_bins: int
    sigma_w: float
    sigma_n: float
    sigma_r2: float
    beta: float
    excluded: bool
    reason: str | None = None


@dataclass(frozen=True)
class NoiseEstimate:
    n: int
    sectors: dict[int, SectorNoise] = field(default_factory=dict)

    @property
    def excluded_sectors(self) -> list[int]:
        return sorted(s for s, v in self.sectors.items() if v.excluded)

    @property
    def undetermined(self) -> bool:
        return not any(not v.excluded for v in self.sectors.values())

    def to_dict(self) -> dict:
        return {
            "n": self.n,
            "undetermined": self.undetermined,
            "sectors": {
                str(s): {
                    "n_bins": v.n_bins,
                    "sigma_w": v.sigma_w,
                    "sigma_n": v.sigma_n,
                    "sigma_r2": v.sigma_r2,
                    "beta": v.beta,
                    "excluded": v.excluded,
                    "reason": v.reason,
                }
                for s, v in sorted(self.sectors.items())
            },
        }


@dataclass(frozen=True)
class EventNoise:
    """The estimates at the two nominal scales of a per-event measurement (M4 piece 2): ``box``
    at ``n_T`` (the in-event cadences) and ``base`` at ``n_B`` (the baseline bands)."""

    box: NoiseEstimate
    base: NoiseEstimate

    def usable(self, sector: int) -> bool:
        a, b = self.box.sectors.get(sector), self.base.sectors.get(sector)
        return a is not None and b is not None and not a.excluded and not b.excluded

    @property
    def undetermined(self) -> bool:
        return not any(self.usable(s) for s in self.box.sectors)

    def to_dict(self) -> dict:
        return {"box": self.box.to_dict(), "base": self.base.to_dict()}


def event_noise(flat, mask, period: float, t0: float, duration: float, plan) -> EventNoise:
    """A1 on a flattened light curve for the per-event measurements of a candidate: the
    candidate's transits masked (``mask``, or the detrending mask of the plan when None), the
    estimate at ``n_T = round(duration / cadence)`` and ``n_B = round(2 (outer - inner) /
    cadence)`` (m4-implementation-map.md, Amendment 2)."""
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


def bls_beta(
    betas: Mapping[int, float], w_in: Mapping[int, float], w_out: Mapping[int, float]
) -> float:
    """β of the BLS depth error (m4-implementation-map.md, Amendment 7): with the BLS variance
    ``1/W_I + 1/W_O`` and each sector's in-transit and out-of-transit means inflated by
    ``β_s²``, ``β_D² = Σ_s β_s² (W_I,s / W_I² + W_O,s / W_O²) / (1/W_I + 1/W_O)``. The sectors
    are those of ``w_in`` and ``w_out``; every one needs a β."""
    sectors = sorted(set(w_in) | set(w_out))
    total_in = float(sum(w_in.get(s, 0.0) for s in sectors))
    total_out = float(sum(w_out.get(s, 0.0) for s in sectors))
    if not (total_in > 0 and total_out > 0):
        raise ValueError("both the in-transit and the out-of-transit weights must be positive")
    num = sum(
        betas[s] ** 2 * (w_in.get(s, 0.0) / total_in**2 + w_out.get(s, 0.0) / total_out**2)
        for s in sectors
    )
    return float(np.sqrt(num / (1.0 / total_in + 1.0 / total_out)))


def segments(
    time: np.ndarray, keep: np.ndarray, gap_split: float, cadence_days: float
) -> list[np.ndarray]:
    """Index arrays of the runs of consecutive kept cadences (see the module docstring)."""
    time = np.asarray(time, dtype=float)
    keep = np.asarray(keep, dtype=bool)
    runs: list[np.ndarray] = []
    current: list[int] = []
    limit = gap_split * cadence_days
    for i in range(time.size):
        if not keep[i]:
            if current:
                runs.append(np.asarray(current))
                current = []
            continue
        if current and (i != current[-1] + 1 or time[i] - time[current[-1]] > limit):
            runs.append(np.asarray(current))
            current = []
        current.append(i)
    if current:
        runs.append(np.asarray(current))
    return runs


def bins(
    time: np.ndarray, keep: np.ndarray, n: int, gap_split: float, cadence_days: float
) -> list[np.ndarray]:
    """Index arrays of the complete bins of ``n`` cadences inside the segments."""
    if n < 1:
        raise ValueError("the bin size must be at least one cadence")
    out = []
    for run in segments(time, keep, gap_split, cadence_days):
        for start in range(0, run.size - n + 1, n):
            out.append(run[start : start + n])
    return out


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
    """The binned-rms estimate at scale ``n``, per sector, with the few-bins rule."""
    time = np.asarray(time, dtype=float)
    resid = np.asarray(resid, dtype=float)
    sector = np.asarray(sector)
    keep = np.asarray(keep, dtype=bool) & np.isfinite(resid)
    out: dict[int, SectorNoise] = {}
    for s in np.unique(sector):
        in_sector = sector == s
        idx = np.flatnonzero(in_sector)
        sel_keep = keep[idx]
        groups = bins(time[idx], sel_keep, n, gap_split, cadence_days)
        sigma_w = robust_sigma(resid[idx][sel_keep]) if np.any(sel_keep) else float("nan")
        n_bins = len(groups)
        if n_bins < b_min or not np.isfinite(sigma_w) or sigma_w <= 0:
            reason = "few_bins" if n_bins < b_min else "no_noise_scale"
            out[int(s)] = SectorNoise(
                int(s), n, n_bins, sigma_w, float("nan"), float("nan"), float("nan"), True, reason
            )
            continue
        means = np.array([resid[idx][g].mean() for g in groups])
        sigma_n = robust_sigma(means)
        sigma_r2 = max(0.0, sigma_n**2 - sigma_w**2 / n)
        beta = float(np.sqrt(1.0 + n * sigma_r2 / sigma_w**2))
        out[int(s)] = SectorNoise(int(s), n, n_bins, sigma_w, sigma_n, sigma_r2, beta, False)
    return NoiseEstimate(n, out)
