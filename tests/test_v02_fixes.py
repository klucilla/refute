"""Regression tests for the v0.1 issues fixed in v0.2 (#1, #2, #3), on synthetic data."""

import numpy as np
import pytest
from typer.testing import CliRunner

from refute.core.verdict import TestStatus
from refute.packs.tess.gauntlet import check_plausibility
from refute.packs.tess.holdout import HiddenYear, PredictedWindow, run_holdout
from refute.packs.tess.params import PlausibilityParams, TessTestPlan
from refute.packs.tess.pipeline import data_quality_warnings
from refute.packs.tess.synthetic import (
    PLANET,
    SignalSpec,
    make_data,
    make_lightcurve,
    make_star,
    trapezoid,
)
from refute.packs.tess.types import Candidate, LightCurveData

# --- issue #2: hidden-year detrending and uncertain timing ---------------------------


def test_hidden_year_detrending_window_grows_with_the_masked_span():
    lc, _ = make_lightcurve(PLANET)
    hidden = lc.select(lc.year == 2020)
    t_pred = PLANET.t0 + 200 * PLANET.period
    wide = PredictedWindow("transit", 200, t_pred, 0.45, 0.50, 0.70)
    narrow = PredictedWindow("transit", 200, t_pred, 0.06, 0.08, 0.2)
    assert HiddenYear(hidden, [wide], TessTestPlan()).detrend_window_days == pytest.approx(3.0)
    assert HiddenYear(hidden, [narrow], TessTestPlan()).detrend_window_days == pytest.approx(1.0)


def _jittered(spec: SignalSpec, jitter_minutes: float, sector_starts, seed: int):
    """A real planet whose transit times scatter (as with poor timing in a short train set)."""
    lc, sectors = make_lightcurve(None, sector_starts=sector_starts, noise_ppm=900.0, seed=seed)
    rng = np.random.default_rng(seed)
    epochs = np.round((lc.time - spec.t0) / spec.period).astype(int)
    shifts = {e: rng.normal(0.0, jitter_minutes / 1440.0) for e in np.unique(epochs)}
    deficit = np.zeros(lc.time.size)
    for epoch, shift in shifts.items():
        sel = epochs == epoch
        deficit[sel] = trapezoid(
            lc.time[sel], spec.period, spec.t0 + shift, spec.depth, spec.duration, 0.15
        )
    flux = lc.flux - deficit
    return LightCurveData(lc.time, flux, lc.flux_err, lc.sector, lc.year), sectors


def test_one_training_sector_far_from_the_hidden_year_does_not_refute_a_planet():
    # One sector in 2018, one in 2023: each round trains on a single sector and must
    # project the ephemeris about five years. With realistic timing scatter the
    # windows become wider than the transit; such a round must not FAIL.
    spec = SignalSpec(period=3.97, t0=1326.2, depth=0.006, duration=2.3 / 24)
    lc, sectors = _jittered(spec, 15.0, (1325.0, 3100.0), seed=11)
    plan = TessTestPlan.model_validate({"search": {"period_max_days": 6.0}})
    outcome = run_holdout(lc, sectors, plan)
    assert outcome.test.status is not TestStatus.FAIL
    assert all(r.status is not TestStatus.FAIL for r in outcome.rounds)


# --- issue #3: TIC rows that do not describe one star --------------------------------


def _candidate(depth=0.257):
    return Candidate(3.02, 0.0, 0.1, depth, 1e-4, 80.0, 1.0, 10.0, 10)


@pytest.mark.parametrize("disposition", ["SPLIT", "DUPLICATE", "ARTIFACT", "split"])
def test_unreliable_tic_disposition_makes_plausibility_inconclusive(disposition):
    star = make_star(disposition=disposition)
    result = check_plausibility(_candidate(), star, PlausibilityParams())
    assert result.status is TestStatus.INCONCLUSIVE
    assert disposition.upper() in result.message.upper()


def test_normal_tic_row_still_refutes_a_deep_eclipse():
    result = check_plausibility(_candidate(), make_star(), PlausibilityParams())
    assert result.status is TestStatus.FAIL


def test_tmag_mismatch_is_a_data_quality_warning():
    lc, sectors = make_lightcurve(PLANET)
    data = make_data(lc, sectors, make_star(tmag=18.42))
    warnings = data_quality_warnings({"catalog": {"TESS Mag": "11.42"}}, data, TessTestPlan())
    assert any("Tmag" in w for w in warnings)
    data_ok = make_data(lc, sectors, make_star(tmag=11.5))
    assert data_quality_warnings({"catalog": {"TESS Mag": "11.42"}}, data_ok, TessTestPlan()) == []


# --- issue #1: printing never turns a completed run into a failure ------------------


def test_cli_exit_code_survives_a_closed_output_stream(tmp_path, monkeypatch):
    import refute.cli as cli
    from refute.core.run import RunOutcome

    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "summary.md").write_text("# summary\n", encoding="utf-8")
    monkeypatch.setattr(
        "refute.core.run.execute_run", lambda *a, **k: RunOutcome(exit_code=0, run_dir=run_dir)
    )

    def closed(*_args, **_kwargs):
        raise ValueError("I/O operation on closed file")

    monkeypatch.setattr(cli.typer, "echo", closed)
    result = CliRunner().invoke(cli.app, ["calibrate", "--claim", "x.yaml", "--offline"])
    assert result.exit_code == 0
