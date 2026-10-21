"""The synthetic controls of specification B (docs/validation/v0.2.1/reopen/stage-1/
spec-b-target-pass.md, B4; the acceptance record x1b-acceptance.md): C1 to C5 and C7, each in white
and in AR(1) noise, with two and with three observing years. A stop of one round that no plan
setting reaches for that round alone is made by a declared replacement of one engine function,
restored afterwards (as in tests/instrumentation_cases.py). Synthetic light curves only; no
network."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

import refute.packs.tess.holdout as holdout
from refute.packs.tess import synthetic
from refute.packs.tess.params import TessTestPlan
from refute.packs.tess.types import LightCurveData

PLANET = synthetic.PLANET
LAYOUTS = {
    2: (1325.0, 1353.0, 2061.0, 2089.0),  # 2018 and 2020, two sectors each
    3: (1325.0, 1353.0, 1700.0, 1728.0, 2061.0, 2089.0),  # 2018, 2019 and 2020
}
NOISES = {"white": 0.0, "ar1": 600.0}  # red_noise_ppm (synthetic.CORRELATED_PROFILE's level)
SEEDS = {("white", 2): 4100, ("white", 3): 4101, ("ar1", 2): 4102, ("ar1", 3): 4103}
# The disappearing planet in AR(1) with three years: with seed 4103 its rounds hiding 2018 and 2019
# FAIL too, which breaks C3's precondition (the other rounds PASS); seeds were tried in order from
# 4200 on the engine before the code of X1b, and 4207 is the first of the twelve tried whose rounds
# hiding 2018 and 2019 PASS and whose round hiding 2020 FAILs (x1b-results.md).
DISAPPEARING_SEEDS = {("ar1", 3): 4207}


def plan(corrections: dict | None = None, holdout_by_year: dict | None = None) -> TessTestPlan:
    d = synthetic.fast_plan_dict()
    d["gauntlet"] = {
        "corrections": {"version": 2, "enabled": True, "r_min": 8, **(corrections or {})}
    }
    if holdout_by_year:
        d["gauntlet"]["holdout_by_year"] = dict(holdout_by_year)
    return TessTestPlan.model_validate(d)


def legacy_plan() -> TessTestPlan:
    """The corrections switch off: the engine's legacy path (not the experimental M4 path)."""
    return TessTestPlan.model_validate(synthetic.fast_plan_dict())


def curve(noise: str, n_years: int, *, signal_years: tuple[int, ...] | None = None, signal=True):
    """The control's light curve: ``signal_years`` limits the planet to those years (the
    disappearing planet: every year but the last); ``signal=False`` gives no transit at all."""
    seed = SEEDS[(noise, n_years)]
    if signal_years is not None:
        seed = DISAPPEARING_SEEDS.get((noise, n_years), seed)
    lc, sectors = synthetic.make_lightcurve(
        PLANET if signal else None,
        sector_starts=LAYOUTS[n_years],
        seed=seed,
        red_noise_ppm=NOISES[noise],
        inject_years=signal_years,
    )
    return lc, sectors


# --- the declared replacements (each stops one named year's round, and only that round) --------

_CURRENT = {"year": None}


def _stop_decision_2(year: int) -> dict[str, Any]:
    """Decision 2 fails in ``year``'s round: ``predicted_error`` called for decision 2 (two
    arguments, no margin) returns infinity there, so ``S_pred,2`` is 0 and the round stops with
    ``insufficient_capacity_hidden_noise`` before its measurement. Every other call is the
    engine's."""
    original_round = holdout._round_corrected
    original_error = holdout.predicted_error

    def round_corrected(raw, sectors, hidden_year, *args, **kwargs):
        _CURRENT["year"] = hidden_year
        try:
            return original_round(raw, sectors, hidden_year, *args, **kwargs)
        finally:
            _CURRENT["year"] = None

    def predicted_error(var_rep, n_pred, *rest, **kwargs):
        if not rest and not kwargs and _CURRENT["year"] == year:
            return float("inf")
        return original_error(var_rep, n_pred, *rest, **kwargs)

    return {"_round_corrected": round_corrected, "predicted_error": predicted_error}


def _no_window_in(year_start: float, year_end: float) -> dict[str, Any]:
    """No predicted transit window in the round hiding the year whose sectors start in
    ``[year_start, year_end)``: ``count_n_pred`` returns 0 there (the round stops with
    ``no_predicted_window``); every other call is the engine's."""
    original = holdout.count_n_pred

    def count_n_pred(windows, spans):
        if spans and all(year_start <= a < year_end for a, _ in spans):
            return 0
        return original(windows, spans)

    return {"count_n_pred": count_n_pred}


YEAR_SPANS = {2018: (1300.0, 1500.0), 2019: (1600.0, 1900.0), 2020: (2000.0, 2200.0)}


@dataclass
class Control:
    name: str  # C1 ... C7b
    noise: str
    n_years: int
    lc: LightCurveData
    sectors: list
    plan: TessTestPlan
    expected_b: str  # the target's status under specification B
    expected_undecided: tuple[int, ...] = ()  # the necessary years left undecided (INCONCLUSIVE)
    replace: dict[str, Any] = field(default_factory=dict)

    @property
    def key(self) -> str:
        return f"{self.name}-{self.noise}-{self.n_years}y"


@contextmanager
def replaced(control: Control):
    saved = {k: getattr(holdout, k) for k in control.replace}
    try:
        for k, v in control.replace.items():
            setattr(holdout, k, v)
        yield
    finally:
        for k, v in saved.items():
            setattr(holdout, k, v)


def controls() -> list[Control]:
    out = []
    for noise in NOISES:
        for n in LAYOUTS:
            years = (2018, 2020) if n == 2 else (2018, 2019, 2020)
            last, first = years[-1], years[0]
            constant = curve(noise, n)
            disappearing = curve(noise, n, signal_years=years[:-1])
            empty = curve(noise, n, signal=False)
            p = plan()
            out += [
                Control("C1", noise, n, *constant, p, "PASS"),
                Control("C2", noise, n, *disappearing, p, "FAIL"),
                Control(
                    "C3",
                    noise,
                    n,
                    *disappearing,
                    p,
                    "INCONCLUSIVE",
                    # in two years the other round trains on the year without the signal and is
                    # undecided too (corrected after the first run against the code; x1b-results.md)
                    (first, last) if n == 2 else (last,),
                    _stop_decision_2(last),
                ),
                Control(
                    "C4", noise, n, *constant, p, "INCONCLUSIVE", (last,), _stop_decision_2(last)
                ),
                Control("C5", noise, n, *empty, p, "INCONCLUSIVE"),
                Control(
                    "C5r",
                    noise,
                    n,
                    *constant,
                    plan(holdout_by_year={"max_train_duration_period_ratio": 1e-6}),
                    "INCONCLUSIVE",
                ),
                Control(
                    "C7a",
                    noise,
                    n,
                    *constant,
                    p,
                    "INCONCLUSIVE",
                    (last,),
                    _no_window_in(*YEAR_SPANS[last]),
                ),
                Control(
                    "C7b",
                    noise,
                    n,
                    *disappearing,
                    p,
                    "FAIL",
                    (),
                    _no_window_in(*YEAR_SPANS[first]),
                ),
            ]
    return out
