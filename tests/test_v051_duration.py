"""v0.5.1: the EB route's diagnostic `duration_excess` (docs/plans/v0.5.1-acceptance.md, section
"The eclipsing-binary route", as decided under plan amendment 9). Synthetic data only; the
acceptance rows D.1 to D.5 are measured by their own runs, not here."""

from __future__ import annotations

import math
from dataclasses import replace

import pytest

from refute.core.verdict import Severity, TestStatus
from refute.packs.tess import battery_v51 as v51
from refute.packs.tess import synthetic as syn
from refute.packs.tess.params import TessTestPlan
from refute.packs.tess.pipeline import expected_tests
from refute.packs.tess.types import Candidate

CADENCE = 2.0 / 1440.0


def _case(duration_hours: float, seed: int = 4):
    spec = syn.SignalSpec(period=3.7, t0=1326.3, depth=0.004, duration=duration_hours / 24.0)
    lc, _ = syn.make_lightcurve(spec, noise_ppm=400.0, seed=seed)
    candidate = Candidate(
        period=3.7,
        t0=1326.3,
        duration=duration_hours / 24.0,
        depth=0.004,
        depth_err=0.00008,
        snr=50.0,
        log_likelihood=0.0,
        sde=20.0,
        n_transits=10,
    )
    return lc, candidate


def _gp():
    return TessTestPlan.model_validate(syn.discovery_v051_plan_dict()).gauntlet


def test_t_max_is_the_circular_orbit_bound():
    # a Sun-like star at 3.7 d: a / R* about 9.9, so T_max about (P / pi) asin(1.06 / 9.9)
    value = v51.t_max(3.7, 0.06, 1.0, 1.0)
    from refute.packs.tess.calib05.c1 import a_over_rstar

    expected = 3.7 / math.pi * math.asin(1.06 / a_over_rstar(3.7))
    assert value == pytest.approx(expected)
    assert v51.t_max(7.4, 0.06, 1.0, 1.0) > value  # longer at twice the period
    assert v51.t_max(3.7, 0.06, 2.0, 1.0) > value  # a larger star, a longer transit
    assert v51.t_max(0.2, 0.5, 5.0, 1.0) == pytest.approx(0.2 / 2.0)  # (1 + k) >= a / R*


@pytest.mark.parametrize(
    "star",
    [
        replace(syn.make_star(), mass_err_msun=None),
        syn.make_star(radius=None),
        None,
    ],
)
def test_d4_a_missing_tic_input_is_missing_input(star):
    lc, candidate = _case(2.5)
    result = v51.check_duration_excess(lc, candidate, star, _gp(), CADENCE, 1)
    assert result.status is TestStatus.INCONCLUSIVE
    assert result.metrics["inconclusive_class"] == "missing_input"
    assert result.severity is Severity.WARNING


def test_a_planet_inside_the_bound_is_measured_with_its_placements():
    lc, candidate = _case(2.5)
    result = v51.check_duration_excess(lc, candidate, syn.make_star(), _gp(), CADENCE, 1)
    placements = result.metrics["placements"]
    assert placements["valid"] + sum(placements["rejected"].values()) == 20
    assert result.status is TestStatus.PASS, result.message
    assert result.coverage == placements["valid"] >= 10
    assert result.metrics["sigma_T_hours"] > 0 and result.metrics["sigma_Tmax_hours"] > 0
    assert result.sensitivity["main"]["unit"] == "h"
    assert result.severity is Severity.WARNING  # never fatal


def test_a_duration_far_above_the_bound_warns():
    # 8 h at 3.7 d around a Sun-like star: far above T_max (about 3 h)
    lc, candidate = _case(8.0)
    result = v51.check_duration_excess(lc, candidate, syn.make_star(), _gp(), CADENCE, 1)
    assert result.status is TestStatus.FAIL, result.message
    assert result.severity is Severity.WARNING
    assert "circular-orbit maximum" in result.message and "verdict" in result.message


def test_too_few_valid_placements_is_not_enough_data(monkeypatch):
    lc, candidate = _case(2.5)
    calls = {"n": 0}
    real = v51._fit_shape_status

    def fail_placements(time, flux, cand):
        calls["n"] += 1
        params, ok, bound = real(time, flux, cand)
        return params, ok if calls["n"] == 1 else False, bound  # only the candidate's own fit

    monkeypatch.setattr(v51, "_fit_shape_status", fail_placements)
    result = v51.check_duration_excess(lc, candidate, syn.make_star(), _gp(), CADENCE, 1)
    assert result.status is TestStatus.INCONCLUSIVE
    assert result.metrics["inconclusive_class"] == "not_enough_data"
    assert result.metrics["placements"]["rejected"]["fit failed"] == 20


def test_fit_shape_keeps_its_procedure():
    lc, candidate = _case(2.5)
    assert (
        v51._fit_shape(lc.time, lc.flux, candidate)
        == v51._fit_shape_status(lc.time, lc.flux, candidate)[0]
    )


def test_the_version_3_battery_expects_the_diagnostic():
    assert "duration_excess" in expected_tests(True, True, True)
    assert "duration_excess" not in expected_tests(True, True)
    plan = TessTestPlan.model_validate(syn.discovery_v051_plan_dict())
    assert plan.discovery.roles["duration_excess"] == "diagnostic"
    v05 = TessTestPlan.model_validate(syn.discovery_v05_plan_dict(catalogs=True))
    assert "duration_excess" not in v05.discovery.roles


def test_a_version_2_claim_cannot_name_the_diagnostic():
    d = syn.discovery_v05_plan_dict(catalogs=True)
    d["discovery"]["diagnostic"] = [*d["discovery"]["diagnostic"], "duration_excess"]
    with pytest.raises(ValueError, match="unknown tests"):
        TessTestPlan.model_validate(d)


def test_the_diagnostic_runs_in_a_version_3_analysis_outside_the_verdict():
    from refute.packs.tess.pipeline import analyze_data

    data = replace(syn.scenario_data("planet"))
    plan = TessTestPlan.model_validate(syn.discovery_v051_plan_dict())
    analysis = analyze_data(data, plan)
    names = {t.name: t for t in analysis.tests}
    assert "duration_excess" in names
    assert analysis.roles.verdict is not None
    assert "duration_excess" not in [t.name for t in analysis.roles.decisive]
    assert "duration_excess" in analysis.roles.diagnostics
