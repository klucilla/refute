"""v0.5.3 stage B, B1: the candidate battery version 5, outside ``src/`` (#217; the maintainer's
decision of 2026-11-11, item 3; ``docs/plans/v0.5.3-stageB1-design.md``, sections 0 and 2).
**Development code; it validates nothing.** ``method_status: not_validated``.

Version 4 (``battery_v52``, ``a0``, ``a0_v4``, ``battery_v51_diff``) is imported unchanged.
``activate(config)`` replaces, in the calling process only, the four call targets that
``pipeline_v52`` reaches; ``deactivate()`` restores version 4's objects exactly. Every new path
counts its executions and branches in ``COUNTS`` (read with ``counts()``, cleared with
``reset_counts()``), so that a record proves which path ran, not only which function was active.

- **E1** (``group_variance``): version 4's ``a0.group_variance`` first; where it refuses, a
  Cauchy-Schwarz completion of the in-window terms (the design's section 2, E1).
- **E2** (``check_odd_even``): the joint GLS contrast of the odd-even difference under A0's full
  covariance, under frozen numerical conditions; otherwise version 4's weights.
- **E3** (``box_after_model``): the residual box by GLS under white noise plus a stationary AR(1)
  in time per sector (ARMA(1,1)), a Kalman filter over the out-of-transit cadences; frozen
  moments and fallbacks.
- **E4** (``check_systematics``'s background sub-check): the box with a window-local quadratic
  baseline on its two bands, for the real events and every pseudo-window alike.
"""

from __future__ import annotations

import hashlib
import inspect
import math
from collections import Counter
from dataclasses import dataclass

import numpy as np

from refute.core.sensitivity import gaussian_probability, rule_block
from refute.core.verdict import Severity, TestResult, TestStatus
from refute.packs.tess import a0, a0_v4
from refute.packs.tess import battery_v51_diff as v51d
from refute.packs.tess import battery_v52 as v52

COUNTS: Counter = Counter()

# --- frozen constants (the design's section 2) ---------------------------------------------
E2_MAX_CONDITION = 1e8
E3_MIN_PAIRS = 200
E3_PHI_MAX = 0.99
E3_MIN_WHITE_SHARE = 0.01
E3_MAX_CONDITION = 1e8
E3_LAG_TOLERANCE = 0.1
E4_MIN_BAND = 3
E4_MAX_CONDITION = 1e6
PSD_TOLERANCE = 1e-12  # version 4's (``a0.group_variance``)


@dataclass(frozen=True)
class Config:
    e1: bool = True
    e2: bool = True
    e3: bool = True
    e4: bool = True

    def as_dict(self) -> dict:
        return {"e1": self.e1, "e2": self.e2, "e3": self.e3, "e4": self.e4}


def counts() -> dict:
    return dict(sorted(COUNTS.items()))


def reset_counts() -> None:
    COUNTS.clear()


# =============================================================================================
# E1: A0's undefined variances, a conservative completion
# =============================================================================================


def _in_window_pairs(events, windows, h, pooled):
    """Version 4's construction of the in-window correlations, without its early return: a list
    of ``(i, j, r)`` with ``r`` None where version 4 would refuse (fewer than ``MIN_PAIRS``)."""
    n = len(events)
    out = []
    cache: dict[tuple, float | None] = {}
    for i in range(n):
        for j in range(i + 1, n):
            ei, ej = events[i], events[j]
            if ei.centre > ej.centre:
                ei, ej = ej, ei
            if ei.sector != ej.sector or ei.segment != ej.segment:
                continue
            k = int(round(abs(ej.centre - ei.centre) / (2.0 * h)))
            if k < 1 or k > a0.MAX_LAG:
                continue
            sub = [w for w in windows if w.sector == ei.sector]
            key = (ei.sector, k, None, None) if pooled.get(ei.sector) else (
                ei.sector, k, ei.stratum, ej.stratum
            )  # fmt: skip
            if key not in cache:
                cache[key] = a0.lag_correlation(sub, k, key[2], key[3])[0]
            out.append((i, j, cache[key]))
    return out


