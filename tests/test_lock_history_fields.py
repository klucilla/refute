"""Issue #65: `refute verify` compares every field a LOCK_HISTORY.md entry shares with
its lock file, each by an explicit rule, and never skips a missing field."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from conftest import replicate_claim, target_entry, write_yaml
from refute.core.lock import (
    HISTORY_SHARED_FIELDS,
    VerifyStatus,
    _history_entry,
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
    # the literal read verify uses
    lock = read_lock(lock_path_for(claim))
    entries = [
        e
        for e in read_history(history_path_for(claim), literal=True)
        if e["claim"] == lock["claim_path"]
    ]
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


# ---- Codex review of #130, round 1 ---------------------------------------------------


def _locked(tmp_path: Path) -> tuple[Path, dict, Path, str]:
    claim = write_yaml(tmp_path / "claim.yaml", replicate_claim([target_entry(1, "planet", 3.7)]))
    lock = create_lock(claim)
    history = history_path_for(claim)
    return claim, lock, history, history.read_text(encoding="utf-8")


def test_whitespace_around_a_value_is_a_difference_through_the_parser(tmp_path):
    """The history is read literally: spaces around a value are not removed."""
    claim, lock, history, text = _locked(tmp_path)
    line = f"- refute_version: {lock['refute_version']}"
    history.write_text(text.replace(line, line + "  "), encoding="utf-8")
    result = verify_claim(claim)
    assert result.status is VerifyStatus.FAIL
    assert any("refute_version: the lock file has" in m for m in result.messages), result.messages


def test_a_field_written_twice_is_a_difference(tmp_path):
    claim, lock, history, text = _locked(tmp_path)
    line = f"- refute_version: {lock['refute_version']}"
    history.write_text(text.replace(line, line + "\n" + line), encoding="utf-8")
    result = verify_claim(claim)
    assert result.status is VerifyStatus.FAIL
    assert any("writes 'refute_version' more than once" in m for m in result.messages), (
        result.messages
    )


def test_a_bullet_repeating_the_heading_time_is_a_difference(tmp_path):
    claim, lock, history, text = _locked(tmp_path)
    line = f"- refute_version: {lock['refute_version']}"
    extra = f"- locked_at_utc: {lock['locked_at_utc']}"
    history.write_text(text.replace(line, line + "\n" + extra), encoding="utf-8")
    result = verify_claim(claim)
    assert result.status is VerifyStatus.FAIL
    assert any("writes 'locked_at_utc' more than once" in m for m in result.messages), (
        result.messages
    )


def test_two_attachment_lists_with_the_same_text_are_not_confused():
    """The collision the review found: [a=H, b=H] and the one path 'a=H, b' with H give
    the same text; a path holding ', ', '=' or a line break is a difference."""
    lock, entry = _pair(HISTORICAL[0])
    sha = "a" * 64
    two = {**lock, "attachments": [{"path": "a", "sha256": sha}, {"path": "b", "sha256": sha}]}
    one = {**lock, "attachments": [{"path": f"a={sha}, b", "sha256": sha}]}
    text = f"a={sha}, b={sha}"
    assert compare_history_entry(two, {**entry, "attachments": text}) == []
    problems = compare_history_entry(one, {**entry, "attachments": text})
    assert len(problems) == 1 and problems[0].startswith("attachments: a path"), problems
    for path in ("x=y.txt", "a, b.txt", "a\nb.txt"):
        odd = {**lock, "attachments": [{"path": path, "sha256": sha}]}
        assert [p.split(":")[0] for p in compare_history_entry(odd, entry)] == ["attachments"]


@pytest.mark.parametrize("drop", ["claim_path", "code.sha256"])
def test_a_lock_file_without_a_field_verify_reads_is_fail_not_an_error(tmp_path, drop):
    claim, lock, history, text = _locked(tmp_path)
    data = json.loads(lock_path_for(claim).read_text(encoding="utf-8"))
    if drop == "claim_path":
        del data["claim_path"]
    else:
        del data["code"]["sha256"]
    lock_path_for(claim).write_text(json.dumps(data), encoding="utf-8")
    result = verify_claim(claim)
    assert result.status is VerifyStatus.FAIL
    assert any(f"no string '{drop}'" in m for m in result.messages), result.messages


@pytest.mark.parametrize("claim", HISTORICAL, ids=["v0.1", "v0.2"])
def test_the_writer_reproduces_the_historical_entries_byte_for_byte(claim):
    """The writer now uses the comparison's rules; for both historical locks it writes
    exactly the bytes of their entries."""
    lock = read_lock(lock_path_for(claim))
    written = _history_entry(lock, action="lock", previous=None, reason="initial lock")
    # each historical history file holds one entry, the last bytes of the file
    assert history_path_for(claim).read_bytes().endswith(written.encode("utf-8"))


@pytest.mark.parametrize("line", ["- claim: other.yaml", "- reason: another reason"])
def test_a_repeated_field_that_is_not_shared_is_a_difference_too(tmp_path, line):
    claim, lock, history, text = _locked(tmp_path)
    anchor = f"- refute_version: {lock['refute_version']}"
    # the entry already has a claim (its heading) and a reason: the added line repeats one
    history.write_text(text.replace(anchor, anchor + "\n" + line), encoding="utf-8")
    result = verify_claim(claim)
    name = line[2:].split(":")[0]
    assert result.status is VerifyStatus.FAIL
    assert any(f"writes '{name}' more than once" in m for m in result.messages), result.messages


@pytest.mark.parametrize(
    "change",
    ["not a list", "path missing", "sha256 missing", "path a number", "sha256 null"],
)
def test_malformed_attachments_in_the_lock_file_are_fail_not_an_error(tmp_path, change):
    notes = tmp_path / "notes.txt"
    notes.write_text("notes\n", encoding="utf-8")
    claim = write_yaml(
        tmp_path / "claim.yaml",
        replicate_claim(
            [target_entry(1, "planet", 3.7)], attachments=[{"path": "notes.txt", "role": "notes"}]
        ),
    )
    create_lock(claim)
    data = json.loads(lock_path_for(claim).read_text(encoding="utf-8"))
    record = data["attachments"][0]
    if change == "not a list":
        data["attachments"] = "notes.txt"
    elif change == "path missing":
        del record["path"]
    elif change == "sha256 missing":
        del record["sha256"]
    elif change == "path a number":
        record["path"] = 7
    else:
        record["sha256"] = None
    lock_path_for(claim).write_text(json.dumps(data), encoding="utf-8")
    result = verify_claim(claim)
    assert result.status is VerifyStatus.FAIL
    assert any("'attachments' is not a list of objects" in m for m in result.messages), (
        result.messages
    )


def _code_root(tmp_path: Path) -> Path:
    root = tmp_path / "code"
    (root / "src" / "pkg").mkdir(parents=True)
    (root / "src" / "pkg" / "mod.py").write_text("X = 1\n", encoding="utf-8")
    (root / "pyproject.toml").write_text("[project]\nname = 'x'\n", encoding="utf-8")
    (root / "uv.lock").write_text("version = 1\n", encoding="utf-8")
    return root


@pytest.mark.parametrize(
    "files",
    [None, [{"sha256": "0" * 64}], [{"path": "src/pkg/mod.py"}], [{"path": 7, "sha256": "0"}], "x"],
    ids=["null", "no path", "no sha256", "path a number", "a string"],
)
def test_malformed_code_files_are_fail_not_an_error(tmp_path, files):
    """With the code changed, verify would compare the file lists: a malformed
    code.files is FAIL with the field named (an absent list stays allowed)."""
    root = _code_root(tmp_path)
    claim = write_yaml(tmp_path / "claim.yaml", replicate_claim([target_entry(1, "planet", 3.7)]))
    create_lock(claim, code_root=root)
    data = json.loads(lock_path_for(claim).read_text(encoding="utf-8"))
    data["code"]["files"] = files
    lock_path_for(claim).write_text(json.dumps(data), encoding="utf-8")
    (root / "src" / "pkg" / "mod.py").write_text("X = 2\n", encoding="utf-8")
    result = verify_claim(claim, code_root=root)
    assert result.status is VerifyStatus.FAIL
    assert any("'code.files' is not a list of objects" in m for m in result.messages), (
        result.messages
    )


def test_an_absent_code_files_list_is_still_allowed(tmp_path):
    root = _code_root(tmp_path)
    claim = write_yaml(tmp_path / "claim.yaml", replicate_claim([target_entry(1, "planet", 3.7)]))
    create_lock(claim, code_root=root)
    data = json.loads(lock_path_for(claim).read_text(encoding="utf-8"))
    del data["code"]["files"]
    lock_path_for(claim).write_text(json.dumps(data), encoding="utf-8")
    assert verify_claim(claim, code_root=root).status is VerifyStatus.PASS


def test_a_history_that_is_not_utf8_is_fail_not_an_error(tmp_path):
    claim, lock, history, text = _locked(tmp_path)
    history.write_bytes(text.encode("utf-8") + b"\xff\n")
    result = verify_claim(claim)
    assert result.status is VerifyStatus.FAIL
    assert any("cannot read LOCK_HISTORY.md" in m for m in result.messages), result.messages


def test_an_unreadable_history_keeps_tampered_first(tmp_path):
    """TAMPERED still takes precedence over the FAIL of an unreadable history."""
    claim, lock, history, text = _locked(tmp_path)
    history.write_bytes(b"\xff")
    claim.write_text(claim.read_text(encoding="utf-8").replace("3.7", "3.8"), encoding="utf-8")
    result = verify_claim(claim)
    assert result.status is VerifyStatus.TAMPERED
    assert any("cannot read LOCK_HISTORY.md" in m for m in result.messages), result.messages


def test_create_lock_still_reads_a_malformed_previous_lock_as_before(tmp_path):
    """read_lock is not stricter: a previous lock without claim_path still gives its
    claim_sha256 to a forced re-lock (the Codex review of #130, round 2)."""
    claim, lock, history, text = _locked(tmp_path)
    data = json.loads(lock_path_for(claim).read_text(encoding="utf-8"))
    del data["claim_path"]
    lock_path_for(claim).write_text(json.dumps(data), encoding="utf-8")
    assert read_lock(lock_path_for(claim))["claim_sha256"] == lock["claim_sha256"]
