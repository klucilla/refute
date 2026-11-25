"""v0.5.11 step 1: identity (A5) and versions 1 to 4, written before the `src/` change
(docs/plans/v0.5.11-spec.md, sections 2, 3 and 8; the charter's section 2.3).

- **Unmarked tests** must pass now and after the change: versions 1 to 4 against the baseline
  (differential), the A4 sabotage on the verdict, and `entry` refused for versions 1 to 4.
- **Strict expected failures** need the new implementation. Each names the exception it fails
  with now: a plan of discovery version 5 is refused when validated.

Synthetic data only; no network.
"""

from __future__ import annotations

import copy
import json
import os
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from refute.core.io import dumps_json
from refute.core.verdict import Severity, TestResult, TestStatus, aggregate
from refute.packs.tess.params import TessTestPlan
from refute.packs.tess.synthetic import (
    discovery_plan_dict,
    discovery_v05_plan_dict,
    discovery_v051_plan_dict,
    discovery_v052_plan_dict,
    scenario_data,
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
import baseline_code_v0511 as bc  # noqa: E402

TARGET = bc.TARGET
CONTEXT = {"claim_id": "synthetic-v5", "claim_kind": "discover", "hypothesis": "h"}


def v5_plan_dict() -> dict:
    d = discovery_v05_plan_dict()
    d["discovery"]["version"] = 5
    d["discovery"]["entry"] = "search"
    return d


# --- versions 1 to 4: the golden snapshot, differential (must pass before and after) ---------


@pytest.fixture(scope="module")
def differential(tmp_path_factory):
    if not bc.baseline_available():
        if os.environ.get("CI"):
            pytest.fail(f"the baseline {bc.BASELINE} is not in CI's clone")
        pytest.skip(f"the baseline {bc.BASELINE} is not in this clone")
    base = bc.baseline_outputs(tmp_path_factory.mktemp("baseline-v0511"))
    return base, bc.outputs()


def test_versions_1_to_4_give_the_baseline_bytes(differential):
    base, current = differential
    assert sorted(current) == sorted(base)
    for name in base:
        assert current[name] == base[name], name


@pytest.mark.parametrize(
    "plan", [discovery_plan_dict, discovery_v05_plan_dict, discovery_v051_plan_dict,
             discovery_v052_plan_dict],
)  # fmt: skip
def test_an_authored_entry_is_refused_for_versions_1_to_4(plan):
    d = plan()
    d["discovery"]["entry"] = "search"
    with pytest.raises(ValidationError):
        TessTestPlan.model_validate(d)


@pytest.mark.parametrize(
    "plan", [discovery_plan_dict, discovery_v05_plan_dict, discovery_v051_plan_dict,
             discovery_v052_plan_dict],
)  # fmt: skip
def test_an_authored_null_entry_is_refused_for_versions_1_to_4(plan):
    # Codex's review of the step-2 diff, item 2: an explicit null is an authored entry too
    d = plan()
    d["discovery"]["entry"] = None
    with pytest.raises(ValidationError):
        TessTestPlan.model_validate(d)


@pytest.mark.parametrize(
    "plan", [discovery_plan_dict, discovery_v05_plan_dict, discovery_v051_plan_dict,
             discovery_v052_plan_dict],
)  # fmt: skip
def test_versions_1_to_4_dump_no_entry(plan):
    dumped = TessTestPlan.model_validate(plan()).model_dump(mode="json")
    assert "entry" not in dumped["discovery"]


# --- A4 on the verdict (today's aggregate, kept as it is) -------------------------------------


def _r(name, status, severity=Severity.FATAL, coverage=1):
    return TestResult(name, status, severity, "m", coverage=coverage, coverage_unit="u")


def test_a4_an_inconclusive_or_missing_decisive_test_never_gives_survived():
    gate = _r("snr", TestStatus.PASS, Severity.GATE)
    v, _ = aggregate([gate, _r("odd_even", TestStatus.INCONCLUSIVE)], expected=["snr", "odd_even"])
    assert v.value != "SURVIVED"
    v, _ = aggregate([gate], expected=["snr", "odd_even"])
    assert v.value != "SURVIVED"
    uncovered = _r("odd_even", TestStatus.PASS, coverage=0)
    v, _ = aggregate([gate, uncovered], expected=["snr", "odd_even"])
    assert v.value != "SURVIVED"


# --- version 5 (strict expected failures until step 2) --------------------------------------


def test_version_5_requires_entry_search():
    TessTestPlan.model_validate(v5_plan_dict())
    bad = v5_plan_dict()
    bad["discovery"]["entry"] = "catalog"
    with pytest.raises(ValidationError):
        TessTestPlan.model_validate(bad)
    missing = v5_plan_dict()
    del missing["discovery"]["entry"]
    with pytest.raises(ValidationError):
        TessTestPlan.model_validate(missing)


def _strip_v5(obj):
    """Remove the differences the specification allows (section 2): the field `screen`, the
    recorded discovery version (`discovery_version`, and the `version` of the plan's own
    discovery section, which every record echoes in `test_plan`), and the plan's `entry`."""
    if isinstance(obj, dict):
        is_discovery = "decisive" in obj and "survived_meaning" in obj
        return {
            k: _strip_v5(v)
            for k, v in obj.items()
            if k not in ("screen", "discovery_version", "entry")
            and not (is_discovery and k == "version")
        }
    if isinstance(obj, list):
        return [_strip_v5(x) for x in obj]
    return obj


@pytest.mark.parametrize("scenario", ["planet_three_years", "eb_odd_even", "noise"])
def test_version_5_equals_version_2_through_analyze_and_build_result(scenario):
    from refute.packs.tess.pipeline import analyze_data, build_result

    p5 = TessTestPlan.model_validate(v5_plan_dict())
    p2 = TessTestPlan.model_validate(discovery_v05_plan_dict())
    data = scenario_data(scenario)
    a5, a2 = analyze_data(data, p5, stage=2), analyze_data(data, p2, stage=2)
    assert "screen" in a5.extras and "screen" not in a2.extras
    assert a5.verdict == a2.verdict and a5.verdict_reason == a2.verdict_reason
    assert [t.to_dict() for t in a5.tests] == [t.to_dict() for t in a2.tests]
    assert a5.deferred == a2.deferred and a5.stage == a2.stage
    r5 = json.loads(dumps_json(build_result(TARGET, data, p5, a5, CONTEXT)))
    r2 = json.loads(dumps_json(build_result(TARGET, data, p2, a2, CONTEXT)))
    assert "screen" in r5 and "screen" not in r2
    assert _strip_v5(r5) == _strip_v5(r2)


@pytest.mark.parametrize("stage", [1, 2])
def test_version_5_equals_version_2_through_the_measurement_chain(stage):
    from refute.packs.tess.discover.measure import chain

    p5 = TessTestPlan.model_validate(v5_plan_dict())
    p2 = TessTestPlan.model_validate(discovery_v05_plan_dict())
    data = scenario_data("planet_three_years")
    c5, c2 = chain(data, p5, stage), chain(data, p2, stage)
    assert "screen" in c5 and "screen" not in c2
    assert c5["screen"]["version"] == 5
    assert _strip_v5(c5) == _strip_v5(c2)
    assert c5["stage_verdict"] == c2["stage_verdict"]
    assert c5["stage_verdict_reason"] == c2["stage_verdict_reason"]


def test_version_5_equals_version_2_in_the_error_record():
    from refute.packs.tess.pipeline import TessAnalyzer

    p5 = TessTestPlan.model_validate(v5_plan_dict()).model_dump(mode="json")
    p2 = discovery_v05_plan_dict()
    e5 = TessAnalyzer().error_result(TARGET, "boom", CONTEXT, test_plan=p5)
    e2 = TessAnalyzer().error_result(TARGET, "boom", CONTEXT, test_plan=p2)
    assert _strip_v5(json.loads(dumps_json(e5))) == _strip_v5(json.loads(dumps_json(e2)))


def test_version_5_keeps_the_legacy_error_type_and_message():
    from refute.packs.tess.pipeline import analyze_data

    def broken(*args, **kwargs):
        raise RuntimeError("search failed on purpose")

    p5 = TessTestPlan.model_validate(v5_plan_dict())
    p2 = TessTestPlan.model_validate(discovery_v05_plan_dict())
    data = scenario_data("planet")
    errors = []
    for plan in (p5, p2):
        with pytest.raises(RuntimeError) as info:
            analyze_data(data, plan, search_fn=broken, stage=1)
        errors.append((type(info.value), str(info.value)))
    assert errors[0] == errors[1]


def test_version_5_is_deterministic():
    from refute.packs.tess.pipeline import analyze_data, build_result

    p5 = TessTestPlan.model_validate(v5_plan_dict())
    outs = []
    for _ in range(2):
        data = scenario_data("planet")
        a = analyze_data(data, p5, stage=1)
        outs.append(dumps_json(build_result(TARGET, data, p5, a, CONTEXT)))
    assert outs[0] == outs[1]


def test_the_version_5_plan_dump_differs_from_version_2_only_by_version_and_entry():
    d5 = TessTestPlan.model_validate(v5_plan_dict()).model_dump(mode="json")
    d2 = TessTestPlan.model_validate(discovery_v05_plan_dict()).model_dump(mode="json")
    assert d5["discovery"]["entry"] == "search"
    a, b = copy.deepcopy(d5), copy.deepcopy(d2)
    for d in (a, b):
        d["discovery"].pop("version")
        d["discovery"].pop("entry", None)
    assert a == b
