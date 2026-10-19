"""The ``R_min`` study's evaluator (map Amendment 27), written before the code, on built records.

Interface (declared here), in ``docs/validation/v0.2.1/population/rmin_evaluate.py``: a target
record is ``{"target", "group", "scenario", "years", "rounds"}`` with one
``calibration_measurement`` record per observing year; ``choose_k(records, min_snr)`` (raises
``StudyStoppedError`` on an empty set), ``pair_for_r(records, k, r_min, min_snr)`` (``None`` without
residuals),
``completeness_problems(manifest, records)``, ``target_outcomes(record, r_min, b, s, min_snr)``,
``criteria(records, r_min, pair, min_snr)`` (per group) and ``choose_r_min(results)``.
"""

import importlib
import sys
from pathlib import Path

import pytest
from scipy.stats import beta

ROOT = Path(__file__).resolve().parents[1]
POPULATION = ROOT / "docs" / "validation" / "v0.2.1" / "population"
MIN_SNR = 5.0
GROUPS = (
    "white, no variability",
    "white, variability",
    "AR(1), no variability",
    "AR(1), variability",
)


@pytest.fixture(scope="module")
def ev():
    sys.path.insert(0, str(POPULATION))
    return importlib.import_module("rmin_evaluate")


def rnd(year, **kw):
    """A measured round that passes every decision at every R of the set (counts 30) and PASSes,
    unless changed."""
    base = {
        "hidden_year": year,
        "stage": None,
        "reason": None,
        "decision_1": "pass",
        "decision_2": "pass",
        "n_years": 2,
        "train_n_rep": [30, 30, 30],
        "hidden_n_rep": [30, 30, 30],
        "hidden_noise_undetermined": False,
        "s_pred_1": 12.0,
        "s_pred_2": 12.0,
        "s_meas": 12.0,
        "d_train": 1e-3,
        "e_train": 1e-4,
        "d_hidden": 1e-3,
        "e_hidden": 1e-4,
        "dp": 0.0,
        "measurement_status": "ok",
        "d_twin": 1e-3,
        "twin_status": "ok",
    }
    base.update(kw)
    return base


def target(i, scenario="constant", group=GROUPS[0], years=(2018, 2020), rounds=None):
    return {
        "target": f"refute-v0.2.1-rmin-study-1/planet-near-white-{i:04d}",
        "group": group,
        "scenario": scenario,
        "years": list(years),
        "rounds": rounds if rounds is not None else [rnd(y) for y in years],
    }


FAIL_ROUND = {"s_meas": 1.0, "d_hidden": 0.0}  # not detected, Z = 1e-3 / 1.41e-4 > 3


# --- k (item 4) ---------------------------------------------------------------------------------


def _bs(residuals_1, residuals_2):
    """Targets whose rounds give the residuals S_meas - S_pred,k given (S_pred,k = 10)."""
    out = []
    for i, (r1, r2) in enumerate(zip(residuals_1, residuals_2, strict=True)):
        meas = 10.0 + r1
        rounds = [rnd(2018, s_pred_1=10.0, s_pred_2=meas - r2, s_meas=meas)]
        out.append(target(i, years=(2018,), rounds=rounds))
    return out


def test_k_is_the_smaller_spread(ev):
    out = ev.choose_k(_bs([-1, 0, 1], [-3, 0, 3]), MIN_SNR)
    assert out["k"] == 1 and out["a"][1] == pytest.approx(1.4826)


def test_a_tie_within_five_percent_goes_to_k_2_inclusive(ev):
    # MADs 20 and 19: exactly 5 % of the larger apart (the factor 1.4826 cancels in the rule)
    out = ev.choose_k(_bs([-20, 0, 20], [-19, 0, 19]), MIN_SNR)
    assert out["k"] == 2
    out = ev.choose_k(_bs([-19, 0, 19], [-20, 0, 20]), MIN_SNR)
    assert out["k"] == 2  # a tie whichever is larger
    out = ev.choose_k(_bs([-18.5, 0, 18.5], [-20, 0, 20]), MIN_SNR)
    assert out["k"] == 1  # 7.5 % apart: the smaller, k = 1


def test_both_spreads_zero_go_to_k_2(ev):
    assert ev.choose_k(_bs([0, 0, 0], [0, 0, 0]), MIN_SNR)["k"] == 2


