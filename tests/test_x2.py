"""X2's execution package (docs/validation/v0.2.1/reopen/stage-1/x2-declaration.md, revision 2;
x2-execution-package.md): the realizations, the cases, the seeds, X2-A's geometry and causes,
X2-B's statistics and verdicts, and the lot's resumption (an interrupted lot relaunched gives the
records of a continuous run, byte for byte). Synthetic data only; no network."""

from __future__ import annotations

import hashlib
import importlib
import math
import sys
import uuid
from collections import Counter
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
POPULATION = ROOT / "docs" / "validation" / "v0.2.1" / "population"


@pytest.fixture(scope="module")
def x2():
    sys.path.insert(0, str(POPULATION))
    return importlib.import_module("x2_study")


@pytest.fixture(scope="module")
def ev():
    sys.path.insert(0, str(POPULATION))
    return importlib.import_module("x2_evaluate")


# --- the cases, the seeds, the realizations ------------------------------------------------------


def test_the_cases_are_the_declared_rule(x2):
    cases = x2.x2_cases()
    assert len(cases) == 80 and len({c["id"] for c in cases}) == 80
    groups = Counter(x2.rs.group_of(c) for c in cases)
    assert groups == {g: 20 for g in x2.GROUPS}
    for g in x2.GROUPS:
        rows = [c for c in cases if x2.rs.group_of(c) == g]
        assert Counter(c["band"] for c in rows) == {"near": 10, "measurable": 10}
        mech = Counter(c["mechanism"] for c in rows)
        if g.endswith("no variability"):
            assert mech == {"two_years": 10, "three_years": 6, "few_train": 4}
        else:
            assert mech == {"variability_some_years": 20}
    assert x2.x2_cases() == cases  # deterministic


def test_the_seeds_are_the_declared_rule_and_distinct(x2):
    cases = x2.x2_cases()
    c = cases[0]
    g = x2.rs.group_of(c)
    text = f"refute/v0.2.1/stage-1/X2/{g}/{c['id']}/7"
    assert x2.realization_seed(g, c["id"], 7) == int.from_bytes(
        hashlib.sha256(text.encode()).digest()[:8], "big"
    )
    seeds = [x2.realization_seed(x2.rs.group_of(c), c["id"], j) for c in cases for j in range(100)]
    assert len(set(seeds)) == 8000


@pytest.fixture(scope="module")
def two_cases(x2):
    cases = x2.x2_cases()
    white = next(c for c in cases if c["noise"] == "white" and c["mechanism"] == "two_years")
    red = next(c for c in cases if c["noise"] == "correlated" and c["mechanism"] != "two_years")
    return white, red


def test_the_case_s_own_seed_gives_the_case_byte_for_byte(x2, two_cases):
    for case in two_cases:
        blob, _ = x2.pv2.build_case(case)
        meta, arrays = x2.pv2.deserialize(blob)
        ref = x2.pv2.parts_to_data(meta, arrays)
        data, p, model, _ = x2.realization(case, x2.case_noise_seed(meta))
        for f in ("time", "flux", "flux_err", "sector", "year"):
            assert getattr(data.lc, f).tobytes() == getattr(ref.lc, f).tobytes(), (case["id"], f)
        assert data.sectors == ref.sectors and p == meta["parameters"]


def test_another_seed_changes_the_noise_only(x2, two_cases):
    for case in two_cases:
        g = x2.rs.group_of(case)
        a, pa, ma, _ = x2.realization(case, x2.realization_seed(g, case["id"], 0))
        b, pb, mb, _ = x2.realization(case, x2.realization_seed(g, case["id"], 1))
        assert pa == pb and np.array_equal(ma, mb)
        for f in ("time", "flux_err", "sector", "year"):
            assert np.array_equal(getattr(a.lc, f), getattr(b.lc, f))
        assert not np.array_equal(a.lc.flux, b.lc.flux)
        assert np.std((a.lc.flux - ma) - (b.lc.flux - mb)) > 0  # the noises differ, the model not


# --- X2-A ----------------------------------------------------------------------------------------


