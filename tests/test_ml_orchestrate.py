"""ML pack runner, part 2: execution of a paper in phases with the WP2 accountant (WP3
design D-S4), offline. A fake backend gives the usage, exit code and stop reason of each
container; the last test runs synthetic commands on the real subprocess backend."""

import os
import sys
import textwrap
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from refute.core import budget as bg
from refute.packs.ml import orchestrate as orc
from refute.packs.ml import sandbox as sb

M = 100  # stopping margin of the tests, in microseconds


class Fake:
    """A backend whose containers behave as told: usage (an int, or a function of F),
    exit code, stop reason, an exception, or a barrier to prove they run together."""

    name = "fake"

    def __init__(self, behavior=None):
        self.behavior = behavior or {}
        self.calls = []
        self.lock = threading.Lock()

    def run(self, spec):
        cid = spec.env["CID"]
        with self.lock:
            self.calls.append((cid, spec.threshold_usec))
        b = self.behavior.get(cid, {})
        if "barrier" in b:
            b["barrier"].wait(timeout=10)
        if "raise" in b:
            raise OSError(b["raise"])
        usage = b.get("usage", 1000)
        if callable(usage):
            usage = usage(spec.threshold_usec)
        stopped = b.get("stopped")
        exit_code = None if stopped else b.get("exit", 0)
        return sb.RunResult(exit_code, usage, stopped, 0.0, spec.log_path)


def container(tmp_path, cid, threshold=None):
    def make(f):
        return sb.RunSpec(
            argv=["x"],
            workdir=tmp_path,
            env={"CID": cid},
            log_path=tmp_path / f"{cid.replace('/', '_')}.log",
            threshold_usec=f if threshold is None else threshold,
            active_time_limit_s=10.0,
            no_progress_s=10.0,
        )

    return orc.Container(cid, make)


def step(tmp_path, name, *cids):
    return orc.Step(name, [container(tmp_path, c) for c in cids])


def claim(tmp_path, key, base, attacks, obtained=True):
    return orc.ClaimPlan(
        key,
        [step(tmp_path, n, *cids) for n, cids in base],
        [step(tmp_path, n, *cids) for n, cids in attacks],
        lambda records, ok=obtained: ok,
    )


def paper(tmp_path, claims, setup=(("build", ("setup/build",)),)):
    return orc.PaperPlan([step(tmp_path, n, *cids) for n, cids in setup], claims)


def accountant(keys, base=10_000, attacks=6_000):
    return bg.Accountant(keys, margin_usec=M, base_pool_usec=base, attack_pool_base_usec=attacks)


def two_claims(tmp_path, obtained=(True, True)):
    return paper(
        tmp_path,
        [
            claim(
                tmp_path,
                "C1",
                [("run", ("C1/run",)), ("recompute", ("C1/r1", "C1/r2"))],
                [("seeds", ("C1/seeds",))],
                obtained[0],
            ),
            claim(tmp_path, "C2", [("run", ("C2/run",))], [("seeds", ("C2/seeds",))], obtained[1]),
        ],
    )


def outcomes(run):
    return [(s.phase, s.claim, s.step, s.outcome) for s in run.steps]


# ---- order and thresholds (D-S4, WP2 reserves) -----------------------------------------------


def test_setup_then_every_base_then_attacks_with_the_wp2_thresholds(tmp_path):
    backend = Fake()
    run = orc.PaperRunner(two_claims(tmp_path), backend, accountant(["C1", "C2"])).run()
    # Setup: the whole base pool, F = 10000 - M. S = 1000, base reserve (10000-1000)//2.
    # C1 run: 9000 - 4500 reserved for C2 -> R 4500. C1 recompute, 2 containers:
    # (8000 - 4500) // 2 = 1750 each. C2: 10000 - 4000 used -> 6000. Attack pool:
    # 6000 + base balance 5000 = 11000, reserve 5500; C1 gets 5500, then C2 10000.
    assert backend.calls[:2] == [("setup/build", 9_900), ("C1/run", 4_400)]
    assert sorted(backend.calls[2:4]) == [("C1/r1", 1_650), ("C1/r2", 1_650)]  # in parallel
    assert backend.calls[4:] == [("C2/run", 5_900), ("C1/seeds", 5_400), ("C2/seeds", 9_900)]
    order = [c for c, _ in backend.calls]
    assert order.index("C2/run") < order.index("C1/seeds")  # every base before any attack
    assert all(s.outcome is orc.Outcome.COMPLETED for s in run.steps)
    assert run.base_obtained == {"C1": True, "C2": True}
    assert run.attack_claims == ["C1", "C2"] and not run.no_distribution
    assert run.accounting_valid and run.completeness == orc.COMPLETENESS_NOT_APPLICABLE


