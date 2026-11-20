"""v0.5.5, R1: the frozen outcome rules, futility rules, seeds and machine policy
(``docs/validation/v0.5.5/r1_common.py``), on hand-made inputs; no data, no network."""

from __future__ import annotations

import datetime as dt
import math
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[2] / "docs/validation/v0.5.5"
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import r1_common as rc  # noqa: E402


def test_seeds_are_new_and_disjoint():
    a = rc.seed("d1p", "A", "EB1", 0)
    assert a == rc.seed("d1p", "A", "EB1", 0)
    assert (
        len(
            {
                a,
                rc.seed("d1p", "B", "EB1", 0),
                rc.seed("d2f", "A", "EB1", 0),
                rc.seed("d1p", "A", "EB2", 0),
                rc.seed("d1p", "A", "EB1", 1),
            }
        )
        == 5
    )


def test_machine_policy():
    friday_10 = dt.datetime(2026, 11, 20, 10, 0, tzinfo=rc.BRT)
    friday_19 = dt.datetime(2026, 11, 20, 19, 0, tzinfo=rc.BRT)
    saturday = dt.datetime(2026, 11, 21, 10, 0, tzinfo=rc.BRT)
    # R1 keeps at most 10 workers at every hour, so no pause is needed (the conservative option)
    for now in (friday_10, friday_19, saturday):
        assert rc.workers_now(now) == 10 and rc.pause_at(now) == rc.NO_PAUSE
    assert rc.working_hours(friday_10) and not rc.working_hours(saturday)
    assert rc.next_working_start(saturday) == dt.datetime(2026, 11, 23, 8, 0, tzinfo=rc.BRT)
    pins = rc.pin()
    assert len(pins) == 24 and min(pins) == 8 and max(pins) == 31 and len(set(pins)) == 24


def test_the_drivers_pause_comparison_accepts_every_pause_at():
    """The driver compares ``clock() >= pause_at`` (driver.py, its batch and its loop), with
    aware datetimes in its own zone; ``pause_at`` must never be None (Codex, r0r1 round 1)."""
    v052 = Path(__file__).resolve().parents[2] / "docs/validation/v0.5.2/stage2"
    if str(v052) not in sys.path:
        sys.path.insert(0, str(v052))
    import driver

    for now in (
        dt.datetime(2026, 11, 20, 10, 0, tzinfo=rc.BRT),
        dt.datetime(2026, 11, 20, 19, 0, tzinfo=rc.BRT),
    ):
        pause = rc.pause_at(now)
        assert isinstance(pause, dt.datetime) and pause.tzinfo is not None
        assert (now.astimezone(driver.BRT) >= pause) is False
    assert driver.workers_for(dt.datetime(2026, 11, 20, 10, 0, tzinfo=rc.BRT), 22) == 10


def test_identity_is_keyed_by_relative_path(tmp_path):
    (tmp_path / "a.txt").write_text("x", "utf-8")
    ident = rc.identity(tmp_path, [tmp_path / "a.txt"])
    assert list(ident["files"]) == ["a.txt"] and len(ident["sha256"]) == 64


def test_wilson_and_non_rejection():
    lo, hi = rc.wilson(0, 100)
    assert lo == pytest.approx(0.0, abs=1e-12) and 0.03 < hi < 0.04
    assert rc.non_rejection(0.0, 0.05) == pytest.approx(0.95)
    assert rc.non_rejection(10.0, 0.05) < 1e-6


def test_d1p_readings_and_exit_outcome():
    assert rc.d1p_set_reading(8.0, 10, 0.5, 0.99) == "route"
    assert rc.d1p_set_reading(8.1, 10, 0.9, 0.99) == "unresolved"
    assert rc.d1p_set_reading(8.0, 10, 0.49, 0.99) == "unresolved"
    assert rc.d1p_set_reading(10.5, 10, 0.0, 0.04) == "closed"
    assert rc.d1p_set_reading(10.0, 10, 0.0, 0.01) == "unresolved"  # not above k
    route = {"A": {"EB1": "route", "EB2": "route"}, "B": {"EB1": "route", "EB2": "route"}}
    assert rc.d1p_exit_outcome(route) == "route"
    one_closed = {"A": {"EB1": "closed", "EB2": "route"}, "B": {"EB1": "closed", "EB2": "route"}}
    assert rc.d1p_exit_outcome(one_closed) == "closed"
    split = {"A": {"EB1": "closed", "EB2": "route"}, "B": {"EB1": "unresolved", "EB2": "route"}}
    assert rc.d1p_exit_outcome(split) == "unresolved"
    assert rc.d1p_exit_outcome({"A": route["A"]}) == "unresolved"  # one set is never enough


def test_d1p_futility():
    assert rc.d1p_futile_after_first({"weakened": {"EB1": "unresolved", "EB2": "route"}})
    assert not rc.d1p_futile_after_first({"weakened": {"EB1": "route", "EB2": "route"}})
    assert not rc.d1p_futile_after_first({"weakened": {"EB1": "closed", "EB2": "unresolved"}})


def test_d2f_outcome_has_no_closed():
    # pooled 18 of 356 with each set at 9 of 178 (0.0506 <= 14/178): route
    assert rc.d2f_variant_outcome({"A": (9, 178), "B": (9, 178)}) == "route under the variant"
    # pooled 19 of 356: the Wilson upper end passes 14/178
    assert rc.d2f_variant_outcome({"A": (10, 178), "B": (9, 178)}) == "unresolved"
    # a large count never closes D2 (Codex, r0r1 round 1): it stays unresolved
    assert rc.d2f_variant_outcome({"A": (60, 178), "B": (60, 178)}) == "unresolved"
    assert rc.d2f_variant_outcome({"A": (5, 178)}) == "unresolved"  # two sets at least


def test_d2f_futility():
    assert rc.d2f_futile_after_first({"current": (20, 178), "variant_2_joint": (15, 178)})
    assert not rc.d2f_futile_after_first({"current": (20, 178), "variant_2_joint": (14, 178)})


def test_t2ae_outcome_and_futility():
    assert rc.t2ae_outcome(80, 90, 12) == "an error model is worth building"
    assert rc.t2ae_outcome(30, 90, 12) == "empirically limited for this estimator class"
    assert rc.t2ae_outcome(50, 90, 12) == "unresolved"
    assert rc.t2ae_outcome(80, 80, 22) == "INCONCLUSIVE (too many unknown)"
    assert rc.t2ae_futile_after_first(10, 30, 21, 51)
    assert not rc.t2ae_futile_after_first(10, 45, 6, 51)


def test_chi2_upper_factor():
    f = rc.chi2_upper_factor(24)
    assert 1.2 < f < 1.5 and math.isfinite(f)
    with pytest.raises(ValueError):
        rc.chi2_upper_factor(1)
