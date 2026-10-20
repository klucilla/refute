"""The lots of the ``R_min`` study and of ``bs-choice`` (map Amendment 19; Amendments 26 and 27),
written before the code: the case lists, the manifest, and the record of one target and scenario.

Interface (declared here), in ``rmin_study.py``: ``bs_choice_cases()``; ``study_cases()`` (the
cases of each group, whole blocks of the prefixes ``refute-v0.2.1-rmin-study-<k>`` in order of
``k``); ``lot_manifest(lot)`` (the expected ``(target, scenario)`` pairs); ``record_target(case,
prefix, scenarios, expected)`` (one record per scenario, the measurement's records with the years
of the metadata); ``write_record(run_dir, record)`` (never replaces a file).
"""

import importlib
import json
import sys
import uuid
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
POPULATION = ROOT / "docs" / "validation" / "v0.2.1" / "population"


@pytest.fixture(scope="module")
def study():
    sys.path.insert(0, str(POPULATION))
    return importlib.import_module("rmin_study")


def test_bs_choice_is_every_tenth_planet_of_the_bands_near_and_measurable(study):
    cases = study.bs_choice_cases()
    assert len(cases) == 100
    assert all(c["class"] == "planet" and c["band"] in ("near", "measurable") for c in cases)
    assert all(c["index"] % 10 == 0 for c in cases)
    assert Counter(study.group_of(c) for c in cases) == {
        "white, no variability": 40,
        "white, variability": 10,
        "AR(1), no variability": 40,
        "AR(1), variability": 10,
    }


def test_the_study_is_whole_blocks_per_group(study):
    lots = study.study_cases()
    sizes = Counter(study.group_of(c) for _, c in lots)
    assert sizes == {
        "white, no variability": 6400,
        "white, variability": 6400,
        "AR(1), no variability": 6400,
        "AR(1), variability": 6400,
    }
    prefixes = Counter((study.group_of(c), p) for p, c in lots)
    by_group = Counter(g for g, _ in prefixes)
    assert by_group == {
        "white, no variability": 16,
        "white, variability": 64,
        "AR(1), no variability": 16,
        "AR(1), variability": 64,
    }
    for (group, prefix), n in prefixes.items():
        assert n == (400 if group.endswith("no variability") else 100), (group, prefix)
    expected = {f"refute-v0.2.1-rmin-study-{k}" for k in range(1, 65)}
    assert {p for p, _ in lots} == expected
    assert len({f"{p}/{c['id']}" for p, c in lots}) == len(lots) == 25600


def test_the_manifest_lists_every_target_and_scenario(study):
    manifest = study.lot_manifest("bs-choice")
    assert len(manifest) == 100 and {s for _, s in manifest} == {"constant"}
    assert all(t.startswith("refute-v0.2.1-bs-choice/") for t, _ in manifest)


def _declared():
    return {
        "format": "refute-m4-configuration/1",
        "name": "M4-rmin-study",
        "path": "docs/validation/v0.2.1/population/m4-configurations/rmin-study.json",
        "sha256": "0" * 64,
        "block_sha256": "1" * 64,
    }


def _plan(**corrections):
    from refute.packs.tess import synthetic
    from refute.packs.tess.params import TessTestPlan

    plan = synthetic.fast_plan_dict()
    plan["gauntlet"] = {"corrections": {"version": 2, "enabled": True, "r_min": 8, **corrections}}
    return TessTestPlan.model_validate(plan)


