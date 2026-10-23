"""The generator population_v4 (plan B, section 3; its acceptance record
docs/validation/v0.2.1/population/population-v4-acceptance.md): the population and its layouts'
allocation, the layouts and their rejection, the built cases, the independent band check, the
replay of the attempts, the correspondence with X2f, the import boundaries and the order check.
Synthetic data only; no network; no engine run."""

from __future__ import annotations

import ast
import hashlib
import importlib
import json
import math
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
POPULATION = ROOT / "docs" / "validation" / "v0.2.1" / "population"
V2_SHA256 = "8b3b6ad6aca6e713636b04e40db5a7d253c05458c8b143c38d984100072c1f82"
V3_SHA256 = "3620cca07e7e8389f23710f724d68f362c973ff469b3f6a96e282565f2183787"
DT = 120.0 / 86400.0
SEC = 1.0 / 86400.0


def _module(name: str):
    if str(POPULATION) not in sys.path:
        sys.path.insert(0, str(POPULATION))
    return importlib.import_module(name)


@pytest.fixture(scope="module")
def v4():
    return _module("population_v4")


@pytest.fixture(scope="module")
def v2(v4):
    return v4.pv2


@pytest.fixture(scope="module")
def chk():
    return _module("population_v4_check")


@pytest.fixture(scope="module")
def band():
    return _module("band_check_v4")


@pytest.fixture(scope="module")
def cases(v4):
    return v4.population_cases("acceptance")


def _first(cases, **want):
    for c in cases:
        if all(
            (c["extra"].get(k) if k in ("geometry", "order") else c[k]) == v
            for k, v in want.items()
        ):
            return c
    raise LookupError(want)


def _reserialized(v2, meta, arrays):
    index = meta.pop("arrays")
    return v2.serialize(meta, [(name, arrays[name], dtype) for name, dtype, _ in index])


# --- the frozen generators -----------------------------------------------------------------------


def test_population_v2_and_v3_are_unchanged(v4):
    for name, digest in (("population_v2.py", V2_SHA256), ("population_v3.py", V3_SHA256)):
        assert hashlib.sha256((POPULATION / name).read_bytes()).hexdigest() == digest, name
    assert v4.V2_SHA256 == V2_SHA256


def test_v4_reuses_v2_objects(v4, v2):
    for name in ("draw_parameters", "_place_in_band", "_noise", "_mechanism_condition", "sub_seed"):
        assert getattr(v4, name) is getattr(v2, name)
    assert v4.BANDS is v2.BANDS and v4.DEPTH_LIMITS is v2.DEPTH_LIMITS
    assert v2.NOISE_PPM == 600.0 and v2.AR_PPM == 600.0


# --- the population (criterion 4) and the allocation (criterion 3) -------------------------------


def test_the_population_composition(cases, v4, v2, chk):
    assert len(cases) == 5860 and len({c["id"] for c in cases}) == 5860
    assert Counter(c["noise"] for c in cases) == {"white": 3730, "correlated": 2130}
    count = Counter((c["class"], c["noise"], c["band"], c["mechanism"]) for c in cases)
    for noise in ("white", "correlated"):
        for b in ("below", "near", "measurable"):
            assert count[("planet", noise, b, "three_years")] == 180
            assert count[("planet", noise, b, "variability_some_years")] == 180
        for b, n in (("below", 100), ("near", 100), ("measurable", 250)):
            got = [count[("false_positive", noise, b, m)] for m in v2.FP_MECHANISMS]
            assert got == ([63, 63, 62, 62] if n == 250 else [25, 25, 25, 25])
    nt = {
        n: [count[("no_transit", n, None, m)] for m in v2.NOTRANSIT_MECHANISMS]
        for n in ("white", "correlated")
    }
    assert nt == {"white": [880, 660, 660], "correlated": [240, 180, 180]}
    for c in cases:
        tag = c["band"] or "none"
        assert c["seed"] == str(
            v2.case_seed(v4.ACCEPTANCE_PREFIX, c["class"], tag, c["noise"], c["index"])
        )
        if c["class"] == "no_transit":
            assert c["catalog_variant"] is None
        else:
            assert c["catalog_variant"] == v2.CATALOG_VARIANTS[c["index"] % 5]
    assert chk.composition_problems(cases) == []
    assert chk.composition_problems(cases[:-1]) != []


