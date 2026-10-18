"""M4 piece 2: the propagation of A1 to the per-event depths, the stacked depth and the gate
(revision 3 of the corrections plan, section 2.2; docs/validation/v0.2.1/reopen/
m4-implementation-map.md, Amendment 2)."""

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest

from refute.core.runner import default_workers, run_processes
from refute.packs.tess import synthetic
from refute.packs.tess.events import per_event_depths
from refute.packs.tess.params import EventParams, TessTestPlan
from refute.packs.tess.pipeline import analyze_data
from refute.packs.tess.rednoise import EventNoise, NoiseEstimate, SectorNoise
from refute.packs.tess.types import LightCurveData

ROOT = Path(__file__).resolve().parents[1]
REF_DIR = ROOT / "docs" / "validation" / "v0.2.1" / "reopen" / "m4"
REFERENCE = json.loads((REF_DIR / "analysis-reference.json").read_text(encoding="utf-8"))
CADENCE = 120.0 / 86400.0
ON = {"enabled": True}


def _reference_module():
    spec = importlib.util.spec_from_file_location(
        "analysis_reference", REF_DIR / "analysis_reference.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _plan(corrections=None):
    plan = synthetic.fast_plan_dict()
    if corrections is not None:
        plan["gauntlet"] = {"corrections": corrections}
    return TessTestPlan.model_validate(plan)


def _test(analysis, name):
    return next(t for t in analysis.tests if t.name == name)


def analyze_with(task):
    """Top-level helper for the process pool: (scenario, seed, noise, corrections)."""
    name, seed, noise, corrections = task
    return analyze_data(synthetic.scenario_data(name, seed, noise), _plan(corrections))


# --- P1: the switch off is the M3 code path ------------------------------------------------

SAME_PLATFORM = sys.platform == REFERENCE["platform"] and np.__version__ == REFERENCE["numpy"]


@pytest.mark.skipif(not SAME_PLATFORM, reason="the analysis digests are bound to their platform")
@pytest.mark.parametrize("key", sorted(REFERENCE["digests"]))
def test_p1_with_the_switch_off_every_analysis_is_unchanged(key):
    name, seed, noise = key.split("|")
    assert _reference_module().record((name, int(seed), noise)) == REFERENCE["digests"][key]


def test_p1_an_explicit_switch_off_equals_the_default_plan():
    from refute.core.io import dumps_json, to_jsonable

    data = synthetic.scenario_data("planet", 0)
    a = analyze_data(data, _plan())
    b = analyze_data(data, _plan({"enabled": False}))
    assert dumps_json(to_jsonable([t.to_dict() for t in a.tests])) == dumps_json(
        to_jsonable([t.to_dict() for t in b.tests])
    )


# --- P2: in white noise the gate changes by at most 5% (median) ----------------------------


@pytest.fixture(scope="module")
def white_planets():
    tasks = [("planet", seed, "white", ON) for seed in range(10)]
    return run_processes(analyze_with, tasks, max(1, min(len(tasks), default_workers())))


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="m4-implementation-map.md, Amendment 3: the median is 0.812; the acceptance of piece 2 "
    "is not met (option (c)); the mark does not satisfy it",
)
def test_p2_white_noise_gate_unchanged_within_5_percent(white_planets):
    ratios = []
    for analysis in white_planets:
        snr = _test(analysis, "snr")
        ratios.append(snr.metrics["snr"] / snr.metrics["bls_depth_snr"])
    median = float(np.median(ratios))
    assert 0.95 <= median <= 1.05, (median, ratios)


def test_p2b_the_corrected_snr_is_the_bls_depth_over_the_stacked_error():
    """Added after the Codex review of the stage (map Amendment 5): P2 is an expected failure, so a
    positive check of the gate's identity is needed (a wrong factor would stay hidden)."""
    from refute.packs.tess.events import group_mean

    analysis = analyze_with(("planet", 0, "white", ON))
    snr = _test(analysis, "snr")
    primary = analysis.gauntlet.primary
    stacked = group_mean(primary.depths, primary.errors)
    candidate = analysis.gauntlet.candidate
    assert snr.metrics["stacked_error_ppm"] == pytest.approx(stacked.error * 1e6, rel=1e-12)
    assert candidate.depth_err == pytest.approx(stacked.error, rel=1e-12)
    assert snr.metrics["snr"] == pytest.approx(candidate.depth / stacked.error, rel=1e-12)
    assert snr.metrics["events"] == len(primary)


# --- P3, P4, P7: the per-event variance, shared cadences, excluded sectors ------------------


def _flat_lc(n_days=27.0, seed=0, sectors=(1, 2)):
    rng = np.random.default_rng(seed)
    times, secs = [], []
    for i, s in enumerate(sectors):
        t = 1325.0 + i * 30.0 + np.arange(0.0, n_days, CADENCE)
        times.append(t)
        secs.append(np.full(t.size, s))
    t = np.concatenate(times)
    flux = 1.0 + rng.normal(0.0, 600e-6, t.size)
    return LightCurveData(
        t, flux, np.full(t.size, 600e-6), np.concatenate(secs), np.full(t.size, 2018)
    )


