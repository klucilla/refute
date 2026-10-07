import math

import pytest

from refute.core.verdict import Severity, TestStatus
from refute.packs.tess.gauntlet import check_plausibility, max_transit_duration
from refute.packs.tess.params import PlausibilityParams
from refute.packs.tess.synthetic import make_star
from refute.packs.tess.types import Candidate


def _test(results, name):
    return next(t for t in results if t.name == name)


def _candidate(depth=0.01, duration_hours=2.5, period=3.7):
    return Candidate(
        period=period,
        t0=0.0,
        duration=duration_hours / 24,
        depth=depth,
        depth_err=1e-4,
        snr=100.0,
        log_likelihood=1.0,
        sde=10.0,
        n_transits=10,
    )


def test_planet_passes(scenario_results):
    test = _test(scenario_results["planet"].tests, "plausibility")
    assert test.status is TestStatus.PASS
    assert test.inputs["tic_version"] == "synthetic"


def test_equal_depth_binary_is_refuted_by_its_radius(scenario_results):
    result = scenario_results["eb_equal"]
    test = _test(result.tests, "plausibility")
    assert test.status is TestStatus.FAIL
    assert test.severity is Severity.FATAL
    assert test.metrics["companion_radius_rjup"] > 2.5
    assert result.verdict == "REFUTED"


def test_missing_radius_is_inconclusive_never_pass(scenario_results):
    result = scenario_results["no_radius"]
    assert _test(result.tests, "plausibility").status is TestStatus.INCONCLUSIVE
    assert result.verdict == "INCONCLUSIVE"


@pytest.mark.parametrize(
    "star",
    [
        None,
        make_star(radius=None),
        make_star(radius=1.0, radius_err=None),
        make_star(radius=1.0, radius_err=0.31),
    ],
)
def test_unreliable_radius_is_inconclusive(star):
    result = check_plausibility(_candidate(depth=0.3), star, PlausibilityParams())
    assert result.status is TestStatus.INCONCLUSIVE


def test_duration_too_long_for_the_orbit_is_a_warning():
    result = check_plausibility(_candidate(duration_hours=8.0), make_star(), PlausibilityParams())
    assert result.status is TestStatus.FAIL
    assert result.severity is Severity.WARNING
    assert result.metrics["duration_ratio"] > 1.5


def test_max_duration_matches_textbook_value():
    # Sun-like star, P = 365.25 d, Earth-size planet: about 13 hours.
    hours = max_transit_duration(365.25, 1.0, 1.0, math.sqrt(8.4e-5)) * 24
    assert 12.5 < hours < 13.5


def test_mass_from_logg_when_tic_mass_is_missing():
    star = make_star(mass=None, logg=4.438)
    result = check_plausibility(_candidate(), star, PlausibilityParams())
    assert result.status is TestStatus.PASS
    assert result.metrics["stellar_mass_source"] == "TIC logg and radius"
    assert abs(result.metrics["stellar_mass_msun"] - 1.0) < 0.05
