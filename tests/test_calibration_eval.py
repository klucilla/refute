"""Self-claim evaluation, including the degeneracy guard, on fabricated results."""

import pytest

from conftest import calibration_claim, target_entry, targets_file, write_yaml
from refute.core.claim import load_claim
from refute.packs.tess.calibration import TessCalibrator


def _result(kind, verdict, rel_error):
    return {
        "target_key": f"TIC-{id(object())}",
        "target_kind": kind,
        "verdict": verdict,
        "status": "OK",
        "tests": [],
        "period_comparison": {"relative_error": rel_error},
    }


@pytest.fixture
def loaded(tmp_path):
    targets = [target_entry(i, "planet", 3.0) for i in range(1, 11)] + [
        target_entry(i, "false_positive", 2.0) for i in range(11, 14)
    ]
    write_yaml(tmp_path / "targets.yaml", targets_file(targets))
    claim = calibration_claim(
        10, 3, min_recovered_planets=9, min_flagged_false_positives=2, max_refuted_planets=1
    )
    return load_claim(write_yaml(tmp_path / "claim.yaml", claim))


def _evaluate(loaded, planets, fps, complete=True):
    return TessCalibrator().evaluate(loaded, planets + fps, complete)["self_claim"]


def test_pass(loaded):
    planets = [_result("planet", "SURVIVED", 1e-5)] * 9 + [_result("planet", "REFUTED", 0.5)]
    fps = [_result("false_positive", "REFUTED", None)] * 2 + [
        _result("false_positive", "SURVIVED", None)
    ]
    assert _evaluate(loaded, planets, fps)["result"] == "PASS"


def test_refute_everything_gauntlet_fails_the_claim(loaded):
    planets = [_result("planet", "REFUTED", 1e-5)] * 10
    fps = [_result("false_positive", "REFUTED", None)] * 3
    claim = _evaluate(loaded, planets, fps)
    assert claim["result"] == "FAIL"
    guard = next(c for c in claim["criteria"] if "degeneracy" in c["criterion"])
    assert guard["passed"] is False
    assert all(c["passed"] for c in claim["criteria"] if c is not guard)


def test_too_few_recovered_or_flagged_fails(loaded):
    planets = [_result("planet", "SURVIVED", 1e-5)] * 8 + [_result("planet", "SURVIVED", 0.01)] * 2
    fps = [_result("false_positive", "REFUTED", None)] * 3
    assert _evaluate(loaded, planets, fps)["result"] == "FAIL"
    planets = [_result("planet", "SURVIVED", 1e-5)] * 10
    fps = [_result("false_positive", "INCONCLUSIVE", None)] * 2 + [
        _result("false_positive", "REFUTED", None)
    ]
    assert _evaluate(loaded, planets, fps)["result"] == "FAIL"


def test_partial_or_mismatched_runs_are_not_evaluated(loaded):
    planets = [_result("planet", "SURVIVED", 1e-5)] * 10
    fps = [_result("false_positive", "REFUTED", None)] * 3
    assert _evaluate(loaded, planets, fps, complete=False)["result"] == "NOT_EVALUATED"
    assert _evaluate(loaded, planets[:9], fps)["result"] == "NOT_EVALUATED"


def test_error_counts_against_the_claim(loaded):
    error = {**_result("planet", "INCONCLUSIVE", None), "status": "ERROR"}
    planets = [_result("planet", "SURVIVED", 1e-5)] * 8 + [error, error]
    fps = [_result("false_positive", "REFUTED", None)] * 3
    assert _evaluate(loaded, planets, fps)["result"] == "FAIL"
