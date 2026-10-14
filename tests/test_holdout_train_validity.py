"""v0.2.1 H4: a holdout round whose train-only candidate is not a valid basis for a
prediction is INCONCLUSIVE, never FAIL. Cases A1-A7 of
docs/validation/v0.2.1/H4-acceptance.md (fabricated inputs, plus test doubles of the
train search and of the train ephemeris fit, declared in each test)."""

from dataclasses import replace

import numpy as np
import pytest
from pydantic import ValidationError

from conftest import replicate_claim, target_entry, write_yaml
from refute.core.claim import load_claim
from refute.core.verdict import TestStatus
from refute.packs.tess import holdout
from refute.packs.tess.ephemeris import Ephemeris
from refute.packs.tess.holdout import (
    REASON_DURATION_RATIO,
    REASON_TRAIN_SNR,
    REASON_WINDOW_FRACTION,
    PredictedWindow,
    hidden_window_fraction,
    train_validity,
)
from refute.packs.tess.params import TessTestPlan
from refute.packs.tess.search import search_period
from refute.packs.tess.synthetic import fast_plan_dict, scenario_data
from refute.packs.tess.types import Candidate


def _plan(**holdout_overrides):
    plan = fast_plan_dict()
    plan["gauntlet"] = {"holdout_by_year": holdout_overrides}
    return TessTestPlan.model_validate(plan)


def _candidate(period=3.0, duration=0.1, snr=20.0):
    return Candidate(
        period=period,
        t0=1326.0,
        duration=duration,
        depth=0.002,
        depth_err=1e-4,
        snr=snr,
        log_likelihood=1.0,
        sde=10.0,
        n_transits=8,
    )


def _windows(centers, half, kind="transit"):
    return [
        PredictedWindow(kind, i, float(c), float(half), half + 0.1, half + 0.3)
        for i, c in enumerate(centers)
    ]


# --- A1: rule (a), the SNR gate -----------------------------------------------------------


def test_a1_train_snr_below_the_gate_is_invalid():
    plan = _plan()
    assert plan.gauntlet.snr.min_snr == 7.1
    below = train_validity(_candidate(snr=7.09), plan)
    at = train_validity(_candidate(snr=7.1), plan)
    assert below["reasons"] == [REASON_TRAIN_SNR]
    assert at["reasons"] == []
    assert below["train_snr"] == 7.09 and below["min_train_snr"] == 7.1
    assert below["applied"] is True


def test_a1_non_finite_train_snr_is_invalid():
    assert train_validity(_candidate(snr=float("nan")), _plan())["reasons"] == [REASON_TRAIN_SNR]


# --- A2: rule (b), duration over period ---------------------------------------------------


def test_a2_duration_period_ratio_boundary():
    plan = _plan()
    assert plan.gauntlet.holdout_by_year.max_train_duration_period_ratio == 0.2
    assert 0.125 / 0.625 == 0.2  # the correctly rounded quotient is the literal
    at = train_validity(_candidate(period=0.625, duration=0.125), plan)
    above = train_validity(_candidate(period=float(np.nextafter(0.625, 0.0)), duration=0.125), plan)
    assert at["reasons"] == [] and at["duration_period_ratio"] == 0.2
    assert above["reasons"] == [REASON_DURATION_RATIO]
    assert above["max_duration_period_ratio"] == 0.2


# --- A3: rule (c), fraction of the hidden year covered by the windows ---------------------

SPANS = [(0.0, 10.0)]


def test_a3_window_fraction_counts_the_union_clipped_to_the_spans():
    assert hidden_window_fraction(_windows([1, 3, 5, 7, 9], 0.5), SPANS) == 0.5
    # Overlapping windows are counted once: [1, 3.5] is 2.5 of 10.
    assert hidden_window_fraction(_windows([2.0, 2.5], 1.0), SPANS) == 0.25
    # A window crossing the end of the span is clipped: [9.5, 10] is 0.5 of 10.
    assert hidden_window_fraction(_windows([10.0], 0.5), SPANS) == 0.05
    # A window across a gap between two spans counts only inside them.
    two = [(0.0, 10.0), (20.0, 30.0)]
    assert hidden_window_fraction(_windows([15.0], 6.0), two) == 0.1
    # Control windows do not count.
    controls = _windows([1, 3, 5, 7, 9], 0.75, kind="control")
    assert hidden_window_fraction(_windows([5.0], 0.5) + controls, SPANS) == 0.1


def test_a3_rule_c_alone():
    plan = _plan()
    assert plan.gauntlet.holdout_by_year.max_hidden_window_fraction == 0.5
    candidate = _candidate(period=2.0, duration=0.3, snr=50.0)  # D/P 0.15: valid for (b)
    half = _windows([1, 3, 5, 7, 9], 0.5)
    more = _windows([1, 3, 5, 7, 9], 0.625)
    at = train_validity(candidate, plan, windows=half, spans=SPANS)
    above = train_validity(candidate, plan, windows=more, spans=SPANS)
    assert at["reasons"] == [] and at["hidden_window_fraction"] == 0.5
    assert above["reasons"] == [REASON_WINDOW_FRACTION]
    assert above["hidden_window_fraction"] == 0.625
    assert above["max_hidden_window_fraction"] == 0.5
    # Without windows (before they are predicted), (c) is not evaluated.
    assert train_validity(candidate, plan)["hidden_window_fraction"] is None


