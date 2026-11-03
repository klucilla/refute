"""The sensitivity rule of the engine (v0.5 WP1, #185; docs/plans/v0.5-acceptance.md, cases 1.1
to 1.5 and 1.9, and the engine sabotage checks)."""

from __future__ import annotations

import math

import numpy as np
import pytest

from refute.core.sensitivity import (
    REQUIRED_PROBABILITY,
    RULE,
    Z_POWER,
    category_block,
    enforce_sensitivity,
    gaussian_probability,
    registry_problems,
    rule_block,
    seed_for,
    simulated_probability,
)
from refute.core.verdict import Severity, TestResult, TestStatus, aggregate

REGISTRY = {
    "odd_even": {"main": RULE},
    "systematics": {"dumps": "fraction", "sap": RULE, "background": RULE},
    "eb_catalog": {"main": "catalog-lookup"},
}


def _result(name, status=TestStatus.PASS, severity=Severity.FATAL, sensitivity=None):
    return TestResult(
        name, status, severity, "msg", coverage=5, coverage_unit="events", sensitivity=sensitivity
    )


def _rule(probability):
    return rule_block("odd/even difference", 1000.0, "ppm", "gaussian-1", probability)


def _one(result):
    (out,) = enforce_sensitivity([result], REGISTRY)
    return out


# --- case 1.1 -------------------------------------------------------------------------------


def test_a_pass_with_a_detectable_rule_stands():
    out = _one(_result("odd_even", sensitivity={"main": _rule(0.99)}))
    assert out.status is TestStatus.PASS


def test_a_fatal_pass_that_could_not_detect_is_inconclusive():
    out = _one(_result("odd_even", sensitivity={"main": _rule(0.40)}))
    assert out.status is TestStatus.INCONCLUSIVE
    assert out.message.startswith("PASS refused: insufficient sensitivity: odd/even difference")
    assert "0.400 < 0.95" in out.message


def test_a_warning_pass_without_a_block_is_inconclusive():
    out = _one(_result("odd_even", severity=Severity.WARNING))
    assert out.status is TestStatus.INCONCLUSIVE
    assert "no sensitivity declared" in out.message


def test_a_fail_is_never_changed():
    failed = _result("odd_even", status=TestStatus.FAIL, sensitivity={"main": _rule(0.1)})
    assert _one(failed) == failed
    assert _one(_result("odd_even", status=TestStatus.FAIL)).status is TestStatus.FAIL


def test_an_unregistered_test_cannot_pass():
    out = _one(_result("new_test", sensitivity={"main": _rule(0.99)}))
    assert out.status is TestStatus.INCONCLUSIVE
    assert "no sensitivity rule or category registered" in out.message


# --- case 1.2: malformed blocks -------------------------------------------------------------


def _bad_blocks():
    good = _rule(0.99)
    missing = {k: v for k, v in good.items() if k != "probability"}
    return {
        "missing key": missing,
        "detectable as text": {**good, "detectable": "yes"},
        "NaN probability": {**good, "probability": math.nan},
        "probability above 1": {**good, "probability": 1.5},
        "detectable disagrees": {**good, "probability": 0.5},
        "boolean alternative": {**good, "alternative": True},
        "not a mapping": ["detectable", True],
        "category on a statistical test": category_block("catalog-lookup", "a lookup"),
        # the probes of Codex's end-of-round review (2026-11-03)
        "requirement lowered by the result": {
            **good,
            "probability": 0.10,
            "required_probability": 0.05,
            "detectable": True,
        },
        "NaN effect": {**good, "effect": math.nan},
        "unit None": {**good, "unit": None},
        "empty rule_id": {**good, "rule_id": " "},
    }


@pytest.mark.parametrize("kind", list(_bad_blocks()))
def test_a_malformed_block_never_passes(kind):
    out = _one(_result("odd_even", sensitivity={"main": _bad_blocks()[kind]}))
    assert out.status is TestStatus.INCONCLUSIVE
    assert "invalid sensitivity block" in out.message


