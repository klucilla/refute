"""v0.5.5: the fix of I4's convergence check (#218; the maintainer's decision of 2026-11-20, night,
item 3a). ``method_status: not_validated``.

**What I4 checks.** I4's ``odd_even`` bound (``docs/validation/v0.5.4/i4_bound.py``) uses the
analytic derivatives of the generator's trapezoid with respect to ``t0``, ``period``,
``duration`` and ``ingress_fraction``, and checks each against central differences
``(f(+h) - f(-h)) / 2h`` at frozen steps: the planet is invalid if any relative L2 difference
passes 1e-2 (``i4_bound.convergence``, ``CONVERGENCE_TOL``).

**The hypothesis** (the independent review's): the trapezoid has corners (where the ramp meets the
flat bottom, and where it meets the out-of-transit level). At a cadence whose two perturbed
evaluations ``f(+h)`` and ``f(-h)`` fall on different sides of a corner, the central difference is
not the derivative on either side, so it differs from the analytic one there by an O(1) amount,
and a few such cadences can pass 1e-2 in L2 although the analytic derivatives are right.

**The fix (declared).** The same comparison, restricted to the cadences whose segment (out of
transit, ramp, flat) is the same at ``-h``, ``0`` and ``+h``: the only cadences where a central
difference estimates a derivative. The analytic derivatives, the Fisher matrix and the bound are
unchanged; only the check's domain changes. **A guard:** if the cadences left out exceed
``MAX_MASKED_FRACTION`` of the cadences where that column is non-zero, the check is not made and
the planet stays invalid ("the masked check covers too little").

Nothing in ``src/`` changes.
"""

from __future__ import annotations

import math

import numpy as np

CONVERGENCE_TOL = 1e-2  # I4's, unchanged
MAX_MASKED_FRACTION = 0.25  # at most a quarter of a column's support may be left out
NAMES = ("t0", "period", "duration", "ingress_fraction")
KEYS = {
    "t0": "t0_btjd",
    "period": "period_days",
    "duration": "duration_days",
    "ingress_fraction": "ingress_fraction",
}


def steps(truth: dict, n: np.ndarray) -> dict:
    """I4's frozen steps (``i4_bound.convergence``), unchanged."""
    return {
        "t0": 1e-6,
        "duration": 1e-6 * truth["duration_days"],
        "ingress_fraction": 1e-6 * truth["ingress_fraction"],
        "period": 1e-7 / max(float(np.max(np.abs(n))), 1.0),
    }


def segment(t: np.ndarray, truth: dict) -> np.ndarray:
    """Per cadence: 0 out of transit, 1 on a ramp, 2 on the flat bottom (the trapezoid's pieces,
    as ``i4_bound.shape_and_derivatives`` defines them)."""
    p, t0 = truth["period_days"], truth["t0_btjd"]
    dur, q = truth["duration_days"], truth["ingress_fraction"]
    dt = np.mod(t - t0 + 0.5 * p, p) - 0.5 * p
    w = max(q * dur, 1e-6)
    shape = np.clip((dur / 2.0 - np.abs(dt)) / w, 0.0, 1.0)
    return np.where(shape <= 0.0, 0, np.where(shape >= 1.0, 2, 1))


def straddling(t: np.ndarray, truth: dict, name: str, h: float) -> np.ndarray:
    """The cadences whose segment differs between ``-h``, ``0`` and ``+h`` for ``name``."""
    lo, hi = dict(truth), dict(truth)
    lo[KEYS[name]] -= h
    hi[KEYS[name]] += h
    s0, s_lo, s_hi = segment(t, truth), segment(t, lo), segment(t, hi)
    return (s0 != s_lo) | (s0 != s_hi)


def masked_convergence(t: np.ndarray, truth: dict, analytic: dict, n: np.ndarray, numeric) -> dict:
    """Per derivative: I4's relative L2 difference over every cadence (``full``), the same over the
    cadences that straddle no corner (``masked``), the counts, and whether the masked check is
    made (``covered``). ``numeric(name, h)`` is I4's central difference (``i4_bound._numeric``)."""
    out = {}
    for name, h in steps(truth, n).items():
        num = numeric(name, h)
        a = analytic[name]
        support = (np.abs(a) > 0) | (np.abs(num) > 0)
        cross = straddling(t, truth, name, h)
        keep = ~cross
        full = float(np.linalg.norm(num - a) / max(float(np.linalg.norm(a)), 1e-300))
        denom = max(float(np.linalg.norm(a[keep])), 1e-300)
        masked = float(np.linalg.norm((num - a)[keep]) / denom)
        left_out = int((cross & support).sum())
        n_support = int(support.sum())
        covered = n_support > 0 and left_out <= MAX_MASKED_FRACTION * n_support
        out[name] = {
            "full": full,
            "masked": masked,
            "straddling": int(cross.sum()),
            "left_out_of_support": left_out,
            "support": n_support,
            "covered": bool(covered),
        }
    return out


def passes(conv: dict) -> bool | None:
    """True if every derivative's masked difference is at most I4's tolerance; None if a masked
    check is not covered (the planet stays invalid); False otherwise."""
    if not all(c["covered"] for c in conv.values()):
        return None
    return all(math.isfinite(c["masked"]) and c["masked"] <= CONVERGENCE_TOL for c in conv.values())
