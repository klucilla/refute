"""The C/D viability package's code (its acceptance record
docs/validation/v0.2.1/population/viability-cd-acceptance.md): the geometries, the cases and seeds,
the layouts, the generation, the record, the runner, the readings, the rule, section 9's step and
the destinations. Synthetic data and synthetic geometries only; no network; no case of the lot."""

from __future__ import annotations

import concurrent.futures as cf
import hashlib
import importlib
import json
import math
import multiprocessing
import sys
import uuid
from collections import Counter
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
POPULATION = ROOT / "docs" / "validation" / "v0.2.1" / "population"
WORK = ROOT / ".cache" / "test-viability-cd"


def _module(name: str):
    if str(POPULATION) not in sys.path:
        sys.path.insert(0, str(POPULATION))
    return importlib.import_module(name)


@pytest.fixture(scope="module")
def vc():
    return _module("viability_cd")


@pytest.fixture(scope="module")
def ev():
    return _module("viability_cd_evaluate")


# --- synthetic metadata --------------------------------------------------------------------------

# MJD of 2019-02-01, 2020-01-31, 2021-01-30, 2022-01-30, 2023-01-29 (00:00 UTC)
STARTS = (58515.0, 58879.0, 59244.0, 59609.0, 59973.0)


def _found(sectors, spans=None, tpf=None, extra_rows=()):
    spans = spans or {}
    rows = [{"sequence_number": s, "t_min": t, "t_max": t + spans.get(s, 27.0)} for s, t in sectors]
    rows += list(extra_rows)
    pixel = [{"sequence_number": s} for s, _ in sectors if tpf is None or s in tpf]
    return {"light_curves": rows, "pixel_files": pixel, "retrieved_utc": "2026-10-27T03:00:00Z"}


def _c_sectors(base=1, shift=0.0):
    return [(base + k, STARTS[k] + shift) for k in range(3)]


def _d_sectors(base=1, shift=0.0):
    return [(base + k, STARTS[k] + shift) for k in range(4)]


def _geometry(vc, alternative="C", spans=(27.0, 27.4, 28.0, 26.6)):
    sectors = _c_sectors() if alternative == "C" else _d_sectors()
    found = _found(sectors, {s: spans[k] for k, (s, _) in enumerate(sectors)})
    t = vc.tic_geometry(1000, found)
    assert t["alternative"] == alternative
    return {
        "key": [x["sector"] for x in t["sectors"]],
        "tic": 1000,
        "other_tics": [],
        "years": t["years"],
        "sectors": vc._btjd_sectors(t),
    }


# --- G1 to G8 ------------------------------------------------------------------------------------


def test_g1_the_source_s_sha256_is_checked(vc):
    path = WORK / uuid.uuid4().hex / "mast-rows.json"
    path.parent.mkdir(parents=True)
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit, match="SHA-256"):
        vc.load_mast_rows(path)


def test_g2_to_g4_consolidation_years_and_every_reason(vc):
    dup = [{"sequence_number": 2, "t_min": STARTS[1] - 0.5, "t_max": STARTS[1] + 20.0}]
    t = vc.tic_geometry(15, _found(_c_sectors(), extra_rows=dup))
    s2 = next(x for x in t["sectors"] if x["sector"] == 2)
    assert s2["t_min_mjd"] == STARTS[1] - 0.5 and s2["t_max_mjd"] == STARTS[1] + 27.0
    assert t["years"] == [2019, 2020, 2021] and t["alternative"] == "C"
    assert vc.tic_geometry(14, _found(_d_sectors()))["alternative"] == "D"
    two = vc.tic_geometry(12, _found([(1, STARTS[0]), (2, STARTS[1])]))
    assert two["alternative"] is None and two["reasons"] == ["years: 2"]
    bad = vc.tic_geometry(13, _found(_c_sectors(), spans={1: 25.49, 3: 30.01}, tpf={1, 3}))
    assert bad["reasons"][0] == "no target pixel file: [2]"
    assert [r.split(":")[0] for r in bad["reasons"][1:]] == ["span outside 25.5 to 30.0 d"] * 2
    assert "1 25.49" in bad["reasons"][1] and "3 30.01" in bad["reasons"][2]
    closed = vc.tic_geometry(16, _found(_c_sectors(), spans={1: 25.5, 2: 30.0}))
    assert closed["alternative"] == "C"
    assert vc.utc_year(STARTS[0]) == 2019 and vc.utc_year(58484.0 - 1e-6) == 2018
    with pytest.raises(ValueError):
        vc.consolidate({"light_curves": [{"sequence_number": 1, "t_min": 2.0, "t_max": 1.0}]})


def _rows(n_c: int, n_d: int) -> dict:
    rows = {}
    for k in range(n_c):
        rows[str(100 + k)] = _found(_c_sectors(base=10 * k + 1))
    for k in range(n_d):
        rows[str(500 + k)] = _found(_d_sectors(base=10 * k + 1))
    return rows


def test_g5_unique_keys_take_the_lowest_eligible_tic_s_dates(vc):
    rows = {
        "5": _found(_c_sectors(shift=0.3), spans={1: 24.0}),  # same key, ineligible
        "11": _found(_c_sectors(shift=0.1)),
        "10": _found(_c_sectors(shift=0.2)),
        "20": _found(_c_sectors(shift=0.4)),
    }
    listing = vc.geometry_list(rows)
    (geo,) = listing["alternatives"]["C"]["eligible"]
    assert geo["tic"] == 10 and geo["other_tics"] == [11, 20]
    assert geo["sectors"][0]["t_min_btjd"] == pytest.approx(STARTS[0] + 0.2 - 56999.5, abs=1e-9)


def test_g6_the_seeded_selection_and_its_sizes(vc):
    listing = vc.geometry_list(_rows(30, 15))
    for a, n, size in (("C", 30, 24), ("D", 15, 12)):
        part = listing["alternatives"][a]
        ordered = part["eligible"]
        assert [g["key"] for g in ordered] == sorted(g["key"] for g in ordered)
        assert len(ordered) == n
        seed = int.from_bytes(
            hashlib.sha256(f"refute/v0.2.1/viability-cd/geometries/{a}".encode()).digest()[:8],
            "big",
        )
        perm = np.random.default_rng(seed).permutation(n)
        assert part["permutation"] == [int(i) for i in perm]
        assert part["selected"] == [ordered[int(i)] for i in perm][:size]
    few = vc.geometry_list(_rows(5, 0))
    assert len(few["alternatives"]["C"]["selected"]) == 5
    assert few["alternatives"]["D"]["selected"] == []


