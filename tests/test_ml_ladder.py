"""ML pack: the build ladder and the allowed patches (WP3 W3.9), offline. Each case goes
through the WP2 core (``aggregate_claim``) to show the verdict path of the
``environment_build`` gate."""

import hashlib

import pytest

from refute.core.paper import BASE_GATES, FailureCause, aggregate_claim
from refute.core.verdict import PaperVerdict, Severity, TestResult, TestStatus
from refute.packs.ml import ladder as ld
from refute.packs.ml.orchestrate import Outcome

PROCEDURE = ld.RungResult(Outcome.FAILED, FailureCause.BUILD_LADDER, "pip: no matching dist")
BUILT = ld.RungResult(Outcome.COMPLETED)


def full_ladder():
    return ld.ladder_rungs("Dockerfile", "requirements.txt", ["3.10", "3.11"])


def runner(*results):
    """A build that returns the given results in order and records the rungs it saw."""
    seen, queue = [], list(results)

    def build(rung):
        seen.append(rung.name)
        return queue.pop(0)

    return build, seen


def verdict(result):
    return aggregate_claim(
        [result.gate],
        [],
        [],
        metric_recompute_applies=False,
        failures={ld.GATE: result.failure} if result.failure else None,
    ).verdict


# ---- rungs ----------------------------------------------------------------------------------


def test_the_rungs_come_from_the_inputs_found_and_the_python_ladder():
    rungs = full_ladder()
    assert [(r.name, r.applicable, r.python) for r in rungs] == [
        ("own_environment", True, None),
        ("requirements_compiled", True, "3.10"),
        ("requirements_compiled_next_python", True, "3.11"),
    ]
    only_req = ld.ladder_rungs(None, "requirements.txt", ["3.10"])
    assert [r.applicable for r in only_req] == [False, True, False]
    assert only_req[2].reason == "no next Python version in the ladder"
    nothing = ld.ladder_rungs(None, None, ["3.10", "3.11"])
    assert [r.applicable for r in nothing] == [False, False, False]
    with pytest.raises(ValueError, match="non-empty"):
        ld.ladder_rungs(None, None, [])


def test_the_ladder_order_is_fixed():
    rungs = full_ladder()
    with pytest.raises(ValueError, match="fixed"):
        ld.run_ladder([rungs[1], rungs[0], rungs[2]], lambda r: BUILT)
    with pytest.raises(ValueError, match="fixed"):
        ld.run_ladder(rungs[:2], lambda r: BUILT)


# ---- the first rung that builds is used; every attempt is logged ----------------------------


def test_the_first_rung_that_builds_is_used():
    build, seen = runner(PROCEDURE, BUILT, BUILT)
    result = ld.run_ladder(full_ladder(), build)
    assert result.built_with == "requirements_compiled" and seen == RUNGS_FIRST_TWO
    assert result.gate.status is TestStatus.PASS and result.failure is None
    log = result.gate.metrics["attempts"]
    assert [(a["rung"], a["reached"], a["outcome"], a["python"]) for a in log] == [
        ("own_environment", True, "failed", None),
        ("requirements_compiled", True, "completed", "3.10"),
        ("requirements_compiled_next_python", False, None, "3.11"),
    ]
    assert log[0]["detail"] == "pip: no matching dist"
    assert verdict(result) is not PaperVerdict.NOT_REPRODUCIBLE


RUNGS_FIRST_TWO = ["own_environment", "requirements_compiled"]


def test_a_built_gate_with_every_other_check_complete_gives_the_claims_own_verdict():
    """#59 (Codex, round 1 of #94): the gate of a ladder that built, next to the other base
    gates and the fatal check, all complete, leaves the verdict to the claim itself:
    REPRODUCED when the base reproduction passes, NOT_REPRODUCED when it fails."""
    build, _ = runner(PROCEDURE, BUILT)
    result = ld.run_ladder(full_ladder(), build)
    assert result.gate.status is TestStatus.PASS
    others = [
        TestResult(name, TestStatus.PASS, Severity.GATE, "", coverage=1, coverage_unit="items")
        for name in BASE_GATES
        if name != ld.GATE
    ]

    def claim(status):
        fatal = TestResult(
            "base_reproduction", status, Severity.FATAL, "", coverage=1, coverage_unit="items"
        )
        return aggregate_claim(
            [result.gate, *others, fatal], [], [], metric_recompute_applies=False
        ).verdict

    assert claim(TestStatus.PASS) is PaperVerdict.REPRODUCED
    assert claim(TestStatus.FAIL) is PaperVerdict.NOT_REPRODUCED


def test_a_rung_that_does_not_apply_is_logged_and_skipped():
    build, seen = runner(BUILT)
    rungs = ld.ladder_rungs(None, "requirements.txt", ["3.10", "3.11"])
    result = ld.run_ladder(rungs, build)
    assert seen == ["requirements_compiled"] and result.built_with == "requirements_compiled"
    first = result.gate.metrics["attempts"][0]
    assert first["applicable"] is False and first["reason"] == "no own environment file"


