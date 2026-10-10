"""v0.2.1 H9(a) end to end: full analyses with a synthetic catalog (B1-B3), the
calibration evaluation (C1-C3) and the property over every scenario (D1-D2) of
docs/validation/v0.2.1/H9a-acceptance.md. Premises use the switch
``same_photometry_catalogs: []`` (the v0.2 behavior)."""

from types import SimpleNamespace

import pytest

from conftest import target_entry
from refute.core.runner import default_workers, run_processes
from refute.packs.tess import synthetic
from refute.packs.tess.calibration import TessCalibrator
from refute.packs.tess.params import TessTestPlan
from refute.packs.tess.pipeline import build_result
from refute.packs.tess.report import EB_CATALOG_DOWNGRADE_NOTE, render_report

SCENARIOS = (*synthetic.SCENARIOS, "fp_variability_dominates", "variability_train_only")
# Injected period of each scenario (the neighbor's for "blend"; an arbitrary fixed
# period where nothing periodic is injected).
PERIODS = {
    "planet": 3.7,
    "planet_three_years": 3.7,
    "noise": 3.7,
    "eb_secondary": 2.9,
    "eb_odd_even": 1.8,
    "eb_equal": 1.6,
    "vanishing": 3.7,
    "no_radius": 3.7,
    "single_year": 3.7,
    "blend": 2.3,
    "sinusoid": synthetic.SINUSOID_PERIOD,
    "fp_variability_dominates": synthetic.FP_VARIABILITY_PERIOD,
    "variability_train_only": 3.7,
}
ON, OFF = {}, {"same_photometry_catalogs": []}
SEEDS = tuple(range(10))


def _own(period):
    return f"TESS-EB,TIC 1 (1),1,{synthetic.TARGET_RA},{synthetic.TARGET_DEC},{period}"


def _neighbor(period):
    dec = synthetic.TARGET_DEC + 5.0 / 3600.0
    return f"TESS-EB,TIC 2 (1),2,{synthetic.TARGET_RA},{dec},{period}"


@pytest.fixture(scope="module")
def analyses():
    tasks = [
        {"name": n, "seed": s, "rows": [_own(PERIODS[n])], "eb_catalog": g, "tag": tag}
        for n in SCENARIOS
        for s in SEEDS
        for tag, g in (("on", ON), ("off", OFF))
    ]
    tasks += [
        {"name": "blend", "seed": s, "rows": [_neighbor(2.3)], "eb_catalog": ON, "tag": "nb"}
        for s in range(5)
    ]
    workers = max(1, min(len(tasks), default_workers()))
    results = run_processes(synthetic.analyze_scenario_with_catalog, tasks, workers)
    return {(t["name"], t["seed"], t["tag"]): r for t, r in zip(tasks, results, strict=True)}


def _test(analysis, name):
    return next(t for t in analysis.tests if t.name == name)


def _fatal_failures(analysis):
    return [
        t.name for t in analysis.tests if t.status.value == "FAIL" and t.severity.value == "fatal"
    ]


def _plan(guard):
    plan = synthetic.fast_plan_dict()
    plan["gauntlet"] = {"eb_catalog": guard}
    return TessTestPlan.model_validate(plan)


def _result(analyses, name, seed, tag, kind, tic):
    guard = OFF if tag == "off" else ON
    target = target_entry(tic, kind, PERIODS[name], name=f"{name} {seed}")
    context = {"pass_criteria": {"period_tolerance": 0.001}}
    data = synthetic.scenario_data(name, seed)
    return build_result(target, data, _plan(guard), analyses[(name, seed, tag)], context)


# --- B ------------------------------------------------------------------------------------


@pytest.mark.parametrize("seed", range(5))
def test_b1_planet_with_its_own_tess_eb_entry_is_weakened(analyses, seed):
    before, after = analyses[("planet", seed, "off")], analyses[("planet", seed, "on")]
    assert before.verdict == "REFUTED", f"premise: {before.verdict}"
    assert _fatal_failures(before) == ["eb_catalog"], f"premise: {_fatal_failures(before)}"
    assert after.verdict == "WEAKENED"
    eb = _test(after, "eb_catalog")
    assert eb.status.value == "FAIL" and eb.severity.value == "warning"
    assert eb.metrics["downgraded"] is True
    result = _result(analyses, "planet", seed, "on", "planet", 1)
    assert EB_CATALOG_DOWNGRADE_NOTE in render_report(result, {"claim_kind": "calibration"})
    unchanged = _result(analyses, "planet", seed, "off", "planet", 1)
    assert EB_CATALOG_DOWNGRADE_NOTE not in render_report(unchanged, {"claim_kind": "calibration"})


