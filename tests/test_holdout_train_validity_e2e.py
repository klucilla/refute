"""v0.2.1 H4 end to end on synthetic data: cases B1-B6 (rounds of chosen scenarios) and
D1-D3 (property and regression over every scenario) of
docs/validation/v0.2.1/H4-acceptance.md.

Every case first checks its premise; premises about today's behavior use the switch
``require_valid_train: false``. A premise that does not hold fails the test.
"""

from dataclasses import replace

import pytest

from refute.core.runner import default_workers, run_processes
from refute.core.verdict import TestStatus
from refute.packs.tess import holdout, synthetic
from refute.packs.tess.holdout import REASON_DURATION_RATIO, REASON_TRAIN_SNR
from refute.packs.tess.params import TessTestPlan
from refute.packs.tess.search import search_period

DEVELOPMENT_SEEDS = tuple(range(10))
SCENARIOS = (*synthetic.SCENARIOS, "fp_variability_dominates", "variability_train_only")
ON, OFF = {}, {"require_valid_train": False}
# Scenarios allowed to have train-validity reasons (D3).
WITH_REASONS = {
    "noise",
    "vanishing",
    "sinusoid",
    "fp_variability_dominates",
    "variability_train_only",
}


@pytest.fixture(scope="module")
def outcomes():
    tasks = [
        {"name": name, "seed": seed, "holdout": guard}
        for name in SCENARIOS
        for seed in DEVELOPMENT_SEEDS
        for guard in (ON, OFF)
    ]
    workers = max(1, min(len(tasks), default_workers()))
    results = run_processes(synthetic.holdout_scenario_seed, tasks, workers)
    return {
        (t["name"], t["seed"], "on" if t["holdout"] == ON else "off"): r
        for t, r in zip(tasks, results, strict=True)
    }


def _round(outcome, year):
    matches = [r for r in outcome.rounds if r.hidden_year == year]
    assert len(matches) == 1, f"no round hiding {year}"
    return matches[0]


def _reasons(round_):
    return round_.metrics["train_validity"]["reasons"]


def _train(round_):
    return round_.metrics["train_candidate"]


@pytest.mark.parametrize("seed", range(5))
def test_b1_variability_in_train_only_is_inconclusive(outcomes, seed):
    on = outcomes[("variability_train_only", seed, "on")]
    off = outcomes[("variability_train_only", seed, "off")]
    before, after = _round(off, 2020), _round(on, 2020)
    train = _train(before)
    assert train["period"] == pytest.approx(synthetic.SINUSOID_PERIOD, rel=1e-3), (
        f"premise: the 2020 round trained on {train['period']} d"
    )
    assert before.status is TestStatus.FAIL, f"premise: the 2020 round is {before.status}"
    assert after.status is TestStatus.INCONCLUSIVE
    assert _reasons(after) == [REASON_DURATION_RATIO]
    assert after.metrics["train_validity"]["hidden_window_fraction"] is None  # stopped at (b)
    assert after.access_log == []
    # (c) would not have triggered: measured with the guard off, where it is reported.
    assert before.metrics["train_validity"]["hidden_window_fraction"] < 0.5
    for year in (2018, 2019):  # valid train: outside H4, unchanged
        assert _reasons(_round(on, year)) == []
        assert _round(on, year).status is _round(off, year).status


def _vanishing_2020(monkeypatch, seed, guard):
    def search_double(lc, params):
        result = search_period(lc, params)
        if 2020 in lc.years:  # the double changes only the round that hides 2020
            return result
        return replace(result, candidate=replace(result.candidate, snr=6.9))

    monkeypatch.setattr(holdout, "search_period", search_double)
    plan = synthetic.fast_plan_dict()
    plan["gauntlet"] = {"holdout_by_year": guard}
    data = synthetic.scenario_data("vanishing", seed)
    outcome = holdout.run_holdout(data.lc, data.sectors, TessTestPlan.model_validate(plan))
    return _round(outcome, 2020)


@pytest.mark.parametrize("seed", range(4))  # seed 4 excluded (declared in H4-acceptance.md)
def test_b2_train_below_the_gate_turns_a_fail_into_inconclusive(monkeypatch, seed):
    before = _vanishing_2020(monkeypatch, seed, OFF)
    assert _train(before)["snr"] == 6.9
    assert before.status is TestStatus.FAIL, f"premise: the 2020 round is {before.status}"
    after = _vanishing_2020(monkeypatch, seed, ON)
    assert after.status is TestStatus.INCONCLUSIVE
    assert _reasons(after) == [REASON_TRAIN_SNR]
    assert after.access_log == []