# --- A4: several reasons at once ----------------------------------------------------------


def test_a4_every_reason_is_reported():
    candidate = _candidate(period=1.0, duration=0.4, snr=5.0)
    validity = train_validity(candidate, _plan(), windows=_windows([5.0], 4.0), spans=SPANS)
    assert validity["reasons"] == [REASON_TRAIN_SNR, REASON_DURATION_RATIO, REASON_WINDOW_FRACTION]


# --- A5: an invalid round is INCONCLUSIVE, never FAIL -------------------------------------


def _round_2020(monkeypatch, data, plan, *, candidate_change=None, ephemeris_fn=None):
    """The 2020 round of ``data``, with declared doubles of the train search (the real
    search, then ``candidate_change`` applied to its candidate) and of the ephemeris fit."""
    if candidate_change is not None:

        def search_double(lc, params):
            result = search_period(lc, params)
            return replace(result, candidate=candidate_change(result.candidate))

        monkeypatch.setattr(holdout, "search_period", search_double)
    if ephemeris_fn is not None:
        monkeypatch.setattr(holdout, "fit_linear_ephemeris", ephemeris_fn)
    return holdout._round(data.lc, data.sectors, 2020, plan)


@pytest.mark.parametrize(
    ("change", "reasons"),
    [
        (lambda c: replace(c, snr=6.9), [REASON_TRAIN_SNR]),
        (lambda c: replace(c, duration=0.25 * c.period), [REASON_DURATION_RATIO]),
        (
            lambda c: replace(c, snr=6.9, duration=0.25 * c.period),
            [REASON_TRAIN_SNR, REASON_DURATION_RATIO],
        ),
    ],
    ids=["a", "b", "a+b"],
)
@pytest.mark.parametrize("name", ["vanishing", "planet"])
def test_a5_invalid_train_from_the_search_is_inconclusive(monkeypatch, name, change, reasons):
    data = scenario_data(name, 0)
    result = _round_2020(monkeypatch, data, _plan(), candidate_change=change)
    assert result.status is TestStatus.INCONCLUSIVE
    assert result.metrics["train_validity"]["reasons"] == reasons
    assert result.access_log == []


def test_a5_invalid_windows_are_inconclusive(monkeypatch):
    # Declared doubles: the train candidate is the real one with D/P set to 0.15 (valid
    # for (b)) and the ephemeris has a constant timing error of half a duration (within
    # the timing-uncertainty rule), so the windows (half-width 2 durations, 4 durations
    # wide per 6.67 durations of period) cover more than half of the hidden year.
    data = scenario_data("planet", 0)
    state = {}

    def change(candidate):
        state["duration"] = 0.15 * candidate.period
        return replace(candidate, duration=state["duration"])

    def ephemeris(times):
        first = min(times, key=lambda t: t.epoch)
        sigma = 0.5 * state["duration"]
        return Ephemeris(
            t_ref=first.time,
            n_ref=first.epoch,
            period=3.7,
            cov=((sigma**2, 0.0), (0.0, 0.0)),
            chi2_reduced=1.0,
            n_transits=len(times),
        )

    result = _round_2020(
        monkeypatch, data, _plan(), candidate_change=change, ephemeris_fn=ephemeris
    )
    validity = result.metrics["train_validity"]
    assert validity["duration_period_ratio"] == pytest.approx(0.15)
    assert validity["hidden_window_fraction"] > 0.5
    assert validity["reasons"] == [REASON_WINDOW_FRACTION]
    assert result.status is TestStatus.INCONCLUSIVE
    assert result.access_log == []


# --- A6: the switch -----------------------------------------------------------------------


def test_a6_switch_off_reports_without_acting():
    plan = _plan(require_valid_train=False)
    validity = train_validity(_candidate(snr=6.9), plan)
    assert validity["applied"] is False
    assert validity["reasons"] == [REASON_TRAIN_SNR]


def test_a6_switch_off_leaves_the_round_unchanged(monkeypatch):
    data = scenario_data("vanishing", 0)
    off = _plan(require_valid_train=False)
    result = _round_2020(monkeypatch, data, off, candidate_change=lambda c: replace(c, snr=6.9))
    assert result.metrics["train_validity"]["reasons"] == [REASON_TRAIN_SNR]
    assert result.metrics["train_validity"]["applied"] is False
    assert result.access_log  # the hidden year was read, as before H4
    assert result.status is TestStatus.FAIL


# --- A7: schema ---------------------------------------------------------------------------


@pytest.mark.parametrize("field", ["max_train_duration_period_ratio", "max_hidden_window_fraction"])
@pytest.mark.parametrize("value", [0.0, -0.1, 1.5])
def test_a7_thresholds_outside_the_unit_interval_are_rejected(field, value):
    with pytest.raises(ValidationError, match=field):
        _plan(**{field: value})


def test_a7_defaults_are_resolved(tmp_path):
    claim = write_yaml(tmp_path / "claim.yaml", replicate_claim([target_entry(1, "planet", 3.7)]))
    params = load_claim(claim).claim.test_plan["gauntlet"]["holdout_by_year"]
    assert params["require_valid_train"] is True
    assert params["max_train_duration_period_ratio"] == 0.2
    assert params["max_hidden_window_fraction"] == 0.5
    assert (
        _plan(max_hidden_window_fraction=1.0).gauntlet.holdout_by_year.max_hidden_window_fraction
        == 1.0
    )