def test_the_allocation_is_exact(cases, chk):
    geo = Counter(
        (c["class"], c["noise"], c["band"], c["extra"]["geometry"], c["extra"].get("order"))
        for c in cases
    )
    for noise in ("white", "correlated"):
        fp = ("false_positive", noise, "measurable")
        assert geo[(*fp, "G-a", None)] == 126
        assert geo[(*fp, "G-b", "short-long")] == 64  # 16 in each mechanism's group
        assert geo[(*fp, "G-b", "long-short")] == 60  # 15 in each
        pl = ("planet", noise, "near")
        assert geo[(*pl, "G-a", None)] == 180
        assert geo[(*pl, "G-b", "short-long")] == geo[(*pl, "G-b", "long-short")] == 90
    assert chk.allocation_problems(cases) == []
    broken = [dict(c, extra=dict(c["extra"])) for c in cases]
    broken[0]["extra"] = {"geometry": "G-b", "order": "short-long"}
    assert chk.allocation_problems(broken) != []


def test_the_geometry_follows_the_position_in_the_group(cases, v4):
    rows = [
        c
        for c in cases
        if c["class"] == "false_positive"
        and c["noise"] == "white"
        and c["band"] == "measurable"
        and c["mechanism"] == "eb_odd_even"
    ]
    assert len(rows) == 63
    for j, c in enumerate(rows):
        assert c["extra"] == v4.geometry_of(j)
    assert v4.geometry_of(0) == {"geometry": "G-a"}
    assert v4.geometry_of(1) == {"geometry": "G-b", "order": "short-long"}
    assert v4.geometry_of(2) == {"geometry": "G-a"}
    assert v4.geometry_of(3) == {"geometry": "G-b", "order": "long-short"}


def test_other_populations(v4):
    small = v4.population_cases("selftest")
    assert 0 < len(small) < 400
    assert {c["class"] for c in small} == {"planet", "false_positive", "no_transit"}
    assert {c["extra"]["geometry"] for c in small} == {"G-a", "G-b"}
    named = v4.population_cases("prefix:refute-test-prefix")
    assert len(named) == 5860
    assert named[0]["seed"] != v4.population_cases("acceptance")[0]["seed"]
    with pytest.raises(SystemExit):
        v4.population_cases("dev")


# --- the layouts (criteria 1, 2 and 3) -----------------------------------------------------------


@pytest.fixture(scope="module")
def some_layouts(cases, v4):
    picked = []
    for cls in ("planet", "false_positive", "no_transit"):
        for noise in ("white", "correlated"):
            for geometry, order in (("G-a", None), ("G-b", "short-long"), ("G-b", "long-short")):
                want = {"class": cls, "noise": noise, "geometry": geometry}
                if order:
                    want["order"] = order
                picked.append(_first(cases, **want))
    return [(c, v4.draw_layout(c)) for c in picked]


def test_layouts_are_inside_and_deterministic(some_layouts, v4):
    for case, lay in some_layouts:
        assert lay["domain"].inside, (case["id"], lay["domain"].reason)
        again = v4.draw_layout(case)
        assert again["attempt"] == lay["attempt"] and again["draws"] == lay["draws"]
        for a, b in zip(lay["times"], again["times"], strict=True):
            assert np.array_equal(a, b)


def test_the_layout_stream(some_layouts, v4, v2):
    case, lay = some_layouts[0]
    rng = np.random.default_rng(v2.sub_seed(int(case["seed"]), "layout", lay["attempt"]))
    assert lay["draws"]["first_start"] == 1325.0 + 365.25 * rng.uniform()
    assert v4.LAYOUT_STREAM == "layout"


def test_the_layout_draws_and_the_geometry(some_layouts):
    for case, lay in some_layouts:
        d = lay["draws"]
        assert 1325.0 <= d["first_start"] < 1325.0 + 365.25
        sep = d["separations"]
        long_ = [710.0 <= s < 750.0 for s in sep]
        short = [345.0 <= s < 385.0 for s in sep]
        assert all(a != b for a, b in zip(long_, short, strict=True))
        g = case["extra"]
        if g["geometry"] == "G-a":
            assert short == [True, True]
        else:
            assert long_ == ([False, True] if g["order"] == "short-long" else [True, False])
        assert lay["domain"].separations_days == pytest.approx(sep, abs=1e-5)
        for s in d["sectors"]:
            assert all(12.5 <= x < 14.0 for x in s["orbit_days"])
            assert 0.5 <= s["orbit_gap_days"] < 2.0
            assert 0 <= len(s["blocks"]) <= 4
            for b in s["blocks"]:
                assert 600.0 <= b["seconds"] < 21600.0 and 0.0 <= b["place"] < 1.0
                assert b["removed"] == math.floor(b["seconds"] / 120.0)
            assert 0.0 <= s["loss_rate"] < 0.05


