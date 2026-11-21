"""v0.5.5: T3b's recount, its pure parts (``docs/validation/v0.5.5/t3b_recount.py``; the design
``docs/plans/v0.5.5-t3b-preparation.md``). Offline: synthetic frames, no MAST query."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "docs/validation/v0.5.5/t3b_recount.py"


@pytest.fixture(scope="module")
def tr():
    spec = importlib.util.spec_from_file_location("t3b_recount_under_test", SRC)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _frame():
    members = set(range(1, 64))  # 63
    walked = set(range(1, 42))  # 41
    accepted = set(range(1, 12))  # 11, all walked
    return members, walked, accepted


def test_the_readings_are_the_design_s(tr):
    sets = tr.readings(*_frame())
    assert sets["A"] == list(range(42, 64))  # the 22 never walked
    assert sets["B"] == list(range(12, 64))  # the 52 not accepted
    assert set(sets["A"]) <= set(sets["B"])


@pytest.mark.parametrize(
    "change",
    [
        lambda m, w, a: (m | {99}, w, a),  # 64 members
        lambda m, w, a: (m, w - {41}, a),  # 40 walked
        lambda m, w, a: (m, w, a - {11}),  # 10 accepted
        lambda m, w, a: (m, w | {100}, a),  # a walked star outside the frame
        lambda m, w, a: (m, w, (a - {11}) | {50}),  # an accepted star never walked
    ],
)
def test_another_frame_stops(tr, change):
    with pytest.raises(SystemExit, match="not the design's"):
        tr.readings(*change(*_frame()))


def test_the_tally_counts_and_the_shortage(tr):
    stars = list(range(12, 64))
    results = {
        t: (t % 5 == 0, "" if t % 5 == 0 else ("D-1: x" if t % 2 else "D-4: y")) for t in stars
    }
    out = tr.tally(results, stars)
    accepted = sum(t % 5 == 0 for t in stars)
    assert out["accepted_by_the_domain"] == accepted and out["stars"] == 52
    assert sum(out["rejected_by_clause"].values()) == 52 - accepted
    assert out["shortage"] == max(0, 11 - accepted) and out["needed"] == 11
    many = {t: (True, "") for t in stars}
    assert tr.tally(many, stars)["shortage"] == 0
