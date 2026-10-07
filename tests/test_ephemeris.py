import numpy as np

from refute.packs.tess.detrend import detrend
from refute.packs.tess.ephemeris import TransitTime, fit_linear_ephemeris, measure_transit_times
from refute.packs.tess.events import per_point_sigma, transit_mask
from refute.packs.tess.params import DetrendParams
from refute.packs.tess.synthetic import PLANET, make_lightcurve


def test_linear_fit_recovers_period_and_epoch():
    rng = np.random.default_rng(1)
    period, t0 = 2.345678, 1000.123
    times = [TransitTime(n, t0 + n * period + rng.normal(0, 1e-4), 1e-4) for n in range(0, 40, 3)]
    eph = fit_linear_ephemeris(times)
    assert abs(eph.period - period) < 5 * eph.period_err
    t_pred, sigma = eph.predict(0)
    assert abs(t_pred - t0) < 5 * sigma
    _, sigma_far = eph.predict(500)
    assert sigma_far > sigma


def test_transit_times_are_measured_on_synthetic_data():
    lc, _ = make_lightcurve(PLANET, seed=5)
    mask = transit_mask(lc.time, PLANET.period, PLANET.t0, PLANET.duration)
    flat = detrend(lc, DetrendParams(), mask=mask)
    sigma = per_point_sigma(
        flat, transit_mask(flat.time, PLANET.period, PLANET.t0, PLANET.duration)
    )
    times = measure_transit_times(
        flat,
        PLANET.period,
        PLANET.t0,
        PLANET.duration * 0.9,
        PLANET.depth,
        sigma,
        cadence_days=120 / 86400,
    )
    assert len(times) >= 10
    for t in times:
        truth = PLANET.t0 + t.epoch * PLANET.period
        assert abs(t.time - truth) < 6 / 1440  # within 6 minutes
    eph = fit_linear_ephemeris(times)
    assert abs(eph.period - PLANET.period) < 1e-4
