from refute.core.verdict import Severity, TestStatus
from refute.packs.tess.gauntlet import check_snr
from refute.packs.tess.params import SnrParams
from refute.packs.tess.types import Candidate


def _test(results, name):
    return next(t for t in results if t.name == name)


def test_injected_planet_passes_the_gate(scenario_results):
    snr = _test(scenario_results["planet"].tests, "snr")
    assert snr.status is TestStatus.PASS
    assert snr.metrics["snr"] > 20


def test_pure_noise_fails_the_gate_and_is_inconclusive(scenario_results):
    result = scenario_results["noise"]
    snr = _test(result.tests, "snr")
    assert snr.status is TestStatus.FAIL
    assert snr.severity is Severity.GATE
    assert result.verdict == "INCONCLUSIVE"


def test_threshold_is_applied_exactly():
    params = SnrParams(min_snr=7.1)
    base = dict(period=3.0, t0=0.0, duration=0.1, depth=1e-3, log_likelihood=1.0, sde=5.0)
    above = Candidate(depth_err=1e-3 / 7.1, snr=7.1, n_transits=5, **base)
    below = Candidate(depth_err=1e-3 / 7.0, snr=7.09, n_transits=5, **base)
    assert check_snr(above, params).status is TestStatus.PASS
    assert check_snr(below, params).status is TestStatus.FAIL
    assert check_snr(None, params).status is TestStatus.FAIL
