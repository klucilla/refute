"""Walk, claim inventories, claim draw and publication proof (WP5 W5.6 to W5.11), offline."""

import copy
import hashlib
import random
from datetime import UTC, datetime, timedelta

import pytest

from refute.selection import inventory as inv_mod
from refute.selection.inventory import InventoryError, draw_claims, replace_claim
from refute.selection.publication import PublicationError, check_publication, fetch_push_runs
from refute.selection.walk import (
    ACCEPTED,
    REJECTED,
    STOPPED,
    RetryPolicy,
    TransientError,
    TriageResult,
    WalkError,
    log_markdown,
    rejection_profile,
    walk,
)

NOW = datetime(2026, 10, 15, 12, 0, 0, tzinfo=UTC)

# ---- walk (W5.6 to W5.8) ------------------------------------------------------------------


def no_sleep(seconds):
    no_sleep.calls.append(seconds)


no_sleep.calls = []


def test_walk_stops_at_the_needed_acceptances_with_reasons_and_evidence():
    decisions = {
        "2401.00001": TriageResult(REJECTED, "requires_gpu", "README line 12: CUDA only"),
        "2401.00002": TriageResult(ACCEPTED, ACCEPTED, "triage record 2"),
        "2401.00003": TriageResult(ACCEPTED, ACCEPTED, "triage record 3"),
        "2401.00004": TriageResult(ACCEPTED, ACCEPTED, "never reached"),
    }
    log = walk(
        list(decisions), decisions.__getitem__, 2, RetryPolicy(3, 5.0), no_sleep, lambda: NOW
    )
    assert log.accepted == ["2401.00002", "2401.00003"] and log.complete
    assert [e.position for e in log.entries] == [1, 2, 3]
    assert rejection_profile(log)["requires_gpu"] == 1
    assert "requires_gpu" in log_markdown(log)


def test_a_transient_error_is_retried_and_logged_apart():
    calls = {"n": 0}

    def flaky(arxiv_id):
        calls["n"] += 1
        if calls["n"] == 1:
            raise TransientError("HTTP 503")
        return TriageResult(ACCEPTED, ACCEPTED, "ok")

    no_sleep.calls = []
    log = walk(["2401.00001"], flaky, 1, RetryPolicy(3, 7.5), no_sleep, lambda: NOW)
    entry = log.entries[0]
    assert entry.decision == ACCEPTED and len(entry.transient_attempts) == 1
    assert entry.transient_attempts[0].error == "HTTP 503" and no_sleep.calls == [7.5]


def test_a_persistent_transient_error_stops_the_walk_and_is_not_a_rejection():
    def down(arxiv_id):
        raise TransientError("timeout")

    log = walk(["2401.00001", "2401.00002"], down, 1, RetryPolicy(3, 1.0), no_sleep, lambda: NOW)
    assert log.stopped and len(log.entries) == 1
    entry = log.entries[0]
    assert entry.decision == STOPPED and len(entry.transient_attempts) == 3
    assert sum(rejection_profile(log).values()) == 0
    assert "stopped on transient errors" in log_markdown(log)


def test_a_non_transient_error_propagates():
    def broken(arxiv_id):
        raise ValueError("bug")

    with pytest.raises(ValueError):
        walk(["2401.00001"], broken, 1, RetryPolicy(3, 1.0), no_sleep, lambda: NOW)


@pytest.mark.parametrize(
    "bad",
    [
        dict(decision=REJECTED, reason="looks_hard", evidence="x"),
        dict(decision=ACCEPTED, reason="requires_gpu", evidence="x"),
        dict(decision=REJECTED, reason="requires_gpu", evidence=" "),
        dict(decision="maybe", reason=ACCEPTED, evidence="x"),
    ],
)
def test_triage_results_outside_the_closed_list_are_refused(bad):
    with pytest.raises(WalkError):
        TriageResult(**bad)