def test_containers_of_one_step_start_together(tmp_path):
    barrier = threading.Barrier(2)
    backend = Fake({"C1/r1": {"barrier": barrier}, "C1/r2": {"barrier": barrier}})
    run = orc.PaperRunner(two_claims(tmp_path), backend, accountant(["C1", "C2"])).run()
    record = run.of("base", "C1")[1]
    assert record.outcome is orc.Outcome.COMPLETED  # the barrier needed both at once
    assert [c.container_id for c in record.containers] == ["C1/r1", "C1/r2"]


# ---- how a step ends ---------------------------------------------------------------------------


def test_a_failed_base_step_skips_the_rest_of_that_claim_only(tmp_path):
    backend = Fake({"C1/run": {"exit": 2}})
    run = orc.PaperRunner(two_claims(tmp_path), backend, accountant(["C1", "C2"])).run()
    assert outcomes(run)[1:3] == [
        ("base", "C1", "run", orc.Outcome.FAILED),
        ("base", "C1", "recompute", orc.Outcome.NOT_EXECUTED),
    ]
    assert run.base_obtained == {"C1": False, "C2": True}
    assert run.attack_claims == ["C2"]
    skipped = run.of("attacks", "C1")[0]
    assert skipped.outcome is orc.Outcome.NOT_EXECUTED and "not eligible" in skipped.reason
    assert run.accounting_valid


def test_base_not_obtained_by_the_gates_gives_no_attacks(tmp_path):
    run = orc.PaperRunner(
        two_claims(tmp_path, obtained=(False, False)), Fake(), accountant(["C1", "C2"])
    ).run()
    assert run.no_distribution and run.attack_claims == []
    assert all(s.outcome is orc.Outcome.NOT_EXECUTED for s in run.steps if s.phase == "attacks")


def test_the_threshold_is_budget_exhaustion_never_a_failure_of_the_artifact(tmp_path):
    backend = Fake({"C1/run": {"stopped": sb.STOP_THRESHOLD, "usage": lambda f: f + 10}})
    run = orc.PaperRunner(two_claims(tmp_path), backend, accountant(["C1", "C2"])).run()
    record = run.of("base", "C1")[0]
    assert record.outcome is orc.Outcome.BUDGET_EXHAUSTED and "threshold" in record.reason
    assert run.base_obtained["C1"] is False and run.accounting_valid  # within R = F + M


@pytest.mark.parametrize("stop", [sb.STOP_ACTIVE_TIME, sb.STOP_NO_PROGRESS])
def test_a_guard_is_an_operational_stop(tmp_path, stop):
    run = orc.PaperRunner(
        two_claims(tmp_path), Fake({"C2/run": {"stopped": stop}}), accountant(["C1", "C2"])
    ).run()
    assert run.of("base", "C2")[0].outcome is orc.Outcome.OPERATIONAL_GUARD


def test_a_refused_grant_names_the_pool(tmp_path):
    # the setup leaves less than the reserve of C2 plus M: C1's grant is refused
    # S = 5000, reserve 2500. C1 run: R = 5000 - 2500 = 2500, uses 2400. Recompute, two
    # containers: (2600 - 2500) // 2 = 50 each, below M: refused.
    backend = Fake({"setup/build": {"usage": 5_000}, "C1/run": {"usage": 2_400}})
    plan = two_claims(tmp_path)
    run = orc.PaperRunner(plan, backend, accountant(["C1", "C2"], base=10_000)).run()
    first = run.of("base", "C1")
    assert first[0].outcome is orc.Outcome.COMPLETED
    assert first[1].outcome is orc.Outcome.BUDGET_EXHAUSTED
    assert first[1].reason == "budget_exhausted (base)"
    assert run.accounting_valid


def test_a_setup_that_exhausts_the_base_pool_stops_every_claim(tmp_path):
    backend = Fake({"setup/build": {"usage": 9_950}})
    run = orc.PaperRunner(two_claims(tmp_path), backend, accountant(["C1", "C2"])).run()
    assert run.setup_exhausted
    for key in ("C1", "C2"):
        for record in run.of("base", key):
            assert record.outcome is orc.Outcome.NOT_EXECUTED
            assert record.reason == "budget_exhausted (setup)"
    assert run.no_distribution and run.accounting_valid


