"""The instrumentation of the calibration record (stage 1, item D), written before the code, from
its acceptance record: docs/validation/v0.2.1/reopen/stage-1/instrumentation-acceptance.md
(revision 2). No decision of the engine changes; the new fields are copies of values the round
already computes. Synthetic light curves only (tests/instrumentation_cases.py).

The new fields of ``calibration_measurement``'s record (declared by the acceptance record):
``n_pred``, ``grid_dp``, ``train_var_rep``, ``hidden_var_rep``, ``e_pred_1``, ``e_pred_2``,
``m_beta``, ``d_c``, ``train_ephemeris``, ``train_duration_days``, ``max_timing_sigma_days``,
``n_transit_times``; on the evaluator's side (``rmin_study.record_target``), a ``truth`` mapping
added after the engine's calls, guarded against any read during them.
"""

import importlib
import inspect
import json
import math
import sys
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pytest

import refute.packs.tess.holdout as holdout
import refute.packs.tess.search as search_module
from refute.core.io import dumps_json, to_jsonable

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import instrumentation_cases as ic  # noqa: E402

SNAPSHOT = Path(__file__).resolve().parent / "fixtures" / "instrumentation_snapshot.json"
DIAG = ("train_ephemeris", "train_duration_days", "max_timing_sigma_days", "n_transit_times")
CAPACITY = ("n_pred", "grid_dp", "d_c", "m_beta")
NEW = (*DIAG, *CAPACITY, "train_var_rep", "e_pred_1", "hidden_var_rep", "e_pred_2")
ALL = set(NEW)

# matrix (a) of the acceptance record: the fields set at each stopping point (the others None)
MATRIX = {
    "no_train_data": set(),
    "no_candidate": set(),
    "rejected_before_times": {"train_duration_days"},
    "train_noise_undetermined": {"train_duration_days"},
    "too_few_times": {"train_duration_days", "n_transit_times"},
    "timing_stop": set(DIAG),
    "validity_after_windows": set(DIAG),
    "no_predicted_window": set(DIAG) | set(CAPACITY),
    "train_replicas_below": set(DIAG) | set(CAPACITY) | {"train_var_rep"},
    "decision_1_failed": ALL,
    "hidden_noise_stop": ALL - {"e_pred_2"},
    "decision_2_failed": ALL,
    "measurement_stop": ALL,
    "measured_white": ALL,
    "measured_ar1": ALL,
}


@contextmanager
def spies(calls):
    """Record the value each source function returned during one calibration call."""
    names = (
        "count_n_pred",
        "period_grid",
        "train_replica_stats",
        "predicted_error",
        "replica_stats",
        "fit_linear_ephemeris",
        "corrected_transit_times",
        "_predict_windows",
    )
    saved = {n: getattr(holdout, n) for n in names}
    saved_fin = search_module.finalize_candidate

    def wrap(name, fn):
        def inner(*a, **k):
            out = fn(*a, **k)
            calls.setdefault(name, []).append(out)
            return out

        return inner

    try:
        for n in names:
            setattr(holdout, n, wrap(n, saved[n]))
        search_module.finalize_candidate = wrap("finalize_candidate", saved_fin)
        yield
    finally:
        for n, fn in saved.items():
            setattr(holdout, n, fn)
        search_module.finalize_candidate = saved_fin


def _json(value):
    return json.loads(dumps_json(to_jsonable(value)))


@pytest.fixture(scope="module")
def results():
    out = {}
    for case in ic.cases():
        calls: dict = {}
        with ic.replaced(case):
            with spies(calls):
                record = holdout.calibration_measurement(
                    case.lc,
                    case.sectors,
                    case.hidden_year,
                    case.plan,
                    identity=ic.identity(case.plan),
                )
            outcome = holdout.run_holdout(case.lc, case.sectors, case.plan)
        out[case.name] = {"case": case, "record": record, "calls": calls, "outcome": outcome}
    return out


@pytest.fixture(scope="module")
def snapshot():
    return json.loads(SNAPSHOT.read_text(encoding="utf-8"))


def _round_of(outcome, year):
    return next(r for r in outcome.rounds if r.hidden_year == year)


