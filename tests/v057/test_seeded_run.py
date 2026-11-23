"""v0.5.7 TOI-seeded mode: the seed's window, the ephemeris record, the provenance, the pilot's
comparison and the doors' cohort guard.

Synthetic data and the git bundles only; no network and no light curve download.
"""

from __future__ import annotations

import hashlib
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


sr = _load("v057_seeded_run", "docs/validation/v0.5.7/seeded_run.py")
rep = _load("v057_seeded_report", "docs/validation/v0.5.7/seeded_report.py")


def _curve(offset_hours: float, depth: float, duration: float = 0.1, seed: int = 1):
    rng = np.random.default_rng(seed)
    t = np.arange(0.0, 27.0, 2.0 / 1440.0)
    period, epoch = 3.0, 1.0
    flux = 1.0 + rng.normal(0.0, 1e-3, t.size)
    true_t0 = epoch + offset_hours / 24.0
    phase = (t - true_t0 + 0.5 * period) % period - 0.5 * period
    flux[np.abs(phase) < duration / 2.0] -= depth
    return t, flux, np.full(t.size, 1e-3), period, epoch, duration


def test_the_window_grid_is_centred_and_never_passes_its_edge():
    duration = 83.46 / 1440.0  # not a multiple of the two-minute step
    offsets, full = sr.window_offsets(3.0, duration)
    assert not full
    assert offsets.max() <= duration + 1e-12 and offsets.min() >= -duration - 1e-12
    assert offsets[len(offsets) // 2] == 0.0 and np.allclose(offsets, -offsets[::-1])


def test_the_window_spans_the_whole_phase_only_inside_one_period():
    offsets, full = sr.window_offsets(0.3, 0.2)
    assert full
    assert offsets.min() >= -0.15 - 1e-12 and offsets.max() < 0.15


def test_the_seed_needs_valid_ephemeris_values():
    with pytest.raises(ValueError):
        sr.window_offsets(1.0, 1.5)
    with pytest.raises(ValueError):
        sr.window_offsets(float("nan"), 0.1)


def test_the_window_finds_an_offset_inside_it():
    t, f, s, p, e, d = _curve(offset_hours=1.0, depth=3e-3)
    w = sr.refine_epoch(t, f, s, p, e, d)
    assert w["found"]
    assert abs(w["offset_hours"] - 1.0) <= 2.0 / 60.0 + 1e-9


def test_a_strong_dip_just_beyond_the_edge_is_not_taken():
    d = 83.46 / 1440.0
    t, f, s, p, e, _ = _curve(offset_hours=(d * 24.0) + 1.5, depth=2e-2, duration=d)
    w = sr.refine_epoch(t, f, s, p, e, d)
    assert abs(w["offset_hours"]) <= w["window_half_width_hours"] + 1e-9


def test_no_data_in_the_window_keeps_the_propagated_epoch():
    t, f, s, p, e, d = _curve(offset_hours=0.0, depth=0.0)
    keep = np.abs((t - e + 0.5 * p) % p - 0.5 * p) > 2.0 * d  # no cadence near any transit
    w = sr.refine_epoch(t[keep], f[keep], s[keep], p, e, d)
    assert w["found"] is False and w["offset_hours"] == 0.0 and w["seed_depth"] is None


def test_epoch_offset_is_signed_and_wrapped():
    assert sr.epoch_offset_hours(1.5, 1.0, 3.0) == pytest.approx(12.0)
    assert sr.epoch_offset_hours(3.5, 1.0, 3.0) == pytest.approx(-12.0)
    assert sr.epoch_offset_hours(4.0, 1.0, 3.0) == pytest.approx(0.0)


def test_the_ephemeris_record_measures_drift_across_the_data():
    # the fit is 0.001 d longer than the TOI's period: 100 cycles later it is 0.1 d (one duration)
    rec = sr.ephemeris_record(3.0, 1.0, 0.1, 3.001, 1.0, 1.0, 1.0, 301.0, 5)
    assert rec["max_epoch_residual_durations"] == pytest.approx(1.0, rel=1e-6)
    assert rec["stayed_on_toi_ephemeris"] is True  # factor 1 and the epoch on time at t0
    off = sr.ephemeris_record(3.0, 1.0, 0.1, 3.0, 1.06, 1.0, 1.0, 30.0, 5)
    assert off["stayed_on_toi_ephemeris"] is False  # 1.44 h off, half a duration is 1.2 h
    none = sr.ephemeris_record(3.0, 1.0, 0.1, None, None, None, 1.0, 30.0, 0)
    assert none["stayed_on_toi_ephemeris"] is False and none["any_toi_event_covered"] is False


def _files(sectors, digest="a"):
    return [{"name": f"s{s:04d}", "sector": s, "sha256": f"{digest}{s}"} for s in sectors]


def test_provenance_refuses_other_sectors_and_compares_hashes():
    hist = {"light_curve_sectors": [1, 2], "pixel_file_sectors": [1, 2],
            "tpf_manifest": _files([1, 2]), "light_curve_manifest": _files([1, 2])}  # fmt: skip
    assert sr.provenance(_files([1, 2]), _files([1, 2]), hist)["overall"] == "same"
    other = sr.provenance(_files([1, 2, 3]), _files([1, 2]), hist)
    assert other["refuse"] and other["overall"] == "different"
    rebytes = sr.provenance(_files([1, 2], "b"), _files([1, 2]), hist)
    assert not rebytes["refuse"] and rebytes["overall"] == "different"
    part_a = {k: v for k, v in hist.items() if k != "light_curve_manifest"}
    assert sr.provenance(_files([1, 2]), _files([1, 2]), part_a)["overall"] == "unknown"
    assert sr.provenance(_files([1]), _files([1]), None)["overall"] == "unknown"


def test_the_seed_runs_through_the_unchanged_battery_on_a_synthetic_planet():
    from refute.packs.tess.calib05 import c1
    from refute.packs.tess.detrend import detrend
    from refute.packs.tess.params import TessTestPlan
    from refute.packs.tess.pipeline import attack_candidate, global_prewhitening
    from refute.packs.tess.synthetic import discovery_v05_plan_dict

    plan = TessTestPlan.model_validate(discovery_v05_plan_dict())
    seed = int(hashlib.sha256(b"refute-v057-dev:seeded-P:0").hexdigest()[:16], 16)
    data, truth = c1.generate("P", seed)
    target = {
        "period_days": truth["period_days"],
        "epoch_bjd": truth["t0_btjd"] + sr.BTJD + 0.4 * truth["duration_days"],
        "duration_hours": truth["duration_days"] * 24.0,
    }
    flat = detrend(data.lc, plan.detrend)
    pw, searched = global_prewhitening(data, plan, flat)
    given, window = sr.seed_candidate(searched, target)
    assert given.period == pytest.approx(truth["period_days"])
    outcome = attack_candidate(data, given, plan, None, None, pw)
    final = outcome.candidate
    assert final is not None
    eph = sr.ephemeris_record(
        target["period_days"], target["epoch_bjd"] - sr.BTJD, truth["duration_days"],
        final.period, final.t0, 1.0, float(data.lc.time.min()), float(data.lc.time.max()), 3,
    )  # fmt: skip
    assert eph["final_epoch_offset_hours"] is not None
    assert {t.name for t in outcome.tests} >= {"snr", "odd_even", "secondary_eclipse"}


def test_pilot_comparison_requires_every_test_and_the_outcome():
    s = {"target_key": "TIC-1", "status": "OK", "outcome": "SURVIVED",
         "tests": {"snr": {"status": "PASS"}, "odd_even": {"status": "PASS"}}}  # fmt: skip
    assert sr.compare({**s}, s)["reproduced"]
    one = {**s, "tests": {"snr": {"status": "PASS"}, "odd_even": {"status": "FAIL"}}}
    row = sr.compare(one, s)
    assert not row["reproduced"] and row["tests_differing"] == {
        "odd_even": {"search": "PASS", "seeded": "FAIL"}
    }
    assert not sr.compare({**s, "tests": {"snr": {"status": "PASS"}}}, s)["reproduced"]
    assert not sr.compare({**s, "status": "ERROR"}, s)["reproduced"]


def test_pilot_set_is_ten_matched_records_in_draw_order():
    targets = sr.targets()
    pilot = sr.pilot_set(targets)
    assert len(pilot) == 10 and sum(t["part"] == "A" for t in pilot) == 5
    searched = sr.search_records()
    assert all(searched[t["key"]]["identity"]["matched"] for t in pilot)


def _synthetic(outcome: str = "INCONCLUSIVE", stayed: bool = True) -> list[dict]:
    out = []
    for key, c in rep.cohort().items():
        out.append({"target_key": key, "part": c["part"], "arm": c["arm"], "status": "OK",
                    "outcome": outcome, "decisive": ["snr"],
                    "tests": {"snr": {"status": "PASS", "severity": "fatal"},
                              "period_alias": {"status": "FAIL", "severity": "warning"}},
                    "ephemeris": {"stayed_on_toi_ephemeris": stayed}})  # fmt: skip
    return out


def test_doors_are_not_marked_for_an_incomplete_or_wrong_cohort():
    report = rep.build_from([], "none")
    for version in ("total", "stayed"):
        assert all(d["found"] is None for d in report["doors"][version].values())
    base = report["doors"]["search_mode_baseline"]
    assert base["door_1"]["refuted_snr_pass"] == 22 and base["door_3"]["tois"] == 60
    records = _synthetic()
    records.append(dict(records[0]))  # a duplicate
    assert rep.build_from(records, "dup")["complete"] is False
    wrong = _synthetic()
    wrong[0]["arm"] = "fp" if wrong[0]["arm"] != "fp" else "planet"
    assert rep.build_from(wrong, "wrong")["complete"] is False


def test_door_two_counts_only_fatal_failures_and_both_versions_are_kept():
    records = _synthetic()
    report = rep.build_from(json.loads(json.dumps(records)), "synthetic")
    assert report["complete"] is True
    total = report["doors"]["total"]
    assert "period_alias" not in total["door_2"]["per_test"]  # a warning FAIL is never counted
    assert total["door_1"]["refuted_snr_pass"] == 0 and total["door_1"]["found"] is True
    assert total["door_4"]["found"] is False
    none_stayed = rep.build_from(_synthetic(stayed=False), "none stayed")
    assert none_stayed["doors"]["stayed"]["door_4"]["planets"] == 0
