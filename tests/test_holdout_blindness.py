"""v0.2.1 H4 blindness: replacing the hidden year's data must not change any decision
taken before its windows are read. Cases C1-C2 of
docs/validation/v0.2.1/H4-acceptance.md."""

import inspect

import pytest

from refute.core.canonical import canonical_bytes
from refute.core.io import to_jsonable
from refute.core.runner import default_workers, run_processes
from refute.core.verdict import TestStatus
from refute.packs.tess import holdout, synthetic
from refute.packs.tess.params import TessTestPlan

SEEDS = (0, 1, 2)
SCENARIOS = ("planet", "vanishing", "variability_train_only", "sinusoid")
VARIANTS = ("noise", "signal", "nothing")
# Everything in a round result that is decided before the hidden windows are read.
PRE_READ_METRICS = (
    "train_candidate",
    "n_transit_times",
    "train_validity",
    "n_predicted_transits",
    "max_timing_sigma_days",
    "hidden_detrend_window_days",
)


@pytest.fixture(scope="module")
def outcomes():
    tasks = []
    for name in SCENARIOS:
        for seed in SEEDS:
            tasks.append({"name": name, "seed": seed, "holdout": {}})
            years = synthetic.scenario_data(name, seed).lc.years
            for year in years:
                for variant in VARIANTS:
                    tasks.append(
                        {"name": name, "seed": seed, "holdout": {}, "replace": (year, variant)}
                    )
    workers = max(1, min(len(tasks), default_workers()))
    results = run_processes(synthetic.holdout_scenario_seed, tasks, workers)
    return {
        (t["name"], t["seed"], t.get("replace")): r for t, r in zip(tasks, results, strict=True)
    }


def _round(outcome, year):
    return next(r for r in outcome.rounds if r.hidden_year == year)


def _canonical(value):
    return canonical_bytes(to_jsonable(value))


def _pre_read(round_):
    return _canonical(
        {
            "metrics": {k: round_.metrics.get(k) for k in PRE_READ_METRICS},
            "train_ephemeris": round_.train_ephemeris,
            "windows": round_.windows,
        }
    )


@pytest.mark.parametrize("variant", VARIANTS)
@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("name", SCENARIOS)
def test_c1_replacing_the_hidden_year_changes_no_pre_read_decision(outcomes, name, seed, variant):
    original = outcomes[(name, seed, None)]
    decided_before_read = 0
    for year in [r.hidden_year for r in original.rounds]:
        before = _round(original, year)
        after = _round(outcomes[(name, seed, (year, variant))], year)
        assert "train_validity" in before.metrics
        assert _pre_read(after) == _pre_read(before), (name, seed, year, variant)
        if not before.access_log:
            # Decided from the train side: the whole round is identical and unread.
            decided_before_read += 1
            assert before.status is TestStatus.INCONCLUSIVE
            assert after.access_log == []
            assert _canonical(after.to_dict()) == _canonical(before.to_dict())
    if name in ("sinusoid", "variability_train_only"):
        assert decided_before_read >= 1, "premise: some round is decided before the read"


def test_c1_the_replacement_reaches_the_hidden_year(outcomes):
    # Control: the replaced data are really used where the hidden year is read.
    read = [r for r in outcomes[("planet", 0, None)].rounds if r.access_log]
    assert read, "premise: some planet round reads its hidden year"
    year = read[0].hidden_year
    replaced = _round(outcomes[("planet", 0, (year, "nothing"))], year)
    assert replaced.access_log
    assert replaced.metrics["hidden_snr"] != read[0].metrics["hidden_snr"]


def test_c2_the_pre_read_step_receives_no_hidden_flux():
    params = list(inspect.signature(holdout.plan_round).parameters)
    assert params == ["train_raw", "hidden_spans", "hidden_year", "plan"]


class _NoHiddenYear:
    def __init__(self, *args, **kwargs):
        raise AssertionError("HiddenYear constructed")


def test_c2_an_invalid_train_never_builds_the_hidden_year(monkeypatch):
    plan = TessTestPlan.model_validate(synthetic.fast_plan_dict())
    sinusoid = synthetic.scenario_data("sinusoid", 0)
    variability = synthetic.scenario_data("variability_train_only", 0)
    planet = synthetic.scenario_data("planet", 0)
    monkeypatch.setattr(holdout, "HiddenYear", _NoHiddenYear)
    for data, year in ((sinusoid, 2018), (sinusoid, 2020), (variability, 2020)):
        result = holdout._round(data.lc, data.sectors, year, plan)
        assert result.status is TestStatus.INCONCLUSIVE
        assert result.metrics["train_validity"]["reasons"]
    # Control: the replacement is live, a valid round does try to build it.
    with pytest.raises(AssertionError, match="HiddenYear constructed"):
        holdout._round(planet.lc, planet.sectors, 2020, plan)