def test_a_category_other_than_the_registered_one_is_refused():
    wrong = _one(_result("eb_catalog", sensitivity={"main": category_block("fraction", "x")}))
    assert wrong.status is TestStatus.INCONCLUSIVE
    right = _one(
        _result("eb_catalog", sensitivity={"main": category_block("catalog-lookup", "rows")})
    )
    assert right.status is TestStatus.PASS


def test_an_unknown_category_cannot_be_built():
    with pytest.raises(ValueError):
        category_block("anything", "x")


def test_a_category_with_an_empty_reason_is_refused():
    out = _one(_result("eb_catalog", sensitivity={"main": category_block("catalog-lookup", "")}))
    assert out.status is TestStatus.INCONCLUSIVE


@pytest.mark.parametrize("value", [["main"], "main", 1, {"main"}])
def test_a_sensitivity_that_is_not_a_mapping_is_inconclusive_not_a_crash(value):
    out = _one(_result("odd_even", sensitivity=value))
    assert out.status is TestStatus.INCONCLUSIVE
    assert "not a mapping of sub-checks" in out.message


@pytest.mark.parametrize("entry", [{}, None, ["main"]])
def test_an_empty_or_malformed_registry_entry_never_lets_a_pass_through(entry):
    for severity in (Severity.FATAL, Severity.WARNING):
        (out,) = enforce_sensitivity([_result("x", severity=severity)], {"x": entry})
        assert out.status is TestStatus.INCONCLUSIVE
    assert registry_problems(["x"], {"x": entry}, exempt=[]) == [
        "x: no sensitivity rule or category registered"
    ]


# --- case 1.3: composite tests --------------------------------------------------------------


def _systematics(sap_probability):
    return {
        "dumps": category_block("fraction", "dump fraction"),
        "sap": _rule(sap_probability),
        "background": _rule(0.99),
    }


def test_a_composite_pass_needs_every_sub_check():
    ok = _one(_result("systematics", severity=Severity.WARNING, sensitivity=_systematics(0.99)))
    assert ok.status is TestStatus.PASS
    weak = _one(_result("systematics", severity=Severity.WARNING, sensitivity=_systematics(0.5)))
    assert weak.status is TestStatus.INCONCLUSIVE
    partial = _systematics(0.99)
    del partial["background"]
    missing = _one(_result("systematics", severity=Severity.WARNING, sensitivity=partial))
    assert missing.status is TestStatus.INCONCLUSIVE
    assert "for background" in missing.message


# --- case 1.4: the gate ---------------------------------------------------------------------


def test_the_gate_is_exempt():
    gate = TestResult("snr", TestStatus.PASS, Severity.GATE, "SNR 9", coverage=4)
    assert _one(gate) == gate


# --- case 1.5: the registry at load time ----------------------------------------------------


def test_a_decisive_test_without_a_registry_entry_is_a_load_problem():
    problems = registry_problems(["snr", "odd_even", "single_event"], REGISTRY, exempt=["snr"])
    assert problems == ["single_event: no sensitivity rule or category registered"]
    bad = {"odd_even": {"main": "guess"}}
    assert registry_problems(["odd_even"], bad, exempt=[]) == [
        "odd_even.main: unknown kind 'guess'"
    ]


# --- case 1.7, at the engine: the verdict ---------------------------------------------------


def test_an_underpowered_warning_makes_the_verdict_inconclusive():
    gate = TestResult("snr", TestStatus.PASS, Severity.GATE, "SNR 12", coverage=6)
    fatal = _result("odd_even", sensitivity={"main": _rule(0.99)})
    warning = _result("systematics", severity=Severity.WARNING, sensitivity=_systematics(0.3))
    tests = enforce_sensitivity([gate, fatal, warning], REGISTRY)
    verdict, reason = aggregate(tests)
    assert verdict.value == "INCONCLUSIVE"
    assert "systematics" in reason
    # without the rule (the sabotage) the same results SURVIVE
    assert aggregate([gate, fatal, warning])[0].value == "SURVIVED"


# --- the computations and case 1.9 ----------------------------------------------------------


