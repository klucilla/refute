"""Tests of v0.5.3 stage B's smoke validator (``b1_forecast.smoke_problems``): the checks that
decide whether B1.1's smoke passed. No network; synthetic records only."""

from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[2] / "docs/validation/v0.5.3/stageB"


@pytest.fixture(scope="module")
def runner():
    sys.path.insert(0, str(HERE))
    import b1_forecast

    yield b1_forecast
    b1_forecast.battery_b1.deactivate()


ROWS = [
    ("d2-03000", {"kind": "d2", "index": 3000}),
    ("t2a-K-6", {"kind": "t2a", "key": "K", "slot": 6, "row": {}}),
]
ACT = {"config": {"e1": True}, "replaced": {"a": "h"}}
FULL = {"e2.calls": 1, "e3.sinusoid_calls": 1, "e4.systematics_calls": 1, "e2.gls": 1}
REFUSED = {"e2.calls": 0, "e3.sinusoid_calls": 1, "e4.systematics_calls": 1}


def good():
    return [
        {"kind": "d2", "index": 3000, "status": "OK", "v5_activation": ACT, "v5_counts": FULL,
         "v5_tests": {"odd_even": {"refused": None}}},
        {"kind": "t2a", "key": "K", "slot": 6, "status": "OK", "compat_problems": [],
         "v5_activation": ACT, "sectors": 8,
         "v5A": {"selection": {"refused": "8 sectors: the sector selection is not certified"}},
         "v5A_counts": REFUSED, "v5C": {"selection": {"refused": None}}, "v5C_counts": FULL},
    ]  # fmt: skip


def test_accepts_correct_records_with_the_structural_refusal(runner):
    problems, report = runner.smoke_problems(good(), ROWS, ACT)
    assert problems == []
    assert [r["selector_refused"] for r in report] == [False, True, False]


@pytest.mark.parametrize(
    "mutate",
    [
        lambda recs: recs.clear(),
        lambda recs: recs[0].pop("v5_counts"),
        lambda recs: recs[0].update(v5_activation={"config": {}, "replaced": {}}),
        lambda recs: recs[1].update(compat_problems=["verdict differs"]),
        lambda recs: recs[1].update(v5C_counts={**FULL, "e2.calls": 0}),
        lambda recs: recs[1].update(v5A_counts={**REFUSED, "e2.calls": 2}),
        lambda recs: recs[0].update(status="ERROR"),
        lambda recs: recs[0].update(v5_counts={**FULL, "e3.sinusoid_calls": 1.5}),
    ],
)
def test_rejects_incomplete_or_wrong_evidence(runner, mutate):
    recs = copy.deepcopy(good())
    mutate(recs)
    problems, _ = runner.smoke_problems(recs, ROWS, ACT)
    assert problems
