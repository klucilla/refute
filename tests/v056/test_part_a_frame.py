"""v0.5.6 part A: the frame, the split and the predicted transits
(``docs/validation/v0.5.6/part_a_frame.py``). Offline, on synthetic tables."""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "docs/validation/v0.5.6/part_a_frame.py"
TESS = "Transiting Exoplanet Survey Satellite (TESS)"


@pytest.fixture(scope="module")
def fa():
    spec = importlib.util.spec_from_file_location("part_a_frame_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _toi(toi, tid, disp, period="2.0", epoch="2459000.0", dur="2.0", depth="1000.0"):
    return {"toi": toi, "tid": str(tid), "tfopwg_disp": disp, "pl_orbper": period,
            "pl_tranmid": epoch, "pl_trandurh": dur, "pl_trandep": depth, "st_tmag": "10.0",
            "toi_created": "2020-01-01", "rowupdate": "2024-01-01"}  # fmt: skip


def _planet(name, tic, period, facility=TESS):
    return {"pl_name": name, "tic_id": f"TIC {tic}", "pl_orbper": str(period),
            "disc_facility": facility}  # fmt: skip


TOIS = [
    _toi("100.01", 100, "CP"),  # planet arm (a TESS planet within 1 %)
    _toi("101.01", 101, "FP"),  # open arm, prior exposure
    _toi("102.01", 102, "PC"),  # several TOIs: excluded
    _toi("102.02", 102, "PC"),
    _toi("103.01", 103, "PC", epoch=""),  # incomplete ephemeris: excluded
    _toi("104.01", 104, "KP"),  # a planet found by another facility: open arm
    _toi("105.01", 105, "CP"),  # two matching TESS planets: ambiguous, excluded
    _toi("106.01", 106, "PC"),  # the same TOI listed twice: one TOI
    _toi("106.01", 106, "PC"),
]
PLANETS = [
    _planet("A b", 100, 2.02),  # exactly 1 % away: inclusive
    _planet("B b", 104, 2.0, "HATNet"),
    _planet("C b", 105, 2.0),
    _planet("C c", 105, 2.005),
]


def test_the_frame_rules(fa):
    rows, excluded = fa.build_frame(TOIS, PLANETS, {101})
    by = {r["tic_id"]: r for r in rows}
    assert set(by) == {100, 101, 104, 106}
    assert by[100]["arm"] == "planet" and by[100]["pl_name"] == "A b"
    assert by[101]["arm"] == "open" and by[101]["prior_exposure"] is True
    assert by[104]["arm"] == "open" and by[106]["arm"] == "open"
    assert excluded["several_tois"] == [102] and excluded["ephemeris"] == [103]
    assert excluded["ambiguous"] == [105]


def test_the_disposition_changes_no_decision(fa):
    swapped = [{**t, "tfopwg_disp": {"CP": "FP", "FP": "CP"}.get(t["tfopwg_disp"], "FA")}
               for t in TOIS]  # fmt: skip
    a, _ = fa.build_frame(TOIS, PLANETS, {101})
    b, _ = fa.build_frame(swapped, PLANETS, {101})
    keys = ("tic_id", "toi", "arm", "half", "prior_exposure", "period_days", "epoch_bjd")
    assert [{k: r[k] for k in keys} for r in a] == [{k: r[k] for k in keys} for r in b]
    assert [fa.draw_key(r["tic_id"]) for r in a] == [fa.draw_key(r["tic_id"]) for r in b]


def test_the_split_uses_the_whole_digest(fa):
    # a TIC whose whole digest and its first 64 bits have different parities
    for tic in range(1, 10_000):
        digest = hashlib.sha256(f"{fa.SEED}:split:{tic}".encode()).hexdigest()
        if int(digest, 16) % 2 != int(digest[:16], 16) % 2:
            break
    expected = "exploration" if int(digest, 16) % 2 == 0 else "confirmation"
    assert fa.half_of(tic) == expected
    halves = [fa.half_of(t) for t in range(1000, 1400)]
    assert 0.4 < halves.count("exploration") / len(halves) < 0.6


def test_predicted_transits_are_a_union_with_an_edge_margin(fa):
    # epoch JD 2459000.5 (MJD 59000), period 2 d: transits at MJD 59002 and 59004 inside
    w = {"t_min_mjd": 59001.0, "t_max_mjd": 59005.5}
    assert fa.predicted(2.0, 2459000.5, [w]) == 2
    assert fa.predicted(2.0, 2459000.5, [w, dict(w)]) == 2  # a repeated window counts once
    # a transit closer to the edge than the margin does not count
    edge = {"t_min_mjd": 59001.995, "t_max_mjd": 59003.0}
    assert fa.predicted(2.0, 2459000.5, [edge]) == 0
    assert fa.predicted(2.0, 2459000.5, [{"t_min_mjd": 59002.5, "t_max_mjd": 59003.5}]) == 0
