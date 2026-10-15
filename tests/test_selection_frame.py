"""Frame snapshot and mechanical filters of the v0.3 selection (WP5 W5.3 to W5.6), offline,
on a synthetic frame."""

import random

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from refute import drand
from refute.selection.filters import (
    DEFAULT_WINDOW,
    Alternative,
    FilterError,
    Window,
    apply_filters,
    category_allowed,
    check_adjustment,
    choose_adjustment,
    keyword_hits,
)
from refute.selection.frame import FRAME_COLUMNS, FrameError, FrameSnapshot, file_sha256, load_frame


def row(pid, repo, official=True, mentioned=True, framework="pytorch"):
    return {
        "paper_arxiv_id": pid,
        "repo_url": repo,
        "is_official": official,
        "mentioned_in_paper": mentioned,
        "framework": framework,
    }


FRAME = [
    row("2301.00001", "https://github.com/a/one"),  # window start: kept
    row("2301.00001", "https://github.com/a/one"),  # exact duplicate
    row("2506.99999", "https://github.com/b/two"),  # window end: kept
    row("2212.12345", "https://github.com/c/three"),  # before the window
    row("2507.00001", "https://github.com/d/four"),  # after the window
    row("2401.11111", "https://github.com/e/five", official=False),
    row("2401.22222", "https://github.com/f/six", mentioned=None),  # null is not true
    row("2402.33333", "https://github.com/g/seven"),  # two official repositories
    row("2402.33333", "https://github.com/g/seven-bis"),
    row("1234.5678", "https://github.com/h/old-style"),  # four-digit number: not new-style
    row("2313.12345", "https://github.com/i/month13"),  # month 13
    row("2403.44444v2", "https://github.com/j/version"),  # with a version suffix
    row("2404.55555", "https://github.com/k/pilot"),  # a pilot paper
    row("2405.66666", "https://github.com/l/kept"),
    row("2406.77777", "https://github.com/m/conflict"),  # duplicate with another framework
    row("2406.77777", "https://github.com/m/conflict", framework="jax"),
]


def test_filters_counts_order_and_removed_papers():
    papers, steps = apply_filters(FRAME, DEFAULT_WINDOW, pilot_ids=["2404.55555"])
    assert [p["paper_arxiv_id"] for p in papers] == [
        "2301.00001",
        "2405.66666",
        "2406.77777",
        "2506.99999",
    ]
    log = {s.name: s for s in steps}
    assert [s.name for s in steps] == [
        "1_deduplicate",
        "2_official_and_mentioned",
        "3_window",
        "5_one_repository",
        "7_not_in_pilot",
    ]
    assert (log["1_deduplicate"].rows_after, log["1_deduplicate"].papers_after) == (14, 13)
    assert log["1_deduplicate"].conflicts == ["2406.77777 https://github.com/m/conflict"]
    assert log["2_official_and_mentioned"].removed_papers == ["2401.11111", "2401.22222"]
    assert log["3_window"].removed_papers == [
        "1234.5678",
        "2212.12345",
        "2313.12345",
        "2403.44444v2",
        "2507.00001",
    ]
    assert log["5_one_repository"].removed_papers == ["2402.33333"]
    assert log["7_not_in_pilot"].removed_papers == ["2404.55555"]
    assert log["7_not_in_pilot"].papers_after == 4


def test_filters_do_not_depend_on_the_input_order():
    expected = apply_filters(FRAME, pilot_ids=["2404.55555"])
    for seed in range(5):
        shuffled = FRAME[:]
        random.Random(seed).shuffle(shuffled)
        assert apply_filters(shuffled, pilot_ids=["2404.55555"]) == expected


def test_filters_refuse_rows_without_text_ids():
    with pytest.raises(FilterError):
        apply_filters([{**row("2401.00001", "x"), "paper_arxiv_id": None}])