def completed_variance(weights, sigmas, events, windows, h, pooled) -> tuple[float | None, str]:
    """E1's completion where version 4 refuses: (variance or None, branch)."""
    w = np.asarray(weights, dtype=float)
    s = np.asarray(sigmas, dtype=float)
    n = w.size
    pairs = _in_window_pairs(events, windows, h, pooled)
    # the matrix that decides the PSD branch: the estimated terms, zero for the missing ones
    # (Codex's round 3); used for nothing else
    decide = np.diag(s**2)
    for i, j, r in pairs:
        if r is not None:
            decide[i, j] = decide[j, i] = s[i] * s[j] * r
    eig = np.linalg.eigvalsh(decide) if n else np.zeros(0)
    psd = bool(n) and eig.min() >= -PSD_TOLERANCE * max(eig.max(), 0.0)
    var = float(np.sum(w**2 * s**2))
    if psd:
        branch = "e1.completion_missing"
        for i, j, r in pairs:
            term = 2.0 * w[i] * w[j] * s[i] * s[j]
            var += term * r if r is not None else abs(term)
    else:
        branch = "e1.completion_nonpsd"
        for i, j, _ in pairs:
            var += abs(2.0 * w[i] * w[j] * s[i] * s[j])
    return (var if var > 0 else None), branch


def group_variance(weights, sigmas, events, windows, h, pooled):
    """E1: version 4's variance when it is finite; otherwise the completion."""
    COUNTS["e1.calls"] += 1
    var = _V4["a0.group_variance"](weights, sigmas, events, windows, h, pooled)
    if var is not None:
        COUNTS["e1.v4_finite"] += 1
        return var
    out, branch = completed_variance(weights, sigmas, events, windows, h, pooled)
    COUNTS[branch] += 1
    if out is None:
        COUNTS["e1.still_undefined"] += 1
    return out


# =============================================================================================
# E2: odd_even's joint GLS contrast
# =============================================================================================


def a0_covariance(sigmas, events, windows, h, pooled) -> np.ndarray | None:
    """A0's covariance of the measured events, built exactly as version 4's ``group_variance``
    builds it; None where version 4 would refuse."""
    s = np.asarray(sigmas, dtype=float)
    cov = np.diag(s**2)
    for i, j, r in _in_window_pairs(events, windows, h, pooled):
        if r is None:
            return None
        cov[i, j] = cov[j, i] = s[i] * s[j] * r
    eig = np.linalg.eigvalsh(cov)
    if eig.min() < -PSD_TOLERANCE * max(eig.max(), 0.0):
        return None
    return cov


def gls_contrast(depths, signs, cov) -> tuple[float, float] | None:
    """The joint GLS of ``d_i = mu + s_i delta / 2``: (delta, its variance), or None when a frozen
    numerical condition fails (Cholesky, ``cond(C)``, ``cond(X^T C^-1 X)``)."""
    if np.linalg.cond(cov) > E2_MAX_CONDITION:
        return None
    try:
        chol = np.linalg.cholesky(cov)
    except np.linalg.LinAlgError:
        return None
    x = np.column_stack([np.ones(len(depths)), 0.5 * np.asarray(signs, dtype=float)])
    xw = np.linalg.solve(chol, x)  # triangular in effect: L^-1 X
    dw = np.linalg.solve(chol, np.asarray(depths, dtype=float))
    info = xw.T @ xw
    if np.linalg.cond(info) > E2_MAX_CONDITION:
        return None
    q, r = np.linalg.qr(xw)
    coef = np.linalg.solve(r, q.T @ dw)
    var = float(np.linalg.inv(info)[1, 1])
    if not (var > 0 and math.isfinite(coef[1])):
        return None
    return float(coef[1]), var


