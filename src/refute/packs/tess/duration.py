"""Transit-duration uncertainty (v0.4 WP4, issue #176), as specified before the code in
docs/plans/v0.4-duration-method.md (method ``trapezoid-least-squares-1``).

A symmetric trapezoid (centre offset, flat-bottom depth, total duration, ingress) is fitted by
least squares to the detrended cadences within 1.5 BLS durations of each transit centre; the
duration error comes from the covariance at the solution, scaled by the reduced chi-square when
it is above 1. The result is either a value with its error (a 68 % interval) or an explicit,
justified absence: passing the gate is not enough.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

METHOD = "trapezoid-least-squares-1"
# The method failed case 4.1 of its acceptance on 2026-10-29 (coverage 0.54 and 0.55 of the
# nominal 0.68 at SNR 20 and 40; docs/validation/v0.4/wp4-duration-acceptance.md). Until the
# maintainer decides, its values are recorded in verdict.json but never exported as an
# uncertainty.
METHOD_ACCEPTED = False
NOT_ACCEPTED_REASON = (
    f"the method {METHOD} did not pass its acceptance "
    "(docs/validation/v0.4/wp4-duration-acceptance.md)"
)
WINDOW_DURATIONS = 1.5
MIN_IN_TRANSIT = 10
MIN_TRANSITS = 2
MAX_RELATIVE_ERROR = 0.5
MAX_DURATION_FACTOR = 3.0


def _shape(dt: np.ndarray, duration: float, ingress: float) -> np.ndarray:
    half = duration / 2.0
    return np.clip((half - np.abs(dt)) / max(ingress, 1e-9), 0.0, 1.0)


def estimate_duration(
    time: np.ndarray,
    flux: np.ndarray,
    sigma: np.ndarray,
    period: float,
    t0: float,
    duration_bls: float,
    depth: float,
    cadence_days: float,
) -> dict[str, Any]:
    """The duration (days) with its error, or an absence with the reason of the first rule that
    fails (docs/plans/v0.4-duration-method.md)."""
    from scipy.optimize import least_squares

    out: dict[str, Any] = {
        "method": METHOD,
        "estimable": False,
        "duration_days": None,
        "duration_err_days": None,
        "reason": "",
    }
    time, flux, sigma = (np.asarray(a, dtype=float) for a in (time, flux, sigma))
    good = np.isfinite(time) & np.isfinite(flux) & np.isfinite(sigma) & (sigma > 0)
    time, flux, sigma = time[good], flux[good], sigma[good]
    if not (period > 0 and duration_bls > 0):
        out["reason"] = "no period or duration to fit"
        return out
    epoch = np.round((time - t0) / period)
    dt = time - t0 - epoch * period
    window = np.abs(dt) <= WINDOW_DURATIONS * duration_bls
    if window.sum() < 5:
        out["reason"] = "fewer than 5 cadences in the transit windows"
        return out
    dt, y, s, ep = dt[window], flux[window], sigma[window], epoch[window]
    upper_t = MAX_DURATION_FACTOR * duration_bls

    def residuals(p: np.ndarray) -> np.ndarray:
        c, d, total, ingress = p
        ingress = min(ingress, total / 2.0)
        return (y - (1.0 - d * _shape(dt - c, total, ingress))) / s

    start = [0.0, max(depth, 1e-6), duration_bls, 0.15 * duration_bls]
    lower = [-0.5 * duration_bls, 0.0, cadence_days, cadence_days * 1e-3]
    upper = [0.5 * duration_bls, 1.0, upper_t, upper_t / 2.0]
    start = [
        min(max(v, lo + 1e-12), hi - 1e-12) for v, lo, hi in zip(start, lower, upper, strict=True)
    ]
    try:
        fit = least_squares(residuals, start, bounds=(lower, upper), method="trf")
    except (ValueError, np.linalg.LinAlgError) as exc:
        out["reason"] = f"the fit failed: {exc}"
        return out
    c, d, total, ingress = fit.x
    out.update({"fit_status": int(fit.status), "depth": float(d), "ingress_days": float(ingress)})
    if fit.status <= 0:
        out["reason"] = "the fit did not converge"
        return out
    try:
        cov = np.linalg.inv(fit.jac.T @ fit.jac)
    except np.linalg.LinAlgError:
        out["reason"] = "the covariance is singular"
        return out
    dof = max(1, y.size - 4)
    chi2 = float(np.sum(fit.fun**2)) / dof
    if chi2 > 1.0:
        cov = cov * chi2
    var = float(cov[2, 2])
    if not (math.isfinite(var) and var > 0):
        out["reason"] = "the duration variance is not finite and positive"
        return out
    err = math.sqrt(var)
    inside = np.abs(dt - c) < total / 2.0
    n_in = int(inside.sum())
    n_transits = int(np.unique(ep[inside]).size)
    out.update(
        {
            "reduced_chi2": chi2,
            "in_transit_cadences": n_in,
            "transits": n_transits,
            "fitted_duration_days": float(total),
            "fitted_duration_err_days": err,
        }
    )
    at_bound = total <= lower[2] * (1 + 1e-6) or total >= upper[2] * (1 - 1e-6)
    rules = [
        (n_in >= MIN_IN_TRANSIT, f"fewer than {MIN_IN_TRANSIT} in-transit cadences"),
        (n_transits >= MIN_TRANSITS, f"fewer than {MIN_TRANSITS} transits with data"),
        (ingress >= cadence_days, "the ingress is not resolved (shorter than one cadence)"),
        (err / total <= MAX_RELATIVE_ERROR, f"relative error above {MAX_RELATIVE_ERROR:g}"),
        (not at_bound, "the fitted duration is at a bound of the fit"),
    ]
    for ok, why in rules:
        if not ok:
            out["reason"] = why
            return out
    out.update(
        {"estimable": True, "duration_days": float(total), "duration_err_days": err, "reason": ""}
    )
    return out
