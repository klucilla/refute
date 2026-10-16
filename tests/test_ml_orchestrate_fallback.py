"""The fallback step of the orchestrator (the build ladder as one setup step, WP3
integration requirement 2), offline, with a fake backend. The fallback classifies each
container once: "completed", "next" or "stop"."""

import pytest

from refute.core import budget as bg
from refute.packs.ml import orchestrate as orc
from refute.packs.ml import sandbox as sb


class Fake:
    name = "fake"

    def __init__(self, exits):
        self.exits, self.calls = exits, []

    def run(self, spec):
        cid = spec.env["CID"]
        self.calls.append(cid)
        code = self.exits[cid]
        stopped = code if isinstance(code, str) else None
        return sb.RunResult(None if stopped else code, 1000, stopped, 0.0, spec.log_path)


def container(tmp_path, cid):
    def make(f):
        return sb.RunSpec(
            argv=["x"],
            workdir=tmp_path,
            env={"CID": cid},
            log_path=tmp_path / f"{cid.replace('/', '_')}.log",
            threshold_usec=f,
            active_time_limit_s=10.0,
            no_progress_s=10.0,
        )

    return orc.Container(cid, make)


def by_exit(record):
    """Built when the container exited 0; an error of the procedure otherwise."""
    if record.result.stopped:
        return "stop"
    return "completed" if record.result.exit_code == 0 else "next"


def run(tmp_path, exits, fallback=by_exit):
    rungs = ["setup/r1", "setup/r2", "setup/r3"]
    step = orc.Step("build", [container(tmp_path, r) for r in rungs], fallback=fallback)
    claim = orc.ClaimPlan(
        "C1", [orc.Step("run", [container(tmp_path, "C1/run")])], [], lambda records: True
    )
    plan = orc.PaperPlan([step], [claim])
    backend = Fake({**exits, "C1/run": 0})
    acc = bg.Accountant(["C1"], margin_usec=100, base_pool_usec=100_000, attack_pool_base_usec=0)
    return orc.PaperRunner(plan, backend, acc).run(), backend, acc


def test_the_step_stops_at_the_first_container_classified_as_built(tmp_path):
    out, backend, acc = run(tmp_path, {"setup/r1": 1, "setup/r2": 0, "setup/r3": 0})
    setup = out.steps[0]
    assert setup.outcome is orc.Outcome.COMPLETED
    assert [c.container_id for c in setup.containers] == ["setup/r1", "setup/r2"]
    assert backend.calls == ["setup/r1", "setup/r2", "C1/run"]
    assert acc.total_charged() == 3000  # every container that ran is accounted


def test_every_container_classified_next_fails_the_step(tmp_path):
    out, backend, _ = run(tmp_path, dict.fromkeys(["setup/r1", "setup/r2", "setup/r3"], 2))
    assert out.steps[0].outcome is orc.Outcome.FAILED
    assert len(out.steps[0].containers) == 3
    assert "C1/run" not in backend.calls  # the base does not run without the setup


def test_stop_ends_the_step_at_that_container(tmp_path):
    out, backend, _ = run(tmp_path, {"setup/r1": 1, "setup/r2": 0, "setup/r3": 0}, lambda r: "stop")
    assert out.steps[0].outcome is orc.Outcome.FAILED
    assert backend.calls == ["setup/r1"]


def test_an_exit_0_not_classified_as_built_fails_the_step(tmp_path):
    """Codex review of #110: the classification, not the exit code, decides; a container
    that exited 0 but is not a success ends the step as FAILED, with no next rung."""
    out, backend, _ = run(
        tmp_path, dict.fromkeys(["setup/r1", "setup/r2", "setup/r3"], 0), lambda r: "stop"
    )
    assert out.steps[0].outcome is orc.Outcome.FAILED
    assert backend.calls == ["setup/r1"]


def test_a_non_zero_exit_classified_as_built_completes_the_step(tmp_path):
    out, _, _ = run(tmp_path, {"setup/r1": 5, "setup/r2": 0, "setup/r3": 0}, lambda r: "completed")
    assert out.steps[0].outcome is orc.Outcome.COMPLETED


@pytest.mark.parametrize("decision", ["completed", "next", "stop"])
@pytest.mark.parametrize(
    ("stop", "outcome"),
    [
        (sb.STOP_THRESHOLD, orc.Outcome.BUDGET_EXHAUSTED),
        (sb.STOP_ACTIVE_TIME, orc.Outcome.OPERATIONAL_GUARD),
        (sb.STOP_NO_PROGRESS, orc.Outcome.OPERATIONAL_GUARD),
    ],
)
def test_a_stop_on_refutes_side_is_never_overridden(tmp_path, stop, outcome, decision):
    """Codex review of #110: whatever the classification answers, a container stopped by
    its threshold or a guard ends the step with that outcome, and no next rung runs."""
    asked = []

    def fallback(record):
        asked.append(record.container_id)
        return decision

    exits = {"setup/r1": stop, "setup/r2": 0, "setup/r3": 0}
    out, backend, _ = run(tmp_path, exits, fallback)
    assert out.steps[0].outcome is outcome
    assert backend.calls == ["setup/r1"] and asked == []


def test_a_guard_stop_ends_the_step_with_its_own_outcome(tmp_path):
    exits = {"setup/r1": sb.STOP_NO_PROGRESS, "setup/r2": 0, "setup/r3": 0}
    out, backend, _ = run(tmp_path, exits)
    assert out.steps[0].outcome is orc.Outcome.OPERATIONAL_GUARD
    assert backend.calls == ["setup/r1"]


@pytest.mark.parametrize("fallback", [lambda r: 1 / 0, lambda r: "maybe"])
def test_a_fallback_that_raises_or_answers_nonsense_is_a_refute_error(tmp_path, fallback):
    out, _, _ = run(tmp_path, {"setup/r1": 1, "setup/r2": 0, "setup/r3": 0}, fallback)
    assert out.steps[0].outcome is orc.Outcome.REFUTE_ERROR
    assert not out.accounting_valid


def test_only_a_fallback_step_may_hold_several_setup_containers(tmp_path):
    step = orc.Step("build", [container(tmp_path, "a"), container(tmp_path, "b")])
    claim = orc.ClaimPlan(
        "C1", [orc.Step("run", [container(tmp_path, "C1/run")])], [], lambda r: True
    )
    with pytest.raises(ValueError, match="one container at a time"):
        orc.PaperPlan([step], [claim])