def test_the_identity_classes_and_their_tolerance(ev):
    d, span = 0.1, 700.0
    eps = d / (2 * span)
    assert ev.identity_class(3.0 * (1 + 0.9 * eps), 3.0, d, span) == "same"
    assert ev.identity_class(3.0 * (1 + 1.1 * eps), 3.0, d, span) == "other"
    assert ev.identity_class(6.0, 3.0, d, span) == "alias x2"
    assert ev.identity_class(9.0, 3.0, d, span) == "alias x3"
    assert ev.identity_class(1.5, 3.0, d, span) == "alias /2"
    assert ev.identity_class(1.0, 3.0, d, span) == "alias /3"
    assert ev.identity_class(4.1, 3.0, d, span) == "other"


def test_the_predicted_centers_are_the_engine_s(ev):
    from refute.packs.tess.ephemeris import Ephemeris
    from refute.packs.tess.holdout import _predict_windows
    from refute.packs.tess.params import HoldoutParams

    eph = Ephemeris(1326.3, 4, 3.7, ((1e-6, 0.0), (0.0, 1e-10)), 1.0, 8)
    spans = [(2061.0, 2088.0), (2089.0, 2116.0)]
    engine = [
        w.t_pred for w in _predict_windows(eph, 0.1, spans, HoldoutParams()) if w.kind == "transit"
    ]
    mine = ev.predicted_centers(eph.to_dict(), 0.0, spans)
    assert np.allclose(sorted(engine), sorted(mine), rtol=0, atol=1e-9)
    shifted = ev.predicted_centers(eph.to_dict(), 1e-4, spans)
    m = [(c - eph.t_ref) / eph.period for c in mine]
    assert np.allclose(np.array(shifted) - np.array(mine), np.round(m) * 1e-4, atol=1e-9)


TRUTH = {
    "period": 3.7,
    "t0": 1326.3,
    "duration": 0.104,
    "depth": 0.002,
    "impact": 0.2,
    "ingress_fraction": 0.1,
}
SPANS = [(2061.0, 2088.0)]
SPAN = 2088.0 - 1325.0


def _deficit(t):
    from refute.packs.tess import synthetic

    spec = synthetic.SignalSpec(
        period=TRUTH["period"],
        t0=TRUTH["t0"],
        depth=TRUTH["depth"],
        duration=TRUTH["duration"],
        ingress_fraction=TRUTH["ingress_fraction"],
    )
    return 1.0 - synthetic.signal_model(t, spec)


HIDDEN_T = np.arange(2061.0, 2088.0, 2.0 / 1440.0)


def _round(**kw):
    eph = {
        "t_ref": TRUTH["t0"],
        "n_ref": 0,
        "period": TRUTH["period"],
        "t_ref_err": 1e-4,
        "period_err": 1e-7,
    }
    base = {
        "train_ephemeris": eph,
        "train_duration_days": TRUTH["duration"],
        "max_timing_sigma_days": 0.002,
        "measurement_status": "ok",
        "twin_status": "ok",
        "dp": 0.0,
        "d_train": None,
        "d_twin": None,
        "d_hidden": 0.0018,
        "e_train": 3e-5,
        "e_hidden": 3e-5,
    }
    base.update(kw)
    return base


def _registered(eph: dict, duration: float = TRUTH["duration"]) -> list[dict]:
    """The windows the engine registers for this ephemeris (its own functions)."""
    from refute.packs.tess.ephemeris import Ephemeris
    from refute.packs.tess.holdout import _predict_windows, register_replicas
    from refute.packs.tess.params import HoldoutParams

    e = Ephemeris(eph["t_ref"], eph["n_ref"], eph["period"], ((1e-8, 0.0), (0.0, 1e-12)), 1.0, 8)
    windows = _predict_windows(e, duration, SPANS, HoldoutParams())
    return [
        {
            "kind": w.kind,
            "epoch": w.epoch,
            "t_pred": w.t_pred,
            "half_width": w.half_width,
            "baseline_inner": w.baseline_inner,
            "baseline_outer": w.baseline_outer,
        }
        for w in [*windows, *register_replicas(e, windows, SPANS)]
    ]


def _geom(ev, registered="engine", **kw):
    rnd = _round(**kw)
    if registered == "engine":
        registered = _registered(rnd["train_ephemeris"])
    return ev.round_geometry(rnd, TRUTH, HIDDEN_T, SPANS, SPAN, _deficit, registered)


