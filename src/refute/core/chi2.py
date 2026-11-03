"""Chi-square tail probabilities without new dependencies (v0.5; scipy is not a dependency of
Refute, and adding one is a dependency change).

- :func:`chi2_sf`: P(X > x) for a central chi-square with ``dof`` degrees of freedom, the
  regularized upper incomplete gamma function Q(dof/2, x/2) (a series below a + 1, a continued
  fraction above, as in Press et al., Numerical Recipes, section 6.2);
- :func:`chi2_isf`: the x with ``chi2_sf(x, dof) = p``, by bisection;
- :func:`ncx2_sf`: P(X > x) for a non-central chi-square with non-centrality ``lam``, as the
  Poisson mixture of central tails, sum_j Pois(j; lam/2) Q(dof/2 + j, x/2).
"""

from __future__ import annotations

import math

_EPS = 1e-15
_ITMAX = 10_000


def _gser(a: float, x: float) -> float:
    """The regularized lower incomplete gamma P(a, x) by its series (x < a + 1)."""
    ap, total, delta = a, 1.0 / a, 1.0 / a
    for _ in range(_ITMAX):
        ap += 1.0
        delta *= x / ap
        total += delta
        if abs(delta) < abs(total) * _EPS:
            break
    return total * math.exp(-x + a * math.log(x) - math.lgamma(a))


def _gcf(a: float, x: float) -> float:
    """The regularized upper incomplete gamma Q(a, x) by its continued fraction (x >= a + 1)."""
    tiny = 1e-300
    b = x + 1.0 - a
    c = 1.0 / tiny
    d = 1.0 / b
    h = d
    for i in range(1, _ITMAX):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        if abs(d) < tiny:
            d = tiny
        c = b + an / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        step = d * c
        h *= step
        if abs(step - 1.0) < _EPS:
            break
    return math.exp(-x + a * math.log(x) - math.lgamma(a)) * h


def gamma_q(a: float, x: float) -> float:
    """Q(a, x) = Gamma(a, x) / Gamma(a), for a > 0 and x >= 0."""
    if not (a > 0) or not (x >= 0) or not math.isfinite(a) or math.isnan(x):
        raise ValueError(f"gamma_q needs a > 0 and x >= 0: a={a}, x={x}")
    if x == 0:
        return 1.0
    if math.isinf(x):
        return 0.0
    if x < a + 1.0:
        return max(0.0, 1.0 - _gser(a, x))
    return min(1.0, _gcf(a, x))


def chi2_sf(x: float, dof: int) -> float:
    """P(X > x), X a central chi-square with ``dof`` degrees of freedom."""
    if dof < 1:
        raise ValueError("dof must be at least 1")
    if x <= 0:
        return 1.0
    return gamma_q(dof / 2.0, x / 2.0)


def chi2_isf(p: float, dof: int) -> float:
    """The x with ``chi2_sf(x, dof) = p`` (0 < p < 1), by bisection to a relative 1e-12."""
    if not 0.0 < p < 1.0:
        raise ValueError("p must be in (0, 1)")
    lo, hi = 0.0, max(1.0, float(dof))
    while chi2_sf(hi, dof) > p:
        hi *= 2.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if chi2_sf(mid, dof) > p:
            lo = mid
        else:
            hi = mid
        if hi - lo <= 1e-12 * hi:
            break
    return 0.5 * (lo + hi)


def ncx2_sf(x: float, dof: int, lam: float) -> float:
    """P(X > x), X a non-central chi-square (``dof`` degrees of freedom, non-centrality
    ``lam`` >= 0), summing the Poisson mixture until the remaining Poisson mass is below 1e-14."""
    if lam < 0 or not math.isfinite(lam):
        raise ValueError("lam must be finite and non-negative")
    if lam == 0:
        return chi2_sf(x, dof)
    if x <= 0:
        return 1.0
    half = lam / 2.0
    # start at the Poisson mode and sum outward, so a large lam does not underflow
    mode = int(math.floor(half))
    log_w_mode = -half + mode * math.log(half) - math.lgamma(mode + 1)
    total = 0.0
    mass = 0.0
    j, log_w = mode, log_w_mode
    while j >= 0:
        w = math.exp(log_w)
        total += w * gamma_q(dof / 2.0 + j, x / 2.0)
        mass += w
        if w < 1e-16 and j < mode:
            break
        log_w -= math.log(half) - math.log(j) if j > 0 else 0.0
        j -= 1
    j, log_w = mode + 1, log_w_mode + math.log(half) - math.log(mode + 1)
    while mass < 1.0 - 1e-14:
        w = math.exp(log_w)
        total += w * gamma_q(dof / 2.0 + j, x / 2.0)
        mass += w
        if w < 1e-16 and j > mode + 10:
            break
        j += 1
        log_w += math.log(half) - math.log(j)
    return min(1.0, max(0.0, total))
