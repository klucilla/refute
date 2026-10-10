"""v0.2.1 H7: a false positive counts as flagged only if its catalogued signal was the one
analyzed (fabricated results). Cases A1-A13 of docs/validation/v0.2.1/H7-acceptance.md."""

from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from conftest import calibration_claim, target_entry, targets_file, write_yaml
from refute.core.claim import ClaimError, load_claim
from refute.packs.tess.calibration import TessCalibrator, signal_recovered

ROOT = Path(__file__).resolve().parents[1]
FACTORS = [1.0, 2.0, 0.5]
DEVELOPMENT_SEEDS = range(10)


def _test(name, status, severity):
    return {"name": name, "status": status, "severity": severity, "message": "", "coverage": 1}


GATE = _test("snr", "PASS", "gate")
ODD_EVEN_FAIL = _test("odd_even", "FAIL", "fatal")
CATALOG_FAIL = _test("eb_catalog", "FAIL", "fatal")


def _comparison(published, found):
    error = None
    if published is not None and found is not None:
        error = abs(found - published) / published
    return {"published_period_days": published, "found_period_days": found, "relative_error": error}


def _fp(key, published, found, verdict="REFUTED", tests=None, status="OK"):
    return {
        "target_key": key,
        "target_kind": "false_positive",
        "verdict": verdict,
        "status": status,
        "tests": [GATE, ODD_EVEN_FAIL] if tests is None else tests,
        "period_comparison": _comparison(published, found),
    }


def _planet(key, published, found, verdict="SURVIVED"):
    return {
        "target_key": key,
        "target_kind": "planet",
        "verdict": verdict,
        "status": "OK",
        "tests": [GATE] if verdict != "REFUTED" else [GATE, ODD_EVEN_FAIL],
        "period_comparison": _comparison(published, found),
    }


def _loaded(planets=1, fps=1, **extra):
    criteria = {
        "period_tolerance": 0.001,
        "expected_planets": planets,
        "min_recovered_planets": 0,
        "expected_false_positives": fps,
        "min_flagged_false_positives": 0,
        "max_refuted_planets": planets,
        **extra,
    }
    claim = SimpleNamespace(pass_criteria=criteria, id="c", hypothesis="h", definitions={})
    return SimpleNamespace(claim=claim, attachment_by_role=lambda _role: None)


def _on(**extra):
    return _loaded(flag_requires_signal_recovery=True, **extra)


def _summary(loaded, results):
    return TessCalibrator().evaluate(loaded, results, complete=True)


def _flagged(loaded, results):
    return _summary(loaded, results)["self_claim"]["criteria"][1]


# --- A1-A3: counted as flagged ------------------------------------------------------------


def test_a1_exact_period_is_recovered_and_flagged():
    result = _fp("TIC-1", 3.0, 3.0)
    assert signal_recovered(result, 0.001, FACTORS) is True
    assert _flagged(_on(), [result])["value"] == 1


@pytest.mark.parametrize("found", [6.0 * (1 + 5e-4), 1.5 * (1 - 5e-4)])
def test_a2_double_and_half_period_within_tolerance_are_recovered(found):
    result = _fp("TIC-1", 3.0, found)
    assert signal_recovered(result, 0.001, FACTORS) is True
    assert _flagged(_on(), [result])["value"] == 1


@pytest.mark.parametrize("found", [9.0, 7.0, 18.0, 14.0, 4.5, 3.5])
def test_a3_boundary_is_inclusive(found):
    # Tolerance 1/8 and published period 8: every relative error here is exactly 1/8 in
    # binary floating point (P: 9 and 7; 2P: 18 and 14; P/2: 4.5 and 3.5).
    result = _fp("TIC-1", 8.0, found)
    assert signal_recovered(result, 0.125, FACTORS) is True
    assert _flagged(_on(period_tolerance=0.125), [result])["value"] == 1


