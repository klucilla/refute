"""v0.5.1 WP5: battery version 3 (docs/plans/v0.5.1-acceptance.md, rows 5.1 to 5.4).

Row 5.1: a version-3 claim keeps every test of the v0.5 battery (its decisive and diagnostic
tests); one without a role is refused at load time. Synthetic plans only."""

from __future__ import annotations

import copy
import json
from dataclasses import replace
from pathlib import Path

import pytest
import yaml

from refute.core.io import dumps_json
from refute.packs.tess.calib05.values import V05_DECISIVE, V05_DIAGNOSTIC
from refute.packs.tess.discover.paired import paired_chain
from refute.packs.tess.params import TessTestPlan
from refute.packs.tess.pipeline import TessAnalyzer, analyze_data, build_result
from refute.packs.tess.report import render_report
from refute.packs.tess.synthetic import (
    discovery_v05_plan_dict,
    discovery_v051_plan_dict,
    scenario_data,
)


def _without(d: dict, name: str) -> dict:
    d = copy.deepcopy(d)
    for role in ("decisive", "diagnostic"):
        d["discovery"][role] = [n for n in d["discovery"][role] if n != name]
    d["discovery"]["stages"].pop(name, None)
    d["discovery"]["required_diagnostics"] = [
        n for n in d["discovery"]["required_diagnostics"] if n != name
    ]
    return d


def test_the_version_3_plan_keeps_every_test_of_the_v05_battery():
    plan = TessTestPlan.model_validate(discovery_v051_plan_dict())
    assert set(V05_DECISIVE) | set(V05_DIAGNOSTIC) <= set(plan.discovery.roles)


@pytest.mark.parametrize("name", ["duty_cycle", "eb_catalog", "holdout_by_year", "single_event"])
def test_5_1_a_version_3_claim_without_a_v05_test_is_refused_at_load(name):
    # duty_cycle and eb_catalog are decisive in v0.5; holdout_by_year and single_event diagnostic
    # in the v0.5 calibration (decisive in the synthetic v0.5 plan: either role counts)
    with pytest.raises(ValueError, match=f"version 3 keeps every test of the v0.5 battery.*{name}"):
        TessTestPlan.model_validate(_without(discovery_v051_plan_dict(), name))


def test_5_1_a_version_2_claim_is_not_checked():
    d = _without(discovery_v05_plan_dict(catalogs=True), "eb_catalog")
    assert TessTestPlan.model_validate(d).discovery.version == 2


# --- row 5.2 (a): the code paths of the earlier claims keep their bytes -------------------------

# Written by the code of the v0.5.0 calibration lock (b6249b5) with
# tests/fixtures/v051_wp5/make_fixtures.py: the TESS plans of the v0.1, v0.2, v0.4 and v0.5 claims
# on one synthetic scenario. Evidence about the code paths, not a re-execution of recorded claims
# (that is row 5.2 (b), after the maintainer's approval).
ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "v051_wp5"
TARGET = {"key": "TIC-1", "tic_id": 1, "kind": "exploration", "name": "synthetic", "published": {}}


def _fixture(name: str) -> str:
    return (FIXTURES / name).read_bytes().decode("utf-8")


def _claim_plans() -> dict:
    canon = ROOT / "tests" / "fixtures" / "locked_canonical"
    out = {}
    for label, name in (
        ("v01", "tess-calibration-v0.1.json"),
        ("v02", "tess-calibration-v0.2.json"),
    ):
        out[label] = json.loads((canon / name).read_text(encoding="utf-8"))["canonical"][
            "test_plan"
        ]
    for label, path in (
        ("v04", "calibration/v0.4/claim.yaml"),
        ("v05", "calibration/v0.5/claim.yaml"),
    ):
        out[label] = yaml.safe_load((ROOT / path).read_text(encoding="utf-8"))["test_plan"]
    return out


@pytest.fixture(scope="module")
def claim_plans():
    return _claim_plans()


@pytest.mark.parametrize("label", ["v01", "v02", "v04", "v05"])
def test_5_2_the_plans_of_earlier_claims_produce_the_recorded_bytes(label, claim_plans):
    plan = TessTestPlan.model_validate(claim_plans[label])
    assert not plan.is_v051
    discover = plan.discovery is not None
    kind = "discover" if discover else "calibration"
    context = {"claim_id": f"synthetic-{label}", "claim_kind": kind, "hypothesis": "h"}
    data = scenario_data("planet_three_years")
    analysis = analyze_data(data, plan, stage=2 if discover else None)
    result = build_result(TARGET, data, plan, analysis, context)
    assert dumps_json(result) == _fixture(f"verdict-{label}.json")
    assert render_report(result, context) == _fixture(f"report-{label}.md")
    error = TessAnalyzer().error_result(TARGET, "boom", context, test_plan=claim_plans[label])
    assert dumps_json(error) == _fixture(f"error-{label}.json")


def test_5_2_the_paired_chain_of_the_v05_calibration_keeps_its_bytes(claim_plans):
    p04 = TessTestPlan.model_validate(claim_plans["v04"])
    p05 = TessTestPlan.model_validate(claim_plans["v05"])
    chain = paired_chain(scenario_data("planet_three_years"), p04, p05, stage=2)
    assert dumps_json(chain) == _fixture("paired-v04-v05.json")


# --- row 5.4 (part): the paired chain of a version-3 battery carries the WP4 classes ------------


def test_the_version_3_paired_chain_carries_the_classes_and_tallies(claim_plans):
    from refute.core.inconclusive import CLASSES, tally
    from refute.packs.tess.calib05.plans import v05_plan

    p04 = TessTestPlan.model_validate(claim_plans["v04"])
    d3 = v05_plan(claim_plans["v04"])
    d3["discovery"]["version"] = 3
    d3["v051"] = {}
    p3 = TessTestPlan.model_validate(d3)
    data = replace(scenario_data("planet_three_years"), aux=None)  # missing_input
    chain = paired_chain(data, p04, p3, stage=2)
    v3, v4 = chain["v05"], chain["v04"]
    assert "v051" not in v4 and all("inconclusive_class" not in t for t in v4["tests"].values())
    inconclusive = {n: t for n, t in v3["tests"].items() if t["status"] == "INCONCLUSIVE"}
    assert inconclusive
    for name, t in inconclusive.items():
        assert t["inconclusive_class"] in CLASSES, name
        assert t["inconclusive_class_source"] != "fallback", name
        assert v3["v051"]["inconclusive_classes"][name]["class"] == t["inconclusive_class"]
    assert inconclusive["aperture_depth"]["inconclusive_class"] == "missing_input"
    if v3["verdict"] == "INCONCLUSIVE" and v3["v051"]["inconclusive_condition"] is None:
        assert v3["v051"]["inconclusive_class"] == "missing_input"
    t = tally([{"verdict": v3["verdict"], "v051": v3["v051"]}])
    assert sum(t["verdicts"].values()) == 1
    assert t["tests_classified_by_fallback"] == 0
