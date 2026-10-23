"""The domain function of the profile ``three-observing-years/1`` (Amendment B of
docs/validation/v0.2.1/population-study.md; the definitions of
docs/validation/v0.2.1/population/population-v4-acceptance.md, section 2.1): D1 to D5 on per-sector
kept time stamps. Synthetic time stamps only; no network."""

from __future__ import annotations

import json

import numpy as np
import pytest

from refute.packs.tess import domain
from refute.packs.tess.synthetic import sector_times

DT = 120.0 / 86400.0  # one cadence, in days
SEC = 1.0 / 86400.0
X2F_STARTS = (1325.0, 1700.0, 2061.0)


def orbits(start: float, l1: float = 13.0, gap: float = 1.0, l2: float = 13.0) -> np.ndarray:
    """Two orbits of round(l / DT) cadences; the second starts ``gap`` days after the first
    orbit's last cadence."""
    n1, n2 = round(l1 / DT), round(l2 / DT)
    first = start + DT * np.arange(n1)
    second = first[-1] + gap + DT * np.arange(n2)
    return np.concatenate([first, second])


def three(starts=(1325.0, 1700.0, 2075.0), **kw) -> list[np.ndarray]:
    return [orbits(s, **kw) for s in starts]


def drop(t: np.ndarray, index: int, count: int = 1) -> np.ndarray:
    return np.delete(t, np.arange(index, index + count))


def shifted(t: np.ndarray, index: int, seconds: float) -> np.ndarray:
    """Every time stamp from ``index`` on moved by ``seconds``."""
    t = t.copy()
    t[index:] += seconds * SEC
    return t


# --- inside --------------------------------------------------------------------------------------


def test_profile_name():
    assert domain.PROFILE == "three-observing-years/1"


def test_the_x2f_layout_is_inside_with_its_measured_quantities():
    sectors = [sector_times(s) for s in X2F_STARTS]
    result = domain.check_domain(sectors)
    assert result.inside and result.failed is None and result.reason is None
    assert result.conditions == {c: True for c in ("D1", "D2", "D3", "D4", "D5")}
    assert [s.label for s in result.sectors] == [2018, 2019, 2020]
    assert result.separations_days == pytest.approx((375.0, 361.0), abs=1e-9)
    for t, s in zip(sectors, result.sectors, strict=True):
        n1 = int(np.count_nonzero(t < t[0] + 13.5))
        assert s.n_kept == t.size
        assert s.orbit_days == pytest.approx((n1 * DT, (t.size - n1) * DT), abs=1e-9)
        assert s.orbit_gap_days == pytest.approx(t[n1] - t[n1 - 1], abs=1e-12)
        assert s.other_gaps_seconds == ()
        assert s.span_days == pytest.approx(t[-1] - t[0] + DT, abs=1e-12)
        assert s.coverage == pytest.approx(t.size * DT / (t[-1] - t[0] + DT), rel=1e-12)
        assert s.coverage == pytest.approx(0.963, abs=0.001)
        assert s.k_counts == {1: t.size - 2, 2: 0, 3: 0, 4: 0}


def test_near_the_bounds_inside():
    a = orbits(1325.0, gap=0.5 + 1e-6)
    b = shifted(orbits(1325.0 + 345.001), 3001, 21599.0 - 120.0)  # another gap of 21 599 s
    c = shifted(drop(orbits(1325.0 + 345.001 + 749.999), 5000, 3), 5000, 0.49)  # 480.49 s
    result = domain.check_domain([a, b, c])
    assert result.inside, result.reason
    assert result.sectors[1].other_gaps_seconds == pytest.approx((21599.0,), abs=1e-3)
    assert result.sectors[2].k_counts[4] == 1
    assert result.sectors[2].residual_max_s == pytest.approx(0.49, abs=1e-3)


def test_missing_cadences_and_jitter_inside_tolerance():
    rng = np.random.default_rng(1)
    sectors = []
    for s in (1325.0, 1700.0, 2075.0):
        t = drop(drop(drop(orbits(s), 100), 200, 2), 300, 3)  # k = 2, 3 and 4 once each
        sectors.append(t + rng.uniform(-0.25, 0.25, t.size) * SEC)
    result = domain.check_domain(sectors)
    assert result.inside, result.reason
    s = result.sectors[0]
    assert (s.k_counts[2], s.k_counts[3], s.k_counts[4]) == (1, 1, 1)
    assert -0.5 < s.residual_min_s <= s.residual_max_s < 0.5


