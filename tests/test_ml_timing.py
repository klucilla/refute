"""The measured detection delay D and stop latency S (wp3-acceptance.md 1.4a), recorded for
every stopped run, and the alert when one exceeds its V22 maximum (item F of the
maintainer's review of 2026-10-16): recorded only, with no automatic adjustment of M, T or
any limit. Offline: a fake tracker and a fake backend.

D and S are measured on ``time.perf_counter_ns`` (every instant they use, the first planned
instant included), the loop and its guards run on ``time.monotonic``. Exact values are
checked only on a simulated clock; a test on the real clocks checks the integration and
never asserts a time bound or a sign of D (the maintainer's decision of 2026-10-16, after
the failure of main run 38902889911: on Windows with Python 3.12, ``time.monotonic`` has a
resolution of 15.625 ms)."""

import math
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from refute.core import budget as bg
from refute.packs.ml import orchestrate as orc
from refute.packs.ml import sandbox as sb

NS = 1_000_000_000


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
        # waits by the clock the supervisor measures S with (time.perf_counter_ns), so the
        # measured S is at least stop_s by construction, not by a timing assumption
        end = time.perf_counter_ns() + round(self.stop_s * NS)
        while time.perf_counter_ns() < end:
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


# ---- real clocks: integration only, no time bound and no sign of D -------------------------


def test_a_stopped_run_records_d_and_s(tmp_path):
    """The stop reason, D and S present and finite, S at least the time the stop took on the
    measurement clock (the tracker waits on that clock), and the clock recorded."""
    result = sb._supervise(spec(tmp_path), FakeTracker(step=400, stop_s=0.2))
    assert result.stopped == sb.STOP_THRESHOLD
    for value in (result.detection_delay_s, result.stop_latency_s):
        assert type(value) is float and math.isfinite(value)
    assert result.stop_latency_s >= 0.2
    info = time.get_clock_info("perf_counter")
    assert result.measurement_clock == info.implementation
    assert result.measurement_resolution_s == info.resolution


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


# ---- a simulated clock: exact values ---------------------------------------------------------


