"""The version rule of the corrections (map Amendment 17; the maintainer's decision of
2026-10-18): version 1 is the legacy block, always the M3 path; version 2 with enabled true is M4;
no default changes. The marker in the verdict record says what ran, not what the plan asked for.
"""

import pytest

from refute.core.claim import load_claim
from refute.packs.tess import synthetic
from refute.packs.tess.params import CorrectionsParams, TessTestPlan
from refute.packs.tess.pipeline import analyze_data, build_result

V02_CLAIM = "calibration/v0.2/self_claim.yaml"


@pytest.mark.parametrize(
    ("block", "active"),
    [
        (None, False),
        ({"version": 1}, False),
        ({"version": 1, "enabled": True}, False),
        ({"version": 2}, False),
        ({"version": 2, "enabled": True}, True),
    ],
)
def test_the_version_matrix(block, active):
    plan = synthetic.fast_plan_dict()
    if block is not None:
        plan["gauntlet"] = {"corrections": block}
    assert TessTestPlan.model_validate(plan).gauntlet.corrections.active is active


def test_no_default_of_the_block_changes():
    d = CorrectionsParams()
    assert (d.version, d.enabled, d.r_min, d.b_min) == (1, False, 20, 20)
    with pytest.raises(ValueError):
        CorrectionsParams(version=3)


def _record(plan):
    data = synthetic.scenario_data("planet", 0)
    analysis = analyze_data(data, plan)
    target = {"key": "synthetic", "tic_id": 1, "kind": "planet", "name": "planet-0"}
    return build_result(target, data, plan, analysis, {"pass_criteria": {}}), analysis


def _claim_plan(corrections=None):
    """The test plan of the v0.2 calibration claim (a legacy claim, without the block), with the
    fast search of the synthetic suite, and the block when given."""
    loaded = load_claim(synthetic_root() / V02_CLAIM)
    plan = loaded.canonical()["test_plan"]
    plan["search"] = {**plan["search"], **synthetic.FAST_SEARCH}
    if corrections is not None:
        plan["gauntlet"]["corrections"] = corrections
    return TessTestPlan.model_validate(plan)


def synthetic_root():
    from pathlib import Path

    return Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def new_version():
    return _record(_claim_plan({"version": 2, "enabled": True}))


@pytest.fixture(scope="module")
def legacy():
    return _record(_claim_plan())


def test_a_claim_with_the_new_version_runs_the_corrected_path(new_version):
    record, analysis = new_version
    assert record["corrections"]["version"] == 2
    executed = record["corrections"]["executed"]
    assert {"a1_noise", "bls_beta_gate", "trapezoid_timing"} <= set(executed)
    assert "m4_holdout" in executed
    snr = next(t for t in analysis.tests if t.name == "snr")
    assert "beta_d" in snr.metrics  # the gate of method (a) ran


def test_a_claim_without_the_block_stays_on_m3(legacy):
    record, analysis = legacy
    assert "corrections" not in record
    assert record["test_plan"]["gauntlet"]["corrections"]["version"] == 1
    snr = next(t for t in analysis.tests if t.name == "snr")
    assert "beta_d" not in snr.metrics
    assert all("corrections_path" not in r.metrics for r in analysis.holdout.rounds)


def test_m3_does_not_run_on_the_new_path(monkeypatch):
    import refute.packs.tess.holdout as holdout
    import refute.packs.tess.pipeline as pipeline

    calls = {"box_scan": 0, "m3_holdout": 0}
    real_scan, real_measure = pipeline.measure_transit_times, holdout._measure

    def scan(*a, **k):
        calls["box_scan"] += 1
        return real_scan(*a, **k)

    def measure(*a, **k):
        calls["m3_holdout"] += 1
        return real_measure(*a, **k)

    monkeypatch.setattr(pipeline, "measure_transit_times", scan)
    monkeypatch.setattr(holdout, "_measure", measure)
    _record(_claim_plan({"version": 2, "enabled": True}))
    assert calls == {"box_scan": 0, "m3_holdout": 0}
    _record(_claim_plan({"version": 1, "enabled": True}))  # the legacy version: M3
    assert calls["box_scan"] > 0 and calls["m3_holdout"] > 0
