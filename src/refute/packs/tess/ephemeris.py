"""Individual transit times and a weighted linear ephemeris.

Each transit time comes from a deterministic chi-square scan of a box model
(fixed depth and duration) over shifts of +-``scan_half_width_durations`` times
the duration, in steps of ``step_minutes``. The 1-sigma error is half the width
of the region where chi-square is within 1 of its minimum, floored at half a
cadence. Transits whose best shift lies on the edge of the scan are discarded.

The linear ephemeris ``t(n) = t_ref + (n - n_ref) * P`` is a weighted least-squares
fit with the reference epoch at the weighted mean epoch. Errors are inflated by
``sqrt(reduced chi-square)`` when it exceeds 1.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from refute.packs.tess.events import event_epochs
from refute.packs.tess.types import LightCurveData


@dataclass(frozen=True)
class TransitTime:
    epoch: int
    time: float
    error: float


def measure_transit_times(
    lc: LightCurveData,
    period: float,
    t0: float,
    duration: float,
    depth: float,
    sigma: np.ndarray,
    *,
    cadence_days: float,
    step_minutes: float = 1.0,
    scan_half_width_durations: float = 0.5,
    min_coverage: float = 0.5,
) -> list[TransitTime]:
    half = duration / 2.0
    scan = scan_half_width_durations * duration
    step = step_minutes / 1440.0
    shifts = np.arange(-scan, scan + step / 2.0, step)
    window = half + scan + duration
    expected = 2.0 * duration / cadence_days
    times: list[TransitTime] = []
    if depth <= 0:
        return times
    for epoch in event_epochs(lc.time, period, t0):
        center = t0 + epoch * period
        lo = np.searchsorted(lc.time, center - window, side="left")
        hi = np.searchsorted(lc.time, center + window, side="right")
        if hi - lo < 3:
            continue
        t = lc.time[lo:hi]
        resid = lc.flux[lo:hi] - 1.0
        weight = 1.0 / np.square(sigma[lo:hi])
        if np.count_nonzero(np.abs(t - center) <= duration) < min_coverage * expected:
            continue
        inside = np.abs(t[None, :] - (center + shifts[:, None])) <= half
        # chi2(shift) - chi2(no transit) = sum over in-box points of w*(2*depth*resid + depth^2)
        delta = np.where(inside, weight * (2.0 * depth * resid + depth * depth), 0.0).sum(axis=1)
        best = int(np.argmin(delta))
        if best == 0 or best == shifts.size - 1:
            continue
        within = set(np.nonzero(delta <= delta[best] + 1.0)[0].tolist())
        # contiguous region around the minimum
        left = best
        while left - 1 in within:
            left -= 1
        right = best
        while right + 1 in within:
            right += 1
        error = max(0.5 * (shifts[right] - shifts[left]), step, 0.5 * cadence_days)
        times.append(TransitTime(int(epoch), float(center + shifts[best]), float(error)))
    return times


@dataclass(frozen=True)
class Ephemeris:
    t_ref: float
    n_ref: int
    period: float
    cov: tuple[tuple[float, float], tuple[float, float]]
    chi2_reduced: float
    n_transits: int

    @property
    def t_ref_err(self) -> float:
        return float(np.sqrt(self.cov[0][0]))

    @property
    def period_err(self) -> float:
        return float(np.sqrt(self.cov[1][1]))

    def predict(self, epoch: int) -> tuple[float, float]:
        """Predicted mid-time and its 1-sigma error for an epoch (original numbering)."""
        m = epoch - self.n_ref
        variance = self.cov[0][0] + 2 * m * self.cov[0][1] + m * m * self.cov[1][1]
        return self.t_ref + m * self.period, float(np.sqrt(max(variance, 0.0)))

    def to_dict(self) -> dict:
        return {
            "t_ref": self.t_ref,
            "n_ref": self.n_ref,
            "period": self.period,
            "t_ref_err": self.t_ref_err,
            "period_err": self.period_err,
            "chi2_reduced": self.chi2_reduced,
            "n_transits": self.n_transits,
        }


def fit_linear_ephemeris(times: list[TransitTime]) -> Ephemeris:
    if len(times) < 2:
        raise ValueError("at least two transit times are needed")
    epochs = np.array([t.epoch for t in times], dtype=float)
    values = np.array([t.time for t in times], dtype=float)
    weights = 1.0 / np.square([t.error for t in times])
    n_ref = int(np.round(np.sum(weights * epochs) / np.sum(weights)))
    x = epochs - n_ref
    design = np.column_stack([np.ones_like(x), x])
    normal = design.T @ (design * weights[:, None])
    cov = np.linalg.inv(normal)
    coef = cov @ (design.T @ (weights * values))
    resid = values - design @ coef
    dof = len(times) - 2
    chi2_red = float(np.sum(weights * resid**2) / dof) if dof > 0 else 1.0
    cov = cov * max(1.0, chi2_red)
    return Ephemeris(
        t_ref=float(coef[0]),
        n_ref=n_ref,
        period=float(coef[1]),
        cov=((float(cov[0, 0]), float(cov[0, 1])), (float(cov[1, 0]), float(cov[1, 1]))),
        chi2_reduced=chi2_red,
        n_transits=len(times),
    )