def test_the_overlaps_use_every_registered_window(ev):
    """Codex's review: with the train period twice the true one, the true transits between the
    predicted ones fall in the control windows, which the engine masks: none is outside a mask."""
    b = _geom(ev)["b_true"]
    eph = {**_round()["train_ephemeris"], "period": 2 * TRUTH["period"]}
    g = _geom(ev, d_train=b, d_twin=b, train_ephemeris=eph)
    kinds = {w["kind"] for w in _registered(eph)}
    assert {"transit", "control"} <= kinds
    assert g["outside_masks"] == pytest.approx(0.0)
    assert g["overlap_box"] == pytest.approx(0.5, abs=0.1)  # every other true transit boxed
    transit_only = [w for w in _registered(eph) if w["kind"] == "transit"]
    g_t = _geom(ev, registered=transit_only, d_train=b, d_twin=b, train_ephemeris=eph)
    assert g_t["outside_masks"] > 0.3  # without the control masks the same transits look unmasked
    # windows not registered (a round stopped before them): no overlap claimed, the rest kept
    g_none = _geom(ev, registered=None, d_train=b, d_twin=b)
    assert "outside_masks" not in g_none and g_none["identity"] == "same"


def test_the_exact_ephemeris_has_no_loss(ev):
    probe = _geom(ev)
    b = probe["b_true"]
    g = _geom(ev, d_train=b, d_twin=b)
    assert g["identity"] == "same" and g["offset_max_durations"] < 1e-6
    assert g["overlap_box"] == pytest.approx(1.0) and g["outside_masks"] == 0.0
    assert (
        g["L"] == pytest.approx(1.0)
        and g["I"] == pytest.approx(1.0)
        and g["A"] == pytest.approx(1.0)
    )
    assert g["cause"] == "none"
    # the factors multiply to d_twin / d_train
    g2 = _geom(
        ev,
        d_train=1.7 * b,
        d_twin=0.6 * b,
        train_ephemeris={**_round()["train_ephemeris"], "t_ref": TRUTH["t0"] + 0.02},
    )
    assert (1 / g2["I"]) * g2["L"] * g2["A"] == pytest.approx(0.6 / 1.7)


def test_each_cause_is_named_by_its_largest_reduction(ev):
    b = _geom(ev)["b_true"]
    eph = _round()["train_ephemeris"]
    assert _geom(ev, d_train=3 * b, d_twin=b)["cause"] == "inflated train depth"
    assert _geom(ev, d_train=b, d_twin=0.1 * b)["cause"] == "attenuation in the processing"
    assert _geom(ev, d_train=b, d_twin=-0.1 * b)["cause"] == "attenuation in the processing"
    off = _geom(ev, d_train=b, d_twin=0.0, train_ephemeris={**eph, "t_ref": TRUTH["t0"] + 0.3})
    assert off["L"] == 0.0 and off["cause"] == "imprecise extrapolation"
    assert off["offset_max_durations"] > 0.5 and off["overlap_box"] == 0.0
    double = _geom(ev, d_train=b, d_twin=b, train_ephemeris={**eph, "period": 2 * TRUTH["period"]})
    assert double["identity"] == "alias x2" and double["cause"] == "wrong candidate"
    assert (
        _geom(ev, d_train=b, d_twin=b, measurement_status="too_few_windows")["cause"]
        == "twin unavailable"
    )
    no_eph = ev.round_geometry({}, TRUTH, HIDDEN_T, SPANS, SPAN, _deficit, None)
    assert no_eph["cause"] == "twin unavailable" and no_eph["has_ephemeris"] is False
    assert ev.cause({"has_ephemeris": False}) == "twin unavailable"
    # a tie goes to the first in the declared order (inflated, extrapolation, processing)
    tie = {"has_ephemeris": True, "twin_ok": True, "identity": "same", "I": 2.0, "L": 0.5, "A": 0.5}
    assert ev.cause(tie) == "inflated train depth"
    undefined = {"has_ephemeris": True, "twin_ok": True, "identity": "same"}
    assert ev.cause(undefined) == "none"


