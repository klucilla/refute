"""Reviewer reports attached to dossiers (WP4): stored, linked, tamper-evident."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from refute.cli import app
from refute.core.dossier import check_dossier, write_manifest
from refute.core.review import ReviewError, attach_review, verify_reviews


def _dossier(tmp_path: Path) -> Path:
    root = tmp_path / "TIC-1"
    (root / "data").mkdir(parents=True)
    (root / "verdict.json").write_text(json.dumps({"verdict": "SURVIVED"}), encoding="utf-8")
    (root / "report.md").write_text("# report\n", encoding="utf-8")
    (root / "data" / "manifest.json").write_text('{"files": []}', encoding="utf-8")
    write_manifest(root)
    return root


def _report(tmp_path: Path, text: str = "No objection found.\n") -> Path:
    path = tmp_path / "review.md"
    path.write_text(text, encoding="utf-8")
    return path


def test_attach_stores_links_and_keeps_the_dossier_intact(tmp_path):
    root = _dossier(tmp_path)
    entry = attach_review(root, _report(tmp_path), reviewer="opus-1", model="claude-opus-5-5")
    assert (root / "review" / "opus-1.md").is_file()
    index = json.loads((root / "review" / "index.json").read_text(encoding="utf-8"))
    assert index["reviews"][0]["sha256"] == entry["sha256"]
    assert "opus-1.md" in (root / "review" / "index.md").read_text(encoding="utf-8")
    assert verify_reviews(root) == []
    assert check_dossier(root).ok


def test_changing_the_verdict_after_review_is_detected(tmp_path):
    root = _dossier(tmp_path)
    attach_review(root, _report(tmp_path), reviewer="opus-1", model="m")
    (root / "verdict.json").write_text(json.dumps({"verdict": "REFUTED"}), encoding="utf-8")
    write_manifest(root)  # even with a rewritten manifest
    problems = verify_reviews(root)
    assert any("verdict.json changed" in p for p in problems)
    assert any("analysis files changed" in p for p in problems)
    assert not check_dossier(root).ok


def test_editing_a_report_is_detected(tmp_path):
    root = _dossier(tmp_path)
    attach_review(root, _report(tmp_path), reviewer="opus-1", model="m")
    (root / "review" / "opus-1.md").write_text("edited\n", encoding="utf-8")
    assert any("modified" in p for p in check_dossier(root).integrity_problems)


def test_second_reviewer_and_refusals(tmp_path):
    root = _dossier(tmp_path)
    attach_review(root, _report(tmp_path), reviewer="opus-1", model="m")
    attach_review(root, _report(tmp_path, "Objection: ...\n"), reviewer="codex-1", model="x")
    assert verify_reviews(root) == []
    with pytest.raises(ReviewError, match="already attached"):
        attach_review(root, _report(tmp_path), reviewer="opus-1", model="m")
    with pytest.raises(ReviewError, match="reviewer id"):
        attach_review(root, _report(tmp_path), reviewer="../x", model="m")
    (root / "report.md").write_text("tampered\n", encoding="utf-8")
    with pytest.raises(ReviewError, match="not intact"):
        attach_review(root, _report(tmp_path), reviewer="opus-2", model="m")


def test_cli_review_attach(tmp_path):
    root = _dossier(tmp_path)
    args = ["review", "attach", str(root), str(_report(tmp_path))]
    result = CliRunner().invoke(app, [*args, "--reviewer", "opus-1", "--model", "m"])
    assert result.exit_code == 0, result.output
    again = CliRunner().invoke(app, [*args, "--reviewer", "opus-1", "--model", "m"])
    assert again.exit_code == 1
