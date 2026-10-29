"""v0.4 WP5: the case ledger, the case format and the funnel's promotion (cases 5.1 to 5.9 of
docs/plans/v0.4-acceptance.md, and protocol sections 4.4 and 7). Synthetic data only."""

from __future__ import annotations

import json

import pytest

from refute.core.canonical import canonical_bytes
from refute.core.ledger import (
    GENESIS,
    LedgerError,
    append_event,
    make_event,
    read_events,
    verify_events,
    verify_file,
)
from refute.packs.tess.discover import case as cs
from refute.packs.tess.discover import funnel
from refute.packs.tess.report import HOLDOUT_BLINDNESS_NOTE, render_report

UTC = "2026-10-29T00:00:00Z"


def _chain(n: int = 3):
    events, previous = [], None
    for i in range(n):
        previous = make_event(previous, f"case-{i}", "opened", UTC, {"i": i})
        events.append(previous)
    return events


def test_5_1_a_chain_of_events_verifies():
    events = _chain()
    assert verify_events(events) == []
    assert events[0]["prev_hash"] == GENESIS and events[1]["prev_hash"] == events[0]["hash"]


def test_5_2_one_changed_byte_breaks_the_chain_at_that_event():
    events = _chain()
    events[1]["data"]["i"] = 99
    problems = verify_events(events)
    assert problems and problems[0].startswith("event 2: hash")


def test_5_3_a_removed_event_breaks_the_chain():
    events = _chain()
    del events[1]
    problems = verify_events(events)
    assert any("seq" in p for p in problems) and any("prev_hash" in p for p in problems)


def test_5_4_a_correction_is_a_new_event_and_the_old_one_stays(tmp_path):
    path = tmp_path / "ledger.jsonl"
    first = make_event(None, "case-1", "concluded", UTC, {"conclusion": {"text": "x"}})
    append_event(path, first)
    correction = make_event(first, "case-1", "corrected", UTC, {"why": "typo"}, corrects=1)
    append_event(path, correction)
    events = read_events(path)
    assert [e["type"] for e in events] == ["concluded", "corrected"]
    assert events[1]["corrects"] == 1
    assert verify_file(path, anchor_hash=first["hash"]) == []
    assert verify_file(path, anchor_hash="f" * 64) == ["the anchor hash is not in the chain"]
    assert path.read_bytes().splitlines()[0] == canonical_bytes(first)
    with pytest.raises(LedgerError):
        make_event(correction, "case-1", "corrected", UTC, {})
    with pytest.raises(LedgerError, match="corrects"):
        append_event(path, make_event(correction, "case-1", "reviewed", UTC, {}, corrects=9))


def _stage1_verdict(**change):
    verdict = {
        "target_key": "TIC-5",
        "status": "OK",
        "verdict": "INCONCLUSIVE",
        "verdict_reason": "could not be decided: centroid_shift, aperture_depth",
        "method_status": "not_validated",
        "temporal_diagnostic": {"state": "pass"},
        "discovery": {"stage": 1, "deferred_tests": ["centroid_shift", "aperture_depth"]},
        "expected_tests": [
            "snr",
            "odd_even",
            "secondary_eclipse",
            "plausibility",
            "centroid_shift",
            "aperture_depth",
            "nearby_contamination",
            "period_alias",
            "systematics",
        ],
        "tests": [
            {"name": n, "status": "PASS", "severity": "fatal"}
            for n in ("odd_even", "secondary_eclipse", "plausibility", "period_alias")
        ]
        + [{"name": "snr", "status": "PASS", "severity": "gate"}]
        + [
            {"name": n, "status": "PASS", "severity": "warning"}
            for n in ("nearby_contamination", "systematics")
        ]
        + [
            {"name": n, "status": "INCONCLUSIVE", "severity": "fatal"}
            for n in ("centroid_shift", "aperture_depth")
        ],
        "candidate": {"period": 2.0},
    }
    verdict.update(change)
    return verdict


