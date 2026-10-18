"""v0.2.1 issue #23: the report says how blind the holdout is, and what it says is true of
the code (docs/validation/v0.2.1/reopen/issue-23-acceptance.md)."""

import numpy as np
import pytest

from refute.packs.tess import holdout
from refute.packs.tess.holdout import HiddenYear, HoldoutAccessError, PredictedWindow
from refute.packs.tess.params import TessTestPlan
from refute.packs.tess.report import HOLDOUT_BLINDNESS_NOTE, render_report
from refute.packs.tess.synthetic import CORRELATED_PROFILE, PLANET, make_lightcurve

OLD_SENTENCE = "read only inside the predicted windows"


def _result(rounds):
    return {
        "target_key": "TIC-1",
        "verdict": "SURVIVED",
        "verdict_reason": "every test passed",
        "tests": [],
        "holdout_rounds": rounds,
    }


def _hidden_year(**noise):
    lc, _ = make_lightcurve(PLANET, seed=2, trend_amplitude=0.002, **noise)
    hidden = lc.select(lc.year == 2020)
    epoch = 200
    t0 = PLANET.t0 + epoch * PLANET.period
    windows = [
        PredictedWindow("transit", n, t0 + (n - epoch) * PLANET.period, 0.06, 0.08, 0.2)
        for n in range(epoch - 3, epoch + 8)
    ]
    return hidden, windows


# --- A. The report -----------------------------------------------------------------------


def test_a1_the_report_states_how_blind_the_holdout_is():
    rounds = [{"hidden_year": 2020, "status": "PASS", "metrics": {"hidden_snr": 9.0}}]
    text = render_report(_result(rounds), {"claim_kind": "calibration"})
    assert "## Blind holdout by year" in text
    assert HOLDOUT_BLINDNESS_NOTE in text
    assert OLD_SENTENCE not in text


def test_a1_the_note_names_the_unlogged_detrending_and_the_logged_reads():
    assert "whole hidden year is detrended once" in HOLDOUT_BLINDNESS_NOTE
    # Amendment 2: only rounds that reach the measurement build HiddenYear; the mask
    # reaches the inner edge of each baseline band; the clipping can drop hidden cadences.
    assert "In each round that reaches the measurement" in HOLDOUT_BLINDNESS_NOTE
    assert "inner edge of its baseline band" in HOLDOUT_BLINDNESS_NOTE
    assert "outlier clipping can drop hidden cadences" in HOLDOUT_BLINDNESS_NOTE
    assert "not logged" in HOLDOUT_BLINDNESS_NOTE
    assert "every such read is logged" in HOLDOUT_BLINDNESS_NOTE
    assert OLD_SENTENCE not in HOLDOUT_BLINDNESS_NOTE


def test_a3_rounds_of_the_corrections_add_the_replica_note():
    """Issue #23 after M4 pieces 4 and 5 (map Amendment 17): with the corrections on, the hidden
    year also masks and reads the replica spans, first; the report says so only then."""
    from refute.packs.tess.report import HOLDOUT_REPLICA_NOTE

    m4 = [{"hidden_year": 2020, "status": "PASS", "metrics": {"corrections_path": "m4_holdout"}}]
    text = render_report(_result(m4), {"claim_kind": "calibration"})
    assert HOLDOUT_BLINDNESS_NOTE in text and HOLDOUT_REPLICA_NOTE in text
    assert "replica spans" in HOLDOUT_REPLICA_NOTE and "before any window" in HOLDOUT_REPLICA_NOTE
    m3 = [{"hidden_year": 2020, "status": "PASS", "metrics": {"hidden_snr": 9.0}}]
    assert HOLDOUT_REPLICA_NOTE not in render_report(_result(m3), {"claim_kind": "calibration"})


def test_a2_no_rounds_no_holdout_section():
    text = render_report(_result([]), {"claim_kind": "calibration"})
    assert "Blind holdout by year" not in text
    assert HOLDOUT_BLINDNESS_NOTE not in text


# --- B. The sentence is true of the code -------------------------------------------------


@pytest.mark.parametrize(
    "noise",
    [{}, CORRELATED_PROFILE],
    ids=["white", "correlated"],  # correlated: R-M1 of correlated-noise-acceptance.md
)
def test_b1_every_hidden_cadence_reaches_the_detrending_and_nothing_is_logged(monkeypatch, noise):
    hidden, windows = _hidden_year(**noise)
    calls = []
    real = holdout.detrend

    def spy(lc, params, mask=None):
        calls.append({"n": len(lc), "time": lc.time.copy(), "mask": np.array(mask)})
        return real(lc, params, mask=mask)

    monkeypatch.setattr(holdout, "detrend", spy)
    year = HiddenYear(hidden, windows, TessTestPlan())
    assert len(calls) == 1
    assert calls[0]["n"] == len(hidden)
    assert np.array_equal(calls[0]["time"], hidden.time)
    expected = np.zeros(len(hidden), dtype=bool)
    for w in windows:
        expected |= np.abs(hidden.time - w.t_pred) <= w.baseline_inner
    assert np.array_equal(calls[0]["mask"], expected)
    assert 0 < int(expected.sum()) < len(hidden)
    assert year.access_log == []


def test_b2_reads_are_logged_and_unregistered_reads_are_refused():
    hidden, windows = _hidden_year()
    year = HiddenYear(hidden, windows, TessTestPlan())
    w = windows[3]
    year.window(w.t_pred, w.half_width)
    year.local_baseline(w.t_pred, w.half_width)
    assert [e["kind"] for e in year.access_log] == ["transit-window", "transit-baseline"]
    with pytest.raises(HoldoutAccessError):
        year.window(w.t_pred + 0.5, w.half_width)
    assert len(year.access_log) == 2
