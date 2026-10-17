"""The pure parts of calibration/v0.3/pilot/select_pilot.py, offline (no drand, no arXiv,
no GitHub)."""

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "select_pilot", ROOT / "calibration" / "v0.3" / "pilot" / "select_pilot.py"
)
pilot = importlib.util.module_from_spec(_spec)
sys.modules["select_pilot"] = pilot
_spec.loader.exec_module(pilot)

ATOM = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/2401.01234v3</id>
    <title>A  Synthetic
      Title</title>
    <summary>An abstract about {topic}.</summary>
    <arxiv:primary_category term="{category}" scheme="http://arxiv.org/schemas/atom"/>
  </entry>
</feed>"""


def entry(category="cs.LG", topic="optimizers"):
    return ATOM.replace("{category}", category).replace("{topic}", topic)


def candidate(category="cs.LG", topic="optimizers", **repo):
    meta = pilot.parse_arxiv_entry(entry(category, topic), "2401.01234")
    base = {"host": "github", "exists": True, "archived": False}
    return {"arxiv": meta, "repository": base | repo}


def test_the_arxiv_answer_is_read():
    meta = pilot.parse_arxiv_entry(entry(), "2401.01234")
    assert meta == {
        "versioned_id": "2401.01234v3",
        "primary_category": "cs.LG",
        "title": "A Synthetic Title",
        "abstract": "An abstract about optimizers.",
    }


@pytest.mark.parametrize("other", ["2401.09999", "2312.01234"])
def test_an_answer_for_another_paper_is_refused(other):
    with pytest.raises(pilot.PilotError, match="the arXiv answer is for"):
        pilot.parse_arxiv_entry(entry(), other)


def test_an_answer_without_one_entry_is_refused():
    with pytest.raises(pilot.PilotError, match="0 entries"):
        pilot.parse_arxiv_entry('<feed xmlns="http://www.w3.org/2005/Atom"/>', "2401.01234")


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://github.com/owner/repo", ("owner", "repo")),
        ("https://github.com/owner/repo.git", ("owner", "repo")),
        ("https://github.com/owner/repo/", ("owner", "repo")),
        ("https://gitlab.com/owner/repo", None),
        ("https://github.com/owner/repo/tree/main", None),
    ],
)
def test_github_repository_urls(url, expected):
    assert pilot.github_repo(url) == expected


@pytest.mark.parametrize(
    ("kwargs", "reason"),
    [
        ({"category": "cs.CV"}, "category_outside_list"),
        ({"topic": "clinical diagnosis"}, "out_of_scope"),
        ({"exists": False}, "repository_unavailable"),
        ({"archived": True}, "repository_unavailable"),
        ({}, None),
        ({"category": "stat.ML", "topic": "molecularly"}, None),
    ],
)
def test_mechanical_rejections(kwargs, reason):
    repo = {k: v for k, v in kwargs.items() if k in ("exists", "archived")}
    rest = {k: v for k, v in kwargs.items() if k not in repo}
    assert pilot.mechanical(candidate(**rest, **repo))[0] == reason


def test_the_draw_is_deterministic_and_excludes():
    rows = [{"paper_arxiv_id": f"2401.{i:05d}"} for i in range(60)]
    first = pilot.draw_ids(rows, 12345, set())
    assert first == pilot.draw_ids(list(reversed(rows)), 12345, set())
    assert len(first) == pilot.PILOT_SIZE
    again = pilot.draw_ids(rows, 12345, {r["paper_arxiv_id"] for r in first})
    assert len(again) == pilot.PILOT_SIZE
    assert not {r["paper_arxiv_id"] for r in again} & {r["paper_arxiv_id"] for r in first}


def test_the_protocol_states_the_script_constants():
    text = (ROOT / "calibration" / "v0.3" / "pilot" / "PROTOCOL.md").read_text(encoding="utf-8")
    for value in (
        str(pilot.PILOT_ROUND),
        pilot.FRAME_SHA256,
        pilot.FRAME_REVISION,
        "**3 attempts in total**",
        "**15-second**",
        pilot.ADDITIONAL_NEEDED,
    ):
        assert value in text, value
    for keyword in pilot.KEYWORDS:
        assert f"`{keyword}`" in text, keyword
    for path in pilot.PROTOCOL_FILES:
        assert f"`{path.rsplit('/', 1)[-1]}`" in text or f"`{path}`" in text, path


def test_the_additional_round_is_the_first_one_an_hour_after_the_push():
    # 2026-10-17T22:00:00Z is round 6561446; a push at 20:59:45 needs a round at or after
    # 21:59:45, which is 22:00:00
    assert pilot.round_after("2026-10-17T20:59:45Z") == 6561446
    assert pilot.round_after("2026-10-17T21:00:00Z") == 6561446
    assert pilot.round_after("2026-10-17T21:00:01Z") == 6561447


def test_only_the_first_commit_that_records_the_need_fixes_the_additional_round():
    """Codex review of the pilot protocol: a later commit that keeps the same triage record
    must not give another round."""
    need = f"Triage approved.\n{pilot.ADDITIONAL_NEEDED}\n"
    files = {"c1": None, "c2": "Triage in progress.\n", "c3": need, "c4": need}
    assert pilot.first_with_need(["c1", "c2", "c3", "c4"], files.get) == "c3"
    assert pilot.first_with_need(["c1", "c2"], files.get) is None


def test_the_draw_files_are_created_exclusively(tmp_path):
    target = tmp_path / "pilot_draw.json"
    pilot._write_new(target, "first")
    with pytest.raises(FileExistsError):
        pilot._write_new(target, "second")
    assert target.read_text(encoding="utf-8") == "first"
