"""Leak tests: nothing from the global search may reach the hidden-year processing."""

import inspect

import numpy as np
import pytest

from refute.core.canonical import canonical_bytes
from refute.core.io import to_jsonable
from refute.packs.tess.holdout import HiddenYear, PredictedWindow, run_holdout
from refute.packs.tess.params import TessTestPlan
from refute.packs.tess.pipeline import analyze_data
from refute.packs.tess.search import SearchResult
from refute.packs.tess.synthetic import PLANET, fast_plan_dict, make_lightcurve, scenario_data
from refute.packs.tess.types import Candidate


def _holdout_bytes(analysis) -> bytes:
    return canonical_bytes(to_jsonable(analysis.holdout.to_dict()))


def _wrong_search(_lc, _params):
    wrong = Candidate(
        period=2.1,
        t0=1326.0,
        duration=0.08,
        depth=0.001,
        depth_err=1e-4,
        snr=10.0,
        log_likelihood=1.0,
        sde=5.0,
        n_transits=10,
    )
    return SearchResult(wrong, {"note": "deliberately wrong"})


def _skipped_search(_lc, _params):
    return SearchResult(None, {"note": "skipped"})


def test_holdout_is_identical_whatever_the_global_search_returns(scenario_results):
    plan = TessTestPlan.model_validate(fast_plan_dict())
    data = scenario_data("planet")
    true = _holdout_bytes(scenario_results["planet"])  # computed in another process
    wrong_analysis = analyze_data(data, plan, search_fn=_wrong_search)
    skipped_analysis = analyze_data(data, plan, search_fn=_skipped_search)
    assert wrong_analysis.gauntlet.candidate.period != pytest.approx(PLANET.period, rel=1e-2)
    assert skipped_analysis.gauntlet.candidate is None
    assert _holdout_bytes(wrong_analysis) == true
    assert _holdout_bytes(skipped_analysis) == true


def test_hidden_year_detrending_depends_only_on_the_registered_windows():
    """The hidden year's detrending mask is built from the registered windows only.

    A probe window is read with the same geometry in two HiddenYear objects. With
    windows from a correct train ephemeris, the whole transit is masked and keeps its
    depth. With windows from a wrong ephemeris, most of the transit is unmasked, the
    trend is pulled into it and the measured depth shrinks: the mask path is live and
    is driven only by the windows given to the constructor.
    """
    lc, _ = make_lightcurve(PLANET, seed=2, trend_amplitude=0.002)
    hidden = lc.select(lc.year == 2020)
    plan = TessTestPlan()
    epoch = 200
    t_true = PLANET.t0 + epoch * PLANET.period

    def windows(period: float, probe_inner: float) -> list[PredictedWindow]:
        others = [
            PredictedWindow("transit", n, t_true + (n - epoch) * period, 0.06, 0.08, 0.2)
            for n in range(epoch - 3, epoch + 8)
            if n != epoch
        ]
        return [*others, PredictedWindow("transit", epoch, t_true, 0.03, probe_inner, 0.2)]

    year_true = HiddenYear(hidden, windows(PLANET.period, 0.08), plan)
    year_wrong = HiddenYear(hidden, windows(2.9, 0.01), plan)
    _, f_true = year_true.window(t_true, 0.03)
    _, f_wrong = year_wrong.window(t_true, 0.03)
    assert f_true.size == f_wrong.size > 0
    assert not np.allclose(f_true, f_wrong)
    assert (1.0 - np.mean(f_true)) > (1.0 - np.mean(f_wrong))


def test_run_holdout_rejects_a_candidate_argument():
    params = list(inspect.signature(run_holdout).parameters)
    assert params == ["raw", "sectors", "plan"]
    data = scenario_data("planet")
    plan = TessTestPlan.model_validate(fast_plan_dict())
    candidate_result = _wrong_search(None, None).candidate
    with pytest.raises(TypeError):
        run_holdout(data.lc, data.sectors, plan, candidate_result)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        run_holdout(candidate_result, data.sectors, plan)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        run_holdout(data.lc, [candidate_result], plan)  # type: ignore[list-item]


def test_access_log_stays_inside_predicted_windows_and_bands(scenario_results):
    for round_ in scenario_results["planet"].holdout.rounds:
        assert round_.access_log
        assert round_.train_ephemeris is not None
        for entry in round_.access_log:
            centre = 0.5 * (entry["t_lo"] + entry["t_hi"])
            half = 0.5 * (entry["t_hi"] - entry["t_lo"])
            assert entry["kind"] in {
                "transit-window",
                "transit-baseline",
                "control-window",
                "control-baseline",
            }
            # every access is centred on a predicted time and bounded in width
            assert half < 1.0
            assert any(abs(centre - w["t_pred"]) < 1e-9 for w in round_.windows) or entry[
                "kind"
            ].startswith("control")
