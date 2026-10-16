"""The measured detection delay D and stop latency S (wp3-acceptance.md 1.4a), recorded for
every stopped run, and the alert when one exceeds its V22 maximum (item F of the
maintainer's review of 2026-10-16): recorded only, with no automatic adjustment of M, T or
any limit. Offline: a fake tracker and a fake backend."""

import time
from pathlib import Path

import pytest

from refute.core import budget as bg
from refute.packs.ml import orchestrate as orc
from refute.packs.ml import sandbox as sb


class FakeTracker(sb._Tracker):
    """A run whose usage grows by ``step`` per reading and whose stop takes ``stop_s``."""

    def __init__(self, step, stop_s=0.0, exit_after=None):
        self.usage, self.step, self.stop_s = 0, step, stop_s
        self.readings, self.exit_after = 0, exit_after

    def poll(self):
        self.readings += 1
        if self.exit_after is not None and self.readings > self.exit_after:
            return 0
        return None

    def usage_usec(self):
        self.usage += self.step
        return self.usage

    def final_usage_usec(self):
        return self.usage

    def stop(self):
        # waits by the clock the supervisor reads (time.monotonic), not by one sleep: on
        # Windows a sleep of 0.2 s was measured as 0.188 s by that coarser clock (CI run
        # 38853937526), so the test bound S >= stop_s did not hold
        end = time.monotonic() + self.stop_s
        while time.monotonic() < end:
            time.sleep(0.005)

    def close(self):
        pass


def spec(tmp_path, **kw):
    values = dict(
        argv=["x"],
        workdir=tmp_path,
        env={},
        log_path=tmp_path / "run.log",
        threshold_usec=1000,
        active_time_limit_s=60.0,
        no_progress_s=30.0,
        poll_s=0.01,
    )
    values.update(kw)
    return sb.RunSpec(**values)


def test_a_stopped_run_records_d_and_s(tmp_path):
    result = sb._supervise(spec(tmp_path), FakeTracker(step=400, stop_s=0.2))
    assert result.stopped == sb.STOP_THRESHOLD
    assert result.detection_delay_s is not None and 0 <= result.detection_delay_s < 5
    assert result.stop_latency_s is not None and result.stop_latency_s >= 0.2


def test_a_run_that_ends_by_itself_records_neither(tmp_path):
    result = sb._supervise(spec(tmp_path, threshold_usec=None), FakeTracker(1, exit_after=3))
    assert result.exit_code == 0 and result.stopped is None
    assert result.detection_delay_s is None and result.stop_latency_s is None


def test_a_guard_stop_records_d_and_s_too(tmp_path):
    result = sb._supervise(
        spec(tmp_path, threshold_usec=None, active_time_limit_s=0.05), FakeTracker(1)
    )
    assert result.stopped == sb.STOP_ACTIVE_TIME
    assert result.detection_delay_s is not None and result.stop_latency_s is not None


class FakeClock:
    """A monotonic clock that moves only when told: a reading of the usage takes
    ``read_s``, a sleep lasts ``late_s`` longer than asked, and the stop takes ``stop_s``
    (the wait until every process of the run has ended)."""

    def __init__(self, read_s, late_s):
        self.now, self.read_s, self.late_s = 0.0, read_s, late_s

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds + self.late_s


class ClockedTracker(FakeTracker):
    def __init__(self, clock, step, stop_s):
        super().__init__(step)
        self.clock, self.stop_s = clock, stop_s

    def usage_usec(self):
        self.clock.now += self.clock.read_s
        return super().usage_usec()

    def stop(self):
        self.clock.now += self.stop_s


def test_d_and_s_are_exact_on_a_simulated_clock(tmp_path, monkeypatch):
    """D runs from the planned instant of the reading that reached F (poll_s after the
    previous reading ended) to the stop request: a late wake-up and a slow reading count
    in it. S runs from the request to the end of the stop. Values chosen to be exact in
    binary floating point."""
    clock = FakeClock(read_s=0.25, late_s=0.125)
    monkeypatch.setattr(sb, "time", clock)
    tracker = ClockedTracker(clock, step=400, stop_s=0.75)  # F = 1000: the 3rd reading
    result = sb._supervise(spec(tmp_path, poll_s=1.0), tracker)
    assert result.stopped == sb.STOP_THRESHOLD and tracker.readings == 3
    assert result.detection_delay_s == 0.375  # 0.125 late + 0.25 of reading
    assert result.stop_latency_s == 0.75


def test_the_cadence_of_the_readings_is_unchanged(tmp_path, monkeypatch):
    """Codex review of #108: the loop still sleeps poll_s after each reading (no catching
    up on a late schedule), so the readings and the stop are those of before."""
    clock = FakeClock(read_s=0.5, late_s=0.0)
    monkeypatch.setattr(sb, "time", clock)
    slept = []
    original = clock.sleep

    def sleep(seconds):
        slept.append(seconds)
        original(seconds)

    clock.sleep = sleep
    tracker = ClockedTracker(clock, step=400, stop_s=0.0)
    sb._supervise(spec(tmp_path, poll_s=1.0), tracker)
    assert slept == [1.0, 1.0]  # every sleep is poll_s, after the reading