def check_odd_even(flat, measured, windows, candidate, gp, sp, cadence_days, exclude, seed):
    """E2: version 4's ``check_odd_even``, with the odd-even difference and its error from the
    joint GLS contrast where version 4's covariance is complete and the frozen conditions hold;
    otherwise version 4's computation (with E1's variance where version 4 refuses, if active)."""
    COUNTS["e2.calls"] += 1
    base = _V4["v52.check_odd_even"](
        flat, measured, windows, candidate, gp, sp, cadence_days, exclude, seed
    )
    if base.status is TestStatus.INCONCLUSIVE and base.metrics.get("inconclusive_class") == (
        "not_enough_data"
    ):
        COUNTS["e2.not_enough_data"] += 1
        return base
    params, ev = gp.odd_even, gp.events
    expected_in = candidate.duration / cadence_days
    metas = [
        a0.event_meta(flat.time, flat.sector, ctr, n / expected_in, ev.min_coverage)
        for ctr, n in zip(measured.centers.tolist(), measured.n_in.tolist(), strict=True)
    ]
    h = a0.half_width(candidate.duration, ev.baseline_outer_durations)
    pooled = {s: a0.shortcut(windows, s, seed + s) for s in {m.sector for m in metas}}
    sigmas = [float(e) for e in measured.errors]
    cov = a0_covariance(sigmas, metas, windows, h, pooled)
    if cov is None:
        COUNTS["e2.v4_path_incomplete"] += 1
        return base
    signs = np.array([1.0 if int(e) % 2 != 0 else -1.0 for e in measured.epochs])
    got = gls_contrast(measured.depths, signs, cov)
    if got is None:
        COUNTS["e2.v4_path_condition"] += 1
        return base
    COUNTS["e2.gls"] += 1
    delta, var = got
    sigma = math.sqrt(var)
    zscore = abs(delta) / sigma
    alternative = sp.odd_even_alternative_depth_fraction * candidate.depth
    block = rule_block(
        "odd/even depth difference",
        alternative * 1e6,
        "ppm",
        "gaussian-1",
        gaussian_probability(alternative, sigma, params.max_sigma),
    )
    metrics = {
        **base.metrics,
        "difference_sigma": zscore,
        "gls_difference_ppm": delta * 1e6,
        "gls_difference_err_ppm": sigma * 1e6,
        "v4_difference_sigma": base.metrics.get("difference_sigma"),
        "estimator": "joint GLS contrast of the measured box depths under A0's covariance "
        "(candidate version 5, E2)",
    }
    n_odd, n_even = int(np.sum(signs > 0)), int(np.sum(signs < 0))
    status = TestStatus.FAIL if zscore >= params.max_sigma else TestStatus.PASS
    return TestResult(
        "odd_even",
        status,
        Severity.FATAL,
        f"odd/even depths differ by {zscore:.1f} sigma ({n_odd} odd, {n_even} even; GLS)",
        metrics=metrics,
        thresholds=base.thresholds,
        coverage=len(measured),
        coverage_unit="measured transits",
        sensitivity={"main": block},
    )


# =============================================================================================
# E3: the sinusoid's residual box by an ARMA(1,1) state-space GLS
# =============================================================================================

_SINUSOID_SECTOR: dict = {"sector": None}


def _cadence(t: np.ndarray) -> float:
    d = np.diff(t)
    d = d[d > 0]
    return float(np.median(d)) if d.size else float("nan")


def moments(t: np.ndarray, r: np.ndarray, delta: float) -> dict | None:
    """The frozen moments of one sector's out-of-transit residuals (mean removed): gamma0, and
    gamma1, gamma2 over pairs exactly one and two cadences apart; None below ``E3_MIN_PAIRS``."""
    x = r - r.mean()
    out = {"gamma0": float(np.mean(x * x))}
    for lag in (1, 2):
        j = np.searchsorted(t, t + lag * delta - E3_LAG_TOLERANCE * delta, side="left")
        ok = j < t.size
        jj = np.where(ok, j, 0)
        ok &= np.abs(t[jj] - t - lag * delta) < E3_LAG_TOLERANCE * delta
        n = int(ok.sum())
        out[f"pairs{lag}"] = n
        if n < E3_MIN_PAIRS:
            return None
        out[f"gamma{lag}"] = float(np.mean(x[ok] * x[jj[ok]]))
    return out


