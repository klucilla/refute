"""M4 piece 3: transit times with an ingress model (revision 3 of the corrections plan, section 3;
docs/validation/v0.2.1/reopen/m4-implementation-map.md, piece 3 and Amendment 3).

The case of the numeric criteria is declared in Amendment 3: ``synthetic.PLANET``, white noise of
600 ppm, 2-minute cadence, the two default sectors, at the injected ephemeris, seeds 0, 1, 2, ...
until at least 200 transits are measured. The switch off is covered by P1 of
``test_rednoise_propagation.py`` (the 13 reference analyses, byte for byte).
"""

import numpy as np
import pytest

from refute.packs.tess import synthetic
from refute.packs.tess.ephemeris import fit_linear_ephemeris
from refute.packs.tess.events import per_point_sigma, transit_mask
from refute.packs.tess.params import TessTestPlan
from refute.packs.tess.pipeline import analyze_data
from refute.packs.tess.rednoise import NoiseEstimate, SectorNoise
from refute.packs.tess.timing import (
    TimingTemplate,
    corrected_transit_times,
    fit_timing_template,
    measure_template_times,
)
from refute.packs.tess.types import LightCurveData

CADENCE = 120.0 / 86400.0
PLANET = synthetic.PLANET
TAU = PLANET.ingress_fraction * PLANET.duration
SIGMA_W = 600e-6
CARTER = (SIGMA_W / PLANET.depth) * np.sqrt(TAU * CADENCE / 2.0)
ON = {"enabled": True}


def _plan(corrections=None):
    plan = synthetic.fast_plan_dict()
    if corrections is not None:
        plan["gauntlet"] = {"corrections": corrections}
    return TessTestPlan.model_validate(plan)


def _sigma(lc):
    mask = transit_mask(lc.time, PLANET.period, PLANET.t0, PLANET.duration)
    return per_point_sigma(lc, mask)


def _noise(sectors, beta=None, excluded=()):
    beta = beta or {}
    return NoiseEstimate(
        11,
        {
            s: SectorNoise(s, 11, 100, SIGMA_W, float("nan"), 0.0, beta.get(s, 1.0), s in excluded)
            for s in sectors
        },
    )


def _template():
    return TimingTemplate(PLANET.depth, PLANET.duration, TAU)


# --- the template -----------------------------------------------------------------------------


def test_the_template_fit_recovers_a_low_noise_trapezoid():
    lc, _ = synthetic.make_lightcurve(PLANET, noise_ppm=50.0, seed=0)
    template = fit_timing_template(
        lc, PLANET.period, PLANET.t0, 1.2 * PLANET.duration, _sigma(lc), CADENCE
    )
    assert template is not None
    assert template.depth == pytest.approx(PLANET.depth, rel=0.03)
    assert template.t14 == pytest.approx(PLANET.duration, rel=0.03)
    assert template.tau == pytest.approx(TAU, rel=0.15)


def test_no_template_without_a_dip():
    lc, _ = synthetic.make_lightcurve(None, seed=0)
    bump = synthetic.trapezoid(lc.time, PLANET.period, PLANET.t0, 0.002, PLANET.duration, 0.15)
    raised = LightCurveData(lc.time, lc.flux + bump, lc.flux_err, lc.sector, lc.year)
    template = fit_timing_template(
        raised, PLANET.period, PLANET.t0, PLANET.duration, _sigma(raised), CADENCE
    )
    assert template is None


# --- the two numeric criteria (white, the declared case) ---------------------------------------


@pytest.fixture(scope="module")
def seeded_transits():
    plan = _plan(ON)
    rows = []  # (error, pull)
    seed = 0
    while len(rows) < 200:
        lc, _ = synthetic.make_lightcurve(PLANET, seed=seed)
        result = corrected_transit_times(
            lc, PLANET.period, PLANET.t0, PLANET.duration, _sigma(lc), plan
        )
        for t in result.times:
            truth = PLANET.t0 + t.epoch * PLANET.period
            rows.append((t.error, (t.time - truth) / t.error))
        seed += 1
    return np.array(rows)


def test_the_per_transit_error_is_within_30_percent_of_carter(seeded_transits):
    ratio = float(np.median(seeded_transits[:, 0] / CARTER))
    assert 0.7 <= ratio <= 1.3, (ratio, CARTER * 1440)


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="m4-implementation-map.md, Amendment 4: |pull| <= 2 in 0.919 of 210 at the declared "
    "case; the criterion is not met (option (c)); the mark does not satisfy it",
)
def test_the_pulls_of_200_seeded_transits_are_within_the_k_margins(seeded_transits):
    pulls = seeded_transits[:, 1]
    assert pulls.size >= 200
    one = float(np.mean(np.abs(pulls) <= 1.0))
    two = float(np.mean(np.abs(pulls) <= 2.0))
    median = float(np.median(pulls))
    assert 0.60 <= one <= 0.76, (one, two, median)
    assert 0.92 <= two <= 0.98, (one, two, median)
    assert abs(median) <= 0.2, (one, two, median)


# --- mechanisms ---------------------------------------------------------------------------------


