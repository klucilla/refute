"""Issue #59: two paths where `refute verify` raised instead of returning a result. A lock
file whose JSON holds an integer beyond Python's conversion limit, and an attachment that
cannot be read, are now FAIL with the reason; TAMPERED from another component keeps its
precedence. Synthetic claims, no network."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

import refute.core.lock as lock_module
from conftest import replicate_claim, target_entry, write_yaml
from refute.core.lock import (
    LockError,
    VerifyStatus,
    code_only_note,
    create_lock,
    lock_path_for,
    read_lock,
    verify_claim,
)


def _code_root(tmp_path: Path) -> Path:
    root = tmp_path / "code"
    (root / "src" / "pkg").mkdir(parents=True)
    (root / "src" / "pkg" / "mod.py").write_text("X = 1\n", encoding="utf-8")
    (root / "pyproject.toml").write_text("[project]\nname = 'x'\n", encoding="utf-8")
    (root / "uv.lock").write_text("version = 1\n", encoding="utf-8")
    return root


def _locked(tmp_path: Path, attachments: list | None = None) -> tuple[Path, Path]:
    root = _code_root(tmp_path)
    claim = write_yaml(
        tmp_path / "claim.yaml",
        replicate_claim([target_entry(1, "planet", 3.7)], attachments=attachments or []),
    )
    create_lock(claim, code_root=root)
    return claim, root


@pytest.fixture
def int_limit():
    """Python's default limit for converting a string to an int (4,300 digits), set for
    the test and restored after it, so an environment that lifts it cannot hide the case."""
    if not hasattr(sys, "get_int_max_str_digits"):
        pytest.skip("this Python has no limit on int conversion")
    before = sys.get_int_max_str_digits()
    sys.set_int_max_str_digits(4300)
    yield 4300
    sys.set_int_max_str_digits(before)


def _with_long_integer(lock_file: Path, digits: int) -> None:
    data = json.loads(lock_file.read_text(encoding="utf-8"))
    text = json.dumps(data, indent=2)
    # an extra top-level field whose value is an integer literal of `digits` digits
    text = text.replace("{", '{\n  "padding": ' + "7" * digits + ",", 1)
    lock_file.write_text(text, encoding="utf-8")


# -- a lock file whose JSON holds an integer beyond the conversion limit -------------------


def test_a_lock_with_a_too_long_integer_is_fail_with_the_reason(tmp_path, int_limit):
    claim, root = _locked(tmp_path)
    _with_long_integer(lock_path_for(claim), int_limit + 1)
    result = verify_claim(claim, code_root=root)
    assert result.status is VerifyStatus.FAIL and result.exit_code == 1
    assert len(result.messages) == 1
    assert result.messages[0].startswith(f"cannot read lock file {lock_path_for(claim)}: ")
    assert "4300" in result.messages[0]
    assert result.lock is None
    assert code_only_note(result) is None


def test_an_integer_at_the_limit_still_reads(tmp_path, int_limit):
    # the control: exactly the limit converts, so the lock reads and verify goes on
    claim, root = _locked(tmp_path)
    _with_long_integer(lock_path_for(claim), int_limit)
    result = verify_claim(claim, code_root=root)
    assert result.status is VerifyStatus.PASS


def test_read_lock_itself_is_unchanged(tmp_path, int_limit):
    # create_lock and the other callers see the same behaviour as before: read_lock raises
    # the ValueError of json.loads (not a LockError); only verify turns it into FAIL
    claim, _root = _locked(tmp_path)
    _with_long_integer(lock_path_for(claim), int_limit + 1)
    with pytest.raises(ValueError) as caught:
        read_lock(lock_path_for(claim))
    assert not isinstance(caught.value, LockError)


def test_a_lock_nested_too_deep_is_fail_with_the_reason(tmp_path):
    # json.loads raises RecursionError on very deep nesting (Codex review of #138)
    claim, root = _locked(tmp_path)
    lock_file = lock_path_for(claim)
    depth = 100_000
    text = lock_file.read_text(encoding="utf-8")
    lock_file.write_text(
        text.replace("{", '{"padding": ' + "[" * depth + "]" * depth + ", ", 1),
        encoding="utf-8",
    )
    result = verify_claim(claim, code_root=root)
    assert result.status is VerifyStatus.FAIL and result.exit_code == 1
    assert len(result.messages) == 1
    assert result.messages[0].startswith(f"cannot read lock file {lock_file}: ")
    assert result.lock is None


def test_the_cli_reports_fail_for_the_too_long_integer(tmp_path, int_limit, monkeypatch):
    from typer.testing import CliRunner

    import refute.cli as cli

    claim, root = _locked(tmp_path)
    _with_long_integer(lock_path_for(claim), int_limit + 1)
    original = cli.verify_claim
    monkeypatch.setattr(cli, "verify_claim", lambda path: original(path, code_root=root))
    as_json = CliRunner().invoke(cli.app, ["verify", str(claim), "--json"])
    assert as_json.exit_code == 1
    data = json.loads(as_json.output)
    assert data["status"] == "FAIL" and data["exit_code"] == 1
    assert data["messages"][0].startswith("cannot read lock file ")


# -- an attachment that cannot be read ------------------------------------------------------


def _unreadable(monkeypatch, name: str) -> None:
    """Make hashing the attachment called `name` fail as a permission error would; every
    other file hashes as usual."""
    original = lock_module.sha256_text_normalized

    def fake(path):
        if Path(path).name == name:
            raise PermissionError(13, "Permission denied", str(path))
        return original(path)

    monkeypatch.setattr(lock_module, "sha256_text_normalized", fake)


def _unexaminable(monkeypatch, name: str) -> None:
    """Make examining the attachment called `name` fail as a permission error would:
    Path.stat raises, so Path.is_file raises too (it ignores only "not found" errors).
    Every other path is examined as usual."""
    original = Path.stat

    def fake(self, *args, **kwargs):
        if self.name == name:
            raise PermissionError(13, "Permission denied", str(self))
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", fake)


def test_an_attachment_that_cannot_be_examined_is_fail_with_the_reason(tmp_path, monkeypatch):
    (tmp_path / "notes.txt").write_text("notes\n", encoding="utf-8")
    claim, root = _locked(tmp_path, attachments=[{"path": "notes.txt", "role": "notes"}])
    _unexaminable(monkeypatch, "notes.txt")
    result = verify_claim(claim, code_root=root)
    assert result.status is VerifyStatus.FAIL and result.tampered == []
    reasons = [m for m in result.failures if m.startswith("cannot read attachment notes.txt: ")]
    assert len(reasons) == 1 and "Permission denied" in reasons[0]


def test_tampered_claim_keeps_precedence_over_an_attachment_that_cannot_be_examined(
    tmp_path, monkeypatch
):
    (tmp_path / "notes.txt").write_text("notes\n", encoding="utf-8")
    claim, root = _locked(tmp_path, attachments=[{"path": "notes.txt", "role": "notes"}])
    claim.write_text(claim.read_text(encoding="utf-8").replace("3.7", "3.8"), encoding="utf-8")
    _unexaminable(monkeypatch, "notes.txt")
    result = verify_claim(claim, code_root=root)
    assert result.status is VerifyStatus.TAMPERED and result.tampered == ["claim"]
    assert any(m.startswith("cannot read attachment notes.txt: ") for m in result.failures)


def test_an_unreadable_attachment_is_fail_with_the_reason(tmp_path, monkeypatch):
    (tmp_path / "notes.txt").write_text("notes\n", encoding="utf-8")
    claim, root = _locked(tmp_path, attachments=[{"path": "notes.txt", "role": "notes"}])
    _unreadable(monkeypatch, "notes.txt")
    result = verify_claim(claim, code_root=root)
    assert result.status is VerifyStatus.FAIL and result.exit_code == 1
    assert result.tampered == []
    reasons = [m for m in result.messages if m.startswith("cannot read attachment notes.txt: ")]
    assert len(reasons) == 1 and "Permission denied" in reasons[0]
    assert result.failures == reasons


def test_the_other_attachments_are_still_checked(tmp_path, monkeypatch):
    (tmp_path / "a.txt").write_text("a\n", encoding="utf-8")
    (tmp_path / "b.txt").write_text("b\n", encoding="utf-8")
    claim, root = _locked(
        tmp_path,
        attachments=[{"path": "a.txt", "role": "notes"}, {"path": "b.txt", "role": "notes"}],
    )
    _unreadable(monkeypatch, "a.txt")
    (tmp_path / "b.txt").write_text("edited\n", encoding="utf-8")
    result = verify_claim(claim, code_root=root)
    # the unreadable one is a failure, the edited one is still found: TAMPERED wins
    assert result.status is VerifyStatus.TAMPERED and result.exit_code == 2
    assert result.tampered == ["attachment:b.txt"]
    assert any(m.startswith("cannot read attachment a.txt: ") for m in result.failures)


def test_tampered_code_keeps_precedence_over_an_unreadable_attachment(tmp_path, monkeypatch):
    (tmp_path / "notes.txt").write_text("notes\n", encoding="utf-8")
    claim, root = _locked(tmp_path, attachments=[{"path": "notes.txt", "role": "notes"}])
    _unreadable(monkeypatch, "notes.txt")
    (root / "src" / "pkg" / "mod.py").write_text("X = 2\n", encoding="utf-8")
    result = verify_claim(claim, code_root=root)
    assert result.status is VerifyStatus.TAMPERED and result.tampered == ["code"]
    assert any(m.startswith("cannot read attachment notes.txt: ") for m in result.failures)
    # a FAIL-level problem next to the code: no code-only note (issue #66)
    assert code_only_note(result) is None


def test_tampered_claim_keeps_precedence_over_an_unreadable_attachment(tmp_path, monkeypatch):
    (tmp_path / "notes.txt").write_text("notes\n", encoding="utf-8")
    claim, root = _locked(tmp_path, attachments=[{"path": "notes.txt", "role": "notes"}])
    _unreadable(monkeypatch, "notes.txt")
    claim.write_text(claim.read_text(encoding="utf-8").replace("3.7", "3.8"), encoding="utf-8")
    result = verify_claim(claim, code_root=root)
    assert result.status is VerifyStatus.TAMPERED and result.tampered == ["claim"]
    assert any(m.startswith("cannot read attachment notes.txt: ") for m in result.failures)
