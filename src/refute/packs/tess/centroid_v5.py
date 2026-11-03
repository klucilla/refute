"""The v0.5 centroid test, per sector (docs/plans/v0.5-acceptance.md, WP4; #183, #187, #190).

The source position of each sector follows ``battery.source_offset`` (v0.4), with two changes:
the error of a centroid shift is max(formal error, the scatter of the same measurement at
out-of-transit control epochs), and the offset and its covariance are converted to the sky
(arcsec east and north) with the sector's pixel-to-sky Jacobian. A sector qualifies when the
transit is detected in its aperture flux, it has a WCS and a CROWDSAP value, and its aperture
depth agrees, at ``centroid_qualification_sigma``, with the light-curve depth times its
CROWDSAP. A fatal FAIL needs at least ``centroid_min_sectors`` qualified sectors that agree.
The FAIL states a measurement, never a cause. A PASS does not exclude unresolved blends closer
than the minimum offset.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

import numpy as np

from refute.core.chi2 import chi2_sf
from refute.core.sensitivity import rule_block, simulated_probability
from refute.core.verdict import Severity, TestResult, TestStatus
from refute.packs.tess.events import group_mean, per_event_depths, per_point_sigma, transit_mask
from refute.packs.tess.types import LightCurveData

if TYPE_CHECKING:
    from refute.packs.tess.params import TessTestPlan
    from refute.packs.tess.types import Candidate, PixelData, SectorAux

UNIT = "pixel-file cadences"
NAME = "centroid_shift"


def _detrended(time, values, sector, candidate: Candidate, plan: TessTestPlan):
    """The detrended series of ``battery.event_shift`` (the real transits masked) and its
    per-point noise, so that the same estimator can be read at any phase."""
    from refute.packs.tess.battery import additive_residuals

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
    n = int(ok.sum())
    series = LightCurveData(time[ok], 1.0 + resid[ok], np.ones(n), sector[ok], np.zeros(n))
    return series, per_point_sigma(series, mask[ok])


def shift_at(detrended, candidate: Candidate, plan: TessTestPlan, phase: float):
    """``battery.event_shift`` read at ``phase`` of the candidate's period (0: the transit)."""
    if detrended is None:
        return None
    series, sigma = detrended
    cadence = plan.data.exptime_seconds / 86400.0
    events = per_event_depths(
        series,
        candidate.period,
        candidate.t0,
        candidate.duration,
        cadence,
        plan.gauntlet.events,
        phase,
        sigma,
    )
    return None if len(events) == 0 else group_mean(events.depths, events.errors)


def control_phases(candidate: Candidate, count: int, seed: int) -> list[float]:
    """Up to ``count`` phases in [0.15, 0.35] and [0.65, 0.85], drawn with the seed, whose
    in-event windows lie at least one duration from the transit and phase-0.5 windows and do not
    overlap each other (acceptance, WP4)."""
    rng = np.random.default_rng(seed)
    p, d = candidate.period, candidate.duration
    phases: list[float] = []
    for _ in range(200 * count):
        if len(phases) == count:
            break
        u = rng.uniform(0.15, 0.35) + (0.5 if rng.uniform() < 0.5 else 0.0)
        if min(u, 1.0 - u) * p < 2.0 * d or abs(u - 0.5) * p < 2.0 * d:
            continue
        if any(abs(u - q) * p < d for q in phases):
            continue
        phases.append(float(u))
    return phases


