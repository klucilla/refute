import numpy as np

from refute.packs.tess.detrend import detrend, robust_sigma
from refute.packs.tess.events import transit_mask
from refute.packs.tess.params import DetrendParams
from refute.packs.tess.synthetic import PLANET, make_lightcurve


def test_quadratic_detrending_removes_stellar_variability():
    lc, _ = make_lightcurve(None, noise_ppm=100.0, trend_amplitude=0.01, trend_period_days=3.0)
    flat = detrend(lc, DetrendParams())
    # 1% sinusoidal variability (3-day period) leaves residuals well below the noise level.
    assert robust_sigma(flat.flux - 1.0) < 1.3e-4
    assert abs(np.median(flat.flux) - 1.0) < 2e-5


def test_transits_are_never_clipped_and_masked_detrending_keeps_depth():
    lc, _ = make_lightcurve(PLANET, noise_ppm=300.0, trend_amplitude=0.002)
    params = DetrendParams()
    mask = transit_mask(lc.time, PLANET.period, PLANET.t0, PLANET.duration)
    flat = detrend(lc, params, mask=mask)
    in_transit = transit_mask(flat.time, PLANET.period, PLANET.t0, 0.3 * PLANET.duration)
    assert (
        in_transit.sum()
        == transit_mask(lc.time, PLANET.period, PLANET.t0, 0.3 * PLANET.duration).sum()
    )
    depth = 1.0 - np.mean(flat.flux[in_transit])
    assert abs(depth - PLANET.depth) < 1.5e-4


def test_upward_outliers_are_removed():
    lc, _ = make_lightcurve(None, noise_ppm=200.0)
    lc.flux[1000] += 0.05
    flat = detrend(lc, DetrendParams())
    assert len(flat) == len(lc) - 1