# --- AB3: every stopping point of matrix (a) ---------------------------------------------------


@pytest.mark.parametrize("name", sorted(MATRIX))
def test_each_stopping_point_records_exactly_its_row(results, snapshot, name):
    record = results[name]["record"]
    # the case reached its row (the precondition of the row, checked on the old fields)
    assert snapshot["cases"][name]["row"] == results[name]["case"].row
    for f in NEW:
        assert f in record, f"{name}: {f} absent (it must be present, None when unknown)"
        if f in MATRIX[name]:
            assert record[f] is not None, f"{name}: {f} should be set"
        else:
            assert record[f] is None, f"{name}: {f} should be None, is {record[f]!r}"


# --- AC5: nothing else changes -----------------------------------------------------------------


def _same(a, b, path=""):
    """Equal structure, keys, list lengths and every non-float value (strings, statuses, reasons,
    integers, booleans, None); a float matches a float of the same kind (finite, NaN or infinite).

    The first version compared floats to 1e-9 relative; CI (run 39627687323) showed that the
    engine's own floats differ across platforms far more than that (a train period at 2e-6
    relative, a BLS SNR at 2e-4), with every status and reason identical. The values themselves
    are compared exactly in the snapshot's environment (the test above)."""
    if isinstance(a, dict) and isinstance(b, dict):
        assert set(a) == set(b), f"{path}: keys {sorted(set(a) ^ set(b))}"
        for k in a:
            _same(a[k], b[k], f"{path}.{k}")
    elif isinstance(a, list) and isinstance(b, list):
        assert len(a) == len(b), f"{path}: lengths {len(a)} {len(b)}"
        for i, (x, y) in enumerate(zip(a, b, strict=True)):
            _same(x, y, f"{path}[{i}]")
    elif isinstance(a, float) and isinstance(b, float):

        def kind(x):
            return "nan" if math.isnan(x) else "inf" if math.isinf(x) else "finite"

        assert kind(a) == kind(b), f"{path}: {a!r} against {b!r}"
    else:
        assert a == b, f"{path}: {a!r} != {b!r}"


# The environment the snapshot was made in (tests/make_instrumentation_snapshot.py, run on
# 2026-10-21 in the integration worktree's venv). Recorded with the tests after Codex's review of
# the round; the generator did not record it.
SNAPSHOT_ENV = ("Windows", "3.13.16")


def _exact(a, b, path=""):
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True), path


@pytest.mark.parametrize("name", sorted(MATRIX))
def test_the_old_record_and_run_holdout_are_byte_identical_in_the_snapshot_s_environment(
    results, snapshot, name
):
    """AC5 exactly where it can be exact: in the snapshot's own environment the old fields and the
    whole run_holdout outcome are identical as JSON, bit for bit."""
    import platform

    if (platform.system(), platform.python_version()) != SNAPSHOT_ENV:
        pytest.skip(f"exact only in {SNAPSHOT_ENV}; the tolerant comparison below runs everywhere")
    old = snapshot["cases"][name]
    record = _json(results[name]["record"])
    _exact({k: v for k, v in record.items() if k not in ALL}, old["record"], name)
    _exact(_json(results[name]["outcome"].to_dict()), old["run_holdout"], name)


@pytest.mark.parametrize("name", sorted(MATRIX))
def test_the_old_record_and_run_holdout_are_unchanged(results, snapshot, name):
    old = snapshot["cases"][name]
    record = _json(results[name]["record"])
    _same({k: v for k, v in record.items() if k not in ALL}, old["record"], name)
    _same(_json(results[name]["outcome"].to_dict()), old["run_holdout"], name)


# --- AC2: every new field is the value the round used -------------------------------------------


def _set_fields(name, results):
    return [f for f in MATRIX[name]]