class SimClock:
    """Simulated time for ``sandbox.time``, in integer nanoseconds.

    The real instant ``t`` (ns) starts at ``t0``. ``monotonic()``, the clock of the loop and
    its guards, returns ``(loop_origin + t) / 1e9``. ``perf_counter_ns()``, the measurement
    clock of D and S, returns ``measure_origin + Q(t)``, where Q is the identity (a fine
    clock) or, with a step ``q``, ``floor(t / q) * q``: the value of the last tick at or
    before ``t``, rounding down as a tick counter does. ``sleep(s)`` advances ``t`` by
    ``round(s * 1e9) + late_ns`` (a negative ``late_ns`` is an early wake-up); a reading of
    the usage advances it by ``read_ns`` and the stop by ``stop_ns`` (ClockedTracker).
    Every value is an exact integer of nanoseconds, so D and S are exact."""

    def __init__(self, t0=0, read_ns=0, late_ns=0, step_ns=None, loop_origin=0, measure_origin=0):
        self.t, self.read_ns, self.late_ns, self.step_ns = t0, read_ns, late_ns, step_ns
        self.loop_origin, self.measure_origin = loop_origin, measure_origin
        self.slept = []

    def monotonic(self):
        return (self.loop_origin + self.t) / NS

    def perf_counter_ns(self):
        q = self.t if self.step_ns is None else (self.t // self.step_ns) * self.step_ns
        return self.measure_origin + q

    def sleep(self, seconds):
        self.slept.append(seconds)
        self.t += round(seconds * NS) + self.late_ns

    def get_clock_info(self, name):
        assert name == "perf_counter"
        return SimpleNamespace(implementation="simulated", resolution=(self.step_ns or 1) / NS)


class ClockedTracker(FakeTracker):
    def __init__(self, clock, step, stop_ns=0):
        super().__init__(step)
        self.clock, self.stop_ns = clock, stop_ns

    def usage_usec(self):
        self.clock.t += self.clock.read_ns
        return super().usage_usec()

    def stop(self):
        self.clock.t += self.stop_ns


def simulate(tmp_path, monkeypatch, clock, step=400, stop_ns=0, **kw):
    """F = 1000 µs and a usage of 400 µs per reading: the 3rd reading reaches F (1200)."""
    monkeypatch.setattr(sb, "time", clock)
    tracker = ClockedTracker(clock, step=step, stop_ns=stop_ns)
    return sb._supervise(spec(tmp_path, **kw), tracker), tracker


def test_an_early_wake_up_gives_a_negative_d_recorded_as_measured(tmp_path, monkeypatch):
    """poll 1 s; every sleep ends 0.25 s early; fine clock. Readings (real t = clock value):
    start t=0, planned 0 | 1st t=0, usage 400, planned 1.0, sleep to t=0.75 | 2nd t=0.75,
    usage 800, planned 1.75, sleep to t=1.5 | 3rd t=1.5, usage 1200 >= F, request at 1.5:
    D = 1.5 - 1.75 = -0.25, kept negative; S = 0."""
    clock = SimClock(late_ns=-250_000_000)
    result, _ = simulate(tmp_path, monkeypatch, clock, poll_s=1.0)
    assert result.stopped == sb.STOP_THRESHOLD
    assert result.detection_delay_s == -0.25 and result.stop_latency_s == 0.0


def test_a_late_wake_up_counts_in_d(tmp_path, monkeypatch):
    """poll 1 s; every sleep ends 0.125 s late; fine clock. Readings: start planned 0 |
    1st t=0, planned 1.0, sleep to 1.125 | 2nd t=1.125, planned 2.125, sleep to 2.25 |
    3rd t=2.25, request at 2.25: D = 0.125."""
    clock = SimClock(late_ns=125_000_000)
    result, _ = simulate(tmp_path, monkeypatch, clock, poll_s=1.0)
    assert result.detection_delay_s == 0.125 and result.stop_latency_s == 0.0


def test_a_slow_reading_counts_in_d(tmp_path, monkeypatch):
    """poll 1 s; a reading of the usage takes 0.25 s; fine clock. Readings: start planned 0 |
    1st usage read to t=0.25, planned 1.25, sleep to 1.25 | 2nd usage read to t=1.5,
    planned 2.5, sleep to 2.5 | 3rd usage read to t=2.75, request at 2.75: D = 0.25 (the
    reading that reached F counts in D)."""
    clock = SimClock(read_ns=250_000_000)
    result, _ = simulate(tmp_path, monkeypatch, clock, poll_s=1.0)
    assert result.detection_delay_s == 0.25 and result.stop_latency_s == 0.0


def test_a_slow_stop_counts_in_s_only(tmp_path, monkeypatch):
    """poll 1 s; the stop takes 0.75 s; fine clock. Readings: start planned 0 | 1st t=0,
    planned 1.0, sleep to 1.0 | 2nd t=1.0, planned 2.0, sleep to 2.0 | 3rd t=2.0, request at
    2.0: D = 0; the stop ends at 2.75: S = 0.75."""
    clock = SimClock()
    result, _ = simulate(tmp_path, monkeypatch, clock, stop_ns=750_000_000, poll_s=1.0)
    assert result.detection_delay_s == 0.0 and result.stop_latency_s == 0.75


def test_d_and_s_are_exact_on_a_simulated_clock(tmp_path, monkeypatch):
    """D runs from the planned instant of the reading that reached F (poll_s after the
    previous reading ended) to the stop request: a late wake-up and a slow reading count in
    it. S runs from the request to the end of the stop. poll 1 s, reading 0.25 s, sleeps
    0.125 s late, stop 0.75 s; fine clock. Readings: start planned 0 | 1st usage read to
    t=0.25, planned 1.25, sleep to 1.375 | 2nd usage read to t=1.625, planned 2.625, sleep
    to 2.75 | 3rd usage read to t=3.0, request at 3.0: D = 0.375; stop ends at 3.75: S =
    0.75."""
    clock = SimClock(read_ns=250_000_000, late_ns=125_000_000)
    result, tracker = simulate(tmp_path, monkeypatch, clock, stop_ns=750_000_000, poll_s=1.0)
    assert result.stopped == sb.STOP_THRESHOLD and tracker.readings == 3
    assert result.detection_delay_s == 0.375
    assert result.stop_latency_s == 0.75


Q = 15_625_000  # 1/64 s, the step of a coarse clock (GetTickCount64 on Windows, Python 3.12)
POLL = 1 / 128  # 7 812 500 ns, shorter than one step


def test_a_quantized_clock_can_give_d_of_minus_one_poll(tmp_path, monkeypatch):
    """The failure of main run 38902889911, reproduced exactly. Step q = 1/64 s, poll 1/128
    s, t0 = 5/512 s (9 765 625 ns); the clock value is floor(t/q)*q. Readings (ns):
    start t=9 765 625, clock 0, planned 0 | 1st t=9 765 625, clock 0, planned 7 812 500,
    sleep to t=17 578 125 | 2nd t=17 578 125, clock 15 625 000, planned 23 437 500, sleep
    to t=25 390 625 | 3rd t=25 390 625, clock 15 625 000 (same tick), request at
    15 625 000: D = -7 812 500 ns = -1/128 s, while the real delay is 0. Recorded as
    measured, with the clock's resolution."""
    clock = SimClock(t0=9_765_625, step_ns=Q)
    result, tracker = simulate(tmp_path, monkeypatch, clock, poll_s=POLL)
    assert tracker.readings == 3 and clock.slept == [POLL, POLL]
    assert result.detection_delay_s == -1 / 128
    assert result.measurement_clock == "simulated" and result.measurement_resolution_s == 1 / 64


def test_a_quantized_clock_in_the_opposite_phase_gives_plus_one_poll(tmp_path, monkeypatch):
    """Same clock, t0 = 0. Readings (ns): start t=0, clock 0, planned 0 | 1st t=0, clock 0,
    planned 7 812 500, sleep to t=7 812 500 | 2nd t=7 812 500, clock 0, planned 7 812 500,
    sleep to t=15 625 000 | 3rd t=15 625 000, clock 15 625 000, request at 15 625 000:
    D = +7 812 500 ns = +1/128 s, while the real delay is 0."""
    clock = SimClock(t0=0, step_ns=Q)
    result, tracker = simulate(tmp_path, monkeypatch, clock, poll_s=POLL)
    assert tracker.readings == 3 and clock.slept == [POLL, POLL]
    assert result.detection_delay_s == 1 / 128


def test_the_same_path_on_a_fine_clock_gives_d_zero(tmp_path, monkeypatch):
    """t0 = 5/512 s, fine clock. Readings (ns): start planned 9 765 625 | 1st t=9 765 625,
    planned 17 578 125, sleep to 17 578 125 | 2nd t=17 578 125, planned 25 390 625, sleep to
    25 390 625 | 3rd t=25 390 625, request at 25 390 625: D = 0."""
    clock = SimClock(t0=9_765_625)
    result, _ = simulate(tmp_path, monkeypatch, clock, poll_s=POLL)
    assert result.detection_delay_s == 0.0


def test_d_uses_one_clock_whatever_the_origins(tmp_path, monkeypatch):
    """The loop clock starts at 0 s and the measurement clock at 1000 s; fine clocks, no
    delay. Readings (measurement clock, s): start planned 1000 | 1st t=0, planned 1001, sleep
    to t=1 | 2nd t=1, planned 1002, sleep to t=2 | 3rd t=2, request at 1002: D = 0. A D
    mixing the two clocks would be about -1000 or +1000."""
    clock = SimClock(loop_origin=0, measure_origin=1000 * NS)
    result, _ = simulate(tmp_path, monkeypatch, clock, poll_s=1.0)
    assert result.detection_delay_s == 0.0 and result.stop_latency_s == 0.0
    assert result.elapsed_s == 2.0  # the loop's own clock


def test_f_reached_at_the_first_reading_uses_the_measured_start(tmp_path, monkeypatch):
    """The first planned instant is the start of the supervision on the measurement clock
    (before, it was the start on the loop clock). Origins 0 (loop) and 1000 s
    (measurement); a usage of 1000 µs per reading, so the 1st reading reaches F; reading
    0.25 s, stop 0.75 s. Readings (measurement clock, s): start planned 1000 | 1st usage read
    to t=0.25, request at 1000.25: D = 0.25; the stop ends at 1001: S = 0.75. No sleep."""
    clock = SimClock(read_ns=250_000_000, loop_origin=0, measure_origin=1000 * NS)
    result, tracker = simulate(tmp_path, monkeypatch, clock, step=1000, stop_ns=750_000_000)
    assert tracker.readings == 1 and clock.slept == []
    assert result.detection_delay_s == 0.25 and result.stop_latency_s == 0.75


def test_the_cadence_of_the_readings_is_unchanged(tmp_path, monkeypatch):
    """Codex review of #108: the loop still sleeps poll_s after each reading (no catching
    up on a late schedule), so the readings and the stop are those of before."""
    clock = SimClock(read_ns=500_000_000)
    simulate(tmp_path, monkeypatch, clock, poll_s=1.0)
    assert clock.slept == [1.0, 1.0]  # every sleep is poll_s, after the reading


def test_a_no_progress_stop_records_d_and_s(tmp_path, monkeypatch):
    """No usage growth after the first reading; no_progress 2 s, poll 1 s, stop 0.5 s; fine
    clock. Readings: start planned 0 | 1st t=0, progress, planned 1, sleep to 1 | 2nd t=1,
    no progress (1 s), planned 2, sleep to 2 | 3rd t=2, no progress for 2 s: stop requested
    at 2: D = 0; S = 0.5."""
    clock = SimClock()
    monkeypatch.setattr(sb, "time", clock)
    tracker = ClockedTracker(clock, step=0, stop_ns=500_000_000)  # no usage growth
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


def test_a_negative_d_never_raises_an_alert():
    """A negative D is below any positive maximum: recorded, no alert."""
    assert sb.timing_alerts(run_result(-0.0078125, 0.0), MAXIMA) == []


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
