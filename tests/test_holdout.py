import numpy as np
import pytest

from refute.core.verdict import TestStatus
from refute.packs.tess.holdout import HiddenYear, HoldoutAccessError, PredictedWindow
from refute.packs.tess.params import TessTestPlan
from refute.packs.tess.synthetic import PLANET, make_lightcurve


def _holdout(result):
    return result.holdout


def test_planet_passes_with_each_year_hidden(scenario_results):
    for name, n_years in (("planet", 2), ("planet_three_years", 3)):
        holdout = _holdout(scenario_results[name])
        assert holdout.test.status is TestStatus.PASS
        assert len(holdout.rounds) == n_years
        assert all(r.status is TestStatus.PASS for r in holdout.rounds)
        for r in holdout.rounds:
            assert r.metrics["n_windows_with_data"] >= 2
            assert r.metrics["hidden_snr"] >= 5.0


def test_signal_absent_in_hidden_year_fails(scenario_results):
    result = scenario_results["vanishing"]
    holdout = _holdout(result)
    assert holdout.test.status is TestStatus.FAIL
    statuses = {r.hidden_year: r.status for r in holdout.rounds}
    assert statuses[2020] is TestStatus.FAIL
    assert result.verdict == "REFUTED"


def test_pure_noise_does_not_pass(scenario_results):
    # v0.1 gave FAIL here. From v0.2 (issue #2) a round whose train-only timing is too
    # uncertain is INCONCLUSIVE: on noise the train "transits" have a reduced chi-square
    # far above 1, so the rounds are INCONCLUSIVE. Either way, noise never passes.
    holdout = _holdout(scenario_results["noise"])
    assert holdout.test.status is not TestStatus.PASS


def test_single_year_is_inconclusive(scenario_results):
    holdout = _holdout(scenario_results["single_year"])
    assert holdout.test.status is TestStatus.INCONCLUSIVE
    assert holdout.rounds == []


def test_hidden_year_refuses_access_outside_registered_windows():
    lc, _ = make_lightcurve(PLANET)
    hidden = lc.select(lc.year == 2020)
    t_pred = PLANET.t0 + 200 * PLANET.period
    window = PredictedWindow("transit", 200, t_pred, 0.06, 0.08, 0.2)
    year = HiddenYear(hidden, [window], TessTestPlan())
    t, f = year.window(t_pred, 0.06)
    assert t.size > 0 and np.all(np.abs(t - t_pred) <= 0.06)
    tb, _ = year.local_baseline(t_pred, 0.06)
    assert np.all((np.abs(tb - t_pred) > 0.08) & (np.abs(tb - t_pred) <= 0.2))
    with pytest.raises(HoldoutAccessError):
        year.window(t_pred + 1.0, 0.06)
    with pytest.raises(HoldoutAccessError):
        year.window(t_pred, 0.5)
    with pytest.raises(HoldoutAccessError):
        year.local_baseline(t_pred + 0.3, 0.06)
    assert [entry["kind"] for entry in year.access_log] == ["transit-window", "transit-baseline"]
