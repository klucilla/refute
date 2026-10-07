import numpy as np

from refute.core.verdict import Severity, TestStatus
from refute.packs.tess.events import EventDepths
from refute.packs.tess.gauntlet import check_secondary_eclipse
from refute.packs.tess.params import SecondaryParams


def _test(results, name):
    return next(t for t in results if t.name == name)


def test_planet_passes(scenario_results):
    assert _test(scenario_results["planet"].tests, "secondary_eclipse").status is TestStatus.PASS


def test_deep_secondary_eclipse_is_fatal(scenario_results):
    result = scenario_results["eb_secondary"]
    test = _test(result.tests, "secondary_eclipse")
    assert test.status is TestStatus.FAIL
    assert test.severity is Severity.FATAL
    assert test.metrics["depth_ratio"] > 0.1
    assert result.verdict == "REFUTED"


def _events(depth, n=10, err=1e-5):
    return EventDepths(
        np.arange(n), np.arange(n, dtype=float), np.full(n, depth), np.full(n, err), np.full(n, 50)
    )


def test_shallow_significant_secondary_is_only_a_warning():
    # e.g. the occultation of a hot Jupiter: significant but < 10% of the transit depth
    result = check_secondary_eclipse(_events(1e-2), _events(3e-4), SecondaryParams())
    assert result.status is TestStatus.FAIL
    assert result.severity is Severity.WARNING


def test_no_phase_half_coverage_is_inconclusive():
    empty = EventDepths(*(np.zeros(0) for _ in range(5)))
    result = check_secondary_eclipse(_events(1e-2), empty, SecondaryParams())
    assert result.status is TestStatus.INCONCLUSIVE