def _noise(sectors, sigma_w, r2_box, r2_base, excluded=()):
    def est(n, r2):
        return NoiseEstimate(
            n,
            {
                s: SectorNoise(s, n, 100, sigma_w, float("nan"), r2, 1.0, s in excluded, None)
                for s in sectors
            },
        )

    return EventNoise(box=est(75, r2_box), base=est(108, r2_base))


def test_p3_the_per_event_variance_follows_the_formula():
    lc = _flat_lc()
    params = EventParams()
    sigma_w, r2_box, r2_base = 600e-6, 4e-8, 3e-8
    noise = _noise((1, 2), sigma_w, r2_box, r2_base)
    ev = per_event_depths(lc, 3.7, 1326.3, 2.5 / 24, CADENCE, params, noise=noise)
    assert len(ev) > 5
    half = 2.5 / 48
    inner = half + params.baseline_gap_durations * 2.5 / 24
    outer = half + params.baseline_outer_durations * 2.5 / 24
    for center, err, n_in in zip(ev.centers, ev.errors, ev.n_in, strict=True):
        dt = np.abs(lc.time - center)
        n_base = int(np.sum((dt > inner) & (dt <= outer)))
        assert int(np.sum(dt <= half)) == n_in
        expected = np.sqrt(sigma_w**2 * (1 / n_in + 1 / n_base) + r2_box + r2_base)
        assert err == pytest.approx(expected, rel=1e-12)


def test_p4_events_sharing_cadences_keep_only_the_earlier():
    lc = _flat_lc()
    params = EventParams(baseline_outer_durations=6.0)  # spans of 13 h at a 0.4 d period
    noise = _noise((1, 2), 600e-6, 0.0, 0.0)
    ev = per_event_depths(lc, 0.4, 1325.2, 2.0 / 24, CADENCE, params, noise=noise)
    assert ev.dropped.get("shared_cadences", 0) > 0
    outer = 1.0 / 24 + 6.0 * 2.0 / 24
    spans = [(c - outer, c + outer) for c in ev.centers]
    for (_a0, a1), (b0, _b1) in zip(spans, spans[1:], strict=False):
        assert b0 > a1 or not np.any((lc.time >= b0) & (lc.time <= a1))


def test_p7_events_of_an_excluded_sector_are_dropped_and_reported():
    lc = _flat_lc()
    noise = _noise((1, 2), 600e-6, 0.0, 0.0, excluded=(2,))
    ev = per_event_depths(lc, 3.7, 1326.3, 2.5 / 24, CADENCE, EventParams(), noise=noise)
    assert len(ev) > 0
    assert ev.dropped.get("excluded_sector", 0) > 0
    assert np.all(ev.centers < 1355.0)  # only sector 1


# --- P5: the corrected error is never below the white-propagated one ------------------------


def test_p5_correlated_noise_never_lowers_the_per_event_error():
    flat = synthetic.scenario_data("planet", 0, "correlated").lc
    plan = _plan(ON)
    from refute.packs.tess.rednoise import event_noise

    duration = 2.5 / 24
    noise = event_noise(flat, None, synthetic.PLANET.period, synthetic.PLANET.t0, duration, plan)
    with_noise = per_event_depths(
        flat,
        synthetic.PLANET.period,
        synthetic.PLANET.t0,
        duration,
        CADENCE,
        plan.gauntlet.events,
        noise=noise,
    )
    white = per_event_depths(
        flat, synthetic.PLANET.period, synthetic.PLANET.t0, duration, CADENCE, plan.gauntlet.events
    )
    common = np.intersect1d(with_noise.epochs, white.epochs)
    assert common.size > 5
    for epoch in common:
        a = with_noise.errors[with_noise.epochs == epoch][0]
        b = white.errors[white.epochs == epoch][0]
        assert a >= 0.9 * b  # sigma_r2 >= 0; sigma_w per sector vs per point within 10%
    assert np.median(with_noise.errors) > 1.5 * np.median(white.errors)


# --- P6: an undetermined noise model makes the gate INCONCLUSIVE ---------------------------


def test_p6_an_undetermined_noise_model_makes_the_gate_inconclusive():
    data = synthetic.scenario_data("planet", 0)
    analysis = analyze_data(data, _plan({"enabled": True, "b_min": 100_000}))
    snr = _test(analysis, "snr")
    assert snr.status.value == "INCONCLUSIVE"
    assert "noise model undetermined" in snr.message
    assert analysis.verdict == "INCONCLUSIVE"


def test_the_corrections_section_is_validated():
    with pytest.raises(ValueError):
        _plan({"enabled": True, "b_min": 0})
    defaults = TessTestPlan().gauntlet.corrections
    assert defaults.enabled is False
    assert (defaults.b_min, defaults.gap_split, defaults.r_min) == (20, 5, 20)