def test_a_failed_setup_runs_no_claim(tmp_path):
    run = orc.PaperRunner(
        two_claims(tmp_path), Fake({"setup/build": {"exit": 1}}), accountant(["C1", "C2"])
    ).run()
    assert run.steps[0].outcome is orc.Outcome.FAILED
    assert all(
        s.outcome is orc.Outcome.NOT_EXECUTED and s.reason == "the setup did not complete"
        for s in run.steps
        if s.phase == "base"
    )
    assert run.no_distribution


def test_attacks_are_independent_of_each_other(tmp_path):
    plan = paper(
        tmp_path,
        [
            claim(
                tmp_path,
                "C1",
                [("run", ("C1/run",))],
                [("seeds", ("C1/s",)), ("data_split", ("C1/d",)), ("leakage", ("C1/l",))],
            )
        ],
    )
    backend = Fake({"C1/s": {"exit": 1}, "C1/d": {"stopped": sb.STOP_NO_PROGRESS}})
    run = orc.PaperRunner(plan, backend, accountant(["C1"])).run()
    assert [s.outcome for s in run.of("attacks", "C1")] == [
        orc.Outcome.FAILED,
        orc.Outcome.OPERATIONAL_GUARD,
        orc.Outcome.COMPLETED,
    ]


# ---- Refute errors stop the paper --------------------------------------------------------------


def test_a_breach_invalidates_the_accounting_and_stops_the_paper(tmp_path):
    backend = Fake({"C1/run": {"usage": lambda f: f + M + 1}})  # above R = F + M
    run = orc.PaperRunner(two_claims(tmp_path), backend, accountant(["C1", "C2"])).run()
    assert run.of("base", "C1")[0].outcome is orc.Outcome.REFUTE_ERROR
    later = [s for s in run.steps[2:]]
    assert later and all(s.outcome is orc.Outcome.NOT_EXECUTED for s in later)
    assert not run.accounting_valid
    assert any("breach" in r for r in run.invalid_reasons)
    assert [c for c, _ in backend.calls] == ["setup/build", "C1/run"]


def test_a_backend_failure_is_a_refute_error_and_stops_the_paper(tmp_path):
    backend = Fake({"C2/run": {"raise": "supervisor lost"}})
    run = orc.PaperRunner(two_claims(tmp_path), backend, accountant(["C1", "C2"])).run()
    record = run.of("base", "C2")[0]
    assert record.outcome is orc.Outcome.REFUTE_ERROR and "supervisor lost" in record.reason
    assert record.containers[0].result is None
    assert all(s.outcome is orc.Outcome.NOT_EXECUTED for s in run.steps if s.phase == "attacks")
    assert not run.accounting_valid and run.stopped


def test_a_run_without_the_threshold_of_its_grant_never_starts(tmp_path):
    plan = orc.PaperPlan(
        [orc.Step("build", [container(tmp_path, "setup/build", threshold=10**9)])],
        [claim(tmp_path, "C1", [("run", ("C1/run",))], [])],
    )
    backend = Fake()
    run = orc.PaperRunner(plan, backend, accountant(["C1"])).run()
    assert run.steps[0].outcome is orc.Outcome.REFUTE_ERROR
    assert "threshold of its grant" in run.steps[0].reason
    assert backend.calls == [] and not run.accounting_valid


def test_a_container_not_started_after_its_grant_stops_the_paper(tmp_path, monkeypatch):
    """Codex review: a failure while starting the containers of a step is recorded; the
    containers already started are waited for and accounted, none is invented."""

    class FlakyPool(ThreadPoolExecutor):
        submitted = 0

        def submit(self, *args, **kwargs):
            type(self).submitted += 1
            if type(self).submitted == 4:  # setup, C1/run, C1/r1, then C1/r2 fails
                raise RuntimeError("cannot start a thread")
            return super().submit(*args, **kwargs)

    monkeypatch.setattr(orc, "ThreadPoolExecutor", FlakyPool)
    acc = accountant(["C1", "C2"])
    run = orc.PaperRunner(two_claims(tmp_path), Fake(), acc).run()
    record = run.of("base", "C1")[1]
    assert record.outcome is orc.Outcome.REFUTE_ERROR
    r1, r2 = record.containers
    assert r1.result is not None and "C1/r1" in acc.records
    assert r2.result is None and r2.error.startswith("not started: RuntimeError")
    assert "C1/r2" in acc.running  # granted, never recorded: the accounting is invalid
    assert not run.accounting_valid and run.stopped
    assert all(s.outcome is orc.Outcome.NOT_EXECUTED for s in run.steps[3:])