def arma_parameters(m: dict) -> tuple[float, float, float] | str:
    """(phi, sigma_a^2, sigma_w^2) or the fallback's reason."""
    g0, g1, g2 = m["gamma0"], m["gamma1"], m["gamma2"]
    if not all(math.isfinite(v) for v in (g0, g1, g2)):
        return "non-finite moment"
    if g1 <= 0 or g2 <= 0:
        return "gamma1 or gamma2 not positive"
    phi = g2 / g1
    if not 0.0 < phi < E3_PHI_MAX:
        return "phi outside (0, 0.99)"
    sa2 = g1 / phi
    sw2 = g0 - sa2
    if sw2 <= E3_MIN_WHITE_SHARE * g0:
        return "white variance at most 0.01 gamma0"
    return phi, sa2, sw2


def whiten(t: np.ndarray, z: np.ndarray, phi: float, sa2: float, sw2: float, delta: float):
    """The Kalman filter's standardized innovations of ``z`` (rows: cadences of one sector, in
    time order, out-of-transit only; columns: series), under ``y = x + e``, ``x`` stationary AR(1)
    in time with correlation ``phi^(dt/delta)``. Returns (whitened, gains, factors, sqrtF)."""
    n = t.size
    z = z.reshape(n, -1)
    out = np.empty_like(z, dtype=float)
    gains, factors, roots = np.empty(n), np.empty(n), np.empty(n)
    state = np.zeros(z.shape[1])
    p = sa2
    prev = None
    for k in range(n):
        f = 1.0 if prev is None else phi ** ((t[k] - prev) / delta)
        state = f * state
        p = f * f * p + sa2 * (1.0 - f * f)
        big_f = p + sw2
        root = math.sqrt(big_f)
        innov = z[k] - state
        out[k] = innov / root
        gain = p / big_f
        state = state + gain * innov
        p = (1.0 - gain) * p
        gains[k], factors[k], roots[k] = gain, f, root
        prev = t[k]
    return out, gains, factors, roots


def whiten_adjoint(g: np.ndarray, gains, factors, roots) -> np.ndarray:
    """``W^T g`` for the whitening map ``W`` of ``whiten`` (the same gains), one column."""
    n = g.size
    zbar = np.empty(n)
    sbar_next = 0.0  # the adjoint of the predicted state at k + 1
    for k in range(n - 1, -1, -1):
        # forward: e_k = (z_k - s_k) / r_k ; a_k = s_k + K_k (z_k - s_k) ;
        # s_{k+1} = f_{k+1} a_k
        f_next = factors[k + 1] if k + 1 < n else 0.0
        abar = f_next * sbar_next
        zbar[k] = g[k] / roots[k] + gains[k] * abar
        sbar_next = -g[k] / roots[k] + (1.0 - gains[k]) * abar
    return zbar


def quad_k(t: np.ndarray, u: np.ndarray, phi: float, delta: float) -> float:
    """``u^T K u`` with ``K_ij = phi^(|t_i - t_j| / delta)``, ``t`` sorted: ``R_1 = 0``,
    ``R_i = phi^((t_i - t_{i-1}) / delta) (R_{i-1} + u_{i-1})``, ``sum u_i^2 + 2 sum u_i R_i``."""
    total = float(np.sum(u * u))
    run = 0.0
    for i in range(1, t.size):
        run = phi ** ((t[i] - t[i - 1]) / delta) * (run + u[i - 1])
        total += 2.0 * u[i] * run
    return total


