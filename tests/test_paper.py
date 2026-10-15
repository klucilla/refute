"""Paper claim verdicts and the result of a paper (docs/validation/v0.3/wp2-acceptance.md,
W2.1-W2.7). All cases are synthetic and offline."""

from pathlib import Path

import pytest

from refute.core.paper import (
    BASE_GATES,
    EXPECTED_COVERAGE,
    ROBUSTNESS_INCONCLUSIVE,
    Attack,
    CoverageMinimum,
    FailureCause,
    GateFailure,
    aggregate_claim,
    apply_minimum_coverage,
    attack_result,
    data_split_attack,
    paper_profile,
    seeds_attack,
)
from refute.core.verdict import PaperVerdict, Severity, TestResult, TestStatus

OK, KO, UNK = TestStatus.PASS, TestStatus.FAIL, TestStatus.INCONCLUSIVE
ROOT = Path(__file__).resolve().parents[1]


def check(name, status, severity=Severity.GATE, coverage=1):
    return TestResult(name, status, severity, "", coverage=coverage, coverage_unit="items")


def base(recompute=True, **overrides):
    """A complete, passing base reproduction; overrides replace one check's status
    (None removes it)."""
    checks = [check(g, OK) for g in BASE_GATES]
    checks.append(check("base_reproduction", OK, Severity.FATAL))
    if recompute:
        checks.append(check("metric_recompute", OK, Severity.FATAL))
    out = []
    for c in checks:
        if c.name in overrides:
            value = overrides[c.name]
            if value is None:
                continue
            c = check(c.name, value, c.severity, c.coverage)
        out.append(c)
    return out


FATAL = ("base_reproduction", "metric_recompute")


def attack(name, result, prereq=OK, coverage=5):
    """An attack with both prerequisites in state ``prereq``; ``result`` is a status or
    a ready TestResult."""
    if isinstance(result, TestStatus):
        result = attack_result(name, result, coverage)
    return Attack(
        name,
        run=check(f"{name}:run", prereq),
        metric=check(f"{name}:metric", prereq),
        result=result,
    )


def verdict(base_checks, attacks=(), expected=("seeds", "data_split"), recompute=True, **kw):
    return aggregate_claim(base_checks, attacks, expected, metric_recompute_applies=recompute, **kw)


def complete(cause, attempts=3):
    return GateFailure(cause, attempts_completed=attempts, attempts_required=attempts)


# W2.1 -----------------------------------------------------------------------------


def test_paper_verdict_has_inconclusive_and_matches_the_docs():
    values = [v.value for v in PaperVerdict]
    assert values == [
        "REPRODUCED",
        "FRAGILE",
        "NOT_REPRODUCED",
        "NOT_REPRODUCIBLE",
        "INCONCLUSIVE",
    ]
    doc = (ROOT / "docs" / "verdicts.md").read_text(encoding="utf-8")
    paper = doc.split("## Paper verdicts (from v0.3)", 1)[1].split("**Status.**", 1)[0]
    assert all(f"`{v}`" in paper for v in values)


# W2.2 order, steps 0-6 ----------------------------------------------------------


def test_step6_reproduced():
    v = verdict(base(), [attack("seeds", OK), attack("data_split", OK, coverage=3)])
    assert v.verdict is PaperVerdict.REPRODUCED
    assert v.basic_reproduction_obtained and not v.incomplete_coverage


def test_step6_reproduced_without_metric_recompute_when_it_does_not_apply():
    v = verdict(
        base(recompute=False), [attack("seeds", OK), attack("data_split", OK)], recompute=False
    )
    assert v.verdict is PaperVerdict.REPRODUCED


def test_step0_zero_coverage_pass_is_not_reproduced():
    checks = base()
    checks[-2] = check("base_reproduction", OK, Severity.FATAL, coverage=0)
    v = verdict(checks, [attack("seeds", OK), attack("data_split", OK)])
    assert v.verdict is PaperVerdict.INCONCLUSIVE
    assert "incomplete" in v.reason


def test_step0_below_positive_minimum_is_not_reproduced():
    v = verdict(
        base(),
        [attack("seeds", OK, coverage=3), attack("data_split", OK, coverage=3)],
        minimums={"seeds": CoverageMinimum(positive=5, negative=2)},
    )
    assert v.verdict is PaperVerdict.INCONCLUSIVE
    assert v.status == ROBUSTNESS_INCONCLUSIVE


