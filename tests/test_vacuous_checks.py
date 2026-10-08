"""TESS pack: checks that examined nothing are INCONCLUSIVE, never PASS (audit before the
v0.2 lock). Each case has a vacuous input (must not PASS) and a real one (must work)."""

import numpy as np
import pytest

from refute.core.verdict import Severity, TestStatus
from refute.packs.tess.battery import (
    check_aperture_depth,
    check_nearby_contamination,
    check_period_alias,
    check_systematics,
)
from refute.packs.tess.ephemeris import Ephemeris
from refute.packs.tess.holdout import HiddenYear, PredictedWindow, _measure
from refute.packs.tess.params import ContaminationParams, TessTestPlan
from refute.packs.tess.synthetic import (
    PLANET,
    make_aux,
    make_lightcurve,
    make_sector_aux,
    make_star,
)
from refute.packs.tess.types import Candidate, Neighbor


def _candidate(**changes):
    values = {
        "period": PLANET.period,
        "t0": PLANET.t0,
        "duration": PLANET.duration,
        "depth": PLANET.depth,
        "depth_err": 4e-5,
        "snr": 50.0,
        "log_likelihood": 1.0,
        "sde": 10.0,
        "n_transits": 14,
    }
    values.update(changes)
    return Candidate(**values)


# --- aperture_depth: transit not seen in the pixels -----------------------------------


def test_aperture_depth_is_inconclusive_when_the_pixels_do_not_show_the_transit():
    noise, _ = make_lightcurve(None, seed=8)
    result = check_aperture_depth(make_aux(noise, seed=8).pixels, _candidate(), TessTestPlan())
    assert result.status is TestStatus.INCONCLUSIVE
    assert "not detected in the pixel photometry" in result.message


def test_aperture_depth_still_passes_a_detected_transit():
    lc, _ = make_lightcurve(PLANET, seed=8)
    result = check_aperture_depth(make_aux(lc, seed=8).pixels, _candidate(), TessTestPlan())
    assert result.status is TestStatus.PASS and result.coverage > 0


# --- period_alias: no in-transit cadence ----------------------------------------------


def test_period_alias_is_inconclusive_without_in_transit_cadences():
    lc, _ = make_lightcurve(PLANET, seed=9)
    # A candidate whose transits all fall in the data gaps: the box is empty.
    gap_epoch = 1325.0 + 13.5  # the mid-sector downlink gap of the first sector
    candidate = _candidate(period=1000.0, t0=gap_epoch, duration=0.1)
    result = check_period_alias(lc, candidate, TessTestPlan())
    assert result.status is TestStatus.INCONCLUSIVE
    assert result.severity is Severity.FATAL
    assert result.coverage == 0


def test_period_alias_measures_a_real_transit():
    lc, _ = make_lightcurve(PLANET, seed=9)
    result = check_period_alias(lc, _candidate(), TessTestPlan())
    assert result.status is TestStatus.PASS and result.coverage > 100


# --- systematics: strict sub-check coverage -------------------------------------------


def _aux(lc, crowd=0.98):
    return make_sector_aux(lc, crowd, np.random.default_rng(0))


def test_systematics_is_inconclusive_when_crowdsap_is_missing():
    lc, _ = make_lightcurve(PLANET, seed=6)
    aux = _aux(lc)
    for a in aux:
        a.crowdsap = None
    result = check_systematics(aux, _candidate(), TessTestPlan())
    assert result.status is TestStatus.INCONCLUSIVE
    assert "no CROWDSAP" in result.message
    assert result.metrics["sub_checks_not_run"]["sap_vs_pdcsap"] == "no CROWDSAP value"


def test_systematics_is_inconclusive_with_too_few_transits_for_the_dump_check():
    lc, _ = make_lightcurve(PLANET, seed=6)
    short = lc.select(lc.time < PLANET.t0 + 1.5 * PLANET.period)  # two transits only
    result = check_systematics(_aux(short), _candidate(), TessTestPlan())
    assert result.status is TestStatus.INCONCLUSIVE
    assert "momentum_dumps" in result.metrics["sub_checks_not_run"]


