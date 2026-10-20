"""M4 piece 6: ``period_alias`` by revision 3, section 5, and revision 4, section 3
(docs/validation/v0.2.1/reopen/m4-implementation-map.md, Amendment 21, which declares the
computation and these cases before the tests and the code).

The candidate is given (the injected ephemeris); synthetic light curves only, the two-year layout
of ``synthetic``, white 600 ppm or white 600 ppm plus AR(1) 400 ppm with ``tau`` = 1 h; the seeds
6000 to 6099 are new, one per case and noise model, in the order of the amendment's list. Each case
states its preconditions; a failed precondition makes the case incompatible with its construction,
never a reason to try another seed.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from refute.core.verdict import Severity, TestStatus
from refute.packs.tess.battery import check_period_alias
from refute.packs.tess.params import CorrectionsParams, TessTestPlan
from refute.packs.tess.synthetic import SignalSpec, make_lightcurve
from refute.packs.tess.types import Candidate, LightCurveData

P, T0, T14 = 3.7, 1326.3, 2.5 / 24.0
A_VAR = 2000e-6  # the variability's semi-amplitude
S_WEAK = 2.5  # the declared significance of a weak box
S_STRONG = 20.0  # and of a strong one
NOISE = {"white": 0.0, "correlated": 400.0}
# One seed per case and noise model, in the order of the amendment's list (R1, R2, R3, R4a, R4b).
SEEDS = {
    ("R1", "white"): 6000,
    ("R1", "correlated"): 6001,
    ("R2", "white"): 6002,
    ("R2", "correlated"): 6003,
    ("R3", "white"): 6004,
    ("R3", "correlated"): 6005,
    ("R4a", "white"): 6006,
    ("R4a", "correlated"): 6007,
    ("R4b", "white"): 6008,
    ("R4b", "correlated"): 6009,
}
Z_STAR, F_STAR, G_STAR = 18.47, 0.5, 10.0


def _plan(**corrections) -> TessTestPlan:
    block = {"version": 2, "enabled": True, **corrections}
    return TessTestPlan.model_validate({"gauntlet": {"corrections": block}})


def _candidate(period=P, t0=T0, duration=T14, depth=1e-3) -> Candidate:
    return Candidate(
        period=period,
        t0=t0,
        duration=duration,
        depth=depth,
        depth_err=depth / 50,
        snr=50.0,
        log_likelihood=1.0,
        sde=10.0,
        n_transits=14,
    )


def _curve(depth, seed, noise, variability_phase=None, period=P):
    """The two-year layout with a box of ``depth`` (none if 0) and, if ``variability_phase`` is
    given, the variability ``-A cos(2 pi (phi - phase))`` whose minimum is at that phase."""
    spec = None
    if depth:
        spec = SignalSpec(period=period, t0=T0, depth=depth, duration=T14)
    lc, _ = make_lightcurve(spec, seed=seed, red_noise_ppm=NOISE[noise])
    if variability_phase is not None:
        phi = (lc.time - T0) / period
        lc = LightCurveData(
            lc.time,
            lc.flux * (1.0 - A_VAR * np.cos(2.0 * np.pi * (phi - variability_phase))),
            lc.flux_err,
            lc.sector,
            lc.year,
        )
    return lc


def _box(seed, noise, variability_phase, s, period=P):
    """A box built by the declared rule: its depth is ``s`` times the error of d_box that the
    test itself reports on the same noise realization without the box (Amendment 21)."""
    bare = check_period_alias(
        _curve(0.0, seed, noise, variability_phase, period), _candidate(period=period), _plan()
    )
    err = bare.metrics.get("d_box_err", float("nan"))
    assert math.isfinite(err) and err > 0, bare.message  # precondition of the construction
    return _curve(s * err, seed, noise, variability_phase, period)


def _weak(seed, noise, variability_phase):
    return _box(seed, noise, variability_phase, S_WEAK)


def _run(lc, **corrections):
    return check_period_alias(lc, _candidate(), _plan(**corrections))


# --- the four regimes of revision 3, section 5 (row 5 of section 10) ---------------------------


@pytest.mark.parametrize("noise", ["white", "correlated"])
def test_r1_a_dip_made_by_variability_with_little_box_gain_fails(noise):
    r = _run(_weak(SEEDS[("R1", noise)], noise, 0.0))
    m = r.metrics
    assert m["d_box"] > 0, (r.message, m)  # preconditions
    assert m["z_f"] >= Z_STAR and m["f"] >= F_STAR and m["g"] < G_STAR, (r.message, m)
    assert r.status is TestStatus.FAIL and r.severity is Severity.FATAL


@pytest.mark.parametrize("noise", ["white", "correlated"])
def test_r2_significant_variability_that_does_not_explain_the_dip_is_inconclusive(noise):
    r = _run(_weak(SEEDS[("R2", noise)], noise, 0.25))
    m = r.metrics
    assert m["d_box"] > 0, (r.message, m)  # preconditions
    assert m["z_f"] >= Z_STAR and m["f"] < F_STAR and m["g"] < G_STAR, (r.message, m)
    assert r.status is TestStatus.INCONCLUSIVE


@pytest.mark.parametrize("noise", ["white", "correlated"])
def test_r3_a_weak_dip_without_variability_is_inconclusive(noise):
    r = _run(_weak(SEEDS[("R3", noise)], noise, None))
    m = r.metrics
    assert m["d_box"] > 0 and m["z_f"] < Z_STAR and m["g"] < G_STAR, (r.message, m)  # precond.
    assert r.status is TestStatus.INCONCLUSIVE


@pytest.mark.parametrize("noise", ["white", "correlated"])
@pytest.mark.parametrize(("case", "phase"), [("R4a", None), ("R4b", 0.0)])
def test_r4_a_strong_box_passes_with_or_without_variability(noise, case, phase):
    r = _run(_box(SEEDS[(case, noise)], noise, phase, S_STRONG))
    assert r.metrics["g"] >= G_STAR, (r.message, r.metrics)  # precondition
    assert r.status is TestStatus.PASS and r.severity is Severity.FATAL


# --- the undefined statistics of revision 4, section 3 -----------------------------------------


def test_u1_a_box_depth_that_is_not_positive_is_inconclusive():
    r = _run(_box(6010, "white", None, -S_STRONG))  # a bump
    assert r.status is TestStatus.INCONCLUSIVE
    assert r.metrics["reason"] == "box_depth_not_positive"


def test_u2_a_singular_design_is_inconclusive():
    # a period of two cadences: every phase is 0 or 0.5, so cos(4 pi phi) equals the constant
    two = 2 * 120.0 / 86400.0
    lc = _curve(0.0, 6011, "white")
    r = check_period_alias(
        lc, _candidate(period=two, t0=float(lc.time[0]), duration=two / 4), _plan()
    )
    assert r.status is TestStatus.INCONCLUSIVE
    assert r.metrics["reason"] == "singular_design"


@pytest.mark.parametrize("which", ["z_f", "f", "g", "d_box_err"])
def test_u3_a_non_finite_statistic_is_inconclusive(which):
    from refute.packs.tess.battery import alias_m4_decision

    stats = {"z_f": 100.0, "f": 2.0, "g": 0.0, "d_box": 1e-4, "d_box_err": 4e-5}  # a FAIL
    assert alias_m4_decision(**stats, z_star=Z_STAR, f_star=F_STAR, g_star=G_STAR) == (
        TestStatus.FAIL,
        None,
    )
    stats[which] = float("nan")
    status, reason = alias_m4_decision(**stats, z_star=Z_STAR, f_star=F_STAR, g_star=G_STAR)
    assert (status, reason) == (TestStatus.INCONCLUSIVE, "non_finite_statistic")


def test_u4_an_undetermined_noise_is_inconclusive():
    r = _run(_curve(1000e-6, 6013, "white"), b_min=1_000_000)
    assert r.status is TestStatus.INCONCLUSIVE
    assert r.metrics["reason"] == "noise_undetermined"


# --- the warning, the settings, the switch and the input ---------------------------------------


def test_w_the_systematic_period_warning_is_kept():
    period = 13.7 / 4
    lc = _box(6014, "white", None, S_STRONG, period=period)
    r = check_period_alias(lc, _candidate(period=period), _plan())
    assert r.metrics["g"] >= G_STAR, (r.message, r.metrics)  # precondition
    assert r.status is TestStatus.FAIL and r.severity is Severity.WARNING
    assert r.metrics["near_systematic_periods_days"]


def test_the_thresholds_are_one_of_the_six_declared_pairs():
    assert (CorrectionsParams().alias_z_f, CorrectionsParams().alias_f) == (18.47, 0.5)
    for z in (18.47, 30.0, 50.0):
        for f in (0.5, 0.7):
            CorrectionsParams(alias_z_f=z, alias_f=f)
    for z, f in ((18.47, 0.6), (20.0, 0.5), (50.0, 0.9)):
        with pytest.raises(ValueError):
            CorrectionsParams(alias_z_f=z, alias_f=f)


def test_the_thresholds_reach_the_decision(monkeypatch):
    import refute.packs.tess.battery as battery

    lc = _weak(SEEDS[("R1", "white")], "white", 0.0)
    m = _run(lc).metrics
    assert m["thresholds_m4"] == {"z_f": Z_STAR, "f": F_STAR, "g": G_STAR}
    # the configured pair is the one the decision receives (added before the sabotages: with
    # these curves every declared pair gives the same outcome, so only a spy shows the wiring)
    seen = []
    real = battery.alias_m4_decision

    def spy(*args, **kwargs):
        seen.append(kwargs)
        return real(*args, **kwargs)

    monkeypatch.setattr(battery, "alias_m4_decision", spy)
    strict = _run(lc, alias_z_f=50.0, alias_f=0.7).metrics["thresholds_m4"]
    assert strict == {"z_f": 50.0, "f": 0.7, "g": G_STAR}
    assert seen == [{"z_star": 50.0, "f_star": 0.7, "g_star": G_STAR}]


@pytest.mark.parametrize(
    ("z_star", "f_star", "status"),
    [
        (18.47, 0.5, TestStatus.FAIL),
        (30.0, 0.5, TestStatus.INCONCLUSIVE),  # Z_F = 25 below z_F*
        (18.47, 0.7, TestStatus.INCONCLUSIVE),  # f = 0.6 below f*
    ],
)
def test_the_two_thresholds_each_decide(z_star, f_star, status):
    # added after the Codex stage review: a direct case in which the pairs differ
    from refute.packs.tess.battery import alias_m4_decision

    got = alias_m4_decision(25.0, 0.6, 0.0, 1e-4, 4e-5, z_star=z_star, f_star=f_star, g_star=G_STAR)
    assert got[0] is status


def test_a_sector_excluded_by_a1_leaves_the_fits_and_the_coverage():
    # added after the Codex stage review: one sector valid and one excluded side by side
    lc = _curve(1000e-6, 6016, "white")
    second = lc.sector == lc.sector.max()
    short = second & (lc.time < lc.time[second].min() + 1.0)  # one day: too few bins at n_T
    lc = lc.select(~second | short)
    r = _run(lc)
    m = r.metrics
    assert m["sectors_excluded"] == [int(lc.sector.max())]
    assert m["sectors_used"] == [int(lc.sector.min())]
    assert m["n_cadences"] == int(np.sum(lc.sector == lc.sector.min()))
    used = lc.sector == lc.sector.min()
    box = np.abs(((lc.time[used] - T0 + 0.5 * P) % P) - 0.5 * P) <= T14 / 2
    assert r.coverage == int(box.sum())


@pytest.mark.parametrize(
    "block", [{"version": 1, "enabled": True}, {"version": 2, "enabled": False}]
)
def test_off_an_inactive_block_runs_the_bic_test_byte_for_byte(block):
    lc = _curve(1000e-6, 6015, "white")
    legacy = check_period_alias(lc, _candidate(), TessTestPlan())
    off = TessTestPlan.model_validate({"gauntlet": {"corrections": block}})
    assert check_period_alias(lc, _candidate(), off).to_dict() == legacy.to_dict()
    assert "box_delta_bic" in legacy.metrics and "z_f" not in legacy.metrics


def test_in_the_pipeline_passes_the_raw_curve_and_marks_the_m4_test(monkeypatch):
    import refute.packs.tess.pipeline as pipeline
    from refute.packs.tess import synthetic

    seen = []
    real = pipeline.check_period_alias

    def spy(lc, candidate, plan):
        seen.append(lc)
        return real(lc, candidate, plan)

    monkeypatch.setattr(pipeline, "check_period_alias", spy)
    data = synthetic.scenario_data("planet", 0)
    plan = synthetic.fast_plan_dict()
    plan["gauntlet"] = {"corrections": {"version": 2, "enabled": True}}
    plan = TessTestPlan.model_validate(plan)
    analysis = pipeline.analyze_data(data, plan)
    assert seen and all(lc is data.lc for lc in seen)
    target = {"key": "synthetic", "tic_id": 1, "kind": "planet", "name": "planet-0"}
    record = pipeline.build_result(target, data, plan, analysis, {"pass_criteria": {}})
    assert "period_alias_m4" in record["corrections"]["executed"]
    alias = next(t for t in analysis.tests if t.name == "period_alias")
    assert "z_f" in alias.metrics
