"""ML pack: the base reproduction check (WP3 design 1.0.4, 1.0.5, 1.0.7), offline, through
the WP2 core."""

from decimal import Decimal
from fractions import Fraction
from functools import partial

import pytest

from refute.core.paper import CoverageMinimum, aggregate_claim
from refute.core.verdict import PaperVerdict, Severity, TestResult, TestStatus
from refute.packs.ml import predicates as pr
from refute.packs.ml import reproduction as rp

TOL = pr.Tolerance("1.8")


def two_sided(x):
    return pr.value_predicate(x, "91.2", "two_sided", TOL)


def verdict(result, n_base):
    gates = [
        TestResult(g, TestStatus.PASS, Severity.GATE, "ok", coverage=1)
        for g in ("environment_build", "data_present", "run_completed", "metric_extracted")
    ]
    minimum = {"base_reproduction": CoverageMinimum(n_base, n_base)}
    return aggregate_claim(
        [*gates, result], [], [], metric_recompute_applies=False, minimums=minimum
    ).verdict


def test_the_mean_of_the_base_runs_is_compared_exactly():
    result = rp.base_reproduction(["90.1", "91.0", "92.6"], two_sided)  # mean 91.233...
    assert result.status is TestStatus.PASS and result.coverage == 3
    assert result.metrics["mean"] == "2737/30"  # exact; not a finite decimal
    exact = rp.base_reproduction(["91.0", "91.4"], two_sided)
    assert exact.metrics["mean"] == "91.2"
    assert verdict(result, 3) is PaperVerdict.REPRODUCED


def test_a_value_at_the_limit_reproduces():
    # 91.2 + 1.8 = 93.0 exactly: equality at the limit counts as reproduced
    result = rp.base_reproduction(["93.0", "93.0"], two_sided)
    assert result.status is TestStatus.PASS


def test_a_mean_outside_the_tolerance_is_not_reproduced():
    result = rp.base_reproduction(["88.0", "89.0", "89.3"], two_sided)  # mean 88.77
    assert result.status is TestStatus.FAIL and result.coverage == 3
    assert verdict(result, 3) is PaperVerdict.NOT_REPRODUCED


def test_a_missing_base_run_never_gives_a_failure():
    result = rp.base_reproduction(["50.0", None, "50.0"], two_sided)
    assert result.status is TestStatus.INCONCLUSIVE and result.coverage == 2
    assert verdict(result, 3) is PaperVerdict.INCONCLUSIVE


def test_fewer_seeds_than_the_paper_are_recorded():
    result = rp.base_reproduction(["91.2", "91.2"], two_sided, reported_n_seeds=5)
    assert "fewer than the paper's 5" in result.message


def test_a_comparison_uses_the_mean_of_the_oriented_per_seed_differences():
    method, reference = ["91.0", "92.0", "90.0"], ["89.0", "89.5", "88.5"]
    d = rp.oriented_differences(method, reference, "method_minus_reference")
    assert d == [Decimal("2.0"), Decimal("2.5"), Decimal("1.5")]
    flipped = rp.oriented_differences(method, reference, "reference_minus_method")
    assert flipped == [-x for x in d]
    margin = partial(pr.comparison_predicate, mode="margin", tol=pr.Tolerance("0.5"), g_pub="2.2")
    assert rp.base_reproduction(d, margin).status is TestStatus.PASS  # 2.0 >= 2.2 - 0.5
    direction = partial(pr.comparison_predicate, mode="direction")
    tie = rp.oriented_differences(["90", "91"], ["91", "90"], "method_minus_reference")
    assert rp.base_reproduction(tie, direction).status is TestStatus.FAIL  # d_rep = 0


def test_a_seed_with_a_missing_side_has_no_difference():
    d = rp.oriented_differences(["91", None], ["89", "88"], "method_minus_reference")
    assert d == [Decimal("2"), None]
    with pytest.raises(ValueError, match="same seeds"):
        rp.oriented_differences(["91"], ["89", "88"], "method_minus_reference")
    with pytest.raises(ValueError, match="orientation"):
        rp.oriented_differences(["91"], ["89"], "method")


def test_a_predicate_that_cannot_decide_stays_inconclusive():
    lower = partial(
        pr.value_predicate, reported="91.2", mode="two_sided", tol=pr.Tolerance("1", True)
    )
    result = rp.base_reproduction(["85.0"], lower)
    assert result.status is TestStatus.INCONCLUSIVE
    assert verdict(result, 1) is PaperVerdict.INCONCLUSIVE


def test_a_small_advantage_is_never_cancelled_by_rounding():
    """Codex review: 1 + 1e-50 - 1 summed in 50-digit decimals gives 0, a false tie."""
    direction = partial(pr.comparison_predicate, mode="direction")
    d = rp.oriented_differences(["1", "1e-50", "0"], ["0", "0", "1"], "method_minus_reference")
    for order in ([0, 1, 2], [2, 1, 0], [1, 2, 0]):
        result = rp.base_reproduction([d[i] for i in order], direction)
        assert result.status is TestStatus.PASS  # the exact mean is 1e-50 / 3 > 0
        assert result.metrics["mean"] == "1/300000000000000000000000000000000000000000000000000"


def test_a_mean_too_close_to_the_limit_is_inconclusive():
    # 91.2 + 1.8 = 93; the exact mean exceeds 93 by 1e-60 / 3, beyond 50 digits
    tiny = "93." + "0" * 59 + "1"
    result = rp.base_reproduction(["93", "93", tiny], two_sided)
    assert result.status is TestStatus.INCONCLUSIVE
    assert result.message.startswith(rp.UNDECIDABLE_MEAN)
    assert verdict(result, 3) is PaperVerdict.INCONCLUSIVE


def test_a_long_finite_mean_goes_to_the_predicate_exactly():
    """Codex review, round 2: x = reported = 1 + 1e-60 with tolerance 0 must reproduce;
    rounding the mean to 50 digits on both sides would have given FAIL twice."""
    value = "1." + "0" * 59 + "1"
    exact = partial(pr.value_predicate, reported=value, mode="two_sided", tol=pr.Tolerance("0"))
    result = rp.base_reproduction([value], exact)
    assert result.status is TestStatus.PASS and result.metrics["mean"] == value


def test_a_passing_interval_narrower_than_the_rounding_is_never_a_failure():
    """The exact mean 1/3 is within 1e-60 of the published value, but both of its
    50-digit roundings are farther: the answer is INCONCLUSIVE, not FAIL."""
    reported = "0." + "3" * 61
    narrow = partial(
        pr.value_predicate, reported=reported, mode="two_sided", tol=pr.Tolerance("1e-60")
    )
    result = rp.base_reproduction(["1", "0", "0"], narrow)
    assert result.status is TestStatus.INCONCLUSIVE
    assert result.message.startswith(rp.UNDECIDABLE_MEAN)
    wide = partial(pr.value_predicate, reported="0.3", mode="two_sided", tol=pr.Tolerance("0.01"))
    assert rp.base_reproduction(["1", "0", "0"], wide).status is TestStatus.FAIL
    loose = partial(pr.value_predicate, reported="0.3", mode="two_sided", tol=pr.Tolerance("0.05"))
    assert rp.base_reproduction(["1", "0", "0"], loose).status is TestStatus.PASS


def test_a_difference_is_exact_whatever_the_exponents():
    d = rp.oriented_differences(["1e300"], ["1e-300"], "method_minus_reference")
    assert Fraction(d[0]) == Fraction(10) ** 300 - Fraction(1, 10**300)


def test_at_least_one_run():
    with pytest.raises(ValueError):
        rp.base_reproduction([], two_sided)