def test_a_failing_base_evaluation_is_recorded_and_stops_the_paper(tmp_path):
    def broken(records):
        raise KeyError("metric")

    plan = paper(
        tmp_path,
        [
            orc.ClaimPlan("C1", [step(tmp_path, "run", "C1/run")], [], broken),
            claim(tmp_path, "C2", [("run", ("C2/run",))], [("seeds", ("C2/s",))]),
        ],
    )
    run = orc.PaperRunner(plan, Fake(), accountant(["C1", "C2"])).run()
    failed = run.of("base", "C1")[-1]
    assert failed.step == "base_obtained" and failed.outcome is orc.Outcome.REFUTE_ERROR
    assert "KeyError" in failed.reason
    assert [s.outcome for s in run.of("base", "C2")] == [orc.Outcome.NOT_EXECUTED]
    assert run.base_obtained == {"C1": False, "C2": False} and not run.accounting_valid


def test_an_unknown_stop_reason_is_never_masked_by_a_known_one(tmp_path):
    backend = Fake({"C1/r1": {"stopped": sb.STOP_THRESHOLD}, "C1/r2": {"stopped": "oom_killed"}})
    run = orc.PaperRunner(two_claims(tmp_path), backend, accountant(["C1", "C2"])).run()
    record = run.of("base", "C1")[1]
    assert record.outcome is orc.Outcome.REFUTE_ERROR and "oom_killed" in record.reason


def test_a_rejected_record_is_a_refute_error(tmp_path):
    backend = Fake({"C2/run": {"usage": 1.5}})  # not an integer of microseconds
    run = orc.PaperRunner(two_claims(tmp_path), backend, accountant(["C1", "C2"])).run()
    record = run.of("base", "C2")[0]
    assert record.outcome is orc.Outcome.REFUTE_ERROR and "record rejected" in record.reason
    assert not run.accounting_valid


def test_base_obtained_without_an_applicable_attack_gives_no_attack(tmp_path):
    plan = paper(tmp_path, [claim(tmp_path, "C1", [("run", ("C1/run",))], [])])
    run = orc.PaperRunner(plan, Fake(), accountant(["C1"])).run()
    assert run.base_obtained == {"C1": True}
    assert run.no_distribution and run.attack_claims == [] and run.accounting_valid


def test_two_containers_using_their_whole_reservation_keep_the_next_reserve(tmp_path):
    full = {"usage": lambda f: f + M}  # exactly R = F + M
    backend = Fake({"C1/r1": full, "C1/r2": full})
    acc = accountant(["C1", "C2"])
    run = orc.PaperRunner(two_claims(tmp_path), backend, acc).run()
    # C1 used 1000 + 2 x 1750 = 4500; C2 still gets its whole reserve of 4500
    assert ("C2/run", 4_400) in backend.calls
    assert run.accounting_valid and acc.invariant_holds()


# ---- completeness (W2.10) ------------------------------------------------------------------------


def test_completeness_is_checked_when_a_parent_cgroup_exists(tmp_path):
    def runner(parent, tolerance):
        return orc.PaperRunner(
            two_claims(tmp_path),
            Fake(),
            accountant(["C1", "C2"]),
            parent_usage=lambda: parent,
            tolerance_usec=tolerance,
        ).run()

    total = 7 * 1000  # seven containers of 1000 usec each
    ok = runner(total + 50, 50)
    assert ok.completeness == orc.COMPLETENESS_COMPLETE and ok.accounting_valid
    missing = runner(total + 51, 50)  # for example a builder left out of the records
    assert missing.completeness == orc.COMPLETENESS_INVALID and not missing.accounting_valid


def test_a_failing_parent_reading_makes_the_accounting_invalid(tmp_path):
    def unreadable():
        raise OSError("cpu.stat not readable")

    run = orc.PaperRunner(
        two_claims(tmp_path),
        Fake(),
        accountant(["C1", "C2"]),
        parent_usage=unreadable,
        tolerance_usec=50,
    ).run()
    assert run.completeness == orc.COMPLETENESS_INVALID and not run.accounting_valid
    assert "cpu.stat not readable" in run.stopped


# ---- validation ----------------------------------------------------------------------------------