def test_a_no_progress_stop_records_d_and_s(tmp_path, monkeypatch):
    clock = FakeClock(read_s=0.0, late_s=0.0)
    monkeypatch.setattr(sb, "time", clock)
    tracker = ClockedTracker(clock, step=0, stop_s=0.5)  # no usage growth
    tracker.usage = 1  # one reading of progress, then none
    result = sb._supervise(
        spec(tmp_path, threshold_usec=None, poll_s=1.0, no_progress_s=2.0), tracker
    )
    assert result.stopped == sb.STOP_NO_PROGRESS
    assert result.detection_delay_s == 0.0 and result.stop_latency_s == 0.5


def run_result(d=None, s=None):
    return sb.RunResult(None, 10, sb.STOP_THRESHOLD, 1.0, Path("x.log"), d, s)


MAXIMA = sb.TimingMaxima(detection_delay_s=0.5, stop_latency_s=2.0)


def test_an_alert_only_above_the_v22_maximum():
    assert sb.timing_alerts(run_result(0.5, 2.0), MAXIMA) == []  # at the maximum: no alert
    assert sb.timing_alerts(run_result(None, None), MAXIMA) == []
    assert sb.timing_alerts(run_result(None, 2.5), MAXIMA) == [
        "stop latency S 2.500 s above the V22 maximum 2.000 s"
    ]
    assert sb.timing_alerts(run_result(0.75, None), MAXIMA) == [
        "detection delay D 0.750 s above the V22 maximum 0.500 s"
    ]
    alerts = sb.timing_alerts(run_result(0.75, 2.5), MAXIMA)
    assert alerts == [
        "detection delay D 0.750 s above the V22 maximum 0.500 s",
        "stop latency S 2.500 s above the V22 maximum 2.000 s",
    ]


@pytest.mark.parametrize("bad", [0, -1, float("inf"), float("nan"), "1"])
def test_the_maxima_are_positive_and_finite(bad):
    with pytest.raises(ValueError, match="positive and finite"):
        sb.TimingMaxima(detection_delay_s=bad, stop_latency_s=1.0)


# ---- through the orchestrator: an alert is recorded and changes nothing else -------------------


class Fake:
    name = "fake"

    def __init__(self, timings):
        self.timings = timings

    def run(self, spec):
        cid = spec.env["CID"]
        d, s, stopped = self.timings.get(cid, (None, None, None))
        exit_code = None if stopped else 0
        return sb.RunResult(exit_code, 1000, stopped, 0.0, spec.log_path, d, s)


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


def plan(tmp_path):
    claim = orc.ClaimPlan(
        "C1",
        [orc.Step("run", [container(tmp_path, "C1/run")])],
        [orc.Step("seeds", [container(tmp_path, "C1/s1"), container(tmp_path, "C1/s2")])],
        lambda records: True,
    )
    return orc.PaperPlan([orc.Step("build", [container(tmp_path, "setup/build")])], [claim])


def run(tmp_path, maxima):
    acc = bg.Accountant(["C1"], margin_usec=100, base_pool_usec=10_000, attack_pool_base_usec=6_000)
    timings = {
        "C1/s1": (0.9, 1.0, sb.STOP_THRESHOLD),
        "C1/s2": (0.1, 3.0, sb.STOP_NO_PROGRESS),  # a guard stop is timed and alerted too
    }
    out = orc.PaperRunner(plan(tmp_path), Fake(timings), acc, timing_maxima=maxima).run()
    return out, acc


def test_the_orchestrator_records_alerts_and_changes_nothing_else(tmp_path):
    with_alerts, acc_a = run(tmp_path, MAXIMA)
    without, acc_b = run(tmp_path, None)
    assert with_alerts.timing_alerts == [
        "C1/s1: detection delay D 0.900 s above the V22 maximum 0.500 s",
        "C1/s2: stop latency S 3.000 s above the V22 maximum 2.000 s",
    ]
    assert without.timing_alerts == []
    # the same outcomes, thresholds, charges, margin and accounting: no adjustment
    assert [(s.step, s.outcome) for s in with_alerts.steps] == [
        (s.step, s.outcome) for s in without.steps
    ]
    thresholds = [[c.threshold_usec for c in s.containers] for s in with_alerts.steps]
    assert thresholds == [[c.threshold_usec for c in s.containers] for s in without.steps]
    assert acc_a.margin_usec == acc_b.margin_usec == 100
    assert acc_a.total_charged() == acc_b.total_charged()
    assert with_alerts.accounting_valid == without.accounting_valid
    assert with_alerts.invalid_reasons == without.invalid_reasons
    # the measured values are kept in the records
    stopped = [c.result for s in with_alerts.steps for c in s.containers if c.result.stopped]
    assert sorted((r.detection_delay_s, r.stop_latency_s) for r in stopped) == [
        (0.1, 3.0),
        (0.9, 1.0),
    ]


def test_the_orchestrator_refuses_maxima_of_another_type(tmp_path):
    acc = bg.Accountant(["C1"], margin_usec=100, base_pool_usec=10_000, attack_pool_base_usec=6_000)
    with pytest.raises(ValueError, match="TimingMaxima"):
        orc.PaperRunner(plan(tmp_path), Fake({}), acc, timing_maxima=(0.5, 2.0))
