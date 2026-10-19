"""The noiseless twin of the ``R_min`` study's coverage reference (map Amendment 19; its
implementation, Amendment 26, 4), written before the code.

Interface (declared here): ``calibration_measurement(..., twin_model=None)``, ``twin_model`` an
array with one value per cadence of ``raw`` (only the hidden year's values are read), given by the
evaluator only; the record's ``d_twin`` is the twin's depth at the ``dP`` chosen (``None`` without a
twin or without a measurement). ``HiddenYear.twin(model_hidden)`` returns an object with the same
registered windows whose flux is ``model_hidden / trend`` on the cadences the noisy detrending kept
(``model_hidden`` has one value per cadence of the raw hidden year). Synthetic light curves only.
"""

import math

import numpy as np
import pytest

import refute.packs.tess.holdout as holdout
from refute.core.io import dumps_json, to_jsonable
from refute.packs.tess import synthetic
from refute.packs.tess.holdout import HiddenYear, calibration_measurement, run_holdout
from refute.packs.tess.params import TessTestPlan
from refute.packs.tess.types import LightCurveData

PLANET = synthetic.PLANET
TWO_BY_TWO = (1325.0, 1353.0, 2061.0, 2089.0)
DEPTH = 0.002


def _plan(**corrections):
    plan = synthetic.fast_plan_dict()
    plan["gauntlet"] = {"corrections": {"version": 2, "enabled": True, "r_min": 8, **corrections}}
    return TessTestPlan.model_validate(plan)


def _spec(depth):
    return synthetic.SignalSpec(
        period=PLANET.period, t0=PLANET.t0, depth=depth, duration=PLANET.duration
    )


def _ident(plan):
    from refute.core.canonical import canonical_sha256

    block = canonical_sha256(plan.gauntlet.corrections.model_dump(mode="json"))
    return {"path": "probe.json", "sha256": "0" * 64, "block_sha256": block}


def _json(value):
    return dumps_json(to_jsonable(value))


@pytest.fixture(scope="module")
def curve():
    lc, sectors = synthetic.make_lightcurve(_spec(DEPTH), sector_starts=TWO_BY_TWO, seed=3500)
    return lc, sectors


def _measure(curve, twin=None):
    lc, sectors = curve
    plan = _plan()
    return calibration_measurement(lc, sectors, 2020, plan, identity=_ident(plan), twin_model=twin)


def test_without_a_twin_the_record_has_no_twin_depth(curve):
    rec = _measure(curve)
    assert rec["s_meas"] is not None  # precondition: the round is measured
    assert rec["d_twin"] is None


def test_a_twin_equal_to_the_raw_flux_gives_the_noisy_depth_exactly(curve):
    lc, _ = curve
    rec = _measure(curve, twin=lc.flux.copy())
    assert rec["s_meas"] is not None  # precondition
    # the same cadences, dP, baseline form and frequencies: the very same windows' depths
    assert rec["d_twin"] == rec["d_hidden"]


def test_the_noiseless_twin_measures_near_the_injected_depth(curve):
    lc, _ = curve
    model = synthetic.signal_model(lc.time, _spec(DEPTH))
    rec = _measure(curve, twin=model)
    assert rec["d_twin"] is not None and math.isfinite(rec["d_twin"])
    assert rec["d_twin"] == pytest.approx(DEPTH, rel=0.15)


def test_the_twin_changes_nothing_of_the_noisy_analysis(curve):
    lc, sectors = curve
    plan = _plan()
    before = _json(run_holdout(lc, sectors, plan).to_dict())
    model = synthetic.signal_model(lc.time, _spec(DEPTH))
    other = synthetic.signal_model(lc.time, _spec(0.5 * DEPTH))
    records = [_measure(curve), _measure(curve, twin=model), _measure(curve, twin=other)]
    after = _json(run_holdout(lc, sectors, plan).to_dict())
    assert before == after
    stripped = [_json({k: v for k, v in r.items() if k != "d_twin"}) for r in records]
    assert stripped[0] == stripped[1] == stripped[2]
    assert records[1]["d_twin"] != records[2]["d_twin"]


def test_the_twin_reads_the_cadences_the_noisy_detrending_kept(curve):
    lc, sectors = curve
    plan = _plan()
    hidden = lc.select(lc.year == 2020)
    t_mid = PLANET.t0 + math.ceil((hidden.time.min() + 3.0 - PLANET.t0) / PLANET.period) * (
        PLANET.period
    )
    window = holdout.PredictedWindow(
        kind="transit",
        epoch=0,
        t_pred=t_mid,
        half_width=0.2,
        baseline_inner=0.2,
        baseline_outer=0.6,
    )
    # an upward outlier in the window's baseline band: the noisy detrending clips it
    k = int(np.argmin(np.abs(hidden.time - (t_mid + 0.4))))
    flux = hidden.flux.copy()
    flux[k] += 0.05
    spiked = LightCurveData(hidden.time, flux, hidden.flux_err, hidden.sector, hidden.year)
    noisy = HiddenYear(spiked, [window], plan)
    t_noisy, _ = noisy.local_baseline(window.t_pred, window.half_width)
    assert not np.any(t_noisy == hidden.time[k])  # precondition: the outlier was clipped
    twin = noisy.twin(np.ones(len(spiked)))
    for read in ("window", "local_baseline"):
        t_a, _ = getattr(noisy, read)(window.t_pred, window.half_width)
        t_b, f_b = getattr(twin, read)(window.t_pred, window.half_width)
        assert np.array_equal(t_a, t_b), read
        assert np.all(np.isfinite(f_b))


def test_a_twin_of_the_wrong_length_is_refused(curve):
    lc, _ = curve
    with pytest.raises(ValueError):
        _measure(curve, twin=lc.flux[:-1])