def test_the_time_stamps_follow_the_rules(some_layouts):
    for _case, lay in some_layouts:
        for t, s, jit in zip(lay["times"], lay["draws"]["sectors"], lay["jitter_s"], strict=True):
            assert t.size == jit.size and np.all(jit >= -0.25) and np.all(jit < 0.25)
            n1, n2 = round(s["orbit_days"][0] / DT), round(s["orbit_days"][1] / DT)
            assert s["n_nominal"] == n1 + n2
            assert t.size == n1 + n2 - s["n_lost_blocks"] - s["n_lost_single"]
            assert s["n_lost_single"] <= s["n_eligible"]
        for sec in lay["domain"].sectors:
            n_intervals = sum(sec.k_counts.values()) + len(sec.other_gaps_seconds) + 1
            assert n_intervals == sec.n_kept - 1
            assert all(g >= 720.0 - 0.5 for g in sec.other_gaps_seconds)


def test_the_orbits_ends_are_kept(some_layouts):
    for _case, lay in some_layouts:
        for t, s in zip(lay["times"], lay["draws"]["sectors"], strict=True):
            n1, n2 = round(s["orbit_days"][0] / DT), round(s["orbit_days"][1] / DT)
            first_last = s["start"] + (n1 - 1) * DT
            second_first = first_last + s["orbit_gap_days"]
            second_last = second_first + (n2 - 1) * DT
            for nominal in (s["start"], first_last, second_first, second_last):
                assert np.min(np.abs(t - nominal)) <= 0.25 * SEC + 1e-9


def test_blocks_and_single_losses_on_a_constructed_layout(v4):
    sectors = [
        {
            "orbit_days": (13.0, 13.0),
            "orbit_gap_days": 1.0,
            "blocks": [{"seconds": 3600.0, "place": 0.25}, {"seconds": 600.0, "place": 0.75}],
            "loss_rate": 0.04,
        }
    ] * 3
    built = v4.layout_from_draws(
        first_start=1325.0, separations=(370.0, 370.0), sectors=sectors, seed=7
    )
    result = v4.domain.check_domain(built["times"])
    assert result.inside, result.reason
    for sec in result.sectors:
        assert sorted(round(g) for g in sec.other_gaps_seconds) == [720, 3720]
        assert sec.k_counts[2] > 0


def test_the_rejection_draws_again_and_records_the_reason(v4, cases, monkeypatch):
    case = _first(cases, **{"class": "no_transit", "noise": "white"})
    real = v4.domain.check_domain
    calls = {"n": 0}

    def fails_twice(sectors):
        calls["n"] += 1
        result = real(sectors)
        if calls["n"] <= 2:
            return v4.domain.DomainResult(
                inside=False,
                failed="D1",
                reason="D1: forced by the test",
                conditions={**result.conditions, "D1": False},
                sectors=result.sectors,
                separations_days=result.separations_days,
            )
        return result

    monkeypatch.setattr(v4.domain, "check_domain", fails_twice)
    lay = v4.draw_layout(case)
    assert lay["attempt"] == 2 and lay["redraws"] == {"layout:D1": 2}


def test_a_label_collision_is_rejected(v4):
    sector = {"orbit_days": (13.0, 13.0), "orbit_gap_days": 1.0, "blocks": [], "loss_rate": 0.0}
    # BTJD 1486.5 is 2019-01-03; 345 d later is still 2019
    built = v4.layout_from_draws(
        first_start=1486.5, separations=(345.0, 365.0), sectors=[sector] * 3, seed=1
    )
    assert v4.domain.check_domain(built["times"]).failed == "D1"


# --- the built cases (criteria 1, 4, 5 and 6) ----------------------------------------------------


@pytest.fixture(scope="module")
def built(cases, v4):
    picks = [
        _first(
            cases,
            **{
                "class": "planet",
                "mechanism": "variability_some_years",
                "noise": "correlated",
                "geometry": "G-b",
            },
        ),
        _first(cases, **{"class": "false_positive", "mechanism": "blend", "noise": "white"}),
        _first(
            cases,
            **{
                "class": "false_positive",
                "mechanism": "eb_secondary",
                "noise": "correlated",
                "band": "below",
            },
        ),
        _first(
            cases, **{"class": "no_transit", "mechanism": "trend_variability", "noise": "white"}
        ),
        _first(cases, **{"class": "planet", "mechanism": "three_years", "noise": "white"}),
    ]
    return [(c, *v4.build_case(c)) for c in picks]


