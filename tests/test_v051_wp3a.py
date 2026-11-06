"""v0.5.1 WP3 (a): ``aperture_depth`` and ``systematics`` with the A0 error of the difference,
discovery version 3 (docs/plans/v0.5.1-acceptance.md, WP3 (a)). Mechanism cases on synthetic
data; the rate rows (3a.1 to 3a.6) run in the acceptance scripts on frozen code."""

from __future__ import annotations

import numpy as np

from refute.core.sensitivity import enforce_sensitivity
from refute.core.verdict import TestStatus
from refute.packs.tess import battery_v51_diff as v51d
from refute.packs.tess import power
from refute.packs.tess.params import TessTestPlan
from refute.packs.tess.synthetic import (
    BLEND_NEIGHBOR,
    BLEND_SCENE,
    PLANET,
    SignalSpec,
    discovery_v05_plan_dict,
    make_aux,
    make_blend,
    make_lightcurve,
    make_sector_aux,
    signal_model,
)
from refute.packs.tess.types import Candidate


def _plan():
    d = discovery_v05_plan_dict()
    d["discovery"]["version"] = 3
    d["v051"] = {}
    return TessTestPlan.model_validate(d)


def _candidate(spec: SignalSpec = PLANET) -> Candidate:
    return Candidate(period=spec.period, t0=spec.t0, duration=spec.duration, depth=spec.depth,
                     depth_err=spec.depth / 50, snr=50.0, log_likelihood=1.0, sde=10.0,
                     n_transits=14)  # fmt: skip


# --- aperture_depth ---------------------------------------------------------------------------


def test_aperture_depth_passes_on_the_target_with_a0_errors_and_a_block():
    plan = _plan()
    lc, _ = make_lightcurve(PLANET, seed=1)
    r = v51d.check_aperture_depth(make_aux(lc, seed=1).pixels, _candidate(), plan, seed=5)
    assert r.status is TestStatus.PASS
    m = r.metrics
    assert m["estimator"].startswith("large-minus-core difference series")
    assert m["depth_difference_err_ppm"] > 0 and m["core_difference_correlation"] is not None
    block = r.sensitivity["main"]
    assert block["rule_id"] == "compound-sim-2"
    assert block["alternative"] == plan.gauntlet.aperture_depth.min_depth_ratio + 0.3


def test_aperture_depth_refutes_a_signal_outside_the_core():
    plan = _plan()
    lc, _, aux = make_blend(BLEND_NEIGHBOR, scene=BLEND_SCENE, trend_amplitude=0.002, seed=3)
    r = v51d.check_aperture_depth(aux.pixels, _candidate(BLEND_NEIGHBOR), plan, seed=5)
    assert r.status is TestStatus.FAIL
    assert r.metrics["depth_ratio_large_to_core"] >= plan.gauntlet.aperture_depth.min_depth_ratio


def test_without_pixels_aperture_depth_is_inconclusive():
    r = v51d.check_aperture_depth([], _candidate(), _plan(), seed=5)
    assert r.status is TestStatus.INCONCLUSIVE and r.coverage == 0


# --- systematics ------------------------------------------------------------------------------


def _aux(lc, crowd=0.98, seed=0, **kwargs):
    return make_sector_aux(lc, crowd, np.random.default_rng(seed), **kwargs)


def test_sap_identical_to_pdcsap_makes_the_sap_sub_check_not_applicable():
    # 3a.6, first case: no correction applied (SAP equal to PDCSAP), noise in both
    plan = _plan()
    lc, _ = make_lightcurve(PLANET, seed=6)
    aux = _aux(lc, crowd=1.0)
    for a in aux:
        a.sap_flux = 2.0 * a.pdcsap_flux  # identical up to a constant factor
    r = v51d.check_systematics(aux, _candidate(), plan, seed=7)
    assert r.metrics["sub_checks_not_applicable"]
    assert r.sensitivity["sap"] == {"applicable": False, "reason": r.metrics[
        "sub_checks_not_applicable"]["sap_vs_pdcsap"]}  # fmt: skip
    assert "detectable" not in r.sensitivity["sap"]
    assert r.status is not TestStatus.FAIL


def test_sap_with_independent_noise_is_applicable_with_a_non_zero_error():
    # 3a.6, second case: SAP equal to PDCSAP plus independent noise of the same level
    plan = _plan()
    lc, _ = make_lightcurve(PLANET, seed=6)
    aux = _aux(lc, crowd=1.0)
    rng = np.random.default_rng(3)
    for a in aux:
        a.sap_flux = a.pdcsap_flux + rng.normal(0.0, 3e-4, a.sap_flux.size)
    r = v51d.check_systematics(aux, _candidate(), plan, seed=7)
    assert not r.metrics["sub_checks_not_applicable"]
    assert r.metrics["sap_minus_expected_err_ppm"] > 0
    assert "SAP versus PDCSAP" in r.metrics["sub_checks_run"]
    assert r.status is TestStatus.PASS


def test_a_sap_only_dip_at_the_transits_fails_systematics():
    # 3a.5: a SAP-only systematic dip (relative difference 0.8)
    plan = _plan()
    lc, _ = make_lightcurve(PLANET, seed=6)
    aux = _aux(lc, crowd=1.0)
    rng = np.random.default_rng(4)
    for a in aux:
        dip = 0.8 * (1.0 - signal_model(a.time, PLANET))
        a.sap_flux = a.pdcsap_flux - dip + rng.normal(0.0, 3e-4, a.sap_flux.size)
    r = v51d.check_systematics(aux, _candidate(), plan, seed=7)
    assert r.status is TestStatus.FAIL
    assert r.metrics["sap_relative_difference"] > 0.5


def test_the_registry_makes_sap_conditional_and_background_required():
    plan = _plan()
    reg = power.registry_for(plan)
    assert reg["systematics"] == {"dumps": "fraction", "sap": "rule?", "background": "rule"}
    lc, _ = make_lightcurve(PLANET, seed=6)
    aux = _aux(lc, crowd=1.0)
    for a in aux:
        a.sap_flux = a.pdcsap_flux.copy()
    r = v51d.check_systematics(aux, _candidate(), plan, seed=7)
    (checked,) = enforce_sensitivity([r], reg)
    # a PASS rests on the background and the dumps; the not-applicable SAP never makes it pass
    if checked.status is TestStatus.PASS:
        assert r.sensitivity["background"]["detectable"]


def test_a0_depth_is_none_when_the_error_is_not_measurable():
    plan = _plan()
    lc, _ = make_lightcurve(PLANET, seed=6)
    flat = np.ones(lc.time.size)
    assert v51d.a0_depth(lc.time, flat, lc.sector, _candidate(), plan, seed=1) is None


def test_the_expected_sap_depth_uses_each_sector_crowdsap():
    # Codex (WP3 (a) review): sectors with different CROWDSAP, SAP consistent in each
    plan = _plan()
    lc, _ = make_lightcurve(PLANET, seed=6)
    aux = _aux(lc, crowd=1.0)
    rng = np.random.default_rng(5)
    for a, crowd in zip(aux, (0.7, 1.0), strict=False):
        a.crowdsap = crowd
        a.sap_flux = 1.0 + crowd * (a.pdcsap_flux - 1.0) + rng.normal(0.0, 3e-4, a.time.size)
    r = v51d.check_systematics(aux, _candidate(), plan, seed=7)
    assert 0.7 < r.metrics["effective_crowdsap"] < 1.0
    assert r.metrics["sap_relative_difference"] < 0.1
    assert r.status is not TestStatus.FAIL