# --- A4-A7: not flagged, signal not recovered -------------------------------------------


def test_a4_a_different_signal_is_not_recovered():
    # Fabricated values of the TOI-1481.01 type: relative error 0.23, not an alias.
    result = _fp("TIC-1", 2.185, 1.677)
    assert signal_recovered(result, 0.001, FACTORS) is False
    assert _flagged(_on(), [result])["value"] == 0
    assert _flagged(_loaded(), [result])["value"] == 1  # counted under the v0.2 definition


@pytest.mark.parametrize("found", [9.0, 1.0])
def test_a5_triple_and_third_period_are_outside_the_factors(found):
    result = _fp("TIC-1", 3.0, found)
    assert signal_recovered(result, 0.001, FACTORS) is False
    assert _flagged(_on(), [result])["value"] == 0


@pytest.mark.parametrize(
    ("published", "found", "tolerance"),
    [
        (3.0, 3.0 * (1 + 1.1e-3), 0.001),
        (3.0, 6.0 * (1 - 1.1e-3), 0.001),
        (8.0, float(np.nextafter(9.0, np.inf)), 0.125),
        (8.0, float(np.nextafter(4.5, np.inf)), 0.125),
    ],
)
def test_a6_just_above_the_tolerance_is_not_recovered(published, found, tolerance):
    result = _fp("TIC-1", published, found)
    assert signal_recovered(result, tolerance, FACTORS) is False
    assert _flagged(_on(period_tolerance=tolerance), [result])["value"] == 0


@pytest.mark.parametrize(
    "result",
    [
        {**_fp("TIC-1", 3.0, None, verdict="INCONCLUSIVE", tests=[]), "status": "ERROR"},
        {**_fp("TIC-1", 3.0, None), "period_comparison": _comparison(3.0, None)},
        _fp("TIC-1", None, 3.0),
        {k: v for k, v in _fp("TIC-1", 3.0, 3.0).items() if k != "period_comparison"},
    ],
    ids=["analysis-error", "no-found-period", "no-published-period", "no-comparison"],
)
def test_a7_missing_periods_are_not_recovered(result):
    assert signal_recovered(result, 0.001, FACTORS) is False
    assert _flagged(_on(), [result])["value"] == 0


# --- A8: recovered but not refuted -------------------------------------------------------


@pytest.mark.parametrize(
    ("verdict", "tests"),
    [("SURVIVED", [GATE]), ("INCONCLUSIVE", [GATE]), ("SURVIVED", [GATE, CATALOG_FAIL])],
)
def test_a8_identity_never_creates_a_flag(verdict, tests):
    result = _fp("TIC-1", 3.0, 3.0, verdict=verdict, tests=tests)
    excluded = ["eb_catalog"] if CATALOG_FAIL in tests else []
    assert signal_recovered(result, 0.001, FACTORS) is True
    assert _flagged(_on(flag_excluded_tests=excluded), [result])["value"] == 0


# --- A9-A11: regression ------------------------------------------------------------------

MIXED = [
    _planet("TIC-1", 3.7, 3.7),
    _planet("TIC-2", 3.7, 7.4),
    _planet("TIC-3", 3.7, 3.7, verdict="REFUTED"),
    _fp("TIC-4", 2.9, 2.9),
    _fp("TIC-5", 2.185, 1.677),
    _fp("TIC-6", 2.9, 2.9, verdict="SURVIVED", tests=[GATE]),
    {**_fp("TIC-7", 2.9, None, verdict="INCONCLUSIVE", tests=[]), "status": "ERROR"},
    _fp("TIC-8", 1.8, 0.9, tests=[GATE, CATALOG_FAIL, ODD_EVEN_FAIL]),
    _fp("TIC-9", 1.8, 1.8, tests=[GATE, CATALOG_FAIL]),
]