def test_built_time_stamps_are_the_layouts(built, v4, v2):
    for case, blob, entry in built:
        meta, arrays = v2.deserialize(blob)
        lay = v4.draw_layout(case)
        for k, t in enumerate(lay["times"]):
            sel = arrays["lc/sector"] == k + 1
            assert np.array_equal(arrays["lc/time"][sel], t)
            assert np.all(arrays["lc/year"][sel] == lay["domain"].sectors[k].label)
        assert meta["generator"] == "refute-population-v4/1"
        assert meta["domain"]["inside"] is True
        assert entry["redraws"] == meta["redraws"]


def test_built_cases_are_deterministic(built, v4):
    case, blob, _ = built[3]
    assert v4.build_case(case)[0] == blob


def test_the_variability_free_year_is_one_of_the_curve(built, v2):
    _case, blob, _ = built[0]
    meta, _ = v2.deserialize(blob)
    p = meta["parameters"]
    labels = [s["year"] for s in meta["data"]["sectors"]]
    assert len(set(labels)) == 3
    assert p["var_absent_year"] == labels[p["var_absent_position"]]


def test_the_built_checks_pass(built, chk):
    for case, blob, _ in built:
        report = chk.built_report(case, blob)
        assert report["problems"] == [], (case["id"], report["problems"])
        assert report["replayed_attempts"] >= 1 and report["cadences"] > 0


def test_the_replay_catches_an_undeclared_redraw(built, chk, v2):
    case, blob, _ = built[4]
    meta, arrays = v2.deserialize(blob)
    meta["redraws"] = {**meta["redraws"], "band": meta["redraws"].get("band", 0) + 1}
    assert chk.built_report(case, _reserialized(v2, meta, arrays))["problems"] != []


def test_the_replay_catches_a_changed_parameter(built, chk, v2):
    case, blob, _ = built[4]
    meta, arrays = v2.deserialize(blob)
    meta["parameters"]["impact"] = meta["parameters"]["impact"] * 0.5
    assert chk.built_report(case, _reserialized(v2, meta, arrays))["problems"] != []


def test_the_independent_band_check_passes(built, band):
    for case, blob, _ in built:
        report = band.check(blob)
        assert report["problems"] == [], (case["id"], report["problems"])
        if case["class"] == "no_transit":
            assert report["snr_checked"] == 0
        else:
            assert report["snr_checked"] > 0
        if case["mechanism"] != "blend":
            assert report["flux_checked"] > 0


def test_the_band_check_catches_a_wrong_snr(built, band, v2):
    _case, blob, _ = built[2]
    meta, arrays = v2.deserialize(blob)
    meta["expected_snr"]["global"] *= 1.0 + 1e-6
    assert band.check(_reserialized(v2, meta, arrays))["problems"] != []


def test_the_band_check_catches_a_hidden_transit(built, band, v2):
    _case, blob, _ = built[3]
    meta, arrays = v2.deserialize(blob)
    flux = arrays["lc/flux"].copy()
    flux[1000:1060] -= 1000e-6
    arrays["lc/flux"] = flux
    assert band.check(_reserialized(v2, meta, arrays))["problems"] != []


def test_the_band_check_catches_variability_in_three_years(built, band, v2):
    _case, blob, _ = built[0]
    meta, arrays = v2.deserialize(blob)
    labels = [s["year"] for s in meta["data"]["sectors"]]
    others = [y for y in (2018, 2019, 2020) if y not in labels] or [1999]
    meta["parameters"]["var_absent_year"] = others[0]
    assert band.check(_reserialized(v2, meta, arrays))["problems"] != []


# --- X2f (criterion 8) ---------------------------------------------------------------------------


def test_the_x2f_cases_are_one_point_of_the_domain(chk):
    report = chk.x2f_report()
    assert report["problems"] == []
    assert report["geometry"] == "G-a"
    assert report["separations_days"] == pytest.approx([375.0, 361.0], abs=1e-9)
    assert report["coverage"] == pytest.approx([0.963] * 3, abs=0.001)


# --- the checks need data (criterion 2) ----------------------------------------------------------