def test_g7_g8_dates_and_the_analytic_acceptance(vc):
    geo = _geometry(vc)
    assert geo["sectors"][0]["t_min_btjd"] == STARTS[0] - 56999.5
    rng = np.random.default_rng(7)
    for span in (25.7, 27.0, 29.3):
        g = rng.uniform(0.5, 2.0, 400000)
        d = rng.uniform(-0.5, 0.5, 400000)
        l1 = (span - g) / 2 + d
        l2 = span - g - l1
        mc = np.mean((l1 >= 12.5) & (l1 <= 14) & (l2 >= 12.5) & (l2 <= 14))
        assert vc.orbit_acceptance(span) == pytest.approx(mc, abs=3e-3)
    assert vc.orbit_acceptance(24.0) == 0.0
    listing = vc.geometry_list(_rows(3, 1))
    acc = listing["acceptance"]["C"]
    assert len(acc["sectors"]) == 9 and acc["expected_exhausted_draws"] >= 0.0


# --- K1 to K6 ------------------------------------------------------------------------------------


def test_k_the_cases_seeds_assignment_and_order(vc):
    cases = vc.lot_cases("C", 24)
    assert len(cases) == 720 and len({c["id"] for c in cases}) == 720
    groups = Counter((c["noise"], c["mechanism"]) for c in cases)
    assert set(groups.values()) == {180} and len(groups) == 4
    assert [(c["noise"], c["mechanism"], c["index"]) for c in cases[:4]] == [
        ("white", "three_years", 0),
        ("white", "variability_some_years", 0),
        ("correlated", "three_years", 0),
        ("correlated", "variability_some_years", 0),
    ]
    c = next(x for x in cases if x["noise"] == "correlated" and x["index"] == 31)
    text = f"refute/v0.2.1/viability-cd/C/AR(1)/{c['mechanism']}/31"
    assert int(c["seed"]) == int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big")
    assert c["extra"] == {"alternative": "C", "geometry": 31 % 24}
    assert c["id"] == f"C-correlated-{c['mechanism']}-0031" and c["band"] == "measurable"
    assert len({x["seed"] for x in cases}) == 720
    d = vc.lot_cases("D", 12)
    assert len(d) == 240 and Counter(x["noise"] for x in d) == {"white": 120, "correlated": 120}
    assert {x["mechanism"] for x in d} == {"three_years"}
    test = vc.lot_cases("C", 24, vc.TEST_SEED_ROOT)
    assert not {x["seed"] for x in test} & {x["seed"] for x in cases}
    assert vc.SUBLOTS["viability-c"].prefix == "refute-v0.2.1-viability-cd-1"


# --- L1 to L4 ------------------------------------------------------------------------------------


def _case(vc, alternative="C", regime="three_years", noise="white", i=0):
    return vc.make_case(vc.TEST_SEED_ROOT, alternative, noise, regime, i, 0)


def test_l_a_layout_s_draw_order_ranges_and_checks(vc):
    geo = _geometry(vc)
    case = _case(vc)
    lay = vc.draw_layout(case, geo)
    v4 = vc.v4
    rng = np.random.default_rng(vc.pv2.sub_seed(int(case["seed"]), "layout", lay["attempt"]))
    for k, x in enumerate(geo["sectors"]):  # rebuilt by hand, in the declared order
        while True:
            g, delta = rng.uniform(0.5, 2.0), rng.uniform(-0.5, 0.5)
            l1 = (x["span_days"] - g) / 2 + delta
            l2 = x["span_days"] - g - l1
            if 12.5 <= l1 <= 14 and 12.5 <= l2 <= 14:
                break
        blocks = [
            {"seconds": float(rng.uniform(600, 21600)), "place": float(rng.uniform())}
            for _ in range(int(rng.integers(0, 5)))
        ]
        rho = rng.uniform(0, 0.05)
        n = round(l1 / v4.DT) + round(l2 / v4.DT)
        losses, jitter = rng.uniform(size=n), rng.uniform(-0.25, 0.25, size=n)
        t, _, _ = v4._sector(x["t_min_btjd"], (l1, l2), g, blocks, rho, losses, jitter)
        assert np.array_equal(t, lay["times"][k])
    res = lay["domain"]
    assert res.conditions["D3"] and res.conditions["D4"] and res.conditions["D1"]
    assert [s.label for s in res.sectors] == [2019, 2020, 2021]
    for s in res.sectors:
        assert all(12.5 <= o <= 14.0 for o in s.orbit_days)
    assert lay["times"][0][0] == pytest.approx(geo["sectors"][0]["t_min_btjd"], abs=1e-5)


def test_l_redraws_their_reasons_and_exhaustion(vc, monkeypatch):
    geo = _geometry(vc)
    case = _case(vc)
    real = vc.domain.check_domain
    calls = []

    def first_fails(times):
        calls.append(1)
        r = real(times)
        if len(calls) == 1:
            return r.__class__(False, "D4", "D4: x", {**r.conditions, "D4": False}, r.sectors, ())
        return r

    monkeypatch.setattr(vc.domain, "check_domain", first_fails)
    lay = vc.draw_layout(case, geo)
    assert lay["attempt"] == 1 and lay["redraws"] == {"layout:D4": 1}
    monkeypatch.setattr(vc.domain, "check_domain", real)
    three = real(vc.draw_layout(case, geo)["times"])
    assert vc.layout_failure("D", three) == "layout:labels"
    assert vc.layout_failure("C", three) is None
    with pytest.raises(RuntimeError, match="orbit draw"):
        vc._orbits(np.random.default_rng(1), 24.0)
    d_lay = vc.draw_layout(_case(vc, "D"), _geometry(vc, "D"))
    assert len({s.label for s in d_lay["domain"].sectors}) == 4


# --- P1 to P5 ------------------------------------------------------------------------------------


def test_p_a_built_curve_its_absent_year_its_twin_and_its_noise(vc):
    geo = _geometry(vc)
    case = _case(vc, regime="variability_some_years", noise="correlated", i=3)
    built = vc.build_curve(case, geo)
    p, lc = built["parameters"], built["lc"]
    labels = sorted({int(s.year) for s in built["sectors"]})
    assert labels == [2019, 2020, 2021]
    assert p["var_absent_year"] == labels[p["var_absent_position"]]
    assert p["var_amplitude"] == p["var_amplitude_factor"] * p["depth"]
    assert [s.sector for s in built["sectors"]] == geo["key"]
    rng = np.random.default_rng(vc.pv2.sub_seed(int(built["attempt_seed"]), "noise"))
    noise = np.concatenate(
        [vc.pv2._noise(rng, lc.time[lc.sector == s], "correlated") for s in geo["key"]]
    )
    assert np.allclose(lc.flux - built["model"], noise, rtol=0, atol=1e-15)
    absent = lc.year == p["var_absent_year"]
    assert absent.any() and not absent.all()


