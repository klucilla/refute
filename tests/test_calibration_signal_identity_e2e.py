"""v0.2.1 H7 end to end on synthetic data: full analysis, build_result, then the
calibrator. Cases B1-B6 of docs/validation/v0.2.1/H7-acceptance.md.

Every case first checks its premise (which period the search found). A premise that
does not hold fails the test; it is never skipped.
"""

from types import SimpleNamespace

import pytest

from conftest import target_entry
from refute.core.runner import default_workers, run_processes
from refute.packs.tess import synthetic
from refute.packs.tess.calibration import TessCalibrator
from refute.packs.tess.params import TessTestPlan
from refute.packs.tess.pipeline import build_result

TOLERANCE = 0.001
FACTORS = (1.0, 2.0, 0.5)
# Development seeds used end to end (subset of the development set 0-9).
SEEDS = (0, 1, 2)
# Periods injected by synthetic.scenario_data.
INJECTED = {
    "fp_variability_dominates": synthetic.FP_VARIABILITY_PERIOD,
    "eb_secondary": 2.9,
    "eb_odd_even": 1.8,
    "eb_equal": 1.6,
    "planet": synthetic.PLANET.period,
    "planet_three_years": synthetic.PLANET.period,
}
# A published period that is not P, 2P or P/2 of the injected eb_secondary period.
WRONG_PUBLISHED = 2.9 * 1.37


@pytest.fixture(scope="module")
def analyses():
    tasks = [(name, seed) for name in INJECTED for seed in SEEDS]
    workers = max(1, min(len(tasks), default_workers()))
    results = run_processes(synthetic.analyze_scenario_seed, tasks, workers)
    return dict(zip(tasks, results, strict=True))


def _result(analyses, name, seed, kind, published):
    criteria = {"pass_criteria": {"period_tolerance": TOLERANCE}}
    plan = TessTestPlan.model_validate(synthetic.fast_plan_dict())
    target = target_entry(1, kind, published, name=name)
    data = synthetic.scenario_data(name, seed)
    return build_result(target, data, plan, analyses[(name, seed)], criteria)


def _summary(results, flag):
    criteria = {
        "period_tolerance": TOLERANCE,
        "expected_planets": 1,
        "min_recovered_planets": 0,
        "expected_false_positives": 1,
        "min_flagged_false_positives": 0,
        "max_refuted_planets": 1,
        "flag_requires_signal_recovery": flag,
    }
    claim = SimpleNamespace(pass_criteria=criteria, id="c", hypothesis="h", definitions={})
    loaded = SimpleNamespace(claim=claim, attachment_by_role=lambda _role: None)
    return TessCalibrator().evaluate(loaded, results, complete=True)


def _found(result):
    found = result["period_comparison"]["found_period_days"]
    assert found is not None, f"premise: the search found no candidate for {result['target_name']}"
    return found


def _matches(found, period, factors):
    return any(abs(found - f * period) / (f * period) <= TOLERANCE for f in factors)


@pytest.mark.parametrize("seed", SEEDS)
def test_b1_variability_dominates_signal_not_recovered(analyses, seed):
    name = "fp_variability_dominates"
    result = _result(analyses, name, seed, "false_positive", INJECTED[name])
    found = _found(result)
    assert not _matches(found, INJECTED[name], FACTORS), (
        f"premise: the search found {found} d, a multiple of the eclipse period"
    )
    on, off = _summary([result], True), _summary([result], False)
    assert on["targets"][0]["signal_recovered"] is False
    assert on["self_claim"]["criteria"][1]["value"] == 0
    assert on["information"]["false_positives_signal_not_recovered"]["count"] == 1
    # Whatever the verdict, the v0.2 definition would have counted it if it is REFUTED.
    counted_before = off["self_claim"]["criteria"][1]["value"]
    assert counted_before == (result["verdict"] == "REFUTED")
    assert on["information"]["flagged_without_signal_identity"] == counted_before


@pytest.mark.parametrize("seed", SEEDS)
def test_b2_wrong_published_period_is_not_recovered(analyses, seed):
    right = _result(analyses, "eb_secondary", seed, "false_positive", INJECTED["eb_secondary"])
    wrong = _result(analyses, "eb_secondary", seed, "false_positive", WRONG_PUBLISHED)
    found = _found(wrong)
    assert _matches(found, INJECTED["eb_secondary"], (1.0,)), f"premise: found {found} d"
    assert not _matches(found, WRONG_PUBLISHED, FACTORS)
    assert wrong["verdict"] == right["verdict"]
    on = _summary([wrong], True)
    assert on["targets"][0]["signal_recovered"] is False
    assert on["self_claim"]["criteria"][1]["value"] == 0


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("name", ["eb_secondary", "eb_odd_even"])
def test_b3_correct_published_period_counts_as_before(analyses, name, seed):
    result = _result(analyses, name, seed, "false_positive", INJECTED[name])
    found = _found(result)
    assert _matches(found, INJECTED[name], (1.0,)), f"premise: found {found} d"
    assert result["verdict"] == "REFUTED"
    on, off = _summary([result], True), _summary([result], False)
    assert on["targets"][0]["signal_recovered"] is True
    assert on["self_claim"]["criteria"][1]["value"] == 1
    assert off["self_claim"]["criteria"][1]["value"] == 1


@pytest.mark.parametrize("seed", SEEDS)
def test_b4_equal_eclipses_found_at_an_allowed_alias_are_recovered(analyses, seed):
    result = _result(analyses, "eb_equal", seed, "false_positive", INJECTED["eb_equal"])
    found = _found(result)
    assert _matches(found, INJECTED["eb_equal"], (1.0, 0.5)), f"premise: found {found} d"
    on = _summary([result], True)
    assert on["targets"][0]["signal_recovered"] is True


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize(("multiple", "factor"), [(2.0, 0.5), (0.5, 2.0)])
def test_b6_forced_aliases_are_recovered(analyses, multiple, factor, seed):
    # Amendment 1: the published period is 2x (found = P/2) or 1/2x (found = 2P) the
    # injected one, so the alias factors are exercised whichever alias the search finds.
    published = INJECTED["eb_secondary"] * multiple
    result = _result(analyses, "eb_secondary", seed, "false_positive", published)
    found = _found(result)
    assert _matches(found, INJECTED["eb_secondary"], (1.0,)), f"premise: found {found} d"
    matching = [f for f in FACTORS if _matches(found, published, (f,))]
    assert matching == [factor], f"premise: found {found} d matches factors {matching}"
    assert result["verdict"] == "REFUTED"
    on = _summary([result], True)
    assert on["targets"][0]["signal_recovered"] is True
    assert on["self_claim"]["criteria"][1]["value"] == 1


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("name", ["planet", "planet_three_years"])
def test_b5_planets_do_not_depend_on_the_flag(analyses, name, seed):
    result = _result(analyses, name, seed, "planet", INJECTED[name])
    _found(result)
    on, off = _summary([result], True), _summary([result], False)
    for index in (0, 2):
        assert on["self_claim"]["criteria"][index] == off["self_claim"]["criteria"][index]
    assert on["targets"][0]["recovered"] == off["targets"][0]["recovered"]
    assert on["targets"][0]["signal_recovered"] is None
