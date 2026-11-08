"""The A0 acceptance runner hands the per-event measurements the pipeline's own series (#208,
the maintainer's decision of 2026-11-08, item 2a).

The first A0 acceptance run passed the raw synthetic curve to functions that, in the version-3
pipeline, receive the flattened curve of ``pipeline.attack_candidate``. This module runs one unit
of every kind of the corrected runner (``docs/validation/v0.5.1/acceptance/a0.py``) on
development seeds, records every series that ``rednoise.event_noise``,
``events.per_event_depths``, ``a0.empirical_events`` and ``battery_v51.check_odd_even`` receive,
and checks, byte for byte, that each equals the series the pipeline's ``attack_candidate`` gives
the same functions for the same raw curve and candidate. It also checks that the first run's
behaviour (the raw curve handed to all four) fails that check. Synthetic data only; no network.

Scope (Codex's review of the second run, round 1, objection 2): this proves the construction of
the series for a fixed candidate. The runner measures with the declared ephemeris (the A0 runner's
design, revision 3), whereas the pipeline measures with ``finalize_candidate``'s refinement of the
search candidate; candidate equivalence is not claimed here.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "docs" / "validation" / "v0.5.1" / "acceptance" / "a0.py"
FIELDS = ("time", "flux", "flux_err", "sector", "year")
SEED = 20261108  # a development seed; never an acceptance seed
SPIED = ("event_noise", "per_event_depths", "empirical_events", "check_odd_even")


def _runner():
    name = "v051_accept_a0_runner"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, RUNNER)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


def _bytes(lc) -> tuple[bytes, ...]:
    return tuple(np.ascontiguousarray(getattr(lc, f)).tobytes() for f in FIELDS)


class _StopPipelineError(Exception):
    """Ends the pipeline's run once the spied functions have their series."""


class _Spies:
    """Records the light curve each spied function receives, in ``self.calls`` (the target
    list is switched between the runner's unit and the pipeline)."""

    def __init__(self, monkeypatch):
        from refute.packs.tess import a0, events, pipeline, rednoise
        from refute.packs.tess import battery_v51 as v51

        self.calls: list = []
        self.flats: dict[int, tuple] = {}
        self.stop_after_odd_even = False
        real_ee, real_oe, real_pe = a0.empirical_events, v51.check_odd_even, events.per_event_depths
        real_en = rednoise.event_noise

        def en(flat, *args, **kwargs):
            self.calls.append(("event_noise", flat))
            return real_en(flat, *args, **kwargs)

        def ee(flat, *args, **kwargs):
            self.calls.append(("empirical_events", flat))
            return real_ee(flat, *args, **kwargs)

        def oe(flat, *args, **kwargs):
            self.calls.append(("check_odd_even", flat))
            result = real_oe(flat, *args, **kwargs)
            if self.stop_after_odd_even:
                # the pipeline has handed all three functions their series (v05_tests calls
                # per_event_depths and A0 before odd_even); the rest of the battery is not needed
                raise _StopPipelineError
            return result

        def pe(flat, *args, **kwargs):
            self.calls.append(("per_event_depths", flat))
            return real_pe(flat, *args, **kwargs)

        monkeypatch.setattr(a0, "empirical_events", ee)
        monkeypatch.setattr(v51, "check_odd_even", oe)
        monkeypatch.setattr(events, "per_event_depths", pe)
        monkeypatch.setattr(pipeline, "per_event_depths", pe)
        monkeypatch.setattr(rednoise, "event_noise", en)
        monkeypatch.setattr(pipeline, "event_noise", en)

        runner = _runner()
        real_flat = runner._flat

        def flat(raw, cand, plan):
            out = real_flat(raw, cand, plan)
            self.flats[id(out)] = (raw, cand, plan, out)
            return out

        monkeypatch.setattr(runner, "_flat", flat)


def _pipeline_series(raw, cand, plan, spies: _Spies) -> set[tuple[bytes, ...]]:
    """The series ``attack_candidate`` hands the spied functions for ``raw`` and ``cand`` (one
    series: the flattened curve of the gauntlet)."""
    from refute.packs.tess import pipeline
    from refute.packs.tess import synthetic as syn

    spies.calls = []
    spies.stop_after_odd_even = True
    try:
        with pytest.raises(_StopPipelineError):
            pipeline.attack_candidate(syn.make_data(raw, [], syn.make_star()), cand, plan)
    finally:
        spies.stop_after_odd_even = False
    names = {name for name, _ in spies.calls}
    assert set(SPIED) <= names
    series = {_bytes(lc) for _, lc in spies.calls}
    assert len(series) == 1
    return series


def _units():
    """One unit of every kind the runner has (development seeds)."""
    r = _runner()
    return {
        "a01-trend-partial": (r.unit_a01, ("trend", "partial", 0, SEED)),
        "a01-long-full": (r.unit_a01, ("long", "full", 0, SEED + 1)),
        "a04-correlated_trend-minimal": (
            r.unit_group,
            ("a04", "correlated_trend", "minimal", 3, 0, SEED + 2),
        ),
        "a07-hetero": (r.unit_group, ("a07", "hetero", "mixed", 2, 0, SEED + 3)),
        "a05-p1": (r.unit_a05, ("p1", 3.0, "trend_one", "long", "partial", 2, 0, SEED + 4)),
        "a06-trend": (r.unit_a06, ("trend", "full", 1.0, 0, SEED + 5)),
        "a08-event": (r.unit_a08, ("event", "trend", "full", 2, 4.0, 0, SEED + 6)),
    }


def test_first_run_behaviour_is_caught(monkeypatch):
    """The first run's runner (``_flat`` absent: the raw curve handed on) fails the check."""
    runner = _runner()
    spies = _Spies(monkeypatch)
    seen: list = []

    def raw_as_is(raw, cand, plan):
        seen.append((raw, cand, plan))
        return raw

    monkeypatch.setattr(runner, "_flat", raw_as_is)
    spies.calls = []
    runner.unit_group(("a04", "correlated_trend", "partial", 2, 0, SEED))
    received = list(spies.calls)
    assert len(seen) == 1
    raw, cand, plan = seen[0]
    # each of the four functions received the raw curve, and that is not the pipeline's series
    assert {name for name, _ in received} == set(SPIED)
    assert all(lc is raw for _, lc in received)
    assert _bytes(raw) not in _pipeline_series(raw, cand, plan, spies)


@pytest.mark.parametrize("name", list(_units()))
def test_runner_hands_a0_the_pipeline_series(name, monkeypatch):
    fn, arg = _units()[name]
    spies = _Spies(monkeypatch)
    spies.calls = []
    fn(arg)
    runner_calls = list(spies.calls)
    assert any(n == "empirical_events" for n, _ in runner_calls)
    pipeline_cache: dict[int, set] = {}
    for fname, lc in runner_calls:
        # every series a spied function receives in the unit is an output of ``_flat``
        assert id(lc) in spies.flats, f"{fname} received a series that is not the runner's _flat"
        raw, cand, plan, out = spies.flats[id(lc)]
        if id(lc) not in pipeline_cache:
            pipeline_cache[id(lc)] = _pipeline_series(raw, cand, plan, spies)
            # the first run's defect: it handed these functions the raw curve itself
            assert _bytes(raw) not in pipeline_cache[id(lc)]
        assert pipeline_cache[id(lc)] == {_bytes(lc)}, f"{fname}: not the pipeline's series"