def test_p2_the_absent_year_names_the_sorted_distinct_label_at_its_position(vc):
    for drawn, want in ((2018, 2019), (2019, 2020), (2020, 2021)):
        p = {"var_absent_year": drawn}
        vc.map_absent_year(p, [2019, 2019, 2020, 2021])  # two sectors in the first year
        assert p["var_absent_year"] == want
        assert p["var_absent_position"] == (2018, 2019, 2020).index(drawn)
    untouched = {"period": 3.0}
    vc.map_absent_year(untouched, [2019, 2020, 2021])
    assert untouched == {"period": 3.0}


def test_p5_the_curve_is_the_same_in_another_process(vc):
    geo = _geometry(vc)
    case = _case(vc, i=5)
    here = vc.case_digest(case, geo)
    with cf.ProcessPoolExecutor(1, mp_context=multiprocessing.get_context("spawn")) as pool:
        there = pool.submit(vc.case_digest, case, geo).result()
    assert here == there == vc.case_digest(case, geo)


def test_p5_the_determinism_check_builds_the_first_tasks_three_times(vc):
    spec = vc.SubLot("viability-test", "C", 1.0, 100.0, vc.TEST_PREFIX, vc.TEST_SEED_ROOT)
    out = vc.determinism(spec, [_geometry(vc)], 2, workers=2)
    assert out["agree"] is True and len(out["digests"]) == 2 and out["workers"] == [0, 1, 2]
    assert out["tasks"] == [c["id"] for c in vc.lot_cases("C", 1, vc.TEST_SEED_ROOT)[:2]]


# --- R1 to R6 (the real engine on a synthetic geometry) -----------------------------------------


def _declared():
    return {
        "format": "refute-m4-configuration/1",
        "name": "M4-rmin-study",
        "path": "docs/validation/v0.2.1/population/m4-configurations/rmin-study.json",
        "sha256": "0" * 64,
        "block_sha256": "1" * 64,
    }


def _plan():
    from refute.packs.tess import synthetic
    from refute.packs.tess.params import TessTestPlan

    plan = synthetic.fast_plan_dict()
    plan["gauntlet"] = {"corrections": {"version": 2, "enabled": True, "r_min": 8}}
    return TessTestPlan.model_validate(plan)


@pytest.fixture
def lot_env(vc, monkeypatch):
    import refute.packs.tess.holdout as holdout

    monkeypatch.setattr(vc.v3, "STATE", {"problem": None, "identity": _declared()})
    monkeypatch.setattr(vc.v3, "_plan", _plan)
    original = holdout.calibration_measurement

    def measurement(raw, sectors, year, plan, *, identity, twin_model=None):
        from refute.core.canonical import canonical_sha256

        block = canonical_sha256(plan.gauntlet.corrections.model_dump(mode="json"))
        return original(
            raw, sectors, year, plan, identity={**identity, "block_sha256": block},
            twin_model=twin_model,
        )  # fmt: skip

    monkeypatch.setattr(holdout, "calibration_measurement", measurement)
    return vc


def _spec(vc):
    return vc.SubLot("viability-test", "C", 1.0, 100.0, vc.TEST_PREFIX, vc.TEST_SEED_ROOT)


@pytest.fixture(scope="module")
def real_record():
    """One record from the real engine (module scope: built once, about a minute)."""
    vc = _module("viability_cd")
    mp = pytest.MonkeyPatch()
    import refute.packs.tess.holdout as holdout

    mp.setattr(vc.v3, "STATE", {"problem": None, "identity": _declared()})
    mp.setattr(vc.v3, "_plan", _plan)
    original = holdout.calibration_measurement

    def measurement(raw, sectors, year, plan, *, identity, twin_model=None):
        from refute.core.canonical import canonical_sha256

        block = canonical_sha256(plan.gauntlet.corrections.model_dump(mode="json"))
        return original(
            raw, sectors, year, plan, identity={**identity, "block_sha256": block},
            twin_model=twin_model,
        )  # fmt: skip

    mp.setattr(holdout, "calibration_measurement", measurement)
    try:
        geo = _geometry(vc)
        case = _case(vc, i=1)
        rec = vc.record_target(case, geo, _declared(), _spec(vc))
        yield vc, case, geo, json.loads(vc.x2.record_text(rec))
    finally:
        mp.undo()


def test_r_a_record_from_the_engine_is_complete(real_record):
    vc, case, geo, rec = real_record
    assert vc.record_problems(rec, case, geo, _declared(), _spec(vc)) == []
    assert rec["years"] == [2019, 2020, 2021] and len(rec["rounds"]) == 3
    assert set(rec["truth"]) == set(vc.x2.TRUTH_FIELDS) and rec["truth"]["s"] == 1.0
    for y in rec["years"]:
        ident = rec["identity"][str(y)]
        rnd = next(r for r in rec["rounds"] if r["hidden_year"] == y)
        if rnd["train_ephemeris"] is None:
            assert ident == {"identifiable": False, "period_ratio": None, "flag": None}
        else:
            ratio = rnd["train_ephemeris"]["period"] / rec["truth"]["period"]
            assert ident["flag"] == (abs(ratio - 1) > 0.01)
        assert set(rec["oracle"][str(y)]) == set(vc.ORACLE_FIELDS)
    for drop in (
        "rounds", "identity", "oracle", "truth", "sectors", "geometry", "layout", "attempt_seed",
        "curve_sha256", "redraws",
    ):  # fmt: skip
        bad = {k: v for k, v in rec.items() if k != drop}
        assert vc.record_problems(bad, case, geo, _declared(), _spec(vc)), drop

    def tampered(change):
        bad = json.loads(json.dumps(rec))
        change(bad)
        return vc.record_problems(bad, case, geo, _declared(), _spec(vc))

    assert tampered(lambda r: r["geometry"].update(position=5))
    assert tampered(lambda r: r["geometry"].update(tic=999))

    def shift_years(r):  # every year moved by 100 years, consistently in every field
        for s in r["sectors"]:
            s["year"] += 100
        r["years"] = [y + 100 for y in r["years"]]
        for rnd in r["rounds"]:
            rnd["hidden_year"] += 100
        r["identity"] = {str(int(k) + 100): v for k, v in r["identity"].items()}
        r["oracle"] = {str(int(k) + 100): v for k, v in r["oracle"].items()}

    assert any("label" in p for p in tampered(shift_years))
    assert any("real dates" in p for p in tampered(lambda r: r["sectors"][0].update(t_start=0.0)))
    assert tampered(lambda r: r["layout"]["sectors"].pop())


