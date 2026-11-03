"""v0.5 WP4: the centroid test per sector (docs/plans/v0.5-acceptance.md, cases 4.1 to 4.9 and
the sabotage checks). Mechanism cases on synthetic pixel data; the rate cases run in the
acceptance scripts."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from refute.core.sensitivity import enforce_sensitivity
from refute.core.verdict import TestStatus
from refute.packs.tess.centroid_v5 import check_centroid_v5, control_phases
from refute.packs.tess.params import TessTestPlan
from refute.packs.tess.pipeline import attack_candidate, detrend
from refute.packs.tess.power import TESS_REGISTRY
from refute.packs.tess.search import search_period
from refute.packs.tess.synthetic import (
    SignalSpec,
    discovery_v05_plan_dict,
    make_blend_sky,
    make_data,
    make_star,
    scenario_data,
    sector_jacobian,
    with_sky_jacobians,
)
from refute.packs.tess.types import Candidate

PLAN = TessTestPlan.model_validate(discovery_v05_plan_dict())
NEIGHBOR = SignalSpec(period=5.1, t0=1326.2, depth=0.08, duration=2.4 / 24)


def _final(data):
    cand = search_period(detrend(data.lc, PLAN.detrend), PLAN.search).candidate
    return attack_candidate(data, cand, PLAN).candidate


@pytest.fixture(scope="module")
def blend():
    lc, sectors, aux = make_blend_sky(NEIGHBOR, (42.0, 0.0), seed=1)
    data = make_data(lc, sectors, make_star(), aux=aux)
    return data, _final(data)


@pytest.fixture(scope="module")
def planet():
    data = with_sky_jacobians(scenario_data("planet_three_years"))
    return data, _final(data)


def test_a_plain_pixel_file_has_no_sky_frame():
    # the earlier generators keep producing PixelData (their anchored digests do not change)
    data = scenario_data("planet")
    assert all(type(px).__name__ == "PixelData" for px in data.aux.pixels)
    final = _final(data)
    result = _check(data, final)
    assert result.status is TestStatus.INCONCLUSIVE
    assert set(result.metrics["not_qualified"].values()) == {"no pixel-to-sky transform (WCS)"}


def _check(data, final, pixels=None, sectors=None, plan=PLAN):
    aux = data.aux
    return check_centroid_v5(
        aux.pixels if pixels is None else pixels,
        aux.sectors if sectors is None else sectors,
        final,
        plan,
        11,
    )


def test_4_1_an_off_target_source_in_three_sectors_fails(blend):
    data, final = blend
    result = _check(data, final)
    assert result.status is TestStatus.FAIL
    assert len(result.metrics["qualified_sectors"]) == 3
    assert result.metrics["heterogeneity_p"] >= PLAN.stronger.chi2_alpha


def test_4_2_one_sector_is_inconclusive_even_with_an_offset(blend):
    data, final = blend
    result = _check(data, final, pixels=data.aux.pixels[:1])
    assert result.status is TestStatus.INCONCLUSIVE
    assert result.message == "single sector"


def test_4_4_when_no_sector_qualifies_it_is_never_a_pass(blend):
    data, final = blend
    wrong_depth = replace(final, depth=final.depth * 3.0)  # aperture depth cannot agree
    result = _check(data, wrong_depth)
    assert result.status is TestStatus.INCONCLUSIVE
    assert result.message.startswith("qualification failed")


def test_4_5_an_on_target_planet_passes_with_sensitivity(planet):
    data, final = planet
    result = _check(data, final)
    assert result.status is TestStatus.PASS
    assert result.sensitivity["main"]["detectable"] is True
    (kept,) = enforce_sensitivity([result], TESS_REGISTRY)
    assert kept.status is TestStatus.PASS
    assert "does not exclude unresolved blends" in result.message


def test_4_6_sectors_with_opposite_sky_offsets_disagree(blend):
    data, final = blend
    # one sector's cube read twice, the second time with the opposite Jacobian (as sector 2,
    # whose CROWDSAP exists): the same pixel offset becomes opposite sky offsets
    first, second = data.aux.pixels[0], data.aux.pixels[1]
    jac = -np.asarray(first.sky_jacobian, dtype=float)
    mirrored = replace(first, sector=second.sector, sky_jacobian=tuple(map(tuple, jac)))
    result = _check(data, final, pixels=[first, mirrored])
    assert result.status is TestStatus.INCONCLUSIVE
    assert result.message.startswith("sectors disagree")


def test_4_7_no_wcs_or_no_crowdsap_does_not_qualify(blend):
    data, final = blend
    no_wcs = [replace(px, sky_jacobian=None) for px in data.aux.pixels]
    result = _check(data, final, pixels=no_wcs)
    assert result.status is TestStatus.INCONCLUSIVE
    assert set(result.metrics["not_qualified"].values()) == {"no pixel-to-sky transform (WCS)"}
    no_crowd = [replace(a, crowdsap=None) for a in data.aux.sectors]
    result = _check(data, final, sectors=no_crowd)
    assert set(result.metrics["not_qualified"].values()) == {"no CROWDSAP (dilution unknown)"}


@pytest.mark.parametrize("period, duration", [(5.1, 0.1), (2.3, 0.07), (12.0, 0.2)])
def test_4_8_control_epochs_avoid_the_events_and_each_other(period, duration):
    cand = Candidate(period, 1000.0, duration, 1e-3, 1e-4, 10.0, 0.0, 10.0, 5)
    phases = control_phases(cand, 20, seed=3)
    assert phases == control_phases(cand, 20, seed=3)
    for u in phases:
        assert 0.15 <= u <= 0.35 or 0.65 <= u <= 0.85
        assert min(u, 1 - u) * period >= 2 * duration
        assert abs(u - 0.5) * period >= 2 * duration
    for i, u in enumerate(phases):
        for q in phases[i + 1 :]:
            assert abs(u - q) * period >= duration


def test_4_9_the_fail_message_states_a_measurement_not_a_cause(blend):
    data, final = blend
    message = _check(data, final).message
    assert "arcsec" in message and "sigma" in message
    assert "comes from" not in message and "another star" not in message


# --- sabotage checks ----------------------------------------------------------------------


def test_sabotage_one_sector_allowed_makes_4_2_fail(blend):
    data, final = blend
    sabotaged = PLAN.model_copy(
        update={"stronger": PLAN.stronger.model_copy(update={"centroid_min_sectors": 1})}
    )
    result = _check(data, final, pixels=data.aux.pixels[:1], plan=sabotaged)
    assert result.status is TestStatus.FAIL


def test_sabotage_pixel_frame_makes_4_1_disagree(blend):
    data, final = blend
    # every sector read with sector 0's orientation: the pixel offsets are compared as if
    # they were in one frame, and the rotated sectors no longer agree
    same = tuple(map(tuple, np.asarray(sector_jacobian(0), dtype=float)))
    pixels = [replace(px, sky_jacobian=same) for px in data.aux.pixels]
    result = _check(data, final, pixels=pixels)
    assert result.status is TestStatus.INCONCLUSIVE
    assert result.message.startswith("sectors disagree")
