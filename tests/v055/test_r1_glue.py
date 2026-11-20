"""v0.5.5, R1: the glue functions of the three checks, on hand-made inputs (the maintainer's
decision of 2026-11-20, night, item 4d): D2-F's ``categories`` and ``floors``, D1-P's ``_family``,
T2a-E's ``shift_phases``, ``placebo`` (with a fake E4) and ``_check_i1``, and each part's cap
against its projection. No data, no network, no run; nothing is written to a ledger."""

from __future__ import annotations

import math
import sys
import types
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parents[2] / "docs/validation/v0.5.5"
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import r1_common as rc  # noqa: E402

# --- D2-F ---------------------------------------------------------------------------------------


def _d2f_rec(
    *,
    data=False,
    power=0.99,
    invalid=(),
    so=None,
    detail=None,
):
    rows = {"odd_even": {"status": "PASS"}, "sinusoid": {"status": "PASS"}}
    if data:
        rows["odd_even"] = {"status": "INCONCLUSIVE", "inconclusive_class": "not_enough_data"}
    if detail:
        rows["sinusoid"] = {"status": "INCONCLUSIVE", "inconclusive_detail": detail}
    oe = {"invalid": list(invalid)}
    if power is not None and not invalid:
        oe["power"] = power
    return {
        "v5_tests": rows,
        "decisive": ["odd_even", "sinusoid"],
        "odd_even_oracle": oe,
        "sinusoid_oracle": so
        or {"status": "OK", "min_frechet": 0.99, "min_joint": 0.99, "p_large": 0.99},
    }


def test_d2f_categories():
    import d2f_floor as d2

    clean = d2.categories(_d2f_rec())
    assert clean == {
        "DATA": False,
        "INFO": False,
        "SIN_F": False,
        "SIN_J": False,
        "RULE": False,
        "RULE_3": False,
    }
    assert d2.categories(_d2f_rec(data=True))["DATA"] is True
    assert d2.categories(_d2f_rec(power=0.9))["INFO"] is True
    # an invalid bound is unknown, never a number
    assert d2.categories(_d2f_rec(invalid=["F is ill-conditioned (3.55e+14)"]))["INFO"] is None
    so = {"status": "OK", "min_frechet": 0.92, "min_joint": 0.945, "p_large": 0.5}
    c = d2.categories(_d2f_rec(so=so, detail="AMBIGUOUS_SINUSOID"))
    # Fréchet below 0.93: True; joint within ±0.01 of 0.95: unknown; RULE and RULE_3 (P_large low)
    assert c["SIN_F"] is True and c["SIN_J"] is None and c["RULE"] is True and c["RULE_3"] is True
    so_hi = {"status": "OK", "min_frechet": 0.95, "min_joint": 0.99, "p_large": 0.999}
    c = d2.categories(_d2f_rec(so=so_hi, detail="AMBIGUOUS_SINUSOID"))
    # Fréchet within the band: unknown; a large residual shown: RULE_3 False
    assert c["SIN_F"] is None and c["SIN_J"] is False and c["RULE_3"] is False
    c = d2.categories(_d2f_rec(so={"status": "OUTSIDE_DOMAIN"}))
    assert c["SIN_F"] is False and c["SIN_J"] is False
    c = d2.categories(_d2f_rec(so={"status": "UNK"}, detail="AMBIGUOUS_SINUSOID"))
    assert c["SIN_F"] is None and c["SIN_J"] is None and c["RULE_3"] is None


def test_d2f_floors_strict_and_upper_per_variant():
    import d2f_floor as d2

    f, t, u = False, True, None
    cats = [
        {"DATA": f, "INFO": f, "SIN_F": t, "SIN_J": f, "RULE": f, "RULE_3": f},
        {"DATA": f, "INFO": u, "SIN_F": f, "SIN_J": f, "RULE": f, "RULE_3": f},
        {"DATA": f, "INFO": f, "SIN_F": f, "SIN_J": u, "RULE": t, "RULE_3": f},
        {"DATA": f, "INFO": f, "SIN_F": f, "SIN_J": f, "RULE": f, "RULE_3": f},
    ]
    fl = d2.floors(cats)
    assert set(fl) == set(d2.VARIANTS)
    assert fl["current"] == (2, 3)
    assert fl["variant_2_joint"] == (1, 2)
    assert fl["variant_3_evidence"] == (1, 2)
    assert fl["variant_4_combined"] == (0, 2)


