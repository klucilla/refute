"""The v0.5 acceptance harness (docs/validation/v0.5/acceptance/acceptance.py): its binomial
bands, its seed rule and its decision rules, without running any case."""

from __future__ import annotations

import hashlib
import importlib.util
import math
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "docs" / "validation" / "v0.5" / "acceptance" / "acceptance.py"


@pytest.fixture(scope="module")
def acc():
    spec = importlib.util.spec_from_file_location("v05_acceptance", PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _cdf(n, p, k):
    return sum(math.comb(n, j) * p**j * (1 - p) ** (n - j) for j in range(k + 1))


def test_quantiles_follow_the_conventions(acc):
    # the smallest k whose cumulative probability reaches q
    for n, p in ((200, 0.95), (200, 0.0027), (12, 0.95), (400, 0.5)):
        lo = acc.lower_quantile(n, p)
        hi = acc.upper_quantile(n, p)
        assert _cdf(n, p, lo) >= 0.025 and (lo == 0 or _cdf(n, p, lo - 1) < 0.025)
        assert _cdf(n, p, hi) >= 0.975 and (hi == 0 or _cdf(n, p, hi - 1) < 0.975)
    assert acc.lower_quantile(200, 0.95) == 184
    assert acc.upper_quantile(200, 0.0027) == 2


def test_seed_rule_is_the_declared_sha256(acc):
    expected = int(hashlib.sha256(b"refute-v05-accept:1.8-odd_even-a:red:7").hexdigest()[:16], 16)
    assert acc.seed_of("accept", "1.8-odd_even-a:red", 7) == expected
    assert acc.seed_of("dev", "1.8-odd_even-a:red", 7) != expected


def _rows(statuses, severity="fatal", **extra):
    return [
        {"i": i, "status": s, "severity": severity, "constructed": True, **extra}
        for i, s in enumerate(statuses)
    ]


def test_rate_rules_and_validity(acc):
    rows = _rows(["FAIL"] * 184 + ["PASS"] * 16)
    assert acc.decide("1.8-odd_even-a", rows, 200)["result"] == "PASS"
    rows = _rows(["FAIL"] * 183 + ["PASS"] * 17)
    assert acc.decide("1.8-odd_even-a", rows, 200)["result"] == "FAIL"
    # an error, a missing trial or an unconstructed trial makes the case INVALID
    rows = _rows(["FAIL"] * 199 + ["ERROR"])
    assert acc.decide("1.8-odd_even-a", rows, 200)["result"] == "INVALID"
    assert acc.decide("1.8-odd_even-a", _rows(["FAIL"] * 199), 200)["result"] == "INVALID"
    rows = _rows(["FAIL"] * 200)
    rows[0]["constructed"] = False
    assert acc.decide("1.8-odd_even-a", rows, 200)["result"] == "INVALID"


def test_severity_is_enforced(acc):
    rows = _rows(["FAIL"] * 200, severity="warning")
    out = acc.decide("1.8-odd_even-a", rows, 200)
    assert out["result"] == "FAIL" and len(out["severity_wrong_trials"]) == 200


def test_never_pass_and_else_pass(acc):
    assert acc.decide("1.8-odd_even-b", _rows(["INCONCLUSIVE"] * 5), 5)["result"] == "PASS"
    rows = _rows(["INCONCLUSIVE"] * 4 + ["PASS"])
    assert acc.decide("1.8-odd_even-b", rows, 5)["result"] == "FAIL"
    rows = _rows(["PASS"] * 199 + ["INCONCLUSIVE"])
    assert acc.decide("4.5-centroid-c", rows, 200)["result"] == "FAIL"
    assert acc.decide("4.5-centroid-c", _rows(["PASS"] * 200), 200)["result"] == "PASS"


def test_pulls_never_shrink_the_denominator(acc):
    rows = [
        {"i": i, "status": "MEASURED", "constructed": True, "event_pull": 0.0, "group_pull": 0.0}
        for i in range(4)
    ]
    rows[1]["event_pull"] = None
    assert acc.decide("1.10-pulls", rows, 4)["result"] == "INVALID"


def test_the_matrix(acc):
    assert acc.noises_for("4.6-centroid-opposite") == ("none",)
    assert "trend" not in acc.noises_for("3.8-sinusoid-c")
    assert acc.noises_for("1.8-odd_even-a") == ("white", "red", "trend")
    assert acc.trials_for("1.10-pulls", 200) == 400
    assert acc.trials_for("1.8-odd_even-a", 200) == 200
    for name, (fn, _kind, rule, _param) in acc.CASES.items():
        assert rule in {
            "fail_at_least",
            "false_fail_at_most",
            "false_fail_else_pass",
            "never_pass",
            "disagree_at_least",
            "pulls",
            "alias",
        }, name
        assert fn in acc.SEVERITY or rule == "pulls", name
