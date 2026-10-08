"""Tests for calibration/update_readme.py (README calibration section)."""

import importlib.util
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "update_readme", ROOT / "calibration" / "update_readme.py"
)
update_readme = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(update_readme)

START, END = update_readme.START, update_readme.END
LOCK = {
    "claim_sha256": "a" * 64,
    "code": {"sha256": "b" * 64},
    "git_commit": "c" * 40,
    "locked_at_utc": "2026-10-07T21:00:00Z",
}


def test_replace_section_is_idempotent_and_keeps_surroundings():
    text = f"# Title\n\nbefore\n{START}\nold\n{END}\nafter\n"
    once = update_readme.replace_section(text, "new body")
    assert once == f"# Title\n\nbefore\n{START}\nnew body\n{END}\nafter\n"
    assert update_readme.replace_section(once, "new body") == once


@pytest.mark.parametrize(
    "text",
    ["no markers", f"{START}\n{START}\n{END}", f"{END}\nx\n{START}", f"{START} only"],
)
def test_bad_markers_are_rejected(text):
    with pytest.raises(update_readme.MarkerError):
        update_readme.replace_section(text, "body")


def test_render_pending():
    body = update_readme.render(
        {"stage": "pending", "claim_sha256": "d" * 64, "targets_note": "10 planets"}
    )
    assert "lock pending" in body
    assert "d" * 64 in body


def test_render_locked_shows_hashes_and_commit_link():
    body = update_readme.render(
        {
            "stage": "locked",
            "lock": LOCK,
            "verify_status": "PASS",
            "repo_url": "https://github.com/example/refute",
        }
    )
    assert "locked, not yet run" in body
    assert "a" * 64 in body and "b" * 64 in body
    assert f"https://github.com/example/refute/commit/{'c' * 40}" in body
    assert "WARNING" not in body


def test_render_warns_when_verify_does_not_pass():
    body = update_readme.render(
        {"stage": "locked", "lock": LOCK, "verify_status": "TAMPERED", "repo_url": None}
    )
    assert "[!WARNING]" in body and "TAMPERED" in body


def test_render_points_to_the_locked_code_when_a_ref_has_it():
    body = update_readme.render(
        {
            "stage": "locked",
            "lock": LOCK,
            "verify_status": "TAMPERED",
            "repo_url": "https://github.com/example/refute",
            "locked_code_ref": {"ref": "v0.1.0", "is_tag": True},
        }
    )
    assert "[!WARNING]" not in body and "[!NOTE]" in body
    assert "TAMPERED on this branch" in body
    assert "https://github.com/example/refute/tree/v0.1.0" in body
    assert "> git checkout v0.1.0" in body
    assert "PASS" not in body


def _git(cwd, *args):
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=refute-test",
            "-c",
            "user.email=refute-test@example.invalid",
            "-c",
            "commit.gpgsign=false",
            "-c",
            "tag.gpgsign=false",
            *args,
        ],
        cwd=cwd,
        check=True,
        capture_output=True,
    )


@pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")
def test_code_hash_at_ref_equals_the_working_tree_hash(tmp_path):
    from refute.core.codehash import compute_code_hash

    (tmp_path / "src" / "refute").mkdir(parents=True)
    (tmp_path / "src" / "refute" / "__init__.py").write_bytes(b'__version__ = "0"\n')
    (tmp_path / "pyproject.toml").write_bytes(b"[project]\nname = 'x'\n")
    (tmp_path / "uv.lock").write_bytes(b"version = 1\n")
    (tmp_path / "notes.md").write_bytes(b"not part of the code hash\n")
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "init")
    _git(tmp_path, "tag", "v9.9.9")
    expected = compute_code_hash(tmp_path).sha256

    assert update_readme.code_hash_at_ref(tmp_path, "v9.9.9") == expected
    assert update_readme.code_hash_at_ref(tmp_path, "no-such-ref") is None
    found = update_readme.find_locked_code_ref(tmp_path, expected, [])
    assert found == {"ref": "v9.9.9", "is_tag": True}
    assert update_readme.find_locked_code_ref(tmp_path, "0" * 64, []) is None


def test_render_results_copies_the_outcome_whatever_it_is():
    summary = {
        "self_claim": {
            "result": "FAIL",
            "note": "at least one criterion failed",
            "criteria": [
                {
                    "criterion": "flagged false positives",
                    "value": 1,
                    "of": 3,
                    "requirement": ">= 2",
                    "passed": False,
                }
            ],
        },
        "run": {"run_id": "r1", "run_git_commit": "e" * 40, "finished_utc": "2026-10-08"},
    }
    body = update_readme.render(
        {
            "stage": "results",
            "lock": LOCK,
            "verify_status": "PASS",
            "repo_url": None,
            "summary": summary,
            "summary_md": "calibration/results/r1/summary.md",
            "runs_md": "calibration/results/r1/RUNS.md",
            "postmortem": "calibration/POSTMORTEM.md",
        }
    )
    assert "Self-claim result: FAIL" in body
    assert "| flagged false positives | 1 of 3 | >= 2 | no |" in body
    assert "[run log](calibration/results/r1/RUNS.md)" in body
    assert "post-mortem" in body


def test_readme_contains_the_markers_exactly_once():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert text.count(START) == 1 and text.count(END) == 1
    assert text.index(START) < text.index(END)