@pytest.mark.parametrize("name", [n for n, s in MATRIX.items() if "n_pred" in s])
def test_the_capacity_fields_are_the_values_the_round_used(results, name):
    r = results[name]
    record, calls, plan = r["record"], r["calls"], r["case"].plan
    assert record["n_pred"] == calls["count_n_pred"][0]
    grid = [float(x) for x in calls["period_grid"][0]]
    assert record["grid_dp"] == grid
    assert record["m_beta"] == plan.gauntlet.corrections.m_beta
    assert record["d_c"] == pytest.approx(
        record["d_train"] - holdout.CAPACITY_K * record["e_train"], rel=1e-12
    )
    if record["train_var_rep"] is not None:
        counts, variances = calls["train_replica_stats"][0]
        assert len(record["train_var_rep"]) == len(grid)
        for i, v in enumerate(variances):  # element-wise, paired with grid_dp[i]
            assert record["train_var_rep"][i] == v
    if record["e_pred_1"] is not None:
        assert record["e_pred_1"] == calls["predicted_error"][0]
    if record["hidden_var_rep"] is not None:
        stats = calls["replica_stats"][0]
        assert record["hidden_var_rep"] == [p.var_rep for p in stats.per_dp]
        assert [p.dp for p in stats.per_dp] == record["grid_dp"]
    if record["e_pred_2"] is not None:
        assert record["e_pred_2"] == calls["predicted_error"][1]


def test_the_variances_differ_across_dp_so_the_pairing_is_checked(results):
    """The precondition of the element-wise checks (sabotage S2: a permutation keeps the
    maximum)."""
    rec = results["measured_white"]["record"]
    assert len(set(rec["train_var_rep"])) > 1
    assert len(set(rec["hidden_var_rep"])) > 1


@pytest.mark.parametrize("name", [n for n, s in MATRIX.items() if "train_ephemeris" in s])
def test_the_ephemeris_and_the_timing_are_the_round_s(results, name):
    r = results[name]
    record, outcome, year = r["record"], r["outcome"], r["case"].hidden_year
    eph = r["calls"]["fit_linear_ephemeris"][0]
    assert record["train_ephemeris"] == eph.to_dict()
    assert record["train_ephemeris"] == _round_of(outcome, year).train_ephemeris
    assert record["n_transit_times"] == len(r["calls"]["corrected_transit_times"][0].times)


@pytest.mark.parametrize("name", [n for n, s in MATRIX.items() if "max_timing_sigma_days" in s])
def test_the_timing_sigma_is_the_one_of_the_predicted_windows(results, name):
    """AC2 for max_timing_sigma_days in every row that has it (added after Codex's review of the
    round): recomputed from plan_round's predicted windows (its first _predict_windows call)."""
    r = results[name]
    record, plan = r["record"], r["case"].plan
    windows = r["calls"]["_predict_windows"][0]
    duration = record["train_duration_days"]
    expected = max(
        (
            (w.half_width - duration / 2) / plan.gauntlet.holdout_by_year.timing_sigma
            for w in windows
            if w.kind == "transit"
        ),
        default=0.0,
    )
    assert record["max_timing_sigma_days"] == expected


def test_the_timing_number_is_the_one_the_reason_prints(results):
    record = results["timing_stop"]["record"]
    printed = f"({record['max_timing_sigma_days'] * 24:.2f} h)"
    assert printed in record["reason"]
    metrics = _round_of(results["timing_stop"]["outcome"], 2020).metrics
    assert record["max_timing_sigma_days"] == metrics["max_timing_sigma_days"]


@pytest.mark.parametrize("name", [n for n, s in MATRIX.items() if "train_duration_days" in s])
def test_the_duration_is_the_train_candidate_s(results, name):
    r = results[name]
    record = r["record"]
    # the refit is plan_round's last finalize_candidate call (search_period calls it too, first;
    # corrected after the first run of these tests, whose spy read the search's call)
    refit = r["calls"]["finalize_candidate"][-1]
    assert record["train_duration_days"] == refit.duration
    metrics = _round_of(r["outcome"], r["case"].hidden_year).metrics
    if "train_candidate" in metrics:
        assert record["train_duration_days"] == metrics["train_candidate"]["duration"]


@pytest.mark.parametrize("name", ["too_few_times"])
def test_the_transit_time_count_at_a_too_few_times_stop(results, name):
    r = results[name]
    assert r["record"]["n_transit_times"] == len(r["calls"]["corrected_transit_times"][0].times)
    assert f"only {r['record']['n_transit_times']} train transit times" in r["record"]["reason"]