def test_zero_coverage_is_a_failure(chk):
    assert chk.domain_problems([]) != []
    assert chk.coverage_problems([]) != []
    assert chk.allocation_problems([]) != []
    assert chk.composition_problems([]) != []


def test_coverage_catches_a_narrow_dimension(some_layouts, chk):
    records = [chk.layout_record(c, lay) for c, lay in some_layouts]
    narrowed = json.loads(json.dumps(records))
    for r in narrowed:
        r["draws"]["first_start"] = 1326.0
    assert any("first_start" in p for p in chk.coverage_problems(narrowed))


# --- the import boundaries (criteria 5 and 6) ----------------------------------------------------


def _imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            names += [f"{node.module}.{a.name}" for a in node.names]
    return names


def test_band_check_imports_only_the_standard_library_and_numpy():
    for name in _imports(POPULATION / "band_check_v4.py"):
        root = name.split(".")[0]
        assert root == "numpy" or root in sys.stdlib_module_names, name


def test_v4_imports_from_refute_only_the_data_modules():
    allowed = {f"refute.packs.tess.{m}" for m in ("synthetic", "params", "types", "domain")}
    found = [n for n in _imports(POPULATION / "population_v4.py") if n.startswith("refute")]
    assert found and all(any(n.startswith(a) for a in allowed) for n in found), found


def test_v4_reads_only_declared_attributes(chk):
    assert chk.source_problems() == []


def test_redraw_reasons_are_declared(v4):
    assert set(v4.REDRAW_REASONS) == {
        "layout:D1",
        "layout:D2",
        "layout:D3",
        "layout:D4",
        "layout:D5",
        "band",
        "depth_limit",
        "no_transit_in_a_year",
        "commensurate_periods",
    }
    assert math.isclose(v4.FIRST_START, 1325.0) and math.isclose(v4.ONE_YEAR_DAYS, 365.25)


# --- the order (criterion 9) ---------------------------------------------------------------------


def test_the_order_check_rejects_an_invalid_history(chk):
    good = [
        ("a", ["docs/validation/v0.2.1/population/population-v4-acceptance.md"]),
        ("b", ["tests/test_domain.py", "tests/test_population_v4.py"]),
        (
            "c",
            [
                "src/refute/packs/tess/domain.py",
                "docs/validation/v0.2.1/population/population_v4.py",
            ],
        ),
    ]
    assert chk.order_problems(good) == []
    assert chk.order_problems([good[0], good[2], good[1]]) != []
    assert chk.order_problems([good[1], good[0], good[2]]) != []
    assert chk.order_problems([good[0], good[2]]) != []


def test_the_first_run_record_must_show_every_test_failing(chk):
    committed = (POPULATION / "v4-acceptance" / "first-run.json").read_text(encoding="utf-8")
    assert chk.first_run_problems(committed) == []
    record = json.loads(committed)
    record["runs"][1]["counts"]["passed"] = 1
    assert chk.first_run_problems(json.dumps(record)) != []
    assert chk.first_run_problems(json.dumps({"runs": []})) != []
    assert chk.first_run_problems(None) != []


def test_the_sabotages_output_must_record_each_caught(chk):
    ok = {
        "all_caught": True,
        "sabotages": [
            {"id": s, "caught": True, "control": {"passed": True, "coverage": 1}}
            for s in chk.SABOTAGE_IDS
        ],
    }
    assert chk.sabotage_output_problems(json.dumps(ok)) == []
    missing = dict(ok, sabotages=ok["sabotages"][:-1])
    assert chk.sabotage_output_problems(json.dumps(missing)) != []
    uncaught = json.loads(json.dumps(ok))
    uncaught["sabotages"][0]["caught"] = False
    assert chk.sabotage_output_problems(json.dumps(uncaught)) != []
    assert chk.sabotage_output_problems(None) != []


# --- review fixes (Codex, 610bc02) ---------------------------------------------------------------


def test_the_serialized_case_must_be_the_declared_case(built, chk, v2):
    case, blob, _ = built[4]
    meta, arrays = v2.deserialize(blob)
    meta["case"]["class"] = "false_positive"
    report = chk.built_report(case, _reserialized(v2, meta, arrays))
    assert any(p.startswith("[4] the serialized case") for p in report["problems"])