@pytest.mark.parametrize("off", [{}, {"flag_requires_signal_recovery": False}])
@pytest.mark.parametrize("excluded", [[], ["eb_catalog"]])
def test_a9_flag_off_keeps_the_v02_definition_and_output(off, excluded):
    summary = _summary(_loaded(planets=3, fps=6, flag_excluded_tests=excluded, **off), MIXED)
    flagged = summary["self_claim"]["criteria"][1]
    expected_name = "flagged false positives"
    if excluded:
        expected_name += " (without eb_catalog)"
    assert flagged["criterion"] == expected_name
    # TIC-4, TIC-5 and TIC-8 always; TIC-9 only when eb_catalog counts.
    assert flagged["value"] == (3 if excluded else 4) and flagged["of"] == 6
    assert "false_positives_signal_not_recovered" not in summary["information"]
    assert "flagged_without_signal_identity" not in summary["information"]
    assert all("signal_recovered" not in row for row in summary["targets"])
    markdown = TessCalibrator().summary_markdown(summary)
    assert "Signal recovered" not in markdown and "Definition change" not in markdown


@pytest.mark.parametrize("excluded", [[], ["eb_catalog"]])
def test_a10_planet_criteria_do_not_depend_on_the_flag(excluded):
    off = _summary(_loaded(planets=3, fps=6, flag_excluded_tests=excluded), MIXED)
    on = _summary(_on(planets=3, fps=6, flag_excluded_tests=excluded), MIXED)
    for index in (0, 2):
        assert on["self_claim"]["criteria"][index] == off["self_claim"]["criteria"][index]
    assert [r["recovered"] for r in on["targets"]] == [r["recovered"] for r in off["targets"]]


def _random_results(seed):
    rng = np.random.default_rng(seed)
    verdicts = ["REFUTED", "SURVIVED", "INCONCLUSIVE", "WEAKENED"]
    results = []
    for index in range(40):
        kind = "planet" if rng.random() < 0.4 else "false_positive"
        published = float(rng.uniform(0.5, 10.0)) if rng.random() < 0.95 else None
        roll = rng.random()
        if published is None or roll < 0.1:
            found = None
        elif roll < 0.6:
            factor = float(rng.choice([1.0, 2.0, 0.5, 3.0, 1.0 / 3.0]))
            found = published * factor * (1 + float(rng.normal(0.0, 1e-3)))
        else:
            found = float(rng.uniform(0.5, 12.0))
        verdict = str(rng.choice(verdicts))
        tests = [GATE, ODD_EVEN_FAIL] if verdict == "REFUTED" else [GATE]
        if rng.random() < 0.3:
            tests = [*tests, CATALOG_FAIL]
        status = "ERROR" if found is None and rng.random() < 0.5 else "OK"
        builder = _planet if kind == "planet" else _fp
        result = builder(f"TIC-{index}", published, found, verdict=verdict)
        results.append({**result, "tests": tests, "status": status})
    return results


@pytest.mark.parametrize("seed", DEVELOPMENT_SEEDS)
@pytest.mark.parametrize("excluded", [[], ["eb_catalog"]])
def test_a11_flagged_with_identity_is_a_subset(seed, excluded):
    results = _random_results(seed)
    fps = [r for r in results if r["target_kind"] == "false_positive"]

    def flagged_keys(loaded):
        # One result at a time: each target's flag depends only on its own result.
        return {r["target_key"] for r in fps if _flagged(loaded, [r])["value"] == 1}

    off_loaded = _loaded(flag_excluded_tests=excluded)
    on_loaded = _on(flag_excluded_tests=excluded)
    with_identity, without_identity = flagged_keys(on_loaded), flagged_keys(off_loaded)
    assert with_identity <= without_identity
    on, off = _flagged(on_loaded, results), _flagged(off_loaded, results)
    assert on["of"] == off["of"] == len(fps)
    assert on["value"] == len(with_identity) and off["value"] == len(without_identity)
    information = _summary(on_loaded, results)["information"]
    assert information["flagged_without_signal_identity"] == len(without_identity)