# --- AC1: the formulas, piecewise ---------------------------------------------------------------


@pytest.mark.parametrize("name", ["measured_white", "measured_ar1", "decision_2_failed"])
def test_s_pred_follows_the_formulas_where_they_apply(results, name):
    rec = results[name]["record"]
    n = rec["n_pred"]
    assert n > 0 and all(math.isfinite(v) and v >= 0 for v in rec["train_var_rep"])
    e1 = rec["m_beta"] * math.sqrt(max(rec["train_var_rep"]) / n)
    e2 = math.sqrt(max(rec["hidden_var_rep"]) / n)
    assert rec["e_pred_1"] == pytest.approx(e1, rel=1e-12)
    assert rec["e_pred_2"] == pytest.approx(e2, rel=1e-12)
    assert rec["s_pred_1"] == pytest.approx(rec["d_c"] / e1, rel=1e-12)
    assert rec["s_pred_2"] == pytest.approx(rec["d_c"] / e2, rel=1e-12)


def _with_train_variances(transform):
    """The measured white case with the train replica variances replaced by ``transform``."""
    case = next(c for c in ic.cases() if c.name == "measured_white")
    original = holdout.train_replica_stats

    def patched(*a, **k):
        counts, variances = original(*a, **k)
        return counts, transform(list(variances))

    holdout.train_replica_stats = patched
    try:
        return holdout.calibration_measurement(
            case.lc, case.sectors, case.hidden_year, case.plan, identity=ic.identity(case.plan)
        )
    finally:
        holdout.train_replica_stats = original


@pytest.mark.parametrize(
    "transform",
    [
        lambda v: [float("nan")] + v[1:],
        lambda v: [-1.0] + v[1:],
        lambda v: [float("inf")] + v[1:],
    ],
    ids=["nan", "negative", "inf"],
)
def test_an_invalid_variance_gives_nan_as_today(transform):
    rec = _with_train_variances(transform)
    assert math.isnan(rec["e_pred_1"]) and math.isnan(rec["s_pred_1"])
    assert rec["decision_1"] == "insufficient_capacity_train"


def test_all_zero_variances_give_a_zero_error_and_a_nan_snr():
    rec = _with_train_variances(lambda v: [0.0] * len(v))
    assert rec["e_pred_1"] == 0.0
    assert math.isnan(rec["s_pred_1"])


def _with_hidden_variances(transform):
    """The measured white case with the hidden replica variances replaced by ``transform`` (the
    hidden branches of AC1, added after Codex's review of the round)."""
    import dataclasses

    case = next(c for c in ic.cases() if c.name == "measured_white")
    original = holdout.replica_stats

    def patched(*a, **k):
        stats = original(*a, **k)
        values = transform([p.var_rep for p in stats.per_dp])
        per_dp = [
            dataclasses.replace(p, var_rep=v) for p, v in zip(stats.per_dp, values, strict=True)
        ]
        return dataclasses.replace(stats, per_dp=per_dp)

    holdout.replica_stats = patched
    try:
        return holdout.calibration_measurement(
            case.lc, case.sectors, case.hidden_year, case.plan, identity=ic.identity(case.plan)
        )
    finally:
        holdout.replica_stats = original


@pytest.mark.parametrize(
    "transform",
    [
        lambda v: [float("nan")] + v[1:],
        lambda v: [-1.0] + v[1:],
        lambda v: [float("inf")] + v[1:],
    ],
    ids=["nan", "negative", "inf"],
)
def test_an_invalid_hidden_variance_gives_nan_as_today(transform):
    rec = _with_hidden_variances(transform)
    assert math.isnan(rec["e_pred_2"]) and math.isnan(rec["s_pred_2"])
    assert rec["decision_2"] == "insufficient_capacity_hidden_noise"
    assert rec["hidden_var_rep"] is not None


def test_all_zero_hidden_variances_give_a_zero_error_and_a_nan_snr():
    rec = _with_hidden_variances(lambda v: [0.0] * len(v))
    assert rec["e_pred_2"] == 0.0
    assert math.isnan(rec["s_pred_2"])
    assert rec["decision_2"] == "insufficient_capacity_hidden_noise"