def test_the_z_train_the_fail_and_the_class_counts_over_every_round(ev):
    b = _geom(ev)["b_true"]
    g = _geom(ev, d_train=b, d_twin=0.1 * b)
    assert g["z_train"] == pytest.approx((b - 0.1 * b) / math.sqrt(2) / 3e-5)
    failing = _geom(ev, d_train=b, d_twin=0.1 * b, s_meas=1.0, d_hidden=0.0)
    assert failing["fail"] is True and g["fail"] is False  # g has no s_meas
    no_eph = ev.round_geometry({}, TRUTH, HIDDEN_T, SPANS, SPAN, _deficit, None)
    counts = ev.class_counts([g, _geom(ev, d_train=b, d_twin=b), failing, no_eph])
    assert counts["all"]["n"] == 4 and counts["all"]["counts"]["twin unavailable"] == 1
    assert counts["z_train_ge_3"]["n"] == 2 and counts["fail"]["n"] == 1


# --- X2-B ----------------------------------------------------------------------------------------


def _rows(n, sigma, e_pred, seed=0, offset=0.0):
    rng = np.random.default_rng(seed)
    return [
        {
            "measured": True,
            "twin_ok": True,
            "d_twin": 1e-3 + offset * k,
            "d_hidden": 1e-3 + offset * k + rng.normal(0, sigma),
            "e_hidden": e_pred,
            "e_pred_1": 1.2 * e_pred,
            "e_pred_2": e_pred,
        }
        for k in range(n)
    ]


def test_the_measurement_s_scatter_is_separated_from_the_signal_s(ev):
    s = ev.case_year_stats(_rows(400, 1e-4, 1e-4, offset=1e-6))
    assert s["sigma_meas_sd"] == pytest.approx(1e-4, rel=0.1)
    assert s["sigma_sig"] == pytest.approx(np.std(1e-6 * np.arange(400), ddof=1), rel=1e-6)
    assert s["sigma_tot"] > s["sigma_meas_sd"]
    assert s["rho_2_sd"] == pytest.approx(1.0, rel=0.1)
    assert ev.case_year_stats(_rows(29, 1e-4, 1e-4))["excluded"] is True
    unmeasured = [{**r, "measured": False} for r in _rows(40, 1e-4, 1e-4)]
    assert ev.case_year_stats(unmeasured) == {"realizations": 40, "measured": 0, "excluded": True}


def test_the_cell_interval_is_a_cluster_bootstrap_with_its_fixed_seed(ev):
    per_case = {f"c{i}": [1.0 + 0.01 * i, 1.0 - 0.01 * i] for i in range(20)}
    a = ev.cell_interval(per_case, n_boot=300)
    assert a == ev.cell_interval(per_case, n_boot=300)
    assert a["cases"] == 20 and a["lo"] <= a["value"] <= a["hi"]
    assert ev.cell_interval({f"c{i}": [1.0] for i in range(14)})["value"] is None
    assert ev.boot_seed() == int.from_bytes(
        hashlib.sha256(b"refute/v0.2.1/stage-1/X2/bootstrap").digest()[:8], "big"
    )


def test_the_verdicts_and_the_scale_s_disagreement(ev):
    assert ev.verdict(0.95, 1.05, 1.0) == "calibrated or conservative as designed"
    assert ev.verdict(0.95, 1.30, 1.2) == "calibrated or conservative as designed"
    assert ev.verdict(1.20, 1.40, 1.0) == "overestimated"
    assert ev.verdict(0.60, 0.85, 1.0) == "underestimated"
    assert ev.verdict(0.85, 1.05, 1.0) == "not determined"
    assert ev.verdict(None, None, 1.0) == "not determined"
    same = {"lo": 0.95, "hi": 1.05}
    assert ev.cell_verdict(same, same, 1.0)["verdict"] == "calibrated or conservative as designed"
    assert ev.cell_verdict(same, {"lo": 1.2, "hi": 1.4}, 1.0)["verdict"] == "not determined"


# --- the lot's resumption ------------------------------------------------------------------------


def _declared():
    return {
        "format": "refute-m4-configuration/1",
        "name": "M4-rmin-study",
        "path": "docs/validation/v0.2.1/population/m4-configurations/rmin-study.json",
        "sha256": "0" * 64,
        "block_sha256": "1" * 64,
    }


