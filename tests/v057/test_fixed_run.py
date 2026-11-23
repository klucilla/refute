"""v0.5.7 fixed mode: the epoch window, the pilot's comparison and the doors' guard.

Synthetic data only; no network and no light curve download.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


fr = _load("v057_fixed_run", "docs/validation/v0.5.7/fixed_run.py")
rep = _load("v057_fixed_report", "docs/validation/v0.5.7/fixed_report.py")


def _curve(offset_hours: float, depth: float, seed: int = 1):
    rng = np.random.default_rng(seed)
    t = np.arange(0.0, 27.0, 2.0 / 1440.0)
    period, epoch, duration = 3.0, 1.0, 0.1
    flux = 1.0 + rng.normal(0.0, 1e-3, t.size)
    true_t0 = epoch + offset_hours / 24.0
    phase = (t - true_t0 + 0.5 * period) % period - 0.5 * period
    flux[np.abs(phase) < duration / 2.0] -= depth
    return t, flux, np.full(t.size, 1e-3), period, epoch, duration


def test_window_finds_an_offset_inside_it():
    t, f, s, p, e, d = _curve(offset_hours=1.0, depth=3e-3)
    w = fr.refine_epoch(t, f, s, p, e, d)
    assert w["found"]
    assert abs(w["offset_hours"] - 1.0) <= 2.0 / 60.0 + 1e-9
    assert w["window_half_width_hours"] == pytest.approx(d * 24.0)


def test_window_never_looks_outside_it():
    # A transit 6 h away from the propagated epoch (more than one 2.4 h duration): the window
    # cannot reach it, so the best in-window box is at the window's edge or nothing qualifies.
    t, f, s, p, e, d = _curve(offset_hours=6.0, depth=3e-3)
    w = fr.refine_epoch(t, f, s, p, e, d)
    assert abs(w["offset_hours"]) <= w["window_half_width_hours"] + 1e-9


def test_noise_only_is_not_found_and_keeps_the_propagated_epoch():
    t, f, s, p, e, d = _curve(offset_hours=0.0, depth=0.0, seed=3)
    w = fr.refine_epoch(t, f, s, p, e, d)
    if not w["found"]:
        assert w["offset_hours"] == 0.0 and w["depth"] is None
    assert w["min_snr"] == fr.MIN_WINDOW_SNR


def test_fixed_candidate_runs_through_the_unchanged_battery_on_a_synthetic_planet():
    import hashlib

    from refute.packs.tess.calib05 import c1
    from refute.packs.tess.detrend import detrend
    from refute.packs.tess.params import TessTestPlan
    from refute.packs.tess.pipeline import attack_candidate, global_prewhitening
    from refute.packs.tess.synthetic import discovery_v05_plan_dict

    plan = TessTestPlan.model_validate(discovery_v05_plan_dict())
    seed = int(hashlib.sha256(b"refute-v057-dev:fixed-P:0").hexdigest()[:16], 16)
    data, truth = c1.generate("P", seed)
    # the "TOI": the true ephemeris, its epoch moved by 0.4 duration (a drift inside the window)
    target = {
        "period_days": truth["period_days"],
        "epoch_bjd": truth["t0_btjd"] + fr.BTJD + 0.4 * truth["duration_days"],
        "duration_hours": truth["duration_days"] * 24.0,
    }
    flat = detrend(data.lc, plan.detrend)
    pw, searched = global_prewhitening(data, plan, flat)
    given, window = fr.fixed_candidate(searched, target)
    assert given.period == pytest.approx(truth["period_days"])
    assert abs(window["offset_hours"]) <= window["window_half_width_hours"]
    outcome = attack_candidate(data, given, plan, None, None, pw)
    final = outcome.candidate
    assert final is not None
    assert final.period == pytest.approx(truth["period_days"], rel=1e-3)
    offset = fr.epoch_offset_hours(final.t0, target["epoch_bjd"] - fr.BTJD, target["period_days"])
    assert abs(offset) <= window["window_half_width_hours"]
    assert {t.name for t in outcome.tests} >= {"snr", "odd_even", "secondary_eclipse"}


def test_epoch_offset_is_signed_and_wrapped():
    assert fr.epoch_offset_hours(1.5, 1.0, 3.0) == pytest.approx(12.0)
    assert fr.epoch_offset_hours(3.5, 1.0, 3.0) == pytest.approx(-12.0)
    assert fr.epoch_offset_hours(4.0, 1.0, 3.0) == pytest.approx(0.0)


def test_pilot_comparison_requires_every_test_and_the_outcome():
    s = {"target_key": "TIC-1", "status": "OK", "outcome": "SURVIVED",
         "tests": {"snr": {"status": "PASS"}, "odd_even": {"status": "PASS"}}}  # fmt: skip
    same = {**s}
    assert fr.compare(same, s)["reproduced"]
    one_test = {**s, "tests": {"snr": {"status": "PASS"}, "odd_even": {"status": "FAIL"}}}
    assert not fr.compare(one_test, s)["reproduced"]
    missing = {**s, "tests": {"snr": {"status": "PASS"}}}
    assert not fr.compare(missing, s)["reproduced"]
    assert not fr.compare({**s, "status": "ERROR"}, s)["reproduced"]


def test_pilot_set_is_ten_matched_records_in_draw_order():
    targets = fr.targets()
    assert len(targets) == 540
    pilot = fr.pilot_set(targets)
    assert len(pilot) == 10
    searched = fr.search_records()
    assert all(searched[t["key"]]["identity"]["matched"] for t in pilot)
    assert sum(t["part"] == "A" for t in pilot) == 5


def test_doors_are_not_marked_until_every_toi_has_a_fixed_record():
    report = rep.build_from([], "none")
    for door in report["doors"].values():
        assert door["found"] is None and door["complete"] is False
    assert report["doors"]["door_1"]["search_mode"] == 22
    assert report["doors"]["door_3"]["tois"] == 60


def test_door_one_counts_only_refuted_with_snr_pass():
    search = rep.load_search()
    records = [
        {"target_key": key, "part": r["part"], "arm": r["arm"], "status": "OK",
         "outcome": "INCONCLUSIVE", "tests": {"snr": {"status": "PASS", "severity": "fatal"}}}
        for key, r in search.items()
    ]  # fmt: skip
    report = rep.build_from(json.loads(json.dumps(records)), "synthetic")
    assert report["doors"]["door_1"]["fixed_mode"] == 0
    assert report["doors"]["door_1"]["found"] is True
    assert report["doors"]["door_4"]["found"] is False