# --- AC3: the decisions, from the fields, at the threshold and its neighbours --------------------


@pytest.mark.parametrize("step", ["exact", "up", "down"])
def test_decision_1_recomputed_from_the_fields_at_the_threshold(results, step):
    case = results["measured_white"]["case"]
    s1 = results["measured_white"]["record"]["s_pred_1"]
    threshold = {
        "exact": s1,
        "up": math.nextafter(s1, math.inf),
        "down": math.nextafter(s1, -math.inf),
    }[step]
    original = holdout.capacity_threshold
    holdout.capacity_threshold = lambda *a, **k: threshold
    try:
        rec = holdout.calibration_measurement(
            case.lc, case.sectors, case.hidden_year, case.plan, identity=ic.identity(case.plan)
        )
    finally:
        holdout.capacity_threshold = original
    recomputed = "pass" if rec["s_pred_1"] >= rec["threshold"] else "insufficient_capacity_train"
    assert rec["decision_1"] == recomputed
    assert rec["decision_1"] == ("insufficient_capacity_train" if step == "up" else "pass")


@pytest.mark.parametrize("step", ["exact", "up", "down"])
def test_decision_2_recomputed_from_the_fields_at_the_threshold(results, step):
    """The boundary of decision 2 (added after Codex's review of the round); the calibration
    measurement computes decision 2 whatever decision 1 gave."""
    case = results["measured_white"]["case"]
    s2 = results["measured_white"]["record"]["s_pred_2"]
    threshold = {
        "exact": s2,
        "up": math.nextafter(s2, math.inf),
        "down": math.nextafter(s2, -math.inf),
    }[step]
    original = holdout.capacity_threshold
    holdout.capacity_threshold = lambda *a, **k: threshold
    try:
        rec = holdout.calibration_measurement(
            case.lc, case.sectors, case.hidden_year, case.plan, identity=ic.identity(case.plan)
        )
    finally:
        holdout.capacity_threshold = original
    assert rec["s_pred_2"] == s2
    expected = "insufficient_capacity_hidden_noise" if step == "up" else "pass"
    recomputed = (
        "pass" if rec["s_pred_2"] >= rec["threshold"] else "insufficient_capacity_hidden_noise"
    )
    assert rec["decision_2"] == recomputed == expected


@pytest.mark.parametrize("name", ["measured_white", "decision_1_failed", "decision_2_failed"])
def test_both_decisions_recomputed_from_the_fields(results, name):
    rec = results[name]["record"]
    d1 = "pass" if rec["s_pred_1"] >= rec["threshold"] else "insufficient_capacity_train"
    d2 = "pass" if rec["s_pred_2"] >= rec["threshold"] else "insufficient_capacity_hidden_noise"
    assert rec["decision_1"] == d1 and rec["decision_2"] == d2


# --- AC4 and AB: lengths and boundaries ----------------------------------------------------------


@pytest.mark.parametrize("name", sorted(MATRIX))
def test_the_lengths_agree(results, name):
    rec = results[name]["record"]
    n = None if rec["grid_dp"] is None else len(rec["grid_dp"])
    for f in ("train_n_rep", "hidden_n_rep", "train_var_rep", "hidden_var_rep"):
        if rec.get(f) is not None and n is not None:
            assert len(rec[f]) == n, (name, f)


def test_no_predicted_window_records_zero(results):
    rec = results["no_predicted_window"]["record"]
    assert rec["n_pred"] == 0 and rec["reason"] == "no_predicted_window"


def test_an_empty_grid_stops_at_the_train_replicas_with_empty_fields():
    case = next(c for c in ic.cases() if c.name == "measured_white")
    original = holdout.period_grid
    holdout.period_grid = lambda *a, **k: np.array([], dtype=float)
    try:
        rec = holdout.calibration_measurement(
            case.lc, case.sectors, case.hidden_year, case.plan, identity=ic.identity(case.plan)
        )
    finally:
        holdout.period_grid = original
    assert rec["reason"] == "train_replicas_below_r_min"
    assert rec["grid_dp"] == [] and rec["train_var_rep"] == []
    assert rec["e_pred_1"] is None


