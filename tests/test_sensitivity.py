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
    Kind,
    category_block,
    enforce_sensitivity,
    gaussian_probability,
    not_applicable_block,
    parse_kind,
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
    "edge_events": {"proximity": "fraction", "comparison": "rule?"},
    "period_alias": {"main": "rule@0.9"},
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


# --- registry kinds: conditional sub-checks and a registered requirement (Codex design review) --


@pytest.mark.parametrize(
    "kind, parsed",
    [
        ("rule", Kind(RULE, REQUIRED_PROBABILITY, False)),
        ("rule?", Kind(RULE, REQUIRED_PROBABILITY, True)),
        ("rule@0.9", Kind(RULE, 0.9, False)),
        ("rule@0.9?", Kind(RULE, 0.9, True)),
        ("fraction?", Kind("fraction", None, True)),
    ],
)
def test_a_kind_is_parsed(kind, parsed):
    assert parse_kind(kind) == parsed


@pytest.mark.parametrize("kind", ["", "rules", "rule@x", "rule@0.2", "rule@nan", "fraction@0.9", 3])
def test_a_bad_kind_is_refused(kind):
    with pytest.raises(ValueError):
        parse_kind(kind)


def _edge(comparison):
    return {"proximity": category_block("fraction", "edge fraction 0.2"), "comparison": comparison}


def test_a_conditional_sub_check_may_be_not_applicable():
    out = _one(
        _result(
            "edge_events",
            severity=Severity.WARNING,
            sensitivity=_edge(
                not_applicable_block("fewer than half of the events are near an edge")
            ),
        )
    )
    assert out.status is TestStatus.PASS


def test_an_applicable_conditional_sub_check_must_be_detectable():
    out = _one(_result("edge_events", severity=Severity.WARNING, sensitivity=_edge(_rule(0.3))))
    assert out.status is TestStatus.INCONCLUSIVE
    assert "insufficient sensitivity" in out.message


@pytest.mark.parametrize(
    "block",
    [
        {"applicable": False, "reason": ""},
        {"applicable": True, "reason": "x"},
        {"applicable": False, "reason": "x", "detectable": True},
    ],
)
def test_a_malformed_not_applicable_block_is_refused(block):
    out = _one(_result("edge_events", severity=Severity.WARNING, sensitivity=_edge(block)))
    assert out.status is TestStatus.INCONCLUSIVE


def test_a_required_sub_check_cannot_be_declared_not_applicable():
    out = _one(_result("odd_even", sensitivity={"main": not_applicable_block("no reason to run")}))
    assert out.status is TestStatus.INCONCLUSIVE
    assert "requires this sub-check" in out.message


def test_a_pass_needs_at_least_one_applicable_sub_check():
    registry = {"x": {"a": "rule?", "b": "rule?"}}
    blocks = {"a": not_applicable_block("n/a"), "b": not_applicable_block("n/a")}
    (out,) = enforce_sensitivity([_result("x", sensitivity=blocks)], registry)
    assert out.status is TestStatus.INCONCLUSIVE
    assert "no applicable sub-check" in out.message
    assert registry_problems(["x"], registry, exempt=[]) == ["x: every sub-check is conditional"]


def test_the_registry_sets_a_rule_requirement_the_result_cannot_change():
    # period_alias: detectable iff at least 45 of 50 simulated sinusoids FAIL (acceptance WP1)
    ok = rule_block("sinusoid", 1000.0, "ppm", "alias-sim-1", 46 / 50, required=0.9)
    assert _one(_result("period_alias", sensitivity={"main": ok})).status is TestStatus.PASS
    weak = rule_block("sinusoid", 1000.0, "ppm", "alias-sim-1", 44 / 50, required=0.9)
    assert (
        _one(_result("period_alias", sensitivity={"main": weak})).status is TestStatus.INCONCLUSIVE
    )
    # the engine default (0.95) is not the registered 0.9: refused
    default = rule_block("sinusoid", 1000.0, "ppm", "alias-sim-1", 0.99)
    out = _one(_result("period_alias", sensitivity={"main": default}))
    assert out.status is TestStatus.INCONCLUSIVE
    assert "registered 0.9" in out.message
