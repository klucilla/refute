from pathlib import Path

import pytest

from conftest import (
    calibration_claim,
    git,
    replicate_claim,
    target_entry,
    targets_file,
    write_yaml,
)
from refute.core.canonical import canonical_bytes, canonical_sha256
from refute.core.claim import load_claim
from refute.core.lock import (
    EXIT_CODES,
    LockError,
    VerifyStatus,
    create_lock,
    history_path_for,
    lock_path_for,
    read_history,
    read_lock,
    verify_claim,
)


def test_canonical_form_ignores_key_order_and_normalizes_unicode():
    a = {"b": 1, "a": [1.5, "é"], "c": {"y": None, "x": True}}
    b = {"c": {"x": True, "y": None}, "a": [1.5, "é"], "b": 1}
    assert canonical_bytes(a) == canonical_bytes(b)
    assert canonical_sha256(a) == canonical_sha256(b)
    assert canonical_sha256(a) != canonical_sha256({**a, "b": 2})


def test_canonical_form_rejects_nan():
    with pytest.raises(ValueError):
        canonical_bytes({"x": float("nan")})


def _replicate(tmp_path: Path) -> Path:
    return write_yaml(tmp_path / "claim.yaml", replicate_claim([target_entry(1, "planet", 3.7)]))


def test_comments_and_key_order_do_not_change_the_claim_hash(tmp_path):
    claim = _replicate(tmp_path)
    original = load_claim(claim).sha256()
    text = claim.read_text(encoding="utf-8")
    lines = text.splitlines()
    reordered = "# a comment\n" + "\n".join(reversed(lines[:3])) + "\n" + "\n".join(lines[3:])
    other = tmp_path / "other" / "claim.yaml"
    other.parent.mkdir()
    other.write_text(reordered + "\n", encoding="utf-8")
    assert load_claim(other).sha256() == original


def test_lock_then_verify_pass(tmp_path):
    claim = _replicate(tmp_path)
    lock = create_lock(claim)
    assert lock_path_for(claim).is_file()
    assert lock["claim_sha256"] == load_claim(claim).sha256()
    assert lock["code"]["algorithm"] == "refute-code-1"
    result = verify_claim(claim)
    assert result.status is VerifyStatus.PASS
    assert result.exit_code == 0


def test_value_edit_is_tampered_and_restore_passes(tmp_path):
    claim = _replicate(tmp_path)
    create_lock(claim)
    original = claim.read_bytes()
    claim.write_text(claim.read_text(encoding="utf-8").replace("3.7", "3.8"), encoding="utf-8")
    result = verify_claim(claim)
    assert result.status is VerifyStatus.TAMPERED
    assert result.exit_code == 2
    assert "claim" in result.tampered
    claim.write_bytes(original)
    assert verify_claim(claim).status is VerifyStatus.PASS


def test_threshold_default_change_is_tampered(tmp_path):
    claim = _replicate(tmp_path)
    create_lock(claim)
    data = replicate_claim([target_entry(1, "planet", 3.7)])
    data["test_plan"]["gauntlet"] = {"snr": {"min_snr": 7.0}}
    write_yaml(claim, data)
    assert verify_claim(claim).status is VerifyStatus.TAMPERED


def test_missing_lock_is_fail(tmp_path):
    claim = _replicate(tmp_path)
    result = verify_claim(claim)
    assert result.status is VerifyStatus.FAIL
    assert result.exit_code == EXIT_CODES[VerifyStatus.FAIL] == 1


def test_attachment_edit_is_tampered_and_missing_is_fail(tmp_path):
    notes = tmp_path / "notes.txt"
    notes.write_text("pre-registered notes\n", encoding="utf-8")
    claim = write_yaml(
        tmp_path / "claim.yaml",
        replicate_claim(
            [target_entry(1, "planet", 3.7)], attachments=[{"path": "notes.txt", "role": "notes"}]
        ),
    )
    create_lock(claim)
    notes.write_text("edited after locking\n", encoding="utf-8")
    result = verify_claim(claim)
    assert result.status is VerifyStatus.TAMPERED
    assert "attachment:notes.txt" in result.tampered
    notes.unlink()
    assert verify_claim(claim).status is VerifyStatus.FAIL