def test_a_one_sector_hidden_year_is_recorded_as_computed(results):
    rec = results["measured_ar1"]["record"]
    assert rec["hidden_var_rep"] is not None and len(rec["hidden_var_rep"]) == len(rec["grid_dp"])


def test_the_record_stays_plain_json(results):
    for r in results.values():
        json.loads(dumps_json(to_jsonable(r["record"])))


# --- AL: no leak of the evaluator's truth ---------------------------------------------------------


def test_the_engine_signatures_are_unchanged():
    assert list(inspect.signature(holdout.run_holdout).parameters) == ["raw", "sectors", "plan"]
    assert list(inspect.signature(holdout.calibration_measurement).parameters) == [
        "raw",
        "sectors",
        "hidden_year",
        "plan",
        "identity",
        "twin_model",
    ]


@pytest.fixture(scope="module")
def study():
    sys.path.insert(0, str(ROOT / "docs" / "validation" / "v0.2.1" / "population"))
    return importlib.import_module("rmin_study")


def _declared():
    return {
        "format": "refute-m4-configuration/1",
        "name": "M4-rmin-study",
        "path": "docs/validation/v0.2.1/population/m4-configurations/rmin-study.json",
        "sha256": "0" * 64,
        "block_sha256": "1" * 64,
    }


def test_the_truth_cannot_be_read_during_an_engine_call(study):
    truth = study.EvaluatorTruth({"depth": 0.001, "s": 1.0})
    assert truth["depth"] == 0.001
    with study.engine_call():
        with pytest.raises(RuntimeError, match="truth"):
            truth["depth"]
        with pytest.raises(RuntimeError, match="truth"):
            dict(truth)
    assert dict(truth) == {"depth": 0.001, "s": 1.0}


def test_the_truth_is_attached_after_the_engine_calls(study, monkeypatch):
    monkeypatch.setattr(study.v3, "STATE", {"problem": None, "identity": _declared()})
    monkeypatch.setattr(study.v3, "_plan", lambda: ic.plan())
    seen = []

    def fake(raw, sectors, year, plan, *, identity, twin_model):
        seen.append(study.engine_call_active())
        return {"hidden_year": year, "calibration_only": True}

    monkeypatch.setattr(holdout, "calibration_measurement", fake)
    case = study.bs_choice_cases()[0]
    rec = study.record_target(case, study.BS_CHOICE_PREFIX, ("constant",), _declared())[0]
    assert seen and all(seen)  # every engine call ran under the guard
    assert not study.engine_call_active()
    truth = rec["truth"]
    assert truth["s"] == 1.0
    for key in ("period", "t0", "duration", "depth"):
        assert key in truth and truth[key] is not None
    json.loads(dumps_json(to_jsonable(rec)))


def test_changing_the_truth_changes_no_engine_output(study, monkeypatch):
    monkeypatch.setattr(study.v3, "STATE", {"problem": None, "identity": _declared()})
    monkeypatch.setattr(study.v3, "_plan", lambda: ic.plan())

    def fake(raw, sectors, year, plan, *, identity, twin_model):
        return {"hidden_year": year, "calibration_only": True, "flux_sum": float(np.sum(raw.flux))}

    monkeypatch.setattr(holdout, "calibration_measurement", fake)
    case = study.bs_choice_cases()[0]
    first = study.record_target(case, study.BS_CHOICE_PREFIX, ("constant",), _declared())[0]
    original = study.truth_of
    monkeypatch.setattr(study, "truth_of", lambda c, p, s: {k: 123.0 for k in original(c, p, s)})
    second = study.record_target(case, study.BS_CHOICE_PREFIX, ("constant",), _declared())[0]
    assert first["rounds"] == second["rounds"]
    assert first["truth"] != second["truth"]


# Added after Codex's review of the round: every route of the mapping's interface is guarded, an
# engine that reads the truth is caught, and AL3 holds with the real engine, not only a stub.


