"""M4 piece 1, A1: correlated noise estimated from the data by the binned rms (revision 3 of the
corrections plan, section 2.1; criteria of its section 10, row A1; the map in
docs/validation/v0.2.1/reopen/m4-implementation-map.md)."""

import numpy as np
import pytest

from refute.packs.tess import rednoise
from refute.packs.tess.synthetic import ar1_series, sector_times

CADENCE = 120.0 / 86400.0
N_T = 75  # a 2.5-hour transit at 2-minute cadence
GAP_SPLIT = 5
B_MIN = 20


def _sector(start, seed, white=600e-6, red=0.0, tau=1.0 / 24.0):
    t = sector_times(start)
    rng = np.random.default_rng(seed)
    flux = rng.normal(0.0, white, t.size)
    if red > 0:
        flux = flux + ar1_series(t, red, tau, np.random.default_rng([seed, 1]))
    return t, flux


def _two_sectors(seed, **noise):
    t1, f1 = _sector(1325.0, seed, **noise)
    t2, f2 = _sector(1353.0, seed + 100, **noise)
    time = np.concatenate([t1, t2])
    resid = np.concatenate([f1, f2])
    sector = np.concatenate([np.full(t1.size, 1), np.full(t2.size, 2)])
    return time, resid, sector


def _analytic_beta(n, white, red, tau):
    phi = np.exp(-CADENCE / tau)
    k = np.arange(1, n)
    cov = red**2 * (n + 2.0 * np.sum((n - k) * phi**k))
    return float(np.sqrt((white**2 * n + cov) / (n * (white**2 + red**2))))


def _estimate(time, resid, sector, keep=None, n=N_T, b_min=B_MIN):
    keep = np.ones(time.size, dtype=bool) if keep is None else keep
    return rednoise.estimate(time, resid, sector, keep, n, GAP_SPLIT, CADENCE, b_min)


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_white_noise_gives_beta_near_one(seed):
    time, resid, sector = _two_sectors(seed)
    result = _estimate(time, resid, sector)
    assert not result.undetermined
    for s in result.sectors.values():
        assert not s.excluded
        assert 0.9 <= s.beta <= 1.1, s
        assert s.sigma_w == pytest.approx(600e-6, rel=0.05)


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_ar1_beta_is_within_15_percent_of_its_analytic_value(seed):
    white, red, tau = 600e-6, 600e-6, 1.0 / 24.0
    time, resid, sector = _two_sectors(seed, white=white, red=red, tau=tau)
    expected = _analytic_beta(N_T, white, red, tau)
    result = _estimate(time, resid, sector)
    for s in result.sectors.values():
        assert s.beta == pytest.approx(expected, rel=0.15), (s.beta, expected)
    assert expected > 2.0  # the case is not trivial


def test_bins_never_cross_a_gap_or_a_mask():
    time, resid, sector = _two_sectors(0)
    keep = np.ones(time.size, dtype=bool)
    keep[500:540] = False  # a mask inside the first orbit
    keep[9000:9001] = False  # one dropped cadence
    for idx in rednoise.bins(time, keep, N_T, GAP_SPLIT, CADENCE):
        assert idx.size == N_T
        assert np.all(keep[idx])
        assert np.all(np.diff(idx) == 1)
        assert np.all(np.diff(time[idx]) <= GAP_SPLIT * CADENCE + 1e-12)
    # the orbit gap (about 1 day) and the masks split the runs
    runs = rednoise.segments(time, keep, GAP_SPLIT, CADENCE)
    assert all(np.all(keep[r]) for r in runs)
    assert len(runs) >= 6


def test_a_sector_with_too_few_bins_is_excluded_and_reported():
    time, resid, sector = _two_sectors(0)
    keep = np.ones(time.size, dtype=bool)
    second = sector == 2
    keep[np.flatnonzero(second)[N_T * 10 :]] = False  # leaves 10 bins in sector 2
    result = _estimate(time, resid, sector, keep=keep)
    assert result.sectors[2].excluded
    assert result.sectors[2].reason == "few_bins"
    assert result.sectors[2].n_bins < B_MIN
    assert not result.sectors[1].excluded
    assert not result.undetermined
    assert result.excluded_sectors == [2]


def test_no_sector_left_is_undetermined():
    time, resid, sector = _two_sectors(0)
    result = _estimate(time, resid, sector, b_min=10_000)
    assert result.undetermined
    assert all(s.excluded for s in result.sectors.values())


def test_the_estimate_ignores_masked_cadences():
    time, resid, sector = _two_sectors(1)
    keep = np.ones(time.size, dtype=bool)
    keep[1000:1500] = False
    spoiled = resid.copy()
    spoiled[1000:1500] += 0.05  # a deep feature inside the mask
    a = _estimate(time, resid, sector, keep=keep)
    b = _estimate(time, spoiled, sector, keep=keep)
    assert a.sectors[1].beta == b.sectors[1].beta
    assert a.sectors[1].sigma_w == b.sectors[1].sigma_w


def test_sigma_r2_is_never_negative_and_beta_follows_its_definition():
    time, resid, sector = _two_sectors(2)
    result = _estimate(time, resid, sector)
    for s in result.sectors.values():
        assert s.sigma_r2 >= 0.0
        assert s.beta == pytest.approx(np.sqrt(1.0 + N_T * s.sigma_r2 / s.sigma_w**2))
