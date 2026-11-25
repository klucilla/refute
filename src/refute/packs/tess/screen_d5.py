"""The screen of battery version 5 (discovery version 5): level 1, never a verdict.

Implements the frozen specification docs/plans/v0.5.11-spec.md (commit ab828ce, SHA-256
``SPEC_SHA256``), v0.5.11, exploratory, ``method_status: not_validated``.

- **The core** is F1, decided by OE_box alone (K25 Eq. 11, threshold 3).
- **Report-only:** F1_trap, F2, F3, F4 and U1. Their paper thresholds are displayed, never
  applied.
- **Inputs:** the version-2 gauntlet's flattened curve and final candidate, plus the star record
  for F3. They are never written.
- **Separation:** nothing here enters ``aggregate`` or any legacy rule, and no random number is
  drawn.
- **Containment:** a numerical failure never leaves this module.
  - In F1 it gives ``not_assessed``.
  - In a report-only quantity it gives ``unavailable``, for that quantity and for those that
    depend on the same fit. The core, the other quantities and level 2 are unaffected.

Every [choice] of the specification is implemented as written. The equations' sources are in
docs/plans/sources/v0.5.11-screen-papers-2026-11-24.md. No GPL implementation was read.

**Correction 1** (docs/plans/v0.5.11-spec-correction-1.md, SHA-256 ``CORRECTION_SHA256``): every
sigma of the cadences with finite time and flux must be finite and in [1e-12, 1e3]. Otherwise F1
is ``not_assessed`` and each report-only quantity ``unavailable``, with the reason
``invalid_uncertainty``. The weight is the unscaled 1/sigma^2.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

SPEC_SHA256 = "d498a82ada2e31a5b47768d58d6af2e19af0a3c5e35364693f04886068612f15"
CORRECTION_SHA256 = "62a5532f01c498901dd2c1546ad428e33cb4669efa14caf3d80d57f9b19b6df7"
SIGMA_MIN, SIGMA_MAX = 1e-12, 1e3  # correction 1: the input range of sigma, both ends included
INVALID_UNCERTAINTY = "invalid_uncertainty"
LABELS = ["exploratory", "method_status: not_validated"]
GATE_TEST = "snr"
F1_THRESHOLD = 3.0
MIN_VALID = 20
MIN_IN_PER_EPOCH = 3
MIN_BASELINE = 10
MIN_BINS = 3
MIN_CELL_IN = 3
MIN_CELL_REF = 10
MIN_FRED_CELLS = 10
N_TCE = 1
F2_MAX_DURATION_RATIO = 0.1
Q_IN_REDUCED = (0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4)
MAX_COND = 1e12
F1_UNIT = "parity epochs with data"
PAPER = {
    "F1_trap": {"OE_trap": 3.0, "OE_trap_T": 10.0},
    "F2": {"MS4": 0.0, "MS5": -1.0, "MS6": -1.0, "F_red_bypass": 1.8, "depth_ratio": 0.1},
    "F3": {"Rp_earth": 22.0},
    "F4": {"V": 1.5},
    "U1": {"MS1": 0.2, "MS2": 0.8, "MS3": 0.8},
}
UNITS = {
    "F1_trap": "fit cadences",
    "F2": "phase cells with data",
    "F3": "fit cadences",
    "F4": "fit cadences",
    "U1": "phase cells with data",
}
NUMERICAL = (ArithmeticError, ValueError, TypeError, np.linalg.LinAlgError)
F2_FLAGS = {"would_be_significant": None, "exception_first_condition": None}


# --- shared quantities (spec section 5) -------------------------------------------------------


def _finite(*values) -> bool:
    return all(v is not None and math.isfinite(v) for v in values)


def _wmean(x: np.ndarray, w: np.ndarray) -> float | None:
    if x.size == 0:
        return None
    sw = float(np.sum(w))
    if not math.isfinite(sw) or sw <= 0:
        return None
    m = float(np.sum(w * x) / sw)
    return m if math.isfinite(m) else None


def _wstd(x: np.ndarray, w: np.ndarray) -> float | None:
    m = _wmean(x, w)
    if m is None:
        return None
    v = float(np.sum(w * (x - m) ** 2) / np.sum(w))
    return math.sqrt(v) if math.isfinite(v) and v >= 0 else None


INT_EXACT = float(2**53)  # integers above this are not exact in a float64


def _as_index(x: np.ndarray) -> np.ndarray:
    """Floats that hold integers, cast to int64 only when finite and exactly representable;
    otherwise a ValueError, which the guards turn into not_assessed or unavailable."""
    if x.size and (not np.all(np.isfinite(x)) or float(np.max(np.abs(x))) >= INT_EXACT):
        raise ValueError("an epoch or bin index is not finite or not exactly representable")
    return x.astype(np.int64)


def _epochs(t: np.ndarray, period: float, t0: float) -> np.ndarray:
    return _as_index(np.floor((t - t0) / period + 0.5))


def _phase_distance(t: np.ndarray, period: float, t0: float, phi: float) -> np.ndarray:
    return np.abs(np.mod(t - t0 - phi * period + period / 2.0, period) - period / 2.0)


def _valid(time, flux, flux_err):
    """The valid points of the frozen predicate (t, f and sigma finite, sigma > 0) and the count
    dropped."""
    t, f, s = (np.asarray(x, dtype=float) for x in (time, flux, flux_err))
    ok = np.isfinite(t) & np.isfinite(f) & np.isfinite(s) & (s > 0)
    return t[ok], f[ok], s[ok], int((~ok).sum())


def _sigma_in_range(time, flux, flux_err) -> bool:
    """Correction 1: every sigma of the cadences with finite t and f is finite and in
    [SIGMA_MIN, SIGMA_MAX]."""
    t, f, s = (np.asarray(x, dtype=float) for x in (time, flux, flux_err))
    sm = s[np.isfinite(t) & np.isfinite(f)]
    with np.errstate(invalid="ignore"):
        return bool(np.all(np.isfinite(sm) & (sm >= SIGMA_MIN) & (sm <= SIGMA_MAX)))


def _weights(s: np.ndarray) -> np.ndarray:
    """The weights of the valid set: the unscaled 1/sigma^2 of section 5. Under correction 1
    every sigma is in [1e-12, 1e3], so every weight is in [1e-6, 1e24] and, for up to 1e7
    points, no sum or weighted mean can overflow (the correction's section 4)."""
    return 1.0 / s**2


def _candidate_ok(period, t0, duration) -> bool:
    return _finite(period, t0, duration) and period > 0 and duration > 0


def _noise(t, f, w, period, t0, duration):
    """(sigma_w, sigma_r, baseline mask), or (None, None, mask) when unavailable."""
    base = _phase_distance(t, period, t0, 0.0) > duration
    tb, fb, wb = t[base], f[base], w[base]
    if tb.size < MIN_BASELINE:
        return None, None, base
    sigma_w = _wstd(fb, wb)
    if sigma_w is None:
        return None, None, base
    t_first = float(t.min())
    idx = _as_index(np.floor((tb - t_first) / duration))
    means, weights, counts = [], [], []
    for m in np.unique(idx):
        sel = idx == m
        if int(sel.sum()) < 2:
            continue
        mean = _wmean(fb[sel], wb[sel])
        if mean is None:
            return None, None, base
        means.append(mean)
        weights.append(float(wb[sel].sum()))
        counts.append(int(sel.sum()))
    if len(means) < MIN_BINS:
        return None, None, base
    means_a, weights_a, counts_a = np.array(means), np.array(weights), np.array(counts)
    sigma_bin = _wstd(means_a, weights_a)
    if sigma_bin is None:
        return None, None, base
    expected = float(np.mean(sigma_w**2 / counts_a))
    sigma_r2 = max(0.0, sigma_bin**2 - expected)
    if not _finite(sigma_r2):
        return None, None, base
    return sigma_w, math.sqrt(sigma_r2), base


def _pink(sigma_w: float, sigma_r: float, n: int, n_epochs: int) -> float | None:
    if n <= 0 or n_epochs <= 0:
        return None
    v = math.sqrt(sigma_w**2 / n + sigma_r**2 / n_epochs)
    return v if math.isfinite(v) and v > 0 else None


def _core(state: str, reason: str, coverage: int = 0, metrics: dict | None = None) -> dict:
    return {
        "state": state,
        "reason": reason,
        "coverage": int(coverage),
        "coverage_unit": F1_UNIT,
        "metrics": metrics or {},
        "threshold": F1_THRESHOLD,
    }


# --- F1, the core (spec sections 4 and 6) -------------------------------------------------------


def f1_box(time, flux, flux_err, period, t0, duration) -> dict:
    """F1 by OE_box (K25 Eq. 11): pass, fail or not_assessed. A numerical failure gives
    not_assessed."""
    try:
        with np.errstate(all="ignore"):
            return _f1_box(time, flux, flux_err, period, t0, duration)
    except NUMERICAL as exc:
        return _core("not_assessed", f"numerical failure: {type(exc).__name__}")


def _f1_box(time, flux, flux_err, period, t0, duration) -> dict:
    if not _candidate_ok(period, t0, duration):
        return _core("not_assessed", "candidate not finite or not positive")
    t, f, s, dropped = _valid(time, flux, flux_err)
    counts = {"dropped": dropped, "valid": int(t.size)}
    if not _sigma_in_range(time, flux, flux_err):
        return _core("not_assessed", INVALID_UNCERTAINTY, 0, counts)
    if t.size < MIN_VALID:
        return _core("not_assessed", "fewer than 20 valid points", 0, counts)
    w = _weights(s)
    k = _epochs(t, period, t0)
    in_tr = np.abs(t - (t0 + k * period)) <= duration / 2.0
    sel_by, good_by = {}, {}
    for parity, name in ((1, "odd"), (0, "even")):
        sel = in_tr & (np.mod(k, 2) == parity)
        ks, n_in = np.unique(k[sel], return_counts=True)
        sel_by[name] = (sel, ks)
        good_by[name] = int((n_in >= MIN_IN_PER_EPOCH).sum())
    coverage = good_by["odd"] + good_by["even"]
    sigma_w, sigma_r, base = _noise(t, f, w, period, t0, duration)
    if sigma_w is None:
        return _core("not_assessed", "noise unavailable (baseline or bins)", coverage, counts)
    base_mean = _wmean(f[base], w[base])
    if base_mean is None:
        return _core("not_assessed", "baseline mean unavailable", coverage, counts)
    out = {}
    for name in ("odd", "even"):
        sel, ks = sel_by[name]
        n = int(sel.sum())
        if good_by[name] == 0 or n < MIN_IN_PER_EPOCH:
            reason = f"too few in-transit points for the {name} parity"
            return _core("not_assessed", reason, coverage, counts)
        m_in = _wmean(f[sel], w[sel])
        sigma_tr = _pink(sigma_w, sigma_r, n, int(ks.size))
        if m_in is None or sigma_tr is None:
            reason = f"depth or pink noise unavailable for the {name} parity"
            return _core("not_assessed", reason, coverage, counts)
        out[name] = (base_mean - m_in, sigma_tr, n, int(ks.size))
    d_odd, s_odd, n_odd, e_odd = out["odd"]
    d_even, s_even, n_even, e_even = out["even"]
    denom = math.sqrt(s_odd**2 + s_even**2)
    if not math.isfinite(denom) or denom <= 0:
        return _core("not_assessed", "denominator not positive", coverage, counts)
    oe = abs(d_odd - d_even) / denom
    if not math.isfinite(oe):
        return _core("not_assessed", "OE_box not finite", coverage, counts)
    metrics = {
        **counts,
        "oe_box": oe,
        "delta_odd": d_odd,
        "delta_even": d_even,
        "sigma_odd": s_odd,
        "sigma_even": s_even,
        "n_odd": n_odd,
        "n_even": n_even,
        "epochs_odd": e_odd,
        "epochs_even": e_even,
        "sigma_w": sigma_w,
        "sigma_r": sigma_r,
    }
    state = "fail" if oe > F1_THRESHOLD else "pass"
    return _core(state, f"OE_box {oe:.3f} vs {F1_THRESHOLD}", coverage, metrics)


# --- report-only (spec sections 5 and 6) --------------------------------------------------------


def _ro(name: str, state: str, reason: str, coverage: int, metrics=None) -> dict:
    return {
        "state": state,
        "reason": reason,
        "coverage": int(coverage),
        "coverage_unit": UNITS[name],
        "metrics": metrics or {},
        "paper_thresholds": dict(PAPER[name]),
    }


def _unavailable(name: str, reason: str, coverage: int = 0, metrics=None) -> dict:
    if name == "F2":
        metrics = {**F2_FLAGS, **(metrics or {})}
    return _ro(name, "unavailable", reason, coverage, metrics)


def _mes(t, f, w, period, t0, duration, sigma_w, sigma_r, base):
    """The MES grid: a list of (j, phi, mes, depth) for cells with a finite value; None when the
    grid is unavailable."""
    ratio = 4.0 * period / duration
    if not math.isfinite(ratio) or ratio > t.size:
        return None
    cells = []
    for j in range(int(math.ceil(ratio))):
        phi = j * (duration / 4.0) / period
        d = _phase_distance(t, period, t0, phi)
        inn = d <= duration / 2.0
        ref = base & (d > duration)
        n = int(inn.sum())
        if n < MIN_CELL_IN or int(ref.sum()) < MIN_CELL_REF:
            continue
        m_ref, m_in = _wmean(f[ref], w[ref]), _wmean(f[inn], w[inn])
        if m_ref is None or m_in is None:
            continue
        depth = m_ref - m_in
        idx = _as_index(np.floor((t[inn] - t0 - phi * period) / period + 0.5))
        n_epochs = int(np.unique(idx).size)
        sigma = _pink(sigma_w, sigma_r, n, n_epochs)
        if sigma is None or not math.isfinite(depth):
            continue
        mes = depth / sigma
        if math.isfinite(mes):
            cells.append((j, phi, mes, depth))
    return cells


def _cell_distance(phi_a: float, phi_b: float, period: float) -> float:
    x = (phi_a - phi_b) * period
    return abs(((x + period / 2.0) % period) - period / 2.0)


def _pick(cells, keep, value):
    """The first cell (smallest j) with the largest value among those kept."""
    best = None
    for c in cells:
        if not keep(c):
            continue
        if best is None or value(c) > value(best):
            best = c
    return best


def _events(cells, period, duration):
    pri = _pick(cells, lambda c: True, lambda c: c[2])
    if pri is None:
        return None

    def far(c, others, sep):
        return all(_cell_distance(c[1], o[1], period) >= sep * duration for o in others)

    sec = _pick(cells, lambda c: far(c, [pri], 2), lambda c: c[2])
    if sec is None:
        return pri, None, None, None, None
    ter = _pick(cells, lambda c: far(c, [pri, sec], 2), lambda c: c[2])
    pos = _pick(cells, lambda c: far(c, [pri, sec], 3), lambda c: -c[2])
    rest = [c[2] for c in cells if far(c, [pri, sec], 2)]
    fred = float(np.std(np.array(rest))) if len(rest) >= MIN_FRED_CELLS else None
    if fred is not None and not math.isfinite(fred):
        fred = None
    return pri, sec, ter, pos, fred


def _num(x):
    """A finite float, or None."""
    return float(x) if x is not None and math.isfinite(x) else None


def _f2_u1(t, f, w, period, t0, duration, sigma_w, sigma_r, base):
    from scipy.special import erfcinv

    def both(reason: str, cov: int):
        return _unavailable("F2", reason, cov), _unavailable("U1", reason, cov)

    if sigma_w is None:
        return both("noise unavailable", 0)
    cells = _mes(t, f, w, period, t0, duration, sigma_w, sigma_r, base)
    if cells is None:
        return both("the MES grid exceeds the number of valid cadences", 0)
    ev = _events(cells, period, duration)
    cov = len(cells)
    if ev is None or ev[1] is None or ev[2] is None or ev[3] is None:
        return both("an event (pri, sec, ter or pos) has no candidate cell", cov)
    pri, sec, ter, pos, fred = ev
    fa1 = _num(math.sqrt(2.0) * erfcinv(duration / (period * N_TCE)))
    fa2 = _num(math.sqrt(2.0) * erfcinv(duration / period))
    if fa1 is None or fa2 is None:
        return both("FA1 or FA2 not finite", cov)
    mes_pos = -pos[2]
    fred_ok = fred is not None and fred > 0
    ms1 = _num(pri[2] / fred - fa1) if fred_ok else None
    ms2 = _num((pri[2] - ter[2]) - fa2)
    ms3 = _num((pri[2] - mes_pos) - fa2)
    ms4 = _num(sec[2] / fred - fa1) if fred_ok else None
    ms5 = _num((sec[2] - ter[2]) - fa2)
    ms6 = _num((sec[2] - mes_pos) - fa2)
    events = {
        "MES_pri": pri[2],
        "phase_pri": pri[1],
        "MES_sec": sec[2],
        "phase_sec": sec[1],
        "MES_ter": ter[2],
        "phase_ter": ter[1],
        "MES_pos": mes_pos,
        "phase_pos": pos[1],
        "F_red": fred,
        "FA1": fa1,
        "FA2": fa2,
    }
    u1 = _ro("U1", "computed", "model shift MS1 to MS3", cov,
             {**events, "MS1": ms1, "MS2": ms2, "MS3": ms3})  # fmt: skip
    if duration / period > F2_MAX_DURATION_RATIO:
        return _unavailable("F2", "T/P above 0.1", cov, events), u1
    d_pri, d_sec = pri[3], sec[3]
    # K25 IV.3: MS4 > 0 is ignored when F_red > 1.8; null when a needed input is unavailable
    if fred is None:
        first = None
    elif fred > 1.8:
        first = True
    elif ms4 is None:
        first = None
    else:
        first = ms4 > 0
    if first is None or ms5 is None or ms6 is None:
        significant = None
    else:
        significant = bool(ms5 > -1 and ms6 > -1 and first)
    if _finite(d_pri, d_sec) and d_pri > 0:
        first_condition = bool(d_sec < 0.1 * d_pri)
    else:
        first_condition = None
    metrics = {
        **events,
        "delta_pri": d_pri,
        "delta_sec": d_sec,
        "MS4": ms4,
        "MS5": ms5,
        "MS6": ms6,
        "would_be_significant": significant,
        "exception_first_condition": first_condition,
    }
    return _ro("F2", "computed", "model shift MS4 to MS6", cov, metrics), u1


def _trap_model(t, t0, depth, q, q_in, f0, period):
    dt = np.mod(t - t0 + period / 2.0, period) - period / 2.0
    total = q * period
    tau = q_in * total
    half = total / 2.0
    ad = np.abs(dt)
    ramp = (half - ad) / tau if tau > 0 else np.zeros_like(ad)
    shape = np.where(ad <= half - tau, 1.0, np.where(ad < half, ramp, 0.0))
    return f0 - depth * shape


def _fit(fun, x0, lower, upper):
    """``least_squares`` with the frozen settings, or None when the bounds collapse, the start is
    not finite or outside its bounds, or the solver fails."""
    from scipy.optimize import least_squares

    x0, lo, hi = (np.asarray(v, dtype=float) for v in (x0, lower, upper))
    if not (np.all(np.isfinite(x0)) and np.all(np.isfinite(lo)) and np.all(np.isfinite(hi))):
        return None
    if np.any(lo >= hi) or np.any(x0 < lo) or np.any(x0 > hi):
        return None
    try:
        fit = least_squares(
            fun,
            x0,
            bounds=(lo, hi),
            method="trf",
            x_scale="jac",
            ftol=1e-10,
            xtol=1e-10,
            gtol=1e-10,
            max_nfev=2000,
        )
    except NUMERICAL:
        return None
    if fit.status <= 0 or not np.all(np.isfinite(fit.x)) or not np.all(np.isfinite(fit.fun)):
        return None
    return fit


def _uncertainties(fit, n_pts: int) -> np.ndarray | None:
    k = fit.x.size
    if n_pts - k < 1 or np.any(fit.active_mask != 0):
        return None
    jtj = fit.jac.T @ fit.jac
    if not np.all(np.isfinite(jtj)):
        return None
    try:
        if np.linalg.cond(jtj) > MAX_COND:
            return None
        cov = np.linalg.inv(jtj) * float(np.sum(fit.fun**2) / (n_pts - k))
    except np.linalg.LinAlgError:
        return None
    var = np.diag(cov)
    if not np.all(np.isfinite(var)) or np.any(var <= 0):
        return None
    return np.sqrt(var)


def _trapezoid(t, f, s, period, t0c, duration, depth0):
    """The overall fit: (params dict, fit cadences) or (None, cadences)."""
    k = _epochs(t, period, t0c)
    sel = np.abs(t - (t0c + k * period)) <= 2.0 * duration
    tt, ff, ss = t[sel], f[sel], s[sel]
    n = int(tt.size)
    if n < 6:
        return None, n
    q_lo = duration / (10.0 * period)
    q0 = min(max(duration / period, q_lo), 0.5)
    d0 = min(max(depth0, 0.0), 1.0)
    lo = [t0c - duration / 2.0, 0.0, q_lo, 0.5]
    hi = [t0c + duration / 2.0, 1.0, 0.5, 1.5]
    best = None
    for q_in in Q_IN_REDUCED:

        def res(x, q_in=q_in):
            return (ff - _trap_model(tt, x[0], x[1], x[2], q_in, x[3], period)) / ss

        fit = _fit(res, [t0c, d0, q0, 1.0], lo, hi)
        if fit is None:
            continue
        chi2 = float(np.sum(fit.fun**2))
        if best is None or chi2 < best[0]:
            best = (chi2, q_in, fit.x)
    if best is None:
        return None, n
    _, q_in0, x = best

    def res5(y):
        return (ff - _trap_model(tt, y[0], y[1], y[2], y[3], y[4], period)) / ss

    start = [x[0], x[1], x[2], q_in0, x[3]]
    fit = _fit(res5, start, lo[:3] + [0.0, 0.5], hi[:3] + [0.5, 1.5])
    if fit is None:
        return None, n
    t0, depth, q, q_in, f0 = (float(v) for v in fit.x)
    return {"t0": t0, "depth": depth, "q": q, "q_in": q_in, "f0": f0}, n


def _parity_fit(t, f, s, period, t0c, duration, overall, parity):
    k = _epochs(t, period, t0c)
    sel = (np.abs(t - (t0c + k * period)) <= 2.0 * duration) & (np.mod(k, 2) == parity)
    tt, ff, ss = t[sel], f[sel], s[sel]
    n = int(tt.size)
    if n < 4:
        return None, n
    q, q_in, f0 = overall["q"], overall["q_in"], overall["f0"]

    def res(x):
        return (ff - _trap_model(tt, x[0], x[1], q, q_in, f0, period)) / ss

    lo, hi = [t0c - duration / 2.0, 0.0], [t0c + duration / 2.0, 1.0]
    x0 = [min(max(overall["t0"], lo[0]), hi[0]), min(max(overall["depth"], 0.0), 1.0)]
    fit = _fit(res, x0, lo, hi)
    if fit is None:
        return None, n
    err = _uncertainties(fit, n)
    if err is None:
        return None, n
    return (float(fit.x[0]), float(fit.x[1]), float(err[0]), float(err[1])), n


def _f1_trap(t, f, s, period, t0, duration, overall):
    if overall is None:
        return _unavailable("F1_trap", "the overall trapezoid did not converge")
    odd, n_odd = _parity_fit(t, f, s, period, t0, duration, overall, 1)
    even, n_even = _parity_fit(t, f, s, period, t0, duration, overall, 0)
    counts = {"fit_cadences_odd": n_odd, "fit_cadences_even": n_even}
    cov = n_odd + n_even
    if odd is None or even is None:
        return _unavailable("F1_trap", "a parity fit or its uncertainties were refused", cov,
                            counts)  # fmt: skip
    (to, do, sto, sdo), (te, de, ste, sde) = odd, even
    den_d, den_t = math.sqrt(sdo**2 + sde**2), math.sqrt(sto**2 + ste**2)
    if not (den_d > 0 and den_t > 0):
        return _unavailable("F1_trap", "a denominator is not positive", cov, counts)
    oe_d, oe_t = _num(abs(do - de) / den_d), _num(abs(to - te) / den_t)
    if oe_d is None or oe_t is None:
        return _unavailable("F1_trap", "a statistic is not finite", cov, counts)
    metrics = {**counts, "OE_trap": oe_d, "OE_trap_T": oe_t}
    return _ro("F1_trap", "computed", "odd and even trapezoid fits", cov, metrics)


def _reliable_radius(star, plausibility) -> float | None:
    """The stellar radius under the legacy plausibility rule (gauntlet.check_plausibility)."""
    if star is None:
        return None
    unreliable = {d.upper() for d in plausibility.unreliable_tic_dispositions}
    if star.disposition and star.disposition.upper() in unreliable:
        return None
    r, e = star.radius_rsun, star.radius_err_rsun
    if not (_finite(r) and r > 0 and _finite(e) and e > 0):
        return None
    if e / r > plausibility.max_stellar_radius_rel_err:
        return None
    return float(r)


def _delta_f(overall) -> float | None:
    if overall is None or not _finite(overall["f0"]) or overall["f0"] <= 0:
        return None
    df = overall["depth"] / overall["f0"]
    return df if math.isfinite(df) and 0 < df < 1 else None


def _f3(overall, n, star, plausibility):
    from astropy import units as u

    df = _delta_f(overall)
    if df is None:
        return _unavailable("F3", "no converged trapezoid with 0 < dF < 1", n)
    r = _reliable_radius(star, plausibility)
    if r is None:
        return _unavailable("F3", "no reliable stellar radius (legacy rule)", n)
    rp = _num(float((r * math.sqrt(df) * u.R_sun).to(u.R_earth).value))
    if rp is None:
        return _unavailable("F3", "Rp not finite", n)
    return _ro("F3", "computed", "Rp = R* sqrt(dF) (SM03 Eq. 6)", n,
               {"dF": df, "R_star_rsun": r, "Rp_earth": rp})  # fmt: skip


def _f4(t, period, overall, n):
    df = _delta_f(overall)
    if df is None:
        return _unavailable("F4", "no converged trapezoid with 0 < dF < 1", n)
    q, q_in, t0 = overall["q"], overall["q_in"], overall["t0"]
    if not q_in < 0.5:
        return _unavailable("F4", "no flat bottom (q_in = 0.5)", n)
    t_t, t_f = q * period, q * period * (1.0 - 2.0 * q_in)
    dt = np.abs(np.mod(t - t0 + period / 2.0, period) - period / 2.0)
    if not np.any(dt < t_f / 2.0):
        return _unavailable("F4", "no cadence inside the flat interval", n)
    s_t = math.sin(t_t * math.pi / period) ** 2
    if not (math.isfinite(s_t) and s_t > 0):
        return _unavailable("F4", "Eq. 7 ratio undefined", n)
    ratio = math.sin(t_f * math.pi / period) ** 2 / s_t
    denom = 1.0 - ratio
    if not (math.isfinite(denom) and denom > 0):
        return _unavailable("F4", "Eq. 7 denominator not positive", n)
    bracket = ((1 - math.sqrt(df)) ** 2 - ratio * (1 + math.sqrt(df)) ** 2) / denom
    if not (math.isfinite(bracket) and bracket >= 0):
        return _unavailable("F4", "Eq. 7 bracket negative", n)
    b = math.sqrt(bracket)
    return _ro("F4", "computed", "V = sqrt(dF) + b (SM03 Eqs. 6, 7)", n,
               {"dF": df, "b": b, "V": math.sqrt(df) + b})  # fmt: skip


def _guard(names, fn):
    """Run ``fn``; a numerical failure makes every quantity in ``names`` unavailable."""
    try:
        with np.errstate(all="ignore"):
            return fn()
    except NUMERICAL as exc:
        why = f"numerical failure: {type(exc).__name__}"
        out = tuple(_unavailable(n, why) for n in names)
        return out if len(out) > 1 else out[0]


def report_only(flattened, candidate, star, plausibility=None) -> dict:
    """F1_trap, F2, F3, F4 and U1: computed or unavailable; no effect on the screen."""
    from refute.packs.tess.params import PlausibilityParams

    plausibility = plausibility or PlausibilityParams()
    period, t0, duration = candidate.period, candidate.t0, candidate.duration
    names = ("F1_trap", "F2", "F3", "F4", "U1")
    t, f, s, _ = _valid(flattened.time, flattened.flux, flattened.flux_err)
    if not _candidate_ok(period, t0, duration):
        return {n: _unavailable(n, "candidate or curve not usable") for n in names}
    if not _sigma_in_range(flattened.time, flattened.flux, flattened.flux_err):
        return {n: _unavailable(n, INVALID_UNCERTAINTY) for n in names}
    if t.size < MIN_VALID:
        return {n: _unavailable(n, "candidate or curve not usable") for n in names}
    w = _weights(s)

    def noise():
        return _noise(t, f, w, period, t0, duration)

    noise_out = _guard(("F2", "U1"), noise)
    if isinstance(noise_out, tuple) and len(noise_out) == 2:
        f2, u1 = noise_out
        sigma_w = sigma_r = None
        base = _phase_distance(t, period, t0, 0.0) > duration
    else:
        sigma_w, sigma_r, base = noise_out
        f2, u1 = _guard(
            ("F2", "U1"), lambda: _f2_u1(t, f, w, period, t0, duration, sigma_w, sigma_r, base)
        )

    def overall_fit():
        # the start needs only the box depth, not the noise (spec section 5)
        inn = _phase_distance(t, period, t0, 0.0) <= duration / 2.0
        m_base, m_in = _wmean(f[base], w[base]), _wmean(f[inn], w[inn])
        if m_base is None or m_in is None:
            return None, 0
        return _trapezoid(t, f, s, period, t0, duration, m_base - m_in)

    fitted = _guard(("F1_trap",), overall_fit)
    if isinstance(fitted, dict):  # the shared fit failed numerically: its dependents too
        why = fitted["reason"]
        return {
            "F1_trap": fitted,
            "F2": f2,
            "F3": _unavailable("F3", why),
            "F4": _unavailable("F4", why),
            "U1": u1,
        }
    overall, n = fitted
    return {
        "F1_trap": _guard(("F1_trap",), lambda: _f1_trap(t, f, s, period, t0, duration, overall)),
        "F2": f2,
        "F3": _guard(("F3",), lambda: _f3(overall, n, star, plausibility)),
        "F4": _guard(("F4",), lambda: _f4(t, period, overall, n)),
        "U1": u1,
    }


# --- the screen record (spec section 3) ---------------------------------------------------------


def _eligible(candidate, tests) -> tuple[bool, str]:
    gate = next((r for r in tests if r.name == GATE_TEST), None)
    if gate is None:
        return False, "no gate test in the final results"
    if gate.status.value != "PASS":
        return False, f"the gate test is {gate.status.value}"
    if candidate is None or not _candidate_ok(candidate.period, candidate.t0, candidate.duration):
        return False, "no final candidate with finite P > 0, t0 and T > 0"
    return True, "the gate passed and the candidate is finite"


def compute_screen(flattened, candidate, tests, star=None, plausibility=None) -> dict[str, Any]:
    """The screen record: never a verdict, never an input of the legacy aggregation."""
    eligible, why = _eligible(candidate, tests)
    record: dict[str, Any] = {
        "version": 5,
        "spec_sha256": SPEC_SHA256,
        "spec_correction_sha256": CORRECTION_SHA256,
        "entry": "search",
        "eligible": eligible,
        "outcome": None,
        "reason": why,
        "core": {},
        "report_only": {},
        "labels": list(LABELS),
    }
    if not eligible:
        return record
    if flattened is None:
        # Codex's second review of the step-2 diff, item 2: eligible, but no curve to measure
        why = "no flattened curve"
        record["core"] = {"F1": _core("not_assessed", why)}
        record["report_only"] = {n: _unavailable(n, why) for n in UNITS}
        record["outcome"], record["reason"] = "unassessed", "a core test was not assessed"
        return record
    f1 = f1_box(
        flattened.time,
        flattened.flux,
        flattened.flux_err,
        candidate.period,
        candidate.t0,
        candidate.duration,
    )
    record["core"] = {"F1": f1}
    try:
        record["report_only"] = report_only(flattened, candidate, star, plausibility)
    except NUMERICAL as exc:  # a last guard: the core and level 2 are never affected
        why = f"numerical failure: {type(exc).__name__}"
        record["report_only"] = {n: _unavailable(n, why) for n in UNITS}
    states = [c["state"] for c in record["core"].values()]
    if "fail" in states:
        record["outcome"], record["reason"] = "rejected", "a core test failed"
    elif "not_assessed" in states:
        record["outcome"], record["reason"] = "unassessed", "a core test was not assessed"
    else:
        record["outcome"], record["reason"] = "retained", "every core test was assessed and passed"
    return record