def test_a_sector_across_a_year_boundary_is_labelled_by_its_first_cadence():
    # BTJD 1472.5 is 2018-12-20; that sector ends in January 2019
    result = domain.check_domain(three((1472.5, 1472.5 + 370.0, 1472.5 + 740.0)))
    assert result.inside, result.reason
    assert [s.label for s in result.sectors] == [2018, 2019, 2020]


def test_an_empty_sector_is_left_out():
    result = domain.check_domain([*three(), np.array([])])
    assert result.inside and len(result.sectors) == 3


def test_summary_is_plain_json():
    summary = domain.check_domain(three()).summary()
    assert json.loads(json.dumps(summary)) == summary
    assert summary["profile"] == "three-observing-years/1"
    assert summary["inside"] is True and summary["failed"] is None


# --- D1 and D2 -----------------------------------------------------------------------------------


def test_d1_two_sectors_with_one_label():
    # BTJD 1486.5 is 2019-01-03; 345 d later is still 2019
    result = domain.check_domain(three((1486.5, 1486.5 + 345.0, 1486.5 + 710.0)))
    assert not result.inside and result.failed == "D1"
    assert result.reason.startswith("D1")


def test_d1_two_years_only():
    assert domain.check_domain([orbits(1325.0), orbits(2061.0)]).failed == "D1"


def test_d1_four_years():
    assert domain.check_domain([*three(), orbits(2450.0)]).failed == "D1"


def test_d2_two_sectors_in_one_year():
    result = domain.check_domain([*three(), orbits(1360.0)])
    assert result.conditions["D1"] and result.failed == "D2"


# --- D3 ------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("missing", "seconds"),
    [(0, 0.6), (0, -0.6), (3, 0.6), (3, -0.6)],
)
def test_d3_timing_outside_tolerance(missing, seconds):
    sectors = three()
    sectors[1] = shifted(drop(sectors[1], 4000, missing), 4000, seconds)
    result = domain.check_domain(sectors)
    assert result.failed == "D3", result.reason


def test_d3_five_cadences_is_neither_a_gap_nor_a_step():
    sectors = three()
    sectors[0] = shifted(drop(sectors[0], 4000, 4), 4000, -0.1)  # an interval of 599.9 s
    assert domain.check_domain(sectors).failed == "D3"


@pytest.mark.parametrize("bad", ["swap", "duplicate", "nan", "inf"])
def test_d3_unsorted_duplicate_or_not_finite(bad):
    sectors = three()
    t = sectors[2].copy()
    if bad == "swap":
        t[10], t[11] = t[11], t[10]
    elif bad == "duplicate":
        t[11] = t[10]
    else:
        t[50] = np.nan if bad == "nan" else np.inf
    sectors[2] = t
    assert domain.check_domain(sectors).failed == "D3"


def test_full_frame_cadences_are_outside():
    ffi = [s + (200.0 * SEC) * np.arange(round(27.0 / (200.0 * SEC))) for s in (1325.0, 1700.0)]
    result = domain.check_domain([*ffi, orbits(2075.0)])
    assert result.failed == "D3"
    ten = three()
    ten[0] = ten[0][::5]  # ten-minute sampling
    assert not domain.check_domain(ten).inside


# --- D4 ------------------------------------------------------------------------------------------


@pytest.mark.parametrize("kw", [{"l1": 12.4}, {"l2": 14.1}, {"gap": 0.4}, {"gap": 2.1}])
def test_d4_orbits_and_orbit_gap(kw):
    sectors = three()
    sectors[1] = orbits(1700.0, **kw)
    result = domain.check_domain(sectors)
    assert result.conditions["D3"] and result.failed == "D4", result.reason


def test_d4_no_orbit_gap():
    sectors = three()
    sectors[0] = 1325.0 + DT * np.arange(round(27.0 / DT))
    assert domain.check_domain(sectors).failed == "D4"


