"""v0.5.9 prototype: the box, the bounded entry, the probes, the consensus rule, the explicit path,
the centroid guard, the unit bookkeeping and the report's rules.

Offline: synthetic data and the git bundles only; nothing downloads.
"""

from __future__ import annotations

import importlib.util
import json
import math
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


run = _load("v059_prototype_run", "docs/validation/v0.5.9/prototype_run.py")
rep = _load("v059_prototype_report", "docs/validation/v0.5.9/prototype_report.py")


class _Search:
    refine_samples_per_width = 6.0
    final_oversample = 20
    final_duration_steps = 21


def _box_curve(period=3.7, t0=1326.3, duration=0.1, depth=0.002, noise=4e-4, span=54.0, seed=1):
    rng = np.random.default_rng(seed)
    t = np.arange(1325.0, 1325.0 + span, 2.0 / 1440.0)
    ph = (t - t0 + 0.5 * period) % period - 0.5 * period
    f = 1.0 + rng.normal(0.0, noise, t.size)
    f[(ph >= -duration / 2) & (ph < duration / 2)] -= depth
    return t, f, np.full(t.size, noise)


# --- the box and the entry ----------------------------------------------------------------------


def test_box_stats_recovers_an_injected_depth():
    t, f, s = _box_curve()
    st = run.box_stats(t, f, s, 3.7, 1326.3, 0.1)
    assert st["depth"] == pytest.approx(0.002, abs=4 * st["depth_err"])
    assert st["snr"] == pytest.approx(st["depth"] / st["depth_err"])
    assert st["log_likelihood"] == pytest.approx(0.5 * st["snr"] ** 2)
    empty = run.box_stats(t[:2], f[:2], s[:2], 3.7, 1326.3, 0.1)
    assert math.isnan(empty["depth"]) and empty["log_likelihood"] == 0.0


def test_entry_grids_use_the_battery_steps_and_record_them():
    g = run.entry_grids(3.7, 0.1, 54.0, _Search)
    fine = 0.1 * 3.7 / (6.0 * 54.0) / 10.0
    assert g["period_step_days"] == pytest.approx(fine) and not g["period_step_coarsened"]
    assert g["periods"][0] == pytest.approx(3.7 * (1 - run.PERIOD_WINDOW), abs=fine)
    assert g["periods"][-1] == pytest.approx(3.7 * (1 + run.PERIOD_WINDOW), abs=fine)
    assert g["offsets"][0] == pytest.approx(-0.05) and g["offsets"][-1] == pytest.approx(0.05)
    assert g["epoch_step_days"] == pytest.approx(0.1 / 20)
    assert g["durations"][0] == pytest.approx(0.05) and g["durations"][-1] == pytest.approx(0.15)
    long = run.entry_grids(3.7, 0.1, 4000.0, _Search)
    assert long["period_step_coarsened"] and long["period_points"] == 2 * run.MAX_PERIOD_STEPS + 1


def test_bounded_fit_finds_the_injection_inside_the_window():
    t, f, s = _box_curve()
    pivot = run.pivot_epoch(1326.3, 3.7, 0.5 * (t[0] + t[-1]))
    g = run.entry_grids(3.7, 0.1, float(t[-1] - t[0]), _Search)
    best = run.bounded_fit(t, f, s, pivot, g)
    assert best is not None and not run.edges(best, g)
    assert best["period"] == pytest.approx(3.7, abs=2 * g["period_step_days"])
    assert best["t0"] == pytest.approx(pivot, abs=2 * g["epoch_step_days"])
    assert best["duration"] == pytest.approx(0.1, abs=0.011)
    assert best["snr"] > 10


def test_an_entry_far_from_the_signal_sits_on_the_edge_or_finds_nothing():
    t, f, s = _box_curve()
    wrong = 3.7 * (1 + 5 * run.PERIOD_WINDOW)  # the true period is outside the window
    pivot = run.pivot_epoch(1326.3, wrong, 0.5 * (t[0] + t[-1]))
    g = run.entry_grids(wrong, 0.1, float(t[-1] - t[0]), _Search)
    best = run.bounded_fit(t, f, s, pivot, g)
    assert best is None or run.edges(best, g)


def test_the_pivot_is_the_cycle_nearest_the_middle():
    assert run.pivot_epoch(10.0, 2.0, 21.2) == pytest.approx(22.0)
    assert run.pivot_epoch(10.0, 2.0, 10.9) == pytest.approx(10.0)