def test_the_closed_form_is_the_gaussian_probability():
    threshold, sigma = 3.0, 100.0
    at_rule = gaussian_probability((threshold + Z_POWER) * sigma, sigma, threshold)
    assert at_rule == pytest.approx(REQUIRED_PROBABILITY, abs=1e-4)
    assert gaussian_probability(0.0, sigma, threshold) < 0.01
    assert gaussian_probability(1.0, 0.0, threshold) == 0.0
    assert gaussian_probability(math.nan, 1.0, threshold) == 0.0


def test_the_boundary_between_the_threshold_and_the_rule_is_inconclusive():
    # case 1.9: threshold < alternative / sigma < threshold + z_power, and an observation that
    # does not reject: the PASS is refused; a rule without z_power would accept it
    threshold, sigma = 3.0, 100.0
    alternative = (threshold + 0.8) * sigma
    probability = gaussian_probability(alternative, sigma, threshold)
    assert probability < REQUIRED_PROBABILITY
    assert alternative / sigma >= threshold  # the sabotaged rule ("detectable") says PASS
    out = _one(_result("odd_even", sensitivity={"main": _rule(probability)}))
    assert out.status is TestStatus.INCONCLUSIVE


def test_the_simulation_is_deterministic_and_matches_the_closed_form():
    sigma, threshold = 1.0, 3.0
    alternative = (threshold + Z_POWER) * sigma
    seed = seed_for("odd_even", 1.5, 2459000.1)

    def draw(rng, n):
        return alternative + sigma * rng.standard_normal(n)

    def reject(x):
        return x / sigma >= threshold

    first = simulated_probability(draw, reject, seed)
    assert first == simulated_probability(draw, reject, seed)
    assert first == pytest.approx(REQUIRED_PROBABILITY, abs=0.015)


def test_the_simulation_applies_the_full_rejection_region():
    # a compound rule (significance and ratio): an alternative exactly at the ratio boundary
    # is rejected about half the time, whatever the significance (Codex review, correction A)
    def draw(rng, n):
        ratio = 1.2 + 0.01 * rng.standard_normal(n)
        sigma = np.full(n, 50.0)
        return ratio, sigma

    def reject(stats):
        ratio, sigma = stats
        return (sigma >= 3.0) & (ratio >= 1.2)

    probability = simulated_probability(draw, reject, seed=7)
    assert 0.4 < probability < 0.6
    with pytest.raises(ValueError):
        simulated_probability(draw, lambda stats: np.ones(3, dtype=bool), seed=7)


@pytest.mark.parametrize(
    "reject",
    [
        lambda stats: np.full(10, np.nan),  # NaN is truthy: never a detection
        lambda stats: np.ones(10),  # numbers, not booleans
        lambda stats: [True] * 10,  # not a NumPy array
    ],
)
def test_a_rejection_that_is_not_a_boolean_array_is_refused(reject):
    with pytest.raises(ValueError, match="boolean"):
        simulated_probability(lambda rng, n: rng.standard_normal(n), reject, seed=1, draws=10)


@pytest.mark.parametrize("draws", [0, -5, 2.5, True])
def test_the_draw_count_must_be_a_positive_integer(draws):
    with pytest.raises(ValueError, match="positive integer"):
        simulated_probability(lambda rng, n: rng.standard_normal(n), lambda s: s > 0, 1, draws)


@pytest.mark.parametrize(
    "args", [(1.0, 1.0, -math.inf), (1.0, 1.0, math.nan), (math.inf, 1.0, 3.0), (1.0, -1.0, 3.0)]
)
def test_a_bad_gaussian_input_is_never_detectable(args):
    assert gaussian_probability(*args) == 0.0


# --- the result format ----------------------------------------------------------------------


def test_a_result_without_sensitivity_keeps_its_historical_bytes():
    data = _result("odd_even").to_dict()
    assert "sensitivity" not in data
    assert TestResult.from_dict(data).sensitivity is None


def test_a_result_with_sensitivity_round_trips():
    result = _result("odd_even", sensitivity={"main": _rule(0.99)})
    data = result.to_dict()
    assert data["sensitivity"]["main"]["detectable"] is True
    assert TestResult.from_dict(data) == result
