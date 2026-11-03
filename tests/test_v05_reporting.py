"""v0.5 WP6: reporting and exporter (docs/plans/v0.5-acceptance.md, cases 6.1 to 6.12)."""

from __future__ import annotations

import json

import pytest

from refute.packs.tess.discover.steps import published_period_v05
from refute.packs.tess.exporter import BLS_METHOD, SHEET_V05, CandidateParameterExporter, _fields
from refute.packs.tess.params import PublishedParams, TessTestPlan
from refute.packs.tess.pipeline import analyze_data, build_result, duration_record
from refute.packs.tess.report import render_report
from refute.packs.tess.synthetic import discovery_plan_dict, discovery_v05_plan_dict, scenario_data

TARGET = {"key": "TIC-1", "tic_id": 1, "kind": "exploration", "name": "synthetic", "published": {}}
CONTEXT = {"claim_id": "synthetic", "claim_kind": "discover", "hypothesis": "h"}


def _result(plan_dict):
    data = scenario_data("planet_three_years")
    plan = TessTestPlan.model_validate(plan_dict)
    analysis = analyze_data(data, plan, stage=1)
    result = build_result(TARGET, data, plan, analysis, CONTEXT)
    result["duration_estimate"] = duration_record(analysis, plan)
    return result


@pytest.fixture(scope="module")
def v05():
    return _result(discovery_v05_plan_dict())


@pytest.fixture(scope="module")
def v04():
    return _result(discovery_plan_dict())


def test_6_1_the_duration_is_labelled_with_the_method_of_its_value(v05, tmp_path):
    fields = _fields(v05)
    assert fields["sheet_version"] == SHEET_V05
    assert fields["duration_method"] == BLS_METHOD
    assert fields["duration_fit"]["accepted"] is False
    CandidateParameterExporter().export(v05, tmp_path)
    md = (tmp_path / "candidate_parameters.md").read_text(encoding="utf-8")
    assert "not estimable" not in md
    assert "not reported (trapezoid fit not accepted" in md


def test_6_2_period_error_and_epoch_come_from_one_fit(v05):
    fields = _fields(v05)
    eph = v05["global_ephemeris"]
    assert fields["period_days"] == eph["period"]
    assert fields["period_err_days"] == eph["period_err"]
    assert fields["epoch_bjd_tdb"] == eph["t_ref_bjd"]
    assert "one fit" in fields["period_epoch_source"]


def test_6_3_the_sde_is_labelled_not_claimed_for_the_kept_peak(v05):
    # case 6.3 asks for the SDE of the kept peak; this search does not compute it, so the
    # field is labelled for what it is (recorded as not met as written; #186 stays open)
    assert "not the SDE of the kept peak" in v05["v05"]["sde_note"]
    assert "not the SDE of the kept peak" in _fields(v05)["sde_note"]


def test_6_4_diagnostic_tests_are_labelled_diagnostic(v05):
    text = render_report(v05, CONTEXT)
    row = next(line for line in text.splitlines() if line.startswith("| holdout_by_year |"))
    assert "| diagnostic |" in row


def test_6_8_epochs_are_printed_at_full_precision(v05):
    text = render_report(v05, CONTEXT)
    row = next(line for line in text.splitlines() if line.startswith("| Epoch (BJD_TDB) |"))
    assert "e+06" not in row
    assert f"{v05['candidate']['t0_bjd']:.6f}" in row


def test_6_9_each_holdout_round_says_whether_it_tests_the_candidate(v05):
    rounds = v05["v05"]["holdout_rounds"]
    assert rounds and all("train_matches_candidate" in r for r in rounds)
    assert all("depth_consistency_sigma" in r for r in rounds)
    text = render_report(v05, CONTEXT)
    assert "Train ephemeris matches the candidate" in text


def test_6_10_the_cadences_used_per_sector(v05):
    sectors = v05["v05"]["cadences_per_sector"]
    assert sectors
    for row in sectors.values():
        assert 0 < row["fraction_used"] <= 1.0 + 1e-9
    assert "### Cadences used per sector" in render_report(v05, CONTEXT)


def test_4_9_the_blend_caveat_is_in_the_report(v05):
    assert "does not exclude unresolved blends" in render_report(v05, CONTEXT)


def test_6_11_a_control_keeps_its_catalogued_period_uncertainty():
    row = {"pl_orbper": "3.2", "pl_orbpererr1": "0.00002"}
    published, note = published_period_v05("NASA Exoplanet Archive pscomppars", row)
    assert published == {"period_days": 3.2, "period_err_days": 2e-05}
    assert "pl_orbpererr1" in note
    PublishedParams.model_validate(published)  # fits the targets schema
    assert published_period_v05("unknown catalog", row) == ({}, None)


def test_6_12_an_earlier_claim_keeps_its_records(v04, tmp_path):
    assert "v05" not in v04
    fields = _fields(v04)
    assert "sheet_version" not in fields and "sde_note" not in fields
    assert fields["duration_err_hours"] is None
    CandidateParameterExporter().export(v04, tmp_path)
    md = (tmp_path / "candidate_parameters.md").read_text(encoding="utf-8")
    assert "not reported (trapezoid" not in md
    text = render_report(v04, CONTEXT)
    assert "## v0.5 rules" not in text
    assert "Train ephemeris matches" not in text
    json.dumps(v04, allow_nan=True)