# --- the probes and the consensus ---------------------------------------------------------


def test_six_probes_in_the_frozen_order_with_their_steps():
    probes = run.probe_ephemerides(3.7, 1350.0, 0.1, 54.0, _Search)
    assert [p["probe"] for p in probes] == ["p1", "p2", "p3", "p4", "p5", "p6"]
    assert probes[0]["t0"] - 1350.0 == pytest.approx(0.1 / 20)
    assert probes[1]["t0"] - 1350.0 == pytest.approx(-0.1 / 20)
    assert probes[2]["period"] - 3.7 == pytest.approx(0.1 * 3.7 / (6.0 * 54.0) / 10.0)
    assert probes[4]["duration"] - 0.1 == pytest.approx(0.1 / 20)
    assert all(p["step_days"] > 0 for p in probes)
    for p in probes:  # one axis at a time
        moved = [p["period"] != 3.7, p["t0"] != 1350.0, p["duration"] != 0.1]
        assert sum(moved) == 1


def _ok(outcome):
    return {"status": "OK", "outcome": outcome}


def test_consensus_only_demotes_and_names_the_first_disagreement():
    names = [n for n, _, _ in run.PROBES]
    agree = {n: _ok("SURVIVED") for n in names}
    assert run.consensus(_ok("SURVIVED"), agree)["outcome"] == "SURVIVED"
    one = {**agree, "p3": _ok("WEAKENED"), "p5": _ok("REFUTED")}
    c = run.consensus(_ok("SURVIVED"), one)
    assert c["outcome"] == "INCONCLUSIVE" and c["first_disagreeing"] == "p3"
    missing = {n: v for n, v in agree.items() if n != "p6"}
    assert run.consensus(_ok("SURVIVED"), missing)["first_disagreeing"] == "p6"
    failed = {**agree, "p1": {"status": "ERROR"}}
    assert run.consensus(_ok("SURVIVED"), failed)["first_disagreeing"] == "p1"
    assert run.consensus(_ok("INCONCLUSIVE"), {})["outcome"] == "INCONCLUSIVE"
    promote = {n: _ok("SURVIVED") for n in names}
    assert run.consensus(_ok("INCONCLUSIVE"), promote)["outcome"] == "INCONCLUSIVE"
    assert run.consensus(None, agree)["outcome"] is None
    assert run.consensus({"status": "ERROR"}, agree)["outcome"] is None


# --- the explicit path ----------------------------------------------------------------------------


def test_only_the_version_2_path_runs():
    from refute.packs.tess.params import TessTestPlan
    from refute.packs.tess.synthetic import discovery_v05_plan_dict, discovery_v051_plan_dict

    assert run.explicit_path(TessTestPlan.model_validate(discovery_v05_plan_dict())) is None
    assert run.explicit_path(TessTestPlan.model_validate(discovery_v051_plan_dict())) is not None
    assert run.explicit_path(TessTestPlan.model_validate({})) is not None


# --- the centroid guard -------------------------------------------------------------------


def test_the_guards_reject_singular_covariances_and_negative_quadratic_forms():
    rows = [{"sector": 1, "cov_sky": np.array([[1.0, 1.0], [1.0, 1.0]]),
             "offset_sky": np.zeros(2)}]  # fmt: skip
    with pytest.raises(run.NumericFailureError):
        run.guarded_combine(lambda r: None)(rows)
    with pytest.raises(run.NumericFailureError):
        run.guarded_sky_power(lambda r, *a: None)(rows, 1.0)
    sig = run.guarded_sigma(lambda c, d: 1.0)
    with pytest.raises(run.NumericFailureError):
        sig(-5.0, 2)
    with pytest.raises(run.NumericFailureError):
        sig(float("nan"), 2)

    def overflow(c, d):
        raise OverflowError("math range error")

    with pytest.raises(run.NumericFailureError):
        run.guarded_sigma(overflow)(3.0, 2)
    assert sig(3.0, 2) == 1.0


@pytest.mark.parametrize("exc", [np.linalg.LinAlgError("Singular matrix"),
                                 OverflowError("math range error")])  # fmt: skip