def test_determinism_rejects_thin_or_unbound_manifests(chk, tmp_path):
    for g in ("1", "2", "3"):
        manifest = {"population": "acceptance", "cases": {"x": "not-a-sha256"}}
        (tmp_path / f"manifest-{g}.json").write_text(json.dumps(manifest), encoding="utf-8")
        run = {"population": "acceptance", "cases": 1, "workers": 1, "order": "index",
               "checks": {"a": {"passed": True}}, "manifest_sha256": "0" * 64}  # fmt: skip
        (tmp_path / f"population-{g}.json").write_text(json.dumps(run), encoding="utf-8")
    _, problems = chk.determinism_problems(tmp_path)
    text = " ".join(problems)
    for expected in ("does not name this manifest", "cases, the 5860", "not SHA-256",
                     "worker counts", "orders"):  # fmt: skip
        assert expected in text, expected
    assert chk.determinism_problems(tmp_path / "absent")[1] != []


def test_the_band_check_cli_needs_a_case(band, capsys):
    assert band.main([]) == 2


def test_the_sabotage_errors_keep_no_path_or_host():
    sab = _module("population_v4_sabotage")
    import socket

    host = socket.gethostname()
    err = (
        'Traceback\n  File "C:\\Users\\someone\\x.py"\n'
        f"FileNotFoundError: [Errno 2] '\\\\{host}\\share\\dir\\case.bin' and "
        "'C:\\Users\\Jane Doe\\a.json'"
    )
    assert sab._error_line(err, 1) == "FileNotFoundError (exit 1)"
    assert sab._error_line("") == "no output"


def test_determinism_needs_every_check_with_its_coverage(chk, tmp_path, v4):
    ids = {c["id"]: "a" * 64 for c in v4.population_cases("acceptance")}
    runs = ((1, "index"), (2, "reverse"), (3, "interleaved"))
    for g, (workers, order) in zip("123", runs, strict=True):
        blob = json.dumps({"population": "acceptance", "cases": ids}).encode()
        (tmp_path / f"manifest-{g}.json").write_bytes(blob)
        unrelated = {"unrelated": {"passed": True, "coverage": 0, "required": 5860}}
        digest = hashlib.sha256(blob).hexdigest()
        run = {"population": "acceptance", "cases": len(ids), "workers": workers, "order": order,
               "manifest_sha256": digest, "checks": unrelated}  # fmt: skip
        (tmp_path / f"population-{g}.json").write_text(json.dumps(run), encoding="utf-8")
    problems = chk.determinism_problems(tmp_path)[1]
    assert any("required" in p for p in problems)
    assert any("with its coverage" in p for p in problems)


def test_the_sabotages_controls_need_coverage(chk):
    out = {
        "all_caught": True,
        "sabotages": [
            {"id": s, "caught": True, "control": {"passed": True, "coverage": 0}}
            for s in chk.SABOTAGE_IDS
        ],
    }
    assert any("coverage" in p for p in chk.sabotage_output_problems(json.dumps(out)))


def test_the_layout_draw_order(v4, v2, cases):
    """The draws in the record's order (section 2.2), from the layout stream, by hand."""
    case = _first(cases, **{"class": "false_positive", "geometry": "G-b", "order": "long-short"})
    lay = v4.draw_layout(case)
    rng = np.random.default_rng(v2.sub_seed(int(case["seed"]), "layout", lay["attempt"]))
    d = lay["draws"]
    assert d["first_start"] == 1325.0 + 365.25 * rng.uniform()
    assert d["separations"] == [rng.uniform(710.0, 750.0), rng.uniform(345.0, 385.0)]
    for s, jit in zip(d["sectors"], lay["jitter_s"], strict=True):
        l1, gap, l2 = rng.uniform(12.5, 14.0), rng.uniform(0.5, 2.0), rng.uniform(12.5, 14.0)
        assert s["orbit_days"] == [l1, l2] and s["orbit_gap_days"] == gap
        n_blocks = int(rng.integers(0, 5))
        assert len(s["blocks"]) == n_blocks
        for b in s["blocks"]:
            assert (b["seconds"], b["place"]) == (rng.uniform(600.0, 21600.0), rng.uniform())
        assert s["loss_rate"] == rng.uniform(0.0, 0.05)
        n = round(l1 / DT) + round(l2 / DT)
        losses = rng.uniform(size=n)
        jitter = rng.uniform(-0.25, 0.25, size=n)
        assert s["n_nominal"] == n
        assert (
            np.isin(jit, jitter).all() and jit.size == n - s["n_lost_blocks"] - s["n_lost_single"]
        )
        eligible_losses = int(np.count_nonzero(losses < s["loss_rate"]))
        assert s["n_lost_single"] <= eligible_losses