def test_a_target_is_recorded_per_scenario_and_never_replaced(study, monkeypatch):
    import refute.packs.tess.holdout as holdout

    monkeypatch.setattr(study.v3, "STATE", {"problem": None, "identity": _declared()})
    monkeypatch.setattr(study.v3, "_plan", lambda: _plan())

    def fake(raw, sectors, year, plan, *, identity, twin_model):
        assert twin_model.shape == raw.flux.shape
        return {"hidden_year": year, "calibration_only": True}

    monkeypatch.setattr(holdout, "calibration_measurement", fake)
    case = study.bs_choice_cases()[0]
    records = study.record_target(case, study.BS_CHOICE_PREFIX, ("constant",), _declared())
    assert len(records) == 1
    rec = records[0]
    assert rec["target"] == f"{study.BS_CHOICE_PREFIX}/{case['id']}"
    assert rec["scenario"] == "constant" and rec["group"] == study.group_of(case)
    assert [r["hidden_year"] for r in rec["rounds"]] == sorted(rec["years"])
    assert rec["configuration"] == _declared()
    run = ROOT / ".cache" / "test-rmin-lots" / uuid.uuid4().hex
    path = study.write_record(run, rec)
    assert json.loads(path.read_text(encoding="utf-8"))["target"] == rec["target"]
    with pytest.raises(FileExistsError):
        study.write_record(run, rec)


def _built_run(study, lot, records):
    """A run folder with the given records and their manifest (no generation)."""
    run = ROOT / ".cache" / "test-rmin-lots" / uuid.uuid4().hex
    run.mkdir(parents=True)
    manifest = [(r["target"], r["scenario"]) for r in records]
    payload = {
        "format": study.LOT_FORMAT,
        "lot": lot,
        "configuration": _declared(),
        "expected": [list(m) for m in manifest],
    }
    (run / "manifest.json").write_text(json.dumps(payload), encoding="utf-8")
    for r in records:
        study.write_record(run, r)
    return run


def _rec(i, s_pred_1, s_pred_2, s_meas, scenario="constant"):
    r = {
        "hidden_year": 2018,
        "stage": None,
        "reason": None,
        "decision_1": "pass",
        "decision_2": "pass",
        "n_years": 2,
        "train_n_rep": [30, 30, 30],
        "hidden_n_rep": [30, 30, 30],
        "hidden_noise_undetermined": False,
        "s_pred_1": s_pred_1,
        "s_pred_2": s_pred_2,
        "s_meas": s_meas,
        "d_train": 1e-3,
        "e_train": 1e-4,
        "d_hidden": 1e-3,
        "e_hidden": 1e-4,
        "dp": 0.0,
        "measurement_status": "ok",
        "d_twin": 1e-3,
        "twin_status": "ok",
    }
    return {
        "target": f"{study_prefix()}/planet-near-white-{i:04d}",
        "group": "white, no variability",
        "scenario": scenario,
        "years": [2018],
        "configuration": _declared(),
        "rounds": [r],
    }


def study_prefix():
    return "refute-v0.2.1-bs-choice"


def _expected(run):
    """The built run's own manifest, passed as the prescribed one (the built lots are small)."""
    return json.loads((run / "manifest.json").read_text(encoding="utf-8"))["expected"]


def _bs(study, run, configuration=None):
    conf = _declared() if configuration is None else configuration
    return study.evaluate_bs_choice(run, 5.0, conf, _expected(run))


def test_the_bs_choice_evaluation_gives_k_and_a_pair_per_r(study):
    records = [_rec(i, 10.0, 10.0 + d, 10.0 + 2 * d) for i, d in enumerate((-1.0, 0.0, 1.0))]
    out = _bs(study, _built_run(study, "bs-choice", records))
    assert out["complete"] is True
    assert out["k"]["k"] in (1, 2)
    assert set(out["pairs"]) == {str(r) for r in (8, 10, 12, 15, 20)}
    assert all(p is not None for p in out["pairs"].values())  # counts 30 meet every R


