"""Gauntlet v0.2 battery: every test has a synthetic case that must fail and one that
must pass (docs/gauntlet-tess-v0.2.md). No network: all data are synthetic."""

import math

import numpy as np
import pytest

from refute.core.verdict import Severity, TestStatus
from refute.packs.tess.battery import (
    check_centroid_shift,
    check_nearby_contamination,
    check_period_alias,
    check_systematics,
    gaussian_sigma_from_chi2,
)
from refute.packs.tess.params import ContaminationParams, TessTestPlan
from refute.packs.tess.synthetic import (
    PLANET,
    SignalSpec,
    make_aux,
    make_lightcurve,
    make_sector_aux,
    make_star,
)
from refute.packs.tess.types import Candidate, Neighbor, PixelData


def _test(analysis, name):
    return next(t for t in analysis.tests if t.name == name)


def _candidate(spec: SignalSpec = PLANET) -> Candidate:
    return Candidate(
        period=spec.period,
        t0=spec.t0,
        duration=spec.duration,
        depth=spec.depth,
        depth_err=spec.depth / 50,
        snr=50.0,
        log_likelihood=1.0,
        sde=10.0,
        n_transits=14,
    )


# --- centroid_shift -----------------------------------------------------------------


def test_centroid_shift_refutes_a_signal_on_a_neighbor(scenario_results):
    test = _test(scenario_results["blend"], "centroid_shift")
    assert test.status is TestStatus.FAIL and test.severity is Severity.FATAL
    assert test.metrics["mean_offset_pixels"] >= 0.5
    assert test.metrics["offset_sigma"] >= 3.0


def test_centroid_shift_passes_a_transit_on_the_target(scenario_results):
    for name in ("planet", "planet_three_years", "eb_equal"):
        test = _test(scenario_results[name], "centroid_shift")
        assert test.status is TestStatus.PASS, name
        assert test.metrics["mean_offset_pixels"] < 0.5


def test_centroid_shift_is_inconclusive_without_pixels_or_position():
    lc, _ = make_lightcurve(PLANET, seed=1)
    plan = TessTestPlan()
    assert check_centroid_shift([], _candidate(), plan).status is TestStatus.INCONCLUSIVE
    pixels = make_aux(lc, seed=1).pixels
    unknown = [PixelData(p.sector, p.time, p.flux, p.flux_err, p.aperture, None) for p in pixels]
    result = check_centroid_shift(unknown, _candidate(), plan)
    assert result.status is TestStatus.INCONCLUSIVE
    assert all("WCS" in reason for reason in result.metrics["skipped_sectors"].values())


@pytest.mark.parametrize(
    ("chi2", "dof", "expected"),
    [(0.0, 2, 0.0), (2 * math.log(2), 2, 0.0), (9.21, 2, 2.33), (1e5, 4, 37.0), (80.0, 2, 8.59)],
)
def test_gaussian_sigma_from_chi2(chi2, dof, expected):
    assert gaussian_sigma_from_chi2(chi2, dof) == pytest.approx(expected, abs=0.01)


# --- aperture_depth -----------------------------------------------------------------


def test_aperture_depth_refutes_a_signal_outside_the_core(scenario_results):
    test = _test(scenario_results["blend"], "aperture_depth")
    assert test.status is TestStatus.FAIL and test.severity is Severity.FATAL
    assert test.metrics["depth_ratio_large_to_core"] >= 1.2


def test_aperture_depth_passes_a_transit_on_the_target(scenario_results):
    for name in ("planet", "eb_equal", "vanishing"):
        test = _test(scenario_results[name], "aperture_depth")
        assert test.status is TestStatus.PASS, name
        assert test.metrics["depth_ratio_large_to_core"] < 1.2


def test_blend_is_refuted_end_to_end(scenario_results):
    analysis = scenario_results["blend"]
    assert analysis.verdict == "REFUTED"
    assert _test(analysis, "plausibility").status is TestStatus.PASS  # looks like a planet


# --- nearby_contamination -----------------------------------------------------------


def _contamination(neighbors, depth=0.01, crowds=(0.99,), star=None):
    return check_nearby_contamination(
        neighbors, star or make_star(tmag=10.0), depth, list(crowds), ContaminationParams()
    )


def test_contamination_warns_when_a_close_neighbor_could_produce_the_signal():
    # 2 mag fainter at 10 arcsec: needs a 6.3% eclipse to give a 1% depth.
    result = _contamination([Neighbor(2, 12.0, 10.0)])
    assert result.status is TestStatus.FAIL and result.severity is Severity.WARNING
    assert result.metrics["viable_neighbors"][0]["required_eclipse_depth"] == pytest.approx(
        0.0631, rel=1e-2
    )


