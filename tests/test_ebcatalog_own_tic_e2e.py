"""v0.2.1 H9(a) end to end: full analyses with a synthetic catalog (B1-B3), the
calibration evaluation (C1-C3) and the property over every scenario (D1-D2) of
docs/validation/v0.2.1/H9a-acceptance.md. Premises use the switch
``same_photometry_catalogs: []`` (the v0.2 behavior). Cases E0-E1 check the shared
path of option D (docs/validation/v0.2.1/ci-time-option-d-acceptance.md): the
switch-off analyses derived from the default-rule ones equal complete ones."""

from types import SimpleNamespace

import pytest

from conftest import target_entry
from refute.core.io import dumps_json
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
CONTROL_SEEDS = (0, 1)


def _own(period):
    return f"TESS-EB,TIC 1 (1),1,{synthetic.TARGET_RA},{synthetic.TARGET_DEC},{period}"


def _neighbor(period):
    dec = synthetic.TARGET_DEC + 5.0 / 3600.0
    return f"TESS-EB,TIC 2 (1),2,{synthetic.TARGET_RA},{dec},{period}"


@pytest.fixture(scope="module")
def analyses():
    # Option D (docs/validation/v0.2.1/ci-time-option-d-acceptance.md): one complete
    # analysis with the default rule per scenario and seed, from which the switch-off
    # analysis is derived; complete switch-off controls on seeds 0-1 only (E1); the five
    # neighbor-row blends stay complete. 130 + 26 + 5 = 161 complete analyses.
    shared = [
        {
            "name": n,
            "seed": s,
            "rows": [_own(PERIODS[n])],
            "eb_catalog": ON,
            "derived_eb_catalog": OFF,
        }
        for n in SCENARIOS
        for s in SEEDS
    ]
    complete = [
        {"name": n, "seed": s, "rows": [_own(PERIODS[n])], "eb_catalog": OFF, "tag": "off_complete"}
        for n in SCENARIOS
        for s in CONTROL_SEEDS
    ]
    complete += [
        {"name": "blend", "seed": s, "rows": [_neighbor(2.3)], "eb_catalog": ON, "tag": "nb"}
        for s in range(5)
    ]
    workers = max(1, min(len(shared), default_workers()))
    pairs = run_processes(synthetic.analyze_scenario_with_catalog_shared, shared, workers)
    singles = run_processes(synthetic.analyze_scenario_with_catalog, complete, workers)
    out = {}
    for task, (on, off) in zip(shared, pairs, strict=True):
        out[(task["name"], task["seed"], "on")] = on
        out[(task["name"], task["seed"], "off")] = off
    for task, analysis in zip(complete, singles, strict=True):
        out[(task["name"], task["seed"], task["tag"])] = analysis
    return out


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


# --- E (option D: docs/validation/v0.2.1/ci-time-option-d-acceptance.md) ----------------


def _shared(analysis):
    return analysis.extras.get("shared_path") is True


def _record(analysis, name, seed):
    target = target_entry(1, "planet", PERIODS[name], name=f"{name} {seed}")
    context = {"pass_criteria": {"period_tolerance": 0.001}}
    data = synthetic.scenario_data(name, seed)
    return dumps_json(build_result(target, data, _plan(OFF), analysis, context))


def _gauntlet_tests(analysis):
    return dumps_json([t.to_dict() for t in analysis.gauntlet.tests])


def test_e0_switch_off_analyses_come_from_the_shared_path(analyses):
    for name in SCENARIOS:
        for seed in SEEDS:
            assert _shared(analyses[(name, seed, "off")]), (name, seed, "off is not derived")
            assert not _shared(analyses[(name, seed, "on")]), (name, seed, "on is derived")
            control = analyses.get((name, seed, "off_complete"))
            if seed in CONTROL_SEEDS:
                assert control is not None and not _shared(control), (name, seed, "control")
            else:
                assert control is None, (name, seed, "unexpected control")
    complete = {id(a) for a in analyses.values() if not _shared(a)}
    assert len(complete) == 161


