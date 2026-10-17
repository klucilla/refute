"""Issue #66: when the code is the only problem, the text output of `refute verify` adds
a note naming the component; the status (TAMPERED), the exit code (2) and the JSON
output do not change, and in every other case there is no note."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

import refute.cli as cli
from conftest import replicate_claim, target_entry, write_yaml
from refute.core.lock import (
    CODE_ONLY_NOTE,
    VerifyStatus,
    code_only_note,
    create_lock,
    history_path_for,
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


def _change_code(root: Path) -> None:
    (root / "src" / "pkg" / "mod.py").write_text("X = 2\n", encoding="utf-8")


def test_only_the_code_differs_gives_the_note_and_keeps_tampered(tmp_path):
    claim, root = _locked(tmp_path)
    _change_code(root)
    result = verify_claim(claim, code_root=root)
    assert result.status is VerifyStatus.TAMPERED and result.exit_code == 2
    assert result.tampered == ["code"]
    assert code_only_note(result) == CODE_ONLY_NOTE
    # the note is not a message, so the JSON output does not hold it
    assert CODE_ONLY_NOTE not in result.messages
    assert CODE_ONLY_NOTE not in json.dumps(result.to_dict())
    assert "failures" not in result.to_dict()


def test_the_note_names_the_component_and_does_not_judge_the_change():
    assert "only the code component differs" in CODE_ONLY_NOTE
    assert "it does not say whether the change is legitimate or harmless" in CODE_ONLY_NOTE
    rest = CODE_ONLY_NOTE.lower().replace("whether the change is legitimate or harmless", "")
    for word in ("legitimate", "harmless", "safe", "benign", "expected"):
        assert word not in rest, word


def test_no_note_when_nothing_differs(tmp_path):
    claim, root = _locked(tmp_path)
    result = verify_claim(claim, code_root=root)
    assert result.status is VerifyStatus.PASS
    assert code_only_note(result) is None


def test_no_note_when_the_claim_also_differs(tmp_path):
    claim, root = _locked(tmp_path)
    _change_code(root)
    claim.write_text(claim.read_text(encoding="utf-8").replace("3.7", "3.8"), encoding="utf-8")
    result = verify_claim(claim, code_root=root)
    assert result.status is VerifyStatus.TAMPERED and set(result.tampered) == {"claim", "code"}
    assert code_only_note(result) is None


def test_no_note_when_an_attachment_also_differs(tmp_path):
    (tmp_path / "notes.txt").write_text("notes\n", encoding="utf-8")
    claim, root = _locked(tmp_path, attachments=[{"path": "notes.txt", "role": "notes"}])
    _change_code(root)
    (tmp_path / "notes.txt").write_text("edited\n", encoding="utf-8")
    result = verify_claim(claim, code_root=root)
    assert result.status is VerifyStatus.TAMPERED
    assert code_only_note(result) is None


def test_no_note_when_a_fail_level_problem_is_next_to_the_code(tmp_path):
    claim, root = _locked(tmp_path)
    _change_code(root)
    history_path_for(claim).unlink()
    result = verify_claim(claim, code_root=root)
    assert result.status is VerifyStatus.TAMPERED and result.tampered == ["code"]
    assert result.failures
    assert code_only_note(result) is None


def test_the_cli_prints_the_note_in_text_only_and_keeps_exit_code_and_json(tmp_path, monkeypatch):
    claim, root = _locked(tmp_path)
    _change_code(root)
    original = cli.verify_claim
    monkeypatch.setattr(cli, "verify_claim", lambda path: original(path, code_root=root))
    runner = CliRunner()
    text = runner.invoke(cli.app, ["verify", str(claim)])
    assert text.exit_code == 2
    assert text.output.splitlines()[0] == "TAMPERED"
    assert f"  note: {CODE_ONLY_NOTE}" in text.output.splitlines()
    as_json = runner.invoke(cli.app, ["verify", str(claim), "--json"])
    assert as_json.exit_code == 2
    data = json.loads(as_json.output)
    assert data["status"] == "TAMPERED" and data["exit_code"] == 2
    assert CODE_ONLY_NOTE not in as_json.output
    assert set(data) == {
        "status",
        "exit_code",
        "claim_path",
        "messages",
        "tampered_components",
        "changed_files",
        "locked_claim_sha256",
        "locked_code_sha256",
        "current_claim_sha256",
        "current_code_sha256",
        "claim_projection",
        "projected_claim_sha256",
        "verified_at_utc",
    }


def test_the_cli_prints_no_note_when_the_claim_also_differs(tmp_path, monkeypatch):
    claim, root = _locked(tmp_path)
    _change_code(root)
    claim.write_text(claim.read_text(encoding="utf-8").replace("3.7", "3.8"), encoding="utf-8")
    original = cli.verify_claim
    monkeypatch.setattr(cli, "verify_claim", lambda path: original(path, code_root=root))
    text = CliRunner().invoke(cli.app, ["verify", str(claim)])
    assert text.exit_code == 2
    assert "note:" not in text.output