def sector_offset(
    px: PixelData,
    candidate: Candidate,
    plan: TessTestPlan,
    crowdsap: float | None,
    seed: int,
) -> dict[str, Any] | str:
    """One sector's sky offset with its covariance, or the reason the sector does not qualify."""
    from refute.packs.tess.battery import aperture_series

    sp = plan.stronger
    if px.target_xy is None:
        return "no target position (WCS)"
    jacobian = getattr(px, "sky_jacobian", None)  # a plain PixelData has none
    if jacobian is None:
        return "no pixel-to-sky transform (WCS)"
    if crowdsap is None:
        return "no CROWDSAP (dilution unknown)"
    if not px.aperture.any():
        return "empty SPOC aperture"
    t, f, cx, cy = aperture_series(px, px.aperture)
    if t.size < 100:
        return "too few cadences with complete aperture data"
    sector = np.full(t.size, px.sector)
    det_f = _detrended(t, f / np.median(f), sector, candidate, plan)
    det_x = _detrended(t, cx, sector, candidate, plan)
    det_y = _detrended(t, cy, sector, candidate, plan)
    g_f = shift_at(det_f, candidate, plan, 0.0)
    g_x = shift_at(det_x, candidate, plan, 0.0)
    g_y = shift_at(det_y, candidate, plan, 0.0)
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
    rel = g_f.error / depth
    tx, ty = px.target_xy
    off = np.array([c_out[0] - dx * factor - tx, c_out[1] - dy * factor - ty])
    if not np.all(np.isfinite(off)):
        return "centroid offset could not be computed"
    measured = {"sector": int(px.sector), "offset_px": off}  # reported even when not qualified
    expected = candidate.depth * crowdsap
    agree = abs(depth - expected) / math.hypot(g_f.error, candidate.depth_err * crowdsap)
    if agree > sp.centroid_qualification_sigma:
        return {
            **measured,
            "not_qualified": f"aperture depth {depth * 1e6:.0f} ppm disagrees with the "
            f"light-curve depth times CROWDSAP ({expected * 1e6:.0f} ppm) at {agree:.1f} sigma",
        }
    controls_x, controls_y = [], []
    for phase in control_phases(candidate, sp.centroid_control_epochs, seed + px.sector):
        cx_c = shift_at(det_x, candidate, plan, phase)
        cy_c = shift_at(det_y, candidate, plan, phase)
        if cx_c is not None and cy_c is not None:
            controls_x.append(cx_c.mean)
            controls_y.append(cy_c.mean)
    if len(controls_x) < sp.centroid_min_controls:
        why = f"only {len(controls_x)} valid control epochs (< {sp.centroid_min_controls})"
        return {**measured, "not_qualified": why}
    # the shift covariance: max(formal, empirical) on the diagonal, the controls' empirical
    # x-y covariance off it (clipped to keep it positive definite); then the offset's
    # covariance with the term common to x and y from the uncertain depth (Codex's review)
    ctrl = np.cov(np.vstack([controls_x, controls_y]))
    var_x = max(g_x.error**2, float(ctrl[0, 0]))
    var_y = max(g_y.error**2, float(ctrl[1, 1]))
    limit = 0.99 * math.sqrt(var_x * var_y)
    cov_xy = float(np.clip(ctrl[0, 1], -limit, limit))
    shift_cov = np.array([[var_x, cov_xy], [cov_xy, var_y]])
    g = np.array([dx, dy]) * factor * rel
    cov_px = factor**2 * shift_cov + np.outer(g, g)
    if not np.all(np.isfinite(cov_px)) or np.linalg.det(cov_px) <= 0:
        return {**measured, "not_qualified": "the offset covariance is not positive definite"}
    jac = np.asarray(jacobian, dtype=float)
    return {
        **measured,
        "offset_sky": jac @ off,
        "cov_sky": jac @ cov_px @ jac.T,
        "pixel_scale": math.sqrt(abs(float(np.linalg.det(jac)))),
        "n_cadences": int(t.size),
        "controls": len(controls_x),
    }


def combine(rows: list[dict[str, Any]]) -> tuple[np.ndarray, np.ndarray, float]:
    """The weighted mean of the sky offsets with their covariances, its covariance, and the
    heterogeneity chi-square about it."""
    weights = [np.linalg.inv(r["cov_sky"]) for r in rows]
    cov = np.linalg.inv(sum(weights))
    mean = cov @ sum(w @ r["offset_sky"] for w, r in zip(weights, rows, strict=True))
    chi2 = float(
        sum(
            (r["offset_sky"] - mean) @ w @ (r["offset_sky"] - mean)
            for w, r in zip(weights, rows, strict=True)
        )
    )
    return mean, cov, chi2