def test_the_plan_and_the_accountant_must_agree(tmp_path):
    plan = two_claims(tmp_path)
    with pytest.raises(ValueError, match="drawn order"):
        orc.PaperRunner(plan, Fake(), accountant(["C2", "C1"]))
    used = accountant(["C1", "C2"])
    used.grant(bg.SETUP, ["other"])
    with pytest.raises(ValueError, match="new"):
        orc.PaperRunner(plan, Fake(), used)
    with pytest.raises(ValueError, match="together"):
        orc.PaperRunner(plan, Fake(), accountant(["C1", "C2"]), parent_usage=lambda: 0)
    with pytest.raises(ValueError, match="unique in a paper"):
        paper(tmp_path, [claim(tmp_path, "C1", [("run", ("setup/build",))], [])])
    with pytest.raises(ValueError, match="without duplicates"):
        step(tmp_path, "run", "a", "a")
    with pytest.raises(ValueError, match="non-negative"):
        orc.PaperRunner(
            plan, Fake(), accountant(["C1", "C2"]), parent_usage=lambda: 0, tolerance_usec=-1
        )
    with pytest.raises(ValueError, match="one container at a time"):
        paper(tmp_path, [claim(tmp_path, "C1", [], [])], setup=(("build", ("b1", "b2")),))
    with pytest.raises(ValueError, match="step names must be unique"):
        paper(tmp_path, [claim(tmp_path, "C1", [("run", ("x",)), ("run", ("y",))], [])])


# ---- end to end on the subprocess backend --------------------------------------------------------


def test_a_synthetic_paper_on_the_subprocess_backend(tmp_path):
    # each job writes its own file with its start and end times: concurrent appends to
    # one shared file are not atomic on Windows (a line was lost in CI)
    marks = tmp_path / "marks"
    marks.mkdir()
    body = textwrap.dedent(
        f"""
        import pathlib, sys, time
        start = time.time_ns()
        end = time.process_time() + 0.05
        while time.process_time() < end:
            pass
        name = sys.argv[1].replace("/", "_")
        pathlib.Path({str(marks)!r}, name).write_text(f"{{start}} {{time.time_ns()}}")
        """
    )
    path = tmp_path / "job.py"
    path.write_text(body, encoding="utf-8")

    def real(cid):
        def make(f):
            return sb.RunSpec(
                argv=[sys.executable, "-I", str(path), cid],
                workdir=tmp_path,
                env=dict(os.environ),
                log_path=tmp_path / "logs" / f"{cid.replace('/', '_')}.log",
                threshold_usec=f,
                active_time_limit_s=60.0,
                no_progress_s=30.0,
                poll_s=0.05,
            )

        return orc.Container(cid, make)

    def claim_of(key):
        return orc.ClaimPlan(
            key,
            [orc.Step("run", [real(f"{key}/run")])],
            [orc.Step("seeds", [real(f"{key}/s1"), real(f"{key}/s2")])],
            lambda records: True,
        )

    plan = orc.PaperPlan(
        [orc.Step("build", [real("setup/build")])], [claim_of("C1"), claim_of("C2")]
    )
    acc = bg.Accountant(["C1", "C2"], margin_usec=bg.cpu_hours(1) // 3600)  # M = 1 CPU-s
    run = orc.PaperRunner(plan, sb.SubprocessBackend(), acc).run()
    assert all(s.outcome is orc.Outcome.COMPLETED for s in run.steps), outcomes(run)
    times = {}
    for path_ in marks.iterdir():
        start, end = (int(v) for v in path_.read_text().split())
        times[path_.name.replace("_", "/")] = (start, end)
    assert sorted(times) == sorted(
        ["setup/build", "C1/run", "C2/run", "C1/s1", "C1/s2", "C2/s1", "C2/s2"]
    )
    # setup, then the base of C1, then of C2, then every attack (D-S4)
    assert times["setup/build"][1] <= times["C1/run"][0]
    assert times["C1/run"][1] <= times["C2/run"][0]
    attacks_c1 = [times["C1/s1"], times["C1/s2"]]
    attacks_c2 = [times["C2/s1"], times["C2/s2"]]
    assert times["C2/run"][1] <= min(s for s, _ in attacks_c1)
    assert max(e for _, e in attacks_c1) <= min(s for s, _ in attacks_c2)
    assert all(
        type(c.result.usage_usec) is int and c.result.usage_usec > 0
        for s in run.steps
        for c in s.containers
    )
    assert acc.total_charged() == sum(c.result.usage_usec for s in run.steps for c in s.containers)
    assert run.accounting_valid and run.completeness == orc.COMPLETENESS_NOT_APPLICABLE
