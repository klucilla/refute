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


def test_transits_are_counted_with_the_box_membership():
    t = np.array([0.0, 0.03, 0.2, 1.0, 2.04, 2.3, 3.5])  # in the box: cycles 0, 1 and 2
    f, s = np.ones(t.size), np.ones(t.size)
    st = run.box_stats(t, f, s, 1.0, 0.0, 0.1)
    assert st["n_in"] == 4 and st["n_transits"] == 3
    s[3] = np.nan  # the only point of cycle 1 has no finite noise: that cycle does not count
    assert run.box_stats(t, f, s, 1.0, 0.0, 0.1)["n_transits"] == 2


def test_entry_grids_stay_inside_the_window_with_exact_ends():
    g = run.entry_grids(3.7, 0.1, 54.0, _Search)
    fine = 0.1 * 3.7 / (6.0 * 54.0) / 10.0
    assert g["period_step_days"] <= fine and not g["period_step_coarsened"]
    half = 3.7 * run.PERIOD_WINDOW
    assert g["periods"][0] == 3.7 - half and g["periods"][-1] == 3.7 + half
    assert np.all(np.abs(g["periods"] - 3.7) <= half)
    assert np.allclose(np.diff(g["periods"]), g["period_step_days"])
    assert g["offsets"][0] == -0.05 and g["offsets"][-1] == 0.05
    assert np.all(np.abs(g["offsets"]) <= 0.05)
    assert g["epoch_step_days"] == pytest.approx(0.1 / 20)
    assert g["durations"][0] == pytest.approx(0.05) and g["durations"][-1] == pytest.approx(0.15)
    long = run.entry_grids(3.7, 0.1, 4000.0, _Search)
    assert long["period_step_coarsened"] and long["period_points"] == 2 * run.MAX_PERIOD_STEPS + 1
    assert np.all(np.abs(long["periods"] - 3.7) <= half)


def test_an_interior_optimum_is_not_pushed_to_the_edge():
    """The injection sits half a step inside the window's end: the optimum is an interior trial
    or the exact end, never a trial beyond the window."""
    period = 3.7 * (1 + 0.9 * run.PERIOD_WINDOW)
    t, f, s = _box_curve(period=period, noise=1e-4)
    g = run.entry_grids(3.7, 0.1, float(t[-1] - t[0]), _Search)
    best = run.bounded_fit(t, f, s, run.pivot_epoch(1326.3, period, 0.5 * (t[0] + t[-1])), g)
    assert best is not None and abs(best["period"] - 3.7) <= 3.7 * run.PERIOD_WINDOW
    assert "period" not in run.edges(best, g)
    assert best["period"] == pytest.approx(period, abs=2 * g["period_step_days"])


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
    c = run.consensus(_ok("SURVIVED"), missing)  # not recorded: apart from a recorded failure
    assert c["status"] == "INCOMPLETE" and c["outcome"] is None and "p6" in c["reason"]
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
        run.guarded_sky_power(lambda r, *a: None, None)(rows, 1.0)
    with pytest.raises(run.NumericFailureError, match="symmetric"):
        run._check_pd([[1.0, 4.0], [0.0, 1.0]], "an asymmetric matrix")  # Cholesky alone passes
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


def _saved():
    from refute.packs.tess import battery, centroid_v5

    return (centroid_v5.combine, centroid_v5.sky_power, centroid_v5.simulated_probability,
            battery.gaussian_sigma_from_chi2)  # fmt: skip


def test_a_guarded_failure_becomes_an_inconclusive_centroid():
    from refute.core.verdict import TestStatus

    saved = _saved()

    def original(*args):
        raise run.NumericFailureError("a singular matrix (observed): Singular matrix")

    out = run.guarded_centroid(original)([], [], None, None, 0)
    assert out.status is TestStatus.INCONCLUSIVE and out.coverage == 0
    assert out.name == "centroid_shift" and "Singular matrix" in out.message
    assert "Singular matrix" in out.metrics["numerical_failure"]["reason"]
    assert _saved() == saved  # restored


@pytest.mark.parametrize("exc", [np.linalg.LinAlgError("elsewhere"), ValueError("unrelated")])
def test_unrelated_failures_propagate_and_the_patches_are_restored(exc):
    saved = _saved()

    def original(*args):
        raise exc

    with pytest.raises(type(exc)):
        run.guarded_centroid(original)([], [], None, None, 0)
    assert _saved() == saved


def test_the_simulation_path_checks_its_quadratic_forms():
    """``sky_power``'s simulations: a non-finite draw reaches the checked rule and is a numerical
    failure; with valid rows the guarded ``sky_power`` equals the plain one."""
    from types import SimpleNamespace

    from refute.core.sensitivity import simulated_probability
    from refute.packs.tess import centroid_v5

    rows = [{"sector": s, "cov_sky": np.array([[2.0, 0.3], [0.3, 1.5]]),
             "offset_sky": np.array([0.4, -0.2])} for s in (1, 2)]  # fmt: skip
    fake = SimpleNamespace(simulated_probability=simulated_probability)

    def original(rows_, *a):
        def draw(rng, n):
            return np.full((n, 2, 2), np.nan)

        return fake.simulated_probability(draw, lambda o: np.zeros(len(o), bool), 1)

    with pytest.raises(run.NumericFailureError, match="simulated heterogeneity"):
        run.guarded_sky_power(original, fake)(rows)
    assert fake.simulated_probability is simulated_probability  # restored
    plain = centroid_v5.sky_power(rows, 20.0, 10.5, 3.0, 0.00135, 7)
    guarded = run.guarded_sky_power(centroid_v5.sky_power, centroid_v5)(rows, 20.0, 10.5, 3.0,
                                                                       0.00135, 7)  # fmt: skip
    assert guarded == plain and centroid_v5.simulated_probability is simulated_probability


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