@pytest.mark.parametrize("coverage", [0, None])
def test_step0_fail_without_examined_data_is_never_not_reproduced(coverage):
    checks = base()
    checks[-2] = check("base_reproduction", KO, Severity.FATAL, coverage=coverage)
    v = verdict(checks, [attack("seeds", OK), attack("data_split", OK)])
    assert v.verdict is PaperVerdict.INCONCLUSIVE


@pytest.mark.parametrize("coverage", [0, None])
def test_step0_attack_fail_without_examined_data_is_never_fragile(coverage):
    failing = TestResult("seeds", KO, Severity.WARNING, "", coverage=coverage)
    v = verdict(base(), [attack("seeds", failing), attack("data_split", OK)])
    assert v.verdict is PaperVerdict.INCONCLUSIVE
    assert v.status == ROBUSTNESS_INCONCLUSIVE


@pytest.mark.parametrize(
    ("gate", "cause"),
    [
        ("environment_build", FailureCause.BUILD_LADDER),
        ("run_completed", FailureCause.DOCUMENTED_COMMAND),
        ("metric_extracted", FailureCause.DOCUMENTED_COMMAND),
        ("data_present", FailureCause.DOCUMENTED_COMMAND),
        ("data_present", FailureCause.ARTIFACT_ABSENT),
        ("environment_build", FailureCause.ARTIFACT_ABSENT),
    ],
)
def test_step1_each_artifact_cause_with_complete_attempts_gives_not_reproducible(gate, cause):
    v = verdict(base(**{gate: KO}), failures={gate: complete(cause)})
    assert v.verdict is PaperVerdict.NOT_REPRODUCIBLE
    assert cause.value in v.reason


@pytest.mark.parametrize(
    "cause",
    [FailureCause.BUILD_LADDER, FailureCause.DOCUMENTED_COMMAND, FailureCause.ARTIFACT_ABSENT],
)
def test_step1_artifact_cause_with_incomplete_attempts_is_inconclusive(cause):
    gate = {
        FailureCause.BUILD_LADDER: "environment_build",
        FailureCause.DOCUMENTED_COMMAND: "run_completed",
        FailureCause.ARTIFACT_ABSENT: "data_present",
    }[cause]
    failure = GateFailure(cause, attempts_completed=2, attempts_required=3)
    v = verdict(base(**{gate: KO}), failures={gate: failure})
    assert v.verdict is PaperVerdict.INCONCLUSIVE
    assert "incomplete attempts" in v.reason


def test_step1_artifact_cause_on_a_gate_it_does_not_apply_to_is_inconclusive():
    v = verdict(
        base(data_present=KO), failures={"data_present": complete(FailureCause.BUILD_LADDER)}
    )
    assert v.verdict is PaperVerdict.INCONCLUSIVE


def test_step1_artifact_cause_on_an_inconclusive_gate_is_not_not_reproducible():
    v = verdict(
        base(environment_build=UNK),
        failures={"environment_build": complete(FailureCause.BUILD_LADDER)},
    )
    assert v.verdict is PaperVerdict.INCONCLUSIVE


@pytest.mark.parametrize(
    "cause",
    [
        FailureCause.BUDGET_EXHAUSTED,
        FailureCause.OPERATIONAL_GUARD,
        FailureCause.REFUTE_ERROR,
        FailureCause.TRANSIENT_NETWORK,
        FailureCause.INTERRUPTED,
        FailureCause.UNDETERMINED,
        None,
        "not-a-cause",
    ],
)
def test_step1_refute_side_or_unknown_cause_is_never_not_reproducible(cause):
    failures = {} if cause is None else {"run_completed": complete(cause)}
    v = verdict(base(run_completed=KO), failures=failures)
    assert v.verdict is PaperVerdict.INCONCLUSIVE


def test_step1_missing_or_inconclusive_gate_is_inconclusive():
    assert verdict(base(data_present=None)).verdict is PaperVerdict.INCONCLUSIVE
    assert verdict(base(metric_extracted=UNK)).verdict is PaperVerdict.INCONCLUSIVE


@pytest.mark.parametrize("fatal", FATAL)
def test_step2_valid_fatal_failure_is_not_reproduced(fatal):
    v = verdict(base(**{fatal: KO}), [attack("seeds", OK), attack("data_split", OK)])
    assert v.verdict is PaperVerdict.NOT_REPRODUCED
    assert v.attacks_not_executed == []  # both attacks were executed


