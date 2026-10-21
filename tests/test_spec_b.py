"""Specification B's experimental implementation (X1b), written before the code, under its
acceptance record docs/validation/v0.2.1/reopen/stage-1/x1b-acceptance.md (T1 to T9; C6 is
tests/test_holdout_blindness.py, kept). Synthetic data only; no network.

Interface (declared in the acceptance record, section 1): ``holdout.spec_b_outcome(rounds,
necessary_years)`` with ``rounds`` a sequence of ``(hidden_year, status, reason)``;
``holdout.SpecBCompletenessError``; ``holdout.run_holdout(raw, sectors, plan, *,
aggregation="legacy")``; ``rmin_evaluate.target_outcomes(rec, r_min, b, s, min_snr, *,
aggregation="legacy")``.
"""

from __future__ import annotations

import importlib
import itertools
import sys
from pathlib import Path

import pytest

import refute.packs.tess.holdout as holdout
from refute.core.verdict import TestStatus

sys.path.insert(0, str(Path(__file__).resolve().parent))
import spec_b_cases as sb  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
POPULATION = ROOT / "docs" / "validation" / "v0.2.1" / "population"
B = "spec_b_experimental"
NPW = "no_predicted_window"

# --- T1, T2: the rows of B3 ----------------------------------------------------------------------
# (rounds in year order as (status, reason), expected status, expected reason, undecided indices)

B3_ROWS = [
    ((("PASS", None), ("PASS", None)), "PASS", None, ()),
    ((("PASS", None), ("PASS", None), ("PASS", None)), "PASS", None, ()),
    ((("PASS", None), ("INCONCLUSIVE", "x")), "INCONCLUSIVE", "necessary_years_undecided", (1,)),
    (
        (("INCONCLUSIVE", "x"), ("PASS", None), ("PASS", None)),
        "INCONCLUSIVE",
        "necessary_years_undecided",
        (0,),
    ),
    ((("PASS", None), ("FAIL", "inconsistent_with_train")), "FAIL", "prediction_failed", ()),
    ((("INCONCLUSIVE", "x"), ("FAIL", "inconsistent_with_train")), "FAIL", "prediction_failed", ()),
    (
        (("FAIL", "inconsistent_with_train"), ("PASS", None), ("INCONCLUSIVE", "x")),
        "FAIL",
        "prediction_failed",
        (),
    ),
    (
        (("INCONCLUSIVE", "x"), ("INCONCLUSIVE", "y")),
        "INCONCLUSIVE",
        "necessary_years_undecided",
        (0, 1),
    ),
    ((("PASS", None), ("INCONCLUSIVE", NPW)), "INCONCLUSIVE", "necessary_years_undecided", (1,)),
    ((("FAIL", "inconsistent_with_train"), ("INCONCLUSIVE", NPW)), "FAIL", "prediction_failed", ()),
]
YEARS = (2018, 2019, 2020)


def _rounds(row):
    years = YEARS[: len(row)]
    return [(y, s, r) for y, (s, r) in zip(years, row, strict=True)], list(years)


@pytest.mark.parametrize("index", range(len(B3_ROWS)))
def test_t1_every_row_of_b3(index):
    row, status, reason, undecided = B3_ROWS[index]
    rounds, years = _rounds(row)
    out = holdout.spec_b_outcome(rounds, years)
    assert out["rule"] == B
    assert (out["status"], out["reason"]) == (status, reason)
    assert out["fail_years"] == [y for y, s, _ in rounds if s == "FAIL"]
    assert out["pass_years"] == [y for y, s, _ in rounds if s == "PASS"]
    expected_undecided = (
        [{"year": rounds[i][0], "reason": rounds[i][2]} for i in undecided]
        if status == "INCONCLUSIVE"
        else [{"year": y, "reason": r} for y, s, r in rounds if s == "INCONCLUSIVE"]
    )
    assert out["undecided"] == expected_undecided


@pytest.mark.parametrize("index", range(len(B3_ROWS)))
def test_t2_the_order_of_the_rounds_does_not_matter(index):
    row, status, reason, _ = B3_ROWS[index]
    rounds, years = _rounds(row)
    first = holdout.spec_b_outcome(rounds, years)
    for perm in itertools.permutations(rounds):
        for ys in itertools.permutations(years):
            assert holdout.spec_b_outcome(list(perm), list(ys)) == first


def test_the_no_predicted_window_year_keeps_its_reason():
    rounds, years = _rounds((("PASS", None), ("INCONCLUSIVE", NPW)))
    out = holdout.spec_b_outcome(rounds, years)
    assert out["undecided"] == [{"year": 2019, "reason": NPW}]


# --- T3, T4: completeness and fewer than two years -------------------------------------------


