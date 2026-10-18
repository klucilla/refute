"""M4 piece 5: the capacity decisions and the FAIL rule of the holdout (revision 3, 4.3 to 4.6,
with revision 4, 1 and 2; docs/validation/v0.2.1/reopen/m4-implementation-map.md, Amendment 12
and its addendum, which declare the readings and the cases before these tests).

Interface of the tests (declared by Amendment 12): ``capacity_threshold``, ``count_n_pred``,
``predicted_error``, ``replicas_enough``, ``fail_rule``, ``calibration_measurement`` in
``holdout.py``; with the switch on, each round records ``metrics["capacity"]`` and its reason in
``metrics["reason"]``. Synthetic light curves only (``synthetic.make_lightcurve``); each integrated
case states its preconditions, and a failed precondition makes the case incompatible with the
design, never a reason to try another seed.
"""

import json
import math
from statistics import NormalDist

import numpy as np
import pytest

import refute.packs.tess.holdout as holdout
from refute.core.io import dumps_json, to_jsonable
from refute.packs.tess import synthetic
from refute.packs.tess.holdout import (
    PredictedWindow,
    calibration_measurement,
    capacity_threshold,
    count_n_pred,
    fail_rule,
    predicted_error,
    replicas_enough,
    run_holdout,
)
from refute.packs.tess.params import TessTestPlan
from refute.packs.tess.types import LightCurveData

PLANET = synthetic.PLANET
TWO_BY_TWO = (1325.0, 1353.0, 2061.0, 2089.0)  # 2018: two sectors; 2020: two sectors
THREE_BY_ONE = (1325.0, 1353.0, 1381.0, 2061.0)  # 2018: three sectors; 2020: one sector


def _plan(**corrections):
    plan = synthetic.fast_plan_dict()
    plan["gauntlet"] = {"corrections": {"enabled": True, **corrections}}
    return TessTestPlan.model_validate(plan)


def _spec(depth):
    return synthetic.SignalSpec(
        period=PLANET.period, t0=PLANET.t0, depth=depth, duration=PLANET.duration
    )


def _round(outcome, year):
    return next(r for r in outcome.rounds if r.hidden_year == year)


def _json(value):
    return dumps_json(to_jsonable(value))


# --- the pure parts -----------------------------------------------------------------------------


def test_the_threshold_is_min_snr_minus_b_plus_the_upper_quantile_of_alpha_round_times_s():
    for n_years in (2, 3):
        z = NormalDist().inv_cdf(1.0 - 0.005 / n_years)
        assert capacity_threshold(5.0, 0.4, 0.8, n_years) == pytest.approx(5.0 - 0.4 + z * 0.8)
    assert capacity_threshold(5.0, 0.0, 0.0, 2) == 5.0


def _w(t_pred, outer=0.3, kind="transit"):
    return PredictedWindow(kind, 0, t_pred, 0.1, 0.15, outer)


def test_n_pred_counts_only_complete_spans_inside_one_sector():
    spans = [(10.0, 20.0), (30.0, 40.0)]
    windows = [
        _w(15.0),  # inside
        _w(10.1),  # center inside, span not
        _w(25.0),  # between sectors
        _w(20.0 - 0.3),  # span ends exactly at the sector's end: inside (closed)
        _w(35.0, kind="control"),  # not a transit window
    ]
    assert count_n_pred(windows, spans) == 2
    assert count_n_pred([_w(25.0)], spans) == 0


def test_the_predicted_error_is_the_largest_over_the_grid_times_the_margin():
    var_rep = [1.0e-8, 4.0e-8, 2.0e-8]
    assert predicted_error(var_rep, 4) == pytest.approx(math.sqrt(4.0e-8 / 4))
    assert predicted_error(var_rep, 4, margin=1.2) == pytest.approx(1.2 * math.sqrt(4.0e-8 / 4))
    assert math.isnan(predicted_error([float("nan"), 1e-8], 4))


def test_replicas_are_enough_only_if_every_dp_reaches_r_min():
    assert replicas_enough([20, 21, 20], 20)
    assert not replicas_enough([20, 19, 25], 20)
    assert not replicas_enough([], 20)


