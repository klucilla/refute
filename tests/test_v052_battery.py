"""Battery version 4 (v0.5.2): its plan, sector rule, box odd/even and sinusoid decision. No
network, synthetic data only."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pytest
from pydantic import ValidationError

from refute.core.verdict import TestStatus
from refute.packs.tess import battery_v52 as v52
from refute.packs.tess import synthetic as syn
from refute.packs.tess.params import TessTestPlan
from refute.packs.tess.pipeline import analyze_data
from refute.packs.tess.types import Candidate, LightCurveData

CADENCE = 2.0 / 1440.0


def plan_v4(**v052):
    d = syn.discovery_v052_plan_dict()
    d["v052"] = v052
    return TessTestPlan.model_validate(d)


def candidate(period=3.0, t0=100.5, duration=0.1, depth=2e-3):
    return Candidate(
        period=period, t0=t0, duration=duration, depth=depth, depth_err=1e-4, snr=20.0,
        log_likelihood=0.0, sde=10.0, n_transits=5,
    )  # fmt: skip


@dataclass
class Ev:
    baseline_gap_durations: float = 1.0
    baseline_outer_durations: float = 3.0
    min_coverage: float = 0.5


def sectors_curve(events_by_sector):
    """A time grid of 13 days per sector, the sector number, one per entry."""
    times, sectors = [], []
    for k, _ in enumerate(events_by_sector):
        t = np.arange(100.0 + 20.0 * k, 113.0 + 20.0 * k, CADENCE)
        times.append(t)
        sectors.append(np.full(t.size, k + 1))
    return np.concatenate(times), np.concatenate(sectors)


def test_version_4_needs_its_section_and_only_it():
    assert plan_v4().is_v052
    assert plan_v4().is_v051, "version 4 keeps version 3's section"
    bad = syn.discovery_v052_plan_dict()
    del bad["v052"]
    with pytest.raises(ValidationError):
        TessTestPlan.model_validate(bad)
    bad = syn.discovery_v051_plan_dict()
    bad["v052"] = {}
    with pytest.raises(ValidationError):
        TessTestPlan.model_validate(bad)


def test_an_earlier_plan_dumps_without_the_new_section():
    dumped = TessTestPlan.model_validate(syn.discovery_v051_plan_dict()).model_dump(mode="json")
    assert "v052" not in dumped


def test_the_selection_keeps_the_four_sectors_with_most_events():
    t, s = sectors_curve([0] * 6)
    keep = ~((s == 6) & (t > 200.0 + 3.0)) & ~((s == 5) & (t > 180.0 + 6.0))
    choice = v52.choose_sectors(t[keep], s[keep], candidate(), Ev(), CADENCE, True)
    assert choice.chosen == (1, 2, 3, 4)
    assert choice.refused is None
    assert choice.events[1] >= choice.events[5] >= choice.events[6]


def test_the_ties_go_to_the_lower_sector():
    t, s = sectors_curve([0] * 6)
    choice = v52.choose_sectors(t, s, candidate(period=20.0, t0=105.0), Ev(), CADENCE, True)
    assert list(choice.chosen) == sorted(choice.chosen)
    assert set(choice.chosen) == {1, 2, 3, 4}


def test_five_sectors_are_refused_until_the_selector_is_certified():
    t, s = sectors_curve([0] * 5)
    assert "not certified" in v52.choose_sectors(t, s, candidate(), Ev(), CADENCE, False).refused


def test_more_than_twenty_sectors_are_refused_even_when_certified():
    t, s = sectors_curve([0] * 21)
    assert (
        "above the supported" in v52.choose_sectors(t, s, candidate(), Ev(), CADENCE, True).refused
    )


def test_up_to_four_sectors_are_all_kept():
    t, s = sectors_curve([0] * 3)
    choice = v52.choose_sectors(t, s, candidate(), Ev(), CADENCE, False)
    assert choice.chosen == (1, 2, 3)
    assert choice.refused is None


def test_a_sector_without_an_eligible_event_is_not_chosen():
    t, s = sectors_curve([0] * 2)
    near_end = candidate(period=100.0, t0=105.0)
    choice = v52.choose_sectors(t, s, near_end, Ev(), CADENCE, False)
    assert choice.chosen == (1,)


def box_curve(depth, sigma=1e-5, seed=1):
    rng = np.random.default_rng(seed)
    t = np.arange(100.0, 127.0, CADENCE)
    f = np.ones(t.size) + rng.normal(0.0, sigma, t.size)
    c = candidate(depth=depth)
    dt = np.abs(np.mod(t - c.t0 + 0.5 * c.period, c.period) - 0.5 * c.period)
    f[dt <= c.duration / 2.0] -= depth
    return t, f, np.full(t.size, sigma), c, dt


def test_box_after_model_recovers_a_known_box_and_error():
    t, f, e, c, dt = box_curve(1e-3)
    keep = dt > 0.1
    x_all = np.ones((t.size, 1))
    x_kept = x_all[keep]
    box, sigma = v52.box_after_model(t, f, e, keep, x_all, x_kept, c, 1.0)
    assert box == pytest.approx(1e-3, abs=5e-6)
    n_in = np.count_nonzero(dt <= c.duration / 2.0)
    assert sigma == pytest.approx(1e-5 * np.sqrt(1.0 / n_in), rel=0.1)


def test_box_after_model_scales_with_beta():
    t, f, e, c, dt = box_curve(1e-3)
    keep = dt > 0.1
    x_all = np.ones((t.size, 1))
    _, one = v52.box_after_model(t, f, e, keep, x_all, x_all[keep], c, 1.0)
    _, two = v52.box_after_model(t, f, e, keep, x_all, x_all[keep], c, 2.0)
    assert two == pytest.approx(2.0 * one)


def test_no_in_event_cadence_gives_no_box():
    t, f, e, c, dt = box_curve(1e-3)
    outside = dt > 0.1
    x_all = np.ones((outside.sum(), 1))
    box, sigma = v52.box_after_model(
        t[outside], f[outside], e[outside], np.ones(outside.sum(), dtype=bool), x_all, x_all, c, 1.0
    )
    assert np.isnan(box)
    assert np.isnan(sigma)


def lc_of(t, f, sigma=1e-4):
    return LightCurveData(
        t, f, np.full(t.size, sigma), np.ones(t.size, dtype=int), np.zeros(t.size)
    )


def sinusoid_case(amplitude, transit_depth, sigma=1e-4, seed=2):
    rng = np.random.default_rng(seed)
    t = np.arange(100.0, 127.0, CADENCE)
    c = candidate(depth=2e-3)
    phase = 2.0 * np.pi * (t - c.t0) / (c.period / 2.0)
    f = 1.0 + amplitude * np.cos(phase) + rng.normal(0.0, sigma, t.size)
    dt = np.abs(np.mod(t - c.t0 + 0.5 * c.period, c.period) - 0.5 * c.period)
    f[dt <= c.duration / 2.0] -= transit_depth
    return lc_of(t, f, sigma), c


def run_sinusoid(lc, c, fail_allowed=True):
    plan = plan_v4()
    return v52.check_sinusoid(
        lc, c, plan.stronger, plan.v051, plan.gauntlet.events, CADENCE, fail_allowed, 11
    )


def test_a_quiet_star_with_a_transit_is_not_flagged():
    lc, c = sinusoid_case(0.0, 2e-3)
    result = run_sinusoid(lc, c)
    assert result.status is TestStatus.PASS
    assert result.coverage > 0


def test_variability_that_removes_the_dip_fails():
    lc, c = sinusoid_case(4e-3, 0.0)
    result = run_sinusoid(lc, c)
    assert result.status is TestStatus.FAIL


def test_a_transit_on_a_variable_star_is_ambiguous_never_a_fail():
    lc, c = sinusoid_case(4e-3, 2e-3)
    result = run_sinusoid(lc, c)
    assert result.status is TestStatus.INCONCLUSIVE
    assert result.metrics["inconclusive_detail"] == v52.AMBIGUOUS_SINUSOID
    assert result.metrics["inconclusive_class"] == "insufficient_sensitivity"


def test_withdrawing_the_fail_leaves_every_flag_inconclusive():
    lc, c = sinusoid_case(4e-3, 0.0)
    result = run_sinusoid(lc, c, fail_allowed=False)
    assert result.status is TestStatus.INCONCLUSIVE
    assert result.metrics["inconclusive_detail"] == v52.AMBIGUOUS_SINUSOID


def test_a_period_outside_the_domain_is_inconclusive():
    lc, c = sinusoid_case(0.0, 0.0)
    far = candidate(period=100.0, depth=2e-3)
    result = run_sinusoid(lc, far)
    assert result.status is TestStatus.INCONCLUSIVE
    assert result.metrics["inconclusive_class"] == "outside_domain"
    assert c.period == 3.0


def run(name):
    return analyze_data(syn.scenario_data(name), plan_v4())


def test_a_version_4_analysis_runs_every_test_and_uses_the_box():
    analysis = run("planet")
    by = {t.name: t for t in analysis.tests}
    assert "version 4" in by["odd_even"].metrics["estimator"]
    assert {"single_event", "event_consistency", "sinusoid", "duration_excess"} <= set(by)
    assert analysis.verdict in ("SURVIVED", "WEAKENED", "REFUTED", "INCONCLUSIVE")


def test_every_inconclusive_of_version_4_has_a_known_class():
    from refute.core.inconclusive import CLASSES

    for name in ("planet", "eb_odd_even", "sinusoid"):
        for t in run(name).tests:
            if t.status is TestStatus.INCONCLUSIVE:
                assert t.metrics.get("inconclusive_class") in CLASSES, t.name


def test_no_pass_without_coverage_in_version_4():
    for t in run("planet").tests:
        if t.status is TestStatus.PASS:
            assert t.coverage is not None and t.coverage > 0, t.name