# ---- inventory and claim draw (W5.9, W5.10) ----------------------------------------------

SEED = bytes(range(32))


def candidate(i, kind="value", eligible=None, reference=None):
    c = {
        "candidate_id": f"Table 1 / row {i} / col Acc",
        "reading_order": i,
        "type": kind,
        "transcription": {
            "value": f"{80 + i}.0",
            "location": f"Table 1, row {i}",
            "metric": "accuracy",
            "split": "test",
            "command": "python train.py",
        },
    }
    if kind == "comparison":
        c["reference"] = reference or "Baseline"
        c["eligible_comparison"] = eligible if eligible is not None else True
    return c


def inventory(cands):
    return {
        "format": "refute-ml-inventory-1",
        "paper": {"arxiv_id": "2401.01234", "version": 2},
        "candidates": cands,
        "approval": {
            "approved_by": "maintainer",
            "approved_utc": "2026-10-15T12:00:00Z",
            "approved_commit": "a" * 40,
        },
    }


def test_inventory_hash_is_canonical_and_validation_refuses_bad_inventories():
    inv = inventory([candidate(1), candidate(2, "comparison")])
    h = inv_mod.inventory_sha256(inv)
    reordered = {k: inv[k] for k in reversed(list(inv))}
    assert inv_mod.inventory_sha256(reordered) == h
    for mutate in (
        lambda x: x.update(format="other"),
        lambda x: x["candidates"].append(copy.deepcopy(x["candidates"][0])),
        lambda x: x["candidates"][1].pop("reference"),
        lambda x: x["candidates"][0].update(reference="X"),
        lambda x: x["candidates"][0]["transcription"].pop("command"),
        lambda x: x["candidates"][1].update(reading_order=5),
        lambda x: x["paper"].update(arxiv_id="2401.01234v2"),
        lambda x: x["approval"].update(approved_commit="abc"),
    ):
        bad = copy.deepcopy(inv)
        mutate(bad)
        with pytest.raises(InventoryError):
            inv_mod.inventory_sha256(bad)


def test_draw_seed_is_the_plan_formula():
    expected = int.from_bytes(hashlib.sha256(SEED + b"2401.01234").digest(), "big")
    assert inv_mod.draw_seed(SEED, "2401.01234") == expected
    with pytest.raises(InventoryError):
        inv_mod.draw_seed(SEED[:31], "2401.01234")


def test_draw_takes_three_in_shuffled_order():
    inv = inventory([candidate(i) for i in range(1, 7)])
    draw = draw_claims(inv, SEED)
    ids = [c["candidate_id"] for c in inv["candidates"]]
    expected = list(ids)
    random.Random(inv_mod.draw_seed(SEED, "2401.01234")).shuffle(expected)
    assert draw.shuffled == expected and draw.drawn == expected[:3]
    assert draw.no_comparison_evaluated


def test_a_comparison_is_forced_into_the_third_place_when_required():
    cands = [candidate(i) for i in range(1, 9)] + [candidate(9, "comparison")]
    inv = inventory(cands)
    # find a seed for which the comparison is not among the first three
    for b in range(256):
        seed = bytes([b]) * 32
        draw = draw_claims(inv, seed)
        if draw.comparison_substituted:
            break
    else:  # pragma: no cover
        pytest.fail("no seed without a comparison in the first three")
    comparison = cands[-1]["candidate_id"]
    assert draw.comparison_required and draw.drawn[2] == comparison
    assert draw.comparison_substituted == draw.shuffled[2]


def test_ineligible_comparisons_are_never_drawn():
    inv = inventory([candidate(1), candidate(2, "comparison", eligible=False), candidate(3)])
    draw = draw_claims(inv, SEED)
    assert sorted(draw.drawn) == sorted(
        [inv["candidates"][0]["candidate_id"], inv["candidates"][2]["candidate_id"]]
    )
    assert draw.no_comparison_evaluated


