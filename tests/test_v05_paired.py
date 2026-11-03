"""v0.5 WP7 and WP10 (implementation part): the paired comparison (#198) and its reporting rules
(docs/plans/v0.5-acceptance.md, cases 10.1 to 10.3, 7.1, 7.2, 6.5 and 6.7)."""

from __future__ import annotations

import pytest

from refute.packs.tess.discover.measure import chain
from refute.packs.tess.discover.paired import (
    VERDICTS,
    check_pairing,
    injection_groups,
    paired_chain,
    recovery_v05,
    summarize,
    summarize_injections,
    transformed_groups,
    transitions,
    verdict_counts,
)
from refute.packs.tess.params import TessTestPlan
from refute.packs.tess.synthetic import discovery_plan_dict, discovery_v05_plan_dict, scenario_data

V04 = TessTestPlan.model_validate(discovery_plan_dict())
V05 = TessTestPlan.model_validate(discovery_v05_plan_dict())


@pytest.mark.parametrize("scenario", ["planet", "eb_odd_even", "noise"])
def test_10_1_the_v04_battery_on_the_shared_candidate_is_the_v04_chain(scenario):
    data = scenario_data(scenario)
    paired = paired_chain(data, V04, V05, stage=1)
    reference = chain(data, V04, 1)
    reference.pop("survived_stage_tests")
    assert paired["v04"] == reference
    # both batteries attacked the same candidate
    assert paired["v04"]["candidate"] == paired["v05"]["candidate"]


def test_10_1_plans_that_would_not_share_the_candidate_are_refused():
    other = discovery_v05_plan_dict()
    other["search"] = {**other["search"], "period_max_days": 9.0}
    with pytest.raises(ValueError, match="search"):
        check_pairing(V04, TessTestPlan.model_validate(other))
    # the event measurement feeds the final candidate and its gate (Codex's review)
    events = discovery_v05_plan_dict()
    events.setdefault("gauntlet", {})["events"] = {"min_coverage": 0.7}
    with pytest.raises(ValueError, match="events"):
        check_pairing(V04, TessTestPlan.model_validate(events))
    with pytest.raises(ValueError, match="discovery version"):
        check_pairing(V05, V05)


def test_10_3_the_four_verdicts_are_counted_apart():
    assert verdict_counts(["SURVIVED", "WEAKENED", "WEAKENED"]) == {
        "SURVIVED": 1,
        "WEAKENED": 2,
        "REFUTED": 0,
        "INCONCLUSIVE": 0,
    }
    with pytest.raises(ValueError):
        verdict_counts(["PASS"])
    table = transitions([("SURVIVED", "INCONCLUSIVE"), ("SURVIVED", "REFUTED")])
    assert table["SURVIVED"]["INCONCLUSIVE"] == 1 and table["SURVIVED"]["REFUTED"] == 1
    assert set(table) == set(VERDICTS)


def _record(key, status="OK", gate=True, v04="SURVIVED", v05="INCONCLUSIVE", position=1):
    chain_ = {
        "v04": {"gate_passed": gate, "stage_verdict": v04},
        "v05": {"gate_passed": gate, "stage_verdict": v05},
    }
    return {"target_key": key, "status": status, "chain": chain_, "position": position}


def test_6_5_failed_tasks_are_apart_from_inconclusive_verdicts():
    records = [_record("A"), _record("A", status="INCONCLUSIVE"), _record("B", gate=False)]
    out = summarize(records, "x")
    assert out["tasks"] == 3 and out["failed_tasks"] == 1
    assert out["gate_passed"] == 1 and out["stars"] == 2 and out["stars_with_gate_passed"] == 1
    assert out["v05_stage_verdicts"]["INCONCLUSIVE"] == 1  # a verdict, not a failed task


def test_10_3_an_empty_group_is_reported_with_zeros():
    out = summarize([], "empty")
    assert out["tasks"] == 0 and out["gate_passed"] == 0
    assert out["v04_stage_verdicts"] == dict.fromkeys(VERDICTS, 0)


def _injected(key, recovered, status="OK", v04="SURVIVED", v05="INCONCLUSIVE"):
    record = _record(key, status=status, v04=v04, v05=v05)
    record["recovery"] = {"recovered": recovered, "alias": None, "gate_passed": True}
    return record


def test_7_1_hosts_with_their_own_signal_are_never_pooled():
    records = [_injected("A", True), _injected("B", True), _injected("C", True)]
    out = injection_groups(records, own_signal={"C"})
    assert out["original_gate_negative"]["attempted"] == 2
    assert out["signal_bearing"]["attempted"] == 1
    assert "not sensitivity" in out["signal_bearing"]["caveat"]


def test_injection_counts_are_conditioned_on_recovery():
    # a gate-passing detection at an unrelated period (not recovered) never enters the counts
    records = [
        _injected("A", True, v04="SURVIVED", v05="REFUTED"),
        _injected("A", False, v04="SURVIVED", v05="SURVIVED"),
        _injected("B", False, status="ERROR"),
    ]
    out = summarize_injections(records, "x")
    assert out["attempted"] == 3 and out["recovered"] == 1 and out["not_recovered"] == 2
    assert out["failed_tasks"] == 1
    assert out["among_recovered"]["denominator"] == 1
    assert out["among_recovered"]["v05_stage_verdicts"]["REFUTED"] == 1
    assert out["among_recovered"]["v05_stage_verdicts"]["SURVIVED"] == 0
    assert out["among_attempted"]["denominator"] == 3


def test_7_2_inverted_and_rotated_curves_and_both_hosts_are_apart():
    records = [_record("A", position=0), _record("A", position=1), _record("C", position=2)]
    out = transformed_groups(records, own_signal={"C"})
    assert set(out) == {
        "inverted/signal_bearing",
        "inverted/original_gate_negative",
        "rotated/signal_bearing",
        "rotated/original_gate_negative",
    }
    assert out["inverted/original_gate_negative"]["tasks"] == 1
    assert out["rotated/signal_bearing"]["tasks"] == 1
    assert out["inverted/signal_bearing"]["tasks"] == 0  # reported, not dropped


INJ = {"period_days": 4.0, "t0_btjd": 1000.0, "duration_days": 0.1}


def _recover(period, t0):
    found = {"period_days": period, "t0_btjd": t0}
    return recovery_v05(INJ, found, True, period_tolerance=0.01, epoch_tolerance_durations=0.5)


def test_6_7_an_alias_needs_the_epoch_as_well_as_the_period():
    assert _recover(8.0, 1004.0)["alias"] == 2.0  # 2P on an injected transit
    assert _recover(8.0, 1002.0)["alias"] is None  # 2P, but between the transits
    assert _recover(2.0, 1002.0)["alias"] == 0.5  # P/2: every other event is a transit
    assert _recover(2.0, 1001.0)["alias"] is None
    assert _recover(4.0, 1008.0)["recovered"] is True
    assert _recover(4.0, 1002.0)["recovered"] is False
