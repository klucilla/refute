"""v0.4 WP4 (issue #176): the duration uncertainty, cases 4.1 to 4.4 of
docs/plans/v0.4-acceptance.md, against the values fixed in docs/plans/v0.4-duration-method.md.
Synthetic data only."""

from __future__ import annotations

import math

import numpy as np
import pytest

from refute.packs.tess.discover.injection import wilson_interval
from refute.packs.tess.duration import METHOD, METHOD_ACCEPTED, estimate_duration
from refute.packs.tess.exporter import _fields
from refute.packs.tess.synthetic import trapezoid

CADENCE = 2.0 / 1440.0
PERIOD, T0 = 3.7, 1326.3
TRUE_T = 2.5 / 24.0
T_BLS = 3.0 / 24.0  # 2.5 h rounded to the default BLS grid, the tie to the longer (spec)
NOISE = 1e-3
SEEDS = range(200)
NOMINAL = 0.68


def _times() -> np.ndarray:
    return np.concatenate([np.arange(1325.0, 1352.0, CADENCE), np.arange(1353.0, 1380.0, CADENCE)])


TIME = _times()


def _depth_for(snr: float) -> float:
    shape = trapezoid(TIME, PERIOD, T0, 1.0, TRUE_T, 0.15)
    return snr * NOISE / math.sqrt(float(np.sum(shape**2)))


def _curve(snr: float, seed: int, duration: float = TRUE_T, time: np.ndarray = TIME):
    rng = np.random.default_rng(seed)
    depth = _depth_for(snr)
    flux = 1.0 - trapezoid(time, PERIOD, T0, depth, duration, 0.15)
    flux = flux + rng.normal(0.0, NOISE, time.size)
    return flux, np.full(time.size, NOISE), depth


def _fit(snr: float, seed: int, **kw):
    flux, sigma, depth = _curve(snr, seed, **kw)
    time = kw.get("time", TIME)
    return estimate_duration(time, flux, sigma, PERIOD, T0, T_BLS, depth, CADENCE)


FAILED_ON_2026_10_29 = pytest.mark.xfail(
    strict=True,
    reason="trapezoid-least-squares-1 failed case 4.1 on 2026-10-29 (coverage 0.54 and 0.55 at "
    "SNR 20 and 40; docs/validation/v0.4/wp4-duration-acceptance.md); the result is kept",
)


@pytest.mark.parametrize(
    "snr",
    [
        10,
        pytest.param(20, marks=FAILED_ON_2026_10_29),
        pytest.param(40, marks=FAILED_ON_2026_10_29),
    ],
)
def test_4_1_the_interval_covers_the_true_duration_at_the_nominal_rate(snr):
    fits = [_fit(snr, seed) for seed in SEEDS]
    estimable = [f for f in fits if f["estimable"]]
    if snr in (20, 40):
        assert len(estimable) >= 150, f"only {len(estimable)} of 200 estimable at SNR {snr}"
    assert estimable, f"no estimable trial at SNR {snr}"
    covered = sum(
        1 for f in estimable if abs(f["duration_days"] - TRUE_T) <= f["duration_err_days"]
    )
    n = len(estimable)
    low, high = wilson_interval(round(NOMINAL * n), n)
    assert low <= covered / n <= high, (snr, covered, n, low, high)


def test_4_2_a_transit_of_three_cadences_is_not_estimable():
    short = 3 * CADENCE
    flux, sigma, depth = _curve(40, 1, duration=short)
    out = estimate_duration(TIME, flux, sigma, PERIOD, T0, short, depth, CADENCE)
    assert out["estimable"] is False and out["reason"]
    assert out["duration_err_days"] is None


def test_4_2_a_single_transit_is_not_estimable():
    window = TIME[(TIME > T0 - 1.0) & (TIME < T0 + 1.0)]
    flux, sigma, depth = _curve(40, 2, time=window)
    out = estimate_duration(window, flux, sigma, PERIOD, T0, T_BLS, depth, CADENCE)
    assert out["estimable"] is False
    assert "transits" in out["reason"] or "cadences" in out["reason"]


def test_4_3_a_signal_that_passes_the_gate_can_still_be_not_estimable():
    # SNR 40 passes any gate; with one cadence of ingress unresolved by construction (a box),
    # the rule on the ingress or the error decides, not the gate.
    flux, sigma, depth = _curve(40, 3, duration=2 * CADENCE)
    out = estimate_duration(TIME, flux, sigma, PERIOD, T0, 2 * CADENCE, depth, CADENCE)
    assert out["estimable"] is False and out["reason"]


def _record(estimate):
    return {
        "target_key": "TIC-1",
        "tic_id": 1,
        "candidate": {"period": PERIOD, "duration_hours": 3.0, "depth_ppm": 500, "snr": 20},
        "tests": [],
        "verdict": "INCONCLUSIVE",
        "duration_estimate": estimate,
    }


def test_4_4_a_method_that_failed_its_acceptance_is_never_exported():
    assert METHOD_ACCEPTED is False
    fields = _fields(_record(_fit(40, 4)))
    assert fields["duration_method"] == METHOD
    assert fields["duration_err_hours"] is None
    assert fields["duration_note"].startswith("not reported: ")
    assert "did not pass its acceptance" in fields["duration_note"]
    assert fields["submitted"] is False and "NOTHING HAS BEEN SUBMITTED" in fields["disclaimer"]


def test_4_4_an_accepted_method_writes_the_value_or_a_justified_absence(monkeypatch):
    monkeypatch.setattr("refute.packs.tess.duration.METHOD_ACCEPTED", True)
    fields = _fields(_record(_fit(40, 4)))
    assert fields["duration_err_hours"] > 0
    estimate = {"method": METHOD, "estimable": False, "reason": "fewer than 2 transits with data"}
    fields = _fields(_record(estimate))
    assert fields["duration_err_hours"] is None
    assert fields["duration_note"] == "not estimable: fewer than 2 transits with data"


def test_an_old_record_keeps_the_old_sheet():
    fields = _fields({"tests": [], "candidate": {"duration_hours": 2.0}})
    assert "duration_method" not in fields and fields["duration_err_hours"] is None