def test_three_or_fewer_candidates_are_all_taken():
    inv = inventory([candidate(1), candidate(2, "comparison")])
    assert sorted(draw_claims(inv, SEED).drawn) == sorted(
        c["candidate_id"] for c in inv["candidates"]
    )


def test_replacement_keeps_the_comparison_and_the_record():
    cands = [candidate(i) for i in range(1, 6)] + [
        candidate(6, "comparison"),
        candidate(7, "comparison"),
    ]
    inv = inventory(cands)
    draw = draw_claims(inv, SEED)
    comparisons = [i for i in draw.drawn if "row 6" in i or "row 7" in i]
    assert comparisons
    allowed = ("transcription_error_that_changes_identity",)
    new = replace_claim(draw, inv, comparisons[0], allowed[0], allowed)
    replacement = new.replacements[0]["replacement"]
    if len(comparisons) == 1:
        assert "row 6" in replacement or "row 7" in replacement
    assert new.replacements[0]["invalidated"] == comparisons[0]
    with pytest.raises(InventoryError):
        replace_claim(draw, inv, draw.drawn[0], "unfavorable_result", allowed)


# ---- publication proof (W5.11) -------------------------------------------------------------

SHA = "b" * 40
ROUND = datetime(2026, 11, 1, 12, 0, 0, tzinfo=UTC)
FILES = {"inventories/2401.01234.json": "c" * 64}


def run(created, sha=SHA, event="push", run_id=1):
    return {"id": run_id, "head_sha": sha, "event": event, "created_at": created}


def test_a_push_run_before_the_round_is_proof():
    proof = check_publication(
        SHA, [run("2026-10-30T10:00:00Z")], ROUND, timedelta(hours=1), True, FILES, FILES
    )
    assert proof.run_created_at == "2026-10-30T10:00:00Z" and proof.margin_seconds == 3600


@pytest.mark.parametrize(
    ("runs", "tree_clean", "in_commit", "message"),
    [
        ([run("2026-11-01T11:30:00Z")], True, FILES, "not at least"),  # inside the margin
        ([run("2026-11-02T00:00:00Z")], True, FILES, "not at least"),  # after the round
        ([], True, FILES, "no GitHub Actions run"),  # no evidence
        (
            [run("2026-10-30T10:00:00Z", event="workflow_dispatch")],
            True,
            FILES,
            "no GitHub Actions run",
        ),
        ([run("2026-10-30T10:00:00Z", sha="d" * 40)], True, FILES, "another SHA"),
        ([run("2026-10-30T10:00:00Z")], False, FILES, "not clean"),
        ([run("2026-10-30T10:00:00Z")], True, {}, "not in the commit"),
        ([run("2026-10-30T10:00:00Z")], True, {"inventories/2401.01234.json": "e" * 64}, "differs"),
    ],
)
def test_missing_or_late_evidence_is_refused(runs, tree_clean, in_commit, message):
    with pytest.raises(PublicationError, match=message):
        check_publication(SHA, runs, ROUND, timedelta(hours=1), tree_clean, in_commit, FILES)


def test_git_dates_are_ignored_only_the_push_run_counts():
    # a commit dated before the round but pushed after it: its run is after the round
    with pytest.raises(PublicationError):
        check_publication(
            SHA, [run("2026-11-01T13:00:00Z")], ROUND, timedelta(0), True, FILES, FILES
        )


def test_fetch_push_runs_reads_the_api_offline():
    seen = []

    def get_json(url):
        seen.append(url)
        return {"workflow_runs": [run("2026-10-30T10:00:00Z")]}

    runs = fetch_push_runs("owner/repo", SHA, get_json)
    assert runs[0]["head_sha"] == SHA and f"head_sha={SHA}" in seen[0] and "event=push" in seen[0]
    with pytest.raises(PublicationError):
        fetch_push_runs("owner/repo", SHA, lambda url: {})
