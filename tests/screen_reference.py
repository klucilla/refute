"""A test-only reference evaluator of the frozen F1 equations (v0.5.11, docs/plans/v0.5.11-spec.md,
sections 4 to 6; frozen at ab828ce, SHA-256 d498a82a...).

It is written from the specification, before the `src/` implementation exists (step 1). Step 2's
implementation must reproduce its decisions on the same fixtures. It imports nothing from the
screen's own module. Exploratory, `method_status: not_validated`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

MIN_VALID = 20
MIN_IN_PER_EPOCH = 3
MIN_BASELINE = 10
MIN_BINS = 3
THRESHOLD = 3.0


@dataclass
class F1Result:
    state: str  # "pass" | "fail" | "not_assessed"
    reason: str
    coverage: int = 0
    metrics: dict = field(default_factory=dict)


def _wmean(x: np.ndarray, w: np.ndarray) -> float | None:
    if x.size == 0 or not np.isfinite(w.sum()) or w.sum() <= 0:
        return None
    return float(np.sum(w * x) / np.sum(w))


def _wstd(x: np.ndarray, w: np.ndarray) -> float | None:
    m = _wmean(x, w)
    if m is None:
        return None
    return float(math.sqrt(np.sum(w * (x - m) ** 2) / np.sum(w)))


def _epochs(t: np.ndarray, period: float, t0: float) -> np.ndarray:
    return np.floor((t - t0) / period + 0.5).astype(np.int64)


def _phase_distance(t: np.ndarray, period: float, t0: float, phi: float) -> np.ndarray:
    return np.abs(np.mod(t - t0 - phi * period + period / 2.0, period) - period / 2.0)


def noise(t, f, w, period, t0, duration):
    """(sigma_w, sigma_r, baseline mask) or (None, None, mask) when unavailable."""
    base = _phase_distance(t, period, t0, 0.0) > duration
    tb, fb, wb = t[base], f[base], w[base]
    if tb.size < MIN_BASELINE:
        return None, None, base
    sigma_w = _wstd(fb, wb)
    if sigma_w is None or not math.isfinite(sigma_w):
        return None, None, base
    t_first = float(t.min())
    idx = np.floor((tb - t_first) / duration).astype(np.int64)
    means, weights, counts = [], [], []
    for m in np.unique(idx):
        sel = idx == m
        if int(sel.sum()) < 2:
            continue
        means.append(_wmean(fb[sel], wb[sel]))
        weights.append(float(wb[sel].sum()))
        counts.append(int(sel.sum()))
    if len(means) < MIN_BINS:
        return None, None, base
    means_a, weights_a, counts_a = np.array(means), np.array(weights), np.array(counts)
    sigma_bin = _wstd(means_a, weights_a)
    expected = float(np.mean(sigma_w**2 / counts_a))
    sigma_r2 = max(0.0, sigma_bin**2 - expected)
    return sigma_w, math.sqrt(sigma_r2), base


def f1_reference(time, flux, flux_err, period, t0, duration) -> F1Result:
    """F1 by OE_box (spec section 6)."""
    t, f, s = (np.asarray(x, dtype=float) for x in (time, flux, flux_err))
    if not all(math.isfinite(v) for v in (period, t0, duration)) or period <= 0 or duration <= 0:
        return F1Result("not_assessed", "candidate not finite or not positive")
    ok = np.isfinite(t) & np.isfinite(f) & np.isfinite(s) & (s > 0)
    t, f, s = t[ok], f[ok], s[ok]
    if t.size < MIN_VALID:
        return F1Result("not_assessed", "fewer than 20 valid points")
    w = 1.0 / s**2
    sigma_w, sigma_r, base = noise(t, f, w, period, t0, duration)
    if sigma_w is None:
        return F1Result("not_assessed", "noise unavailable (baseline or bins)")
    base_mean = _wmean(f[base], w[base])
    k = _epochs(t, period, t0)
    in_tr = np.abs(t - (t0 + k * period)) <= duration / 2.0
    out = {}
    coverage = 0
    for parity, name in ((1, "odd"), (0, "even")):
        sel = in_tr & (np.mod(k, 2) == parity)
        ks, counts = np.unique(k[sel], return_counts=True)
        good = ks[counts >= MIN_IN_PER_EPOCH]
        coverage += int(good.size)
        n = int(sel.sum())
        if good.size == 0 or n < MIN_IN_PER_EPOCH:
            return F1Result("not_assessed", f"too few in-transit points for the {name} parity")
        m_in = _wmean(f[sel], w[sel])
        n_epochs = int(ks.size)
        sigma_tr = math.sqrt(sigma_w**2 / n + sigma_r**2 / n_epochs)
        if not math.isfinite(sigma_tr) or sigma_tr <= 0:
            return F1Result("not_assessed", "pink noise not finite or not positive")
        out[name] = (base_mean - m_in, sigma_tr, n, n_epochs)
    d_odd, s_odd, n_odd, e_odd = out["odd"]
    d_even, s_even, n_even, e_even = out["even"]
    denom = math.sqrt(s_odd**2 + s_even**2)
    if not math.isfinite(denom) or denom <= 0:
        return F1Result("not_assessed", "denominator not positive")
    oe = abs(d_odd - d_even) / denom
    if not math.isfinite(oe):
        return F1Result("not_assessed", "OE_box not finite")
    metrics = {
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
    state = "fail" if oe > THRESHOLD else "pass"
    return F1Result(state, f"OE_box {oe:.3f} vs {THRESHOLD}", coverage, metrics)