def test_d2f_route_fraction_is_never_looser_than_14_of_178():
    # round 3's unit: v0.4 keeps 173 of 178, so D2 requires ceil(173 - 17.8) = 156 and allows 22;
    # less the estimators' 8: 14/178
    assert rc.d2f_route_fraction(173, 178) == pytest.approx(14 / 178)
    # v0.4 keeping every planet raises D2's requirement to 161: 17 allowed, 9/178 for the route
    assert rc.d2f_route_fraction(178, 178) == pytest.approx(9 / 178)
    # a lower v0.4 kept fraction leaves a larger allowance, but 14/178 still caps it
    assert rc.d2f_route_fraction(150, 178) == pytest.approx(rc.D2_ROUTE)
    with pytest.raises(ValueError):
        rc.d2f_route_fraction(0, 0)


def test_d2f_outcome_uses_the_stricter_threshold():
    ok = {"A": (9, 178, 173), "B": (9, 178, 173)}
    assert rc.d2f_variant_outcome(ok) == "route under the variant"
    assert rc.d2f_variant_outcome({"A": (10, 178, 173), "B": (9, 178, 173)}) == "unresolved"
    assert rc.d2f_variant_outcome({"A": (60, 178, 173), "B": (60, 178, 173)}) == "unresolved"
    assert rc.d2f_variant_outcome({"A": (5, 178, 173)}) == "unresolved"  # two sets at least
    # the same counts where v0.4 keeps every planet: its own unit (9/178 a set) decides
    assert rc.d2f_variant_outcome({"A": (9, 178, 178), "B": (10, 178, 178)}) == "unresolved"
    assert rc.d2f_futile_after_first({"current": (20, 178, 173), "v": (15, 178, 173)})
    assert not rc.d2f_futile_after_first({"current": (20, 178, 173), "v": (14, 178, 173)})


# --- D1-P ---------------------------------------------------------------------------------------


def _binary(family, i, *, eligible=True, survived=True, distance=3.0, status="OK"):
    rec = {"family": family, "index": i, "status": status}
    if status != "OK":
        return rec
    rec["eligible"] = eligible
    rec["v05_verdict"] = "SURVIVED" if survived else "INCONCLUSIVE"
    if eligible:
        rec["distances"] = {r: {"distance": distance} for r in ("prior", "box", "known")}
    return rec


def test_d1p_family_reads_both_views_and_flags_zero_survivors():
    import d1p_price as d1

    rng = np.random.default_rng(1)
    recs = [_binary("EB1", i, survived=i < 50, distance=6.0) for i in range(180)]
    recs += [_binary("EB1", 180 + i, status="GENERATION_FAILURE") for i in range(20)]
    fam = d1._family(recs, "EB1", rng, 150)
    assert fam["valid"] and fam["eligible"] == 180 and fam["survived_by_the_battery"] == 50
    assert fam["generation_failures"] == 20 and not fam["zero_survivors"]
    block = fam["readings"]["prior"][f"{0.05:.6g}"]
    assert set(block) == set(d1.VIEWS)
    # far binaries are rejected: both views read "route"; survivors alone give a lower count
    assert block["all_eligible"]["reading"] == "route"
    assert (
        block["survivors"]["expected_survived_at_projection"]
        <= block["all_eligible"]["expected_survived_at_projection"]
    )
    none = [_binary("EB2", i, survived=False) for i in range(180)]
    fam0 = d1._family(none, "EB2", rng, 150)
    assert fam0["zero_survivors"]
    for block in fam0["readings"]["prior"].values():
        assert block["survivors"]["reading"] == "INCONCLUSIVE (no survivor)"


def test_d1p_family_is_invalid_with_too_few_or_a_missing_distance():
    import d1p_price as d1

    rng = np.random.default_rng(2)
    few = [_binary("EB1", i) for i in range(100)]
    assert not d1._family(few, "EB1", rng, 150)["valid"]
    gap = [_binary("EB1", i) for i in range(180)]
    del gap[0]["distances"]
    out = d1._family(gap, "EB1", rng, 150)
    assert not out["valid"] and out["eligible_without_a_distance"] == 1 and "readings" not in out