def test_a_numerical_failure_becomes_an_inconclusive_centroid(exc):
    from refute.core.verdict import TestStatus
    from refute.packs.tess import battery, centroid_v5

    saved = (centroid_v5.combine, centroid_v5.sky_power, battery.gaussian_sigma_from_chi2)

    def original(*args):
        raise exc

    out = run.guarded_centroid(original)([], [], None, None, 0)
    assert out.status is TestStatus.INCONCLUSIVE and out.coverage == 0
    assert out.name == "centroid_shift" and type(exc).__name__ in out.message
    assert out.metrics["numerical_failure"]["kind"] == type(exc).__name__
    assert (centroid_v5.combine, centroid_v5.sky_power,
            battery.gaussian_sigma_from_chi2) == saved  # restored  # fmt: skip


def test_the_guard_runs_inside_the_real_centroid_test(monkeypatch):
    """A singular sky covariance in a qualified sector reaches ``combine`` in the real
    ``check_centroid_v5``: INCONCLUSIVE with the reason, never ERROR."""
    from types import SimpleNamespace

    from refute.core.verdict import TestStatus
    from refute.packs.tess import centroid_v5
    from refute.packs.tess.params import TessTestPlan
    from refute.packs.tess.synthetic import discovery_v05_plan_dict

    plan = TessTestPlan.model_validate(discovery_v05_plan_dict())

    def row(px, *a):
        return {"sector": px.sector, "offset_px": np.zeros(2), "offset_sky": np.zeros(2),
                "cov_sky": np.array([[1.0, 1.0], [1.0, 1.0]]), "pixel_scale": 21.0,
                "n_cadences": 500, "controls": 10}  # fmt: skip

    monkeypatch.setattr(centroid_v5, "sector_offset", row)
    pixels = [SimpleNamespace(sector=s) for s in (1, 2, 3)]
    with pytest.raises(np.linalg.LinAlgError):
        centroid_v5.check_centroid_v5(pixels, [], None, plan, 0)  # the unguarded test fails
    out = run.guarded_centroid(centroid_v5.check_centroid_v5)(pixels, [], None, plan, 0)
    assert out.status is TestStatus.INCONCLUSIVE and "not positive definite" in out.message


# --- the fixed evaluation and the two entries on synthetic data ---------------------------


@pytest.fixture(scope="module")
def synthetic():
    from refute.packs.tess.params import TessTestPlan
    from refute.packs.tess.synthetic import (
        discovery_v05_plan_dict,
        scenario_data,
        with_sky_jacobians,
    )

    data = with_sky_jacobians(scenario_data("planet"))
    return data, TessTestPlan.model_validate(discovery_v05_plan_dict())


def test_the_fixed_evaluation_keeps_the_given_ephemeris(synthetic):
    from refute.packs.tess import centroid_v5, pipeline

    data, plan = synthetic
    saved = (pipeline.finalize_candidate, centroid_v5.check_centroid_v5)
    ev = run.evaluate_fixed(data, plan, 3.7, 1326.3, 2.5 / 24, 0.0)
    assert (pipeline.finalize_candidate, centroid_v5.check_centroid_v5) == saved  # restored
    c = ev["candidate"]
    assert c["period_days"] == 3.7 and c["t0_btjd"] == 1326.3
    assert c["duration_hours"] == pytest.approx(2.5)
    assert c["depth"] == pytest.approx(0.002, rel=0.3) and c["snr"] > 7.1
    assert ev["outcome"] in ("SURVIVED", "WEAKENED", "REFUTED", "INCONCLUSIVE")
    assert "centroid_shift" in ev["tests"] and "snr" in ev["tests"]


def test_both_entries_reach_the_injected_signal(synthetic):
    from refute.packs.tess.detrend import detrend
    from refute.packs.tess.pipeline import global_prewhitening

    data, plan = synthetic
    t_mid = 0.5 * (float(np.nanmin(data.lc.time)) + float(np.nanmax(data.lc.time)))
    toi = {"period": 3.7, "epoch": 1326.3, "duration": 2.5 / 24}
    e = run.entry_fit(data, plan, toi, t_mid, float(data.lc.span))
    assert e["resolved"] and len(e["passes"]) == 2
    assert e["final"]["period"] == pytest.approx(3.7, rel=run.PERIOD_WINDOW)
    _, searched = global_prewhitening(data, plan, detrend(data.lc, plan.detrend))
    s = run.search_fit(data, plan, searched, t_mid)
    assert s["resolved"] and s["final"]["period"] == pytest.approx(3.7, rel=1e-3)
    bad = run.entry_fit(data, plan, {"period": 3.7, "epoch": float("nan"), "duration": 0.1},
                        t_mid, float(data.lc.span))  # fmt: skip
    assert not bad["resolved"] and "missing or invalid" in bad["unresolved_reason"]


