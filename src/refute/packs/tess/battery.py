"""Gauntlet v0.2 battery: pixel-level and systematics tests for a transit candidate.

Every function here is deterministic and returns a
:class:`~refute.core.verdict.TestResult` with the thresholds it used. All
thresholds are defaults of the claim schema, chosen on synthetic data only and
documented in ``docs/gauntlet-tess-v0.2.md``. None of these functions is ever
given to the blind holdout.

Shared measurement: a time series (aperture flux, centroid, SAP flux, background)
is detrended additively with the same robust local quadratic as the light curve,
with the candidate's transits masked, and each transit's "depth" is the mean of
its local baseline band minus the mean inside the transit (``events``). Group
errors are the larger of the white-noise error and the event-to-event scatter.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import NormalDist
from typing import Any

import numpy as np

from refute.core.verdict import Severity, TestResult, TestStatus
from refute.packs.tess.detrend import _segment_trend, detrend, segment_slices
from refute.packs.tess.events import (
    GroupMean,
    group_mean,
    per_event_depths,
    per_point_sigma,
    phase_offset_days,
    transit_mask,
)
from refute.packs.tess.params import (
    AliasParams,
    ApertureParams,
    CentroidParams,
    ContaminationParams,
    SystematicsParams,
    TessTestPlan,
)
from refute.packs.tess.types import (
    Candidate,
    LightCurveData,
    Neighbor,
    PixelData,
    SectorAux,
    StarInfo,
)

MAX_SIGMA_REPORTED = 37.0


# --- shared measurement ----------------------------------------------------------------


def additive_residuals(
    time: np.ndarray, values: np.ndarray, sector: np.ndarray, mask: np.ndarray, plan: TessTestPlan
) -> np.ndarray:
    """``values`` minus a robust local quadratic trend fitted to the unmasked points."""
    residual = np.full(time.size, np.nan)
    for sec in np.unique(sector):
        idx = np.nonzero(sector == sec)[0]
        t, v, m = time[idx], values[idx], mask[idx]
        res = np.empty(t.size)
        for seg in segment_slices(t, plan.detrend.segment_gap_days):
            res[seg] = v[seg] - _segment_trend(t[seg], v[seg], ~m[seg], plan.detrend)
        residual[idx] = res
    return residual


def event_shift(
    time: np.ndarray,
    values: np.ndarray,
    sector: np.ndarray,
    candidate: Candidate,
    plan: TessTestPlan,
) -> GroupMean | None:
    """Mean over transits of (baseline - in-transit) of a detrended series."""
    good = np.isfinite(time) & np.isfinite(values)
    time, values, sector = time[good], values[good], sector[good]
    if time.size < 10:
        return None
    order = np.argsort(time, kind="stable")
    time, values, sector = time[order], values[order], sector[order]
    half = plan.detrend.transit_mask_half_width_durations * candidate.duration
    mask = transit_mask(time, candidate.period, candidate.t0, half)
    resid = additive_residuals(time, values, sector, mask, plan)
    ok = np.isfinite(resid)
    series = LightCurveData(
        time[ok], 1.0 + resid[ok], np.ones(int(ok.sum())), sector[ok], np.zeros(int(ok.sum()))
    )
    sigma = per_point_sigma(series, mask[ok])
    cadence = plan.data.exptime_seconds / 86400.0
    events = per_event_depths(
        series,
        candidate.period,
        candidate.t0,
        candidate.duration,
        cadence,
        plan.gauntlet.events,
        0.0,
        sigma,
    )
    if len(events) == 0:
        return None
    return group_mean(events.depths, events.errors)


def gaussian_sigma_from_chi2(chi2: float, dof: int) -> float:
    """One-sided Gaussian-equivalent significance of a chi-square value with even dof."""
    if dof <= 0 or dof % 2:
        raise ValueError("dof must be a positive even number")
    half = chi2 / 2.0
    term, total = 1.0, 1.0
    for i in range(1, dof // 2):
        term *= half / i
        total += term
    log_p = -half + math.log(total)
    if log_p < math.log(1e-300):
        return MAX_SIGMA_REPORTED
    p = min(1.0, math.exp(log_p))
    if p >= 0.5:
        return 0.0
    # inv_cdf(p) instead of inv_cdf(1 - p): 1 - p rounds to 1.0 for tiny p.
    return min(MAX_SIGMA_REPORTED, -NormalDist().inv_cdf(p))


# --- pixels ----------------------------------------------------------------------------


def aperture_series(px: PixelData, mask2d: np.ndarray) -> tuple[np.ndarray, ...]:
    """Summed flux and flux-weighted centroid (array coordinates) in ``mask2d``."""
    ys, xs = np.nonzero(mask2d)
    cube = px.flux[:, ys, xs]
    finite = np.isfinite(cube)
    values = np.where(finite, cube, 0.0)
    flux = values.sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        cx = (values * xs).sum(axis=1) / flux
        cy = (values * ys).sum(axis=1) / flux
    good = finite.all(axis=1) & (flux > 0) & np.isfinite(px.time)
    return px.time[good], flux[good], cx[good], cy[good]


def _dilate(mask: np.ndarray, pixels: int) -> np.ndarray:
    out = mask.copy()
    for _ in range(pixels):
        grown = out.copy()
        grown[1:, :] |= out[:-1, :]
        grown[:-1, :] |= out[1:, :]
        grown[:, 1:] |= out[:, :-1]
        grown[:, :-1] |= out[:, 1:]
        grown[1:, 1:] |= out[:-1, :-1]
        grown[:-1, :-1] |= out[1:, 1:]
        grown[1:, :-1] |= out[:-1, 1:]
        grown[:-1, 1:] |= out[1:, :-1]
        out = grown
    return out


def core_aperture(px: PixelData, radius: float) -> np.ndarray:
    """Pixels of the SPOC aperture within ``radius`` pixels of the target.

    Without a target position, or if no aperture pixel is that close, the single
    aperture pixel closest to the target (or the brightest one) is used.
    """
    ny, nx = px.aperture.shape
    yy, xx = np.mgrid[0:ny, 0:nx]
    if px.target_xy is not None:
        tx, ty = px.target_xy
        dist = np.hypot(xx - tx, yy - ty)
        core = px.aperture & (dist <= radius)
        if core.any():
            return core
        choice = np.where(px.aperture, dist, np.inf)
    else:
        choice = np.where(px.aperture, -np.nanmedian(px.flux, axis=0), np.inf)
    core = np.zeros_like(px.aperture)
    core[np.unravel_index(int(np.argmin(choice)), choice.shape)] = True
    return core


@dataclass
class _SectorOffset:
    sector: int
    depth: float
    offset_x: float
    offset_y: float
    sigma_x: float
    sigma_y: float
    n_cadences: int = 0

    @property
    def distance(self) -> float:
        return math.hypot(self.offset_x, self.offset_y)

    @property
    def chi2(self) -> float:
        return (self.offset_x / self.sigma_x) ** 2 + (self.offset_y / self.sigma_y) ** 2

    @property
    def distance_sigma(self) -> float:
        d = self.distance
        if d == 0:
            return math.hypot(self.sigma_x, self.sigma_y)
        return math.hypot(self.offset_x * self.sigma_x, self.offset_y * self.sigma_y) / d


def source_offset(px: PixelData, candidate: Candidate, plan: TessTestPlan) -> _SectorOffset | str:
    """Position of the transit source relative to the target, from centroid shifts.

    With aperture flux F, out-of-transit centroid c_out and fractional depth d, a
    source at position s that dims by d*F moves the flux-weighted centroid by
    dc = d (c_out - s) / (1 - d). Hence s = c_out - dc (1 - d) / d, independent of
    how much light other stars put into the aperture.
    """
    if px.target_xy is None:
        return "no target position (WCS) in the target pixel file"
    if not px.aperture.any():
        return "empty SPOC aperture"
    t, f, cx, cy = aperture_series(px, px.aperture)
    if t.size < 100:
        return "too few cadences with complete aperture data"
    sector = np.full(t.size, px.sector)
    g_f = event_shift(t, f / np.median(f), sector, candidate, plan)
    g_x = event_shift(t, cx, sector, candidate, plan)
    g_y = event_shift(t, cy, sector, candidate, plan)
    if g_f is None or g_x is None or g_y is None:
        return "no transit with enough coverage"
    depth = g_f.mean
    detect = plan.gauntlet.centroid_shift.max_sigma
    if not (depth > 0) or depth / g_f.error < detect:
        return f"transit not detected in the aperture flux ({depth / g_f.error:.1f} sigma)"
    half = plan.detrend.transit_mask_half_width_durations * candidate.duration
    out = ~transit_mask(t, candidate.period, candidate.t0, half)
    if out.sum() < 100:
        return "too few out-of-transit cadences"
    c_out = (float(np.median(cx[out])), float(np.median(cy[out])))
    factor = (1.0 - depth) / depth
    dx, dy = -g_x.mean, -g_y.mean
    sx = c_out[0] - dx * factor
    sy = c_out[1] - dy * factor
    rel = g_f.error / depth
    sig_x = math.hypot(g_x.error * factor, dx * factor * rel)
    sig_y = math.hypot(g_y.error * factor, dy * factor * rel)
    tx, ty = px.target_xy
    values = (sx - tx, sy - ty, sig_x, sig_y)
    if not all(math.isfinite(v) for v in values) or min(sig_x, sig_y) <= 0:
        return "centroid offset could not be computed"
    return _SectorOffset(px.sector, depth, *values, n_cadences=int(t.size))


def check_centroid_shift(
    pixels: list[PixelData], candidate: Candidate, plan: TessTestPlan
) -> TestResult:
    """Fatal if the transit source is significantly and measurably away from the target."""
    params: CentroidParams = plan.gauntlet.centroid_shift
    thresholds = params.model_dump(mode="json")
    used, skipped = [], {}
    for px in pixels:
        result = source_offset(px, candidate, plan)
        if isinstance(result, str):
            skipped[str(px.sector)] = result
        else:
            used.append(result)
    if len(used) < params.min_sectors:
        return TestResult(
            "centroid_shift",
            TestStatus.INCONCLUSIVE,
            Severity.FATAL,
            "no target pixel data usable for a centroid measurement"
            if not pixels
            else f"only {len(used)} usable sector(s) (< {params.min_sectors})",
            metrics={"skipped_sectors": skipped},
            thresholds=thresholds,
            coverage=0,
            coverage_unit="pixel-file cadences",
        )
    chi2 = float(sum(o.chi2 for o in used))
    sigma = gaussian_sigma_from_chi2(chi2, 2 * len(used))
    weights = np.array([1.0 / o.distance_sigma**2 for o in used])
    distance = float(np.sum(weights * [o.distance for o in used]) / np.sum(weights))
    metrics = {
        "offset_sigma": sigma,
        "offset_chi2": chi2,
        "offset_dof": 2 * len(used),
        "mean_offset_pixels": distance,
        "cadences_dropped_to_match_the_light_curve": {
            str(px.sector): px.n_dropped_cadences for px in pixels
        },
        "sectors": {
            str(o.sector): {
                "depth_aperture": o.depth,
                "offset_x_pixels": o.offset_x,
                "offset_y_pixels": o.offset_y,
                "sigma_x_pixels": o.sigma_x,
                "sigma_y_pixels": o.sigma_y,
                "n_cadences": o.n_cadences,
            }
            for o in used
        },
        "skipped_sectors": skipped,
    }
    coverage = sum(o.n_cadences for o in used)
    if sigma >= params.max_sigma and distance >= params.min_offset_pixels:
        return TestResult(
            "centroid_shift",
            TestStatus.FAIL,
            Severity.FATAL,
            f"transit source {distance:.2f} px from the target ({sigma:.1f} sigma): "
            "the signal comes from another star",
            metrics=metrics,
            thresholds=thresholds,
            coverage=coverage,
            coverage_unit="pixel-file cadences",
        )
    return TestResult(
        "centroid_shift",
        TestStatus.PASS,
        Severity.FATAL,
        f"transit source consistent with the target (offset {distance:.2f} px, "
        f"{sigma:.1f} sigma; {len(used)} sector(s), {coverage} cadences)",
        metrics=metrics,
        thresholds=thresholds,
        coverage=coverage,
        coverage_unit="pixel-file cadences",
    )


def check_aperture_depth(
    pixels: list[PixelData], candidate: Candidate, plan: TessTestPlan
) -> TestResult:
    """Fatal if the transit is significantly deeper in a larger aperture than in the core.

    On the target, a larger aperture adds light from other stars and the depth
    decreases. A signal from a star outside the core gets deeper as the aperture
    grows to include that star. The transit must be detected (at ``max_sigma``) in
    at least one of the two apertures; otherwise "the depth does not grow" would be
    vacuous and the test is INCONCLUSIVE.
    """
    params: ApertureParams = plan.gauntlet.aperture_depth
    thresholds = params.model_dump(mode="json")
    series: dict[str, list[np.ndarray]] = {"core": [], "large": [], "time": [], "sector": []}
    for px in pixels:
        if not px.aperture.any():
            continue
        core = core_aperture(px, params.core_radius_pixels)
        finite = np.isfinite(px.flux).all(axis=0)
        large = _dilate(px.aperture, params.dilation_pixels) & finite
        t_c, f_c, _, _ = aperture_series(px, core)
        t_l, f_l, _, _ = aperture_series(px, large)
        common, i_c, i_l = np.intersect1d(t_c, t_l, return_indices=True)
        if common.size < 100:
            continue
        series["time"].append(common)
        series["core"].append(f_c[i_c] / np.median(f_c[i_c]))
        series["large"].append(f_l[i_l] / np.median(f_l[i_l]))
        series["sector"].append(np.full(common.size, px.sector))
    unit = "pixel-file cadences"
    if not series["time"]:
        return TestResult(
            "aperture_depth",
            TestStatus.INCONCLUSIVE,
            Severity.FATAL,
            "no target pixel data usable for aperture photometry",
            thresholds=thresholds,
            coverage=0,
            coverage_unit=unit,
        )
    time = np.concatenate(series["time"])
    sector = np.concatenate(series["sector"])
    coverage = int(time.size)
    g_core = event_shift(time, np.concatenate(series["core"]), sector, candidate, plan)
    g_large = event_shift(time, np.concatenate(series["large"]), sector, candidate, plan)
    if g_core is None or g_large is None:
        return TestResult(
            "aperture_depth",
            TestStatus.INCONCLUSIVE,
            Severity.FATAL,
            "no transit with enough coverage in the pixel data",
            thresholds=thresholds,
            coverage=0,
            coverage_unit="transits measured in the pixel data",
        )
    core_snr = g_core.mean / g_core.error
    large_snr = g_large.mean / g_large.error
    diff_sigma = (g_large.mean - g_core.mean) / math.hypot(g_large.error, g_core.error)
    ratio = g_large.mean / g_core.mean if g_core.mean > 0 else float("inf")
    metrics = {
        "depth_core_ppm": g_core.mean * 1e6,
        "depth_core_err_ppm": g_core.error * 1e6,
        "depth_large_ppm": g_large.mean * 1e6,
        "depth_large_err_ppm": g_large.error * 1e6,
        "detection_sigma_core": core_snr,
        "detection_sigma_large": large_snr,
        "depth_ratio_large_to_core": ratio,
        "difference_sigma": diff_sigma,
        "n_sectors": len(series["time"]),
    }
    if max(core_snr, large_snr) < params.max_sigma:
        return TestResult(
            "aperture_depth",
            TestStatus.INCONCLUSIVE,
            Severity.FATAL,
            f"the transit is not detected in the pixel photometry (core {core_snr:.1f} sigma, "
            f"large {large_snr:.1f} sigma, both < {params.max_sigma}): the depths cannot be "
            "compared",
            metrics=metrics,
            thresholds=thresholds,
            coverage=coverage,
            coverage_unit=unit,
        )
    if diff_sigma >= params.max_sigma and ratio >= params.min_depth_ratio:
        return TestResult(
            "aperture_depth",
            TestStatus.FAIL,
            Severity.FATAL,
            f"depth grows with the aperture (ratio {ratio:.2f}, {diff_sigma:.1f} sigma): "
            "the signal comes from outside the core aperture",
            metrics=metrics,
            thresholds=thresholds,
            coverage=coverage,
            coverage_unit=unit,
        )
    return TestResult(
        "aperture_depth",
        TestStatus.PASS,
        Severity.FATAL,
        f"depth does not grow with the aperture (ratio {ratio:.2f}, {diff_sigma:.1f} sigma; "
        f"transit detected at {max(core_snr, large_snr):.1f} sigma)",
        metrics=metrics,
        thresholds=thresholds,
        coverage=coverage,
        coverage_unit=unit,
    )


# --- neighbors -------------------------------------------------------------------------


def check_nearby_contamination(
    neighbors: list[Neighbor] | None,
    star: StarInfo | None,
    depth: float,
    crowdsaps: list[float],
    params: ContaminationParams,
    query_radius_arcsec: float | None = None,
) -> TestResult:
    """Warning if an unresolved TIC neighbor could produce the signal, or crowding is high.

    A neighbor ``dm`` magnitudes fainter than the target, with the same fraction
    of its light in the aperture, needs an eclipse of depth ``depth * 10**(0.4 dm)``
    to produce the observed (crowding-corrected) depth. Neighbors closer than
    ``max_separation_arcsec`` cannot be separated by the centroid and aperture
    tests, so if such a neighbor could produce the signal the claim is weakened.

    What is examined is the TIC cone query around the target (coverage: 1 query).
    "No neighbor" is a legitimate answer only because that query was made; without
    it (``neighbors`` is None) the test is INCONCLUSIVE. Without CROWDSAP values the
    crowding part cannot be checked, and the test is INCONCLUSIVE too.
    """
    thresholds = params.model_dump(mode="json")
    unit = "TIC cone queries examined"
    if neighbors is None:
        return TestResult(
            "nearby_contamination",
            TestStatus.INCONCLUSIVE,
            Severity.WARNING,
            "no TIC neighbor query available",
            thresholds=thresholds,
            coverage=0,
            coverage_unit=unit,
        )
    if star is None or star.tmag is None:
        return TestResult(
            "nearby_contamination",
            TestStatus.INCONCLUSIVE,
            Severity.WARNING,
            "no TIC magnitude for the target",
            thresholds=thresholds,
            coverage=0,
            coverage_unit=unit,
        )
    ignored = {d.upper() for d in params.ignored_dispositions}
    viable, considered = [], []
    for n in neighbors:
        if n.separation_arcsec > params.max_separation_arcsec:
            continue
        if n.disposition and n.disposition.upper() in ignored:
            continue
        required = None if n.tmag is None else depth * 10 ** (0.4 * (n.tmag - star.tmag))
        row = {
            "tic_id": n.tic_id,
            "tmag": n.tmag,
            "separation_arcsec": n.separation_arcsec,
            "required_eclipse_depth": required,
        }
        considered.append(row)
        if required is None or required <= params.max_eclipse_depth:
            viable.append(row)
    crowd = float(np.median(crowdsaps)) if crowdsaps else None
    query = (
        f"TIC cone query of {query_radius_arcsec:g} arcsec returned {len(neighbors)} source(s)"
        if query_radius_arcsec is not None
        else f"TIC cone query returned {len(neighbors)} source(s)"
    )
    metrics = {
        "query": query,
        "n_sources_returned": len(neighbors),
        "neighbors_within_radius": considered,
        "viable_neighbors": viable,
        "median_crowdsap": crowd,
        "target_tmag": star.tmag,
        "depth_ppm": depth * 1e6,
    }
    problems = []
    if viable:
        problems.append(
            f"{len(viable)} neighbor(s) within {params.max_separation_arcsec:g} arcsec could "
            "produce the signal"
        )
    if crowd is not None and crowd < params.min_crowdsap:
        problems.append(f"median CROWDSAP {crowd:.2f} < {params.min_crowdsap}")
    if problems:
        return TestResult(
            "nearby_contamination",
            TestStatus.FAIL,
            Severity.WARNING,
            f"{'; '.join(problems)} ({query})",
            metrics=metrics,
            thresholds=thresholds,
            coverage=1,
            coverage_unit=unit,
        )
    if crowd is None:
        return TestResult(
            "nearby_contamination",
            TestStatus.INCONCLUSIVE,
            Severity.WARNING,
            f"crowding not checked: no CROWDSAP value ({query}; none could produce the signal)",
            metrics=metrics,
            thresholds=thresholds,
            coverage=1,
            coverage_unit=unit,
        )
    return TestResult(
        "nearby_contamination",
        TestStatus.PASS,
        Severity.WARNING,
        f"{query}: {len(considered)} within {params.max_separation_arcsec:g} arcsec, none could "
        f"produce the signal; median CROWDSAP {crowd:.2f}",
        metrics=metrics,
        thresholds=thresholds,
        coverage=1,
        coverage_unit=unit,
    )


# --- period alias ----------------------------------------------------------------------


def _bic(design: np.ndarray, y: np.ndarray) -> float:
    coef, *_ = np.linalg.lstsq(design, y, rcond=None)
    rss = float(np.sum((y - design @ coef) ** 2))
    n = y.size
    return n * math.log(rss / n) + design.shape[1] * math.log(n)


def check_period_alias(lc: LightCurveData, candidate: Candidate, plan: TessTestPlan) -> TestResult:
    """Fatal if a sinusoid at the found period explains the dip; warning near the
    period of a known systematic.

    The light curve is detrended with a window of at least ``detrend_window_periods``
    periods (transits masked), so a variation at the found period survives. Two
    models are fitted to all points: a Fourier series with ``sine_harmonics``
    harmonics at the found period, and the same series plus a box at the transit.
    If adding the box does not lower the BIC by at least ``min_box_delta_bic``, the
    dip is just part of a periodic variation (for example stellar variability or an
    ellipsoidal variable) and not a transit. A real transit on a star whose
    variability happens to share the period still needs the box, so it passes.

    The comparison needs in-transit cadences: with fewer than one transit's worth
    (``events.min_coverage`` of the cadences of one transit) the test is
    INCONCLUSIVE, never a refutation.
    """
    params: AliasParams = plan.gauntlet.period_alias
    thresholds = params.model_dump(mode="json")
    unit = "in-transit cadences"
    window = max(plan.detrend.window_days, params.detrend_window_periods * candidate.period)
    detrend_params = plan.detrend.model_copy(update={"window_days": window})
    half = plan.detrend.transit_mask_half_width_durations * candidate.duration
    mask = transit_mask(lc.time, candidate.period, candidate.t0, half)
    flat = detrend(lc, detrend_params, mask=mask)
    y = flat.flux - 1.0
    phase = np.mod(flat.time - candidate.t0, candidate.period) / candidate.period
    box = (
        np.abs(phase_offset_days(flat.time, candidate.period, candidate.t0))
        <= candidate.duration / 2
    ).astype(float)
    n_box = int(box.sum())
    cadence = plan.data.exptime_seconds / 86400.0
    needed = plan.gauntlet.events.min_coverage * candidate.duration / cadence
    near = [
        p
        for p in params.systematic_periods_days
        if abs(candidate.period - p) / p <= params.systematic_tolerance
    ]
    if n_box < needed or y.size - n_box < 10:
        return TestResult(
            "period_alias",
            TestStatus.INCONCLUSIVE,
            Severity.FATAL,
            f"only {n_box} in-transit cadences (< {needed:.0f}, one transit's worth): the box "
            "and the sinusoid cannot be compared",
            metrics={"n_in_transit_cadences": n_box, "near_systematic_periods_days": near},
            thresholds=thresholds,
            coverage=n_box,
            coverage_unit=unit,
        )
    columns = [np.ones(y.size)]
    for k in range(1, params.sine_harmonics + 1):
        columns += [np.cos(2 * np.pi * k * phase), np.sin(2 * np.pi * k * phase)]
    sine = np.column_stack(columns)
    bic_sine = _bic(sine, y)
    bic_joint = _bic(np.column_stack([sine, box]), y)
    bic_box = _bic(np.column_stack([columns[0], box]), y)
    gain = bic_sine - bic_joint
    metrics = {
        "bic_sine": bic_sine,
        "bic_sine_plus_box": bic_joint,
        "bic_box": bic_box,
        "box_delta_bic": gain,
        "detrend_window_days": window,
        "n_in_transit_cadences": n_box,
        "near_systematic_periods_days": near,
        "period_days": candidate.period,
    }
    if gain < params.min_box_delta_bic:
        return TestResult(
            "period_alias",
            TestStatus.FAIL,
            Severity.FATAL,
            f"a sinusoid at the found period explains the dip (adding a transit improves the "
            f"BIC by {gain:.1f} < {params.min_box_delta_bic:g})",
            metrics=metrics,
            thresholds=thresholds,
            coverage=n_box,
            coverage_unit=unit,
        )
    if near:
        return TestResult(
            "period_alias",
            TestStatus.FAIL,
            Severity.WARNING,
            f"period within {params.systematic_tolerance:.0%} of a known systematic period "
            f"({', '.join(f'{p:.3f} d' for p in near)})",
            metrics=metrics,
            thresholds=thresholds,
            coverage=n_box,
            coverage_unit=unit,
        )
    return TestResult(
        "period_alias",
        TestStatus.PASS,
        Severity.FATAL,
        f"the dip needs a transit on top of a sinusoid (BIC gain {gain:.0f}, {n_box} "
        "in-transit cadences); not near a known systematic period",
        metrics=metrics,
        thresholds=thresholds,
        coverage=n_box,
        coverage_unit=unit,
    )


# --- systematics -----------------------------------------------------------------------


def transit_centers_with_data(time: np.ndarray, candidate: Candidate) -> np.ndarray:
    if time.size == 0:
        return np.zeros(0)
    first = math.floor((time.min() - candidate.t0) / candidate.period)
    last = math.ceil((time.max() - candidate.t0) / candidate.period)
    centers = candidate.t0 + candidate.period * np.arange(first, last + 1)
    half = candidate.duration / 2
    keep = [np.any(np.abs(time - c) <= half) for c in centers]
    return centers[np.asarray(keep, dtype=bool)]


def check_systematics(aux: list[SectorAux], candidate: Candidate, plan: TessTestPlan) -> TestResult:
    """Warning if the transits line up with momentum dumps, the SAP depth disagrees
    with the PDCSAP depth corrected for crowding, or the background rises in transit.

    Strict coverage rule: each of the three sub-checks must run. If any of them
    cannot run (too few transits with data, no transit measured in SAP, PDCSAP or
    background, a non-positive depth, no CROWDSAP), the test is INCONCLUSIVE with
    the reason of each sub-check, unless another sub-check already found a problem
    (then FAIL: a problem found is evidence). Zero momentum dumps in the quality
    column is a result of the dump sub-check (the column was examined), and the
    report says so.
    """
    params: SystematicsParams = plan.gauntlet.systematics
    thresholds = params.model_dump(mode="json")
    unit = "sub-checks run"
    if not aux:
        return TestResult(
            "systematics",
            TestStatus.INCONCLUSIVE,
            Severity.WARNING,
            "no SAP flux, background or quality data available",
            thresholds=thresholds,
            coverage=0,
            coverage_unit=unit,
        )
    time = np.concatenate([a.time for a in aux])
    sector = np.concatenate([np.full(a.time.size, a.sector) for a in aux])
    dumps = np.sort(np.concatenate([a.dump_times for a in aux]))
    centers = transit_centers_with_data(time, candidate)
    reach = candidate.duration / 2 + params.dump_margin_hours / 24
    near = [bool(dumps.size and np.min(np.abs(dumps - c)) <= reach) for c in centers]
    fraction = float(np.mean(near)) if near else 0.0

    g_pdc = event_shift(time, np.concatenate([a.pdcsap_flux for a in aux]), sector, candidate, plan)
    g_sap = event_shift(time, np.concatenate([a.sap_flux for a in aux]), sector, candidate, plan)
    g_bkg = event_shift(time, np.concatenate([a.sap_bkg for a in aux]), sector, candidate, plan)
    crowds = [a.crowdsap for a in aux if a.crowdsap is not None]

    metrics: dict[str, Any] = {
        "n_transits_with_data": len(centers),
        "n_momentum_dumps": int(dumps.size),
        "n_transits_near_dumps": int(sum(near)),
        "fraction_near_dumps": fraction,
        "median_crowdsap": float(np.median(crowds)) if crowds else None,
    }
    problems: list[str] = []
    not_run: dict[str, str] = {}
    ran: list[str] = []

    if len(centers) >= params.min_events_for_dumps:
        ran.append(f"momentum dumps ({int(dumps.size)} in the quality column)")
        if fraction >= params.max_dump_fraction:
            problems.append(f"{sum(near)} of {len(centers)} transits are near momentum dumps")
    else:
        not_run["momentum_dumps"] = (
            f"only {len(centers)} transit(s) with data (< {params.min_events_for_dumps})"
        )

    if not crowds:
        not_run["sap_vs_pdcsap"] = "no CROWDSAP value"
    elif g_pdc is None or g_sap is None:
        not_run["sap_vs_pdcsap"] = "no transit measured in the PDCSAP or SAP flux"
    elif not (g_pdc.mean > 0):
        not_run["sap_vs_pdcsap"] = "the PDCSAP depth is not positive"
    else:
        crowd = float(np.median(crowds))
        expected = crowd * g_pdc.mean
        diff = g_sap.mean - expected
        sigma = abs(diff) / math.hypot(g_sap.error, crowd * g_pdc.error)
        rel = abs(diff) / expected
        metrics.update(
            {
                "depth_pdcsap_ppm": g_pdc.mean * 1e6,
                "depth_sap_ppm": g_sap.mean * 1e6,
                "expected_sap_depth_ppm": expected * 1e6,
                "sap_difference_sigma": sigma,
                "sap_relative_difference": rel,
            }
        )
        ran.append("SAP versus PDCSAP")
        if sigma >= params.max_sap_sigma and rel >= params.max_sap_rel_diff:
            problems.append(
                f"SAP depth differs from the crowding-corrected PDCSAP depth by {rel:.0%} "
                f"({sigma:.1f} sigma)"
            )

    if g_bkg is None or g_sap is None:
        not_run["background"] = "no transit measured in the background or SAP flux"
    elif not (g_sap.mean > 0):
        not_run["background"] = "the SAP depth is not positive"
    elif not (g_bkg.error > 0):
        not_run["background"] = "the background has no measurable scatter"
    else:
        rise = -g_bkg.mean
        sigma = rise / g_bkg.error
        frac = rise / g_sap.mean
        metrics.update(
            {
                "background_rise_in_transit": rise,
                "background_rise_sigma": sigma,
                "background_rise_fraction_of_depth": frac,
            }
        )
        ran.append("background")
        if sigma >= params.max_background_sigma and frac >= params.max_background_fraction:
            problems.append(
                f"the background rises in transit by {frac:.0%} of the depth ({sigma:.1f} sigma)"
            )

    metrics["sub_checks_run"] = ran
    metrics["sub_checks_not_run"] = not_run
    if problems:
        return TestResult(
            "systematics",
            TestStatus.FAIL,
            Severity.WARNING,
            "; ".join(problems),
            metrics=metrics,
            thresholds=thresholds,
            coverage=len(ran),
            coverage_unit=unit,
        )
    if not_run:
        reasons = "; ".join(f"{name}: {why}" for name, why in not_run.items())
        return TestResult(
            "systematics",
            TestStatus.INCONCLUSIVE,
            Severity.WARNING,
            f"sub-check(s) could not run ({reasons})",
            metrics=metrics,
            thresholds=thresholds,
            coverage=len(ran),
            coverage_unit=unit,
        )
    return TestResult(
        "systematics",
        TestStatus.PASS,
        Severity.WARNING,
        f"no problem in {len(ran)} sub-checks: " + ", ".join(ran),
        metrics=metrics,
        thresholds=thresholds,
        coverage=len(ran),
        coverage_unit=unit,
    )