@pytest.mark.parametrize(
    "route",
    [
        "getitem",
        "get",
        "iter",
        "len",
        "contains",
        "dict",
        "unpack",
        "repr",
        "str",
        "copy",
        "deepcopy",
        "pickle",
        "json",
        "keys_view",
        "items_view",
        "values_view",
    ],
)
def test_every_route_of_the_truth_s_interface_is_guarded(study, route):
    import copy as copy_module
    import pickle

    truth = study.EvaluatorTruth({"depth": 0.001, "s": 1.0})
    early = {"keys_view": truth.keys(), "items_view": truth.items(), "values_view": truth.values()}
    reads = {
        "getitem": lambda: truth["depth"],
        "get": lambda: truth.get("depth"),
        "iter": lambda: list(iter(truth)),
        "len": lambda: len(truth),
        "contains": lambda: "depth" in truth,
        "dict": lambda: dict(truth),
        "unpack": lambda: {**truth},
        "repr": lambda: repr(truth),
        "str": lambda: str(truth),
        "copy": lambda: copy_module.copy(truth),
        "deepcopy": lambda: copy_module.deepcopy(truth),
        "pickle": lambda: pickle.dumps(truth),
        "json": lambda: json.dumps(truth),
        # views taken before the call and consumed during it
        # consumed by bare iteration, which does not call __len__ (S11 escaped list(), which
        # does, in the first run of the sabotages)
        "keys_view": lambda: next(iter(early["keys_view"])),
        "items_view": lambda: next(iter(early["items_view"])),
        "values_view": lambda: next(iter(early["values_view"])),
    }
    if route != "json":  # json.dumps refuses a Mapping anyway; every other route works outside
        reads[route]()
    with study.engine_call():
        with pytest.raises((RuntimeError, TypeError)) as caught:
            reads[route]()
    if route != "json":
        assert caught.type is RuntimeError and "truth" in str(caught.value)


def test_dict_s_own_methods_do_not_reach_the_truth(study):
    truth = study.EvaluatorTruth({"depth": 0.001})
    assert not isinstance(truth, dict)
    with pytest.raises(TypeError):
        dict.__getitem__(truth, "depth")


def test_an_engine_that_reads_the_truth_is_caught(study, monkeypatch):
    """A stand-in engine that obtains the truth object (as a leak would) and reads it: the read
    raises inside the engine call, and the target is not recorded."""
    monkeypatch.setattr(study.v3, "STATE", {"problem": None, "identity": _declared()})
    monkeypatch.setattr(study.v3, "_plan", lambda: ic.plan())
    made = []
    original_class = study.EvaluatorTruth

    def capture(data):
        t = original_class(data)
        made.append(t)
        return t

    monkeypatch.setattr(study, "EvaluatorTruth", capture)

    def leaky_engine(raw, sectors, year, plan, *, identity, twin_model):
        return {"hidden_year": year, "depth_read": made[-1]["depth"]}

    monkeypatch.setattr(holdout, "calibration_measurement", leaky_engine)
    case = study.bs_choice_cases()[0]
    with pytest.raises(RuntimeError, match="truth"):
        study.record_target(case, study.BS_CHOICE_PREFIX, ("constant",), _declared())
    assert not study.engine_call_active()


def test_changing_the_truth_changes_no_output_of_the_real_engine(study, monkeypatch):
    """AL3 with the real calibration_measurement (a fast plan): the records' engine fields are
    byte for byte the same whatever the truth's values."""
    monkeypatch.setattr(study.v3, "STATE", {"problem": None, "identity": _declared()})
    monkeypatch.setattr(study.v3, "_plan", lambda: ic.plan())
    monkeypatch.setattr(study, "calibration_identity", lambda: ic.identity(ic.plan()))
    case = study.bs_choice_cases()[0]
    first = study.record_target(case, study.BS_CHOICE_PREFIX, ("constant",), _declared())[0]
    original = study.truth_of
    monkeypatch.setattr(study, "truth_of", lambda c, p, s: {k: -7.0 for k in original(c, p, s)})
    second = study.record_target(case, study.BS_CHOICE_PREFIX, ("constant",), _declared())[0]
    assert dumps_json(to_jsonable(first["rounds"])) == dumps_json(to_jsonable(second["rounds"]))
    assert first["truth"] != second["truth"]
    assert first["rounds"] and all(r["calibration_only"] for r in first["rounds"])