def test_an_empty_set_stops_the_study(ev):
    recs = _bs([-1, 0, 1], [-1, 0, 1])
    for r in recs:
        r["rounds"][0]["s_pred_2"] = 4.0  # below min_snr: the set of k = 2 is empty
    with pytest.raises(ev.StudyStoppedError):
        ev.choose_k(recs, MIN_SNR)


def test_k_reads_only_measured_rounds(ev):
    recs = _bs([-1, 0, 1], [-3, 0, 3])
    recs.append(target(9, years=(2018,), rounds=[rnd(2018, s_meas=None, s_pred_1=10.0)]))
    assert ev.choose_k(recs, MIN_SNR)["n"][1] == 3


# --- the pair (item 5) --------------------------------------------------------------------------


def test_the_pair_is_the_median_and_scaled_mad_of_the_rounds_meeting_r(ev):
    recs = _bs([-2, -1, 1, 2], [0, 0, 0, 0])  # residuals of k = 1
    recs[0]["rounds"][0]["hidden_n_rep"] = [30, 9, 30]  # not meeting R = 10
    pair = ev.pair_for_r(recs, 1, 8, MIN_SNR)
    assert pair["b"] == pytest.approx(
        0.0
    )  # the median of an even count: the mean of the middle two
    assert pair["s"] == pytest.approx(1.4826 * 1.5)
    assert (pair["rounds"], pair["targets"]) == (4, 4)
    pair = ev.pair_for_r(recs, 1, 10, MIN_SNR)
    assert pair["rounds"] == 3 and pair["b"] == pytest.approx(1.0)


def test_no_residual_no_pair_and_a_zero_mad_is_kept(ev):
    recs = _bs([0, 0, 0], [0, 0, 0])
    assert ev.pair_for_r(recs, 1, 8, MIN_SNR)["s"] == 0.0
    for r in recs:
        r["rounds"][0]["hidden_noise_undetermined"] = True
    assert ev.pair_for_r(recs, 1, 8, MIN_SNR) is None


# --- completeness (item 3) ----------------------------------------------------------------------


def test_completeness(ev):
    recs = [target(0), target(1)]
    manifest = [(r["target"], r["scenario"]) for r in recs]
    assert ev.completeness_problems(manifest, recs) == []
    assert ev.completeness_problems(manifest + [("x/y", "constant")], recs)  # missing
    assert ev.completeness_problems(manifest, recs + [target(0)])  # duplicated
    assert ev.completeness_problems(manifest[:1], recs)  # extra
    short = target(2, rounds=[rnd(2018)])  # the 2020 round missing
    assert ev.completeness_problems(manifest + [(short["target"], "constant")], recs + [short])
    double = target(3, rounds=[rnd(2018), rnd(2018), rnd(2020)])
    assert ev.completeness_problems(manifest + [(double["target"], "constant")], recs + [double])
    empty = target(4, rounds=[])
    assert ev.completeness_problems(manifest + [(empty["target"], "constant")], recs + [empty])


# --- outcomes and criteria (items 7 to 10) ------------------------------------------------------


def test_the_outcome_aggregates_and_reads_the_last_year_from_the_metadata(ev):
    t = target(0, years=(2018, 2019, 2020))
    t["rounds"][1] = rnd(2019, **FAIL_ROUND)
    out = ev.target_outcomes(t, 8, 0.0, 0.0, MIN_SNR)
    assert out["status"] == "FAIL" and out["eligible"] is True
    assert out["last_year"] == 2020 and out["last_round"]["status"] == "PASS"
    assert out["first_eligible"]["hidden_year"] == 2018


def test_a_missing_last_year_round_is_not_taken_from_the_records(ev):
    t = target(0, years=(2018, 2020), rounds=[rnd(2018)])
    out = ev.target_outcomes(t, 8, 0.0, 0.0, MIN_SNR)
    assert out["last_year"] == 2020 and out["last_round"] is None


def _constant_group(n, n_fail, group=GROUPS[0]):
    out = []
    for i in range(n):
        rounds = [rnd(2018), rnd(2020, **(FAIL_ROUND if i < n_fail else {}))]
        out.append(target(i, group=group, rounds=rounds))
    return out


def _xmax(n, level=0.99, threshold=0.02):
    x = 0
    while x + 1 < n and beta.ppf(level, x + 2, n - x - 1) <= threshold:
        x += 1
    return x