@pytest.mark.parametrize(
    ("snr", "d_train", "e_train", "d_hidden", "e_hidden", "status", "reason"),
    [
        (5.0, 600e-6, 50e-6, 500e-6, 100e-6, "PASS", None),  # SNR = min_snr passes
        (4.8, 600e-6, 50e-6, 480e-6, 100e-6, "INCONCLUSIVE", "not_detected_not_inconsistent"),
        (0.5, 600e-6, 50e-6, 50e-6, 100e-6, "FAIL", None),
        # Z exactly 3 (binary-exact numbers: sqrt(0.75^2 + 1^2) = 1.25): not FAIL
        (1.0, 4.75, 0.75, 1.0, 1.0, "INCONCLUSIVE", None),
        # one-sided: a hidden depth far above the train one never FAILS
        (4.0, 100e-6, 10e-6, 400e-6, 100e-6, "INCONCLUSIVE", "not_detected_not_inconsistent"),
        (4.0, 600e-6, 50e-6, 400e-6, 0.0, "INCONCLUSIVE", "non_finite_statistic"),
        (float("nan"), 600e-6, 50e-6, 400e-6, 1e-4, "INCONCLUSIVE", "non_finite_statistic"),
        (4.0, 600e-6, float("inf"), 400e-6, 1e-4, "INCONCLUSIVE", "non_finite_statistic"),
    ],
)
def test_the_fail_rule(snr, d_train, e_train, d_hidden, e_hidden, status, reason):
    got_status, got_reason, z = fail_rule(snr, 5.0, d_train, e_train, d_hidden, e_hidden)
    assert got_status == status
    if reason is not None:
        assert got_reason == reason
    if status == "INCONCLUSIVE" and reason is None:  # the Z = 3 case
        assert z == 3.0
        assert got_reason == "not_detected_not_inconsistent"


def test_the_declared_algebra_example_is_inconclusive():
    # map Amendment 12, addendum: d_train 600, e_train 50, d_hidden 480, e_hidden 100 ppm
    status, reason, z = fail_rule(4.8, 5.0, 600e-6, 50e-6, 480e-6, 100e-6)
    assert (status, reason) == ("INCONCLUSIVE", "not_detected_not_inconsistent")
    assert z == pytest.approx(120 / math.sqrt(50**2 + 100**2), rel=1e-9)


# --- integrated cases ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def strong():
    lc, sectors = synthetic.make_lightcurve(_spec(0.002), sector_starts=TWO_BY_TWO, seed=3500)
    return lc, sectors, run_holdout(lc, sectors, _plan())


def test_a_strong_signal_in_a_quiet_hidden_year_is_conclusive_and_passes(strong):
    _, _, outcome = strong
    r = _round(outcome, 2020)
    cap = r.metrics["capacity"]
    assert cap["decision_1"] == "pass" and cap["decision_2"] == "pass"
    assert r.status.value == "PASS"
    assert outcome.test.coverage > 0
    assert outcome.test.coverage == sum(
        int(x.metrics.get("n_windows_with_data") or 0)
        for x in outcome.rounds
        if x.status.value != "INCONCLUSIVE"
    )


def test_the_recorded_capacity_follows_its_definitions(strong):
    _, _, outcome = strong
    cap = _round(outcome, 2020).metrics["capacity"]
    plan = _plan()
    m_beta = plan.gauntlet.corrections.m_beta
    n_pred = cap["n_pred"]
    assert len(cap["train_var_rep"]) >= 3  # precondition: a non-trivial grid
    assert cap["d_c"] == pytest.approx(cap["d_train"] - cap["e_train"], rel=1e-12)
    assert cap["e_pred_1"] == pytest.approx(
        m_beta * max(math.sqrt(v / n_pred) for v in cap["train_var_rep"]), rel=1e-12
    )
    assert cap["e_pred_2"] == pytest.approx(
        max(math.sqrt(v / n_pred) for v in cap["hidden_var_rep"]), rel=1e-12
    )
    assert cap["s_pred_1"] == pytest.approx(cap["d_c"] / cap["e_pred_1"], rel=1e-12)
    assert cap["s_pred_2"] == pytest.approx(cap["d_c"] / cap["e_pred_2"], rel=1e-12)
    assert cap["n_years"] == 2
    assert cap["threshold"] == pytest.approx(
        capacity_threshold(5.0, cap["b"], cap["s"], 2), rel=1e-12
    )
    assert (cap["b"], cap["s"]) == (holdout.CAPACITY_B, holdout.CAPACITY_S)


def test_b_and_s_enter_the_threshold(monkeypatch, strong):
    lc, sectors, _ = strong
    monkeypatch.setattr(holdout, "CAPACITY_B", -100.0)  # an impossible threshold
    outcome = run_holdout(lc, sectors, _plan())
    r = _round(outcome, 2020)
    assert r.metrics["capacity"]["threshold"] == pytest.approx(105.0)
    assert r.metrics["reason"] == "insufficient_capacity_train"
    assert r.status.value == "INCONCLUSIVE"
    assert r.access_log == []