def box_after_model(time, flux, err, kept, x_all, x_kept, candidate, beta):
    """E3: version 4's ``box_after`` and ``sigma_r`` by GLS under white plus AR(1) per sector;
    version 4's computation (and a counted reason) on any fallback."""
    COUNTS["e3.calls"] += 1
    v4 = _V4["v52.box_after_model"]
    sector = _SINUSOID_SECTOR["sector"]
    if sector is None or sector.size != time.size:
        COUNTS["e3.fallback:no sector array"] += 1
        return v4(time, flux, err, kept, x_all, x_kept, candidate, beta)
    reason = None
    params: dict[int, tuple] = {}
    # the white fit's out-of-transit residuals (version 4's weights)
    w = 1.0 / np.square(err[kept])
    xtw = x_kept.T * w
    try:
        coef_w = np.linalg.solve(xtw @ x_kept, xtw @ flux[kept])
    except np.linalg.LinAlgError:
        reason = "white fit singular"
    if reason is None:
        resid = flux[kept] - x_kept @ coef_w
        tk, sk = time[kept], sector[kept]
        for s in np.unique(sk):
            sel = sk == s
            delta = _cadence(tk[sel])
            m = moments(tk[sel], resid[sel], delta) if math.isfinite(delta) else None
            if m is None:
                reason = "fewer than 200 pairs at lag 1 or 2"
                break
            got = arma_parameters(m)
            if isinstance(got, str):
                reason = got
                break
            params[int(s)] = (*got, delta)
    if reason is not None:
        COUNTS[f"e3.fallback:{reason}"] += 1
        return v4(time, flux, err, kept, x_all, x_kept, candidate, beta)
    # whitening per sector, on the out-of-transit cadences in time order
    tk, sk, yk = time[kept], sector[kept], flux[kept]
    z = np.column_stack([yk, x_kept])
    zw = np.empty_like(z)
    filt = {}
    for s, (phi, sa2, sw2, delta) in params.items():
        idx = np.nonzero(sk == s)[0]
        order = idx[np.argsort(tk[idx], kind="stable")]
        out, gains, factors, roots = whiten(tk[order], z[order], phi, sa2, sw2, delta)
        zw[order] = out
        filt[s] = (order, gains, factors, roots)
    xw, yw = zw[:, 1:], zw[:, 0]
    q, r = np.linalg.qr(xw)
    if np.linalg.cond(r) > E3_MAX_CONDITION:
        COUNTS["e3.fallback:whitened design ill-conditioned"] += 1
        return v4(time, flux, err, kept, x_all, x_kept, candidate, beta)
    coef = np.linalg.solve(r, q.T @ yw)
    dt = np.abs(
        np.mod(time - candidate.t0 + 0.5 * candidate.period, candidate.period)
        - 0.5 * candidate.period
    )
    inside = dt <= candidate.duration / 2.0
    if not inside.any() or inside.all():
        return float("nan"), float("nan")
    a = np.where(inside, -1.0 / np.count_nonzero(inside), 1.0 / np.count_nonzero(~inside))
    box_after = float(a @ (flux - x_all @ coef))
    # u = (I - H)^T a, with H = x_all (Xw^T Xw)^-1 Xw^T W on the kept cadences:
    # H^T a = W^T Xw (Xw^T Xw)^-1 x_all^T a, padded onto the kept cadences
    g = xw @ np.linalg.solve(r, np.linalg.solve(r.T, x_all.T @ a))
    ht_a = np.zeros(int(kept.sum()))
    for order, gains, factors, roots in filt.values():
        ht_a[order] = whiten_adjoint(g[order], gains, factors, roots)
    u = a.copy()
    u[kept] -= ht_a
    var = 0.0
    for s, (phi, sa2, sw2, delta) in params.items():
        sel = sector == s
        order = np.argsort(time[sel], kind="stable")
        ts, us = time[sel][order], u[sel][order]
        var += sw2 * float(np.sum(us * us)) + sa2 * quad_k(ts, us, phi, delta)
    others = ~np.isin(sector, list(params))
    if np.any(others & (u != 0)):
        COUNTS["e3.fallback:a sector without parameters"] += 1
        return v4(time, flux, err, kept, x_all, x_kept, candidate, beta)
    COUNTS["e3.gls"] += 1
    return box_after, math.sqrt(max(var, 0.0))


