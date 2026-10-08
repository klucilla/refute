"""Calibration v0.2: 'flagged' can exclude tests (e.g. eb_catalog); the guard cannot."""

from types import SimpleNamespace

from refute.packs.tess.calibration import TessCalibrator, signal_verdict


def _test(name, status, severity):
    return {"name": name, "status": status, "severity": severity, "message": ""}


def _result(key, kind, verdict, tests, period=3.0):
    return {
        "target_key": key,
        "target_kind": kind,
        "verdict": verdict,
        "status": "OK",
        "tests": tests,
        "period_comparison": {"relative_error": 0.0, "published_period_days": period},
    }


GATE = _test("snr", "PASS", "gate")
CATALOG_FAIL = _test("eb_catalog", "FAIL", "fatal")
CENTROID_FAIL = _test("centroid_shift", "FAIL", "fatal")


def _loaded(excluded):
    criteria = {
        "period_tolerance": 0.001,
        "expected_planets": 1,
        "min_recovered_planets": 1,
        "expected_false_positives": 2,
        "min_flagged_false_positives": 2,
        "max_refuted_planets": 0,
        "flag_excluded_tests": excluded,
    }
    claim = SimpleNamespace(pass_criteria=criteria, id="c", hypothesis="h", definitions={})
    return SimpleNamespace(claim=claim, attachment_by_role=lambda _role: None)


RESULTS = [
    _result("TIC-1", "planet", "SURVIVED", [GATE]),
    _result("TIC-2", "false_positive", "REFUTED", [GATE, CATALOG_FAIL]),
    _result("TIC-3", "false_positive", "REFUTED", [GATE, CATALOG_FAIL, CENTROID_FAIL]),
]


def test_signal_verdict_ignores_excluded_tests():
    assert signal_verdict(RESULTS[1], ["eb_catalog"]) == "SURVIVED"
    assert signal_verdict(RESULTS[2], ["eb_catalog"]) == "REFUTED"
    assert signal_verdict(RESULTS[1], []) == "REFUTED"


def test_flagged_counts_only_signal_tests_and_reports_the_rest():
    calibrator = TessCalibrator()
    summary = calibrator.evaluate(_loaded(["eb_catalog"]), RESULTS, complete=True)
    flagged = summary["self_claim"]["criteria"][1]
    assert flagged["criterion"] == "flagged false positives (without eb_catalog)"
    assert flagged["value"] == 1 and flagged["passed"] is False
    assert summary["information"]["flagged_false_positives_with_every_test"] == 2
    assert summary["self_claim"]["result"] == "FAIL"
    markdown = calibrator.summary_markdown(summary)
    assert "Information (not a criterion): 2 of 2" in markdown
    assert "Signal verdict" in markdown


def test_degeneracy_guard_uses_the_full_verdict():
    refuted_by_catalog = _result("TIC-1", "planet", "REFUTED", [GATE, CATALOG_FAIL])
    summary = TessCalibrator().evaluate(
        _loaded(["eb_catalog"]), [refuted_by_catalog, *RESULTS[1:]], complete=True
    )
    guard = summary["self_claim"]["criteria"][2]
    assert guard["value"] == 1 and guard["passed"] is False


def test_without_exclusions_the_v01_definition_is_unchanged():
    summary = TessCalibrator().evaluate(_loaded([]), RESULTS, complete=True)
    assert summary["self_claim"]["criteria"][1]["value"] == 2
    assert summary["self_claim"]["result"] == "PASS"
