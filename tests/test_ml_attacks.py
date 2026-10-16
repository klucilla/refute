"""ML pack: evaluation of the robustness attacks (WP3 W3.13), offline, with the claim's
predicates of predicates.py and the WP2 core rules."""

from decimal import Decimal, localcontext
from functools import partial

import pytest

from refute.core.paper import Attack, aggregate_claim, prerequisite_names
from refute.core.verdict import PaperVerdict, Severity, TestResult, TestStatus
from refute.packs.ml import attacks as at
from refute.packs.ml import predicates as pr

TOL = pr.Tolerance("1.0")
LOWER = pr.Tolerance("1.0", lower_bound=True)


def two_sided(x, tol=TOL):
    return pr.value_predicate(x, "90.0", "two_sided", tol)


def at_least(x):
    return pr.value_predicate(x, "90.0", "one_sided_at_least", TOL)


# ---- seeds (plan line 488) -------------------------------------------------------------------


def test_seeds_pass_with_four_of_five_and_the_mean():
    result = at.seeds(["90.5", "89.5", "90", "90.2", "92"], two_sided)  # one valid failure
    assert result.status is TestStatus.PASS and result.coverage == 5


def test_two_valid_seed_failures_are_fragile_even_with_runs_missing():
    result = at.seeds(["92", "88", None, None, None], two_sided)
    assert result.status is TestStatus.FAIL and result.metrics["valid_failures"] == 2


def test_the_mean_of_the_five_seeds_must_hold():
    # each run but one inside the tolerance, the mean outside it: 91.0, 91.0, 91.0, 91.0, 92.1
    result = at.seeds(["91.0", "91.0", "91.0", "91.0", "92.1"], two_sided)
    assert result.status is TestStatus.FAIL


def test_a_missing_seed_run_is_never_a_failure():
    result = at.seeds(["90", "90", "90", "90", None], two_sided)
    assert result.status is TestStatus.INCONCLUSIVE and result.coverage == 4


def test_one_sided_modes_stay_one_sided_in_the_seeds_attack():
    high = ["95", "96", "97", "98", "99"]  # far above 90: a two-sided claim fails
    assert at.seeds(high, at_least).status is TestStatus.PASS
    assert at.seeds(high, two_sided).status is TestStatus.FAIL


def test_a_predicate_that_cannot_decide_is_never_a_valid_failure():
    lower = partial(two_sided, tol=LOWER)  # published uncertainty not convertible
    result = at.seeds(["95", "95", "95", "95", "95"], lower)
    assert result.status is TestStatus.INCONCLUSIVE and result.metrics["valid_failures"] == 0


def test_a_conclusive_failure_of_the_mean_survives_an_undecided_run():
    """Codex review: margin with g_pub 3 and a lower tolerance bound of 1; the runs give
    FAIL, INCONCLUSIVE, PASS, PASS, PASS and the mean (-18) fails for every tolerance."""
    margin = partial(
        pr.comparison_predicate, mode="margin", tol=pr.Tolerance("1", lower_bound=True), g_pub="3"
    )
    result = at.seeds(["-100", "1", "3", "3", "3"], margin)
    assert result.status is TestStatus.FAIL and result.coverage == 5
    got = _through_core(result)
    assert got.verdict is PaperVerdict.FRAGILE


def test_seeds_needs_five_slots():
    with pytest.raises(ValueError, match="5 run slots"):
        at.seeds(["90"] * 4, two_sided)


# ---- data_split (plan line 489) --------------------------------------------------------------


def test_data_split_needs_three_of_three():
    assert at.data_split(["90", "90.5", "89.5"], two_sided).status is TestStatus.PASS
    assert at.data_split(["90", "92", None], two_sided).status is TestStatus.FAIL  # 1 of 3
    assert at.data_split(["90", "90", None], two_sided).status is TestStatus.INCONCLUSIVE


def test_a_comparison_claim_is_attacked_on_magnitude():
    magnitude = partial(pr.comparison_predicate, mode="magnitude", tol=TOL, d_pub="5")
    # every split keeps the direction (d > 0) but one is far from the published gap
    result = at.data_split(["5", "5.5", "1"], magnitude)
    assert result.status is TestStatus.FAIL


# ---- ablation, holdout -----------------------------------------------------------------------


def test_ablation_direction_and_margin():
    assert at.ablation(["0.5", "0.7"], "direction").status is TestStatus.PASS
    assert at.ablation(["0.5", "-0.5"], "direction").status is TestStatus.FAIL  # mean 0
    margin = at.ablation(["2.0", "2.2"], "margin", pr.Tolerance("0.5"), "3.0")
    assert margin.status is TestStatus.FAIL  # 2.1 < 3.0 - 0.5
    assert at.ablation(["2.6", "2.4"], "margin", pr.Tolerance("0.5"), "3.0").status is (
        TestStatus.PASS
    )


def test_ablation_needs_every_run_for_its_mean():
    result = at.ablation(["0.5", None], "direction")
    assert result.status is TestStatus.INCONCLUSIVE and result.coverage == 1


