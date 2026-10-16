"""The fallback step of the orchestrator (the build ladder as one setup step, WP3
integration requirement 2), offline, with a fake backend."""

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


def run(tmp_path, exits, fallback):
    rungs = ["setup/r1", "setup/r2", "setup/r3"]
    step = orc.Step("build", [container(tmp_path, r) for r in rungs], fallback=fallback)
    claim = orc.ClaimPlan(
        "C1", [orc.Step("run", [container(tmp_path, "C1/run")])], [], lambda records: True
    )
    plan = orc.PaperPlan([step], [claim])
    backend = Fake({**exits, "C1/run": 0})
    acc = bg.Accountant(["C1"], margin_usec=100, base_pool_usec=100_000, attack_pool_base_usec=0)
    return orc.PaperRunner(plan, backend, acc).run(), backend, acc


def test_the_step_stops_at_the_first_container_that_completes(tmp_path):
    out, backend, acc = run(tmp_path, {"setup/r1": 1, "setup/r2": 0, "setup/r3": 0}, lambda r: True)
    setup = out.steps[0]
    assert setup.outcome is orc.Outcome.COMPLETED
    assert [c.container_id for c in setup.containers] == ["setup/r1", "setup/r2"]
    assert backend.calls == ["setup/r1", "setup/r2", "C1/run"]
    assert acc.total_charged() == 3000  # every container that ran is accounted


def test_every_container_failing_with_the_fallback_saying_go_on_fails_the_step(tmp_path):
    out, backend, _ = run(
        tmp_path, dict.fromkeys(["setup/r1", "setup/r2", "setup/r3"], 2), lambda r: True
    )
    assert out.steps[0].outcome is orc.Outcome.FAILED
    assert len(out.steps[0].containers) == 3
    assert "C1/run" not in backend.calls  # the base does not run without the setup


def test_the_fallback_saying_stop_ends_the_step_at_that_failure(tmp_path):
    out, backend, _ = run(tmp_path, {"setup/r1": 1, "setup/r2": 0, "setup/r3": 0}, lambda r: False)
    assert out.steps[0].outcome is orc.Outcome.FAILED
    assert backend.calls == ["setup/r1"]


def test_a_guard_stop_ends_the_step_with_its_own_outcome(tmp_path):
    exits = {"setup/r1": sb.STOP_NO_PROGRESS, "setup/r2": 0, "setup/r3": 0}
    out, backend, _ = run(tmp_path, exits, lambda r: True)
    assert out.steps[0].outcome is orc.Outcome.OPERATIONAL_GUARD
    assert backend.calls == ["setup/r1"]


def test_a_fallback_that_raises_is_a_refute_error(tmp_path):
    def broken(record):
        raise RuntimeError("no classification")

    out, _, _ = run(tmp_path, {"setup/r1": 1, "setup/r2": 0, "setup/r3": 0}, broken)
    assert out.steps[0].outcome is orc.Outcome.REFUTE_ERROR
    assert "the fallback failed" in out.steps[0].reason
    assert not out.accounting_valid


def test_only_a_fallback_step_may_hold_several_setup_containers(tmp_path):
    step = orc.Step("build", [container(tmp_path, "a"), container(tmp_path, "b")])
    claim = orc.ClaimPlan(
        "C1", [orc.Step("run", [container(tmp_path, "C1/run")])], [], lambda r: True
    )
    with pytest.raises(ValueError, match="one container at a time"):
        orc.PaperPlan([step], [claim])