def test_step2_not_reproduced_is_kept_when_attacks_are_missing():
    v = verdict(base(base_reproduction=KO), [])
    assert v.verdict is PaperVerdict.NOT_REPRODUCED
    assert v.attacks_not_executed == ["seeds", "data_split"]


def test_step2_lists_only_the_attacks_that_did_not_run():
    v = verdict(base(base_reproduction=KO), [attack("seeds", OK)])
    assert v.attacks_not_executed == ["data_split"]


def test_step1_lists_the_attacks_that_did_not_run():
    v = verdict(base(run_completed=KO), [attack("seeds", OK)])
    assert v.verdict is PaperVerdict.INCONCLUSIVE
    assert v.attacks_not_executed == ["data_split"]


@pytest.mark.parametrize("missing", FATAL)
def test_step3_incomplete_base_is_inconclusive(missing):
    v = verdict(base(**{missing: None}), [attack("seeds", OK), attack("data_split", OK)])
    assert v.verdict is PaperVerdict.INCONCLUSIVE
    assert not v.basic_reproduction_obtained


def test_step4_seed_fragile_two_of_five():
    seeds = seeds_attack([True, False, True, False, True], mean_holds=True)
    assert seeds.status is KO and seeds.coverage == 5
    v = verdict(base(), [attack("seeds", seeds), attack("data_split", OK)])
    assert v.verdict is PaperVerdict.FRAGILE


def test_step4_fragile_from_a_partial_attack_flags_incomplete_coverage():
    seeds = seeds_attack([False, False, None, None, None], mean_holds=None)
    assert seeds.status is KO and seeds.coverage == 2
    v = verdict(base(), [attack("seeds", seeds), attack("data_split", OK, coverage=3)])
    assert v.verdict is PaperVerdict.FRAGILE
    assert v.incomplete_coverage
    assert v.attacks_incomplete == ["seeds"]
    assert v.attacks_not_executed == []


def test_pass_below_the_attack_expected_coverage_is_not_a_pass():
    partial = attack_result("data_split", OK, 2)
    partial.metrics = {EXPECTED_COVERAGE: 3}
    v = verdict(base(), [attack("seeds", OK), attack("data_split", partial)])
    assert v.verdict is PaperVerdict.INCONCLUSIVE
    assert v.status == ROBUSTNESS_INCONCLUSIVE
    assert v.attacks_incomplete == ["data_split"]


def test_step4_split_fragile_one_of_three():
    split = data_split_attack([True, False, True])
    assert split.status is KO and split.coverage == 3
    v = verdict(base(), [attack("seeds", OK), attack("data_split", split)])
    assert v.verdict is PaperVerdict.FRAGILE


def test_step4_valid_failure_next_to_interrupted_attack_stays_fragile():
    seeds = seeds_attack([False, False, True, True, True], mean_holds=True)
    v = verdict(base(), [attack("seeds", seeds), attack("data_split", OK, prereq=UNK)])
    assert v.verdict is PaperVerdict.FRAGILE
    assert v.incomplete_coverage


def test_step5_interrupted_attack_without_failure_is_inconclusive_with_status():
    v = verdict(base(), [attack("seeds", OK), attack("data_split", OK, prereq=UNK)])
    assert v.verdict is PaperVerdict.INCONCLUSIVE
    assert v.status == ROBUSTNESS_INCONCLUSIVE
    assert v.basic_reproduction_obtained


def test_step5_missing_attack_is_inconclusive_and_listed():
    v = verdict(base(), [attack("seeds", OK)])
    assert v.verdict is PaperVerdict.INCONCLUSIVE
    assert v.attacks_not_executed == ["data_split"]


# W2.4: attack prerequisites are both required and never reopen the base -------------


def test_failed_attack_prerequisite_does_not_touch_the_base():
    v = verdict(base(), [attack("seeds", KO, prereq=KO), attack("data_split", OK)])
    assert v.verdict is PaperVerdict.INCONCLUSIVE
    assert v.basic_reproduction_obtained


@pytest.mark.parametrize("drop", ["run", "metric", "both"])
@pytest.mark.parametrize("status", [OK, KO])
def test_attack_without_both_prerequisites_decides_nothing(drop, status):
    seeds = attack("seeds", status)
    if drop in ("run", "both"):
        seeds.run = None
    if drop in ("metric", "both"):
        seeds.metric = None
    v = verdict(base(), [seeds, attack("data_split", OK)])
    assert v.verdict is PaperVerdict.INCONCLUSIVE
    assert v.status == ROBUSTNESS_INCONCLUSIVE