def sky_power(
    rows: list[dict[str, Any]],
    alternative: float,
    min_arcsec: float,
    max_sigma: float,
    alpha: float,
    seed: int,
) -> list[float]:
    """The probability that the whole WP4 rule fails a source at ``alternative`` arcsec, in
    each of eight directions: each qualified sector's offset drawn from its own covariance, the
    draws combined as the test combines them, and a rejection only when the sectors agree
    (heterogeneity), the combined offset reaches ``max_sigma`` and the minimum offset (Codex's
    review of round 2)."""
    from refute.core.chi2 import chi2_isf
    from refute.packs.tess.battery import gaussian_sigma_from_chi2

    weights = [np.linalg.inv(r["cov_sky"]) for r in rows]
    cov = np.linalg.inv(sum(weights))
    inv = np.linalg.inv(cov)
    chols = [np.linalg.cholesky(r["cov_sky"]) for r in rows]
    dof = 2 * (len(rows) - 1)
    critical = chi2_isf(alpha, dof) if dof > 0 else float("inf")
    out = []
    for k in range(8):
        angle = 2.0 * math.pi * k / 8.0
        truth = alternative * np.array([math.cos(angle), math.sin(angle)])

        def draw(rng: np.random.Generator, n: int, truth=truth) -> np.ndarray:
            return np.stack([truth + rng.standard_normal((n, 2)) @ c.T for c in chols], axis=1)

        def reject(o: np.ndarray) -> np.ndarray:  # o: (n, sectors, 2)
            mean = np.einsum("ij,nj->ni", cov, sum(o[:, i] @ w.T for i, w in enumerate(weights)))
            chi_het = sum(
                np.einsum("ni,ij,nj->n", o[:, i] - mean, w, o[:, i] - mean)
                for i, w in enumerate(weights)
            )
            chi = np.einsum("ni,ij,nj->n", mean, inv, mean)
            sig = np.array([gaussian_sigma_from_chi2(float(c), 2) for c in chi])
            agree = chi_het <= critical
            return agree & (sig >= max_sigma) & (np.hypot(mean[:, 0], mean[:, 1]) >= min_arcsec)

        out.append(simulated_probability(draw, reject, seed + k))
    return out


