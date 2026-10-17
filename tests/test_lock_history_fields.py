"""Issue #65: `refute verify` compares every field a LOCK_HISTORY.md entry shares with
its lock file, each by an explicit rule, and never skips a missing field."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from conftest import replicate_claim, target_entry, write_yaml
from refute.core.lock import (
    HISTORY_SHARED_FIELDS,
    VerifyStatus,
    compare_history_entry,
    create_lock,
    history_path_for,
    lock_path_for,
    read_history,
    read_lock,
    verify_claim,
)

ROOT = Path(__file__).resolve().parents[1]
HISTORICAL = [
    ROOT / "calibration" / "self_claim.yaml",
    ROOT / "calibration" / "v0.2" / "self_claim.yaml",
]


def _pair(claim: Path) -> tuple[dict, dict]:
    lock = read_lock(lock_path_for(claim))
    entries = [e for e in read_history(history_path_for(claim)) if e["claim"] == lock["claim_path"]]
    return lock, entries[-1]


def test_the_shared_fields_are_the_ones_the_entry_writes():
    assert HISTORY_SHARED_FIELDS == (
        "locked_at_utc",
        "claim_id",
        "claim_sha256",
        "attachments",
        "code_sha256",
        "git_commit",
        "git_dirty",
        "refute_version",
    )


@pytest.mark.parametrize("claim", HISTORICAL, ids=["v0.1", "v0.2"])
def test_the_historical_locks_match_their_history_entries(claim):
    """Positive control: both historical locks match every shared field of their latest
    entry. Nothing is written: the lock and history files are only read."""
    before = {p: p.read_bytes() for p in (lock_path_for(claim), history_path_for(claim))}
    lock, entry = _pair(claim)
    assert compare_history_entry(lock, entry) == []
    assert {p: p.read_bytes() for p in before} == before


# one changed value per field, as the entry would hold it
ALTERED = {
    "locked_at_utc": "2026-10-07T21:42:16Z",
    "claim_id": "tess-calibration-v0.1-other",
    "claim_sha256": "0" * 64,
    "attachments": "targets.yaml=" + "0" * 64,
    "code_sha256": "1" * 64,
    "git_commit": "2" * 40,
    "git_dirty": "true",
    "refute_version": "0.1.1",
}


@pytest.mark.parametrize("field", HISTORY_SHARED_FIELDS)
def test_each_field_changed_alone_in_the_entry_is_one_difference(field):
    lock, entry = _pair(HISTORICAL[0])
    changed = {**entry, field: ALTERED[field]}
    problems = compare_history_entry(lock, changed)
    assert len(problems) == 1 and problems[0].startswith(f"{field}: "), problems


def test_case_and_order_are_not_normalized():
    lock, entry = _pair(HISTORICAL[1])
    upper = {**entry, "claim_sha256": entry["claim_sha256"].upper()}
    assert [p.split(":")[0] for p in compare_history_entry(lock, upper)] == ["claim_sha256"]
    parts = entry["attachments"].split(", ")
    reordered = {**entry, "attachments": ", ".join(reversed(parts))}
    assert [p.split(":")[0] for p in compare_history_entry(lock, reordered)] == ["attachments"]


@pytest.mark.parametrize("field", HISTORY_SHARED_FIELDS)
def test_a_field_missing_from_the_entry_is_a_difference(field):
    lock, entry = _pair(HISTORICAL[0])
    missing = {k: v for k, v in entry.items() if k != field}
    assert compare_history_entry(lock, missing) == [f"the history entry has no '{field}'"]


def _drop_from_lock(lock: dict, field: str) -> dict:
    lock = copy.deepcopy(lock)
    if field == "code_sha256":
        del lock["code"]["sha256"]
    else:
        del lock[field]
    return lock


@pytest.mark.parametrize("field", HISTORY_SHARED_FIELDS)
def test_a_field_missing_from_the_lock_is_a_difference(field):
    lock, entry = _pair(HISTORICAL[0])
    problems = compare_history_entry(_drop_from_lock(lock, field), entry)
    shown = "code.sha256" if field == "code_sha256" else field
    assert problems == [f"the lock file has no '{shown}'"]


@pytest.mark.parametrize("field", HISTORY_SHARED_FIELDS)
def test_a_field_missing_on_both_sides_gives_both_differences(field):
    lock, entry = _pair(HISTORICAL[0])
    shown = "code.sha256" if field == "code_sha256" else field
    missing = {k: v for k, v in entry.items() if k != field}
    assert compare_history_entry(_drop_from_lock(lock, field), missing) == [
        f"the lock file has no '{shown}'",
        f"the history entry has no '{field}'",
    ]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("git_dirty", "false"),
        ("git_dirty", 0),
        ("git_commit", 5214),
        ("claim_id", None),
        ("refute_version", 1.0),
        ("attachments", "targets.yaml"),
    ],
)
def test_a_lock_value_of_another_type_is_a_difference(field, value):
    lock, entry = _pair(HISTORICAL[0])
    problems = compare_history_entry({**lock, field: value}, entry)
    assert len(problems) == 1 and f"'{field}' in the lock file" in problems[0], problems


def test_null_and_boolean_values_are_written_as_the_entry_holds_them():
    lock, entry = _pair(HISTORICAL[0])
    lock = {**lock, "git_commit": None, "git_dirty": None, "attachments": []}
    entry = {**entry, "git_commit": "none", "git_dirty": "none", "attachments": "none"}
    assert compare_history_entry(lock, entry) == []


def test_verify_fails_naming_the_field_when_one_entry_field_was_edited(tmp_path):
    """End to end: a lock written by `refute lock`, then the history entry's
    refute_version edited: FAIL (exit 1), with the field named; restored, PASS."""
    claim = write_yaml(tmp_path / "claim.yaml", replicate_claim([target_entry(1, "planet", 3.7)]))
    lock = create_lock(claim)
    history = history_path_for(claim)
    text = history.read_text(encoding="utf-8")
    line = f"- refute_version: {lock['refute_version']}"
    assert text.count(line) == 1
    history.write_text(text.replace(line, "- refute_version: 9.9.9"), encoding="utf-8")
    result = verify_claim(claim)
    assert result.status is VerifyStatus.FAIL and result.exit_code == 1
    assert any("refute_version: the lock file has" in m for m in result.messages), result.messages
    history.write_text(text, encoding="utf-8")
    assert verify_claim(claim).status is VerifyStatus.PASS


def test_verify_fails_when_the_entry_lacks_a_field(tmp_path):
    claim = write_yaml(tmp_path / "claim.yaml", replicate_claim([target_entry(1, "planet", 3.7)]))
    create_lock(claim)
    history = history_path_for(claim)
    text = history.read_text(encoding="utf-8")
    kept = "\n".join(line for line in text.splitlines() if not line.startswith("- git_dirty: "))
    history.write_text(kept + "\n", encoding="utf-8")
    result = verify_claim(claim)
    assert result.status is VerifyStatus.FAIL
    assert any("the history entry has no 'git_dirty'" in m for m in result.messages), (
        result.messages
    )
