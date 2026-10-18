"""The pure parts of the main walk (calibration/v0.3/main/select_main.py), offline."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "calibration" / "v0.3" / "main"))

import select_main as sm  # noqa: E402


def cand(category="cs.LG", title="A method", abstract="We learn.", repo=None):
    return {
        "arxiv": {"primary_category": category, "title": title, "abstract": abstract},
        "repository": repo or {"host": "github", "exists": True, "archived": False},
    }


def test_categories_include_cs_ai_after_the_adjustment():
    assert sm.mechanical(cand("cs.AI")) == (None, "")
    assert sm.mechanical(cand("stat.ML")) == (None, "")
    assert sm.mechanical(cand("cs.CV"))[0] == "category_outside_list"


def test_keywords_and_repository():
    assert sm.mechanical(cand(title="Cancer detection"))[0] == "out_of_scope"
    gone = {"host": "github", "exists": False}
    assert sm.mechanical(cand(repo=gone))[0] == "repository_unavailable"
    archived = {"host": "github", "exists": True, "archived": True}
    assert sm.mechanical(cand(repo=archived))[0] == "repository_unavailable"


def test_license_signal():
    repo = {"host": "github", "exists": True, "license_spdx": None}
    assert sm.license_signal(repo, ["README.md", "src"]) is True
    assert sm.license_signal(repo, ["README.md", "LICENSE.txt"]) is False
    assert sm.license_signal(repo, ["COPYING"]) is False
    assert sm.license_signal(repo | {"license_spdx": "MIT"}, ["README.md"]) is False
    assert sm.license_signal(repo, None) is False  # an unread root gives no signal


def test_walk_order_removes_the_pilot_papers_and_is_deterministic():
    rows = [{"paper_arxiv_id": f"2401.{i:05d}"} for i in range(50)]
    order = sm.walk_order(rows, 12345, {"2401.00003", "2401.00007"})
    ids = [r["paper_arxiv_id"] for r in order]
    assert len(ids) == 48 and "2401.00003" not in ids
    assert ids == [
        r["paper_arxiv_id"]
        for r in sm.walk_order(list(reversed(rows)), 12345, {"2401.00003", "2401.00007"})
    ]


def test_batches_and_the_stop_rule():
    assert sm.batch_slice(1) == slice(0, 25)
    assert sm.batch_slice(12) == slice(275, 300)
    assert sm.batch_slice(13) == slice(300, 325)
    # AMENDMENT-1.md: the cap is 1,200 candidates (48 batches)
    assert sm.batch_slice(48) == slice(1175, 1200)
    with pytest.raises(sm.MainError, match="stop rule"):
        sm.batch_slice(49)
    with pytest.raises(sm.MainError):
        sm.batch_slice(0)


def test_amended_batches_need_the_amendment_commit():
    sm.check_protocol_commit(12, sm.ORIGINAL_PROTOCOL)
    sm.check_protocol_commit(13, "a" * 40)
    with pytest.raises(sm.MainError, match="AMENDMENT-1"):
        sm.check_protocol_commit(13, sm.ORIGINAL_PROTOCOL)
    with pytest.raises(sm.MainError, match="AMENDMENT-1"):
        sm.check_protocol_commit(48, sm.ORIGINAL_PROTOCOL)


def test_the_protocol_commit_must_be_the_one_that_adds_the_amendment():
    a, b = "a" * 40, "b" * 40
    sm.check_amendment_commit(a, [a])
    for adding in ([], [b], [a, b], [b, a]):
        with pytest.raises(sm.MainError, match="adds calibration/v0.3/main/AMENDMENT-1.md"):
            sm.check_amendment_commit(a, adding)


def test_the_round_is_fixed_by_the_amendment():
    assert sm.PAPER_ROUND == 6561788
    assert sm.ORIGINAL_PROTOCOL == "b01bc78ccc0dcad63f083fc3d527f9a1ff5f869d"
    sm.check_round(6561788)
    with pytest.raises(sm.MainError, match="not 6561788"):
        sm.check_round(6561789)


def test_the_amendment_keeps_the_original_files_and_adds_its_own():
    assert set(sm.ORIGINAL_PROTOCOL_FILES) < set(sm.PROTOCOL_FILES)
    assert set(sm.PROTOCOL_FILES) - set(sm.ORIGINAL_PROTOCOL_FILES) == {sm.AMENDMENT}
    assert (ROOT / sm.AMENDMENT).is_file()


def test_claim_round_commit_and_sums():
    commits = ["a", "b", "c"]
    assert sm.first_with_file(commits, lambda c: c in {"b", "c"}) == "b"
    assert sm.first_with_file(commits, lambda c: False) is None
    sums = sm.parse_sums("aa" * 32 + "  2401.00001.json\n" + "bb" * 32 + "  2401.00002.json\n")
    assert sums == {"2401.00001.json": "aa" * 32, "2401.00002.json": "bb" * 32}


def test_the_claim_draw_needs_exactly_the_five_main_inventories():
    ids = ["2401.00001", "2401.00002", "2401.00003", "2401.00004", "2401.00005"]
    assert sm.expected_inventories(ids) == sorted(f"{a}.json" for a in ids)
    for bad in (ids[:4], ids[:4] + ids[:1], [*ids[:4], "x"], "2401.00001"):
        with pytest.raises(sm.MainError, match="5 distinct"):
            sm.expected_inventories(bad)


def test_protocol_files_cover_the_draw():
    for path in ("calibration/v0.3/main/PROTOCOL.md", "calibration/v0.3/main/select_main.py",
                 "src/refute/selection/inventory.py", "src/refute/core/hashing.py",
                 "uv.lock"):  # fmt: skip
        assert path in sm.PROTOCOL_FILES