def _plan():
    from refute.packs.tess import synthetic
    from refute.packs.tess.params import TessTestPlan

    plan = synthetic.fast_plan_dict()
    plan["gauntlet"] = {"corrections": {"version": 2, "enabled": True, "r_min": 8}}
    return TessTestPlan.model_validate(plan)


@pytest.fixture
def lot_env(x2, monkeypatch):
    import refute.packs.tess.holdout as holdout

    monkeypatch.setattr(x2.v3, "STATE", {"problem": None, "identity": _declared()})
    monkeypatch.setattr(x2.v3, "_plan", _plan)
    original = holdout.calibration_measurement

    def measurement(raw, sectors, year, plan, *, identity, twin_model=None):
        # the declared identity is a stand-in (its block hash is not the plan's)
        from refute.core.canonical import canonical_sha256

        block = canonical_sha256(plan.gauntlet.corrections.model_dump(mode="json"))
        return original(
            raw,
            sectors,
            year,
            plan,
            identity={**identity, "block_sha256": block},
            twin_model=twin_model,
        )

    monkeypatch.setattr(holdout, "calibration_measurement", measurement)
    return x2


def _bytes(run):
    return {
        p.relative_to(run).as_posix(): p.read_bytes() for p in (run / "records").rglob("*.json")
    }


def _tasks(x2):
    cases = x2.x2_cases()
    white = next(c for c in cases if c["noise"] == "white" and c["mechanism"] == "two_years")
    red = next(c for c in cases if c["noise"] == "correlated" and c["mechanism"] == "two_years")
    return [(white, 0), (white, 1), (red, 0)]


def test_an_interrupted_lot_relaunched_gives_the_continuous_run_s_bytes(lot_env):
    x2 = lot_env
    tasks = _tasks(x2)
    base = ROOT / ".cache" / "test-x2-lots" / uuid.uuid4().hex
    continuous = base / "continuous"
    first = x2.run_x2_lot(continuous, tasks=tasks, workers=1, executor=x2.rs._InlineExecutor())
    assert first["complete"] is True and first["dispatched"] == 3
    reference = _bytes(continuous)
    assert len(reference) == 3

    interrupted = base / "interrupted"
    ticks = iter([0.0, 0.0] + [1e9] * 100)  # the deadline stops the dispatch after one task
    partial = x2.run_x2_lot(
        interrupted,
        tasks=tasks,
        workers=1,
        executor=x2.rs._InlineExecutor(),
        deadline_hours=1.0,
        clock=lambda: next(ticks),
    )
    assert partial["complete"] is False and partial["deadline_reached"] is True
    assert len(_bytes(interrupted)) == 1
    # a write cut short: a temporary file left behind is never read as a record
    case, j = tasks[1]
    left = x2.record_path(interrupted, case["id"], j)
    left.parent.mkdir(parents=True, exist_ok=True)
    (left.parent / f".{left.name}.99999.tmp").write_text('{"truncated', encoding="utf-8")
    assert x2.load_x2_lot(interrupted)["leftovers"]
    resumed = x2.run_x2_lot(interrupted, tasks=tasks, workers=1, executor=x2.rs._InlineExecutor())
    assert resumed["complete"] is True and resumed["dispatched"] == 2
    assert _bytes(interrupted) == reference
    assert x2.x2_lot_problems(interrupted) == []


def test_a_record_is_never_replaced_and_another_manifest_is_refused(lot_env):
    x2 = lot_env
    path = ROOT / ".cache" / "test-x2-lots" / uuid.uuid4().hex / "records" / "c" / "000.json"
    x2.write_record_atomic(path, "{}\n")
    with pytest.raises(FileExistsError):
        x2.write_record_atomic(path, '{"other": 1}\n')
    assert path.read_text(encoding="utf-8") == "{}\n"
    assert not list(path.parent.glob(".*.tmp"))
    run = ROOT / ".cache" / "test-x2-lots" / uuid.uuid4().hex
    x2.run_x2_lot(run, tasks=_tasks(x2)[:1], workers=1, executor=x2.rs._InlineExecutor())
    with pytest.raises(SystemExit, match="manifest"):
        x2.run_x2_lot(run, tasks=_tasks(x2)[:2], workers=1, executor=x2.rs._InlineExecutor())