def _shifted_lc(shift_epoch, shift_days, seed=0, noise_ppm=100.0):
    lc, _ = synthetic.make_lightcurve(None, noise_ppm=noise_ppm, seed=seed)
    epochs = np.round((lc.time - PLANET.t0) / PLANET.period).astype(int)
    t0 = np.where(epochs == shift_epoch, PLANET.t0 + shift_days, PLANET.t0)
    deficit = synthetic.trapezoid(
        lc.time - (t0 - PLANET.t0), PLANET.period, PLANET.t0, PLANET.depth, PLANET.duration, 0.15
    )
    return LightCurveData(lc.time, lc.flux - deficit, lc.flux_err, lc.sector, lc.year)


def test_a_minimum_on_the_edge_of_the_scan_is_discarded():
    lc = _shifted_lc(3, 0.8 * PLANET.duration)
    result = measure_template_times(
        lc, PLANET.period, PLANET.t0, _template(), _sigma(lc), _noise((1, 2)), cadence_days=CADENCE
    )
    epochs = [t.epoch for t in result.times]
    assert 3 not in epochs
    assert {2, 4} <= set(epochs)


def test_same_input_same_times():
    lc, _ = synthetic.make_lightcurve(PLANET, seed=4)
    plan = _plan(ON)
    a = corrected_transit_times(lc, PLANET.period, PLANET.t0, PLANET.duration, _sigma(lc), plan)
    b = corrected_transit_times(lc, PLANET.period, PLANET.t0, PLANET.duration, _sigma(lc), plan)
    assert a.times == b.times and len(a.times) > 5
    assert a.template == b.template


def test_the_error_is_scaled_by_beta_of_the_transit_sector():
    lc, _ = synthetic.make_lightcurve(PLANET, seed=1)
    sigma = _sigma(lc)
    one = measure_template_times(
        lc, PLANET.period, PLANET.t0, _template(), sigma, _noise((1, 2)), cadence_days=CADENCE
    )
    two = measure_template_times(
        lc,
        PLANET.period,
        PLANET.t0,
        _template(),
        sigma,
        _noise((1, 2), beta={1: 2.0}),
        cadence_days=CADENCE,
    )
    assert [t.epoch for t in one.times] == [t.epoch for t in two.times]
    checked = 0
    for a, b in zip(one.times, two.times, strict=True):
        assert a.time == b.time
        sector = int(lc.sector[np.argmin(np.abs(lc.time - a.time))])
        if a.error > 0.5 * CADENCE:  # the floor does not bind
            expected = 2.0 if sector == 1 else 1.0
            assert b.error == pytest.approx(expected * a.error, rel=1e-12)
            checked += 1
    assert checked > 5


def test_transits_of_an_excluded_sector_are_dropped_and_counted():
    lc, _ = synthetic.make_lightcurve(PLANET, seed=2)
    result = measure_template_times(
        lc,
        PLANET.period,
        PLANET.t0,
        _template(),
        _sigma(lc),
        _noise((1, 2), excluded=(2,)),
        cadence_days=CADENCE,
    )
    assert len(result.times) > 0
    assert result.dropped.get("excluded_sector", 0) > 0
    sector_two_start = float(lc.time[lc.sector == 2].min())
    assert all(t.time < sector_two_start for t in result.times)


def test_an_undetermined_estimate_gives_no_transit_times():
    lc, _ = synthetic.make_lightcurve(PLANET, seed=2)
    result = measure_template_times(
        lc,
        PLANET.period,
        PLANET.t0,
        _template(),
        _sigma(lc),
        _noise((1, 2), excluded=(1, 2)),
        cadence_days=CADENCE,
    )
    assert result.times == []


def test_the_scale_of_beta_is_n_tau():
    lc, _ = synthetic.make_lightcurve(PLANET, seed=3)
    result = corrected_transit_times(
        lc, PLANET.period, PLANET.t0, PLANET.duration, _sigma(lc), _plan(ON)
    )
    assert result.noise is not None
    assert result.noise.n == max(1, round(result.template.tau / CADENCE))


# --- the wiring: the global ephemeris and the holdout's train timing ----------------------------


def test_with_the_switch_on_the_ephemerides_come_from_the_template_times(monkeypatch):
    import refute.packs.tess.holdout as holdout_module
    import refute.packs.tess.pipeline as pipeline_module

    calls = {"pipeline": [], "holdout": []}

    def spy(where, real):
        def wrapper(*args, **kwargs):
            result = real(*args, **kwargs)
            calls[where].append(result)
            return result

        return wrapper

    monkeypatch.setattr(
        pipeline_module,
        "corrected_transit_times",
        spy("pipeline", pipeline_module.corrected_transit_times),
    )
    monkeypatch.setattr(
        holdout_module,
        "corrected_transit_times",
        spy("holdout", holdout_module.corrected_transit_times),
    )
    data = synthetic.scenario_data("planet", 0)
    analysis = analyze_data(data, _plan(ON))
    assert len(calls["pipeline"]) == 1
    result = calls["pipeline"][0]
    expected = fit_linear_ephemeris(result.times)
    assert analysis.gauntlet.ephemeris == expected
    assert len(calls["holdout"]) >= 1

    calls["pipeline"].clear()
    calls["holdout"].clear()
    analyze_data(data, _plan())
    assert calls == {"pipeline": [], "holdout": []}
