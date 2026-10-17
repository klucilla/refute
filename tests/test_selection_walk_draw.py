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
    INPUT_EXHAUSTED,
    REJECTED,
    SAMPLE_FILLED,
    STOPPED,
    RetryPolicy,
    TransientError,
    TriageResult,
    WalkError,
    log_markdown,
    rejection_profile,
    transient_query,
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
        "method": "Ours",
        "dataset": "CIFAR-10",
        "conditions": "the repository's training script, default configuration, CPU",
    }
    if kind == "comparison":
        c["reference"] = reference or "Baseline"
        c["eligible_comparison"] = eligible if eligible is not None else True
    return c


def inventory(cands):
    return {
        "format": "refute-ml-inventory-2",
        "paper": {"arxiv_id": "2401.01234", "version": 2},
        "candidates": cands,
        "approval": {
            "approved_by": "maintainer",
            "approved_utc": "2026-10-15T12:00:00Z",
            "approved_commit": "a" * 40,
            "approval_record": "https://github.com/owner/repo/issues/1#issuecomment-1",
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
        # #59, Codex review of #82: the candidate fields of the claim spec and the proof of
        # the approval
        lambda x: x["candidates"][0].pop("method"),
        lambda x: x["candidates"][0].update(dataset=" "),
        lambda x: x["candidates"][1].pop("conditions"),
        lambda x: x["approval"].pop("approval_record"),
        lambda x: x["approval"].update(approval_record="http://example.org/ok"),
        lambda x: x["approval"].update(approved_utc="yesterday"),
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
REQ = list(FILES)


REPO = "owner/repo"
WORKFLOW = ".github/workflows/ci.yml"


def check(*args, **kwargs):
    kwargs.setdefault("repository", REPO)
    kwargs.setdefault("workflow_path", WORKFLOW)
    return check_publication(*args, **kwargs)


def run(created, sha=SHA, event="push", run_id=1, **extra):
    record = {
        "id": run_id,
        "head_sha": sha,
        "event": event,
        "created_at": created,
        "run_attempt": 1,
        "path": WORKFLOW,
        "repository": {"full_name": REPO},
        "head_repository": {"full_name": REPO},
    }
    record.update(extra)
    return record


def test_a_push_run_before_the_round_is_proof():
    proof = check(
        SHA, [run("2026-10-30T10:00:00Z")], ROUND, timedelta(hours=1), True, FILES, FILES, REQ
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
        check(SHA, runs, ROUND, timedelta(hours=1), tree_clean, in_commit, FILES, REQ)


def test_git_dates_are_ignored_only_the_push_run_counts():
    # a commit dated before the round but pushed after it: its run is after the round
    with pytest.raises(PublicationError):
        check(SHA, [run("2026-11-01T13:00:00Z")], ROUND, timedelta(0), True, FILES, FILES, REQ)


def test_forbidden_replacement_reasons_are_refused_even_if_listed():
    inv = inventory([candidate(i) for i in range(1, 6)])
    draw = draw_claims(inv, SEED)
    for reason in (
        "unfavorable_result",
        "observed_cost",
        "INCONCLUSIVE verdict",
        "budget_exceeded",
    ):
        with pytest.raises(InventoryError, match="never a replacement reason"):
            replace_claim(draw, inv, draw.drawn[0], reason, (reason,))
    with pytest.raises(InventoryError, match="never a replacement reason"):
        replace_claim(draw, inv, draw.drawn[0], "typo", ("typo", "bad_result"))


def test_exhausted_replacements_stop_the_draw_and_keep_the_record():
    inv = inventory([candidate(1), candidate(2, "comparison")])
    draw = draw_claims(inv, SEED)
    comparison = inv["candidates"][1]["candidate_id"]
    with pytest.raises(inv_mod.ReplacementExhaustedError) as caught:
        replace_claim(draw, inv, comparison, "typo", ("typo",))
    assert caught.value.record["invalidated"] == comparison
    assert "eligible comparison" in str(caught.value)
    value = inv["candidates"][0]["candidate_id"]
    with pytest.raises(inv_mod.ReplacementExhaustedError):
        replace_claim(draw, inv, value, "typo", ("typo",))


def test_publication_needs_the_published_hashes():
    good = [run("2026-10-30T10:00:00Z")]
    with pytest.raises(PublicationError, match="no published inventory hashes"):
        check(SHA, good, ROUND, timedelta(hours=1), True, FILES, {}, REQ)
    bad = {"inventories/2401.01234.json": "not-a-hash"}
    with pytest.raises(PublicationError, match="not a SHA-256"):
        check(SHA, good, ROUND, timedelta(hours=1), True, bad, bad, REQ)


def test_every_required_inventory_must_be_published():
    good = [run("2026-10-30T10:00:00Z")]
    both = {**FILES, "inventories/2402.00001.json": "f" * 64}
    required = list(both)
    # B is in the commit but its hash was not published: refused
    with pytest.raises(PublicationError, match="missing"):
        check(SHA, good, ROUND, timedelta(hours=1), True, both, FILES, required)
    with pytest.raises(PublicationError, match="empty"):
        check(SHA, good, ROUND, timedelta(hours=1), True, FILES, FILES, [])
    proof = check(SHA, good, ROUND, timedelta(hours=1), True, both, both, required)
    assert proof.commit_sha == SHA


def test_the_round_time_is_recorded_in_utc():
    from datetime import timezone

    brt = timezone(timedelta(hours=-3))
    local = datetime(2026, 11, 1, 9, 0, 0, tzinfo=brt)  # 12:00 UTC
    proof = check(
        SHA, [run("2026-10-30T10:00:00Z")], local, timedelta(minutes=90), True, FILES, FILES, REQ
    )
    assert proof.round_published_at == "2026-11-01T12:00:00Z" and proof.margin_seconds == 5400.0


def test_fetch_push_runs_reads_the_api_offline():
    seen = []

    def get_json(url):
        seen.append(url)
        return {"workflow_runs": [run("2026-10-30T10:00:00Z")], "total_count": 1}

    runs = fetch_push_runs("owner/repo", SHA, get_json)
    assert runs[0]["head_sha"] == SHA and f"head_sha={SHA}" in seen[0] and "event=push" in seen[0]
    with pytest.raises(PublicationError):
        fetch_push_runs("owner/repo", SHA, lambda url: {})


# ---- #59, the Codex review of #82 (the maintainer's approval of 2026-10-17) -------------------


@pytest.mark.parametrize(
    ("extra", "message"),
    [
        ({"repository": {"full_name": "other/repo"}}, "not a run of owner/repo"),
        ({"head_repository": {"full_name": "fork/repo"}}, "head repository is not owner/repo"),
        ({"head_repository": None}, "head repository is not owner/repo"),
        ({"path": ".github/workflows/other.yml"}, "not a run of the workflow"),
        ({"run_attempt": 0}, "run_attempt must be a positive integer"),
        ({"run_attempt": None}, "run_attempt must be a positive integer"),
    ],
)
def test_the_proof_is_bound_to_the_repository_and_the_workflow(extra, message):
    with pytest.raises(PublicationError, match=message):
        check(
            SHA,
            [run("2026-10-30T10:00:00Z", **extra)],
            ROUND,
            timedelta(hours=1),
            True,
            FILES,
            FILES,
            REQ,
        )


@pytest.mark.parametrize(
    ("repository", "workflow", "message"),
    [
        ("not a repo", WORKFLOW, "repository must be owner/name"),
        (REPO, "ci.yml", "workflow_path must be"),
    ],
)
def test_the_protocol_fixes_a_valid_repository_and_workflow(repository, workflow, message):
    with pytest.raises(PublicationError, match=message):
        check(
            SHA,
            [run("2026-10-30T10:00:00Z")],
            ROUND,
            timedelta(hours=1),
            True,
            FILES,
            FILES,
            REQ,
            repository=repository,
            workflow_path=workflow,
        )


def test_a_rerun_keeps_its_creation_time_and_records_its_attempt():
    """A re-run keeps id and created_at and raises run_attempt; run_started_at moves (run
    38896912610 of this repository): the proof reads created_at only."""
    rerun = run("2026-10-30T10:00:00Z", run_attempt=2, run_started_at="2026-11-02T09:00:00Z")
    proof = check(SHA, [rerun], ROUND, timedelta(hours=1), True, FILES, FILES, REQ)
    assert proof.run_created_at == "2026-10-30T10:00:00Z" and proof.run_attempt == 2
    assert proof.repository == REPO and proof.workflow_path == WORKFLOW
    assert proof.inventory_hashes == tuple(sorted(FILES.items()))


def test_several_push_runs_give_the_earliest_creation_and_a_repeat_is_refused():
    runs = [
        run("2026-10-31T10:00:00Z", run_id=2),
        run("2026-10-30T10:00:00Z", run_id=1),
    ]
    proof = check(SHA, runs, ROUND, timedelta(hours=1), True, FILES, FILES, REQ)
    assert proof.run_id == 1
    with pytest.raises(PublicationError, match="repeats a run"):
        check(
            SHA,
            [*runs, run("2026-10-30T10:00:00Z", run_id=1)],
            ROUND,
            timedelta(hours=1),
            True,
            FILES,
            FILES,
            REQ,
        )
    # a run of another repository among them refuses the whole listing
    with pytest.raises(PublicationError, match="not a run of owner/repo"):
        check(
            SHA,
            [*runs, run("2026-10-29T10:00:00Z", run_id=3, repository={"full_name": "other/repo"})],
            ROUND,
            timedelta(hours=1),
            True,
            FILES,
            FILES,
            REQ,
        )


def test_fetch_push_runs_reads_every_page():
    pages = {
        1: [run("2026-10-30T10:00:00Z", run_id=i) for i in range(1, 101)],
        2: [run("2026-10-30T10:00:00Z", run_id=i) for i in range(101, 151)],
    }
    seen = []

    def get_json(url):
        seen.append(url)
        page = int(url.rsplit("page=", 1)[1])
        return {"workflow_runs": pages.get(page, []), "total_count": 150}

    runs = fetch_push_runs("owner/repo", SHA, get_json)
    assert len(runs) == 150 and len(seen) == 2
    assert all("per_page=100" in u for u in seen) and seen[1].endswith("page=2")


@pytest.mark.parametrize(
    ("answers", "message"),
    [
        ([{"workflow_runs": [run("2026-10-30T10:00:00Z")]}], "no total_count"),
        ([{"workflow_runs": [], "total_count": 2}], "read 0 runs, the API counts 2"),
        (
            [
                {"workflow_runs": [run("2026-10-30T10:00:00Z")], "total_count": 2},
                {"workflow_runs": [run("2026-10-30T10:00:00Z", run_id=2)], "total_count": 3},
            ],
            "total_count changed",
        ),
    ],
)
def test_a_short_or_inconsistent_listing_is_refused(answers, message):
    calls = iter(answers)
    with pytest.raises(PublicationError, match=message):
        fetch_push_runs("owner/repo", SHA, lambda url: next(calls))


def test_a_walk_that_runs_out_of_input_is_not_complete():
    decisions = {
        "2401.00001": TriageResult(ACCEPTED, ACCEPTED, "triage record 1"),
        "2401.00002": TriageResult(REJECTED, "requires_gpu", "README: CUDA only"),
    }
    log = walk(
        list(decisions), decisions.__getitem__, 2, RetryPolicy(1, 0.0), no_sleep, lambda: NOW
    )
    assert log.outcome == INPUT_EXHAUSTED and not log.complete and not log.stopped
    assert "input_exhausted (1 of 2 accepted)" in log_markdown(log)
    full = walk(
        list(decisions), decisions.__getitem__, 1, RetryPolicy(1, 0.0), no_sleep, lambda: NOW
    )
    assert full.outcome == SAMPLE_FILLED and full.complete


def test_transient_query_classifies_adapter_failures():
    import urllib.error

    def raising(exc):
        def query():
            raise exc

        return query

    def http(code):
        return urllib.error.HTTPError("https://example.org", code, "status", {}, None)

    for exc, text in (
        (http(503), "arXiv listing: HTTP 503"),
        (TimeoutError(), "arXiv listing: TimeoutError"),
        (ConnectionResetError(), "arXiv listing: ConnectionResetError"),
        (urllib.error.URLError(TimeoutError()), "arXiv listing: TimeoutError"),
    ):
        with pytest.raises(TransientError, match=text):
            transient_query(raising(exc), "arXiv listing")
    with pytest.raises(urllib.error.HTTPError):
        transient_query(raising(http(404)), "arXiv listing")
    with pytest.raises(ValueError):
        transient_query(raising(ValueError("bad JSON")), "arXiv listing")
    assert transient_query(lambda: 7, "arXiv listing") == 7


def test_the_claim_draw_of_the_flow_needs_the_publication_proof():
    inv = inventory([candidate(i) for i in range(1, 6)])
    digest = inv_mod.inventory_sha256(inv)
    files = {"inventories/2401.01234.json": digest}
    proof = check(
        SHA,
        [run("2026-10-30T10:00:00Z")],
        ROUND,
        timedelta(hours=1),
        True,
        files,
        files,
        list(files),
    )
    assert inv_mod.draw_published_claims(inv, SEED, proof) == draw_claims(inv, SEED)
    other = check(
        SHA, [run("2026-10-30T10:00:00Z")], ROUND, timedelta(hours=1), True, FILES, FILES, REQ
    )
    with pytest.raises(InventoryError, match="not one the publication proof covers"):
        inv_mod.draw_published_claims(inv, SEED, other)
    with pytest.raises(InventoryError, match="needs the publication proof"):
        inv_mod.draw_published_claims(inv, SEED, {"inventory_hashes": [("x", digest)]})