# --- A12: reporting ----------------------------------------------------------------------


def test_a12_reporting_states_the_definition_change():
    calibrator = TessCalibrator()
    summary = _summary(_on(planets=3, fps=6), MIXED)
    flagged = summary["self_claim"]["criteria"][1]
    assert flagged["criterion"] == "flagged false positives (signal recovered)"
    # Recovered and REFUTED: TIC-4, TIC-8 (found at P/2) and TIC-9.
    assert flagged["value"] == 3 and flagged["of"] == 6

    information = summary["information"]
    assert information["false_positives_signal_not_recovered"] == {
        "count": 2,
        "targets": ["TIC-5", "TIC-7"],
    }
    assert information["flagged_without_signal_identity"] == 4
    rows = {row["target"]: row for row in summary["targets"]}
    assert [rows[f"TIC-{i}"]["signal_recovered"] for i in (1, 2, 3)] == [None, None, None]
    assert [rows[f"TIC-{i}"]["signal_recovered"] for i in range(4, 10)] == [
        True,
        False,
        True,
        False,
        True,
        True,
    ]

    markdown = calibrator.summary_markdown(summary)
    assert "| Signal recovered |" in markdown
    assert "Definition change since v0.2" in markdown
    assert "factors 1, 2, 0.5" in markdown
    assert "2 of 6 false positives were not recovered" in markdown
    assert "under the v0.2 definition 4 would count as flagged" in markdown

    named = _summary(_on(planets=3, fps=6, flag_excluded_tests=["eb_catalog"]), MIXED)
    assert (
        named["self_claim"]["criteria"][1]["criterion"]
        == "flagged false positives (signal recovered; without eb_catalog)"
    )


def test_a12_custom_factors_are_used_and_reported():
    loaded = _on(planets=3, fps=6, flag_signal_period_factors=[1.0])
    summary = _summary(loaded, MIXED)
    # TIC-8 (found at P/2) no longer counts.
    assert summary["self_claim"]["criteria"][1]["value"] == 2
    assert "factors 1)" in TessCalibrator().summary_markdown(summary)


# --- A13: schema -------------------------------------------------------------------------


def _claim_file(tmp_path, **criteria):
    targets = [target_entry(1, "planet", 3.7), target_entry(2, "false_positive", 2.9)]
    write_yaml(tmp_path / "targets.yaml", targets_file(targets))
    return write_yaml(tmp_path / "claim.yaml", calibration_claim(1, 1, **criteria))


@pytest.mark.parametrize("factors", [[1.0, 0.0], [-2.0], []])
def test_a13_invalid_factors_are_rejected(tmp_path, factors):
    with pytest.raises(ClaimError, match="flag_signal_period_factors"):
        load_claim(_claim_file(tmp_path, flag_signal_period_factors=factors))


def test_a13_defaults_are_resolved(tmp_path):
    criteria = load_claim(_claim_file(tmp_path)).claim.pass_criteria
    assert criteria["flag_requires_signal_recovery"] is False
    assert criteria["flag_signal_period_factors"] == FACTORS
    explicit = load_claim(
        _claim_file(tmp_path, flag_requires_signal_recovery=True, flag_signal_period_factors=[1.0])
    ).claim.pass_criteria
    assert explicit["flag_requires_signal_recovery"] is True
    assert explicit["flag_signal_period_factors"] == [1.0]


def test_a13_the_v02_claim_loads_with_the_defaults():
    # Read only: the locked v0.2 claim has neither field and keeps the v0.2 definition.
    criteria = load_claim(ROOT / "calibration" / "v0.2" / "self_claim.yaml").claim.pass_criteria
    assert criteria["flag_requires_signal_recovery"] is False
    assert criteria["flag_signal_period_factors"] == FACTORS
    assert criteria["flag_excluded_tests"] == ["eb_catalog"]