def test_d1p_rules():
    assert rc.d1p_set_reading(8.0, 10, 0.5) == "route"
    assert rc.d1p_set_reading(8.1, 10, 0.9) == "unresolved"
    assert rc.d1p_set_reading(8.0, 10, 0.49) == "unresolved"
    both = {"A": {"EB1": "route", "EB2": "route"}, "B": {"EB1": "route", "EB2": "route"}}
    assert rc.d1p_exit_outcome({"survivors": both, "all_eligible": both}) == "route"
    split = {"A": {"EB1": "route", "EB2": "route"}, "B": {"EB1": "unresolved", "EB2": "route"}}
    assert rc.d1p_exit_outcome({"survivors": both, "all_eligible": split}) == "unresolved"
    flag = {
        "A": {"EB1": "INCONCLUSIVE (no survivor)", "EB2": "route"},
        "B": {"EB1": "route", "EB2": "route"},
    }
    assert rc.d1p_exit_outcome({"survivors": flag, "all_eligible": both}) == "unresolved"
    # zero or partial coverage is never a route (Codex, night round 1)
    assert rc.d1p_exit_outcome({}) == "INCONCLUSIVE"
    assert rc.d1p_exit_outcome({"survivors": {}, "all_eligible": {}}) == "INCONCLUSIVE"
    assert rc.d1p_exit_outcome({"survivors": {"A": both["A"]}}) == "INCONCLUSIVE"
    assert rc.d1p_exit_outcome({"survivors": both}) == "INCONCLUSIVE"  # one view missing
    empty_b = {"A": both["A"], "B": {}}
    assert rc.d1p_exit_outcome({"survivors": both, "all_eligible": empty_b}) == "INCONCLUSIVE"
    one_family = {"A": {"EB1": "route"}, "B": {"EB1": "route"}}
    assert rc.d1p_exit_outcome({"survivors": both, "all_eligible": one_family}) == "INCONCLUSIVE"
    fut = {"weakened": {"survivors": {"EB1": "route"}, "all_eligible": {"EB1": "unresolved"}}}
    assert rc.d1p_futile_after_first(fut)
    four = {"EB1": "route", "EB2": "route"}
    ok = {"weakened": {"survivors": four, "all_eligible": four}}
    assert not rc.d1p_futile_after_first(ok)
    # incomplete coverage never justifies set B
    partial = {"weakened": {"survivors": {"EB1": "route"}, "all_eligible": {"EB1": "route"}}}
    assert rc.d1p_futile_after_first(partial)
    assert rc.d1p_futile_after_first({"weakened": {"survivors": four}})


# --- T2a-E --------------------------------------------------------------------------------------


def _plan(outer=1.5):
    return types.SimpleNamespace(
        gauntlet=types.SimpleNamespace(events=types.SimpleNamespace(baseline_outer_durations=outer))
    )


def test_shift_phases_keep_clear_of_the_events_and_of_phase_half():
    import t2ae_census as te

    cand = types.SimpleNamespace(period=10.0, t0=0.0, duration=0.06)
    all_ = te.shift_phases(cand, _plan(), exclude_half=False)
    gap = 2.0 * (0.03 + 1.5 * 0.06) / 10.0
    assert len(all_) == te.SHIFTS and all(min(p, 1 - p) > gap for p in all_)
    half = te.shift_phases(cand, _plan(), exclude_half=True)
    assert all(abs(p - 0.5) > gap for p in half) and len(half) < len(all_)
    wide = types.SimpleNamespace(period=1.0, t0=0.0, duration=0.2)
    assert te.shift_phases(wide, _plan(), exclude_half=True) == []


def _cap(seed=7, excl=False):
    cand = types.SimpleNamespace(period=10.0, t0=0.0, duration=0.1)
    return {
        "candidate": cand,
        "plan": _plan(),
        "excl": excl,
        "t": np.arange(10.0),
        "bkg": np.zeros(10),
        "s": np.zeros(10),
        "seed": seed,
    }