@pytest.mark.parametrize("name", SCENARIOS)
def test_e1_shared_path_equals_the_complete_switch_off_analysis(analyses, name):
    for seed in CONTROL_SEEDS:
        complete = analyses.get((name, seed, "off_complete"))
        assert complete is not None, (seed, "no complete switch-off control")
        derived = analyses[(name, seed, "off")]
        assert _shared(derived), (seed, "the switch-off analysis is not derived")
        assert _record(derived, name, seed) == _record(complete, name, seed), seed
        assert _gauntlet_tests(derived) == _gauntlet_tests(complete), seed


@pytest.mark.parametrize("seed", CONTROL_SEEDS)
def test_e1_premise_the_switch_changes_the_planet_analysis(analyses, seed):
    on, off = analyses[("planet", seed, "on")], analyses[("planet", seed, "off")]
    assert _shared(off), "the switch-off analysis is not derived"
    assert (on.verdict, off.verdict) == ("WEAKENED", "REFUTED")
    assert _test(on, "eb_catalog").severity.value == "warning"
    eb_off = _test(off, "eb_catalog")
    assert (eb_off.status.value, eb_off.severity.value) == ("FAIL", "fatal")
    assert eb_off.metrics["downgraded"] is False


# --- Correlated noise (docs/validation/v0.2.1/reopen/correlated-noise-acceptance.md, H9, D) ---

CN_SEEDS = tuple(range(5))
CN_CONTROLS = ("planet", "eb_secondary")


@pytest.fixture(scope="module")
def correlated():
    shared = [
        {
            "name": n,
            "seed": s,
            "rows": [_own(PERIODS[n])],
            "eb_catalog": ON,
            "derived_eb_catalog": OFF,
            "noise": "correlated",
        }
        for n in SCENARIOS
        for s in CN_SEEDS
    ]
    complete = [
        {
            "name": n,
            "seed": s,
            "rows": [_own(PERIODS[n])],
            "eb_catalog": OFF,
            "noise": "correlated",
            "tag": "off_complete",
        }
        for n in CN_CONTROLS
        for s in CONTROL_SEEDS
    ]
    complete += [
        {
            "name": "blend",
            "seed": s,
            "rows": [_neighbor(2.3)],
            "eb_catalog": ON,
            "noise": "correlated",
            "tag": "nb",
        }
        for s in CN_SEEDS
    ]
    workers = max(1, min(len(shared), default_workers()))
    pairs = run_processes(synthetic.analyze_scenario_with_catalog_shared, shared, workers)
    singles = run_processes(synthetic.analyze_scenario_with_catalog, complete, workers)
    out = {}
    for task, (on, off) in zip(shared, pairs, strict=True):
        out[(task["name"], task["seed"], "on")] = on
        out[(task["name"], task["seed"], "off")] = off
    for task, analysis in zip(complete, singles, strict=True):
        out[(task["name"], task["seed"], task["tag"])] = analysis
    return out


@pytest.mark.parametrize("name", SCENARIOS)
def test_cn_h9_m1_downgrade_never_refutes_and_changes_only_eb_catalog(correlated, name):
    for seed in CN_SEEDS:
        on, off = correlated[(name, seed, "on")], correlated[(name, seed, "off")]
        if on.verdict == "REFUTED":
            assert off.verdict == "REFUTED", seed
        assert [t.name for t in on.tests] == [t.name for t in off.tests]
        for a, b in zip(on.tests, off.tests, strict=True):
            assert a.status is b.status, (seed, a.name)
            if a.name == "eb_catalog" and a.severity is not b.severity:
                assert (b.severity.value, a.severity.value) == ("fatal", "warning")
            else:
                assert a.severity is b.severity, (seed, a.name)
        if on.verdict != off.verdict:
            assert _fatal_failures(off) == ["eb_catalog"], (seed, _fatal_failures(off))
            assert on.verdict != "SURVIVED", seed


def _cn_b1_premise(correlated, seed):
    before = correlated[("planet", seed, "off")]
    return before.verdict == "REFUTED" and _fatal_failures(before) == ["eb_catalog"]