def test_the_report_marks_nothing_until_the_run_is_terminal_and_whole():
    rows = [_record("A", m, "SURVIVED") for m in ("E", "S")]
    assert rep.complete(rows, ["A"], "complete")[0]
    assert not rep.complete(rows, ["A"], "open")[0]  # no terminal state
    assert not rep.complete(rows[:1], ["A"], "complete")[0]  # a row is missing
    by = {(r["target_key"], r["entry_mode"]): r for r in rows}
    assert rep.toi_complete(by, "A")
    by[("A", "S")] = {**rows[1], "status": "NO RECORD"}
    assert not rep.toi_complete(by, "A")
    by[("A", "S")] = {**rows[1], "consensus": {"status": "INCOMPLETE"}}
    assert not rep.toi_complete(by, "A")  # a probe never ran: not a demotion
    by[("A", "S")] = {**rows[1], "required_missing": ["TIC-1.S.p2"]}
    assert not rep.toi_complete(by, "A")
    by[("A", "S")] = {**rows[1], "status": "ERROR", "reason": "recorded failure"}
    assert rep.toi_complete(by, "A")  # a recorded failure with its reason is complete


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
    assert base["same_decided_class"]["k"] == 1 and base["both_inconclusive"]["k"] == 1
    assert base["same_class"]["k"] == 2
    cons = rep.pairs(by, ["A", "B", "C"], rep.cons_out)
    assert cons["same_decided_class"]["k"] == 0 and cons["both_inconclusive"]["k"] == 1
    q2 = rep.q2(by, {"SURVIVED": ["A"], "INCONCLUSIVE": ["B"]})
    assert q2["base"]["k"] == 2 and q2["consensus"]["k"] == 1
    q4 = rep.q4(by, ["A", "B", "C"])
    assert q4["E"]["base"]["k"] == 1 and q4["S"]["base"]["k"] == 2
    assert q4["S"]["lost_to_consensus"] == 1
    q3 = rep.q3(by, ["C"])
    assert not q3["all_ended"]


def test_q3_needs_a_reason_and_reports_skipped_evaluations_apart():
    by = {
        ("X", "E"): {"target_key": "X", "entry_mode": "E", "status": "OK",
                     "base": {"outcome": "INCONCLUSIVE", "outcome_reason": "entry unresolved: x",
                              "tests": {}}},
        ("X", "S"): {"target_key": "X", "entry_mode": "S", "status": "NOT_RUN (fetch ERROR)",
                     "reason": None, "base": None},
    }  # fmt: skip
    q3 = rep.q3(by, ["X"])
    assert not q3["all_ended"]  # a skipped mode without a reason does not pass
    assert not q3["all_evaluated"] and q3["rows"][0]["ended_with_status_and_reason"]


# --- downloads and cleanup ----------------------------------------------------------------


def test_downloads_are_metered_and_refused_at_the_allowance(tmp_path):
    from types import SimpleNamespace

    def download_checked(product, row_name, download_dir, **kw):
        path = tmp_path / row_name
        path.write_bytes(b"x" * product)
        return path

    def discard_if_incomplete(path, root):
        Path(path).unlink()
        return True

    adapter = SimpleNamespace(download_checked=download_checked,
                              discard_if_incomplete=discard_if_incomplete)  # fmt: skip
    meter = {"completed_bytes": 0, "partial_bytes": 0, "files": 0}
    with run.metered(adapter, 150, meter):
        adapter.download_checked(100, "a.fits", tmp_path)
        partial = tmp_path / "p.fits"
        partial.write_bytes(b"y" * 30)
        assert adapter.discard_if_incomplete(partial, tmp_path)
        adapter.download_checked(40, "b.fits", tmp_path)  # 130 < 150: allowed
        with pytest.raises(run.DownloadAllowanceError):
            adapter.download_checked(10, "c.fits", tmp_path)  # 170 >= 150: refused
    assert meter == {"completed_bytes": 140, "partial_bytes": 30, "files": 2}
    assert adapter.download_checked is download_checked  # restored


def test_cleanup_needs_a_complete_or_abandoned_run(tmp_path, monkeypatch):
    monkeypatch.setattr(run.sr, "LEDGER", tmp_path / "ledger.json")
    run.sr._save_ledger({"state": "stopped", "batches": []})
    with pytest.raises(SystemExit, match="not complete or abandoned"):
        run.clean()
    run.abandon("the maintainer ended the run")
    assert run.sr._ledger()["state"] == "abandoned"
    run.sr._save_ledger({"state": "open", "batches": []})
    with pytest.raises(SystemExit, match="only a stopped run"):
        run.abandon("too early")


def test_a_changed_file_refuses_a_resume():
    pinned = {**run.fingerprints(), "plan": "0" * 64}
    with pytest.raises(SystemExit, match="changed"):
        run.check_pinned({"pinned_fingerprints": pinned})
    run.check_pinned({"pinned_fingerprints": run.fingerprints()})
    run.check_pinned({})