@pytest.mark.parametrize("seed", range(5))
@pytest.mark.parametrize("name", ["eb_secondary", "eb_odd_even"])
def test_b2_binaries_stay_refuted_by_their_data(analyses, name, seed):
    for tag in ("on", "off"):
        analysis = analyses[(name, seed, tag)]
        assert analysis.verdict == "REFUTED"
        assert set(_fatal_failures(analysis)) - {"eb_catalog"}, "a data test fails"


@pytest.mark.parametrize("seed", range(5))
def test_b3_neighbor_entry_at_the_period_stays_fatal(analyses, seed):
    analysis = analyses[("blend", seed, "nb")]
    assert analysis.gauntlet.candidate.period == pytest.approx(2.3, rel=1e-3), "premise"
    eb = _test(analysis, "eb_catalog")
    assert eb.status.value == "FAIL" and eb.severity.value == "fatal"
    assert eb.metrics["downgraded"] is False
    assert analysis.verdict == "REFUTED"


# --- C ------------------------------------------------------------------------------------


def _summary(results):
    criteria = {
        "period_tolerance": 0.001,
        "expected_planets": 5,
        "min_recovered_planets": 0,
        "expected_false_positives": 5,
        "min_flagged_false_positives": 0,
        "max_refuted_planets": 5,
        "flag_excluded_tests": ["eb_catalog"],
    }
    claim = SimpleNamespace(pass_criteria=criteria, id="c", hypothesis="h", definitions={})
    loaded = SimpleNamespace(claim=claim, attachment_by_role=lambda _role: None)
    return TessCalibrator().evaluate(loaded, results, complete=True)


def test_c_calibration_counts(analyses):
    summaries = {}
    for tag in ("on", "off"):
        planets = [_result(analyses, "planet", s, tag, "planet", 100 + s) for s in range(5)]
        fps = [
            _result(analyses, "eb_secondary", s, tag, "false_positive", 200 + s) for s in range(5)
        ]
        summaries[tag] = _summary(planets + fps)
    on, off = summaries["on"], summaries["off"]
    # C1: flagged false positives unchanged (eb_catalog is excluded from the count).
    assert on["self_claim"]["criteria"][1]["value"] == off["self_claim"]["criteria"][1]["value"]
    # C2: the degeneracy guard drops by exactly the five planets of B1.
    assert off["self_claim"]["criteria"][2]["value"] == 5
    assert on["self_claim"]["criteria"][2]["value"] == 0
    # C3: the planets are listed as downgraded, with the default only.
    downgraded = on["diagnostics"]["eb_catalog_downgraded"]
    assert {f"TIC-{100 + s}" for s in range(5)} <= set(downgraded)
    assert off["diagnostics"]["eb_catalog_downgraded"] == []
    markdown = TessCalibrator().summary_markdown(on)
    assert "eb_catalog downgraded" in markdown and "TIC-100" in markdown


# --- D ------------------------------------------------------------------------------------


@pytest.mark.parametrize("name", SCENARIOS)
def test_d_downgrade_never_refutes_and_changes_only_eb_catalog(analyses, name):
    for seed in SEEDS:
        on, off = analyses[(name, seed, "on")], analyses[(name, seed, "off")]
        # D1
        if on.verdict == "REFUTED":
            assert off.verdict == "REFUTED", (name, seed)
        # D2
        assert [t.name for t in on.tests] == [t.name for t in off.tests]
        for a, b in zip(on.tests, off.tests, strict=True):
            assert a.status is b.status, (name, seed, a.name)
            if a.name == "eb_catalog" and a.severity is not b.severity:
                assert (b.severity.value, a.severity.value) == ("fatal", "warning")
            else:
                assert a.severity is b.severity, (name, seed, a.name)
        if on.verdict != off.verdict:
            assert _fatal_failures(off) == ["eb_catalog"], (name, seed, _fatal_failures(off))
        eb = _test(on, "eb_catalog")
        if eb.status.value == "FAIL":
            assert on.verdict != "SURVIVED", (name, seed)