def test_an_incomplete_lot_is_not_evaluated(study):
    records = [_rec(i, 10.0, 10.0, 10.0) for i in range(3)]
    run = _built_run(study, "bs-choice", records)
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    manifest["expected"].append(["refute-v0.2.1-bs-choice/missing", "constant"])
    (run / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    out = _bs(study, run)
    assert out["complete"] is False and out["problems"] and "k" not in out


# --- added after the Codex review of the round (map Amendment 27's record) --------------------


def _lot_env(study, monkeypatch, fail=()):
    """The lot runner with its configuration, affinity and measurement replaced (no generation)."""
    monkeypatch.setattr(study.v3, "STATE", {"problem": None, "identity": _declared()})
    monkeypatch.setattr(study.v3, "_plan", lambda: _plan())
    monkeypatch.setattr(study.pv2, "affinity_mask", lambda: "0xff")
    calls = []

    def fake(case, prefix, scenarios, expected):
        calls.append(case["id"])
        if case["id"] in fail:
            raise RuntimeError("a worker failure")
        return [
            {
                "target": f"{prefix}/{case['id']}",
                "group": study.group_of(case),
                "scenario": sc,
                "years": [2018],
                "configuration": expected,
                "rounds": [{"hidden_year": 2018}],
            }
            for sc in scenarios
        ]

    monkeypatch.setattr(study, "record_target", fake)
    return calls


def test_a_lot_resumes_on_its_own_manifest_without_replacing(study, monkeypatch):
    calls = _lot_env(study, monkeypatch)
    run = ROOT / ".cache" / "test-rmin-lots" / uuid.uuid4().hex
    first = study.run_lot("bs-choice", run, executor=study._InlineExecutor())
    assert first["complete"] is True and first["dispatched"] == 100 and len(calls) == 100
    before = {p: p.read_bytes() for p in (run / "records").rglob("*.json")}
    second = study.run_lot("bs-choice", run, executor=study._InlineExecutor())
    assert second["dispatched"] == 0 and second["complete"] is True  # the manifest read back
    assert {p: p.read_bytes() for p in (run / "records").rglob("*.json")} == before
    assert len(list(run.glob("run-report-*.json"))) == 2


def test_a_failed_target_is_reported_and_the_lot_is_incomplete(study, monkeypatch):
    first_id = study.bs_choice_cases()[3]["id"]
    _lot_env(study, monkeypatch, fail=(first_id,))
    run = ROOT / ".cache" / "test-rmin-lots" / uuid.uuid4().hex
    report = study.run_lot("bs-choice", run, executor=study._InlineExecutor())
    assert report["complete"] is False
    assert [f["target"].split("/")[1] for f in report["failures"]] == [first_id]
    assert report["integrity_problems"]  # the missing target
    assert len(list((run / "records").rglob("*.json"))) == 99


class _BreaksOnSecondSubmit:
    """An executor whose pool breaks at the second submission (as a dead worker does)."""

    def __init__(self, study):
        self.inner = study._InlineExecutor()
        self.n = 0

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def submit(self, fn, *args):
        self.n += 1
        if self.n == 2:
            raise RuntimeError("BrokenProcessPool stand-in")
        return self.inner.submit(fn, *args)


def test_a_broken_pool_ends_with_a_report(study, monkeypatch):
    # added after the second round of the Codex review
    _lot_env(study, monkeypatch)
    run = ROOT / ".cache" / "test-rmin-lots" / uuid.uuid4().hex
    report = study.run_lot("bs-choice", run, executor=_BreaksOnSecondSubmit(study))
    assert report["complete"] is False and "submission" in report["dispatch_error"]
    assert report["submitted"] == 1 and len(report["not_submitted"]) == 99
    assert len(list(run.glob("run-report-*.json"))) == 1
    assert len(list((run / "records").rglob("*.json"))) == 1


def test_the_ceiling_stops_the_submissions(study, monkeypatch):
    """The study's own ceiling (the maintainer's decision of 2026-10-19, map Amendment 27): the run
    stops submitting targets when its elapsed time reaches the deadline; those in flight end; the
    lot is incomplete and the report says why."""
    _lot_env(study, monkeypatch)
    ticks = iter(range(10_000))
    clock = lambda: float(next(ticks)) * 3600.0  # noqa: E731 - one hour per reading
    run = ROOT / ".cache" / "test-rmin-lots" / uuid.uuid4().hex
    report = study.run_lot(
        "bs-choice", run, executor=study._InlineExecutor(), deadline_hours=5.0, clock=clock
    )
    assert report["complete"] is False and report["deadline_reached"] is True
    assert 0 < report["submitted"] < 100
    assert len(report["not_submitted"]) == 100 - report["submitted"]
    assert report["deadline_hours"] == 5.0
    run2 = ROOT / ".cache" / "test-rmin-lots" / uuid.uuid4().hex
    report = study.run_lot("bs-choice", run2, executor=study._InlineExecutor(), deadline_hours=1e6)
    assert report["complete"] is True and report["deadline_reached"] is False


def test_a_foreign_lot_or_configuration_is_not_evaluated(study):
    records = [_rec(i, 10.0, 10.0, 10.0) for i in range(3)]
    run = _built_run(study, "bs-choice", records)
    other = {**_declared(), "sha256": "2" * 64}
    assert _bs(study, run, other)["complete"] is False  # another configuration
    records = [_rec(i, 10.0, 10.0, 10.0) for i in range(3)]
    records[1]["configuration"] = other
    run = _built_run(study, "bs-choice", records)
    out = _bs(study, run)
    assert out["complete"] is False and any("another configuration" in p for p in out["problems"])
    run = _built_run(study, "study", [_rec(i, 10.0, 10.0, 10.0) for i in range(3)])
    assert _bs(study, run)["complete"] is False  # another lot


def test_the_manifest_must_be_the_lots_own(study):
    # added after the second round of the Codex review: records under the label of another lot
    records = [_rec(i, 10.0, 10.0, 10.0) for i in range(3)]
    run = _built_run(study, "bs-choice", records)
    out = study.evaluate_bs_choice(run, 5.0, _declared())  # the prescribed manifest of bs-choice
    assert out["complete"] is False
    assert any("not those of the lot" in p for p in out["problems"])


def test_the_study_refuses_pairs_of_another_source(study):
    records = [_rec(i, 10.0, 10.0 + d, 10.0 + 2 * d) for i, d in enumerate((-1.0, 0.0, 1.0))]
    bs_run = _built_run(study, "bs-choice", records)
    bs = _bs(study, bs_run)
    assert bs["source"]["lot"] == "bs-choice" and bs["source"]["records"] == 3
    run = _built_run(study, "study", [_rec(i, 10.0, 10.0, 10.0) for i in range(3)])

    def study_eval(pairs, configuration=None, min_snr=5.0):
        conf = _declared() if configuration is None else configuration
        return study.evaluate_study(
            run, pairs, bs_run, min_snr, conf, _expected(run), _expected(bs_run)
        )

    assert study_eval(bs)["complete"] is True  # the genuine pairs
    other = {**_declared(), "sha256": "2" * 64}
    assert study_eval(bs, configuration=other)["complete"] is False
    assert study_eval({**bs, "min_snr": 4.0})["complete"] is False
    assert study_eval({**bs, "source": {**bs["source"], "lot": "study"}})["complete"] is False
    stripped = {**bs, "source": {"lot": "bs-choice", "configuration": _declared()}}
    assert study_eval(stripped)["complete"] is False  # no digests
    changed = {**bs, "pairs": {**bs["pairs"], "8": {**bs["pairs"]["8"], "b": 9.0}}}
    assert study_eval(changed)["complete"] is False  # not the evaluation of bs-choice's folder


def test_another_configuration_records_nothing(study, monkeypatch):
    other = {**_declared(), "name": "M4-rmin-timing"}
    monkeypatch.setattr(study.v3, "STATE", {"problem": None, "identity": other})
    monkeypatch.setattr(study.v3, "_plan", lambda: _plan())

    def never(case):
        raise AssertionError("a case was generated")

    monkeypatch.setattr(study.pv2, "build_case", never)
    with pytest.raises(RuntimeError, match="not the study's"):
        study.record_target(
            study.bs_choice_cases()[0], study.BS_CHOICE_PREFIX, ("constant",), other
        )
