import numpy as np

from refute.core.verdict import TestStatus
from refute.packs.tess.events import EventDepths, group_mean
from refute.packs.tess.gauntlet import check_odd_even
from refute.packs.tess.params import OddEvenParams


def _test(results, name):
    return next(t for t in results if t.name == name)


def test_planet_passes(scenario_results):
    assert _test(scenario_results["planet"].tests, "odd_even").status is TestStatus.PASS


def test_eclipsing_binary_with_unequal_eclipses_is_refuted(scenario_results):
    result = scenario_results["eb_odd_even"]
    test = _test(result.tests, "odd_even")
    assert test.status is TestStatus.FAIL
    assert test.metrics["difference_sigma"] > 3.0
    assert result.verdict == "REFUTED"


def _events(depths, errors):
    n = len(depths)
    return EventDepths(
        np.arange(n),
        np.arange(n, dtype=float),
        np.asarray(depths, float),
        np.asarray(errors, float),
        np.full(n, 50),
    )


def test_inconclusive_with_too_few_transits():
    result = check_odd_even(_events([1e-3, 1e-3, 1e-3], [1e-4] * 3), OddEvenParams())
    assert result.status is TestStatus.INCONCLUSIVE


def test_scatter_inflates_errors_so_red_noise_is_not_a_detection():
    # even epochs: mean 1.00e-3; odd epochs: mean 1.05e-3; both with large real scatter
    depths = [1.0e-3, 1.25e-3, 1.3e-3, 0.8e-3, 0.7e-3, 1.2e-3, 1.0e-3, 0.95e-3]
    events = _events(depths, [1e-5] * len(depths))
    group = group_mean(events.depths, events.errors)
    assert group.error > group.white_error
    white_only_sigma = 0.05e-3 / (2**0.5 * 1e-5 / 2)
    assert white_only_sigma > 3.0  # white-noise errors alone would call this a detection
    result = check_odd_even(events, OddEvenParams())
    assert result.status is TestStatus.PASS
    assert result.metrics["difference_sigma"] < 1.0
