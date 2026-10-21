"""The synthetic cases of the instrumentation's acceptance record
(docs/validation/v0.2.1/reopen/stage-1/instrumentation-acceptance.md, matrix (a)): one case per
stopping point of a calibration record, each reached by a plan setting or, where no setting reaches
it, by a declared replacement of one engine function. Shared by the tests and by the generator of
their snapshot (``make_instrumentation_snapshot.py``, run once with the code before the change).
Synthetic light curves only; no network."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any

import numpy as np

import refute.packs.tess.holdout as holdout
from refute.packs.tess import synthetic
from refute.packs.tess.params import TessTestPlan
from refute.packs.tess.types import LightCurveData

PLANET = synthetic.PLANET
TWO_BY_TWO = (1325.0, 1353.0, 2061.0, 2089.0)  # 2018: two sectors; 2020: two sectors
THREE_BY_ONE = (1325.0, 1353.0, 1381.0, 1500.0)  # 2018: three sectors; 2019: one sector
ONE_YEAR = (1325.0, 1353.0)  # 2018 only


def plan(corrections: dict | None = None, holdout_by_year: dict | None = None) -> TessTestPlan:
    d = synthetic.fast_plan_dict()
    d["gauntlet"] = {
        "corrections": {"version": 2, "enabled": True, "r_min": 8, **(corrections or {})}
    }
    if holdout_by_year:
        d["gauntlet"]["holdout_by_year"] = dict(holdout_by_year)
    return TessTestPlan.model_validate(d)


def identity(p: TessTestPlan) -> dict:
    from refute.core.canonical import canonical_sha256

    block = canonical_sha256(p.gauntlet.corrections.model_dump(mode="json"))
    return {"path": "probe.json", "sha256": "0" * 64, "block_sha256": block}


def spec(depth: float) -> synthetic.SignalSpec:
    return synthetic.SignalSpec(
        period=PLANET.period, t0=PLANET.t0, depth=depth, duration=PLANET.duration
    )


def noisy_hidden(seed: int, depth: float = 0.002, red_ppm: float = 5000.0):
    """A white train joined to a hidden year (2020) with a large AR(1) (as in
    tests/test_holdout_capacity.py)."""
    quiet, sectors = synthetic.make_lightcurve(spec(depth), sector_starts=TWO_BY_TWO, seed=seed)
    noisy, _ = synthetic.make_lightcurve(
        spec(depth), sector_starts=TWO_BY_TWO, seed=seed, red_noise_ppm=red_ppm
    )
    flux = np.where(quiet.year == 2020, noisy.flux, quiet.flux)
    return LightCurveData(quiet.time, flux, quiet.flux_err, quiet.sector, quiet.year), sectors


@dataclass
class Case:
    name: str
    row: str  # the row of matrix (a)
    lc: LightCurveData
    sectors: list
    hidden_year: int
    plan: TessTestPlan
    replace: dict[str, Any] = field(default_factory=dict)  # holdout attribute -> replacement


@contextmanager
def replaced(case: Case):
    """The case's declared replacements of engine functions, restored afterwards."""
    saved = {k: getattr(holdout, k) for k in case.replace}
    try:
        for k, v in case.replace.items():
            setattr(holdout, k, v)
        yield
    finally:
        for k, v in saved.items():
            setattr(holdout, k, v)


def _no_candidate(*args, **kwargs):
    return SimpleNamespace(candidate=None)


def _no_window(*args, **kwargs):
    return 0


def _hidden_noise_stop_plan(lc, sectors, year) -> TessTestPlan:
    """An r_min between the train's and the hidden year's replica counts, so that the train counts
    pass and the hidden replicas do not (holdout.replica_stats: hidden_noise_undetermined)."""
    probe = holdout.calibration_measurement(lc, sectors, year, plan(), identity=identity(plan()))
    train_min = min(probe["train_n_rep"])
    hidden_min = min(probe["hidden_n_rep"])
    r = hidden_min + 1
    if not r <= train_min:
        raise AssertionError(f"precondition: hidden {hidden_min} + 1 <= train {train_min}")
    return plan({"r_min": r})