@pytest.mark.parametrize(
    "rounds, years",
    [
        ([], []),  # empty
        ([], [2018, 2020]),  # empty, with years
        ([(2018, "PASS", None), (2019, "PASS", None)], [2018, 2020]),  # a year not necessary
        ([(2018, "PASS", None), (2018, "PASS", None)], [2018]),  # two rounds of one year
        ([(2018, "PASS", None), (2018, "FAIL", "z"), (2020, "PASS", None)], [2018, 2020]),
        ([(2018, "PASS", None)], [2018, 2020]),  # a necessary year without its round
        ([(2018, "PASS", None), (2020, "PASS", None)], [2018, 2020, 2020]),  # duplicated year
        ([(2018, "PASS", None), (2020, "pass", None)], [2018, 2020]),  # an unknown status
        ([(2018, "PASS", None), (2020, TestStatus.PASS, None)], [2018, 2020]),  # not a string
    ],
)
def test_t3_completeness_is_refused_as_an_error(rounds, years):
    with pytest.raises(holdout.SpecBCompletenessError):
        holdout.spec_b_outcome(rounds, years)
    assert issubclass(holdout.SpecBCompletenessError, ValueError)


def test_t4_one_necessary_year_is_inconclusive():
    out = holdout.spec_b_outcome([(2018, "PASS", None)], [2018])
    assert (out["status"], out["reason"]) == ("INCONCLUSIVE", "fewer_than_two_observing_years")


# --- T5, T6, T8: the engine's argument --------------------------------------------------------


def _small():
    return sb.curve("white", 2)


def test_t5_b_is_refused_outside_the_m4_path(monkeypatch):
    calls = []
    monkeypatch.setattr(holdout, "_round", lambda *a, **k: calls.append(a))
    lc, sectors = _small()
    with pytest.raises(ValueError, match="corrections"):
        holdout.run_holdout(lc, sectors, sb.legacy_plan(), aggregation=B)
    with pytest.raises(ValueError, match="aggregation"):
        holdout.run_holdout(lc, sectors, sb.plan(), aggregation="spec_b")
    assert calls == []


@pytest.fixture(scope="module")
def c4_white_2y():
    """C4 (white, two years): legacy PASS, B INCONCLUSIVE; run with the default, the explicit
    legacy and B."""
    c = next(c for c in sb.controls() if c.key == "C4-white-2y")
    with sb.replaced(c):
        default = holdout.run_holdout(c.lc, c.sectors, c.plan)
        legacy = holdout.run_holdout(c.lc, c.sectors, c.plan, aggregation="legacy")
        spec_b = holdout.run_holdout(c.lc, c.sectors, c.plan, aggregation=B)
    return default, legacy, spec_b


def _outcome_json(outcome):
    import json

    return json.dumps(outcome.to_dict(), sort_keys=True, default=str)


def test_t6_the_default_is_the_legacy_rule_unchanged(c4_white_2y):
    default, legacy, spec_b = c4_white_2y
    assert _outcome_json(default) == _outcome_json(legacy)
    assert default.test.status is TestStatus.PASS
    assert "aggregation" not in default.test.metrics and "spec_b" not in default.test.metrics
    assert spec_b.test.status is TestStatus.INCONCLUSIVE
    assert spec_b.test.metrics["aggregation"] == B
    # the rounds are the same under both rules
    assert [r.to_dict() for r in spec_b.rounds] == [r.to_dict() for r in legacy.rounds]
    for key in ("years", "rounds", "n_pass", "n_fail", "n_inconclusive"):
        assert spec_b.test.metrics[key] == legacy.test.metrics[key]


def test_t8_the_engine_calls_the_shared_function_once(monkeypatch):
    calls = []
    original = holdout.spec_b_outcome

    def spy(rounds, necessary_years):
        calls.append((list(rounds), list(necessary_years)))
        return original(rounds, necessary_years)

    monkeypatch.setattr(holdout, "spec_b_outcome", spy)
    lc, sectors = _small()
    out = holdout.run_holdout(lc, sectors, sb.plan(), aggregation=B)
    assert len(calls) == 1
    assert calls[0][1] == list(lc.years)
    assert sorted(y for y, _, _ in calls[0][0]) == list(lc.years)
    assert out.test.metrics["spec_b"]["status"] == out.test.status.value
    holdout.run_holdout(lc, sectors, sb.plan())  # the default never calls it
    assert len(calls) == 1


# --- T7: the engine controls of B4 -------------------------------------------------------------


def _legacy_status(statuses: list[str]) -> str:
    if "FAIL" in statuses:
        return "FAIL"
    if "PASS" in statuses:
        return "PASS"
    return "INCONCLUSIVE"


@pytest.fixture(scope="module")
def control_runs():
    out = {}
    for c in sb.controls():
        with sb.replaced(c):
            outcome = holdout.run_holdout(c.lc, c.sectors, c.plan, aggregation=B)
        out[c.key] = (c, outcome)
    return out


CONTROL_KEYS = [c.key for c in sb.controls()]