def test_criterion_1_at_its_edges(ev):
    n = 866
    x = _xmax(n)
    ok = ev.criteria(_constant_group(n, x), 8, {"b": 0.0, "s": 0.0}, MIN_SNR)[GROUPS[0]]
    assert ok["false_fail"]["n"] == n and ok["false_fail"]["passed"] is True
    worse = ev.criteria(_constant_group(n, x + 1), 8, {"b": 0.0, "s": 0.0}, MIN_SNR)[GROUPS[0]]
    assert worse["false_fail"]["passed"] is False
    few = ev.criteria(_constant_group(n - 1, 0), 8, {"b": 0.0, "s": 0.0}, MIN_SNR)[GROUPS[0]]
    assert few["false_fail"]["passed"] is False  # below the minimum of 866


def _pulls(pulls, group=GROUPS[0]):
    out = []
    for i, p in enumerate(pulls):
        r = rnd(2018, d_hidden=1e-3, e_hidden=1e-4, d_twin=1e-3 - p * 1e-4)
        out.append(target(i, group=group, years=(2018,), rounds=[r]))
    return out


def test_the_coverage_at_its_edges_and_not_evaluable_without_a_twin(ev):
    # 60 % within 1, 92 % within 2, median 0: both fractions at their lower edges
    pulls = [0.0] * 60 + [1.5] * 32 + [3.0] * 8
    cov = ev.criteria(_pulls(pulls), 8, {"b": 0.0, "s": 0.0}, MIN_SNR)[GROUPS[0]]["coverage"]
    assert cov["evaluable"] is True and cov["passed"] is True
    assert cov["within_1"] == pytest.approx(0.60) and cov["within_2"] == pytest.approx(0.92)
    low = [0.0] * 59 + [1.5] * 33 + [3.0] * 8
    cov = ev.criteria(_pulls(low), 8, {"b": 0.0, "s": 0.0}, MIN_SNR)[GROUPS[0]]["coverage"]
    assert cov["passed"] is False
    recs = _pulls(pulls)
    recs[5]["rounds"][0].update(d_twin=None, twin_status="too_few_windows")
    cov = ev.criteria(recs, 8, {"b": 0.0, "s": 0.0}, MIN_SNR)[GROUPS[0]]["coverage"]
    assert cov["evaluable"] is False and cov["passed"] is False
    assert cov["missing_twin"] == 1


def _power(scenario, n, n_fail, impeded=0, s2=12.0):
    out = []
    for i in range(n):
        last = rnd(2020, s_pred_2=s2, **(FAIL_ROUND if i < n_fail else {}))
        if i >= n - impeded:
            last.update(measurement_status="too_few_windows", s_meas=None)
        rounds = [rnd(2018, s_pred_1=3.0, s_pred_2=3.0), last]  # 2018 fails decision 1
        out.append(target(i, scenario=scenario, rounds=rounds))
    return out


def _lower(x, n, level=0.99):
    return 0.0 if x == 0 else beta.ppf(1 - level, x, n - x + 1)


def test_the_disappearance_keeps_a_qualified_inconclusive_target(ev):
    n = 83
    recs = _power("disappearing", n, n - 1, impeded=1)
    out = ev.criteria(recs, 8, {"b": 0.0, "s": 0.0}, MIN_SNR)[GROUPS[0]]["disappearance"]
    assert out["n"] == n  # the impeded one stays in the denominator
    assert out["fails"] == n - 1
    assert out["passed"] is bool(_lower(n - 1, n) >= 0.80)


def test_the_weakening_filter_reads_the_last_rounds_s_pred_2(ev):
    recs = _power("weakened", 120, 120, s2=10.0)  # 0.3 * 10 = 3: qualified (inclusive)
    out = ev.criteria(recs, 8, {"b": 0.0, "s": 0.0}, MIN_SNR)[GROUPS[0]]["weakening"]
    assert out["n"] == 120 and out["passed"] is True
    recs = _power("weakened", 120, 120, s2=10.5)  # 3.15 > 3: none qualified
    out = ev.criteria(recs, 8, {"b": 0.0, "s": 0.0}, MIN_SNR)[GROUPS[0]]["weakening"]
    assert out["n"] == 0 and out["passed"] is False


def test_the_choice(ev):
    def result(passed):
        return {g: {"all_passed": passed} for g in GROUPS}

    results = {8: result(False), 10: None, 12: result(True), 15: result(True), 20: result(False)}
    assert ev.choose_r_min(results) == 12  # 10 has no pair
    assert ev.choose_r_min({8: result(False), 10: None}) is None
    mixed = {8: {**result(True), GROUPS[2]: {"all_passed": False}}, 10: result(True)}
    assert ev.choose_r_min(mixed) == 10
