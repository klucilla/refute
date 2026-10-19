"""The ``R_min`` study (docs/validation/v0.2.1/reopen/m4-implementation-map.md, Amendment 19; its
implementation, Amendment 26): the evaluator's side of the scenarios.

The study's light curves are the population harness's (``population_v2.build_case``, the frozen
version 2, loaded through version 3, which captures the M4 configuration). This module holds the
pure functions of the scenarios, computed from a case's **recorded final parameters** only (no
random generator is run again):

- ``deficit_and_trend``: the generator's transit deficit ``D(t)`` (``1 - signal_model``) and its
  multiplicative trend (``1`` for ``pure_noise``), as ``build_case`` builds them;
- ``alter_last_year``: the disappearing (``s = 0``) and weakened (``s = 0.3``) scenarios,
  ``flux + (1 - s) D(t) trend(t)`` on the cadences of the last observing year, the noise untouched;
- ``noiseless_model``: the scenario's complete model without noise (the signal times the trend,
  plus the variability, with the alteration where it applies), the twin's input.

The evaluator keeps the parameters and the scenario; the analysis receives only the light curve
and the metadata.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import population_v3 as v3  # noqa: E402

pv2 = v3.pv2

SCENARIOS = {"constant": 1.0, "disappearing": 0.0, "weakened": 0.3}
STUDY_MECHANISMS = ("two_years", "three_years", "few_train", "variability_some_years")


def _check(case: dict) -> None:
    if case["class"] != "planet" or case["mechanism"] not in STUDY_MECHANISMS:
        raise ValueError(f"{case['id']}: not a planet of the study's mechanisms")


def deficit_and_trend(case: dict, p: dict, time: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """The generator's ``D(t)`` and trend at ``time`` (``build_case``, the model before the
    noise)."""
    from refute.packs.tess import synthetic

    _check(case)
    t = np.asarray(time, dtype=float)
    deficit = 1.0 - synthetic.signal_model(t, pv2._signal_spec(synthetic, case, p, p["depth"]))
    if case["mechanism"] == "pure_noise":
        trend = np.ones_like(t)
    else:
        trend = 1.0 + pv2.TREND_AMPLITUDE * np.sin(2 * np.pi * t / pv2.TREND_PERIOD_DAYS)
    return deficit, trend


def _last_year_mask(year: np.ndarray) -> np.ndarray:
    year = np.asarray(year)
    return year == year.max()


def alter_last_year(
    case: dict, p: dict, time: np.ndarray, year: np.ndarray, flux: np.ndarray, s: float
) -> np.ndarray:
    """``flux + (1 - s) D(t) trend(t)`` on the last observing year's cadences; the other cadences
    and the noise unchanged. ``s = 1`` returns the flux as it is."""
    flux = np.asarray(flux, dtype=float)
    if s == 1.0:
        return flux.copy()
    deficit, trend = deficit_and_trend(case, p, time)
    last = _last_year_mask(year)
    return np.where(last, flux + (1.0 - s) * deficit * trend, flux)


def noiseless_model(
    case: dict, p: dict, time: np.ndarray, year: np.ndarray, s: float = 1.0
) -> np.ndarray:
    """The scenario's model without noise: ``(signal + (1 - s_y) D) trend + variability``, with
    ``s_y = s`` in the last observing year and 1 elsewhere (``build_case``'s model, altered as the
    scenario is; with ``s = 1`` the very products of ``build_case``)."""
    from refute.packs.tess import synthetic

    t = np.asarray(time, dtype=float)
    year = np.asarray(year)
    deficit, trend = deficit_and_trend(case, p, t)
    signal = synthetic.signal_model(t, pv2._signal_spec(synthetic, case, p, p["depth"]))
    factor = np.where(_last_year_mask(year), s, 1.0)
    model = (signal + (1.0 - factor) * deficit) * trend
    if "var_amplitude" in p:
        present = year != p.get("var_absent_year")
        model = model + np.where(
            present,
            p["var_amplitude"] * np.sin(2 * np.pi * (t - p["var_phase"]) / p["var_period"]),
            0.0,
        )
    return model