def test_d4_at_most_four_other_gaps():
    sectors = three()
    t = sectors[2]
    for place in (1000, 2000, 3000, 4000):
        t = shifted(t, place, 3600.0 - 120.0)
    sectors[2] = t
    assert domain.check_domain(sectors).inside
    sectors[2] = shifted(t, 5000, 3600.0 - 120.0)
    result = domain.check_domain(sectors)
    assert result.failed == "D4" and len(result.sectors[2].other_gaps_seconds) == 5


def test_d4_another_gap_longer_than_six_hours():
    sectors = three()
    sectors[2] = shifted(sectors[2], 1000, 21601.0 - 120.0)
    assert domain.check_domain(sectors).failed == "D4"


def test_d4_coverage_below_the_floor():
    sectors = three()
    keep = np.ones(sectors[0].size, bool)
    keep[1:-1:3] = False  # a third lost, never two in a row
    sectors[0] = sectors[0][keep]
    result = domain.check_domain(sectors)
    assert result.conditions["D3"] and result.failed == "D4"
    assert result.sectors[0].coverage < 0.84


def test_d4_the_orbit_gap_is_the_longest_gap():
    t = shifted(orbits(1325.0, gap=0.6), 2000, 5.0 * 3600.0 - 120.0)  # a 5-hour gap in orbit 1
    result = domain.check_domain([t, orbits(1700.0), orbits(2075.0)])
    s = result.sectors[0]
    assert result.inside, result.reason
    assert s.orbit_gap_days == pytest.approx(0.6, abs=1e-6)
    assert s.other_gaps_seconds == pytest.approx((18000.0,), abs=1e-3)


# --- D5 ------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "starts",
    [
        (1325.0, 1325.0 + 344.9, 1325.0 + 344.9 + 365.0),
        (1325.0, 1325.0 + 385.1, 1325.0 + 385.1 + 365.0),
        (1325.0, 1325.0 + 500.0, 1325.0 + 865.0),
        (1325.0, 1325.0 + 709.9, 1325.0 + 709.9 + 365.0),
        (1325.0, 1325.0 + 365.0, 1325.0 + 365.0 + 750.1),
        (1325.0, 1325.0 + 730.0, 1325.0 + 1460.0),  # two separations of about two years
    ],
)
def test_d5_separations(starts):
    result = domain.check_domain(three(starts))
    assert result.conditions["D1"] and result.failed == "D5", result.reason


def test_d5_one_long_separation_in_either_order():
    for starts in ((1325.0, 1690.0, 2420.0), (1325.0, 2055.0, 2420.0)):
        assert domain.check_domain(three(starts)).inside


def test_d5_reads_the_sectors_in_time_order():
    assert domain.check_domain(three()[::-1]).inside


# --- unavailable quantities ----------------------------------------------------------------------


def test_a_non_finite_first_time_stamp_gives_no_label():
    sectors = three()
    sectors[1] = sectors[1].copy()
    sectors[1][0] = np.nan
    result = domain.check_domain(sectors)
    assert result.sectors[1].label is None
    assert result.failed == "D1"
    assert not result.conditions["D3"] and not result.conditions["D5"]
    assert result.sectors[1].span_days is None and result.sectors[1].coverage is None


def test_a_sector_of_one_cadence():
    sectors = three()
    sectors[2] = np.array([2075.0])
    result = domain.check_domain(sectors)
    s = result.sectors[2]
    assert result.conditions["D3"] and result.failed == "D4"
    assert s.orbit_gap_days is None and s.orbit_days is None
    assert s.coverage == pytest.approx(1.0)
    assert result.summary()["sectors"][2]["orbit_gap_days"] is None


# --- reporting -----------------------------------------------------------------------------------


def test_every_condition_is_computed_and_the_first_failure_is_named():
    sectors = three((1486.5, 1486.5 + 345.0, 1486.5 + 900.0))  # D1 and D5 fail
    sectors[0] = orbits(1486.5, gap=3.0)  # and D4
    result = domain.check_domain(sectors)
    assert result.failed == "D1"
    assert result.conditions == {"D1": False, "D2": True, "D3": True, "D4": False, "D5": False}
    assert result.sectors[0].orbit_gap_days == pytest.approx(3.0, abs=1e-6)
