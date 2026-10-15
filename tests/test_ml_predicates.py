"""Reproduction predicates of ML claims (plan section 6.2; wp3-acceptance.md 1.0.5,
1.0.6, 1.0.9, 1.0.10 and the cases of section 2), offline. Expected values are worked
out by hand in the comments."""

import math
from decimal import Decimal

import pytest

from refute.core.verdict import TestStatus
from refute.packs.ml import predicates as pr
from refute.packs.ml.predicates import NONE, PublishedUncertainty, Tolerance, ToleranceParams

DEFAULT = ToleranceParams(rel_tol=0.02, k_sd=2.0, abs_floor=0.5)  # percent defaults
NOT_CONVERTIBLE = PublishedUncertainty("not_convertible")
PASS, FAIL, INC = TestStatus.PASS, TestStatus.FAIL, TestStatus.INCONCLUSIVE


def sd(value):
    return PublishedUncertainty("converted", value)


# ---- one-number tolerance ------------------------------------------------------------------


def test_one_number_tolerance():
    # max(0.5, 0.02 * 91.2 = 1.824, 2 * 0.3 = 0.6) = 1.824, exactly
    assert pr.one_number(91.2, DEFAULT, sd(0.3)).value == Decimal("1.824")
    # max(0.5, 1.824, 2 * 1.5 = 3.0) = 3.0
    assert pr.one_number(91.2, DEFAULT, sd(1.5)).value == Decimal("3.0")
    # no published uncertainty: no k_sd term; floor decides for a small value
    assert pr.one_number(10.0, DEFAULT, NONE) == Tolerance("0.5")
    lower = pr.one_number(80.0, DEFAULT, NOT_CONVERTIBLE)
    assert lower == Tolerance("1.6", lower_bound=True)


@pytest.mark.parametrize("sign", [1, -1])
def test_equality_at_the_limit_is_exact(sign):
    """Codex review: in binary floats 61.2 - 60 is 1.2000000000000028, which moved a
    value at the limit across it. The predicates compute in decimal arithmetic."""
    tol = pr.one_number(60.0, DEFAULT, NONE)  # 0.02 * 60 = 1.2, exactly
    assert tol.value == Decimal("1.2")
    assert pr.value_predicate(sign * 61.2, sign * 60.0, "two_sided", tol).status is PASS
    assert pr.comparison_predicate(61.2, "magnitude", tol, d_pub=60.0).status is PASS
    assert pr.comparison_predicate(0.6, "margin", Tolerance(0.5), g_pub=1.1).status is PASS
    # equality is not "more than" the tolerance
    assert pr.trivial_baseline_predicate(51.2, 50.0, True, tol).status is FAIL
    assert pr.trivial_baseline_predicate("51.2", "50", True, tol).status is FAIL
    # just past the limit
    assert pr.value_predicate(sign * 61.21, sign * 60.0, "two_sided", tol).status is FAIL
    assert pr.trivial_baseline_predicate(51.21, 50.0, True, tol).status is PASS


def test_numbers_are_exact_decimals():
    assert pr.dec(0.1) == Decimal("0.1")
    assert pr.dec("91.20") == Decimal("91.20")
    assert pr.dec(3) == Decimal(3)
    for bad in (math.nan, math.inf, "abc", True, None):
        with pytest.raises(ValueError):
            pr.dec(bad)


def test_invalid_parameters_are_refused():
    with pytest.raises(ValueError):
        ToleranceParams(rel_tol=-0.01, k_sd=2, abs_floor=0.5)
    with pytest.raises(ValueError):
        ToleranceParams(rel_tol=0.02, k_sd=math.inf, abs_floor=0.5)
    with pytest.raises(ValueError):
        PublishedUncertainty("converted")
    with pytest.raises(ValueError):
        PublishedUncertainty("none", 0.3)


# ---- value modes ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("mode", "x_rep", "status"),
    [
        ("two_sided", 91.2, PASS),
        ("two_sided", 91.2 + 1.824, PASS),  # equality at the limit reproduces
        ("two_sided", 93.1, FAIL),
        ("two_sided", 89.3, FAIL),
        ("one_sided_at_least", 89.376, PASS),  # 91.2 - 1.824, at the limit
        ("one_sided_at_least", 99.0, PASS),
        ("one_sided_at_least", 89.3, FAIL),
        ("one_sided_at_most", 93.024, PASS),
        ("one_sided_at_most", 80.0, PASS),
        ("one_sided_at_most", 93.1, FAIL),
    ],
)
def test_value_modes(mode, x_rep, status):
    tol = pr.one_number(91.2, DEFAULT, sd(0.3))  # 1.824
    assert pr.value_predicate(x_rep, 91.2, mode, Tolerance(tol.value)).status is status


