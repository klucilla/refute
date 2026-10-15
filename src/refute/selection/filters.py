"""Mechanical filters of the frame (WP5 W5.4, W5.5; plan section 4.2).

Applied to the frame before the draw, in the plan's order, with the count after each
one for the selection log:

0. rows with no arXiv ID or no repository URL are counted and set aside (the archive
   has rows with a null ``paper_arxiv_id``; they cannot be drawn);
1. deduplication of rows with the same ``paper_arxiv_id`` and ``repo_url``;
2. ``is_official`` and ``mentioned_in_paper`` both true;
3. a new-style arXiv ID (``YYMM.NNNNN``) whose year-month is inside the window;
5. one paper, one repository: a paper with more than one official repository is
   removed (``ambiguous_repository``), never resolved by choice;
7. removal of the pilot papers.

Filters 4 (the arXiv primary category) and 6 (out-of-scope keywords in the title or
abstract) need arXiv metadata, so they are checked for walked papers only, by
``category_allowed`` and ``keyword_hits``.

The pilot may adjust the window and the categories once, by the first alternative of
an ordered list whose trigger fires (``choose_adjustment``).
"""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import Any

NEW_STYLE_ID = re.compile(r"^(\d{2})(\d{2})\.\d{5}$")
YEAR_MONTH = re.compile(r"^(\d{4})-(\d{2})$")


class FilterError(Exception):
    """The filters or an adjustment cannot be applied as given."""


@dataclass(frozen=True)
class Window:
    """Inclusive year-month window, ``YYYY-MM``; plan D-2: 2023-01 to 2025-06."""

    first: str
    last: str

    def __post_init__(self) -> None:
        for value in (self.first, self.last):
            match = YEAR_MONTH.match(value)
            if not match or not 1 <= int(match.group(2)) <= 12:
                raise FilterError(f"not a year-month: {value!r}")
        if self.first > self.last:
            raise FilterError("the window starts after it ends")

    def contains(self, arxiv_id: str) -> bool:
        match = NEW_STYLE_ID.match(arxiv_id)
        if not match:
            return False
        year_month = f"20{match.group(1)}-{match.group(2)}"
        return int(match.group(2)) in range(1, 13) and self.first <= year_month <= self.last


DEFAULT_WINDOW = Window("2023-01", "2025-06")
DEFAULT_CATEGORIES = ("cs.LG", "stat.ML")


@dataclass
class FilterStep:
    """One filter of the selection log: its name, the papers left and the papers it removed."""

    name: str
    rows_after: int
    papers_after: int
    removed_papers: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    # rows removed by the step (for 0_ids_present, whose rows have no paper ID to list)
    rows_removed: int = 0


def _papers(rows: Iterable[dict[str, Any]]) -> set[str]:
    return {r["paper_arxiv_id"] for r in rows}