@pytest.mark.parametrize("seed", DEVELOPMENT_SEEDS)
def test_b3_low_train_snr_is_reported(outcomes, seed):
    cases = [(outcomes[("noise", seed, g)], year) for g in ("on", "off") for year in (2018, 2020)]
    cases += [(outcomes[("vanishing", seed, g)], 2018) for g in ("on", "off")]
    for outcome, year in cases:
        round_ = _round(outcome, year)
        assert _train(round_)["snr"] < 7.1, f"premise: train SNR {_train(round_)['snr']}"
        assert round_.status is TestStatus.INCONCLUSIVE
        assert REASON_TRAIN_SNR in _reasons(round_)


@pytest.mark.parametrize("seed", range(5))
@pytest.mark.parametrize("name", ["sinusoid", "fp_variability_dominates"])
def test_b4_variability_no_longer_passes(outcomes, name, seed):
    on, off = outcomes[(name, seed, "on")], outcomes[(name, seed, "off")]
    for before in off.rounds:
        train = _train(before)
        assert train["duration"] / train["period"] > 0.2, "premise: D/P"
        assert before.status is TestStatus.PASS, f"premise: round is {before.status}"
        after = _round(on, before.hidden_year)
        assert after.status is TestStatus.INCONCLUSIVE
        assert REASON_DURATION_RATIO in _reasons(after)
        assert after.access_log == []


@pytest.mark.parametrize("seed", range(5))
@pytest.mark.parametrize("name", ["planet", "planet_three_years"])
def test_b5_planets_are_unchanged(outcomes, name, seed):
    on, off = outcomes[(name, seed, "on")], outcomes[(name, seed, "off")]
    assert on.test.status is off.test.status
    for after in on.rounds:
        assert _reasons(after) == []
        assert after.status is _round(off, after.hidden_year).status


@pytest.mark.parametrize("seed", range(4))  # seed 4 excluded (declared in H4-acceptance.md)
def test_b6_signal_absent_in_hidden_year_still_fails(outcomes, seed):
    before = _round(outcomes[("vanishing", seed, "off")], 2020)
    assert before.status is TestStatus.FAIL, f"premise: the 2020 round is {before.status}"
    after = _round(outcomes[("vanishing", seed, "on")], 2020)
    assert after.status is TestStatus.FAIL
    assert _reasons(after) == []


# --- D: property and regression -----------------------------------------------------------


@pytest.mark.parametrize("name", SCENARIOS)
def test_d_guard_never_creates_a_pass_or_a_fail(outcomes, name):
    for seed in DEVELOPMENT_SEEDS:
        on, off = outcomes[(name, seed, "on")], outcomes[(name, seed, "off")]
        assert [r.hidden_year for r in on.rounds] == [r.hidden_year for r in off.rounds]
        for after in on.rounds:
            before = _round(off, after.hidden_year)
            # D1: unchanged or INCONCLUSIVE.
            assert after.status in (before.status, TestStatus.INCONCLUSIVE)
            # D3: only the expected scenarios have reasons; in noise and vanishing only
            # on rounds that are already INCONCLUSIVE without the guard.
            if _reasons(after):
                assert name in WITH_REASONS, (name, seed, after.hidden_year, _reasons(after))
                if name in ("noise", "vanishing"):
                    assert before.status is TestStatus.INCONCLUSIVE
        # D2: a holdout FAIL with the guard is a FAIL without it.
        if on.test.status is TestStatus.FAIL:
            assert off.test.status is TestStatus.FAIL


# --- Correlated noise (docs/validation/v0.2.1/reopen/correlated-noise-acceptance.md, H4) -----

CN_SEEDS = tuple(range(5))
CN_VANISHING_SEEDS = tuple(range(10))


@pytest.fixture(scope="module")
def correlated():
    keys = [(name, seed) for name in SCENARIOS for seed in CN_SEEDS]
    keys += [("vanishing", seed) for seed in CN_VANISHING_SEEDS if seed not in CN_SEEDS]
    tasks = [
        {"name": name, "seed": seed, "holdout": guard, "noise": "correlated"}
        for name, seed in keys
        for guard in (ON, OFF)
    ]
    workers = max(1, min(len(tasks), default_workers()))
    results = run_processes(synthetic.holdout_scenario_seed, tasks, workers)
    return {
        (t["name"], t["seed"], "on" if t["holdout"] == ON else "off"): r
        for t, r in zip(tasks, results, strict=True)
    }