def check_sinusoid(raw, candidate, sp, cp, ev, cadence_days, fail_allowed, seed):
    """Version 4's ``check_sinusoid`` with the sector array of its cadences made available to
    E3's ``box_after_model`` (the same ``good`` selection as version 4)."""
    COUNTS["e3.sinusoid_calls"] += 1
    good = np.isfinite(raw.flux) & np.isfinite(raw.flux_err) & (raw.flux_err > 0)
    _SINUSOID_SECTOR["sector"] = np.asarray(raw.sector)[good]
    try:
        return _V4["v52.check_sinusoid"](
            raw, candidate, sp, cp, ev, cadence_days, fail_allowed, seed
        )
    finally:
        _SINUSOID_SECTOR["sector"] = None


# =============================================================================================
# E4: the background box with a window-local quadratic baseline
# =============================================================================================


def quadratic_weights(dt_all: np.ndarray, base: np.ndarray, inside: np.ndarray, scale: float):
    """The weights ``c`` of the window's depth ``sum c_k f_k`` (the quadratic fitted on the
    bands, by QR on scaled time, averaged at the in-event cadences, minus the in-event mean), or
    None when a band side has fewer than ``E4_MIN_BAND`` cadences or the scaled design's
    condition passes ``E4_MAX_CONDITION``."""
    tau = dt_all / scale
    if np.sum(base & (tau < 0)) < E4_MIN_BAND or np.sum(base & (tau > 0)) < E4_MIN_BAND:
        return None
    xb = np.column_stack([np.ones(base.sum()), tau[base], tau[base] ** 2])
    q, r = np.linalg.qr(xb)
    if np.linalg.cond(r) > E4_MAX_CONDITION:
        return None
    m = np.array([1.0, tau[inside].mean(), (tau[inside] ** 2).mean()])
    # prediction of the in-event mean: m^T (Xb^T Xb)^-1 Xb^T f_b = (Q R^-T m)^T f_b
    cb = q @ np.linalg.solve(r.T, m)
    c = np.zeros(tau.size)
    c[base] = cb
    c[inside] -= 1.0 / inside.sum()
    return c


def quadratic_box(time, flux, duration, baseline_gap_durations, baseline_outer_durations,
                  min_coverage, cadence_days, sigma=None):  # fmt: skip
    """``a0.box_measure`` with E4's operator: ``measure(centre) -> (depth, coverage)`` or None
    under version 4's coverage rule; version 4's band-mean operator on E4's fallback.
    ``measure.white(centre)`` gives the operator's own white error with ``sigma``."""
    half = duration / 2.0
    inner = half + baseline_gap_durations * duration
    outer = half + baseline_outer_durations * duration
    expected_in = 2.0 * half / cadence_days
    expected_base = 2.0 * (outer - inner) / cadence_days

    def weights(centre: float):
        lo = np.searchsorted(time, centre - outer, side="left")
        hi = np.searchsorted(time, centre + outer, side="left")
        if hi <= lo:
            return None
        d = time[lo:hi] - centre
        ad = np.abs(d)
        inside, base = ad <= half, ad > inner
        n_in, n_base = int(inside.sum()), int(base.sum())
        if n_in < min_coverage * expected_in or n_base < min_coverage * expected_base:
            return None
        c = quadratic_weights(d, base, inside, outer)
        if c is None:
            COUNTS["e4.window_fallback"] += 1
            c = np.zeros(d.size)
            c[base] = 1.0 / n_base
            c[inside] = -1.0 / n_in
        else:
            COUNTS["e4.window_quadratic"] += 1
        return lo, hi, c, n_in / expected_in

    def measure(centre: float):
        got = weights(centre)
        if got is None:
            return None
        lo, hi, c, cov = got
        return float(c @ flux[lo:hi]), cov

    def white(centre: float):
        got = weights(centre)
        if got is None or sigma is None:
            return float("nan")
        lo, hi, c, _ = got
        return float(math.sqrt(np.sum((c * sigma[lo:hi]) ** 2)))

    measure.white = white
    return measure


