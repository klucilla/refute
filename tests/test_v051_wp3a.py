"""v0.5.1 WP3 (a): ``aperture_depth`` and ``systematics`` with the A0 error of the difference,
discovery version 3 (docs/plans/v0.5.1-acceptance.md, WP3 (a)). Mechanism cases on synthetic
data; the rate rows (3a.1 to 3a.6) run in the acceptance scripts on frozen code."""

from __future__ import annotations

from dataclasses import replace

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


def _affine_case(seed=6):
    """3a.7's mechanism: two affine sectors (CROWDSAP 0.98 and 0.7), one short sector (fewer than
    N_min finite cadences) and one flat sector (PDCSAP standard deviation below s_min)."""
    lc, _ = make_lightcurve(PLANET, seed=seed)
    aux = _aux(lc, crowd=1.0)
    for a, crowd in zip(aux, (0.98, 0.7), strict=True):
        a.crowdsap = crowd
        a.sap_flux = 1.0 + crowd * (a.pdcsap_flux - 1.0)
    first = aux[0]
    short = replace(first, sector=901, time=first.time[:60].copy(),
                    pdcsap_flux=first.pdcsap_flux[:60].copy(), sap_flux=first.sap_flux[:60].copy(),
                    sap_bkg=first.sap_bkg[:60].copy(), dump_times=np.array([]))  # fmt: skip
    rng = np.random.default_rng(11)
    flat_pdc = 1.0 + rng.normal(0.0, 1e-6, first.time.size)
    flat = replace(first, sector=902, time=first.time + 1000.0, pdcsap_flux=flat_pdc,
                   sap_flux=flat_pdc + rng.normal(0.0, 3e-4, flat_pdc.size),
                   dump_times=np.array([]))  # fmt: skip
    return aux + [short, flat]


def test_the_affine_case_makes_the_sap_sub_check_not_applicable_in_every_sector():
    # 3a.7 (amendment 6): affine sectors "no correction"; short and flat sectors not_enough_data
    plan = _plan()
    aux = _affine_case()
    r = v51d.check_systematics(aux, _candidate(), plan, seed=7)
    classes = {e["sector"]: e["class"] for e in r.metrics["sap_not_applicable_sectors"]}
    assert classes == {aux[0].sector: "no_correction", aux[1].sector: "no_correction",
                       901: "not_enough_data", 902: "not_enough_data"}  # fmt: skip
    why = r.metrics["sub_checks_not_applicable"]["sap_vs_pdcsap"]
    assert r.sensitivity["sap"] == {"applicable": False, "reason": why}
    for e in r.metrics["sap_not_applicable_sectors"]:
        assert e["reason"] and e["reason"] in why
    assert "SAP versus PDCSAP" not in r.metrics["sub_checks_run"]


def test_the_affine_sectors_meet_the_cutoffs_and_the_others_do_not():
    aux = _affine_case()
    for a in aux[:2]:
        applies, why, kind = v51d.sap_applicability(a)
        assert (applies, kind) == (False, "no_correction") and "affine" in why
        assert a.time.size >= v51d.SAP_MIN_CADENCES
        assert np.std(a.pdcsap_flux / np.median(a.pdcsap_flux)) >= v51d.SAP_MIN_PDCSAP_SD
    for a in aux[2:]:
        assert v51d.sap_applicability(a)[::2] == (False, "not_enough_data")


def test_the_cadence_cutoff_is_inclusive_at_n_min():
    lc, _ = make_lightcurve(PLANET, seed=6)
    a = _aux(lc, crowd=1.0)[0]
    rng = np.random.default_rng(2)
    a.sap_flux = a.pdcsap_flux + rng.normal(0.0, 3e-4, a.time.size)
    n = v51d.SAP_MIN_CADENCES
    keep = replace(a, time=a.time[:n], pdcsap_flux=a.pdcsap_flux[:n], sap_flux=a.sap_flux[:n])
    drop = replace(a, time=a.time[: n - 1], pdcsap_flux=a.pdcsap_flux[: n - 1],
                   sap_flux=a.sap_flux[: n - 1])  # fmt: skip
    assert v51d.sap_applicability(keep)[0] is True
    assert v51d.sap_applicability(drop)[::2] == (False, "not_enough_data")


def test_sabotage_the_written_rule_makes_the_affine_case_detectable(monkeypatch):
    # amendment 6's sabotage: the constant-factor rule treats the affine sectors as applicable and
    # emits a rule block that is detectable without information
    def written(a):
        sap, pdc = v51d._normalized(a.sap_flux), v51d._normalized(a.pdcsap_flux)
        both = np.isfinite(sap) & np.isfinite(pdc)
        if both.any() and np.max(np.abs(sap[both] - pdc[both])) <= v51d.AFFINE_TOLERANCE:
            return False, "identical up to a constant factor", None
        return True, "", None

    plan = _plan()
    aux = _affine_case()[:2]
    monkeypatch.setattr(v51d, "sap_applicability", written)
    r = v51d.check_systematics(aux, _candidate(), plan, seed=7)
    block = r.sensitivity["sap"]
    assert block.get("applicable", True) is not False
    assert block["detectable"] is True


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
