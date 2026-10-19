"""The ``R_min`` study's timing lot (map Amendment 26, 6), written before the code: the 80 targets
of the declared rule, and only times leave a target's evaluation."""

import importlib
import sys
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
POPULATION = ROOT / "docs" / "validation" / "v0.2.1" / "population"


@pytest.fixture(scope="module")
def study():
    sys.path.insert(0, str(POPULATION))
    return importlib.import_module("rmin_study")


def test_the_lot_is_the_declared_rule(study):
    cases = study.timing_cases()
    assert len(cases) == 80
    assert len({(c["noise"], c["id"]) for c in cases}) == 80
    groups = Counter(study.group_of(c) for c in cases)
    assert groups == {
        "white, no variability": 20,
        "white, variability": 20,
        "AR(1), no variability": 20,
        "AR(1), variability": 20,
    }
    for group in groups:
        rows = [c for c in cases if study.group_of(c) == group]
        assert Counter(c["band"] for c in rows) == {"near": 10, "measurable": 10}, group
        mechanisms = Counter(c["mechanism"] for c in rows)
        if group.endswith("no variability"):
            assert mechanisms == {"two_years": 10, "three_years": 5, "few_train": 5}, group
        else:
            assert mechanisms == {"variability_some_years": 20}, group
    assert all(c["seed"] for c in cases)
    # the prefix is the lot's own: no case shares a seed with the development population
    dev = {c["seed"] for c in study.pv2.population_cases("dev")}
    assert not dev & {c["seed"] for c in cases}


def test_only_times_leave_a_target(study, monkeypatch):
    """With the measurement replaced by a stub (the code path, not the science, is under test):
    the returned keys are the target, its group, the times and the worker's block."""
    import refute.packs.tess.holdout as holdout
    from refute.packs.tess import synthetic
    from refute.packs.tess.params import TessTestPlan

    plan_dict = synthetic.fast_plan_dict()
    plan_dict["gauntlet"] = {"corrections": {"version": 2, "enabled": True, "r_min": 8}}
    plan = TessTestPlan.model_validate(plan_dict)
    monkeypatch.setattr(
        study.v3,
        "STATE",
        {"problem": None, "identity": {"path": "p", "sha256": "0" * 64, "block_sha256": "1" * 64}},
    )
    monkeypatch.setattr(study.v3, "_plan", lambda: plan)
    calls = []

    def fake_measurement(raw, sectors, year, plan, *, identity, twin_model):
        calls.append((year, twin_model.shape == raw.flux.shape))
        return {"secret": "a scientific value"}

    monkeypatch.setattr(holdout, "calibration_measurement", fake_measurement)
    monkeypatch.setattr(
        holdout,
        "derive_round",
        lambda rec, r, b, s, m: {"status": "PASS", "eligible": True, "secret": 1},
    )
    case = study.timing_cases()[0]
    out = study.time_target(case)
    assert set(out) == {
        "target",
        "group",
        "generation_seconds",
        "scenarios",
        "pid",
        "identity_block_sha256",
    }
    assert out["target"] == f"{study.TIMING_PREFIX}/{case['id']}"
    assert set(out["scenarios"]) == set(study.SCENARIOS)
    for times in out["scenarios"].values():
        assert set(times) == {"rounds", "aggregation", "total"}
        assert all(isinstance(v, float) and v >= 0 for v in times.values())
    assert "secret" not in repr(out)
    assert calls and all(ok for _, ok in calls)  # every round with the scenario's twin model
    assert len(calls) == 3 * len({y for y, _ in calls})  # each year in each of the scenarios


def test_a_target_without_the_configuration_is_refused(study, monkeypatch):
    monkeypatch.setattr(study.v3, "STATE", {"problem": "not loaded", "identity": None})
    with pytest.raises(RuntimeError):
        study.time_target(study.timing_cases()[0])