def test_contamination_passes_when_no_close_neighbor_could_produce_the_signal():
    # 8 mag fainter at 10 arcsec needs a > 100% eclipse; a bright star at 60 arcsec is
    # left to the centroid and aperture tests.
    result = _contamination([Neighbor(2, 18.0, 10.0), Neighbor(3, 9.0, 60.0)])
    assert result.status is TestStatus.PASS
    assert result.metrics["viable_neighbors"] == []


def test_contamination_warns_on_crowding_and_ignores_non_star_rows():
    assert _contamination([], crowds=(0.6, 0.7)).status is TestStatus.FAIL
    artifact = Neighbor(2, 10.0, 5.0, disposition="ARTIFACT")
    assert _contamination([artifact]).status is TestStatus.PASS


def test_contamination_is_inconclusive_without_a_neighbor_query():
    assert _contamination(None).status is TestStatus.INCONCLUSIVE
    no_mag = make_star(tmag=None)
    assert _contamination([], star=no_mag).status is TestStatus.INCONCLUSIVE


# --- period_alias -------------------------------------------------------------------


def test_period_alias_refutes_a_sinusoid(scenario_results):
    test = _test(scenario_results["sinusoid"], "period_alias")
    assert test.status is TestStatus.FAIL and test.severity is Severity.FATAL
    assert test.metrics["box_delta_bic"] < 10.0


def test_period_alias_passes_transits_and_eclipses(scenario_results):
    for name in ("planet", "eb_secondary", "eb_odd_even", "blend"):
        test = _test(scenario_results[name], "period_alias")
        assert test.status is TestStatus.PASS, name
        assert test.metrics["box_delta_bic"] > 10.0


def test_period_alias_passes_a_transit_whose_period_matches_stellar_variability():
    # The star varies with the planet's period: a sinusoid alone cannot explain the
    # transit, so the box is still needed and the planet is not refuted.
    lc, _ = make_lightcurve(PLANET, trend_amplitude=0.003, trend_period_days=PLANET.period, seed=4)
    result = check_period_alias(lc, _candidate(), TessTestPlan())
    assert result.status is TestStatus.PASS


def test_period_alias_warns_near_a_systematic_period():
    spec = SignalSpec(period=13.7 / 4, t0=1326.0, depth=0.003, duration=2.5 / 24)
    lc, _ = make_lightcurve(spec, seed=5)
    result = check_period_alias(lc, _candidate(spec), TessTestPlan())
    assert result.status is TestStatus.FAIL and result.severity is Severity.WARNING
    assert result.metrics["near_systematic_periods_days"]


# --- systematics --------------------------------------------------------------------


def _aux(lc, **kwargs):
    return make_sector_aux(lc, 0.98, np.random.default_rng(0), **kwargs)


def test_systematics_passes_a_clean_transit(scenario_results):
    test = _test(scenario_results["planet"], "systematics")
    assert test.status is TestStatus.PASS
    lc, _ = make_lightcurve(PLANET, seed=6)
    assert check_systematics(_aux(lc), _candidate(), TessTestPlan()).status is TestStatus.PASS


def test_systematics_warns_when_transits_line_up_with_momentum_dumps():
    lc, _ = make_lightcurve(PLANET, seed=6)
    dumps = {s: PLANET.t0 + PLANET.period * np.arange(-5, 400) for s in lc.sectors}
    result = check_systematics(_aux(lc, dumps=dumps), _candidate(), TessTestPlan())
    assert result.status is TestStatus.FAIL and result.severity is Severity.WARNING
    assert result.metrics["fraction_near_dumps"] == 1.0


def test_systematics_warns_when_sap_disagrees_with_pdcsap():
    lc, _ = make_lightcurve(PLANET, seed=6)
    aux = _aux(lc)
    for a in aux:
        a.sap_flux = np.ones_like(a.sap_flux) + np.random.default_rng(1).normal(
            0, 6e-4, a.sap_flux.size
        )
    result = check_systematics(aux, _candidate(), TessTestPlan())
    assert result.status is TestStatus.FAIL
    assert result.metrics["sap_relative_difference"] > 0.5


def test_systematics_warns_when_the_background_rises_in_transit():
    lc, _ = make_lightcurve(PLANET, seed=6)
    rise = {s: PLANET.depth * (1.0 - _box_model(lc.time[lc.sector == s])) for s in lc.sectors}
    result = check_systematics(_aux(lc, background_series=rise), _candidate(), TessTestPlan())
    assert result.status is TestStatus.FAIL
    assert result.metrics["background_rise_fraction_of_depth"] > 0.5


def _box_model(time):
    from refute.packs.tess.synthetic import signal_model

    return 1.0 - (1.0 - signal_model(time, PLANET)) / PLANET.depth


def test_systematics_is_inconclusive_without_auxiliary_data():
    result = check_systematics([], _candidate(), TessTestPlan())
    assert result.status is TestStatus.INCONCLUSIVE and result.severity is Severity.WARNING