def test_attachment_hash_ignores_crlf(tmp_path):
    notes = tmp_path / "notes.txt"
    notes.write_bytes(b"line one\nline two\n")
    claim = write_yaml(
        tmp_path / "claim.yaml",
        replicate_claim([target_entry(1, "planet", 3.7)], attachments=[{"path": "notes.txt"}]),
    )
    create_lock(claim)
    notes.write_bytes(b"line one\r\nline two\r\n")
    assert verify_claim(claim).status is VerifyStatus.PASS


def test_relock_requires_force_and_reason_and_appends_history(tmp_path):
    claim = _replicate(tmp_path)
    first = create_lock(claim, now="2026-10-07T10:00:00Z")
    history = history_path_for(claim)
    before = history.read_bytes()
    with pytest.raises(LockError, match="already locked"):
        create_lock(claim)
    with pytest.raises(LockError, match="--reason"):
        create_lock(claim, force=True)
    write_yaml(
        claim,
        replicate_claim([target_entry(1, "planet", 3.7)], title="Synthetic replication v2"),
    )
    second = create_lock(claim, force=True, reason="fix title", now="2026-10-07T11:00:00Z")
    after = history.read_bytes()
    assert after.startswith(before), "earlier history entries must never be rewritten"
    entries = read_history(history)
    assert [e["action"] for e in entries] == ["lock", "relock"]
    assert entries[1]["previous_claim_sha256"] == first["claim_sha256"]
    assert entries[1]["claim_sha256"] == second["claim_sha256"]
    assert entries[1]["reason"] == "fix title"
    assert verify_claim(claim).status is VerifyStatus.PASS


def test_lock_not_latest_in_history_is_fail(tmp_path):
    claim = _replicate(tmp_path)
    create_lock(claim)
    history = history_path_for(claim)
    text = history.read_text(encoding="utf-8")
    lock = read_lock(lock_path_for(claim))
    history.write_text(text.replace(lock["claim_sha256"], "0" * 64), encoding="utf-8")
    result = verify_claim(claim)
    assert result.status is VerifyStatus.FAIL
    history.unlink()
    assert verify_claim(claim).status is VerifyStatus.FAIL


def _calibration(repo: Path) -> Path:
    write_yaml(
        repo / "calibration" / "targets.yaml",
        targets_file([target_entry(1, "planet", 3.7), target_entry(2, "false_positive", 1.6)]),
    )
    return write_yaml(repo / "calibration" / "claim.yaml", calibration_claim(1, 1))


def test_calibration_lock_refused_without_commit(git_repo):
    claim = _calibration(git_repo)
    with pytest.raises(LockError, match="at least one commit"):
        create_lock(claim)


def test_calibration_lock_refused_outside_git(tmp_path):
    claim = _calibration(tmp_path)
    with pytest.raises(LockError, match="git repository"):
        create_lock(claim)


def test_calibration_lock_requires_clean_tree_and_records_commit(git_repo):
    claim = _calibration(git_repo)
    git(git_repo, "add", "-A")
    git(git_repo, "commit", "-q", "-m", "commit A")
    commit = git(git_repo, "rev-parse", "HEAD").strip()

    (git_repo / "stray.txt").write_text("uncommitted\n", encoding="utf-8")
    with pytest.raises(LockError, match="stray.txt"):
        create_lock(claim)
    (git_repo / "stray.txt").unlink()

    (git_repo / "calibration" / "targets.yaml").write_text(
        (git_repo / "calibration" / "targets.yaml").read_text(encoding="utf-8") + "\n",
        encoding="utf-8",
    )
    with pytest.raises(LockError, match="targets.yaml"):
        create_lock(claim)
    git(git_repo, "checkout", "--", "calibration/targets.yaml")

    lock = create_lock(claim, now="2026-10-07T12:00:00Z")
    assert lock["git_commit"] == commit
    assert lock["git_dirty"] is False
    assert lock["claim_path_in_repo"] == "calibration/claim.yaml"
    # The sidecar and LOCK_HISTORY.md written by the lock itself do not count as dirty.
    relock = create_lock(claim, force=True, reason="test relock", now="2026-10-07T13:00:00Z")
    assert relock["git_dirty"] is False
    assert verify_claim(claim).status is VerifyStatus.PASS