def _fake_record(x2, case, j, configuration):
    """A complete record of the task without running the engine (the runner's own tests)."""
    g = x2.rs.group_of(case)
    sectors = x2.expected_sectors(case)
    years = sorted({s["year"] for s in sectors})
    return {
        "format": x2.RECORD_FORMAT,
        "target": f"{x2.PREFIX}/{case['id']}",
        "group": g,
        "case_id": case["id"],
        "mechanism": case["mechanism"],
        "band": case["band"],
        "realization": j,
        "noise_seed": str(x2.realization_seed(g, case["id"], j)),
        "years": years,
        "sectors": sectors,
        "configuration": configuration,
        "rounds": [{**dict.fromkeys(x2.ROUND_FIELDS), "hidden_year": y} for y in years],
        "registered_windows": {str(y): None for y in years},
        "truth": dict.fromkeys(x2.TRUTH_FIELDS, 1.0),
    }


@pytest.fixture
def fake_lot(lot_env, monkeypatch):
    x2 = lot_env
    monkeypatch.setattr(x2, "_x2_task", lambda task: _fake_record(x2, *task))
    cases = [c for c in x2.x2_cases() if c["mechanism"] == "two_years"][:6]
    return x2, [(c, 0) for c in cases]


def test_an_incomplete_record_is_refused_at_the_check_and_at_the_relaunch(fake_lot):
    x2, tasks = fake_lot
    run = ROOT / ".cache" / "test-x2-lots" / uuid.uuid4().hex
    assert x2.run_x2_lot(run, tasks=tasks[:2], workers=1, executor=x2.rs._InlineExecutor())[
        "complete"
    ]
    case, j = tasks[0]
    path = x2.record_path(run, case["id"], j)
    good = _fake_record(x2, case, j, _declared())
    assert x2.record_problems(good, case, j, good["noise_seed"], _declared()) == []
    for drop in ("rounds", "years", "truth", "registered_windows", "sectors"):
        rec = {k: v for k, v in good.items() if k != drop}
        assert x2.record_problems(rec, case, j, rec["noise_seed"], _declared()), drop
    # Codex's second review: a whole year missing (its sector, its round and its windows removed),
    # and a round reduced to its hidden year, were accepted
    short = {
        **good,
        "years": good["years"][:1],
        "sectors": good["sectors"][:1],
        "rounds": good["rounds"][:1],
        "registered_windows": {str(good["years"][0]): None},
    }
    assert any(
        "layout" in p for p in x2.record_problems(short, case, j, good["noise_seed"], _declared())
    )
    thin = {**good, "rounds": [{"hidden_year": y} for y in good["years"]]}
    assert any(
        "lacks" in p for p in x2.record_problems(thin, case, j, good["noise_seed"], _declared())
    )
    # a record in its place but naming another realization, a stray copy elsewhere, and a second
    # name for the same task (0000.json beside 000.json)
    bad = _fake_record(x2, case, 1, _declared())
    path.unlink()
    path.write_text(x2.record_text(bad), encoding="utf-8")
    stray = run / "records" / case["id"] / "007.json"
    stray.write_text(x2.record_text(bad), encoding="utf-8")
    (run / "records" / case["id"] / "0000.json").write_text(x2.record_text(good), encoding="utf-8")
    problems = x2.x2_lot_problems(run)
    assert any("names" in p for p in problems)
    assert any("007.json" in p and "own path" in p for p in problems)
    assert any("0000.json" in p and "own path" in p for p in problems)
    with pytest.raises(SystemExit, match="incomplete"):
        x2.run_x2_lot(run, tasks=tasks[:2], workers=1, executor=x2.rs._InlineExecutor())


def test_the_manifest_binds_the_code_and_is_published_atomically(fake_lot, monkeypatch):
    x2, tasks = fake_lot
    run = ROOT / ".cache" / "test-x2-lots" / uuid.uuid4().hex
    x2.run_x2_lot(run, tasks=tasks[:1], workers=1, executor=x2.rs._InlineExecutor())
    manifest = (run / "manifest.json").read_text(encoding="utf-8")
    assert (
        '"code_sha256"' in manifest and '"plan_sha256"' in manifest and '"environment"' in manifest
    )
    monkeypatch.setattr(x2, "code_digest", lambda: "f" * 64)
    with pytest.raises(SystemExit, match="code"):
        x2.run_x2_lot(run, tasks=tasks[:1], workers=1, executor=x2.rs._InlineExecutor())
    other = ROOT / ".cache" / "test-x2-lots" / uuid.uuid4().hex
    other.mkdir(parents=True)
    (other / "manifest.json").write_text('{"truncated', encoding="utf-8")
    with pytest.raises(SystemExit, match="not readable"):
        x2.run_x2_lot(other, tasks=tasks[:1], workers=1, executor=x2.rs._InlineExecutor())


