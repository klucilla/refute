"""The frozen recipe of #222's measurements (v0.5.12 charter, step 1, as approved at 7df389c).

Shared by ``m1_inputs.py`` (the inputs' identity, before any F1 call) and ``m1.py`` (the
measurement). Nothing here calls F1.

- **Times and sectors:** ``synthetic.make_lightcurve(PLANET, seed=s, noise_ppm=0.0)``: two
  sectors (``TWO_YEARS``). The times do not depend on the seed.
- **The model, a noiseless box:** flux ``1 - 0.002`` on F1's exact in-transit mask
  ``|t - (t0 + kP)| <= T/2``, with ``k = floor((t - t0)/P + 0.5)``, and ``1`` elsewhere.
- **The noise stream:** ``numpy.random.default_rng([s, 222]).standard_normal(N)`` (PCG64).
  Flux is ``box + sigma_i * z_i`` and ``flux_err`` is ``sigma_i``. The families share z.
- **sigma0** = 600 ppm. The seven families are those of the charter's table.
- **The T2 and T6 cadence:** among the in-transit cadences of the smallest odd k that has any,
  the one nearest the transit's centre; a tie goes to the earlier time.
- **The B6 cadence:** the earliest cadence of the baseline, ``d(t, 0) > T``.
"""

from __future__ import annotations

import hashlib

import numpy as np

P, T0, T = 3.7, 1326.3, 2.5 / 24
DEPTH = 0.002
SIGMA0 = 600e-6
FAMILIES = ("U", "S9.5", "P2.4", "P9.5", "T2", "T6", "B6")
STREAM = 222


def geometry() -> dict:
    """The times, sectors, epochs, masks and selected cadences (independent of the seed)."""
    # imported here: ruff sorts refute differently inside and outside the container
    from refute.packs.tess.synthetic import PLANET, make_lightcurve

    lc, _ = make_lightcurve(PLANET, seed=1, noise_ppm=0.0)
    t = np.asarray(lc.time, dtype=float)
    sector = np.asarray(lc.sector)
    k = np.floor((t - T0) / P + 0.5)
    intr = np.abs(t - (T0 + k * P)) <= T / 2.0
    d0 = np.abs(np.mod(t - T0 + P / 2.0, P) - P / 2.0)
    odd = np.mod(k, 2) == 1
    k_odd = int(min(k[intr & odd]))
    cand = np.where(intr & (k == k_odd))[0]
    centre = T0 + k_odd * P
    t_idx = int(cand[np.lexsort((t[cand], np.abs(t[cand] - centre)))[0]])
    b_idx = int(np.where(d0 > T)[0][0])
    first_sector = sector == sector.min()
    return {"t": t, "intr": intr, "odd": odd, "first": first_sector, "t_idx": t_idx, "b_idx": b_idx}


def sigmas(g: dict, family: str) -> np.ndarray:
    s = np.full(g["t"].size, SIGMA0)
    if family == "S9.5":
        s[~g["first"]] = 9.5 * SIGMA0
    elif family == "P2.4":
        s[g["odd"]] = 2.4 * SIGMA0
    elif family == "P9.5":
        s[g["odd"]] = 9.5 * SIGMA0
    elif family == "T2":
        s[g["t_idx"]] = SIGMA0 / 100.0
    elif family == "T6":
        s[g["t_idx"]] = SIGMA0 / 1e6
    elif family == "B6":
        s[g["b_idx"]] = SIGMA0 / 1e6
    elif family != "U":
        raise ValueError(family)
    return s


def curve(g: dict, family: str, seed: int, depth_odd_extra=None):
    """(time, flux, flux_err) of one case. ``depth_odd_extra`` is for step 4's sensitivity
    control only (an added odd-parity box depth); None for M1 and M2."""
    t = g["t"]
    box = np.where(g["intr"], 1.0 - DEPTH, 1.0)
    if depth_odd_extra is not None:
        box = box - np.where(g["intr"] & g["odd"], depth_odd_extra, 0.0)
    s = sigmas(g, family)
    z = np.random.default_rng([seed, STREAM]).standard_normal(t.size)
    return t, box + s * z, s


def input_sha256(t: np.ndarray, f: np.ndarray, s: np.ndarray) -> str:
    h = hashlib.sha256()
    for a in (t, f, s):
        h.update(np.ascontiguousarray(a, dtype="<f8").tobytes())
    return h.hexdigest()
