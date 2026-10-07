"""Tests for calibration/update_readme.py (README calibration section)."""

import importlib.util
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
            "postmortem": "calibration/POSTMORTEM.md",
        }
    )
    assert "Self-claim result: FAIL" in body
    assert "| flagged false positives | 1 of 3 | >= 2 | no |" in body
    assert "post-mortem" in body


def test_readme_contains_the_markers_exactly_once():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert text.count(START) == 1 and text.count(END) == 1
    assert text.index(START) < text.index(END)