@pytest.mark.parametrize("name", SCENARIOS)
def test_cn_h4_m1_guard_never_creates_a_pass_or_a_fail(correlated, name):
    for seed in CN_SEEDS:
        on, off = correlated[(name, seed, "on")], correlated[(name, seed, "off")]
        assert [r.hidden_year for r in on.rounds] == [r.hidden_year for r in off.rounds]
        for after in on.rounds:
            before = _round(off, after.hidden_year)
            assert after.status in (before.status, TestStatus.INCONCLUSIVE), (seed, after)
        if on.test.status is TestStatus.FAIL:
            assert off.test.status is TestStatus.FAIL, seed


def _cn_m2_premise(correlated, seed):
    before = _round(correlated[("variability_train_only", seed, "off")], 2020)
    return _train(before)["period"] == pytest.approx(synthetic.SINUSOID_PERIOD, rel=1e-2)


def test_cn_h4_m2_variability_in_train_only_is_inconclusive(correlated):
    looked = 0
    for seed in CN_SEEDS:
        if not _cn_m2_premise(correlated, seed):
            continue
        looked += 1
        after = _round(correlated[("variability_train_only", seed, "on")], 2020)
        assert after.status is TestStatus.INCONCLUSIVE, seed
        assert REASON_DURATION_RATIO in _reasons(after), seed
        assert after.access_log == [], seed
    assert looked >= 1, "non-empty: the premise holds on no seed"


@pytest.mark.parametrize("name", ["sinusoid", "fp_variability_dominates"])
def test_cn_h4_m3_long_train_boxes_are_inconclusive(correlated, name):
    looked = 0
    for seed in CN_SEEDS:
        on, off = correlated[(name, seed, "on")], correlated[(name, seed, "off")]
        for before in off.rounds:
            train = _train(before)
            if train is None or train["duration"] / train["period"] <= 0.2:
                continue
            looked += 1
            after = _round(on, before.hidden_year)
            assert after.status is TestStatus.INCONCLUSIVE, (seed, before.hidden_year)
            assert REASON_DURATION_RATIO in _reasons(after), (seed, before.hidden_year)
            assert after.access_log == [], (seed, before.hidden_year)
    assert looked >= 1, "non-empty: no round trained a box above duration/period 0.2"


def _cn_m4_premise(correlated, seed):
    before = _round(correlated[("vanishing", seed, "off")], 2020)
    return before.status is TestStatus.FAIL and _reasons(before) == []


def test_cn_h4_m4_a_valid_fail_stays_a_fail(correlated):
    looked = 0
    for seed in CN_VANISHING_SEEDS:
        if not _cn_m4_premise(correlated, seed):
            continue
        looked += 1
        after = _round(correlated[("vanishing", seed, "on")], 2020)
        assert after.status is TestStatus.FAIL, seed
        assert _reasons(after) == [], seed
    assert looked >= 1, "non-empty: no valid failing round"


@pytest.mark.parametrize("seed", CN_SEEDS)
@pytest.mark.parametrize("name", ["planet", "planet_three_years"])
def test_cn_h4_e1_planets_are_unchanged(correlated, name, seed):
    on, off = correlated[(name, seed, "on")], correlated[(name, seed, "off")]
    assert on.test.status is off.test.status
    for after in on.rounds:
        assert _reasons(after) == []
        assert after.status is _round(off, after.hidden_year).status


@pytest.mark.parametrize("name", SCENARIOS)
def test_cn_h4_e2_reasons_only_where_expected(correlated, name):
    for seed in CN_SEEDS:
        on, off = correlated[(name, seed, "on")], correlated[(name, seed, "off")]
        for after in on.rounds:
            if _reasons(after):
                assert name in WITH_REASONS, (seed, after.hidden_year, _reasons(after))
                if name in ("noise", "vanishing"):
                    assert _round(off, after.hidden_year).status is TestStatus.INCONCLUSIVE


@pytest.mark.parametrize("seed", CN_SEEDS)
def test_cn_h4_e3_premise_variability_train_only(correlated, seed):
    train = _train(_round(correlated[("variability_train_only", seed, "off")], 2020))
    assert _cn_m2_premise(correlated, seed), f"the 2020 round trained on {train['period']} d"


@pytest.mark.parametrize("seed", CN_VANISHING_SEEDS)
def test_cn_h4_e3_premise_vanishing_fails_with_a_valid_train(correlated, seed):
    before = _round(correlated[("vanishing", seed, "off")], 2020)
    assert _cn_m4_premise(correlated, seed), (before.status, _reasons(before))