# ---- attribution (plan 8.2) ------------------------------------------------------------------


def test_every_rung_failing_by_its_procedure_is_not_reproducible():
    """The controlled NOT_REPRODUCIBLE of the exit criterion (WP4 W4.3) at the build."""
    build, seen = runner(PROCEDURE, PROCEDURE, PROCEDURE)
    result = ld.run_ladder(full_ladder(), build)
    assert seen == list(ld.RUNGS)
    assert result.gate.status is TestStatus.FAIL and result.gate.coverage == 3
    assert result.failure == ld.GateFailure(FailureCause.BUILD_LADDER, 3, 3)
    assert verdict(result) is PaperVerdict.NOT_REPRODUCIBLE


def test_a_rung_that_did_not_apply_leaves_the_attempts_incomplete():
    """Literal reading of plan line 672: every rung of the ladder must run to its end."""
    build, _ = runner(PROCEDURE, PROCEDURE)
    rungs = ld.ladder_rungs(None, "requirements.txt", ["3.10", "3.11"])
    result = ld.run_ladder(rungs, build)
    assert result.failure == ld.GateFailure(FailureCause.BUILD_LADDER, 2, 3)
    assert verdict(result) is PaperVerdict.INCONCLUSIVE


@pytest.mark.parametrize(
    ("outcome", "cause"),
    [
        (Outcome.BUDGET_EXHAUSTED, FailureCause.BUDGET_EXHAUSTED),
        (Outcome.OPERATIONAL_GUARD, FailureCause.OPERATIONAL_GUARD),
        (Outcome.REFUTE_ERROR, FailureCause.REFUTE_ERROR),
        (Outcome.NOT_EXECUTED, FailureCause.INTERRUPTED),
    ],
)
def test_the_twin_on_refutes_side_stops_the_ladder_and_is_inconclusive(outcome, cause):
    """The twin of the controlled case (WP4 W4.3): the same failures, then a stop on
    Refute's side, is INCONCLUSIVE and never NOT_REPRODUCIBLE; the next rung is not
    tried in place of the interrupted one."""
    build, seen = runner(PROCEDURE, ld.RungResult(outcome, None, "stopped"), BUILT)
    result = ld.run_ladder(full_ladder(), build)
    assert seen == RUNGS_FIRST_TWO
    assert result.gate.status is TestStatus.INCONCLUSIVE and result.failure.cause is cause
    assert result.gate.metrics["attempts"][2]["reached"] is False
    assert verdict(result) is PaperVerdict.INCONCLUSIVE


@pytest.mark.parametrize(
    "cause",
    [None, FailureCause.TRANSIENT_NETWORK, FailureCause.UNDETERMINED, FailureCause.ARTIFACT_ABSENT],
)
def test_a_failure_that_is_not_an_error_of_the_procedure_never_counts(cause):
    build, seen = runner(PROCEDURE, ld.RungResult(Outcome.FAILED, cause), PROCEDURE)
    result = ld.run_ladder(full_ladder(), build)
    assert seen == RUNGS_FIRST_TWO
    assert result.failure.cause in (FailureCause.TRANSIENT_NETWORK, FailureCause.UNDETERMINED)
    assert verdict(result) is PaperVerdict.INCONCLUSIVE


def test_a_build_that_raises_is_a_refute_error():
    def build(rung):
        raise OSError("docker daemon not reachable")

    result = ld.run_ladder(full_ladder(), build)
    assert result.failure.cause is FailureCause.REFUTE_ERROR
    assert "docker daemon not reachable" in result.gate.message
    assert verdict(result) is PaperVerdict.INCONCLUSIVE
    bad = ld.run_ladder(full_ladder(), lambda rung: "built")
    assert bad.failure.cause is FailureCause.REFUTE_ERROR


def test_no_applicable_rung_gives_no_conclusion():
    result = ld.run_ladder(ld.ladder_rungs(None, None, ["3.10"]), lambda rung: BUILT)
    assert result.gate.status is TestStatus.INCONCLUSIVE and result.gate.coverage == 0
    assert verdict(result) is PaperVerdict.INCONCLUSIVE


# ---- allowed patches -------------------------------------------------------------------------


def test_only_a_listed_patch_with_its_locked_hash_is_allowed():
    data = b"--- a/train.py\n+++ b/train.py\n@@ -1 +1 @@\n-cuda\n+cpu\n"
    digest = hashlib.sha256(data).hexdigest()
    allowed = [ld.AllowedPatch("patches/cpu.diff", digest)]
    assert ld.check_patch("patches/cpu.diff", data, allowed) == digest
    with pytest.raises(ld.PatchRefusedError, match="not in the allowed list"):
        ld.check_patch("patches/other.diff", data, allowed)
    with pytest.raises(ld.PatchRefusedError, match="differs"):
        ld.check_patch("patches/cpu.diff", data + b" ", allowed)
    with pytest.raises(ld.PatchRefusedError, match="not in the allowed list"):
        ld.check_patch("patches/cpu.diff", data, [])