# seeds and data_split semantics (plan 6.3, V-3) --------------------------------------


@pytest.mark.parametrize(
    ("runs", "mean", "expected"),
    [
        ([True] * 5, True, OK),
        ([True, True, True, True, False], True, OK),  # 4 of 5 hold
        ([True, True, True, True, False], False, KO),  # the mean fails
        ([True, False, True, False, True], True, KO),  # 2 valid failures
        ([False, False, None, None, None], None, KO),  # 2 valid failures suffice
        ([True, True, True, True, None], True, UNK),  # a missing run is not a failure
        ([True, False, None, True, True], True, UNK),
        ([True] * 5, None, UNK),  # mean not evaluated
        ([None] * 5, None, UNK),
    ],
)
def test_seeds_attack_rule(runs, mean, expected):
    assert seeds_attack(runs, mean).status is expected


@pytest.mark.parametrize(
    ("runs", "expected"),
    [
        ([True, True, True], OK),
        ([True, False, True], KO),
        ([False, None, None], KO),
        ([True, True, None], UNK),
        ([None, None, None], UNK),
    ],
)
def test_data_split_attack_rule(runs, expected):
    assert data_split_attack(runs).status is expected


def test_seeds_and_split_need_every_slot():
    with pytest.raises(ValueError):
        seeds_attack([True] * 4, True)
    with pytest.raises(ValueError):
        data_split_attack([True] * 2)


def test_seeds_with_no_valid_run_never_passes_as_a_claim_check():
    v = verdict(base(), [attack("seeds", seeds_attack([None] * 5, None)), attack("data_split", OK)])
    assert v.verdict is PaperVerdict.INCONCLUSIVE


# Inputs that would silently drop evidence are rejected --------------------------------


def test_metric_recompute_given_when_it_does_not_apply_is_rejected():
    with pytest.raises(ValueError, match="metric_recompute"):
        verdict(base(metric_recompute=KO), recompute=False)


def test_undeclared_base_result_is_rejected():
    with pytest.raises(ValueError, match="not declared"):
        verdict(base() + [check("extra_check", KO, Severity.FATAL)])


@pytest.mark.parametrize("name", ["environment_build", "base_reproduction"])
def test_duplicate_base_result_is_rejected(name):
    checks = base() + [check(name, OK, Severity.FATAL)]
    with pytest.raises(ValueError, match="duplicate"):
        verdict(checks)


def test_duplicate_attack_is_rejected():
    with pytest.raises(ValueError, match="duplicate"):
        verdict(base(), [attack("seeds", KO), attack("seeds", OK), attack("data_split", OK)])


def test_duplicate_expected_attack_is_rejected():
    with pytest.raises(ValueError, match="duplicate"):
        verdict(base(), [attack("seeds", OK)], expected=("seeds", "seeds"))


def test_unexpected_attack_is_rejected():
    with pytest.raises(ValueError, match="not expected"):
        verdict(base(), [attack("seeds", OK), attack("data_split", OK), attack("ablation", KO)])


def test_attack_result_with_another_name_is_rejected():
    wrong = attack("seeds", attack_result("data_split", OK, 5))
    with pytest.raises(ValueError, match="carries a result"):
        verdict(base(), [wrong, attack("data_split", OK)])


def test_minimum_of_a_prerequisite_that_did_not_arrive_is_accepted():
    seeds = attack("seeds", OK)
    seeds.run = None  # interrupted
    minimums = {"seeds:run": CoverageMinimum(positive=1, negative=1)}
    fragile = verdict(base(), [seeds, attack("data_split", KO, coverage=3)], minimums=minimums)
    assert fragile.verdict is PaperVerdict.FRAGILE
    assert fragile.incomplete_coverage
    open_ = verdict(base(), [seeds, attack("data_split", OK)], minimums=minimums)
    assert open_.verdict is PaperVerdict.INCONCLUSIVE
    assert open_.status == ROBUSTNESS_INCONCLUSIVE


def test_prerequisite_with_another_name_is_rejected():
    seeds = attack("seeds", OK)
    seeds.metric = check("seeds:other", OK)
    with pytest.raises(ValueError, match="prerequisite"):
        verdict(base(), [seeds, attack("data_split", OK)])