# --- the units -----------------------------------------------------------------------------------


def test_unit_keys_and_the_order_of_readiness(tmp_path, monkeypatch):
    monkeypatch.setattr(run, "RECORDS", tmp_path)
    t = {"key": "TIC-1", "tic_id": 1}
    assert run.unit_key("TIC-1", "fetch") == "TIC-1.fetch"
    assert run.unit_key("TIC-1", "base", "E") == "TIC-1.E.base"
    assert run.unit_key("TIC-1", "probe", "S", "p4") == "TIC-1.S.p4"

    def write(key, rec):
        (tmp_path / f"{key}.json").write_text(json.dumps(rec), "utf-8")

    assert [u["key"] for u in run.ready_units([t])] == ["TIC-1.fetch"]
    write("TIC-1.fetch", {"status": "OK"})
    assert [u["key"] for u in run.ready_units([t])] == ["TIC-1.E.base", "TIC-1.S.base"]
    write("TIC-1.E.base", {"status": "OK", "outcome": "SURVIVED"})
    write("TIC-1.S.base", {"status": "OK", "outcome": "INCONCLUSIVE"})
    assert [u["key"] for u in run.ready_units([t])] == [f"TIC-1.E.p{i}" for i in range(1, 7)]
    assert not run.target_done(t)
    for i in range(1, 7):
        write(f"TIC-1.E.p{i}", {"status": "OK", "outcome": "SURVIVED"})
    assert run.ready_units([t]) == [] and run.target_done(t)
    write("TIC-2.fetch", {"status": "ERROR"})
    assert run.ready_units([{"key": "TIC-2"}]) == [] and run.target_done({"key": "TIC-2"})


def test_the_set_file_matches_its_rule_when_it_exists():
    if not run.SET_FILE.exists():
        pytest.skip("the set is drawn after the seed is committed")
    doc = json.loads(run.SET_FILE.read_text("utf-8"))
    assert run.build_set() == doc
    assert len(doc["changes"]) == 13 and len(doc["reverse"]) == 1
    assert {doc["tois"][k] for k in doc["numeric_errors"]} == run.NAMED_NUMERIC
    assert all(len(v) == run.CONTROLS_PER_CLASS for v in doc["controls"].values())
    assert len(doc["order"]) == 24 == len(set(doc["order"]))


# --- the report's rules -------------------------------------------------------------------------


def _record(key, mode, outcome, cons=None, status="OK"):
    return {"target_key": key, "entry_mode": mode, "status": status, "toi": key,
            "base": {"outcome": outcome, "outcome_reason": "r"},
            "consensus": {"status": "OK", "outcome": cons or outcome}}  # fmt: skip


def test_the_report_marks_nothing_until_complete():
    ok, problems = rep.complete([_record("A", "E", "SURVIVED")], ["A"])
    assert not ok and problems


def test_the_report_pairs_and_controls():
    by = {
        ("A", "E"): _record("A", "E", "SURVIVED"),
        ("A", "S"): _record("A", "S", "SURVIVED", "INCONCLUSIVE"),
        ("B", "E"): _record("B", "E", "INCONCLUSIVE"),
        ("B", "S"): _record("B", "S", "INCONCLUSIVE"),
        ("C", "E"): _record("C", "E", "REFUTED", status="ERROR"),
        ("C", "S"): _record("C", "S", "REFUTED"),
    }
    base = rep.pairs(by, ["A", "B", "C"], rep.base_out)
    assert base["stable"]["k"] == 2 and base["both_decided"] == 1
    assert base["both_inconclusive"] == 1
    cons = rep.pairs(by, ["A", "B", "C"], rep.cons_out)
    assert cons["stable"]["k"] == 1 and cons["both_inconclusive"] == 1
    q2 = rep.q2(by, {"SURVIVED": ["A"], "INCONCLUSIVE": ["B"]})
    assert q2["base"]["k"] == 2 and q2["consensus"]["k"] == 1
    q4 = rep.q4(by, ["A", "B", "C"])
    assert q4["E"]["base"]["k"] == 1 and q4["S"]["base"]["k"] == 2
    assert q4["S"]["lost_to_consensus"] == 1
    q3 = rep.q3(by, ["C"])
    assert not q3["all_ended"]
