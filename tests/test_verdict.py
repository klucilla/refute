import pytest

from refute.core.verdict import (
    DiscoveryVerdict,
    PaperVerdict,
    Severity,
    TestResult,
    TestStatus,
    aggregate,
)

OK, KO, UNK = TestStatus.PASS, TestStatus.FAIL, TestStatus.INCONCLUSIVE
G, X, W = Severity.GATE, Severity.FATAL, Severity.WARNING


def r(name, status, severity):
    return TestResult(name, status, severity, "")


def test_enums_match_claude_md():
    assert [v.value for v in DiscoveryVerdict] == [
        "SURVIVED",
        "WEAKENED",
        "REFUTED",
        "INCONCLUSIVE",
    ]
    assert [v.value for v in PaperVerdict] == [
        "REPRODUCED",
        "FRAGILE",
        "NOT_REPRODUCED",
        "NOT_REPRODUCIBLE",
    ]
    assert "TRUE" not in {v.value for v in DiscoveryVerdict}


@pytest.mark.parametrize(
    ("results", "expected"),
    [
        ([r("snr", KO, G), r("a", KO, X)], DiscoveryVerdict.INCONCLUSIVE),
        ([r("snr", UNK, G), r("a", OK, X)], DiscoveryVerdict.INCONCLUSIVE),
        ([r("snr", OK, G), r("a", KO, X), r("b", UNK, X)], DiscoveryVerdict.REFUTED),
        ([r("snr", OK, G), r("a", KO, X), r("b", KO, W)], DiscoveryVerdict.REFUTED),
        ([r("snr", OK, G), r("a", UNK, X), r("b", KO, W)], DiscoveryVerdict.INCONCLUSIVE),
        ([r("snr", OK, G), r("a", OK, X), r("b", KO, W)], DiscoveryVerdict.WEAKENED),
        ([r("snr", OK, G), r("a", OK, X), r("b", OK, W)], DiscoveryVerdict.SURVIVED),
    ],
)
def test_aggregate_rules(results, expected):
    verdict, reason = aggregate(results)
    assert verdict is expected
    assert reason


def test_aggregate_requires_a_gate():
    with pytest.raises(ValueError):
        aggregate([r("a", OK, X)])


def test_round_trip():
    result = TestResult("x", KO, W, "msg", {"m": 1.0}, {"t": 2})
    assert TestResult.from_dict(result.to_dict()) == result