def test_the_evaluation_refuses_another_code_than_the_lot_s(fake_lot, monkeypatch):
    x2, tasks = fake_lot
    run = ROOT / ".cache" / "test-x2-lots" / uuid.uuid4().hex
    x2.run_x2_lot(run, tasks=tasks[:1], workers=1, executor=x2.rs._InlineExecutor())
    monkeypatch.setattr(x2, "x2_lot_problems", lambda run_dir: [])  # the subset is not the lot
    monkeypatch.setattr(x2, "code_digest", lambda: "e" * 64)
    with pytest.raises(SystemExit, match="code_sha256"):
        x2.evaluate_lot(run)
    assert "docs/validation/v0.2.1/population/x2_evaluate.py" in x2.CODE_FILES


def test_the_ceiling_is_read_right_before_each_submission(fake_lot):
    """The deadline passes while the runner waits for room (4 per worker in flight): no task is
    submitted after it (Codex's review: the clock was read before the wait)."""
    x2, tasks = fake_lot
    run = ROOT / ".cache" / "test-x2-lots" / uuid.uuid4().hex

    def clock():  # time "passes" once the first records are written, i.e. during the wait
        root = run / "records"
        n = len(list(root.rglob("*.json"))) if root.exists() else 0
        return 0.0 if n == 0 else 1e9

    report = x2.run_x2_lot(
        run,
        tasks=tasks,
        workers=1,
        executor=x2.rs._InlineExecutor(),
        deadline_hours=1.0,
        clock=clock,
    )
    assert report["deadline_reached"] is True and report["submitted"] == 4
    assert len(list((run / "records").rglob("*.json"))) == 4


def test_the_workers_are_explicit(fake_lot, monkeypatch):
    x2, tasks = fake_lot
    monkeypatch.setenv("REFUTE_WORKERS", "3")
    run = ROOT / ".cache" / "test-x2-lots" / uuid.uuid4().hex
    report = x2.run_x2_lot(run, tasks=tasks[:1], workers=2, executor=x2.rs._InlineExecutor())
    assert report["workers"] == 2
    with pytest.raises(SystemExit, match="--workers"):
        x2.main(["run", str(run)])


def test_the_evaluation_orders_the_findings_and_counts_every_round(ev):
    rows = []
    rng = np.random.default_rng(1)
    for g, scale in (("A", 0.5), ("B", 1.0)):  # A: e_pred half the scatter (underestimated)
        for c in range(20):
            for j in range(40):
                d_twin = 1e-3
                rows.append(
                    {
                        "group": g,
                        "mechanism": "two_years",
                        "n_years": 2,
                        "case_id": f"{g}{c}",
                        "realization": j,
                        "year": 2020,
                        "has_ephemeris": True,
                        "identity": "same",
                        "L": 1.0,
                        "cause": "none",
                        "fail": False,
                        "measured": True,
                        "twin_ok": True,
                        "d_twin": d_twin,
                        "d_hidden": d_twin + rng.normal(0, 1e-4),
                        "e_hidden": scale * 1e-4,
                        "e_pred_1": scale * 1e-4,
                        "e_pred_2": scale * 1e-4,
                    }
                )
    rows.append(
        {
            **rows[0],
            "case_id": "A0",
            "year": 2018,
            "has_ephemeris": False,
            "cause": "twin unavailable",
            "measured": False,
        }
    )
    out = ev.evaluate(rows, m_beta=1.0)
    assert out["findings"][0]["verdict"] == "underestimated" and out["findings"][0]["cell"] == "A"
    # Codex's second review: the per-round metrics, the case-year statistics and section 7 are kept
    assert len(out["rows"]) == len(rows)
    stats = out["x2b"]["B"]["case_year_stats"]["B0 | 2020"]
    assert {"sigma_meas_sd", "sigma_meas_mad", "sigma_tot", "sigma_sig"} <= set(stats)
    assert set(out["descriptive"]["A"]) == {
        "stopped_that_would_pass",
        "structural_impediments",
        "rho_by_mechanism",
        "rho_by_n_pred",
        "measured",
    }
    assert out["descriptive"]["A"]["measured"] == {"x": 800, "n": 801}
    assert out["x2a"]["by_cell"]["A"]["all"]["n"] == 801  # the unmeasured round counted
    assert out["x2b"]["A"]["excluded"] == 1  # its case-year has no measured realization
    assert out["x2b"]["B"]["ratios"]["rho_2"]["verdict"] in (
        "calibrated or conservative as designed",
        "not determined",
    )


