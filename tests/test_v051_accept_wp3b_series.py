"""The WP3 (b) acceptance runner hands each test the pipeline's own series (#208, the
maintainer's decision of 2026-11-08, item 3: every runner after A0 needs A0's byte-identity
proof before its run).

``pipeline.v05_tests`` hands ``battery_v51.check_sinusoid`` the raw curve ``data.lc`` with the
plan's ``stronger`` and ``v051`` sections, and hands ``rednoise.event_noise`` and
``events.per_event_depths`` (the measurements of ``secondary_eclipse``, which row 3.3 runs) the
flattened curve of ``attack_candidate``. This module runs one unit of every construction of the
runner (``docs/validation/v0.5.1/acceptance/wp3b.py``) on development seeds, records what those
functions receive, and checks, byte for byte, that each equals what ``attack_candidate`` hands
the same function for the same raw curve and candidate; the parameters handed to
``check_sinusoid`` must equal the pipeline's. Negative controls show the check catches a runner
that hands ``check_sinusoid`` the flattened curve, or the event measurements the raw curve (the
first A0 run's defect). Synthetic data only; no network.

Scope (as A0's proof): the series and the parameters for a fixed candidate; the pipeline's refined
candidate (``finalize_candidate``), and so the seed derived from it, are not claimed equal.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "docs" / "validation" / "v0.5.1" / "acceptance" / "wp3b.py"
FIELDS = ("time", "flux", "flux_err", "sector", "year")
SEED = 20261108  # a development seed; never an acceptance seed


def _runner():
    name = "v051_accept_wp3b_runner"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, RUNNER)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


def _bytes(lc) -> tuple[bytes, ...]:
    return tuple(np.ascontiguousarray(getattr(lc, f)).tobytes() for f in FIELDS)


class _StopPipelineError(Exception):
    """Ends the pipeline's run once ``check_sinusoid`` has its arguments."""


class _Spies:
    def __init__(self, monkeypatch):
        from refute.packs.tess import battery_v51 as v51
        from refute.packs.tess import events, pipeline, rednoise

        self.calls: list = []
        self.flats: dict[int, tuple] = {}
        self.stop = False
        real_sin, real_pe, real_en = (
            v51.check_sinusoid,
            events.per_event_depths,
            rednoise.event_noise,
        )

        def sin(raw, cand, sp, cp, seed):
            self.calls.append(("check_sinusoid", raw, sp, cp))
            if self.stop:
                raise _StopPipelineError
            return real_sin(raw, cand, sp, cp, seed)

        def pe(flat, *args, **kwargs):
            self.calls.append(("per_event_depths", flat, None, None))
            return real_pe(flat, *args, **kwargs)

        def en(flat, *args, **kwargs):
            self.calls.append(("event_noise", flat, None, None))
            return real_en(flat, *args, **kwargs)

        monkeypatch.setattr(v51, "check_sinusoid", sin)
        monkeypatch.setattr(events, "per_event_depths", pe)
        monkeypatch.setattr(pipeline, "per_event_depths", pe)
        monkeypatch.setattr(rednoise, "event_noise", en)
        monkeypatch.setattr(pipeline, "event_noise", en)

        series = sys.modules["series"]
        real_flat = series.pipeline_flat

        def flat(raw, cand, plan):
            out = real_flat(raw, cand, plan)
            self.flats[id(out)] = (raw, cand, plan, out)
            return out

        monkeypatch.setattr(series, "pipeline_flat", flat)


def _pipeline(raw, cand, plan, spies: _Spies):
    """What ``attack_candidate`` hands the spied functions for ``raw`` and ``cand``: the
    sinusoid's (series, sp, cp) and the set of series of the event measurements."""
    from refute.packs.tess import pipeline
    from refute.packs.tess import synthetic as syn

    spies.calls = []
    spies.stop = True
    try:
        with pytest.raises(_StopPipelineError):
            pipeline.attack_candidate(syn.make_data(raw, [], syn.make_star()), cand, plan)
    finally:
        spies.stop = False
    sin = [c for c in spies.calls if c[0] == "check_sinusoid"]
    assert len(sin) == 1
    events = {_bytes(lc) for name, lc, _, _ in spies.calls if name != "check_sinusoid"}
    assert {name for name, *_ in spies.calls} >= {"event_noise", "per_event_depths"}
    assert len(events) == 1
    return sin[0], events


def _units():
    """One unit of every construction of the runner (development seeds)."""
    return {
        "3.1-sin": ("3.1", "sin", "red"),
        "3.1-box": ("3.1", "box", "white"),
        "3.2": ("3.2", "20", "correlated_trend"),
        "3.3-unrelated": ("3.3", "unrelated", "trend"),
        "3.3-rotation": ("3.3", "rotation", "correlated"),
        "3.4": ("3.4", "v2", "trend"),
        "3.5": ("3.5", "15", "white"),
        "3.6": ("3.6", "sin14", "correlated_trend"),
        "3.7": ("3.7", "near", "trend"),
        "3.8a": ("3.8", "a-2P", "correlated"),
        "3.8b": ("3.8", "b-P/2", "white"),
        "3.8c": ("3.8", "c", "trend"),
    }


def _run_unit(runner, spies, key, k):
    row, case, noise = _units()[key]
    spies.calls = []
    record: dict = {}

    real_sinusoid = runner._sinusoid

    def capture(lc, cand):
        record.setdefault("pairs", []).append((lc, cand))
        return real_sinusoid(lc, cand)

    runner._sinusoid = capture
    try:
        runner.unit((row, case, noise, 0, SEED + k, None))
    finally:
        runner._sinusoid = real_sinusoid
    return list(spies.calls), record["pairs"]


@pytest.mark.parametrize("key", list(_units()))
def test_runner_hands_each_test_the_pipeline_series(key, monkeypatch):
    runner = _runner()
    spies = _Spies(monkeypatch)
    plan = runner._plan()
    k = list(_units()).index(key)
    calls, pairs = _run_unit(runner, spies, key, k)
    assert len(pairs) == 1
    raw, cand = pairs[0]
    runner_sin = [c for c in calls if c[0] == "check_sinusoid"]
    assert len(runner_sin) == 1
    (sin_args, events) = _pipeline(raw, cand, plan, spies)
    # check_sinusoid: the raw curve as the pipeline holds it in data.lc, and the plan's sections
    assert _bytes(runner_sin[0][1]) == _bytes(sin_args[1])
    assert runner_sin[0][2].model_dump() == sin_args[2].model_dump()
    assert runner_sin[0][3].model_dump() == sin_args[3].model_dump()
    # negative control: the flattened curve handed to check_sinusoid would be caught
    assert _bytes(runner.series.pipeline_flat(raw, cand, plan)) != _bytes(sin_args[1])
    # the event measurements (row 3.3's secondary_eclipse): the pipeline's flattened series
    runner_events = [c for c in calls if c[0] != "check_sinusoid"]
    if _units()[key][0] == "3.3":
        assert {name for name, *_ in runner_events} == {"event_noise", "per_event_depths"}
        for name, lc, _, _ in runner_events:
            assert id(lc) in spies.flats, f"{name} received a series not from pipeline_flat"
            assert {_bytes(lc)} == events, f"{name}: not the pipeline's series"
        # negative control: the raw curve (the first A0 run's defect) would be caught
        assert _bytes(raw) not in events
    else:
        assert not runner_events