@pytest.mark.parametrize(
    ("first", "last"), [("2023-13", "2025-06"), ("2023-1", "2025-06"), ("2025-07", "2025-06")]
)
def test_window_refuses_bad_bounds(first, last):
    with pytest.raises(FilterError):
        Window(first, last)


def test_the_draw_order_is_fixed_for_a_seed():
    papers, _ = apply_filters(FRAME, pilot_ids=["2404.55555"])
    order = drand.shuffled(papers, 12345, key=lambda p: p["paper_arxiv_id"])
    # random.Random is the same on every platform; this order is recorded here.
    assert [p["paper_arxiv_id"] for p in order] == [
        "2405.66666",
        "2301.00001",
        "2406.77777",
        "2506.99999",
    ]


def test_category_and_keywords_for_walked_papers():
    assert category_allowed("cs.LG") and category_allowed("stat.ML")
    assert not category_allowed("cs.CV")
    assert keyword_hits("A GAN for Medical images", "", ["medical", "gan", "organ"]) == [
        "gan",
        "medical",
    ]
    assert keyword_hits("Organizing data", "", ["organ"]) == []
    with pytest.raises(FilterError):
        keyword_hits("x", "y", [" "])


ALTERNATIVES = [
    Alternative("widen-window", 5, Window("2022-07", "2025-06"), ("cs.LG", "stat.ML")),
    Alternative("add-cs-ai", 3, Window("2023-01", "2025-06"), ("cs.LG", "stat.ML", "cs.AI")),
]


def test_adjustment_is_the_first_triggered_alternative():
    assert (
        choose_adjustment(ALTERNATIVES, pilot_accepted=2, adjustments_made=0).name == "widen-window"
    )
    assert choose_adjustment(ALTERNATIVES, pilot_accepted=5, adjustments_made=0) is None
    check_adjustment(ALTERNATIVES, 2, 0, "widen-window")
    with pytest.raises(FilterError):
        check_adjustment(ALTERNATIVES, 2, 0, "add-cs-ai")  # not the first triggered
    with pytest.raises(FilterError):
        check_adjustment(ALTERNATIVES, 5, 0, "widen-window")  # nothing triggered
    with pytest.raises(FilterError):
        choose_adjustment(ALTERNATIVES, pilot_accepted=0, adjustments_made=1)  # a second one


def _write_frame(path, rows, columns=FRAME_COLUMNS):
    table = pa.table({c: [r.get(c) for r in rows] for c in columns})
    pq.write_table(table, path)


def test_frame_is_read_only_after_its_hash_matches(tmp_path):
    path = tmp_path / "frame.parquet"
    rows = [{**r, "extra": "ignored"} for r in FRAME[:3]]
    _write_frame(path, rows, columns=(*FRAME_COLUMNS, "extra"))
    snapshot = FrameSnapshot(
        "https://example.invalid/frame.parquet", "rev", file_sha256(path), path
    )
    loaded = load_frame(snapshot)
    assert loaded == [{c: r[c] for c in FRAME_COLUMNS} for r in FRAME[:3]]
    assert snapshot.record() == {
        "url": "https://example.invalid/frame.parquet",
        "revision": "rev",
        "sha256": file_sha256(path),
    }


def test_frame_with_another_hash_is_refused(tmp_path):
    path = tmp_path / "frame.parquet"
    _write_frame(path, FRAME[:2])
    with pytest.raises(FrameError, match="SHA-256"):
        load_frame(FrameSnapshot("u", "r", "0" * 64, path))
    with pytest.raises(FrameError, match="lowercase"):
        load_frame(FrameSnapshot("u", "r", file_sha256(path).upper(), path))


def test_frame_missing_a_column_is_refused(tmp_path):
    path = tmp_path / "frame.parquet"
    _write_frame(path, FRAME[:2], columns=FRAME_COLUMNS[:-1])
    with pytest.raises(FrameError, match="framework"):
        load_frame(FrameSnapshot("u", "r", file_sha256(path), path))