@pytest.mark.parametrize("key", CONTROL_KEYS)
def test_t7_each_control_has_its_outcome_under_b(control_runs, key):
    c, outcome = control_runs[key]
    status = outcome.test.status.value
    spec_b = outcome.test.metrics["spec_b"]
    rounds = {r.hidden_year: r for r in outcome.rounds}
    last, first = max(rounds), min(rounds)
    if c.name in ("C5", "C5r"):
        assert status != "PASS"
    else:
        assert status == c.expected_b
    if c.expected_b == "INCONCLUSIVE" and c.name not in ("C5", "C5r"):
        assert [u["year"] for u in spec_b["undecided"]] == list(c.expected_undecided)
    # the preconditions, as checked on the engine before the code (probe.json)
    if c.name == "C1":
        assert all(r.status is TestStatus.PASS for r in outcome.rounds)
    if c.name in ("C2", "C7b"):
        assert rounds[last].status is TestStatus.FAIL
    if c.name in ("C3", "C4"):
        assert rounds[last].metrics.get("reason") == "insufficient_capacity_hidden_noise"
    if c.name == "C7a":
        assert rounds[last].metrics.get("reason") == NPW
        assert spec_b["undecided"] == [{"year": last, "reason": NPW}]
    if c.name == "C7b" and c.n_years == 3:
        # in two years the first year's round trains on the year without the signal and stops
        # before its windows are predicted, so the replacement is never reached there: a year
        # without a window beside a FAIL exists only in three years (and in T1's row)
        assert rounds[first].metrics.get("reason") == NPW
        assert spec_b["undecided"] == [{"year": first, "reason": NPW}]
    # the contrast with today's rule, from the same rounds
    legacy = _legacy_status([r.status.value for r in outcome.rounds])
    if c.name in ("C4", "C7a") or (c.name == "C3" and c.n_years == 3):
        assert legacy == "PASS"  # B4: today PASS, under B INCONCLUSIVE
    if c.name == "C3" and c.n_years == 2:
        # the other round trains on the year without the signal: today's rule cannot PASS
        assert legacy == "INCONCLUSIVE"
    if c.name in ("C2", "C7b"):
        assert legacy == "FAIL"


# --- T8, T9: the evaluator ----------------------------------------------------------------------


@pytest.fixture(scope="module")
def ev():
    sys.path.insert(0, str(POPULATION))
    return importlib.import_module("rmin_evaluate")


def _record_round(year: int, status: str, reason: str | None) -> dict:
    """A calibration record that derive_round turns into ``status`` at every R of the study."""
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
        "s_pred_1": 50.0,
        "s_pred_2": 50.0,
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
    if status == "FAIL":
        base.update(s_meas=1.0, d_hidden=0.0)
    elif status == "INCONCLUSIVE":
        base.update(stage="before_capacity", reason=reason, decision_1=reason)
    return base


def _target(row) -> dict:
    years = list(YEARS[: len(row)])
    return {
        "target": "x1b/planet-near-white-0000",
        "group": "white, no variability",
        "scenario": "constant",
        "years": years,
        "rounds": [_record_round(y, s, r) for y, (s, r) in zip(years, row, strict=True)],
    }


@pytest.mark.parametrize("index", range(len(B3_ROWS)))
def test_t9_the_evaluator_gives_the_shared_function_s_status(ev, index):
    row, status, _, _ = B3_ROWS[index]
    rec = _target(row)
    out = ev.target_outcomes(rec, 8, 0.0, 1.0, 5.0, aggregation=B)
    derived = [(d["record"]["hidden_year"], d["status"], d["reason"]) for d in out["rounds"]]
    assert [s for _, s, _ in derived] == [s for s, _ in row]
    assert out["status"] == holdout.spec_b_outcome(derived, rec["years"])["status"] == status
    assert out["spec_b"] == holdout.spec_b_outcome(derived, rec["years"])
    legacy = ev.target_outcomes(rec, 8, 0.0, 1.0, 5.0)
    assert legacy["status"] == ev.aggregate([s for s, _ in row])
    assert "spec_b" not in legacy


def test_t8_the_evaluator_calls_the_shared_function_once(ev, monkeypatch):
    calls = []
    original = holdout.spec_b_outcome

    def spy(rounds, necessary_years):
        calls.append(list(necessary_years))
        return original(rounds, necessary_years)

    monkeypatch.setattr(holdout, "spec_b_outcome", spy)
    rec = _target((("PASS", None), ("INCONCLUSIVE", NPW)))
    ev.target_outcomes(rec, 8, 0.0, 1.0, 5.0, aggregation=B)
    assert calls == [rec["years"]]
    ev.target_outcomes(rec, 8, 0.0, 1.0, 5.0)
    assert len(calls) == 1


def test_the_evaluator_refuses_an_unknown_aggregation(ev):
    with pytest.raises(ValueError, match="aggregation"):
        ev.target_outcomes(
            _target((("PASS", None), ("PASS", None))), 8, 0.0, 1.0, 5.0, aggregation="b"
        )