def _comb_measure_q(preprocess, original_time, series, duration, half, ev, cadence_days):
    """``a0_v4.comb_measure`` with E4's operator on each comb's preprocessing."""
    h = a0.half_width(duration, ev.baseline_outer_durations)
    layout = a0_v4.grid(series.time, series.sector, h)
    masks = a0_v4.comb_masks(original_time, layout, h, half)
    measures: dict[int, object] = {}

    def box(j: int):
        if j not in measures:
            flat = preprocess(masks[j])
            measures[j] = quadratic_box(
                flat.time, flat.flux, duration, ev.baseline_gap_durations,
                ev.baseline_outer_durations, ev.min_coverage, cadence_days,
            )  # fmt: skip
        return measures[j]

    def measure(centre: float):
        s = a0.sector_of(series.time, series.sector, centre)
        return box(int(round((centre - layout[s][0] - h) / (2.0 * h))) % a0_v4.J)(centre)

    return measure


def a0_depth_quadratic(time, values, sector, candidate, plan, seed, exclude_phase_half=False):
    """``a0_v4.a0_depth`` with E4's operator for the real events and every pseudo-window; the
    real events' model error is the operator's own white error."""
    from refute.packs.tess import detrend_fast as df
    from refute.packs.tess.battery_v51_diff import MIN_MEASURABLE_ERROR, A0Depth
    from refute.packs.tess.events import (
        EventDepths,
        per_event_depths,
        per_point_sigma,
        transit_mask,
    )

    COUNTS["e4.calls"] += 1
    good = np.isfinite(time) & np.isfinite(values)
    time, values, sector = time[good], values[good], sector[good]
    if time.size < 10:
        return None
    order = np.argsort(time, kind="stable")
    time, values, sector = time[order], values[order], sector[order]
    half = plan.detrend.transit_mask_half_width_durations * candidate.duration
    mask = transit_mask(time, candidate.period, candidate.t0, half)
    detrender = df.AdditiveDetrender(time, values, sector, plan.detrend, mask)
    series = detrender.flat()
    ok = np.isfinite(detrender.residuals())
    sigma = per_point_sigma(series, mask[ok])
    cadence = plan.data.exptime_seconds / 86400.0
    ev = plan.gauntlet.events
    box_events = per_event_depths(
        series, candidate.period, candidate.t0, candidate.duration, cadence, ev, 0.0, sigma
    )
    if len(box_events) == 0:
        return None
    real = quadratic_box(
        series.time, series.flux, candidate.duration, ev.baseline_gap_durations,
        ev.baseline_outer_durations, ev.min_coverage, cadence, sigma=sigma,
    )  # fmt: skip
    keep, depths, errors = [], [], []
    for centre in box_events.centers.tolist():
        got = real(centre)
        keep.append(got is not None)
        depths.append(got[0] if got is not None else float("nan"))
        errors.append(real.white(centre) if got is not None else float("nan"))
    keep = np.asarray(keep, dtype=bool)
    events = EventDepths(
        box_events.epochs[keep],
        box_events.centers[keep],
        np.asarray(depths)[keep],
        np.asarray(errors)[keep],
        box_events.n_in[keep],
        {**box_events.dropped, "e4_not_measured": int((~keep).sum())},
    )
    if len(events) == 0:
        return None
    measure = _comb_measure_q(detrender.flat, time, series, candidate.duration, half, ev, cadence)
    measured, windows, _ = a0_v4.empirical_events(
        series, candidate, events, ev, cadence, measure, exclude_phase_half
    )
    if len(measured) == 0:
        return None
    expected_in = candidate.duration / cadence
    metas = []
    for centre, n_in in zip(measured.centers.tolist(), measured.n_in.tolist(), strict=True):
        meta = a0.event_meta(
            series.time, series.sector, centre, n_in / expected_in, ev.min_coverage
        )
        if meta is None:
            return None
        metas.append(meta)
    if len({m.sector for m in metas}) not in v52.GRID_SECTORS:
        return None
    errs = measured.errors
    if not np.all(np.isfinite(errs) & (errs > MIN_MEASURABLE_ERROR)):
        return None
    weights = 1.0 / np.square(errs)
    weights = weights / np.sum(weights)
    pooled = {s: a0.shortcut(windows, s, seed + s) for s in {m.sector for m in metas}}
    h = a0.half_width(candidate.duration, ev.baseline_outer_durations)
    var = a0.group_variance(weights, errs.tolist(), metas, windows, h, pooled)
    if var is None:
        return None
    COUNTS["e4.measured"] += 1
    return A0Depth(
        float(np.sum(weights * measured.depths)),
        math.sqrt(var),
        len(measured),
        windows,
        tuple(int(e) for e in measured.epochs),
        tuple(float(d) for d in measured.depths),
        tuple(float(w) for w in weights),
        tuple(m.sector for m in metas),
    )


