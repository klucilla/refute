"""The synthetic fixtures of v0.5.12 step 2 (#223) and correction 2's suite. Test-only; it imports
nothing from ``src/``. Exploratory, ``method_status: not_validated``.

The geometry (``docs/validation/v0.5.12/step2/README.md``): one sector, a 10-minute cadence from
t = 1325.0 for 27 days (3,888 cadences); the candidate P = 3.7 d, t0 = 1326.3, T = 2.5/24 d. The
flux is a model plus a white Gaussian noise ``sigma * default_rng([seed, 223]).standard_normal``,
then the named modifications. ``build(case)`` returns a plain dict; the same recipe always gives
the same bytes.
"""

from __future__ import annotations

import math

import numpy as np

DT = 10.0 / 1440.0
N = 3888
T_START = 1325.0
P, T0, T = 3.7, 1326.3, 2.5 / 24.0
STREAM = 223


def times() -> np.ndarray:
    return T_START + np.arange(N) * DT


def epochs(t, period, t0) -> np.ndarray:
    return np.floor((t - t0) / period + 0.5)


def phase_distance(t, period, t0, phi=0.0) -> np.ndarray:
    return np.abs(np.mod(t - t0 - phi * period + period / 2.0, period) - period / 2.0)


def in_transit(t, period, t0, duration) -> np.ndarray:
    k = epochs(t, period, t0)
    return np.abs(t - (t0 + k * period)) <= duration / 2.0


def trap_model(t, t0, depth, q, q_in, f0, period) -> np.ndarray:
    """The trapezoid of the specification's section 5 (total duration q*P, ingress q_in of it)."""
    dt = np.mod(t - t0 + period / 2.0, period) - period / 2.0
    total = q * period
    tau = q_in * total
    half = total / 2.0
    ad = np.abs(dt)
    ramp = (half - ad) / tau if tau > 0 else np.zeros_like(ad)
    shape = np.where(ad <= half - tau, 1.0, np.where(ad < half, ramp, 0.0))
    return f0 - depth * shape


def build(case: dict) -> dict:
    """The fixture of one case: {t, f, s, period, t0, duration, star}."""
    period = case.get("period", P)
    t0 = case.get("t0", T0)
    duration = case.get("duration", T)
    t = times()
    model = case.get("model", "null")
    f = np.ones(N)
    k = epochs(t, P, T0)
    intr = in_transit(t, P, T0, case.get("model_duration", duration))
    odd = np.mod(k, 2) == 1
    if model == "box":
        d_even = case["depth"]
        d_odd = case.get("depth_odd", d_even)
        f = f - np.where(intr & odd, d_odd, 0.0) - np.where(intr & ~odd, d_even, 0.0)
        sec = case.get("secondary")
        if sec:
            in_sec = phase_distance(t, P, T0 + sec["offset_days"]) <= duration / 2.0
            f = f - np.where(in_sec, sec["depth"], 0.0)
    elif model == "trapezoid":
        p = case["trapezoid"]
        f = trap_model(t, T0, p["depth"], p["q"], p["q_in"], p["f0"], P)
    sigma = case.get("sigma", 1e-4)
    s = np.full(N, sigma)
    seed = case.get("seed")
    if seed is not None:
        f = f + sigma * np.random.default_rng([seed, STREAM]).standard_normal(N)
    for mod in case.get("mods", []):
        t, f, s = _apply(mod, t, f, s, period, t0, duration)
    return {
        "t": t,
        "f": f,
        "s": s,
        "period": period,
        "t0": t0,
        "duration": duration,
        "star": case.get("star"),
    }


def _apply(mod, t, f, s, period, t0, duration):
    name = mod["name"]
    k = epochs(t, P, T0)
    intr = in_transit(t, P, T0, T)
    odd = np.mod(k, 2) == 1
    base = phase_distance(t, P, T0) > T
    f, s = f.copy(), s.copy()
    if name == "first":
        keep = np.arange(t.size) < mod["count"]
        return t[keep], f[keep], s[keep]
    if name == "window":
        keep = (t >= mod["start"]) & (t <= mod["end"])
        return t[keep], f[keep], s[keep]
    if name == "sigma_at":
        s[mod["index"]] = mod["value"]
    elif name == "constant_baseline":
        f[base] = 1.0
    elif name == "set":
        sel = {
            "baseline_first": np.arange(t.size) == int(np.where(base)[0][0]),
            "odd_in": intr & odd,
            "even_in": intr & ~odd,
            "all": np.ones(t.size, dtype=bool),
        }[mod["where"]]
        if "flux" in mod:
            f[sel] = mod["flux"]
        if "sigma" in mod:
            s[sel] = mod["sigma"]
    elif name == "drop":
        drop = {
            "odd_in": intr & odd,
            "even_in": intr & ~odd,
            "near_transit": phase_distance(t, P, T0) <= 2.0 * T,
        }[mod["where"]]
        if mod.get("keep_first"):
            idx = np.where(drop)[0][: mod["keep_first"]]
            drop[idx] = False
        return t[~drop], f[~drop], s[~drop]
    elif name == "drop_odd_fit_but":
        near = (np.abs(t - (T0 + k * P)) <= 2.0 * T) & odd
        idx = np.where(near)[0]
        drop = np.zeros(t.size, dtype=bool)
        drop[idx[mod["keep"] :]] = True
        return t[~drop], f[~drop], s[~drop]
    elif name == "flux_text":
        f = f.astype(object)
        f[mod["index"]] = "x"
    else:
        raise ValueError(name)
    return t, f, s


def rp_earth(radius_rsun: float, d_f: float) -> float:
    """Rp = R* sqrt(dF) in Earth radii (SM03 Eq. 6), through astropy's units."""
    from astropy import units as u

    return float((radius_rsun * math.sqrt(d_f) * u.R_sun).to(u.R_earth).value)
