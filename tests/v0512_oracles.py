"""Independent, test-only oracles of v0.5.12 step 2 (#223) and correction 2 (revision 1, adopted
at SHA-256 c24e7fd9...). They are written from the specification texts and import nothing from
``src/``. Exploratory, ``method_status: not_validated``.

- ``f1_corrected``: F1 by correction 2 revision 1, section 4 (the effective epoch count of B1,
  alternative A), with the frozen guards and reasons of specification §6 and correction 1.
- ``mes_f2_u1``: the frozen §5 MES grid, its events and the F2 and U1 records, with the frozen
  noise of ``screen_reference.noise`` (report-only noise does not change; correction 2's scope).
- ``trap_fits``: the overall trapezoid and the two parity fits of §5 (F1_trap), with the frozen
  solver settings.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from screen_reference import noise as frozen_noise  # noqa: E402
from v0512_fixtures import trap_model  # noqa: E402

SIGMA_MIN, SIGMA_MAX = 1e-12, 1e3
INT_EXACT = float(2**53)
THRESHOLD = 3.0
NOISE_REASON = "noise unavailable (baseline or bins)"


class NumericalFailureError(Exception):
    pass


def _wmean(x, w):
    if x.size == 0:
        return None
    sw = float(np.sum(w))
    if not math.isfinite(sw) or sw <= 0:
        return None
    m = float(np.sum(w * x) / sw)
    return m if math.isfinite(m) else None


def _index(x):
    if x.size and (not np.all(np.isfinite(x)) or float(np.max(np.abs(x))) >= INT_EXACT):
        raise NumericalFailureError("ValueError")
    return x.astype(np.int64)


def _phase(t, period, t0, phi=0.0):
    return np.abs(np.mod(t - t0 - phi * period + period / 2.0, period) - period / 2.0)


def corrected_noise(t, f, w, period, t0, duration):
    """(s2, sigma_r2, m_b, base) or None: revision 1, section 4."""
    base = _phase(t, period, t0) > duration
    tb, fb, wb = t[base], f[base], w[base]
    nb = int(tb.size)
    if nb < 10:
        return None
    m_b = _wmean(fb, wb)
    if m_b is None:
        return None
    s2 = float(np.sum(wb * (fb - m_b) ** 2) / (nb - 1))
    if not math.isfinite(s2) or s2 <= 0:
        return None
    idx = _index(np.floor((tb - float(t.min())) / duration))
    mus, ws = [], []
    for m in np.unique(idx):
        sel = idx == m
        if int(sel.sum()) < 2:
            continue
        mu = _wmean(fb[sel], wb[sel])
        if mu is None:
            return None
        mus.append(mu)
        ws.append(float(np.sum(wb[sel])))
    if len(mus) < 3:
        return None
    mu, wk = np.array(mus), np.array(ws)
    big_b = float(np.sum(wk))
    mu_bar = float(np.sum(wk * mu) / big_b)
    q0 = float(np.sum(wk * (mu - mu_bar) ** 2))
    prefix = np.concatenate(([0.0], np.cumsum(wk)[:-1]))
    c = float(2.0 * np.sum(wk * (prefix / big_b)))
    if not (math.isfinite(q0) and math.isfinite(c) and math.isfinite(mu_bar)) or c <= 0:
        return None
    sig_r2 = max(0.0, (q0 - s2 * (mu.size - 1)) / c)
    if not math.isfinite(sig_r2):
        return None
    return s2, sig_r2, m_b, base


def f1_corrected(time, flux, flux_err, period, t0, duration) -> dict:
    try:
        with np.errstate(all="ignore"):
            return _f1(time, flux, flux_err, period, t0, duration)
    except NumericalFailureError as exc:
        return {"state": "not_assessed", "reason": f"numerical failure: {exc}", "metrics": {}}


def _na(reason, metrics=None):
    return {"state": "not_assessed", "reason": reason, "metrics": metrics or {}}


def _f1(time, flux, flux_err, period, t0, duration):
    try:
        t, f, s = (np.asarray(x, dtype=float) for x in (time, flux, flux_err))
    except (TypeError, ValueError) as exc:
        raise NumericalFailureError(type(exc).__name__) from None
    if not all(math.isfinite(v) for v in (period, t0, duration)) or period <= 0 or duration <= 0:
        return _na("candidate not finite or not positive")
    ok = np.isfinite(t) & np.isfinite(f) & np.isfinite(s) & (s > 0)
    counts = {"dropped": int((~ok).sum()), "valid": int(ok.sum())}
    sm = s[np.isfinite(t) & np.isfinite(f)]
    if not np.all(np.isfinite(sm) & (sm >= SIGMA_MIN) & (sm <= SIGMA_MAX)):
        return _na("invalid_uncertainty", counts)
    t, f, s = t[ok], f[ok], s[ok]
    if t.size < 20:
        return _na("fewer than 20 valid points", counts)
    w = 1.0 / s**2
    k = _index(np.floor((t - t0) / period + 0.5))
    in_tr = np.abs(t - (t0 + k * period)) <= duration / 2.0
    noise = corrected_noise(t, f, w, period, t0, duration)
    if noise is None:
        return _na(NOISE_REASON, counts)
    s2, sig_r2, m_b, _ = noise
    out = {}
    for parity, name in ((1, "odd"), (0, "even")):
        sel = in_tr & (np.mod(k, 2) == parity)
        ks, n_in = np.unique(k[sel], return_counts=True)
        n = int(sel.sum())
        if int((n_in >= 3).sum()) == 0 or n < 3:
            return _na(f"too few in-transit points for the {name} parity", counts)
        m_in = _wmean(f[sel], w[sel])
        w_par = float(np.sum(w[sel]))
        inv = np.searchsorted(ks, k[sel])
        w_e = np.bincount(inv, weights=w[sel])
        n_eff = w_par**2 / float(np.sum(w_e**2))
        var = s2 / w_par + sig_r2 / n_eff
        if m_in is None or not math.isfinite(var):
            return _na(f"depth or pink noise unavailable for the {name} parity", counts)
        out[name] = (m_in, var, n, int(ks.size), n_eff, w_par)
    denom = math.sqrt(out["odd"][1] + out["even"][1])
    if not math.isfinite(denom) or denom <= 0:
        return _na("denominator not positive", counts)
    oe = abs(out["odd"][0] - out["even"][0]) / denom
    if not math.isfinite(oe):
        return _na("OE_box not finite", counts)
    metrics = {
        **counts,
        "oe_box": oe,
        "delta_odd": m_b - out["odd"][0],
        "delta_even": m_b - out["even"][0],
        "sigma_odd": math.sqrt(out["odd"][1]),
        "sigma_even": math.sqrt(out["even"][1]),
        "n_odd": out["odd"][2],
        "n_even": out["even"][2],
        "epochs_odd": out["odd"][3],
        "epochs_even": out["even"][3],
        "epochs_eff_odd": out["odd"][4],
        "epochs_eff_even": out["even"][4],
        "s2": s2,
        "weight_odd": out["odd"][5],
        "weight_even": out["even"][5],
        "sigma_r": math.sqrt(sig_r2),
    }
    state = "fail" if oe > THRESHOLD else "pass"
    return {"state": state, "reason": f"OE_box {oe:.3f} vs {THRESHOLD}", "metrics": metrics}


# --- the frozen MES grid, F2 and U1 (specification section 5) ----------------------------------


def _pink(sigma_w, sigma_r, n, n_epochs):
    if n <= 0 or n_epochs <= 0:
        return None
    v = math.sqrt(sigma_w**2 / n + sigma_r**2 / n_epochs)
    return v if math.isfinite(v) and v > 0 else None


def _cells(t, f, w, period, t0, duration, sigma_w, sigma_r, base):
    ratio = 4.0 * period / duration
    if ratio > t.size:
        return None
    cells = []
    for j in range(int(math.ceil(ratio))):
        phi = j * (duration / 4.0) / period
        d = _phase(t, period, t0, phi)
        inn, ref = d <= duration / 2.0, base & (d > duration)
        n = int(inn.sum())
        if n < 3 or int(ref.sum()) < 10:
            continue
        m_ref, m_in = _wmean(f[ref], w[ref]), _wmean(f[inn], w[inn])
        if m_ref is None or m_in is None:
            continue
        idx = _index(np.floor((t[inn] - t0 - phi * period) / period + 0.5))
        sigma = _pink(sigma_w, sigma_r, n, int(np.unique(idx).size))
        if sigma is None:
            continue
        mes = (m_ref - m_in) / sigma
        if math.isfinite(mes):
            cells.append((j, phi, mes, m_ref - m_in))
    return cells


def _dist(a, b, period):
    x = (a - b) * period
    return abs(((x + period / 2.0) % period) - period / 2.0)


def _best(cells, keep, value):
    best = None
    for c in cells:
        if keep(c) and (best is None or value(c) > value(best)):
            best = c
    return best


def mes_f2_u1(t, f, s, period, t0, duration) -> dict:
    """{'F2': {...}, 'U1': {...}}: state, reason and metrics of the frozen section 5."""
    from scipy.special import erfcinv

    w = 1.0 / s**2
    sigma_w, sigma_r, base = frozen_noise(t, f, w, period, t0, duration)
    if sigma_w is None:
        return _both("noise unavailable")
    cells = _cells(t, f, w, period, t0, duration, sigma_w, sigma_r, base)
    if cells is None:
        return _both("the MES grid exceeds the number of valid cadences")
    pri = _best(cells, lambda c: True, lambda c: c[2])

    def far(c, others, sep):
        return all(_dist(c[1], o[1], period) >= sep * duration for o in others)

    sec = _best(cells, lambda c: far(c, [pri], 2), lambda c: c[2]) if pri else None
    ter = _best(cells, lambda c: far(c, [pri, sec], 2), lambda c: c[2]) if sec else None
    pos = _best(cells, lambda c: far(c, [pri, sec], 3), lambda c: -c[2]) if sec else None
    if None in (pri, sec, ter, pos):
        return _both("an event (pri, sec, ter or pos) has no candidate cell")
    rest = [c[2] for c in cells if far(c, [pri, sec], 2)]
    fred = float(np.std(np.array(rest))) if len(rest) >= 10 else None
    fa1 = math.sqrt(2.0) * float(erfcinv(duration / period))
    fa2 = math.sqrt(2.0) * float(erfcinv(duration / period))
    mes_pos = -pos[2]
    ok = fred is not None and fred > 0
    ms = {
        "MS1": pri[2] / fred - fa1 if ok else None,
        "MS2": (pri[2] - ter[2]) - fa2,
        "MS3": (pri[2] - mes_pos) - fa2,
        "MS4": sec[2] / fred - fa1 if ok else None,
        "MS5": (sec[2] - ter[2]) - fa2,
        "MS6": (sec[2] - mes_pos) - fa2,
    }
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
    u1_metrics = {**events, **{k: ms[k] for k in ("MS1", "MS2", "MS3")}}
    u1 = {"state": "computed", "reason": "model shift MS1 to MS3", "metrics": u1_metrics}
    u1["coverage"] = len(cells)
    if duration / period > 0.1:
        return {"F2": {"state": "unavailable", "reason": "T/P above 0.1"}, "U1": u1}
    if fred is None:
        first = None
    elif fred > 1.8:
        first = True
    elif ms["MS4"] is None:
        first = None
    else:
        first = ms["MS4"] > 0
    sig = None if first is None else bool(ms["MS5"] > -1 and ms["MS6"] > -1 and first)
    d_pri, d_sec = pri[3], sec[3]
    exc = bool(d_sec < 0.1 * d_pri) if d_pri > 0 else None
    f2 = {
        "state": "computed",
        "reason": "model shift MS4 to MS6",
        "coverage": len(cells),
        "metrics": {
            **events,
            "delta_pri": d_pri,
            "delta_sec": d_sec,
            **{k: ms[k] for k in ("MS4", "MS5", "MS6")},
            "would_be_significant": sig,
            "exception_first_condition": exc,
        },
    }
    return {"F2": f2, "U1": u1}


def _both(reason):
    return {r: {"state": "unavailable", "reason": reason} for r in ("F2", "U1")}


# --- the trapezoid fits (specification section 5) --------------------------------------------

Q_IN_REDUCED = (0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4)
SETTINGS = dict(method="trf", x_scale="jac", ftol=1e-10, xtol=1e-10, gtol=1e-10, max_nfev=2000)


def _lsq(fun, x0, lo, hi):
    from scipy.optimize import least_squares

    fit = least_squares(fun, np.asarray(x0, float), bounds=(lo, hi), **SETTINGS)
    if fit.status <= 0 or not np.all(np.isfinite(fit.x)) or not np.all(np.isfinite(fit.fun)):
        return None
    return fit


def trap_fits(t, f, s, period, t0c, duration) -> dict:
    """The overall fit and F1_trap's two parity fits; values for the oracle's assertions."""
    w = 1.0 / s**2
    base = _phase(t, period, t0c) > duration
    inn = _phase(t, period, t0c) <= duration / 2.0
    depth0 = _wmean(f[base], w[base]) - _wmean(f[inn], w[inn])
    k = np.floor((t - t0c) / period + 0.5)
    sel = np.abs(t - (t0c + k * period)) <= 2.0 * duration
    tt, ff, ss = t[sel], f[sel], s[sel]
    q_lo = duration / (10.0 * period)
    q0 = min(max(duration / period, q_lo), 0.5)
    lo = [t0c - duration / 2.0, 0.0, q_lo, 0.5]
    hi = [t0c + duration / 2.0, 1.0, 0.5, 1.5]
    best = None
    for q_in in Q_IN_REDUCED:
        fit = _lsq(
            lambda x, q_in=q_in: (ff - trap_model(tt, x[0], x[1], x[2], q_in, x[3], period)) / ss,
            [t0c, min(max(depth0, 0.0), 1.0), q0, 1.0],
            lo,
            hi,
        )
        if fit is not None and (best is None or float(np.sum(fit.fun**2)) < best[0]):
            best = (float(np.sum(fit.fun**2)), q_in, fit.x)
    _, q_in0, x = best
    fit = _lsq(
        lambda y: (ff - trap_model(tt, y[0], y[1], y[2], y[3], y[4], period)) / ss,
        [x[0], x[1], x[2], q_in0, x[3]],
        lo[:3] + [0.0, 0.5],
        hi[:3] + [0.5, 1.5],
    )
    t0f, depth, q, q_in, f0 = (float(v) for v in fit.x)
    out = {"overall": {"t0": t0f, "depth": depth, "q": q, "q_in": q_in, "f0": f0}}
    par = {}
    for parity, name in ((1, "odd"), (0, "even")):
        m = sel & (np.mod(k, 2) == parity)
        tp, fp, sp = t[m], f[m], s[m]
        lo2, hi2 = [t0c - duration / 2.0, 0.0], [t0c + duration / 2.0, 1.0]
        x0 = [min(max(t0f, lo2[0]), hi2[0]), min(max(depth, 0.0), 1.0)]

        def res(z, tp=tp, fp=fp, sp=sp):
            return (fp - trap_model(tp, z[0], z[1], q, q_in, f0, period)) / sp

        pf = _lsq(res, x0, lo2, hi2)
        jtj = pf.jac.T @ pf.jac
        cov = np.linalg.inv(jtj) * float(np.sum(pf.fun**2) / (tp.size - 2))
        err = np.sqrt(np.diag(cov))
        par[name] = (float(pf.x[0]), float(pf.x[1]), float(err[0]), float(err[1]), int(tp.size))
    (to, do, sto, sdo, no), (te, de, ste, sde, ne) = par["odd"], par["even"]
    out["F1_trap"] = {
        "fit_cadences_odd": no,
        "fit_cadences_even": ne,
        "OE_trap": abs(do - de) / math.sqrt(sdo**2 + sde**2),
        "OE_trap_T": abs(to - te) / math.sqrt(sto**2 + ste**2),
    }
    return out


def f4_closed_form(d_f: float, q: float, q_in: float, period: float) -> dict:
    """V = sqrt(dF) + b (SM03 Eqs. 6, 7) from the generating parameters."""
    t_t, t_f = q * period, q * period * (1.0 - 2.0 * q_in)
    ratio = math.sin(t_f * math.pi / period) ** 2 / math.sin(t_t * math.pi / period) ** 2
    r = math.sqrt(d_f)
    b = math.sqrt(((1 - r) ** 2 - ratio * (1 + r) ** 2) / (1.0 - ratio))
    return {"dF": d_f, "b": b, "V": r + b}