def test_r_the_truth_is_never_read_during_the_engine_calls(lot_env, monkeypatch):
    import refute.packs.tess.holdout as holdout

    vc = lot_env
    made = []
    original = vc.rs.EvaluatorTruth

    def capture(data):
        t = original(data)
        made.append(t)
        return t

    monkeypatch.setattr(vc.rs, "EvaluatorTruth", capture)

    def leaky(*a, **k):
        made[-1]["period"]
        raise AssertionError("not reached")

    monkeypatch.setattr(holdout, "calibration_measurement", leaky)
    with pytest.raises(RuntimeError, match="truth"):
        vc.record_target(_case(vc), _geometry(vc), _declared(), _spec(vc))


def test_r4_the_oracle_s_bands_leave_out_what_lies_between_them(vc):
    """Cadences between T14/2 and T14 are neither in transit nor baseline: a bump there must not
    move the depth."""
    dt = 120.0 / 86400.0
    t = np.arange(3000.0, 3027.0, dt)
    truth = {"period": 2.5, "t0": 3001.0, "duration": 0.12}
    rng = np.random.default_rng(11)
    flux = 1.0 + rng.normal(0, 1e-6, t.size)
    phase = np.abs(np.mod(t - truth["t0"] + 1.25, 2.5) - 1.25)
    flux[phase <= 0.06] -= 0.002
    flux[(phase > 0.06) & (phase < 0.12)] += 0.01  # between the two bands
    out = vc.oracle_year(t, flux, [(t[0], t[-1])], truth, 7.0)
    assert out["kept"] >= 9 and abs(out["depth"] - 0.002) < 1e-5


def test_r3_the_identity_flag(vc):
    assert vc.identity_flag({"train_ephemeris": None}, 3.0)["identifiable"] is False
    assert vc.identity_flag({"train_ephemeris": {"period": 3.0299}}, 3.0)["flag"] is False
    assert vc.identity_flag({"train_ephemeris": {"period": 3.0301}}, 3.0)["flag"] is True
    assert vc.identity_flag({"train_ephemeris": {"period": 6.0}}, 3.0)["flag"] is True


def test_r4_the_oracle_on_a_constructed_curve(vc):
    dt = 120.0 / 86400.0
    t = np.arange(2000.0, 2027.0, dt)
    truth = {"period": 3.0, "t0": 2000.05, "duration": 0.1}
    rng = np.random.default_rng(3)
    flux = 1.0 + 1e-4 * (t - 2010.0) + rng.normal(0, 5e-4, t.size)
    phase = np.mod(t - truth["t0"] + 1.5, 3.0) - 1.5
    flux[np.abs(phase) <= 0.05] -= 0.002
    out = vc.oracle_year(t, flux, [(t[0], t[-1])], truth, 7.0)
    assert out["n_centres"] == 9 and out["skipped"] == 1 and out["kept"] == 8  # the first is cut
    assert out["depth"] == pytest.approx(0.002, abs=5 * out["error"])
    assert out["detectable"] is True and out["reason"] is None
    none = vc.oracle_year(t, flux, [(t[0], t[0] + 0.01)], truth, 7.0)
    assert none["detectable"] is False and none["reason"] == "no kept transit"
    weak = vc.oracle_year(t, flux, [(t[0], t[-1])], truth, 1e6)
    assert weak["reason"] == "below min_snr"
    # a baseline that reaches 3 T14 but not past it: the bands are closed
    assert vc.ORACLE_MIN_IN == 5 and vc.ORACLE_MIN_SIDE == 10


# --- X1 to X8 (the runner, with a stand-in task) -------------------------------------------------


def _fake_record(vc, case, geometry, configuration, spec):
    from refute.packs.tess.types import btjd_to_year

    order = sorted(geometry["sectors"], key=lambda s: s["t_min_btjd"])
    sectors = [
        {
            "sector": x["sector"],
            "year": btjd_to_year(x["t_min_btjd"]),
            "t_start": x["t_min_btjd"],
            "t_end": x["t_max_btjd"] - 0.01,
            "n_points": 100,
        }
        for x in order
    ]
    years = sorted({x["year"] for x in sectors})
    return {
        "format": vc.RECORD_FORMAT,
        "target": f"{spec.prefix}/{case['id']}",
        "case_id": case["id"],
        "alternative": case["extra"]["alternative"],
        "noise": case["noise"],
        "regime": case["mechanism"],
        "index": case["index"],
        "geometry": {
            "position": case["extra"]["geometry"],
            "key": geometry["key"],
            "tic": geometry["tic"],
        },
        "seed": case["seed"],
        "attempt_seed": "1",
        "layout": {
            "attempt": 0,
            "redraws": {},
            "sectors": [{"sector": x["sector"]} for x in order],
        },
        "redraws": {},
        "curve_sha256": "0" * 64,
        "years": years,
        "sectors": sectors,
        "configuration": configuration,
        "rounds": [{**dict.fromkeys(vc.x2.ROUND_FIELDS), "hidden_year": y} for y in years],
        "identity": {str(y): dict.fromkeys(vc.IDENTITY_FIELDS) for y in years},
        "oracle": {str(y): dict.fromkeys(vc.ORACLE_FIELDS) for y in years},
        "truth": dict.fromkeys(vc.x2.TRUTH_FIELDS, 1.0),
    }


@pytest.fixture
def fake_lot(lot_env, monkeypatch):
    vc = lot_env
    seconds = {"value": 1.0}
    monkeypatch.setattr(vc, "_task", lambda task: (_fake_record(vc, *task), seconds["value"]))
    geos = [_geometry(vc)]
    tasks = vc.lot_cases("C", 1, vc.TEST_SEED_ROOT, {"three_years": 3, "variability_some_years": 0})
    return vc, geos, tasks, seconds


def _run(vc, run, geos, tasks, **kw):
    return vc.run_lot(
        _spec(vc), run, geos, "a" * 64, tasks=tasks, workers=1, executor=vc.rs._InlineExecutor(),
        **kw,
    )  # fmt: skip


def _bytes(run):
    files = (run / "records").rglob("*.json")
    return {p.relative_to(run).as_posix(): p.read_bytes() for p in files}