def test_cn_h9_m2_own_tic_entry_is_downgraded(correlated):
    looked = 0
    for seed in CN_SEEDS:
        if not _cn_b1_premise(correlated, seed):
            continue
        looked += 1
        after = correlated[("planet", seed, "on")]
        assert after.verdict not in ("REFUTED", "SURVIVED"), (seed, after.verdict)
        eb = _test(after, "eb_catalog")
        assert eb.status.value == "FAIL" and eb.severity.value == "warning", seed
        assert eb.metrics["downgraded"] is True, seed
        target = target_entry(1, "planet", PERIODS["planet"], name=f"planet {seed}")
        context = {"pass_criteria": {"period_tolerance": 0.001}}
        data = synthetic.scenario_data("planet", seed, "correlated")
        result = build_result(target, data, _plan(ON), after, context)
        assert EB_CATALOG_DOWNGRADE_NOTE in render_report(result, {"claim_kind": "calibration"})
    assert looked >= 1, "non-empty: the premise holds on no seed"


def _cn_b3_premise(correlated, seed):
    candidate = correlated[("blend", seed, "nb")].gauntlet.candidate
    return candidate is not None and candidate.period == pytest.approx(2.3, rel=1e-3)


def test_cn_h9_m3_neighbor_entry_at_the_period_stays_fatal(correlated):
    looked = 0
    for seed in CN_SEEDS:
        if not _cn_b3_premise(correlated, seed):
            continue
        looked += 1
        analysis = correlated[("blend", seed, "nb")]
        eb = _test(analysis, "eb_catalog")
        assert eb.status.value == "FAIL" and eb.severity.value == "fatal", seed
        assert eb.metrics["downgraded"] is False, seed
        assert analysis.verdict == "REFUTED", seed
    assert looked >= 1, "non-empty: the premise holds on no seed"


@pytest.mark.parametrize("seed", CN_SEEDS)
def test_cn_h9_e1_premise_planet_refuted_only_by_its_own_entry(correlated, seed):
    before = correlated[("planet", seed, "off")]
    assert _cn_b1_premise(correlated, seed), (before.verdict, _fatal_failures(before))


@pytest.mark.parametrize("seed", CN_SEEDS)
def test_cn_h9_e1_premise_blend_found_at_the_neighbor_period(correlated, seed):
    candidate = correlated[("blend", seed, "nb")].gauntlet.candidate
    assert _cn_b3_premise(correlated, seed), candidate


@pytest.mark.parametrize("seed", CN_SEEDS)
@pytest.mark.parametrize("name", ["eb_secondary", "eb_odd_even"])
def test_cn_h9_e2_binaries_stay_refuted_by_their_data(correlated, name, seed):
    for tag in ("on", "off"):
        analysis = correlated[(name, seed, tag)]
        assert analysis.verdict == "REFUTED", tag
        assert set(_fatal_failures(analysis)) - {"eb_catalog"}, "a data test fails"


def _cn_record(analysis, name, seed):
    target = target_entry(1, "planet", PERIODS[name], name=f"{name} {seed}")
    context = {"pass_criteria": {"period_tolerance": 0.001}}
    data = synthetic.scenario_data(name, seed, "correlated")
    return dumps_json(build_result(target, data, _plan(OFF), analysis, context))


@pytest.mark.parametrize("name", CN_CONTROLS)
def test_cn_d_m1_shared_path_equals_the_complete_switch_off_analysis(correlated, name):
    for seed in CONTROL_SEEDS:
        complete = correlated[(name, seed, "off_complete")]
        derived = correlated[(name, seed, "off")]
        assert _shared(derived) and not _shared(complete), seed
        assert _cn_record(derived, name, seed) == _cn_record(complete, name, seed), seed
        assert _gauntlet_tests(derived) == _gauntlet_tests(complete), seed


@pytest.mark.parametrize("seed", CONTROL_SEEDS)
def test_cn_d_e1_premise_the_switch_changes_the_planet_analysis(correlated, seed):
    on, off = correlated[("planet", seed, "on")], correlated[("planet", seed, "off")]
    assert (on.verdict, off.verdict) == ("WEAKENED", "REFUTED")
    assert _test(on, "eb_catalog").severity.value == "warning"
    assert _test(off, "eb_catalog").severity.value == "fatal"
