"""Historical projection of locked claims (docs/validation/v0.3/lock-compat-acceptance.md,
L1-L7 and L10; W3.5 of docs/validation/v0.3/wp3-acceptance.md). Offline: the two real
locked claims are read from the repository, the negative cases use copies in tmp_path."""

import copy
import json
import shutil
from pathlib import Path

import pytest
import yaml

from refute.core.canonical import canonical_sha256
from refute.core.claim import load_claim
from refute.core.lock import VerifyStatus, lock_path_for, read_lock, verify_claim
from refute.core.lock_compat import (
    HISTORICAL_LOCKS,
    IDENTITY_FIELDS,
    LIMIT,
    HistoricalLock,
    find_entry,
    project,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "locked_canonical"

CLAIMS = {
    "tess-calibration-v0.1": ROOT / "calibration" / "self_claim.yaml",
    "tess-calibration-v0.2": ROOT / "calibration" / "v0.2" / "self_claim.yaml",
}
# L10.2: full resolved hashes with the code of main 78822a7 (2026-10-15).
FULL_RESOLVED = {
    "tess-calibration-v0.1": "6f54b8348a90ee0d53e0ab2f45c90707c64a4286de559f61c2285b4ec1a365dc",
    "tess-calibration-v0.2": "5fe1a3de767c45e0b294073c77cf8d3c93f559bd1f94b06a6a5a98718af6d502",
}


def fixture(claim_id):
    return json.loads((FIXTURES / f"{claim_id}.json").read_text(encoding="utf-8"))


def entry_for(claim_id):
    (entry,) = [e for e in HISTORICAL_LOCKS if e.identity["claim_id"] == claim_id]
    return entry


def with_value(tree, path, value):
    out = copy.deepcopy(tree)
    node = out
    for key in path[:-1]:
        node = node.setdefault(key, {})
    node[path[-1]] = value
    return out


# L7: provenance of the table ----------------------------------------------------------


@pytest.mark.parametrize("claim_id", CLAIMS)
def test_fixture_is_the_locked_content(claim_id):
    data = fixture(claim_id)
    lock = read_lock(lock_path_for(CLAIMS[claim_id]))
    assert data["locked_claim_sha256"] == lock["claim_sha256"]
    assert data["lock_commit"] == lock["git_commit"]
    assert canonical_sha256(data["canonical"]) == lock["claim_sha256"]


@pytest.mark.parametrize("claim_id", CLAIMS)
def test_current_resolution_is_fixture_plus_exactly_the_listed_fields(claim_id):
    current = load_claim(CLAIMS[claim_id]).canonical()
    expected = fixture(claim_id)["canonical"]
    for path, value in entry_for(claim_id).added.items():
        expected = with_value(expected, path, value)
    assert current == expected


def test_every_table_entry_has_the_full_identity_and_matches_its_lock():
    for claim_id, path in CLAIMS.items():
        entry = entry_for(claim_id)
        assert set(entry.identity) == set(IDENTITY_FIELDS)
        assert find_entry(read_lock(lock_path_for(path))) is entry


# L10 / W3.5: equality with the locked hashes, and no regression of the full resolution --


@pytest.mark.parametrize("claim_id", CLAIMS)
def test_projection_with_the_new_code_equals_the_locked_hash(claim_id):
    loaded = load_claim(CLAIMS[claim_id])
    lock = read_lock(lock_path_for(CLAIMS[claim_id]))
    projection = project(loaded.canonical(), loaded.raw, lock)
    assert projection.applied
    assert projection.sha256 == lock["claim_sha256"]


@pytest.mark.parametrize("claim_id", CLAIMS)
def test_full_resolved_hash_has_not_changed(claim_id):
    assert load_claim(CLAIMS[claim_id]).sha256() == FULL_RESOLVED[claim_id]


# L5, L6: verify on the real claims in this checkout ------------------------------------


@pytest.mark.parametrize("claim_id", CLAIMS)
def test_verify_passes_the_claim_by_projection_and_stays_tampered_for_the_code(claim_id):
    result = verify_claim(CLAIMS[claim_id])
    lock = read_lock(lock_path_for(CLAIMS[claim_id]))
    assert result.status is VerifyStatus.TAMPERED  # the code differs from the lock
    assert "claim" not in result.tampered
    assert "code" in result.tampered
    assert result.claim_projection == entry_for(claim_id).name
    assert result.projected_claim_sha256 == lock["claim_sha256"]
    assert result.current_claim_sha256 == FULL_RESOLVED[claim_id]
    data = result.to_dict()
    assert data["claim_projection"] == entry_for(claim_id).name
    assert any(LIMIT in m for m in result.messages)


# Negative cases (Codex review) on copies --------------------------------------------------


def copy_v02(tmp_path):
    source = CLAIMS["tess-calibration-v0.2"].parent
    target = tmp_path / "v0.2"
    shutil.copytree(source, target, ignore=shutil.ignore_patterns("results", "audit"))
    return target / "self_claim.yaml"


def edit_claim(claim_file, change):
    data = yaml.safe_load(claim_file.read_text(encoding="utf-8"))
    change(data)
    claim_file.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def test_old_field_changed_is_tampered(tmp_path):
    claim = copy_v02(tmp_path)
    edit_claim(claim, lambda d: d["pass_criteria"].update(min_recovered_planets=8))
    result = verify_claim(claim)
    assert result.status is VerifyStatus.TAMPERED
    assert "claim" in result.tampered
    assert result.claim_projection is None


def test_new_field_written_in_the_claim_file_is_refused(tmp_path):
    claim = copy_v02(tmp_path)
    edit_claim(claim, lambda d: d["pass_criteria"].update(flag_requires_signal_recovery=False))
    result = verify_claim(claim)
    assert result.status is VerifyStatus.TAMPERED
    assert "claim" in result.tampered
    assert any("written in the claim file" in m for m in result.messages)


def test_listed_field_with_another_value_is_refused():
    loaded = load_claim(CLAIMS["tess-calibration-v0.2"])
    lock = read_lock(lock_path_for(CLAIMS["tess-calibration-v0.2"]))
    path = ("test_plan", "gauntlet", "holdout_by_year", "require_valid_train")
    changed = with_value(loaded.canonical(), path, False)  # as if a release changed it
    projection = project(changed, loaded.raw, lock)
    assert not projection.applied
    assert "differs from its frozen value" in projection.reason


@pytest.mark.parametrize("value", [1, 1.0, "true"])
def test_frozen_value_comparison_keeps_types(value):
    loaded = load_claim(CLAIMS["tess-calibration-v0.2"])
    lock = read_lock(lock_path_for(CLAIMS["tess-calibration-v0.2"]))
    path = ("test_plan", "gauntlet", "holdout_by_year", "require_valid_train")
    projection = project(with_value(loaded.canonical(), path, value), loaded.raw, lock)
    assert not projection.applied


def test_unknown_resolved_field_changes_the_projected_hash():
    loaded = load_claim(CLAIMS["tess-calibration-v0.2"])
    lock = read_lock(lock_path_for(CLAIMS["tess-calibration-v0.2"]))
    extra = with_value(loaded.canonical(), ("test_plan", "gauntlet", "new_check"), {"x": 1})
    projection = project(extra, loaded.raw, lock)
    assert projection.applied
    assert projection.sha256 != lock["claim_sha256"]


def test_listed_field_absent_is_refused():
    loaded = load_claim(CLAIMS["tess-calibration-v0.2"])
    lock = read_lock(lock_path_for(CLAIMS["tess-calibration-v0.2"]))
    canonical = copy.deepcopy(loaded.canonical())
    del canonical["pass_criteria"]["flag_requires_signal_recovery"]
    projection = project(canonical, loaded.raw, lock)
    assert not projection.applied
    assert "absent" in projection.reason


@pytest.mark.parametrize("field", IDENTITY_FIELDS)
def test_lock_differing_in_one_identity_field_gets_no_projection(field):
    lock = copy.deepcopy(read_lock(lock_path_for(CLAIMS["tess-calibration-v0.2"])))
    if field == "code_sha256":
        lock["code"]["sha256"] = "0" * 64
    else:
        lock[field] = "changed"
    assert find_entry(lock) is None
    loaded = load_claim(CLAIMS["tess-calibration-v0.2"])
    projection = project(loaded.canonical(), loaded.raw, lock)
    assert projection.entry is None and not projection.applied


def test_wrong_frozen_value_in_the_table_is_refused():
    real = entry_for("tess-calibration-v0.2")
    path = ("test_plan", "gauntlet", "holdout_by_year", "max_hidden_window_fraction")
    wrong = HistoricalLock(real.name, real.identity, {**real.added, path: 0.25})
    loaded = load_claim(CLAIMS["tess-calibration-v0.2"])
    lock = read_lock(lock_path_for(CLAIMS["tess-calibration-v0.2"]))
    projection = project(loaded.canonical(), loaded.raw, lock, table=(wrong,))
    assert not projection.applied


def test_table_missing_a_listed_field_does_not_reach_the_locked_hash():
    real = entry_for("tess-calibration-v0.2")
    short = HistoricalLock(
        real.name,
        real.identity,
        {p: v for p, v in real.added.items() if p[-1] != "require_valid_train"},
    )
    loaded = load_claim(CLAIMS["tess-calibration-v0.2"])
    lock = read_lock(lock_path_for(CLAIMS["tess-calibration-v0.2"]))
    projection = project(loaded.canonical(), loaded.raw, lock, table=(short,))
    assert projection.applied and projection.sha256 != lock["claim_sha256"]


def test_unknown_lock_is_verified_exactly_as_before(tmp_path):
    claim = copy_v02(tmp_path)
    lock_file = lock_path_for(claim)
    lock = json.loads(lock_file.read_text(encoding="utf-8"))
    lock["git_commit"] = "f" * 40  # no table entry for this identity
    lock_file.write_text(json.dumps(lock, indent=2, sort_keys=True), encoding="utf-8")
    result = verify_claim(claim)
    assert result.status is VerifyStatus.TAMPERED
    assert "claim" in result.tampered
    assert result.claim_projection is None
    assert not any("historical projection" in m for m in result.messages)