def test_x_a_complete_run_the_manifest_s_binding_and_records_never_replaced(fake_lot, monkeypatch):
    vc, geos, tasks, _ = fake_lot
    run = WORK / uuid.uuid4().hex
    report = _run(vc, run, geos, tasks)
    assert report["complete"] is True and len(_bytes(run)) == 6
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["geometry_sha256"] == "a" * 64 and manifest["lot"] == "viability-test"
    assert vc.lot_problems(run, _spec(vc), geos, tasks) == []
    before = _bytes(run)
    again = _run(vc, run, geos, tasks)  # a complete sub-lot relaunched runs nothing again
    assert again["dispatched"] == 0 and again["submitted"] == 0 and _bytes(run) == before
    assert again["terminal_failures"] == [] and again["complete"] is True
    with pytest.raises(FileExistsError):
        vc.x2.write_record_atomic(vc.record_path(run, tasks[0]["id"]), "{}\n")
    monkeypatch.setattr(vc, "code_digest", lambda: "f" * 64)
    with pytest.raises(SystemExit, match="manifest"):
        _run(vc, run, geos, tasks)


def test_x7_an_interrupted_sub_lot_resumed_gives_the_continuous_run_s_bytes(fake_lot, monkeypatch):
    vc, geos, tasks, _ = fake_lot
    base = WORK / uuid.uuid4().hex
    _run(vc, base / "continuous", geos, tasks)
    calls = []

    def killed(task):
        calls.append(task)
        if len(calls) == 3:
            raise KeyboardInterrupt  # the process stopped from outside, mid-run
        return _fake_record(vc, *task), 1.0

    monkeypatch.setattr(vc, "_task", killed)
    cut = base / "cut"
    with pytest.raises(KeyboardInterrupt):
        _run(vc, cut, geos, tasks)
    monkeypatch.setattr(vc, "_task", lambda task: (_fake_record(vc, *task), 1.0))
    with pytest.raises(SystemExit, match="consumption"):
        _run(vc, cut, geos, tasks)  # an unclosed invocation needs a recorded decision
    (consumption,) = sorted((cut / "consumption").glob("*.json"))
    hours = json.loads(consumption.read_text(encoding="utf-8"))["elapsed_hours"]
    markers = sorted(p.relative_to(cut).as_posix() for p in (cut / "attempts").rglob("*.json"))
    open_markers = [m for m in markers if not vc.record_path(cut, Path(m).parent.name).exists()]
    (cut / "retry-decisions").mkdir()
    (cut / "retry-decisions" / "001.json").write_text(
        json.dumps(
            {
                "decision": "issue #000: the one pre-approved resumption",
                "covers": open_markers,
                "consumption": {consumption.stem: hours},
            }
        ),
        encoding="utf-8",
    )
    resumed = _run(vc, cut, geos, tasks)
    assert resumed["complete"] is True and resumed["retried"], resumed
    assert resumed["started_utc"] != consumption.stem
    assert _bytes(cut) == _bytes(base / "continuous")


def test_x_an_invocation_never_reuses_an_earlier_invocation_s_stamp(fake_lot, monkeypatch):
    """Two invocations within one tick of the clock: the second takes another stamp."""
    import datetime as dt

    vc, geos, tasks, _ = fake_lot
    run = WORK / uuid.uuid4().hex
    frozen = dt.datetime(2026, 10, 27, 12, 0, 0, 1, tzinfo=dt.UTC)
    ticks = iter([frozen, frozen] + [frozen + dt.timedelta(microseconds=k) for k in range(1, 99)])

    class Clock(dt.datetime):
        @classmethod
        def now(cls, tz=None):
            return next(ticks)

    monkeypatch.setattr(vc, "datetime", Clock)
    first = _run(vc, run, geos, tasks)
    second = _run(vc, run, geos, tasks)
    assert first["complete"] and second["complete"]
    assert first["started_utc"] != second["started_utc"]


def test_x5_the_cost_check_stops_the_sub_lot(fake_lot):
    vc, geos, tasks, seconds = fake_lot
    seconds["value"] = 1e6  # each task as if it took 1e6 s
    run = WORK / uuid.uuid4().hex
    report = _run(vc, run, geos, tasks)
    check = json.loads((run / "cost-check.json").read_text(encoding="utf-8"))
    assert check["stop"] is True and check["tasks_checked"] == 1
    assert report["cost_stop"] is True and report["complete"] is False
    assert report["submitted"] < len(tasks)
    again = _run(vc, run, geos, tasks)
    assert again["submitted"] == 0 and again["cost_stop"] is True
    p = vc.cost_projection([10.0, 20.0], 720, 22)
    assert p["projected_lp_hours"] == pytest.approx(15.0 * 720 / 3600)
    assert p["projected_hours"] == pytest.approx(15.0 * 720 / 22 / 3600)


def test_x3_a_failed_task_is_terminal(fake_lot, monkeypatch):
    vc, geos, tasks, _ = fake_lot

    def crashing(task):
        if task[0]["id"] == tasks[1]["id"]:
            raise RuntimeError("crash")
        return _fake_record(vc, *task), 1.0

    monkeypatch.setattr(vc, "_task", crashing)
    run = WORK / uuid.uuid4().hex
    first = _run(vc, run, geos, tasks)
    assert first["complete"] is False and len(first["failures"]) == 1
    monkeypatch.setattr(vc, "_task", lambda task: (_fake_record(vc, *task), 1.0))
    second = _run(vc, run, geos, tasks)
    assert second["submitted"] == 0 and second["terminal_failures"][0]["case_id"] == tasks[1]["id"]
    problems = vc.lot_problems(run, _spec(vc), geos, tasks)
    assert problems == [f"{tasks[1]['id']}: no record"]


def test_x9_a_generation_defect_stops_the_sub_lot(fake_lot, monkeypatch):
    vc, geos, tasks, _ = fake_lot

    def exhausted(task):
        if task[0]["id"] == tasks[0]["id"]:
            raise vc.GenerationDefectError("no orbit draw within 12.5 to 14.0 d")
        return _fake_record(vc, *task), 1.0

    monkeypatch.setattr(vc, "_task", exhausted)
    run = WORK / uuid.uuid4().hex
    report = _run(vc, run, geos, tasks)
    assert report["defect"] is True and report["complete"] is False
    assert report["submitted"] < len(tasks) and (run / "defect.json").exists()
    again = _run(vc, run, geos, tasks)
    assert again["submitted"] == 0 and again["defect"] is True
    assert isinstance(vc.GenerationDefectError("x"), RuntimeError)
    with pytest.raises(vc.GenerationDefectError):
        vc._orbits(np.random.default_rng(1), 24.0)