def _too_few_windows(lc: LightCurveData) -> LightCurveData:
    """The hidden year (2020) with every predicted transit but the first removed (as in
    tests/test_holdout_capacity.py): the measurement stops with too_few_windows."""
    import math

    t = lc.time[lc.year == 2020]
    n0 = math.ceil((t.min() - PLANET.t0) / PLANET.period)
    n1 = math.floor((t.max() - PLANET.t0) / PLANET.period)
    centers = [PLANET.t0 + n * PLANET.period for n in range(n0, n1 + 1)]
    drop = np.zeros(len(lc), bool)
    for c in centers[1:]:
        drop |= (lc.year == 2020) & (np.abs(lc.time - c) <= 0.06)
    return lc.select(~drop)


def cases() -> list[Case]:
    strong, s2 = synthetic.make_lightcurve(spec(0.002), sector_starts=TWO_BY_TWO, seed=3500)
    weak, s31 = synthetic.make_lightcurve(spec(160e-6), sector_starts=THREE_BY_ONE, seed=3501)
    strong31, s31b = synthetic.make_lightcurve(spec(0.002), sector_starts=THREE_BY_ONE, seed=3507)
    one, s1 = synthetic.make_lightcurve(spec(0.002), sector_starts=ONE_YEAR, seed=3511)
    noisy, sn = noisy_hidden(3502)
    red, sr = synthetic.make_lightcurve(
        spec(0.002), sector_starts=THREE_BY_ONE, seed=3512, red_noise_ppm=600.0
    )
    return [
        Case("no_train_data", "no train data", one, s1, 2018, plan()),
        Case(
            "no_candidate",
            "no train candidate",
            strong,
            s2,
            2020,
            plan(),
            {"search_period": _no_candidate},
        ),
        Case(
            "rejected_before_times",
            "train candidate rejected before its transit times",
            strong,
            s2,
            2020,
            plan(holdout_by_year={"max_train_duration_period_ratio": 1e-6}),
        ),
        Case(
            "train_noise_undetermined",
            "train_noise_undetermined",
            strong,
            s2,
            2020,
            plan({"b_min": 100_000}),
        ),
        Case(
            "too_few_times",
            "too few train transit times",
            strong,
            s2,
            2020,
            plan(holdout_by_year={"min_train_transits": 1000}),
        ),
        Case(
            "timing_stop",
            "timing stop",
            strong,
            s2,
            2020,
            plan(holdout_by_year={"max_timing_sigma_durations": 1e-9}),
        ),
        Case(
            "validity_after_windows",
            "train validity rejected after the windows are predicted",
            strong,
            s2,
            2020,
            plan(holdout_by_year={"max_hidden_window_fraction": 1e-9}),
        ),
        Case(
            "no_predicted_window",
            "no_predicted_window",
            strong,
            s2,
            2020,
            plan(),
            {"count_n_pred": _no_window},
        ),
        Case(
            "train_replicas_below",
            "train replicas below r_min",
            strong,
            s2,
            2020,
            plan({"r_min": 100_000}),
        ),
        Case("decision_1_failed", "decision 1 failed", weak, s31, 2019, plan({"r_min": 10})),
        Case(
            "hidden_noise_stop",
            "hidden noise stop",
            strong31,
            s31b,
            2019,
            _hidden_noise_stop_plan(strong31, s31b, 2019),
        ),
        Case("decision_2_failed", "decision 2 failed", noisy, sn, 2020, plan()),
        Case("measurement_stop", "measurement stop", _too_few_windows(strong), s2, 2020, plan()),
        Case("measured_white", "measured", strong, s2, 2020, plan()),
        Case("measured_ar1", "measured", red, sr, 2019, plan()),
    ]