def test_placebo_with_a_fake_e4(monkeypatch):
    import t2ae_census as te

    def fake(t, bkg, s, cand, plan, seed, excl):
        # a value that depends on the shifted epoch only; one shift refused
        if abs(cand.t0 - 0.4 * cand.period) < 1e-9:
            raise ValueError("refused")
        return types.SimpleNamespace(mean=math.sin(cand.t0), error=0.1)

    monkeypatch.setattr(te.battery_b1, "a0_depth_quadratic", fake)
    out = te.placebo(_cap())
    phases = te.shift_phases(_cap()["candidate"], _plan(), False)
    assert out["phases"] == len(phases) and out["status"] == "OK"
    assert sum(s["status"] == "OK" for s in out["shifts"]) == out["usable"]
    assert all("phase" in s for s in out["shifts"])
    values = [s["value"] for s in out["shifts"] if s["status"] == "OK"]
    assert out["sigma_placebo"] == pytest.approx(float(np.std(values, ddof=1)))
    assert out["sigma_placebo_inflated"] == pytest.approx(
        out["sigma_placebo"] * rc.chi2_upper_factor(len(values))
    )

    def none(*args):
        return types.SimpleNamespace(mean=float("nan"), error=None)

    monkeypatch.setattr(te.battery_b1, "a0_depth_quadratic", none)
    out = te.placebo(_cap())
    assert out["status"] == "UNK" and out["usable"] == 0


def test_check_i1_accepts_the_record_and_refuses_a_difference():
    import t2ae_census as te

    row = {"key": "k", "slot": 0}
    test = {"class": "i", "non_detectable": ["background"]}
    ref = {"class": "i", "non_detectable": ["background"], "background_rise_err": 2.0, "power": 0.5}
    te._check_i1(row, test, 2.0, 0.5, ref)
    with pytest.raises(RuntimeError, match="background error differs"):
        te._check_i1(row, test, 2.0 * (1 + 1e-6), 0.5, ref)
    with pytest.raises(RuntimeError, match="power differs"):
        te._check_i1(row, test, 2.0, 0.5001, ref)
    with pytest.raises(RuntimeError, match="class differs"):
        te._check_i1(row, {"class": "ii", "non_detectable": ["background"]}, 2.0, 0.5, ref)
    with pytest.raises(RuntimeError, match="not class"):
        te._check_i1(row, test, 2.0, 0.5, {**ref, "class": "ii"})


# --- the caps against the projections ------------------------------------------------------------


def test_each_cap_is_at_least_1_3_times_its_projection():
    import ledger_v055 as lv

    for part, projection in lv.PROJECTIONS.items():
        assert lv.ALLOCATIONS[part] / lv.OVERSHOOT >= lv.CAP_MARGIN * projection - 1e-9, part
    assert lv.ALLOCATIONS["r1_reserve"] >= 0
    total = sum(lv.ALLOCATIONS.values()) + lv.CHARGES_ROOM
    assert total == pytest.approx(lv.LINE_HOURS) and lv.LINE_HOURS <= 0.8 * lv.CAP_HOURS


# --- the frozen lists ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", ["d1p_price", "d2f_floor", "t2ae_census"])
def test_frozen_lists_are_complete(name):
    """In a process of its own: other tests' imports would otherwise count as loaded."""
    import subprocess

    code = (
        f"import sys; sys.path.insert(0, {str(HERE)!r}); import {name} as m, r1_common as rc; "
        "print(rc.unfrozen_modules(m.ROOT, m.FROZEN))"
    )
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    assert out.stdout.strip().splitlines()[-1] == "[]"


def test_a_module_outside_the_list_is_reported(tmp_path, monkeypatch):
    root = tmp_path
    (root / "docs").mkdir()
    (root / "docs" / "main.py").write_text("import helper\n", "utf-8")
    (root / "docs" / "helper.py").write_text("x = 1\n", "utf-8")
    monkeypatch.syspath_prepend(str(root / "docs"))
    missing = rc.unfrozen_modules(root, [root / "docs" / "main.py"])
    assert missing == ["docs/helper.py"]
    assert rc.unfrozen_modules(root, [root / "docs" / "main.py", root / "docs" / "helper.py"]) == []
    with pytest.raises(SystemExit, match="not frozen"):
        rc.require_frozen(root, [root / "docs" / "main.py"])


# --- the summaries' glue, on fake records (written to a temporary folder) -----------------------


