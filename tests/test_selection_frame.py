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
    adjustment_record,
    apply_filters,
    category_allowed,
    check_adjustment,
    choose_adjustment,
    keyword_hits,
    version_suffixed_ids,
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
        "0_ids_present",
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


def test_rows_without_ids_are_counted_not_fatal():
    # The archive has rows with a null paper_arxiv_id (Codex review of PR #78).
    rows = [
        row("2405.66666", "https://github.com/l/kept"),
        {**row("x", "https://github.com/n/null-id"), "paper_arxiv_id": None},
        {**row("2405.77777", "y"), "repo_url": None},
        {**row("", "https://github.com/o/empty-id")},
    ]
    papers, steps = apply_filters(rows)
    assert [p["paper_arxiv_id"] for p in papers] == ["2405.66666"]
    first = steps[0]
    assert (first.name, first.rows_after, first.rows_removed) == ("0_ids_present", 1, 3)
    assert steps[1].rows_removed == 0


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


# ---- #59, the Codex review of #78 (the maintainer's approval of 2026-10-17) -------------------


def test_a_deduplication_conflict_records_the_kept_row_and_the_differing_values():
    rows = [
        row("2301.00001", "https://github.com/a/one", official=True),
        row("2301.00001", "https://github.com/a/one", official=False),
        row("2301.00002", "https://github.com/b/two"),
    ]
    _, steps = apply_filters(rows)
    dedup = steps[1]
    assert dedup.conflicts == ["2301.00001 https://github.com/a/one"]
    (detail,) = dedup.conflict_details
    assert detail["paper_arxiv_id"] == "2301.00001"
    # the fixed order keeps False before True (repr), and the other value is recorded
    assert detail["kept"]["is_official"] is False
    assert detail["others"] == [{"is_official": True}]
    # the duplicate row is listed as removed while its paper stays
    assert dedup.removed_rows_paper_kept == ["2301.00001 https://github.com/a/one"]


def test_a_row_removed_while_its_paper_stays_is_listed():
    rows = [
        row("2301.00001", "https://github.com/a/official"),
        row("2301.00001", "https://github.com/a/unofficial", official=False),
    ]
    papers, steps = apply_filters(rows)
    official = steps[2]
    assert official.name == "2_official_and_mentioned"
    assert official.removed_papers == [] and official.rows_removed == 1
    assert official.removed_rows_paper_kept == ["2301.00001 https://github.com/a/unofficial"]
    assert [p["repo_url"] for p in papers] == ["https://github.com/a/official"]


ADJUSTMENTS = [
    Alternative("wider_window", 5, Window("2022-01", "2025-06"), ("cs.LG", "stat.ML")),
    Alternative("more_categories", 3, Window("2023-01", "2025-06"), ("cs.LG", "stat.ML", "cs.CV")),
]


@pytest.mark.parametrize(("accepted", "made"), [(-1, 0), (2, -1), (True, 0), (2, 1.0)])
def test_negative_or_non_integer_counters_are_refused(accepted, made):
    with pytest.raises(FilterError, match="non-negative integer"):
        choose_adjustment(ADJUSTMENTS, accepted, made)


@pytest.mark.parametrize("threshold", [-1, True, 2.0])
def test_an_alternative_needs_a_non_negative_integer_threshold(threshold):
    with pytest.raises(FilterError, match="accepted_below"):
        Alternative("bad", threshold, DEFAULT_WINDOW, ("cs.LG",))


def test_the_adjustment_record_names_the_alternative_and_its_reason():
    record = adjustment_record(ADJUSTMENTS, 2, 0)
    assert record["applied"] == "wider_window"
    assert record["window"] == {"first": "2022-01", "last": "2025-06"}
    assert record["categories"] == ["cs.LG", "stat.ML"]
    assert "2 pilot papers accepted, fewer than 5" in record["reason"]
    none = adjustment_record(ADJUSTMENTS, 6, 0)
    assert none["applied"] is None and "no trigger fired" in none["reason"]
    with pytest.raises(FilterError, match="already adjusted once"):
        adjustment_record(ADJUSTMENTS, 2, 1)


def test_version_suffixed_ids_are_measured():
    rows = [
        row("2301.00001", "https://github.com/a/one"),
        row("2301.00002v3", "https://github.com/b/two"),
        row("2301.00002v3", "https://github.com/b/three"),
        {"paper_arxiv_id": None, "repo_url": "https://github.com/c/x"},
    ]
    assert version_suffixed_ids(rows) == ["2301.00002v3"]
    # the window filter removes such rows; this measurement lists them for the protocol
    papers, _ = apply_filters(rows)
    assert [p["paper_arxiv_id"] for p in papers] == ["2301.00001"]