def test_x8_a_damaged_file_is_a_problem_never_an_exception(fake_lot):
    vc, geos, tasks, _ = fake_lot
    run = WORK / uuid.uuid4().hex
    _run(vc, run, geos, tasks)
    vc.record_path(run, tasks[0]["id"]).write_text('{"truncated', encoding="utf-8")
    stray = run / "records" / "stray" / "000.json"
    stray.parent.mkdir()
    stray.write_text("not json", encoding="utf-8")
    problems = vc.lot_problems(run, _spec(vc), geos, tasks)
    assert f"{tasks[0]['id']}: not JSON" in problems
    assert any("stray" in p and "own path" in p for p in problems)
    good, bad = vc.load_records(run)
    assert len(good) == len(tasks) - 1 and len(bad) == 2
    (run / "manifest.json").write_text("{", encoding="utf-8")
    assert vc.lot_problems(run, _spec(vc), geos, tasks)[0].startswith("the manifest is not")


def test_e_the_evaluator_s_operational_causes_and_notes(fake_lot, ev):
    vc, geos, tasks, _ = fake_lot
    run = WORK / uuid.uuid4().hex
    _run(vc, run, geos, tasks)
    state = ev.sublot_state(run, _spec(vc), geos, "a" * 64, tasks)
    assert state["causes"] == [] and len(state["records"]) == len(tasks)
    assert any("the manifest's geometry_sha256" in c for c in ev.sublot_state(
        run, _spec(vc), geos, "b" * 64, tasks
    )["causes"])  # fmt: skip
    other = vc.SubLot("viability-test", "C", 2.0, 100.0, vc.TEST_PREFIX, vc.TEST_SEED_ROOT)
    assert ev.sublot_state(run, other, geos, "a" * 64, tasks)["causes"]
    (run / "defect.json").write_text("{}", encoding="utf-8")
    assert any(
        "defect" in c for c in ev.sublot_state(run, _spec(vc), geos, "a" * 64, tasks)["causes"]
    )
    (run / "defect.json").unlink()
    (run / "cost-check.json").write_text('{"stop": true}', encoding="utf-8")
    assert any(
        "cost check" in c for c in ev.sublot_state(run, _spec(vc), geos, "a" * 64, tasks)["causes"]
    )
    (run / "cost-check.json").unlink()
    vc.record_path(run, tasks[1]["id"]).unlink()
    state = ev.sublot_state(run, _spec(vc), geos, "a" * 64, tasks)
    assert state["causes"] == [] and "1 records missing" in state["notes"]
    vc.record_path(run, tasks[2]["id"]).write_text("[", encoding="utf-8")
    assert ev.sublot_state(run, _spec(vc), geos, "a" * 64, tasks)["causes"]
    assert ev.sublot_state(WORK / uuid.uuid4().hex, _spec(vc), geos, "a" * 64)["causes"]


def _many(n, rounds_of, noise, regime="three_years", prefix="x"):
    return [
        _record(rounds_of(), noise=noise, regime=regime, case_id=f"{prefix}{noise}{k}")
        for k in range(n)
    ]


def _listing(vc, tmp_name: str, c=True, d=True):
    geo = _geometry(vc)
    data = {
        "format": vc.GEOMETRY_FORMAT,
        "alternatives": {
            "C": {"selected": [geo] if c else []},
            "D": {"selected": [geo] if d else []},
        },
    }
    path = WORK / uuid.uuid4().hex / tmp_name
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def _evaluate_with(ev, monkeypatch, records, listing):
    def state(run_dir, spec, geometries, sha, tasks=None):
        return {"records": records[spec.alternative], "causes": [], "notes": []}

    monkeypatch.setattr(ev, "sublot_state", state)
    return ev.evaluate({"viability-c": None, "viability-d": None}, listing, 7.0)


def test_e_the_step_runs_only_where_the_joint_destination_names_it(vc, ev, monkeypatch):
    passing = lambda: [_rnd(2019), _rnd(2020)]  # noqa: E731
    capacity = lambda: [_rnd(2019), _rnd(2020, **ROW_ROUNDS[11])]  # noqa: E731
    c_pass = [r for noise in vc.NOISES for r in _many(360, passing, noise)]
    d_indet = [r for noise in vc.NOISES for r in _many(120, capacity, noise, prefix="d")]
    for r in d_indet:
        r["alternative"] = "D"
    out = _evaluate_with(ev, monkeypatch, {"C": c_pass, "D": d_indet}, _listing(vc, "l.json"))
    assert out["alternatives"]["C"]["outcome"]["outcome"] == "PASS"
    assert out["alternatives"]["D"]["outcome"]["outcome"] == "INDETERMINATE"
    assert out["steps"] == {} and out["final"]["proposals"] == ["C executable plan"]
    c_indet = [r for noise in vc.NOISES for r in _many(360, capacity, noise)]
    out = _evaluate_with(ev, monkeypatch, {"C": c_indet, "D": d_indet}, _listing(vc, "l.json"))
    assert sorted(out["steps"]) == ["C", "D"]
    assert out["steps"]["C"]["succeeds"] is True  # today's models pass these rounds' fields
    assert out["final"]["proposals"] == ["specification C validation proposal"]
    nothing = _evaluate_with(ev, monkeypatch, {"C": [], "D": []}, _listing(vc, "l.json", c=False))
    assert nothing["alternatives"]["C"]["outcome"] == {
        "outcome": "INDETERMINATE",
        "causes": ["no geometry"],
    }
    assert nothing["steps"]["C"] is None and "C" in nothing["final"]["ended"]


def test_e_the_step_s_ceiling_is_an_operational_closure(ev):
    ticks = iter([0.0] + [1e9] * 50)
    records = {"white": [_record([_rnd(2019), _rnd(2020)])], "correlated": []}
    out = ev.step(records, {"white": 1, "correlated": 0}, 7.0, clock=lambda: next(ticks))
    assert out["closure"] is True and len(out["pairs"]) == 1
    final = ev.final_reading(ev.destination("INDETERMINATE", "FAIL"), {"C": out})
    assert final["closures"] == ["the step over C"] and final["effort_ends_not_approved"] is False


def test_e8_the_reported_bounds_both_ways(ev):
    rows = [ev.target_reading(_record([_rnd(2019), _rnd(2020, **ROW_ROUNDS[11])], case_id="a"))]
    out = ev.alternative_summary(
        [_record([_rnd(2019), _rnd(2020, **ROW_ROUNDS[11])], case_id="a")], "D", []
    )
    w = out["per_noise"]["white"]
    assert w["missing"] == 119 and set(w["R2"]) == {"R2-K", "R2-KT", "R2-KTN"}
    assert w["R2"]["R2-K"]["pass_bounds"]["with_missing"]["k"] == 120
    assert w["R2"]["R2-K"]["pass_bounds"]["without_missing"]["k"] == 1
    assert rows[0]["R2-K"] == "PASS"