def test_d1p_summary_of_set_a_writes_unresolved_when_futile(tmp_path, monkeypatch, capsys):
    import json

    import d1p_price as d1

    recs = [_binary(f, i, survived=i < 40, distance=1.0) for f in d1.FAMILIES for i in range(190)]
    monkeypatch.setattr(d1, "HERE", tmp_path)
    # other tests' imports are loaded in this process; the closure is tested in its own process
    monkeypatch.setattr(d1.rc, "require_frozen", lambda root, frozen: None)
    monkeypatch.setattr(d1, "_read", lambda set_name: recs)
    d1._summarize("A")
    doc = json.loads((tmp_path / "d1p-A.json").read_text("utf-8"))
    assert doc["futile_after_A"] is True and not doc["stops"]
    assert doc["outcome_per_exit"] == {e: "unresolved" for e in d1.EXITS}
    assert set(doc["per_exit_primary"]["weakened"]) == set(d1.VIEWS)
    with pytest.raises(SystemExit, match="written once"):
        d1._summarize("A")


def test_d2f_summary_of_set_a_tabulates_the_unknowns(tmp_path, monkeypatch, capsys):
    import json

    import d2f_floor as d2

    def rec(i):
        r = _d2f_rec(invalid=["F is ill-conditioned (1e15)"] if i < 3 else ())
        r["odd_even_oracle"]["invalid_by_i4"] = list(r["odd_even_oracle"]["invalid"])
        if i < 3:
            r["odd_even_oracle"]["power_of_an_invalid_bound"] = 0.9
        r.update(index=i, status="OK", gate_passed=True, identity=True, v04="SURVIVED")
        r["v5"] = "SURVIVED"
        return r

    recs = [rec(i) for i in range(178)]
    monkeypatch.setattr(d2, "HERE", tmp_path)
    # other tests' imports are loaded in this process; the closure is tested in its own process
    monkeypatch.setattr(d2.rc, "require_frozen", lambda root, frozen: None)
    monkeypatch.setattr(d2, "_read", lambda set_name: recs)
    d2._summarize("A")
    doc = json.loads((tmp_path / "d2f-A.json").read_text("utf-8"))
    c = doc["counts"]
    assert c["eligible"] == 178 and c["v04_kept"] == 178
    assert c["floors"]["variant_4_combined"] == [0, 3]
    assert c["unknown_rate_per_variant"]["current"] == pytest.approx(3 / 178)
    assert c["i4_bound"]["invalid_after_the_fix"] == 3
    assert c["i4_bound"]["powers_of_invalid_bounds"] == [0.9, 0.9, 0.9]
    # 3 of 178 is below the own unit (9/178 when v0.4 keeps every planet): not futile
    assert doc["futile_after_A"] is False and "outcome_per_variant" not in doc


def test_d1p_bridge_compares_the_same_indices_side_by_side(tmp_path, monkeypatch, capsys):
    import json

    import d1p_price as d1

    v2 = [_binary(f, i, survived=i < 30, distance=2.0) for f in d1.FAMILIES for i in range(200)]
    v1 = [
        _binary(f, i, survived=i < 30, distance=2.0, eligible=i != 7)
        for f in d1.FAMILIES
        for i in range(100)
    ]
    monkeypatch.setattr(d1, "HERE", tmp_path)
    monkeypatch.setattr(d1.rc, "require_frozen", lambda root, frozen: None)
    monkeypatch.setattr(d1, "_first_set", lambda: {"_sha256": "0" * 64})
    monkeypatch.setattr(d1, "_read", lambda set_name: v1 if set_name == "bridge" else v2)
    d1._summarize("bridge")
    doc = json.loads((tmp_path / "d1p-bridge.json").read_text("utf-8"))
    b = doc["bridge"]
    assert set(b) >= {"v1", "v2_same_indices", "per_index", "eligibility_differences"}
    # the v2 side holds only indices 0 to 99, the same as the bridge
    assert {r["index"] for r in b["per_index"]} == set(range(100))
    assert b["v2_same_indices"]["families"]["EB1"]["attempted"] == 100
    assert b["eligibility_differences"] == 2  # index 7 in each family
    assert set(b["v1"]["per_exit_primary"]["weakened"]) == set(d1.VIEWS)
    assert "outcome_per_exit" not in doc