def test_minimum_for_an_unknown_check_is_rejected():
    with pytest.raises(ValueError, match="unknown checks"):
        verdict(base(), minimums={"seed": CoverageMinimum(positive=5)})


def test_failure_cause_for_a_name_that_is_not_a_gate_is_rejected():
    with pytest.raises(ValueError, match="not gates"):
        verdict(base(), failures={"base_reproduction": complete(FailureCause.BUILD_LADDER)})


def test_duplicate_claim_in_a_profile_is_rejected():
    with pytest.raises(ValueError, match="duplicate"):
        paper_profile([("C1", PaperVerdict.REPRODUCED), ("C1", PaperVerdict.FRAGILE)])


# W2.6 minimum coverage --------------------------------------------------------------


def test_fail_below_negative_minimum_gives_no_negative_conclusion():
    v = verdict(
        base(),
        [attack("seeds", KO, coverage=1), attack("data_split", OK)],
        minimums={"seeds": CoverageMinimum(positive=5, negative=2)},
    )
    assert v.verdict is PaperVerdict.INCONCLUSIVE


def test_minimum_coverage_rules():
    m = CoverageMinimum(positive=3, negative=2)
    assert apply_minimum_coverage(check("x", OK, coverage=3), m).status is OK
    assert apply_minimum_coverage(check("x", OK, coverage=2), m).status is UNK
    assert apply_minimum_coverage(check("x", KO, coverage=2), m).status is KO
    assert apply_minimum_coverage(check("x", KO, coverage=1), m).status is UNK
    assert apply_minimum_coverage(check("x", KO, coverage=None), None).status is UNK
    assert apply_minimum_coverage(check("x", KO, coverage=0), None).status is UNK
    assert apply_minimum_coverage(check("x", OK, coverage=0), None).status is UNK
    assert apply_minimum_coverage(check("x", KO, coverage=1), None).status is KO
    with pytest.raises(ValueError):
        CoverageMinimum(positive=0)


# W2.7 profile -----------------------------------------------------------------------


def test_profile_unanimous_headline():
    p = paper_profile([(f"C{i}", PaperVerdict.REPRODUCED) for i in range(3)])
    assert p.headline == "3 of 3 drawn claims: REPRODUCED"
    assert not p.has_negative


def test_profile_mixed_and_negative():
    p = paper_profile(
        [("C1", PaperVerdict.REPRODUCED), ("C2", PaperVerdict.FRAGILE), ("C3", "INCONCLUSIVE")]
    )
    assert p.headline == "Mixed results: see the claims"
    assert p.has_negative
    assert [k for k, _ in p.claims] == ["C1", "C2", "C3"]
    assert p.total == 3 and p.counts["INCONCLUSIVE"] == 1


def test_profile_inconclusive_and_reproduced_is_never_called_reproduced():
    p = paper_profile([("C1", PaperVerdict.INCONCLUSIVE), ("C2", PaperVerdict.REPRODUCED)])
    assert "REPRODUCED" not in p.headline
    assert not p.has_negative


def test_profile_all_inconclusive_headline_says_inconclusive():
    p = paper_profile([("C1", PaperVerdict.INCONCLUSIVE), ("C2", PaperVerdict.INCONCLUSIVE)])
    assert p.headline == "2 of 2 drawn claims: INCONCLUSIVE"


def test_profile_needs_claims():
    with pytest.raises(ValueError):
        paper_profile([])


# WP2 package review --------------------------------------------------------------------------


def test_failure_established_by_the_attack_rule_survives_a_negative_minimum():
    seeds = seeds_attack([False, False, None, None, None], mean_holds=None)
    v = verdict(
        base(),
        [attack("seeds", seeds), attack("data_split", OK, coverage=3)],
        minimums={"seeds": CoverageMinimum(positive=5, negative=5)},
    )
    assert v.verdict is PaperVerdict.FRAGILE
    assert v.incomplete_coverage


def test_a_plain_fail_below_the_negative_minimum_still_gives_no_conclusion():
    v = verdict(
        base(),
        [attack("seeds", KO, coverage=2), attack("data_split", OK)],
        minimums={"seeds": CoverageMinimum(positive=5, negative=5)},
    )
    assert v.verdict is PaperVerdict.INCONCLUSIVE