def test_a_weak_signal_is_insufficient_capacity_train_with_an_empty_hidden_log():
    lc, sectors = synthetic.make_lightcurve(_spec(160e-6), sector_starts=THREE_BY_ONE, seed=3501)
    outcome = run_holdout(lc, sectors, _plan())
    r = _round(outcome, 2020)
    # preconditions: the train candidate passed its corrected gate and the replicas sufficed
    assert r.metrics.get("reason") == "insufficient_capacity_train", r.metrics.get("reason")
    assert r.metrics["capacity"]["decision_1"] == "insufficient_capacity_train"
    assert r.status.value == "INCONCLUSIVE"
    assert r.access_log == []
    assert r.metrics["capacity"].get("s_pred_2") is None


def _noisy_hidden(seed, depth=0.002, red_ppm=5000.0):
    """The train of a white curve joined to the hidden year (2020) of the same curve with a large
    AR(1) added (the same times, signal, seed and white noise)."""
    quiet, sectors = synthetic.make_lightcurve(_spec(depth), sector_starts=TWO_BY_TWO, seed=seed)
    noisy, _ = synthetic.make_lightcurve(
        _spec(depth), sector_starts=TWO_BY_TWO, seed=seed, red_noise_ppm=red_ppm
    )
    hidden = quiet.year == 2020
    flux = np.where(hidden, noisy.flux, quiet.flux)
    lc = LightCurveData(quiet.time, flux, quiet.flux_err, quiet.sector, quiet.year)
    return quiet, lc, sectors


def test_a_noisy_hidden_year_is_insufficient_capacity_hidden_noise():
    quiet, lc, sectors = _noisy_hidden(3502)
    train = quiet.year != 2020
    assert np.array_equal(lc.flux[train], quiet.flux[train])  # the train identical
    outcome = run_holdout(lc, sectors, _plan())
    r = _round(outcome, 2020)
    cap = r.metrics["capacity"]
    assert cap["decision_1"] == "pass"  # precondition
    assert r.metrics["reason"] == "insufficient_capacity_hidden_noise"
    assert cap["decision_2"] == "insufficient_capacity_hidden_noise"
    assert not any(e["kind"].startswith(("transit", "control")) for e in r.access_log)


def test_row_n_equal_outside_the_windows_gives_the_same_decision_2_and_hidden_noise():
    lc, sectors = synthetic.make_lightcurve(_spec(0.002), sector_starts=TWO_BY_TWO, seed=3503)
    hidden = lc.year == 2020
    phase = np.abs(
        synthetic.trapezoid(lc.time, PLANET.period, PLANET.t0, 1.0, PLANET.duration, 0.5)
    )
    inside = hidden & (phase > 0)
    other = LightCurveData(
        lc.time, np.where(inside, lc.flux - 0.003, lc.flux), lc.flux_err, lc.sector, lc.year
    )
    a = _round(run_holdout(lc, sectors, _plan()), 2020).metrics["capacity"]
    b = _round(run_holdout(other, sectors, _plan()), 2020).metrics["capacity"]
    keys = ("decision_2", "e_pred_2", "s_pred_2", "hidden_var_rep", "hidden_n_rep", "hidden_noise")
    assert _json({k: a[k] for k in keys}) == _json({k: b[k] for k in keys})


def test_no_signal_in_the_hidden_year_with_high_capacity_fails():
    lc, sectors = synthetic.make_lightcurve(
        _spec(0.002), sector_starts=TWO_BY_TWO, seed=3504, inject_years=(2018,)
    )
    r = _round(run_holdout(lc, sectors, _plan()), 2020)
    cap = r.metrics["capacity"]
    assert cap["decision_1"] == "pass" and cap["decision_2"] == "pass"  # preconditions
    assert r.status.value == "FAIL"
    assert r.metrics["z_inconsistency"] > 3


def test_a_weaker_but_consistent_hidden_signal_is_inconclusive():
    """Two passes, deterministic: the first fixes the train depth that gives S_pred,2 near 6; the
    second reduces only the hidden transits' depth to d_train - 1.5 e_pred,2."""
    seed = 3505
    lc, sectors = synthetic.make_lightcurve(_spec(0.002), sector_starts=TWO_BY_TWO, seed=seed)
    cap = _round(run_holdout(lc, sectors, _plan()), 2020).metrics["capacity"]
    e2 = cap["e_pred_2"]
    d_train = 6.0 * e2 + cap["e_train"]
    hidden_depth = d_train - 1.5 * e2
    base, _ = synthetic.make_lightcurve(None, sector_starts=TWO_BY_TWO, seed=seed)
    unit = synthetic.trapezoid(base.time, PLANET.period, PLANET.t0, 1.0, PLANET.duration, 0.15)
    depth = np.where(base.year == 2020, hidden_depth, d_train)
    built = LightCurveData(
        base.time, base.flux - depth * unit, base.flux_err, base.sector, base.year
    )
    r = _round(run_holdout(built, sectors, _plan()), 2020)
    cap2 = r.metrics["capacity"]
    assert cap2["decision_1"] == "pass" and cap2["decision_2"] == "pass"  # preconditions
    assert r.metrics["hidden_snr"] < 5.0  # precondition: not detected
    assert r.status.value == "INCONCLUSIVE"
    assert r.metrics["reason"] == "not_detected_not_inconsistent"