def test_systematics_passes_only_when_every_sub_check_ran():
    lc, _ = make_lightcurve(PLANET, seed=6)
    result = check_systematics(_aux(lc), _candidate(), TessTestPlan())
    assert result.status is TestStatus.PASS
    assert result.coverage == 3 and result.metrics["sub_checks_not_run"] == {}
    assert result.metrics["n_momentum_dumps"] > 0


# --- nearby_contamination: what was examined is explicit ------------------------------


def test_contamination_with_an_empty_query_passes_and_says_the_query_was_made():
    result = check_nearby_contamination(
        [], make_star(), 0.01, [0.99], ContaminationParams(), query_radius_arcsec=120.0
    )
    assert result.status is TestStatus.PASS and result.coverage == 1
    assert "TIC cone query of 120 arcsec returned 0 source(s)" in result.message


def test_contamination_without_crowdsap_is_inconclusive():
    result = check_nearby_contamination(
        [Neighbor(2, 18.0, 10.0)], make_star(), 0.01, [], ContaminationParams(), 120.0
    )
    assert result.status is TestStatus.INCONCLUSIVE
    assert "no CROWDSAP" in result.message


# --- holdout: windows that cannot be measured -----------------------------------------


@pytest.mark.parametrize("measurable", [False, True])
def test_holdout_windows_that_cannot_be_measured_count_as_none(measurable):
    lc, _ = make_lightcurve(PLANET)
    hidden = lc.select(lc.year == 2020)
    plan = TessTestPlan()
    cadence = 2.0 / 1440
    half = PLANET.duration / 2
    epochs = range(199, 203)
    ephemeris = Ephemeris(
        t_ref=PLANET.t0 + 200 * PLANET.period,
        n_ref=200,
        period=PLANET.period,
        cov=((1e-8, 0.0), (0.0, 0.0)),
        chi2_reduced=1.0,
        n_transits=10,
    )
    # Unmeasurable: the window is exactly the box and the baseline band holds only a
    # few cadences, so no window has the 10 out-of-box points a depth needs.
    outer = half + (3 * cadence if not measurable else 1.5 * PLANET.duration)
    windows = [
        PredictedWindow("transit", e, PLANET.t0 + e * PLANET.period, half, half, outer)
        for e in epochs
    ]
    year = HiddenYear(hidden, windows, plan)
    measured = _measure(
        year, windows, ephemeris, PLANET.duration, cadence, plan.gauntlet.holdout_by_year
    )
    if measurable:
        assert measured["n_windows_with_data"] >= 2 and "snr" in measured
    else:
        assert measured["n_windows_with_data"] == 0
        assert measured["n_windows_unmeasurable"] >= 2


def test_run_holdout_with_unmeasurable_windows_is_inconclusive_end_to_end(monkeypatch):
    # v0.1 code raised KeyError('snr') when windows had data but none could be
    # measured. Force that state through the full round and test: every window
    # depth is unmeasurable (as with too few out-of-box points).
    import refute.packs.tess.holdout as holdout
    from refute.core.verdict import aggregate
    from refute.packs.tess.holdout import run_holdout

    monkeypatch.setattr(holdout, "_window_depth", lambda *args, **kwargs: None)
    lc, sectors = make_lightcurve(PLANET, seed=3)
    plan = TessTestPlan.model_validate({"search": {"period_max_days": 6.0}})
    outcome = run_holdout(lc, sectors, plan)
    assert outcome.test.status is TestStatus.INCONCLUSIVE
    assert outcome.test.coverage == 0
    assert outcome.rounds and all(r.status is TestStatus.INCONCLUSIVE for r in outcome.rounds)
    for r in outcome.rounds:
        assert r.metrics["n_windows_with_data"] == 0
        assert r.metrics["n_windows_unmeasurable"] >= 2
    gate = holdout.TestResult(
        "snr", TestStatus.PASS, Severity.GATE, "", coverage=10, coverage_unit="transits"
    )
    verdict, _ = aggregate([gate, outcome.test])
    assert verdict.value == "INCONCLUSIVE"
