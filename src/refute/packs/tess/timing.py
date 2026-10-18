"""Transit times with an ingress model (M4 of v0.2.1, piece 3).

Revision 3 of the corrections plan, section 3
(docs/validation/v0.2.1/population/corrections-plan/m4-plan-rev3.md); the map of the code and the
readings declared before the tests are in docs/validation/v0.2.1/reopen/m4-implementation-map.md
(piece 3 and Amendment 3). Used only when ``gauntlet.corrections.enabled`` is set; with the switch
off the box scan of ``ephemeris.py`` is unchanged.

- **Template:** a trapezoid (depth, T14, τ) fitted once to the folded light curve at the candidate's
  ephemeris: the depth by weighted least squares for each shape, T14 in [0.5, 1.5] of the
  candidate's duration and τ in [one cadence, T14 / 2] by a grid and then a finer grid around the
  best cell, on the same folded cadences for every cell (within 1.5 times the largest T14 of the
  grid), weights 1/σ². A best fit with depth ≤ 0 gives no template.
- **Scan:** each transit's center is the minimum of a chi-square scan of the fixed template over
  ±``scan_half_width_durations`` T14 in steps of ``step_minutes``; a minimum on the edge of the scan
  is discarded; the coverage rule of ``ephemeris.py``.
- **Error:** half the width of the region where chi-square is within 1 of its minimum, with the two
  crossings located on the parabola of a declared triple of scan points (``crossings``; Amendment 7
  of the map, which replaced the linear interpolation of Amendment 3 after its result), with a
  counted linear fallback, times β(n_τ) of the transit's sector
  (``rednoise.py``, n_τ = max(1, round(τ / cadence))), floored at half a cadence. A transit whose
  sector is excluded at n_τ is dropped and counted; with the estimate undetermined there are no
  transit times.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from refute.packs.tess.ephemeris import TransitTime
from refute.packs.tess.events import event_epochs, phase_offset_days, transit_mask
from refute.packs.tess.rednoise import NoiseEstimate, estimate
from refute.packs.tess.types import LightCurveData

T14_RANGE = (0.5, 1.5)
FIT_WINDOW = 1.5
COARSE = (41, 25)
FINE = 21


def _shape(dt: np.ndarray, t14: float, tau: float) -> np.ndarray:
    return np.clip((0.5 * t14 - np.abs(dt)) / tau, 0.0, 1.0)


@dataclass(frozen=True)
class TimingTemplate:
    depth: float
    t14: float
    tau: float

    def deficit(self, dt: np.ndarray) -> np.ndarray:
        """Fractional flux deficit at the times ``dt`` from the center."""
        return self.depth * _shape(dt, self.t14, self.tau)

    def to_dict(self) -> dict:
        return {"depth": self.depth, "t14": self.t14, "tau": self.tau}


@dataclass(frozen=True)
class TemplateTimes:
    times: list[TransitTime]
    dropped: dict[str, int] = field(default_factory=dict)
    template: TimingTemplate | None = None
    noise: NoiseEstimate | None = None
    linear_crossings: int = 0  # crossings that fell back to the linear interpolation

    def to_dict(self) -> dict:
        return {
            "n_times": len(self.times),
            "dropped": dict(self.dropped),
            "linear_crossings": self.linear_crossings,
            "template": None if self.template is None else self.template.to_dict(),
            "noise": None if self.noise is None else self.noise.to_dict(),
        }


def fit_timing_template(
    lc: LightCurveData,
    period: float,
    t0: float,
    duration: float,
    sigma: np.ndarray,
    cadence_days: float,
) -> TimingTemplate | None:
    """The trapezoid template of the folded light curve (see the module docstring)."""
    t14_lo, t14_hi = T14_RANGE[0] * duration, T14_RANGE[1] * duration
    dt = phase_offset_days(np.asarray(lc.time, dtype=float), period, t0)
    sel = (np.abs(dt) <= FIT_WINDOW * t14_hi) & np.isfinite(lc.flux) & (sigma > 0)
    if np.count_nonzero(sel) < 3:
        return None
    x = dt[sel]
    y = 1.0 - lc.flux[sel]
    w = 1.0 / np.square(sigma[sel])

    def tau_of(t14: float, u: float) -> float:
        return cadence_days + u * max(0.0, 0.5 * t14 - cadence_days)

    def solve(t14: float, u: float) -> tuple[float, float]:
        s = _shape(x, t14, tau_of(t14, u))
        ss = float(np.sum(w * s * s))
        if ss <= 0:
            return float("inf"), 0.0
        depth = float(np.sum(w * y * s) / ss)
        return float(np.sum(w * np.square(y - depth * s))), depth

    def search(t14s: np.ndarray, us: np.ndarray) -> tuple[float, int, int, float]:
        best = (float("inf"), 0, 0, 0.0)
        for i, t14 in enumerate(t14s):
            for j, u in enumerate(us):
                chi2, depth = solve(float(t14), float(u))
                if chi2 < best[0]:
                    best = (chi2, i, j, depth)
        return best

    t14s = np.linspace(t14_lo, t14_hi, COARSE[0])
    us = np.linspace(0.0, 1.0, COARSE[1])
    _, i, j, _ = search(t14s, us)
    fine_t14 = np.linspace(t14s[max(i - 1, 0)], t14s[min(i + 1, t14s.size - 1)], FINE)
    fine_u = np.linspace(us[max(j - 1, 0)], us[min(j + 1, us.size - 1)], FINE)
    chi2, i, j, depth = search(fine_t14, fine_u)
    if not np.isfinite(chi2) or not depth > 0:
        return None
    t14 = float(fine_t14[i])
    return TimingTemplate(depth, t14, tau_of(t14, float(fine_u[j])))


def measure_template_times(
    lc: LightCurveData,
    period: float,
    t0: float,
    template: TimingTemplate,
    sigma: np.ndarray,
    noise: NoiseEstimate,
    *,
    cadence_days: float,
    step_minutes: float = 1.0,
    scan_half_width_durations: float = 0.5,
    min_coverage: float = 0.5,
) -> TemplateTimes:
    """The transit times of the scan of a fixed template (see the module docstring)."""
    dropped: dict[str, int] = {}
    if not template.depth > 0 or noise.undetermined:
        return TemplateTimes([], dropped, template, noise)
    t14 = template.t14
    half = 0.5 * t14
    scan = scan_half_width_durations * t14
    step = step_minutes / 1440.0
    shifts = np.arange(-scan, scan + step / 2.0, step)
    window = half + scan + t14
    expected = 2.0 * t14 / cadence_days
    times: list[TransitTime] = []
    linear = 0
    for epoch in event_epochs(lc.time, period, t0):
        center = t0 + epoch * period
        lo = np.searchsorted(lc.time, center - window, side="left")
        hi = np.searchsorted(lc.time, center + window, side="right")
        if hi - lo < 3:
            continue
        t = lc.time[lo:hi]
        if np.count_nonzero(np.abs(t - center) <= t14) < min_coverage * expected:
            continue
        sector = int(lc.sector[lo + int(np.argmin(np.abs(t - center)))])
        sector_noise = noise.sectors.get(sector)
        if sector_noise is None or sector_noise.excluded:
            dropped["excluded_sector"] = dropped.get("excluded_sector", 0) + 1
            continue
        resid = lc.flux[lo:hi] - 1.0
        weight = 1.0 / np.square(sigma[lo:hi])
        model = template.deficit(t[None, :] - (center + shifts[:, None]))
        # chi2(shift) - chi2(no transit) = sum of w * (2 * model * resid + model^2)
        delta = (weight * (2.0 * model * resid + model * model)).sum(axis=1)
        best = int(np.argmin(delta))
        if best == 0 or best == shifts.size - 1:
            dropped["edge_minimum"] = dropped.get("edge_minimum", 0) + 1
            continue
        x_left, x_right, n_linear = crossings(delta, shifts, best)
        linear += n_linear
        error = max(0.5 * (x_right - x_left) * sector_noise.beta, 0.5 * cadence_days)
        times.append(TransitTime(int(epoch), float(center + shifts[best]), float(error)))
    return TemplateTimes(times, dropped, template, noise, linear)


QUADRATIC_MIN = 1e-12  # |a| below this (delta-chi2 per step squared): a degenerate parabola
ROOT_TOLERANCE = 1e-9  # in scan steps


def _parabolic_root(y: np.ndarray, level: float, lo: float, hi: float) -> float | None:
    """The root of ``a u² + b u + c = level`` through ``(-1, y0), (0, y1), (1, y2)`` in
    ``[lo, hi]`` (scan steps from the middle point), or None if degenerate, absent or not
    unique."""
    a = 0.5 * (y[0] - 2.0 * y[1] + y[2])
    b = 0.5 * (y[2] - y[0])
    c = y[1] - level
    if not (abs(a) >= QUADRATIC_MIN and np.isfinite(a) and np.isfinite(b) and np.isfinite(c)):
        return None
    disc = b * b - 4.0 * a * c
    if not (np.isfinite(disc) and disc >= 0.0):
        return None
    root = np.sqrt(disc)
    found = [
        u
        for u in ((-b - root) / (2.0 * a), (-b + root) / (2.0 * a))
        if np.isfinite(u) and lo - ROOT_TOLERANCE <= u <= hi + ROOT_TOLERANCE
    ]
    if len(found) != 1 and not (len(found) == 2 and found[0] == found[1]):
        return None
    return float(min(max(found[0], lo), hi))


def crossings(delta: np.ndarray, shifts: np.ndarray, best: int) -> tuple[float, float, int]:
    """The two crossings of ``delta[best] + 1`` around the scan minimum ``best`` (Amendment 7 of
    the map): each on the parabola of its declared triple, ``(left - 1, left, left + 1)`` in
    ``[x[left - 1], x[left]]`` and ``(right - 1, right, right + 1)`` in
    ``[x[right], x[right + 1]]``; the linear interpolation when the parabola gives no single root
    (counted); the edge of the scan when the region reaches it. Returns
    ``(x_left, x_right, linear_count)``."""
    step = float(shifts[1] - shifts[0])
    level = delta[best] + 1.0
    left = best
    while left - 1 >= 0 and delta[left - 1] <= level:
        left -= 1
    right = best
    while right + 1 < shifts.size and delta[right + 1] <= level:
        right += 1
    linear = 0
    x_left = float(shifts[left])
    if left > 0:
        u = _parabolic_root(delta[left - 1 : left + 2], level, -1.0, 0.0)
        if u is None:
            linear += 1
            u = -(level - delta[left]) / (delta[left - 1] - delta[left])
        x_left = float(shifts[left] + u * step)
    x_right = float(shifts[right])
    if right < shifts.size - 1:
        u = _parabolic_root(delta[right - 1 : right + 2], level, 0.0, 1.0)
        if u is None:
            linear += 1
            u = (level - delta[right]) / (delta[right + 1] - delta[right])
        x_right = float(shifts[right] + u * step)
    return x_left, x_right, linear


def corrected_transit_times(
    flat: LightCurveData,
    period: float,
    t0: float,
    duration: float,
    sigma: np.ndarray,
    plan,
) -> TemplateTimes:
    """Piece 3 on a flattened light curve: the template, A1 at n_τ with the candidate's transits
    masked (the detrending mask of the plan), and the scan."""
    cadence = plan.data.exptime_seconds / 86400.0
    template = fit_timing_template(flat, period, t0, duration, sigma, cadence)
    if template is None:
        return TemplateTimes([], {}, None, None)
    c = plan.gauntlet.corrections
    params = plan.gauntlet.holdout_by_year
    n_tau = max(1, int(round(template.tau / cadence)))
    half = plan.detrend.transit_mask_half_width_durations * duration
    keep = ~transit_mask(flat.time, period, t0, half)
    noise = estimate(
        flat.time, flat.flux - 1.0, flat.sector, keep, n_tau, c.gap_split, cadence, c.b_min
    )
    return measure_template_times(
        flat,
        period,
        t0,
        template,
        sigma,
        noise,
        cadence_days=cadence,
        step_minutes=params.timing_step_minutes,
        scan_half_width_durations=params.timing_scan_half_width_durations,
    )