# --- E1 to E9 ------------------------------------------------------------------------------------


def test_e2_every_row_an_unmapped_reason_raises_and_the_pinned_sources(ev):
    for reason, row in ev.ROW_EXACT.items():
        assert ev.row_of("INCONCLUSIVE", reason) == row
    assert ev.row_of("INCONCLUSIVE", "only 2 train transit times (< 3)") == 6
    msg = (
        "train-only timing uncertainty in the hidden year (5.10 h) exceeds 1 transit duration(s) "
        "(2.00 h)"
    )
    assert ev.row_of("INCONCLUSIVE", msg) == 7
    assert ev.row_of("PASS", None) == 17 and ev.row_of("FAIL", "inconsistent_with_train") == 17
    for status, reason in (("INCONCLUSIVE", "something else"), ("FAIL", None), ("PASS", "x")):
        with pytest.raises(ev.UnmappedReasonError):
            ev.row_of(status, reason)
    assert ev.source_digests() == ev.PINNED
    assert set(ev.BARRIERS) == set(range(1, 18))
    assert ev.R2_SETS["R2-K"] == {6, 10, 11} and ev.R2_SETS["R2-KTN"] == {6, 7, 10, 11, 12, 13}


def test_e2_the_engine_s_rounds_all_map(real_record, ev):
    _, _, _, rec = real_record
    rounds = ev.target_rounds(rec)
    assert len(rounds) == 3 and all(1 <= r["row"] <= 17 for r in rounds)


def _rnd(year=2019, **over):
    base = {k: None for k in _module("x2_study").ROUND_FIELDS}
    base.update(
        hidden_year=year, stage=None, n_years=3, train_n_rep=[10, 10, 10], s_pred_1=100.0,
        hidden_noise_undetermined=False, hidden_n_rep=[10, 10, 10], s_pred_2=100.0,
        measurement_status="ok", s_meas=20.0, d_train=0.002, e_train=0.0002, d_hidden=0.002,
        e_hidden=0.0001, d_c=0.004, n_pred=4, m_beta=1.2, grid_dp=[-1e-4, 0.0, 1e-4],
        train_var_rep=[4e-8, 1e-8, 9e-8], hidden_var_rep=[4e-8, 1e-8, 9e-8], reason=None,
    )  # fmt: skip
    base.update(over)
    return base


ROW_ROUNDS = {
    7: {
        "stage": "before_capacity",
        "reason": "train-only timing uncertainty in the hidden year (9 h)",
    },
    10: {"stage": "train_counts", "train_n_rep": [3, 10, 10]},
    11: {"s_pred_1": 0.1},
    12: {"stage": "hidden_noise"},
    13: {"s_pred_2": 0.1},
    14: {"measurement_status": "too_few_windows"},
    16: {"s_meas": 1.0, "d_hidden": 0.0018},
    17: {},
}
FAIL_ROUND = {"s_meas": 1.0, "d_hidden": 0.0}


def _record(rounds, noise="white", regime="three_years", case_id="x", detectable=True):
    years = [r["hidden_year"] for r in rounds]
    return {
        "case_id": case_id, "alternative": "C", "noise": noise, "regime": regime,
        "years": years, "rounds": rounds, "geometry": {"position": 0},
        "oracle": {str(y): {"detectable": detectable} for y in years},
        "identity": {str(y): {"identifiable": True, "flag": False} for y in years},
    }  # fmt: skip


def test_e1_e3_e4_the_readings_on_constructed_records(ev):
    for row, over in ROW_ROUNDS.items():
        assert ev.target_rounds(_record([_rnd(**over)]))[0]["row"] == row, row
    r = ev.target_reading(
        _record([_rnd(2019), _rnd(2020, **ROW_ROUNDS[11]), _rnd(2021, **ROW_ROUNDS[12])])
    )
    assert r["R1"] == "INCONCLUSIVE" and r["R2-K"] == "INCONCLUSIVE" and r["R2-KTN"] == "PASS"
    assert r["legacy"] == "PASS" and r["R3"] == "PASS"
    f = ev.target_reading(_record([_rnd(2019, **FAIL_ROUND), _rnd(2020, **ROW_ROUNDS[11])]))
    assert f["R1"] == "FAIL" and f["R2-KTN"] == "FAIL"
    assert ev.target_reading(_record([_rnd(2019)], detectable=False))["R3"] == "not PASS"


def test_e5_e6_the_hurdle_the_worst_assignment_and_every_outcome(ev):
    assert ev.pass_rule(360, 289, 26, 0) and not ev.pass_rule(360, 288, 26, 0)
    assert not ev.pass_rule(360, 289, 27, 0) and not ev.pass_rule(360, 289, 20, 7)
    assert ev.pass_rule(120, 100, 6, 0) and not ev.pass_rule(120, 99, 6, 0)
    assert not ev.pass_rule(120, 100, 7, 0)

    def per(n_pass=300, n_fail=10, r2ktn=330, missing=0):
        base = {"n": 360, "missing": 0, "pass": 300, "fail": 10, "pass_r2ktn": 330}
        white = {"n": 360, "missing": missing, "pass": n_pass, "fail": n_fail, "pass_r2ktn": r2ktn}
        return {"white": white, "correlated": base}

    def out(per_noise, causes=()):
        return ev.outcome(per_noise, list(causes))["outcome"]

    assert out(per()) == "PASS"
    assert out(per(missing=19)) == ev.CLOSURE
    assert out(per(missing=18, n_fail=5)) == "PASS"
    assert out(per(missing=18)) == "INDETERMINATE"  # 28 FAIL at worst
    assert out(per(), ["an integrity error"]) == ev.CLOSURE
    assert out(per(n_pass=200, r2ktn=250)) == "FAIL"
    assert out(per(n_pass=250, n_fail=60)) == "FAIL"
    assert out(per(n_pass=250, r2ktn=300)) == "INDETERMINATE"
    assert out(per(n_pass=280, r2ktn=280)) == "INDETERMINATE"


def test_e7_newcombe_s_interval(ev):
    out = ev.newcombe(56, 70, 48, 80)  # Newcombe (1998), method 10: 0.0524 to 0.3339
    assert out["difference"] == pytest.approx(0.2)
    assert out["lo"] == pytest.approx(0.0524, abs=1e-4)
    assert out["hi"] == pytest.approx(0.3339, abs=1e-4)


