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
    payload = {"lot": lot, "configuration": _declared(), "expected": manifest}
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


def test_the_bs_choice_evaluation_gives_k_and_a_pair_per_r(study):
    records = [_rec(i, 10.0, 10.0 + d, 10.0 + 2 * d) for i, d in enumerate((-1.0, 0.0, 1.0))]
    out = study.evaluate_bs_choice(_built_run(study, "bs-choice", records), 5.0)
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
    out = study.evaluate_bs_choice(run, 5.0)
    assert out["complete"] is False and out["problems"] and "k" not in out


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