def check_centroid_v5(
    pixels: list[PixelData],
    sectors_aux: list[SectorAux],
    candidate: Candidate,
    plan: TessTestPlan,
    seed: int,
) -> TestResult:
    """The v0.5 ``centroid_shift`` (fatal; see the module docstring)."""
    from refute.packs.tess.battery import MAX_SIGMA_REPORTED, gaussian_sigma_from_chi2

    severity = Severity.FATAL
    sp = plan.stronger
    params = plan.gauntlet.centroid_shift
    thresholds = {
        **params.model_dump(mode="json"),
        "min_sectors": sp.centroid_min_sectors,
        "qualification_sigma": sp.centroid_qualification_sigma,
        "max_unqualified_fraction": sp.centroid_max_unqualified_fraction,
        "control_epochs": sp.centroid_control_epochs,
        "min_controls": sp.centroid_min_controls,
        "heterogeneity_alpha": sp.chi2_alpha,
    }
    crowd = {a.sector: a.crowdsap for a in sectors_aux}
    rows: list[dict[str, Any]] = []
    skipped: dict[str, str] = {}
    measured_unqualified: dict[str, dict[str, float]] = {}
    for px in pixels:
        r = sector_offset(px, candidate, plan, crowd.get(px.sector), seed)
        if isinstance(r, str):
            skipped[str(px.sector)] = r
        elif "not_qualified" in r:
            # WP4: a non-qualifying sector is reported with its offset (Codex's review)
            skipped[str(px.sector)] = r["not_qualified"]
            measured_unqualified[str(px.sector)] = {
                "offset_x_px": float(r["offset_px"][0]),
                "offset_y_px": float(r["offset_px"][1]),
            }
        else:
            rows.append(r)
    metrics: dict[str, Any] = {
        "qualified_sectors": {
            str(r["sector"]): {
                "offset_east_arcsec": float(r["offset_sky"][0]),
                "offset_north_arcsec": float(r["offset_sky"][1]),
                "offset_x_px": float(r["offset_px"][0]),
                "offset_y_px": float(r["offset_px"][1]),
                "controls": r["controls"],
                "n_cadences": r["n_cadences"],
            }
            for r in rows
        },
        "not_qualified": skipped,
        "not_qualified_offsets": measured_unqualified,
    }
    coverage = sum(r["n_cadences"] for r in rows)

    def result(status: TestStatus, message: str, sensitivity=None) -> TestResult:
        return TestResult(
            NAME,
            status,
            severity,
            message,
            metrics=metrics,
            thresholds=thresholds,
            coverage=coverage,
            coverage_unit=UNIT,
            sensitivity=sensitivity,
        )

    if not pixels:
        return result(TestStatus.INCONCLUSIVE, "no target pixel data")
    if len(skipped) >= sp.centroid_max_unqualified_fraction * len(pixels):
        why = f"qualification failed: {len(skipped)} of {len(pixels)} sector(s) do not qualify"
        return result(TestStatus.INCONCLUSIVE, why)
    if len(rows) < sp.centroid_min_sectors:
        return result(
            TestStatus.INCONCLUSIVE, "single sector" if len(rows) == 1 else "no qualified sector"
        )
    mean, cov, chi2 = combine(rows)
    dof = 2 * (len(rows) - 1)
    p_het = chi2_sf(chi2, dof) if dof > 0 else 1.0  # one sector: nothing to disagree with
    scale = float(np.mean([r["pixel_scale"] for r in rows]))
    min_arcsec = params.min_offset_pixels * scale
    inv = np.linalg.inv(cov)
    sigma = gaussian_sigma_from_chi2(float(mean @ inv @ mean), 2)
    distance = float(np.hypot(*mean))
    metrics.update(
        {
            "combined_east_arcsec": float(mean[0]),
            "combined_north_arcsec": float(mean[1]),
            "combined_offset_arcsec": distance,
            "combined_offset_px": distance / scale,
            "offset_sigma": sigma,
            # WP6 (#186): the significance is capped; a capped value is a bound, not a measure
            "offset_sigma_saturated": bool(sigma >= MAX_SIGMA_REPORTED),
            "min_offset_arcsec": min_arcsec,
            "heterogeneity_chi2": chi2,
            "heterogeneity_dof": dof,
            "heterogeneity_p": p_het,
        }
    )
    if p_het < sp.chi2_alpha:
        return result(TestStatus.INCONCLUSIVE, f"sectors disagree (heterogeneity p = {p_het:.2g})")
    alt = sp.centroid_alternative_offset_factor * min_arcsec
    probabilities = sky_power(rows, alt, min_arcsec, params.max_sigma, sp.chi2_alpha, seed + 100)
    max_sigma = params.max_sigma
    block = {
        "main": rule_block("source offset", alt, "arcsec", "centroid-sky-sim-1", min(probabilities))
    }
    if sigma >= max_sigma and distance >= min_arcsec:
        message = (
            f"transit source offset {distance:.1f} arcsec ({distance / scale:.2f} px) from the "
            f"target, {sigma:.1f} sigma, from {len(rows)} sectors"
        )
        return result(TestStatus.FAIL, message, block)
    message = (
        f"transit source consistent with the target (offset {distance:.1f} arcsec, {sigma:.1f} "
        f"sigma, {len(rows)} sectors); a PASS does not exclude unresolved blends closer than "
        f"{min_arcsec:.1f} arcsec"
    )
    return result(TestStatus.PASS, message, block)