def test_e8_the_candidate_models(ev):
    r = _rnd()
    assert ev.e_pred("E1.0", r) == pytest.approx(1.2 * math.sqrt(9e-8 / 4))
    assert ev.e_pred("E1.nomargin", r) == pytest.approx(math.sqrt(9e-8 / 4))
    assert ev.e_pred("E1.dp0", r) == pytest.approx(1.2 * math.sqrt(1e-8 / 4))
    assert ev.e_pred("E1.dp0.nomargin", r) == pytest.approx(math.sqrt(1e-8 / 4))
    assert ev.e_pred("E2.0", r) == pytest.approx(math.sqrt(9e-8 / 4))
    assert ev.e_pred("E2.dp0", r) == pytest.approx(math.sqrt(1e-8 / 4))
    assert ev.e_pred("E2.median", r) == pytest.approx(math.sqrt(4e-8 / 4))
    assert math.isnan(ev.e_pred("E2.0", _rnd(hidden_var_rep=[1e-8, None, 1e-8])))
    assert math.isnan(ev.e_pred("E1.dp0", _rnd(grid_dp=[-1e-4, 1e-4, 2e-4])))
    assert math.isnan(ev.e_pred("E2.0", _rnd(n_pred=0)))


def _consistent(r):
    """``s_pred`` of a constructed round set from its own fields by today's models."""
    from refute.packs.tess.holdout import predicted_error

    r = dict(r)
    if r["stage"] != "before_capacity":
        e1 = predicted_error(r["train_var_rep"], r["n_pred"], r["m_beta"])
        e2 = predicted_error(r["hidden_var_rep"], r["n_pred"])
        r["s_pred_1"] = r["d_c"] / e1 if e1 > 0 else float("nan")
        r["s_pred_2"] = r["d_c"] / e2 if e2 > 0 else float("nan")
    return r


def test_e8_today_s_pair_is_derive_round_exactly(ev, real_record):
    from refute.packs.tess.holdout import derive_round

    _, _, _, rec = real_record
    rounds = [_consistent(_rnd(**o)) for o in ROW_ROUNDS.values()]
    rounds += [_consistent(_rnd(d_c=x)) for x in (1e-5, 1e-4, 3e-4, 6e-4, 1e-3)]
    rounds += rec["rounds"]
    for rnd in rounds:
        want = derive_round(rnd, 8, 0.585, 2.883, 7.0)
        got = ev.derive_with(
            rnd, ev.s_pred(rnd, ev.e_pred("E1.0", rnd)), ev.s_pred(rnd, ev.e_pred("E2.0", rnd)), 7.0
        )
        assert (got["status"], got["reason"]) == (want["status"], want["reason"])


def _threshold():
    from refute.packs.tess.holdout import capacity_threshold

    return capacity_threshold(7.0, 0.585, 2.883, 3)


def test_e8_a_released_round_takes_its_measured_outcome_and_the_envelope_bounds(ev):
    e_today = 1.2 * math.sqrt(9e-8 / 4)
    d_c = 1.1 * _threshold() * e_today / 1.2  # below the threshold with the margin, above without
    rnd = _consistent(_rnd(2020, d_c=d_c, **FAIL_ROUND))
    assert ev.derive_with(rnd, ev.s_pred(rnd, ev.e_pred("E1.0", rnd)), 1e9, 7.0)["reason"] == (
        "insufficient_capacity_train"
    )
    released = ev.derive_with(rnd, ev.s_pred(rnd, ev.e_pred("E1.nomargin", rnd)), 1e9, 7.0)
    assert released["status"] == "FAIL"
    records = {
        "white": [_record([_consistent(_rnd(2019)), rnd], case_id=f"w{k}") for k in range(3)],
        "correlated": [_record([_consistent(_rnd(2019))], noise="correlated")],
    }
    out = ev.step(records, {"white": 3, "correlated": 1}, 7.0)
    assert len(out["pairs"]) == 12
    env = out["envelope_descriptive"]
    for pair in out["pairs"].values():
        for noise, x in pair["noise"].items():
            assert x["pass"] <= env[noise]["pass_upper"] and x["fail"] <= env[noise]["fail_upper"]
    assert out["pairs"]["E1.0+E2.0"]["noise"]["white"]["fail"] == 0
    assert out["pairs"]["E1.nomargin+E2.0"]["noise"]["white"]["fail"] == 3
    assert out["succeeds"] is False  # too few planets for the bounds


def test_e8_applicability(ev):
    per = {"white": {"n": 360, "missing": 0, "pass": 250, "fail": 5}}
    with_11 = [{"R1": "INCONCLUSIVE", "rounds": [{"status": "INCONCLUSIVE", "row": 11}]}]
    with_10 = [{"R1": "INCONCLUSIVE", "rounds": [{"status": "INCONCLUSIVE", "row": 10}]}]
    assert ev.step_applies("INDETERMINATE", per, {"white": with_11}) is True
    assert ev.step_applies("INDETERMINATE", per, {"white": with_10}) is False
    assert ev.step_applies("FAIL", per, {"white": with_11}) is False
    ok = {"white": {"n": 360, "missing": 0, "pass": 300, "fail": 5}}
    assert ev.step_applies("INDETERMINATE", ok, {"white": with_11}) is False


def test_e9_the_sixteen_destinations(ev):
    P, F, I, O = "PASS", "FAIL", "INDETERMINATE", ev.CLOSURE  # noqa: E741
    want = {
        (P, P): (["C executable plan"], [], [], False),
        (P, F): (["C executable plan"], [], [], False),
        (P, I): (["C executable plan"], [], [], False),
        (F, F): ([], [], ["C", "D"], True),
        (F, P): (["D sizing proposal"], [], ["C"], False),
        (I, P): (["D sizing proposal"], ["C"], [], False),
        (F, I): ([], ["D"], ["C"], False),
        (I, F): ([], ["C"], ["D"], False),
        (I, I): ([], ["C", "D"], [], False),
        (O, P): (["D sizing proposal"], [], [], False),
        (O, F): ([], [], ["D"], False),
        (O, I): ([], ["D"], [], False),
        (P, O): (["C executable plan"], [], [], False),
        (F, O): ([], [], ["C"], False),
        (I, O): ([], ["C"], [], False),
        (O, O): ([], [], [], False),
    }
    assert len(want) == 16
    for (c, d), (proposals, step, abandoned, ends) in want.items():
        out = ev.destination(c, d)
        assert out["proposals"] == proposals and out["step_over"] == step, (c, d)
        assert out["abandoned"] == abandoned and out["ends"] is ends, (c, d)
        assert out["closures"] == [n for n, x in (("C", c), ("D", d)) if x == O]