def test_holdout_uses_the_widened_tolerance_and_records_the_factor():
    wide = pr.widen(TOL, "2")
    result = at.holdout("91.5", partial(two_sided, tol=wide), "2")
    assert result.status is TestStatus.PASS and result.metrics["factor"] == "2"
    assert at.holdout("92.5", partial(two_sided, tol=wide), "2").status is TestStatus.FAIL
    assert at.holdout(None, two_sided, 1).status is TestStatus.INCONCLUSIVE
    with pytest.raises(ValueError, match="at least 1"):
        at.holdout("90", two_sided, "0.5")


# ---- leakage (plan line 492) -----------------------------------------------------------------


def test_leakage_above_the_fraction_is_a_failure():
    train = ["a", "b", "c"]
    assert at.leakage(train, ["a", "x", "y", "z"], "0.25").status is TestStatus.PASS  # = limit
    result = at.leakage(train, ["a", "b", "y", "z"], "0.25")
    assert result.status is TestStatus.FAIL and result.metrics["fraction"] == "1/2"
    assert result.coverage == 4 and result.coverage_unit == "test examples"


def test_leakage_on_an_empty_split_examines_nothing():
    for train, test in (([], ["a"]), (["a"], []), (None, ["a"])):
        result = at.leakage(train, test, "0.1")
        assert result.status is TestStatus.INCONCLUSIVE and result.coverage == 0


# ---- trivial baseline (1.0.6) ----------------------------------------------------------------


def test_random_baseline_is_exact_and_independent_of_frequencies():
    with localcontext() as ctx:
        ctx.prec = pr.PRECISION
        third = Decimal(100) / Decimal(3)
    for k, acc in ((2, Decimal(50)), (3, third), (10, Decimal(10))):
        labels = list(range(k))
        assert at.trivial_baseline_value("random", labels, "accuracy", "percent") == acc
    assert at.trivial_baseline_value("random", ["a", "b"], "error_rate", "fraction") == Decimal(
        "0.5"
    )


def test_majority_baseline_from_the_training_labels():
    train = ["a"] * 9 + ["b"]
    test = ["a"] * 6 + ["b"] * 4
    value = at.trivial_baseline_value("majority", ["a", "b"], "accuracy", "fraction", train, test)
    assert value == Decimal("0.6")


def test_a_tie_for_the_majority_takes_the_weakest_baseline():
    train = ["a", "a", "b", "b"]
    test = ["a"] * 7 + ["b"] * 3
    value = at.trivial_baseline_value("majority", ["a", "b"], "accuracy", "fraction", train, test)
    assert value == Decimal("0.3")


def test_baseline_validation():
    with pytest.raises(ValueError, match="accuracy and error_rate"):
        at.trivial_baseline_value("random", [0, 1], "f1", "fraction")
    with pytest.raises(ValueError, match="2 distinct"):
        at.trivial_baseline_value("random", [0], "accuracy", "fraction")
    with pytest.raises(ValueError, match="outside the declared"):
        at.trivial_baseline_value("majority", [0, 1], "accuracy", "fraction", [0, 2], [0])
    with pytest.raises(ValueError, match="percent or fraction"):
        at.trivial_baseline_value("random", [0, 1], "accuracy", "native")


def test_the_claim_must_beat_the_baseline_by_more_than_its_tolerance():
    beat = at.trivial_baseline("60", "50", True, TOL, 100)
    assert beat.status is TestStatus.PASS
    assert at.trivial_baseline("50.5", "50", True, TOL, 100).status is TestStatus.FAIL
    assert at.trivial_baseline("60", "50", True, LOWER, 100).status is TestStatus.INCONCLUSIVE
    assert at.trivial_baseline("60", "50", True, TOL, 0).status is TestStatus.INCONCLUSIVE


# ---- through the WP2 core --------------------------------------------------------------------


def _passing(name, severity=Severity.GATE):
    return TestResult(name, TestStatus.PASS, severity, "ok", coverage=1)


@pytest.mark.parametrize(
    ("result", "verdict"),
    [
        (at.seeds(["92", "88", "90", "90", "90"], two_sided), PaperVerdict.FRAGILE),
        (at.leakage(["a"], ["a", "b"], "0.1"), PaperVerdict.FRAGILE),
        (at.seeds(["90", "90", "90", "90", None], two_sided), PaperVerdict.INCONCLUSIVE),
        (at.data_split(["90", "90", "90"], two_sided), PaperVerdict.REPRODUCED),
    ],
)
def test_attack_results_reach_the_expected_claim_verdict(result, verdict):
    assert _through_core(result).verdict is verdict


def _through_core(result):
    base = [
        _passing(g)
        for g in ("environment_build", "data_present", "run_completed", "metric_extracted")
    ]
    base.append(_passing("base_reproduction", Severity.FATAL))
    run, metric = (_passing(n) for n in prerequisite_names(result.name))
    return aggregate_claim(
        base,
        [Attack(result.name, run, metric, result)],
        [result.name],
        metric_recompute_applies=False,
    )
