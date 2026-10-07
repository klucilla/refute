import pytest

from refute.packs.tess.detrend import detrend
from refute.packs.tess.params import TessTestPlan
from refute.packs.tess.pipeline import period_comparison
from refute.packs.tess.search import search_period
from refute.packs.tess.synthetic import PLANET, fast_plan_dict, scenario_data


@pytest.mark.parametrize("name", ["planet", "planet_three_years", "single_year"])
def test_injected_period_recovered_within_0_1_percent(scenario_results, name):
    candidate = scenario_results[name].gauntlet.candidate
    assert candidate is not None
    assert abs(candidate.period - PLANET.period) / PLANET.period < 1e-3
    assert abs(candidate.duration - PLANET.duration) < 0.5 * PLANET.duration


def test_multi_year_baseline_gives_a_much_more_precise_period(scenario_results):
    single = scenario_results["single_year"].gauntlet
    multi = scenario_results["planet_three_years"].gauntlet
    assert abs(multi.candidate.period - PLANET.period) / PLANET.period < 5e-6
    assert multi.ephemeris.period_err < 0.1 * single.ephemeris.period_err
    assert abs(multi.ephemeris.period - PLANET.period) < 5 * multi.ephemeris.period_err


def test_search_is_deterministic():
    plan = TessTestPlan.model_validate(fast_plan_dict())
    data = scenario_data("planet")
    flat = detrend(data.lc, plan.detrend)
    a = search_period(flat, plan.search).candidate
    b = search_period(flat, plan.search).candidate
    assert a == b


def test_equal_eclipse_binary_is_found_at_half_its_orbital_period(scenario_results):
    found = scenario_results["eb_equal"].gauntlet.candidate.period
    comparison = period_comparison(published=3.2, found=found, tolerance=0.001)
    assert comparison["alias"] == "P/2"
    assert comparison["within_tolerance"] is False


@pytest.mark.parametrize(
    ("published", "found", "alias", "within"),
    [
        (3.7, 3.7000001, "P", True),
        (3.7, 7.4000002, "2P", False),
        (3.7, 1.85, "P/2", False),
        (3.7, 2.9, None, False),
        (None, 3.7, None, None),
    ],
)
def test_period_comparison_and_aliases(published, found, alias, within):
    comparison = period_comparison(published, found, 0.001)
    assert comparison["alias"] == alias
    assert comparison["within_tolerance"] is within
