"""v0.5.8: the stage-1 set, the stability report's rules and doors, and the stage-0 helpers.

Offline: the git bundles and synthetic records only; nothing runs the battery or downloads.
"""

from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


run = _load("v058_stability_run", "docs/validation/v0.5.8/stability_run.py")
rep = _load("v058_stability_report", "docs/validation/v0.5.8/stability_report.py")
st0 = _load("v058_stage0", "docs/validation/v0.5.8/stage0_records.py")


def test_the_set_is_the_107_decided_and_a_fixed_draw_of_60():
    a, b = run.build_set(), run.build_set()
    assert len(a["decided"]) == 107 and a["inconclusive_pool"] == 257
    assert len(a["inconclusive_drawn"]) == 60 == len(set(a["inconclusive_drawn"]))
    assert a["inconclusive_drawn"] == b["inconclusive_drawn"]  # the seed fixes it
    assert not set(a["decided"]) & set(a["inconclusive_drawn"])
    base = rep.v056()
    assert {base[k]["outcome"] for k in a["inconclusive_drawn"]} == {"INCONCLUSIVE"}
    assert all(base[k]["identity"]["matched"] for k in a["decided"] + a["inconclusive_drawn"])


def test_wilson_matches_known_values():
    lo, hi = rep.wilson(1, 150)
    assert lo == pytest.approx(0.00118, abs=1e-4) and hi == pytest.approx(0.0368, abs=1e-4)
    assert rep.wilson(0, 0) is None


def test_near_reads_power_margins_and_stated_statistics():
    power = {"tests": {"x": {"sensitivity": {"m": {"probability": 0.94,
                                                   "required_probability": 0.95}},
                             "message": ""}}}  # fmt: skip
    assert rep.near(power, "x")
    far = {"tests": {"x": {"sensitivity": {"m": {"probability": 0.5,
                                                 "required_probability": 0.95}},
                           "message": "odd/even difference 1.38 sigma (<= 3.0)"}}}  # fmt: skip
    assert not rep.near(far, "x")
    stat = {"tests": {"x": {"sensitivity": None,
                            "message": "odd/even depth difference 3.3 sigma (> 3.0)"}}}  # fmt: skip
    assert rep.near(stat, "x")


def _setup():
    s = run.build_set()
    base = rep.v056()
    keys = [*s["decided"], *s["inconclusive_drawn"]]
    fps = [k for k in s["decided"] if base[k]["_part"] == "B" and base[k]["arm"] == "fp"
           and base[k]["outcome"] == "REFUTED"]  # fmt: skip
    planets_b = [k for k in keys if base[k]["_part"] == "B" and base[k]["arm"] == "planet"]
    return s, base, keys, fps, planets_b


def test_identical_records_give_stable_doors():
    s, base, keys, fps, planets_b = _setup()
    new = {k: copy.deepcopy(base[k]) for k in keys}
    d = rep.doors(new, base, keys, s["decided"], fps, planets_b, True)
    assert len(fps) == 17
    assert d["door_1"]["changed_class"] == 0 and d["door_1"]["found"] is True
    assert d["door_2"]["status_changes"] == 0 and d["door_2"]["found"] is False
    assert d["door_3"]["snr_differs"] == 0 and d["door_3"]["needed"] == 9
    assert d["door_4"]["fp_stay_refuted"] == 17 and d["door_4"]["found"] is True


def test_records_not_ok_count_against_stability_and_incomplete_marks_nothing():
    s, base, keys, fps, planets_b = _setup()
    new = {k: {"status": "ERROR"} for k in keys}
    d = rep.doors(new, base, keys, s["decided"], fps, planets_b, True)
    assert d["door_1"]["changed_class"] == 107 and d["door_1"]["found"] is False
    assert d["door_3"]["snr_differs"] == 0
    incomplete = rep.doors({}, base, keys, s["decided"], fps, planets_b, False)
    assert all(v["found"] is None for v in incomplete.values())


def test_door_two_bounds_are_decimal_and_inclusive():
    boundary = {"tests": {"x": {"sensitivity": {"m": {"probability": 0.92,
                                                      "required_probability": 0.90}},
                                "message": ""}}}  # fmt: skip
    assert rep.near(boundary, "x")  # 0.92 - 0.90 is exactly 0.02 in decimal arithmetic
    sigma = {"tests": {"x": {"sensitivity": None,
                             "message": "difference 3.5 sigma (> 3.0)"}}}  # fmt: skip
    assert rep.near(sigma, "x")


def test_door_three_is_strict_and_tells_missing_from_zero():
    def rec(snr):
        return {"status": "OK", "candidate": {"snr": snr}}

    assert rep.snr_differs(rec(11.0), rec(10.0)) is False  # exactly 10 %: not more than 10 %
    assert rep.snr_differs(rec(11.01), rec(10.0)) is True
    assert rep.snr_differs({"status": "ERROR"}, rec(10.0)) is None
    assert rep.snr_differs(rec(None), rec(10.0)) is None
    assert rep.snr_differs(rec(5.0), rec(0.0)) is None


def test_an_empty_same_panel_is_no_data_and_duplicates_are_incomplete():
    s, base, keys, fps, planets_b = _setup()
    empty = rep.doors({}, base, [], [], [], [], True)
    assert all(v["no_data"] and v["found"] is None for v in empty.values())
    records = [{"target_key": k, "status": "OK"} for k in keys]
    assert rep.complete_set(records, keys)[0] is True
    assert rep.complete_set([*records, records[0]], keys)[0] is False
    assert rep.complete_set(records[1:], keys)[0] is False


def test_stage0_fisher_matches_the_v056_verdict():
    assert st0.fisher_one_sided(17, 150, 1, 150) == pytest.approx(4.726e-05, rel=1e-3)
