import pytest

from conftest import (
    calibration_claim,
    replicate_claim,
    target_entry,
    targets_file,
    write_yaml,
)
from refute.core.claim import ClaimError, load_claim


def test_defaults_are_resolved_into_the_locked_form(tmp_path):
    claim = write_yaml(tmp_path / "c.yaml", replicate_claim([target_entry(1, "planet", 3.7)]))
    loaded = load_claim(claim)
    plan = loaded.claim.test_plan
    assert plan["gauntlet"]["snr"]["min_snr"] == 7.1
    assert plan["gauntlet"]["odd_even"]["max_sigma"] == 3.0
    assert plan["gauntlet"]["secondary_eclipse"]["fatal_depth_ratio"] == 0.1
    assert plan["gauntlet"]["plausibility"]["max_companion_radius_rjup"] == 2.5
    assert plan["gauntlet"]["plausibility"]["max_stellar_radius_rel_err"] == 0.3
    assert plan["gauntlet"]["holdout_by_year"]["min_snr"] == 5.0
    assert plan["data"] == {
        "mission": "TESS",
        "author": "SPOC",
        "exptime_seconds": 120,
        "flux_column": "pdcsap_flux",
        "quality_bitmask": "default",
    }
    assert plan["search"]["period_max_days"] == 6.0  # explicit value from the claim
    assert loaded.canonical()["created"] == "2026-10-07"


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda c: c.update(unknown_field=1), "unknown_field"),
        (lambda c: c.update(kind="discover"), "kind"),
        (lambda c: c["test_plan"].update(gauntlet={"snr": {"min_snr": "high"}}), "min_snr"),
        (lambda c: c["test_plan"].update(gauntlet={"snr": {"min_sn": 7}}), "min_sn"),
        (lambda c: c.update(attachments=[{"path": "../secret.txt"}]), ".."),
        (lambda c: c.update(pass_criteria={"period_tolerance": 0.001}), "pass_criteria"),
        (lambda c: c.update(targets=[]), "at least one target"),
        (lambda c: c.update(pack="nope"), "unknown domain pack"),
    ],
)
def test_invalid_claims_are_rejected_with_the_field_path(tmp_path, mutate, message):
    data = replicate_claim([target_entry(1, "planet", 3.7)])
    mutate(data)
    claim = write_yaml(tmp_path / "c.yaml", data)
    with pytest.raises(ClaimError, match=message):
        load_claim(claim)


def test_target_key_must_match_tic(tmp_path):
    target = target_entry(1, "planet", 3.7)
    target["key"] = "TIC-2"
    claim = write_yaml(tmp_path / "c.yaml", replicate_claim([target]))
    with pytest.raises(ClaimError, match="does not match"):
        load_claim(claim)


def test_calibration_requires_pass_criteria_and_matching_population(tmp_path):
    write_yaml(
        tmp_path / "targets.yaml",
        targets_file([target_entry(1, "planet", 3.7), target_entry(2, "false_positive", 1.6)]),
    )
    data = calibration_claim(1, 1)
    claim = write_yaml(tmp_path / "c.yaml", data)
    assert load_claim(claim).claim.pass_criteria["max_refuted_planets"] == 0

    data_missing = dict(data)
    data_missing.pop("pass_criteria")
    write_yaml(claim, data_missing)
    with pytest.raises(ClaimError, match="pass_criteria"):
        load_claim(claim)

    write_yaml(claim, calibration_claim(2, 1))
    with pytest.raises(ClaimError, match="1 planets"):
        load_claim(claim)

    bad = calibration_claim(1, 1)
    bad["pass_criteria"]["min_recovered_planets"] = 5
    write_yaml(claim, bad)
    with pytest.raises(ClaimError, match="cannot exceed"):
        load_claim(claim)