def test_too_few_train_replicas_is_its_own_reason(strong):
    lc, sectors, outcome = strong
    cap = _round(outcome, 2020).metrics["capacity"]
    k = min(cap["train_n_rep"])
    ok = _round(run_holdout(lc, sectors, _plan(r_min=k)), 2020)
    assert ok.metrics["capacity"]["decision_1"] != "train_replicas_below_r_min"
    short = _round(run_holdout(lc, sectors, _plan(r_min=k + 1)), 2020)
    assert short.metrics["reason"] == "train_replicas_below_r_min"
    assert short.access_log == []


def test_an_undetermined_train_correction_is_inconclusive_whatever_the_bls_snr(strong):
    lc, sectors, _ = strong
    outcome = run_holdout(lc, sectors, _plan(b_min=100_000))
    for r in outcome.rounds:
        assert r.status.value == "INCONCLUSIVE"
        assert r.metrics.get("reason") == "train_noise_undetermined"
        assert r.access_log == []


def test_the_corrected_train_snr_is_the_one_the_h4_gate_reads():
    """Strong AR(1) in the train: the BLS SNR passes 7.1, the corrected one does not."""
    lc, sectors = synthetic.make_lightcurve(
        _spec(400e-6), sector_starts=TWO_BY_TWO, seed=3506, red_noise_ppm=2000.0
    )
    r = _round(run_holdout(lc, sectors, _plan()), 2020)
    validity = r.metrics["train_validity"]
    assert r.metrics["train_bls_snr"] >= 7.1  # precondition
    assert validity["train_snr"] < 7.1
    assert "train_snr_below_gate" in validity["reasons"]
    assert r.status.value == "INCONCLUSIVE"


# --- the calibration-only measurement -----------------------------------------------------------


def test_the_calibration_measurement_leaves_run_holdout_unchanged_and_measures_despite_d1():
    lc, sectors = synthetic.make_lightcurve(_spec(160e-6), sector_starts=THREE_BY_ONE, seed=3501)
    plan = _plan(r_min=10)  # the one hidden sector gives fewer replicas than 20
    before = _json(run_holdout(lc, sectors, plan).to_dict())
    flux_before = lc.flux.copy()
    record = calibration_measurement(lc, sectors, 2020, plan)
    after = _json(run_holdout(lc, sectors, plan).to_dict())
    assert before == after
    assert np.array_equal(lc.flux, flux_before)
    assert record["calibration_only"] is True
    official = _round(run_holdout(lc, sectors, plan), 2020)
    assert official.metrics["reason"] == "insufficient_capacity_train"  # precondition
    assert record["decision_1"] == "insufficient_capacity_train"
    assert record["s_meas"] is not None and math.isfinite(record["s_meas"])
    assert record["s_pred_1"] is not None and record["s_pred_2"] is not None


def test_the_calibration_measurement_covers_a_round_stopped_at_decision_2():
    _, lc, sectors = _noisy_hidden(3502)
    record = calibration_measurement(lc, sectors, 2020, _plan())
    assert record["decision_1"] == "pass"
    assert record["decision_2"] == "insufficient_capacity_hidden_noise"
    assert record["s_meas"] is not None


def test_the_calibration_measurement_does_not_overcome_a_measurement_impediment():
    lc, sectors = synthetic.make_lightcurve(_spec(0.002), sector_starts=THREE_BY_ONE, seed=3507)
    record = calibration_measurement(lc, sectors, 2020, _plan(r_min=1000))
    assert record["s_meas"] is None
    assert record["reason"] in ("train_replicas_below_r_min", "hidden_noise_undetermined")


def test_the_calibration_record_is_plain_json():
    lc, sectors = synthetic.make_lightcurve(_spec(0.002), sector_starts=TWO_BY_TWO, seed=3500)
    record = calibration_measurement(lc, sectors, 2020, _plan())
    json.loads(_json(record))
    assert record["calibration_only"] is True