NO_MATCH = {"overall": "no_match"}


def test_5_5_a_light_entry_has_its_fields_and_the_promotion_apart():
    verdict = _stage1_verdict()
    eligibility = funnel.stage1_eligibility(verdict, NO_MATCH)
    data = cs.light_entry(verdict, eligibility, NO_MATCH)
    event = make_event(None, "TIC-5", "ran", UTC, data)
    assert cs.check_event(event) == []
    assert data["promotion"] == {"eligible": True, "reason": "eligible"}
    del data["temporal_diagnostic"]
    problems = cs.check_event(make_event(None, "TIC-5", "ran", UTC, data))
    assert any("temporal_diagnostic" in p for p in problems)
    assert verify_events([make_event(None, "TIC-5", "ran", UTC, data)], cs.check_event)


@pytest.mark.parametrize(
    ("event_type", "data", "hashes", "match"),
    [
        (
            "ran",
            {"stage": 2, "temporal_diagnostic": "pass"},
            {"dossier": "a" * 64},
            "method_status",
        ),
        (
            "ran",
            {"stage": 2, "method_status": "not_validated", "temporal_diagnostic": "confirmed"},
            {"dossier": "a" * 64},
            "temporal_diagnostic",
        ),
        (
            "ran",
            {"stage": 2, "method_status": "not_validated", "temporal_diagnostic": "pass"},
            {},
            "dossier",
        ),
        ("ran", {"method_status": "not_validated", "temporal_diagnostic": "pass"}, {}, "stage"),
        ("promoted", {"promoted": []}, {}, "SHA-256"),
    ],
)
def test_the_event_rules_apply_to_every_type(event_type, data, hashes, match):
    problems = cs.check_event(make_event(None, "c", event_type, UTC, data, hashes=hashes))
    assert any(match in p for p in problems), problems


def test_a_complete_stage_2_run_and_promotion_pass():
    ran = {"stage": 2, "method_status": "not_validated", "temporal_diagnostic": "fail"}
    assert (
        cs.check_event(make_event(None, "c", "ran", UTC, ran, hashes={"dossier": "b" * 64})) == []
    )
    promoted = {"promotion_sha256": "c" * 64, "promoted": ["TIC-5"]}
    assert cs.check_event(make_event(None, "c", "promoted", UTC, promoted)) == []


def test_5_6_a_missing_case_item_is_reported():
    case = {item: {"x": 1} for item in cs.CASE_ITEMS}
    case["conclusion"] = {"text": "no significant signal in these data"}
    assert cs.missing_items(case) == []
    del case["uncertainties"]
    assert cs.missing_items(case) == ["uncertainties"]


@pytest.mark.parametrize(
    "text",
    [
        "no significant signal in these data",
        "signal with a likely alternative explanation: an eclipsing binary, by the test odd_even",
        "signal matches a known object: TOI, TOI-123.01, alias 2",
        "signal survived the declared decisive battery; temporal diagnostic: fail; "
        "method not validated",
        "not evaluated past stage 1: cap",
        "insufficient data to decide: plausibility, no stellar mass",
    ],
)
def test_5_7_the_closed_vocabulary_accepts_its_forms(text):
    assert cs.conclusion_allowed(text)


@pytest.mark.parametrize(
    "text",
    [
        "a confirmed planet",
        "signal survived the declared decisive battery; temporal diagnostic: confirmed; "
        "method not validated",
        "new discovery of a planet",
        "TIC 5 b is a planet",
    ],
)
def test_5_7_other_conclusions_are_refused(text):
    assert not cs.conclusion_allowed(text)
    event = make_event(None, "c", "concluded", UTC, {"conclusion": {"text": text}})
    assert cs.check_event(event)


def test_5_9_the_report_states_the_holdout_blindness():
    record = {
        "target_key": "TIC-5",
        "verdict": "SURVIVED",
        "method_status": "not_validated",
        "discovery": {},
        "holdout_rounds": [{"hidden_year": 2019, "status": "PASS", "metrics": {}}],
    }
    assert HOLDOUT_BLINDNESS_NOTE in render_report(record, {"claim_kind": "discover"})
    assert "detrended once before any logged read" in HOLDOUT_BLINDNESS_NOTE