def test_value_with_uncertainty_not_convertible():
    # section 2: published 80%, SE 2 points with no n, reproduced 75%; the lower
    # tolerance is max(0.5, 1.6) = 1.6, and 5 > 1.6 gives INCONCLUSIVE, never FAIL
    lower = pr.one_number(80.0, DEFAULT, NOT_CONVERTIBLE)
    out = pr.value_predicate(75.0, 80.0, "two_sided", lower)
    assert out.status is INC and pr.NOT_CONVERTIBLE in out.reason
    # inside the lower tolerance: PASS stands for every larger tolerance
    assert pr.value_predicate(79.0, 80.0, "two_sided", lower).status is PASS
    # kind none with the same numbers: FAIL
    none = pr.one_number(80.0, DEFAULT, NONE)
    assert pr.value_predicate(75.0, 80.0, "two_sided", none).status is FAIL


# ---- comparison modes ------------------------------------------------------------------------


def test_direction():
    assert pr.comparison_predicate(0.1, "direction").status is PASS
    assert pr.comparison_predicate(0.0, "direction").status is FAIL  # a tie does not reproduce
    assert pr.comparison_predicate(-1.0, "direction").status is FAIL


def test_margin():
    tol = Tolerance(1.0)
    assert pr.comparison_predicate(2.0, "margin", tol, g_pub=3.0).status is PASS  # at the limit
    assert pr.comparison_predicate(1.9, "margin", tol, g_pub=3.0).status is FAIL
    # d_rep <= 0 never reproduces, even when g_pub - tol_d <= 0
    assert pr.comparison_predicate(0.0, "margin", tol, g_pub=0.5).status is FAIL
    assert pr.comparison_predicate(-0.2, "margin", tol, g_pub=0.5).status is FAIL


def test_magnitude():
    tol = Tolerance(1.0)
    assert pr.comparison_predicate(9.0, "magnitude", tol, d_pub=10.0).status is PASS  # limit
    assert pr.comparison_predicate(11.0, "magnitude", tol, d_pub=10.0).status is PASS
    assert pr.comparison_predicate(8.9, "magnitude", tol, d_pub=10.0).status is FAIL


def test_difference_tolerance_without_paired_uncertainty():
    # tol_m = max(0.5, 1.8) = 1.8 (90), tol_b = max(0.5, 1.6) = 1.6 (80)
    tol = pr.difference_tolerance(10.0, DEFAULT, 90.0, 80.0, NONE, NONE, NONE)
    assert float(tol.value) == pytest.approx(math.sqrt(1.8**2 + 1.6**2)) and not tol.lower_bound


def test_difference_tolerance_with_paired_uncertainty():
    # max(0.5, 0.02 * 10 = 0.2, 2 * 0.4 = 0.8) = 0.8
    tol = pr.difference_tolerance(10.0, DEFAULT, 90.0, 80.0, NONE, NONE, sd(0.4))
    assert tol == Tolerance("0.8")


def test_magnitude_with_paired_uncertainty_not_convertible():
    # section 2: paired SE 0.05 with no n, published 90 and 80 (d_pub 10), reproduced
    # d 8: tol_d is the lower paired tolerance max(0.5, 0.2) = 0.5, not the marginal
    # sqrt(1.8² + 1.6²); the deviation of 2 gives INCONCLUSIVE, never PASS or FAIL
    tol = pr.difference_tolerance(10.0, DEFAULT, 90.0, 80.0, NONE, NONE, NOT_CONVERTIBLE)
    assert tol == Tolerance(0.5, lower_bound=True)
    assert pr.comparison_predicate(8.0, "magnitude", tol, d_pub=10.0).status is INC