def check_systematics(aux, candidate, plan, seed, exclude_phase_half=False, depth=None,
                      a0_aux=None, a0_refused=None):  # fmt: skip
    """Version 4's ``check_systematics`` with E4's operator for the background series only: its
    call is the one with ``seed + 3`` (``battery_v51_diff.check_systematics``)."""
    COUNTS["e4.systematics_calls"] += 1
    base_depth = depth if depth is not None else a0_v4.a0_depth

    def dispatch(t, values, s, cand, pl, call_seed, excl=False):
        if call_seed == seed + 3:
            return a0_depth_quadratic(t, values, s, cand, pl, call_seed, excl)
        return base_depth(t, values, s, cand, pl, call_seed, excl)

    return _V4["v51d.check_systematics"](
        aux, candidate, plan, seed, exclude_phase_half, depth=dispatch, a0_aux=a0_aux,
        a0_refused=a0_refused,
    )  # fmt: skip


# =============================================================================================
# activation
# =============================================================================================

_V4 = {
    "a0.group_variance": a0.group_variance,
    "v52.check_odd_even": v52.check_odd_even,
    "v52.box_after_model": v52.box_after_model,
    "v52.check_sinusoid": v52.check_sinusoid,
    "v51d.check_systematics": v51d.check_systematics,
}
_TARGETS = {
    "a0.group_variance": (a0, "group_variance"),
    "v52.check_odd_even": (v52, "check_odd_even"),
    "v52.box_after_model": (v52, "box_after_model"),
    "v52.check_sinusoid": (v52, "check_sinusoid"),
    "v51d.check_systematics": (v51d, "check_systematics"),
}
_ACTIVE: dict = {"config": None}


def _replacements(config: Config) -> dict:
    out = {}
    if config.e1:
        out["a0.group_variance"] = group_variance
    if config.e2:
        out["v52.check_odd_even"] = check_odd_even
    if config.e3:
        out["v52.box_after_model"] = box_after_model
        out["v52.check_sinusoid"] = check_sinusoid
    if config.e4:
        out["v51d.check_systematics"] = check_systematics
    return out


def activate(config: Config) -> dict:
    """Replace the call targets for ``config`` in this process; returns the activation record
    (the configuration and each replaced function's source SHA-256)."""
    deactivate()
    record = {"config": config.as_dict(), "replaced": {}}
    for name, fn in _replacements(config).items():
        module, attr = _TARGETS[name]
        setattr(module, attr, fn)
        src = inspect.getsource(fn).encode()
        record["replaced"][name] = hashlib.sha256(src).hexdigest()[:16]
    _ACTIVE["config"] = config
    return record


def deactivate() -> None:
    for name, (module, attr) in _TARGETS.items():
        setattr(module, attr, _V4[name])
    _ACTIVE["config"] = None


def check_active(config: Config | None) -> None:
    """Refuse unless the process's targets are exactly those of ``config`` (None: version 4)."""
    want = _replacements(config) if config is not None else {}
    for name, (module, attr) in _TARGETS.items():
        expect = want.get(name, _V4[name])
        if getattr(module, attr) is not expect:
            raise RuntimeError(f"battery_b1: {name} is not the expected function")


def module_sha256() -> str:
    return hashlib.sha256(inspect.getsource(inspect.getmodule(activate)).encode()).hexdigest()
