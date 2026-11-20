"""v0.5.5: version 2 of the C1 generator, for new draws only (#218; the charter's decision (b),
``docs/plans/v0.5.5-charter.md``). ``method_status: not_validated``.

C1 (``refute.packs.tess.calib05.c1``) computes every transit's durations from a star of exactly
1.0 M_sun and 1.0 R_sun (``c1.a_over_rstar``), while each target carries a catalog star of
1.0 ± 0.05 in radius and in mass (``synthetic.make_star``). The true star therefore sits at the
catalog's centre in every curve. Version 2 draws the true star within the catalog's declared
uncertainty instead:

- ``R_true ~ N(1.0, 0.05)`` and ``M_true ~ N(1.0, 0.05)``, the catalog's declared Gaussian
  errors, with no artificial truncation; only the physical domain is kept (a draw with R or M
  not above 0.05 is redrawn from the same stream, about 10^-80 of the mass). **Independent R and
  M errors are a modelling convention** (the catalog declares two errors and no correlation);
- drawn from their own stream, ``numpy.random.default_rng([seed, 5505])``, so every other draw
  of C1 (the family's parameters, the noise, the trend) is unchanged for the same seed;
- the durations use ``a / R_* = c1.a_over_rstar(P) * M_true^(1/3) / R_true`` (Kepler's third law
  for that star). Everything C1 derives from the durations changes with them (the depth that
  ``solve_depth`` fixes for the target SNR, the flat time, the ingress fraction); nothing else
  does. The catalog star the data carries is unchanged (1.0 ± 0.05), as is the noise.

**The effective radius** ``R / M^(1/3)`` is not exactly Gaussian under this law;
``effective_sigma()`` is a first-order approximation of its spread.

**Serial use only.** Nothing in ``src/`` changes: ``c1.a_over_rstar`` is replaced only for the
duration of one ``generate`` call, and restored after it (also on an error). That mutates
process-global module state, so it requires exclusive, serial use within each worker process (the
driver runs one shard at a time per process). Old records and draws do not change; version 1
stays ``c1.generate``.
"""

from __future__ import annotations

import contextlib
import math
from typing import Any

import numpy as np

VERSION = "c1-v2 (v0.5.5)"
STAR_SIGMA = 0.05  # the catalog's declared 5 % in radius and in mass (synthetic.make_star)
PHYSICAL_MIN = 0.05  # the physical domain only: a radius or mass not above this is redrawn
STAR_STREAM = 5505


def true_star(seed: int) -> tuple[float, float]:
    """The true (radius, mass) in solar units for ``seed``, from its own stream."""
    rng = np.random.default_rng([seed, STAR_STREAM])
    while True:
        r, m = (float(x) for x in rng.normal(1.0, STAR_SIGMA, 2))
        if r > PHYSICAL_MIN and m > PHYSICAL_MIN:
            return r, m


def effective_radius(radius: float, mass: float) -> float:
    """``R / M^(1/3)``: the transit durations depend on the star through this combination only."""
    return radius / mass ** (1.0 / 3.0)


def effective_sigma(sigma_r: float = STAR_SIGMA, sigma_m: float = STAR_SIGMA) -> float:
    """The spread of the effective radius under the catalog's errors, **to first order**:
    ``sqrt(sigma_R^2 + sigma_M^2 / 9)`` (about 0.0527 for 5 % and 5 %); not the exact law."""
    return math.sqrt(sigma_r**2 + sigma_m**2 / 9.0)


@contextlib.contextmanager
def _star(radius: float, mass: float):
    """Process-global and serial: see the module's docstring."""
    from refute.packs.tess.calib05 import c1

    original = c1.a_over_rstar
    factor = mass ** (1.0 / 3.0) / radius

    def a_over_rstar(period_days: float) -> float:
        return original(period_days) * factor

    c1.a_over_rstar = a_over_rstar
    try:
        yield
    finally:
        c1.a_over_rstar = original


def generate(family: str, seed: int) -> tuple[Any, dict]:
    """``c1.generate(family, seed)`` with the true star drawn (version 2); the truth records it.
    Raises ``c1.GenerationFailedError`` as C1 does."""
    from refute.packs.tess.calib05 import c1

    radius, mass = true_star(seed)
    with _star(radius, mass):
        data, truth = c1.generate(family, seed)
    truth["true_star"] = {
        "radius_rsun": radius,
        "mass_msun": mass,
        "effective_radius": effective_radius(radius, mass),
        "generator": VERSION,
    }
    return data, truth