def test_margin_with_paired_uncertainty_not_convertible():
    # section 2: g_pub 10; d <= 0 fails for every tolerance; d = 8 is positive but below
    # g_pub minus the lower tolerance: INCONCLUSIVE
    tol = pr.difference_tolerance(10.0, DEFAULT, 90.0, 80.0, NONE, NONE, NOT_CONVERTIBLE)
    assert pr.comparison_predicate(0.0, "margin", tol, g_pub=10.0).status is FAIL
    assert pr.comparison_predicate(-3.0, "margin", tol, g_pub=10.0).status is FAIL
    assert pr.comparison_predicate(8.0, "margin", tol, g_pub=10.0).status is INC
    assert pr.comparison_predicate(9.6, "margin", tol, g_pub=10.0).status is PASS


def test_a_marginal_uncertainty_not_convertible_makes_tol_d_a_lower_bound():
    tol = pr.difference_tolerance(10.0, DEFAULT, 90.0, 80.0, NOT_CONVERTIBLE, NONE, NONE)
    assert tol.lower_bound


# ---- ablation ------------------------------------------------------------------------------


def test_ablation():
    assert pr.ablation_predicate(0.5, "direction").status is PASS
    assert pr.ablation_predicate(0.0, "direction").status is FAIL
    # tol_full = max(0.5, 1.824) = 1.824 (91.2), tol_ablated = max(0.5, 1.8) = 1.8 (90)
    tol = pr.ablation_tolerance(91.2, 90.0, DEFAULT, None, None)
    assert float(tol.value) == pytest.approx(math.sqrt(1.824**2 + 1.8**2))
    assert pr.ablation_predicate(0.1, "margin", tol, g_abl=1.2).status is PASS
    assert pr.ablation_predicate(0.0, "margin", tol, g_abl=1.2).status is FAIL
    assert pr.ablation_predicate(0.3, "margin", Tolerance(0.5, True), g_abl=1.2).status is INC
    assert pr.ablation_predicate(-1, "margin", Tolerance(0.5, True), g_abl=1.2).status is FAIL


# ---- trivial baseline ----------------------------------------------------------------------


def test_trivial_baseline():
    tol = pr.one_number(60.0, DEFAULT, NONE)  # max(0.5, 1.2) = 1.2
    assert pr.trivial_baseline_predicate(60.0, 50.0, True, tol).status is PASS
    exact = Tolerance(1.25)  # binary-exact values, so the limit is exact
    assert pr.trivial_baseline_predicate(51.25, 50.0, True, exact).status is FAIL  # not more than
    assert pr.trivial_baseline_predicate(50.5, 50.0, True, tol).status is FAIL
    # error rate: lower is better
    assert pr.trivial_baseline_predicate(40.0, 50.0, False, tol).status is PASS


def test_trivial_baseline_with_uncertainty_not_convertible():
    # section 2: accuracy published and reproduced 60%, baseline 50%, SE 10 points with no
    # n: an advantage of 10 over a lower tolerance of 1.2 gives INCONCLUSIVE, never PASS;
    # an advantage below the lower tolerance gives FAIL
    lower = pr.one_number(60.0, DEFAULT, NOT_CONVERTIBLE)
    assert lower == Tolerance("1.2", lower_bound=True)
    assert pr.trivial_baseline_predicate(60.0, 50.0, True, lower).status is INC
    assert pr.trivial_baseline_predicate(51.0, 50.0, True, lower).status is FAIL


# ---- holdout -------------------------------------------------------------------------------


def test_holdout_widens_the_claim_tolerance():
    tol = pr.one_number(91.2, DEFAULT, sd(0.3))  # 1.824
    wide = pr.widen(tol, math.sqrt(2))
    assert float(wide.value) == pytest.approx(1.824 * math.sqrt(2))
    # 2.0 away: outside the claim's tolerance, inside the widened one
    assert pr.value_predicate(89.2, 91.2, "two_sided", tol).status is FAIL
    assert pr.value_predicate(89.2, 91.2, "two_sided", wide).status is PASS
    assert pr.widen(Tolerance(1.0, True), 2.0).lower_bound
    with pytest.raises(ValueError):
        pr.widen(tol, 0.9)


def test_non_finite_inputs_are_refused():
    with pytest.raises(ValueError):
        pr.value_predicate(math.nan, 91.2, "two_sided", Tolerance(1.0))
    with pytest.raises(ValueError):
        pr.comparison_predicate(math.inf, "direction")