# --- the funnel: eligibility (section 7) ---------------------------------------------------


def _with(verdict, name, status, severity):
    tests = [dict(t) for t in verdict["tests"]]
    for t in tests:
        if t["name"] == name:
            t.update(status=status, severity=severity)
    return {**verdict, "tests": tests}


def test_a_warning_fail_does_not_block_eligibility():
    verdict = _with(_stage1_verdict(), "systematics", "FAIL", "warning")
    out = funnel.stage1_eligibility(verdict, NO_MATCH)
    assert out["eligible"] and out["warning_fails"] == ["systematics"]


@pytest.mark.parametrize(
    ("verdict", "dedup", "reason"),
    [
        (_with(_stage1_verdict(), "odd_even", "FAIL", "fatal"), NO_MATCH, "alternative"),
        (_with(_stage1_verdict(), "secondary_eclipse", "FAIL", "fatal"), NO_MATCH, "alternative"),
        (
            _with(_stage1_verdict(), "plausibility", "INCONCLUSIVE", "warning"),
            NO_MATCH,
            "insufficient",
        ),
        (_with(_stage1_verdict(), "snr", "FAIL", "gate"), NO_MATCH, "no significant"),
        (_stage1_verdict(), {"overall": "match"}, "known object"),
        (_stage1_verdict(), {"overall": "INCONCLUSIVE"}, "not decided"),
        (_stage1_verdict(), None, "not decided"),
        (_stage1_verdict(status="ERROR"), NO_MATCH, "analysis error"),
        (_stage1_verdict(discovery={"stage": 2}), NO_MATCH, "not a stage-1"),
    ],
)
def test_eligibility_refusals(verdict, dedup, reason):
    out = funnel.stage1_eligibility(verdict, dedup)
    assert out["eligible"] is False and reason in out["reason"]


def test_the_holdout_never_enters_eligibility():
    verdict = _stage1_verdict(temporal_diagnostic={"state": "fail"})
    assert funnel.stage1_eligibility(verdict, NO_MATCH)["eligible"]


def test_promotion_takes_all_at_or_under_the_cap_and_draws_above_it():
    assert funnel.promote([3, 1], None)["promoted"] == [1, 3]
    with pytest.raises(ValueError, match="seed"):
        funnel.promote([1, 2, 3, 4], None)
    drawn = funnel.promote([4, 2, 3, 1, 5], seed=123)
    assert len(drawn["promoted"]) == 3 and len(drawn["not_promoted"]) == 2
    assert funnel.promote([4, 2, 3, 1, 5], seed=123) == drawn
    assert sorted(drawn["promoted"] + drawn["not_promoted"]) == [1, 2, 3, 4, 5]


def test_the_n_k_rule_takes_the_first_pair_that_fits():
    # per star: h_s1 + h_hold + K h_inj + 3 h_tr; projected = 1.5 N (that); limit 0.5 x 98 h
    cheap = funnel.ControlCosts(0.01, 0.01, 0.002, 0.01, 10e6)
    out = funnel.choose_n_k(cheap, hours_used=2.0, bytes_used=1e9)
    assert out["chosen"] == {"N": 100, "K": 20}
    dear = funnel.ControlCosts(0.1, 0.15, 0.04, 0.05, 10e6)  # only (50, 5) fits
    out = funnel.choose_n_k(dear, hours_used=2.0, bytes_used=1e9)
    assert out["chosen"] == {"N": 50, "K": 5}
    assert [e["fits"] for e in out["evaluations"]] == [False, False, False, True]
    none = funnel.choose_n_k(funnel.ControlCosts(5, 5, 5, 5, 1e9), 0.0, 0.0)
    assert none["chosen"] is None
    assert json.dumps(none)  # the record is plain JSON