def test_the_counterfactual_counts_only_the_capacity_refusals(ev):
    """Codex's third review: a round without a predicted window, or with its train replicas below
    r_min, was counted as one that a smaller error would let pass."""
    rows = []
    rng = np.random.default_rng(2)
    for c in range(20):
        for j in range(40):
            rows.append(
                {
                    "group": "A",
                    "mechanism": "two_years",
                    "n_years": 2,
                    "case_id": f"A{c}",
                    "realization": j,
                    "year": 2020,
                    "has_ephemeris": True,
                    "identity": "same",
                    "cause": "none",
                    "fail": False,
                    "measured": True,
                    "twin_ok": True,
                    "d_twin": 1e-3,
                    "d_hidden": 1e-3 + rng.normal(0, 1e-3),
                    "e_hidden": 1e-3,
                    "e_pred_1": 1e-3,
                    "e_pred_2": 1e-3,
                    "d_c": 0.01,
                    "threshold": 5.0,
                    "n_pred": 4,
                    "decision_1": [
                        "no_predicted_window",
                        "train_replicas_below_r_min",
                        "insufficient_capacity_train",
                        "pass",
                    ][j % 4],
                    "decision_2": "insufficient_capacity_hidden_noise" if j % 4 == 3 else None,
                }
            )
    d = ev.evaluate(rows, m_beta=1.0)["descriptive"]["A"]
    assert d["stopped_that_would_pass"]["decision_1"] == {
        "refused_by_capacity": 200,
        "would_pass_with_sigma_meas": 200,
    }
    assert d["stopped_that_would_pass"]["decision_2"]["refused_by_capacity"] == 200
    assert d["structural_impediments"] == {
        "decision_1: no_predicted_window": 200,
        "decision_1: train_replicas_below_r_min": 200,
    }


def test_a_write_cut_short_leaves_no_record(x2, monkeypatch):
    """A process stopped while writing (here: the flush to disk fails) leaves the record absent,
    never a truncated record file; the temporary file left is never read as a record."""
    import os

    path = ROOT / ".cache" / "test-x2-lots" / uuid.uuid4().hex / "records" / "c" / "000.json"

    def cut(fd):
        raise OSError("stopped")

    monkeypatch.setattr(os, "fsync", cut)
    with pytest.raises(OSError, match="stopped"):
        x2.write_record_atomic(path, '{"a": 1}\n')
    assert not path.exists()
    assert [p.name for p in path.parent.iterdir()] == [f".000.json.{os.getpid()}.tmp"]


def test_the_truth_is_never_read_during_the_engine_calls(lot_env, monkeypatch):
    """The record's truth is made before the calls and read only after them (X1's guard): an engine
    that reads it fails, and the record carries the injected parameters."""
    import refute.packs.tess.holdout as holdout

    x2 = lot_env
    case, j = _tasks(x2)[0]
    rec = x2.record_realization(case, j, _declared())
    assert set(rec["truth"]) >= {"period", "t0", "duration", "depth"}
    made = []
    original = x2.rs.EvaluatorTruth

    def capture(data):
        t = original(data)
        made.append(t)
        return t

    monkeypatch.setattr(x2.rs, "EvaluatorTruth", capture)
    current = holdout.calibration_measurement

    def leaky(*a, **k):
        made[-1]["period"]
        return current(*a, **k)

    monkeypatch.setattr(holdout, "calibration_measurement", leaky)
    with pytest.raises(RuntimeError, match="truth"):
        x2.record_realization(case, j, _declared())
