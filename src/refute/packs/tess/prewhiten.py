"""The prewhitening of M4 (v0.2.1, correction B5): revision 3 of the corrections plan, section 7,
with revision 4, section 4 (docs/validation/v0.2.1/reopen/m4-implementation-map.md, Amendment 22).

Two functions. :func:`prewhiten` finds the periodic components of a detrended curve, one at a
time: the generalized Lomb-Scargle periodogram with the A1 weights, the robust asymmetric fit of a
fundamental and one harmonic (cadences below the model are clipped, so dips are protected), the
Baluev false-alarm probability on the kept cadences at the chosen frequency, and the few-harmonic
test on 50 phase bins. :func:`refit` refits given components with a mask (the candidate's
transits). Neither receives a class or a truth; ``prewhiten`` receives no candidate at all.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from refute.packs.tess.params import TessTestPlan
from refute.packs.tess.types import LightCurveData

PHASE_BINS = 50
MIN_BIN_CADENCES = 3
MIN_BINS = 40
MAX_ROBUST_FITS = 10
SAMPLES_PER_PEAK = 10
F_HI = 12.0  # 1 / (2 h), per day


@dataclass(frozen=True)
class Component:
    frequency: float
    fap: float
    h: float
    p1: float
    amplitude: float  # the median over sectors of sqrt(a1^2 + b1^2) of the fundamental
    clipped: int
    coefficients: dict[int, list[float]]
    # the returned model of the robust fit on the used cadences, and the clip set (indices into
    # the curve given); not in the record
    fitted: np.ndarray | None = field(default=None, compare=False, repr=False)
    clip_indices: np.ndarray | None = field(default=None, compare=False, repr=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "frequency": self.frequency,
            "fap": self.fap,
            "h": self.h,
            "p1": self.p1,
            "amplitude": self.amplitude,
            "clipped": self.clipped,
            "coefficients": {str(s): c for s, c in sorted(self.coefficients.items())},
        }


@dataclass
class Prewhitening:
    components: list[Component]
    reason: str
    sectors_used: list[int]
    sectors_left_out: list[int]
    model: np.ndarray  # S on every cadence of the curve given (0 on the sectors left out)
    rejected: dict[str, Any] | None = None  # the statistics of the frequency that stopped it
    used_index: np.ndarray | None = None
    dy: np.ndarray | None = None  # sigma_w on the used cadences
    grid: np.ndarray | None = None
    f_lo: float | None = None
    # Amendment 23: the joint raw refit for the search (its failure, the sectors it left out)
    search_refit_reason: str | None = None
    search_left_out: list[int] = field(default_factory=list)

    @property
    def fundamentals(self) -> list[float]:
        """The accepted frequencies in decreasing amplitude (the order of revision 3, 4.1)."""
        return [c.frequency for c in sorted(self.components, key=lambda c: -c.amplitude)]

    def to_dict(self) -> dict[str, Any]:
        return {
            "components": [c.to_dict() for c in self.components],
            "fundamentals": self.fundamentals,
            "reason": self.reason,
            "sectors_used": self.sectors_used,
            "sectors_left_out": self.sectors_left_out,
            "rejected": self.rejected,
            "f_lo": self.f_lo,
        }


@dataclass
class Refit:
    model: np.ndarray
    reason: str | None
    sectors_left_out: list[int] = field(default_factory=list)


def _noise(curve: LightCurveData, plan: TessTestPlan) -> tuple[np.ndarray, list[int], list[int]]:
    """The per-cadence sigma_w of A1 at n = 1 on every cadence (nan on the sectors left out:
    excluded by the few-bins rule, or sigma_w not finite and positive)."""
    from refute.packs.tess.rednoise import estimate

    c = plan.gauntlet.corrections
    cadence = plan.data.exptime_seconds / 86400.0
    resid = curve.flux - 1.0
    keep = np.ones(resid.size, bool)
    est = estimate(curve.time, resid, curve.sector, keep, 1, c.gap_split, cadence, c.b_min)
    sigma = np.full(resid.size, np.nan)
    used, out = [], []
    for s in sorted(int(x) for x in np.unique(curve.sector)):
        v = est.sectors.get(s)
        ok = v is not None and not v.excluded and math.isfinite(v.sigma_w) and v.sigma_w > 0
        (used if ok else out).append(s)
        if ok:
            sigma[curve.sector == s] = v.sigma_w
    return sigma, used, out


def _design(
    t: np.ndarray, sector: np.ndarray, sectors: list[int], freqs: list[float]
) -> tuple[np.ndarray, list[int]]:
    """A per-sector constant, then per frequency and sector cos and sin at f and 2f; the indices
    of the sinusoidal columns."""
    cols, sinus = [], []
    for s in sectors:
        cols.append((sector == s).astype(float))
    for f in freqs:
        for s in sectors:
            on = (sector == s).astype(float)
            for k in (1, 2):
                for fn in (np.cos, np.sin):
                    sinus.append(len(cols))
                    cols.append(on * fn(2 * np.pi * k * f * t))
    return np.column_stack(cols), sinus


def few_harmonic_test(
    t: np.ndarray, y: np.ndarray, fitted: np.ndarray, frequency: float
) -> tuple[float, int, str | None]:
    """Revision 3, 7.4(b) with revision 4, 4: 50 phase bins of ``(t f) mod 1``; a bin with fewer
    than 3 cadences is dropped; fewer than 40 bins: ``too_few_phase_bins``; otherwise ``h`` = 1 −
    Σ (m_b − μ_b)² / Σ (m_b − m̄)² (bins unweighted); a zero variance or a non-finite ``h``:
    ``non_finite_statistic``. Returns ``(h, bins kept, reason)``."""
    phase = np.mod(np.asarray(t, float) * frequency, 1.0)
    index = np.minimum((phase * PHASE_BINS).astype(int), PHASE_BINS - 1)
    counts = np.bincount(index, minlength=PHASE_BINS)
    good = counts >= MIN_BIN_CADENCES
    n_bins = int(good.sum())
    if n_bins < MIN_BINS:
        return float("nan"), n_bins, "too_few_phase_bins"
    m_b = np.bincount(index, weights=y, minlength=PHASE_BINS)[good] / counts[good]
    mu_b = np.bincount(index, weights=fitted, minlength=PHASE_BINS)[good] / counts[good]
    total = float(np.sum((m_b - m_b.mean()) ** 2))
    if not total > 0:
        return float("nan"), n_bins, "non_finite_statistic"
    h = 1.0 - float(np.sum((m_b - mu_b) ** 2)) / total
    if not math.isfinite(h):
        return h, n_bins, "non_finite_statistic"
    return h, n_bins, None


def _periodogram(t, y, dy):
    from astropy.timeseries import LombScargle

    return LombScargle(
        t, y, dy, fit_mean=True, center_data=True, nterms=1, normalization="standard"
    )


def prewhiten(curve: LightCurveData, plan: TessTestPlan) -> Prewhitening:
    """The components of a detrended curve, one at a time (Amendment 22); ``S`` on every cadence."""
    from refute.packs.tess.battery import _SingularDesignError, _wls
    from refute.packs.tess.detrend import segment_slices

    c = plan.gauntlet.corrections
    sigma, used, out = _noise(curve, plan)
    model = np.zeros(curve.flux.size)
    result = Prewhitening([], "", used, out, model)
    if not used:
        result.reason = "noise_undetermined"
        return result
    if c.max_components == 0:
        result.reason = "max_components"
        return result
    idx = np.flatnonzero(np.isin(curve.sector, used))
    t, sector, dy = curve.time[idx], curve.sector[idx], sigma[idx]
    result.used_index, result.dy = idx, dy
    w = 1.0 / dy**2
    r = curve.flux[idx] - 1.0
    longest = max(
        float(t[s][-1] - t[s][0]) for s in segment_slices(t, plan.detrend.segment_gap_days)
    )
    f_lo = 2.0 / longest if longest > 0 else math.inf
    result.f_lo = f_lo
    if not f_lo < F_HI:
        result.reason = "no_frequency_grid"
        return result
    sub = np.zeros(t.size)
    grid = None
    while True:
        y = r - sub
        l0 = _periodogram(t, y, dy)
        if grid is None:
            grid = l0.autofrequency(
                samples_per_peak=SAMPLES_PER_PEAK, minimum_frequency=f_lo, maximum_frequency=F_HI
            )
            result.grid = grid
        power = np.asarray(l0.power(grid), dtype=float)
        if not np.any(np.isfinite(power)):
            result.reason = "non_finite_statistic"
            break
        f_star = float(grid[int(np.nanargmax(np.where(np.isfinite(power), power, -np.inf)))])
        design, sinus = _design(t, sector, used, [f_star])
        weights = w
        clip = None
        try:
            for _ in range(MAX_ROBUST_FITS):
                _, coef, _, _ = _wls(design, y, weights)
                fitted = design @ coef
                new = (y - fitted) < -c.k_clip * dy
                if clip is not None and np.array_equal(new, clip):
                    break
                clip = new
                weights = np.where(clip, 0.0, w)
            clip = new  # C_last, against the returned model
        except _SingularDesignError:
            result.reason = "singular_design"
            break
        keep = ~clip
        l1 = _periodogram(t[keep], y[keep], dy[keep])
        p1 = float(l1.power(f_star))
        fap = float(
            l1.false_alarm_probability(
                p1,
                method="baluev",
                minimum_frequency=f_lo,
                maximum_frequency=F_HI,
                samples_per_peak=SAMPLES_PER_PEAK,
            )
        )
        h, n_bins, why = few_harmonic_test(t[keep], y[keep], fitted[keep], f_star)
        stats = {"frequency": f_star, "fap": fap, "p1": p1, "h": h, "bins": n_bins}
        if why is None and not (math.isfinite(p1) and math.isfinite(fap)):
            why = "non_finite_statistic"
        if why is None and not fap < c.fap_max:
            why = "fap_above_max"
        if why is None and not h >= c.h_min:
            why = "few_harmonics_fail"
        if why is not None:
            result.reason, result.rejected = why, stats
            break
        sub = sub + design[:, sinus] @ coef[sinus]
        per_sector: dict[int, list[float]] = {}
        amps = []
        for i, s in enumerate(used):
            block = coef[sinus][4 * i : 4 * i + 4]
            per_sector[s] = [float(x) for x in block]
            amps.append(math.hypot(block[0], block[1]))
        result.components.append(
            Component(
                f_star,
                fap,
                h,
                p1,
                float(np.median(amps)),
                int(clip.sum()),
                per_sector,
                fitted=fitted,
                clip_indices=idx[clip],
            )
        )
        if len(result.components) >= c.max_components:
            result.reason = "max_components"
            break
    model[idx] = sub
    result.model = model
    return result


def refit(curve: LightCurveData, components, mask: np.ndarray, plan: TessTestPlan) -> Refit:
    """``S′`` (Amendment 22): one joint weighted fit of the given components' frequencies on the
    cadences outside ``mask``, no clipping; the sinusoidal terms on every used cadence."""
    from refute.packs.tess.battery import _SingularDesignError, _wls

    model = np.zeros(curve.flux.size)
    freqs = [comp.frequency for comp in components]
    if not freqs:
        return Refit(model, None)
    sigma, used, out = _noise(curve, plan)
    if not used:
        return Refit(model, "noise_undetermined", out)
    idx = np.flatnonzero(np.isin(curve.sector, used))
    design, sinus = _design(curve.time[idx], curve.sector[idx], used, freqs)
    fit_on = ~np.asarray(mask, bool)[idx]
    w = np.where(fit_on, 1.0 / sigma[idx] ** 2, 0.0)
    try:
        _, coef, _, _ = _wls(design, curve.flux[idx] - 1.0, w)
    except _SingularDesignError:
        return Refit(model, "singular_design", out)
    model[idx] = design[:, sinus] @ coef[sinus]
    return Refit(model, None, out)