def apply_filters(
    rows: Iterable[dict[str, Any]],
    window: Window = DEFAULT_WINDOW,
    pilot_ids: Iterable[str] = (),
) -> tuple[list[dict[str, Any]], list[FilterStep]]:
    """The filtered frame, one row per paper sorted by arXiv ID, and the log of each step.

    Only ``True`` counts as true for ``is_official`` and ``mentioned_in_paper``: a null
    is not true. The result does not depend on the order of the input rows.
    """
    steps: list[FilterStep] = []

    def step(name: str, kept: list[dict[str, Any]], before: list[dict[str, Any]]) -> None:
        removed = sorted(_papers(before) - _papers(kept))
        steps.append(
            FilterStep(
                name, len(kept), len(_papers(kept)), removed, rows_removed=len(before) - len(kept)
            )
        )

    all_rows = [dict(r) for r in rows]
    # Rows with no text arXiv ID or no text repository URL (the archive has rows with a
    # null paper_arxiv_id) cannot be drawn; they are counted as a step, not an error.
    with_ids = [
        r
        for r in all_rows
        if isinstance(r.get("paper_arxiv_id"), str)
        and r["paper_arxiv_id"]
        and isinstance(r.get("repo_url"), str)
        and r["repo_url"]
    ]
    steps.append(
        FilterStep(
            "0_ids_present",
            len(with_ids),
            len(_papers(with_ids)),
            rows_removed=len(all_rows) - len(with_ids),
        )
    )

    # Duplicates that differ in another column keep the first row in a fixed order (so
    # the result never depends on the input order) and are recorded as conflicts.
    unique: dict[tuple[str, str], dict[str, Any]] = {}
    conflicts: set[str] = set()
    for r in sorted(with_ids, key=_row_key):
        key = (r["paper_arxiv_id"], r["repo_url"])
        if key in unique and unique[key] != r:
            conflicts.add(f"{key[0]} {key[1]}")
        unique.setdefault(key, r)
    deduped = [unique[k] for k in sorted(unique)]
    step("1_deduplicate", deduped, with_ids)
    steps[-1].conflicts = sorted(conflicts)

    official = [
        r for r in deduped if r.get("is_official") is True and r.get("mentioned_in_paper") is True
    ]
    step("2_official_and_mentioned", official, deduped)

    in_window = [r for r in official if window.contains(r["paper_arxiv_id"])]
    step("3_window", in_window, official)

    repos: dict[str, set[str]] = defaultdict(set)
    for r in in_window:
        repos[r["paper_arxiv_id"]].add(r["repo_url"])
    single = [r for r in in_window if len(repos[r["paper_arxiv_id"]]) == 1]
    step("5_one_repository", single, in_window)

    pilot = set(pilot_ids)
    final = [r for r in single if r["paper_arxiv_id"] not in pilot]
    step("7_not_in_pilot", final, single)
    return sorted(final, key=lambda r: r["paper_arxiv_id"]), steps


def _row_key(row: dict[str, Any]) -> tuple:
    return tuple(repr(row.get(k)) for k in sorted(row))


def category_allowed(primary_category: str, allowed: Sequence[str] = DEFAULT_CATEGORIES) -> bool:
    """Filter 4, for a walked paper: its arXiv primary category is in the list."""
    return primary_category in allowed


def keyword_hits(title: str, abstract: str, keywords: Sequence[str]) -> list[str]:
    """Filter 6, for a walked paper: the out-of-scope keywords found as whole words
    (case-insensitive) in its title or abstract, sorted. Any hit rejects the paper."""
    text = f"{title}\n{abstract}".lower()
    hits = []
    for keyword in keywords:
        word = keyword.strip().lower()
        if not word:
            raise FilterError("an empty keyword")
        if re.search(r"(?<!\w)" + re.escape(word) + r"(?!\w)", text):
            hits.append(keyword)
    return sorted(hits)


@dataclass(frozen=True)
class Alternative:
    """One alternative of the pilot's ordered adjustment list: applied when fewer than
    ``accepted_below`` of the pilot papers are accepted."""

    name: str
    accepted_below: int
    window: Window
    categories: tuple[str, ...]


def choose_adjustment(
    alternatives: Sequence[Alternative], pilot_accepted: int, adjustments_made: int
) -> Alternative | None:
    """The first alternative whose trigger fires, or None (W5.5). An adjustment is
    allowed at most once: a second one is refused."""
    if adjustments_made >= 1:
        raise FilterError("the frame was already adjusted once; a second adjustment is refused")
    names = [a.name for a in alternatives]
    if len(set(names)) != len(names):
        raise FilterError("alternative names must be unique")
    for alternative in alternatives:
        if pilot_accepted < alternative.accepted_below:
            return alternative
    return None


def check_adjustment(
    alternatives: Sequence[Alternative],
    pilot_accepted: int,
    adjustments_made: int,
    chosen: str | None,
) -> None:
    """Refuses an adjustment that is not the one ``choose_adjustment`` gives."""
    expected = choose_adjustment(alternatives, pilot_accepted, adjustments_made)
    expected_name = expected.name if expected else None
    if chosen != expected_name:
        raise FilterError(f"the adjustment must be {expected_name!r}, not {chosen!r}")
