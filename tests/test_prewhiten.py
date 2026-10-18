"""M4 piece 7: the prewhitening (revision 3, 7; revision 4, 4;
docs/validation/v0.2.1/reopen/m4-implementation-map.md, Amendment 22, which declares the
computation, the flow and these cases before the tests and the code).

Direct cases give ``prewhiten`` a curve built as already detrended (1 + signal + noise);
integrated cases run the pipeline on raw data. White noise 600 ppm; correlated noise adds an AR(1)
of 400 ppm with ``tau`` = 1 h (the suite's scenarios use their own profile). New seeds 6100 to
6199, one per case and noise model. A failed precondition makes a case incompatible with its
construction (the criterion is then not shown), never a reason to try another seed.
"""

from __future__ import annotations

import inspect
import math

import numpy as np
import pytest

from refute.packs.tess import synthetic
from refute.packs.tess.params import TessTestPlan
from refute.packs.tess.synthetic import SignalSpec, make_lightcurve
from refute.packs.tess.types import LightCurveData

P_V = 0.7  # the variability period (the suite's SINUSOID_PERIOD)
A_V = 4000e-6
BOX = SignalSpec(period=3.7, t0=1326.3, depth=600e-6, duration=2.5 / 24)
NOISE = {"white": 0.0, "correlated": 400.0}


def _plan(**corrections) -> TessTestPlan:
    plan = synthetic.fast_plan_dict()
    plan["gauntlet"] = {"corrections": {"version": 2, "enabled": True, **corrections}}
    return TessTestPlan.model_validate(plan)


def _pw():
    from refute.packs.tess.prewhiten import prewhiten

    return prewhiten


def _with(lc: LightCurveData, extra: np.ndarray) -> LightCurveData:
    return LightCurveData(lc.time, lc.flux + extra, lc.flux_err, lc.sector, lc.year)


def _sine(t, period=P_V, amp=A_V, t0=1325.3):
    return amp * np.sin(2 * np.pi * (t - t0) / period)


def _in_box(t, spec=BOX):
    off = np.mod(t - spec.t0 + 0.5 * spec.period, spec.period) - 0.5 * spec.period
    return np.abs(off) <= spec.duration / 2


def _depth(lc: LightCurveData, model=None, spec=BOX) -> float:
    """d(x): the mean of x - 1 outside the box minus its mean over the box (a dip positive)."""
    x = lc.flux - 1.0 - (0.0 if model is None else model)
    box = _in_box(lc.time, spec)
    return float(np.mean(x[~box]) - np.mean(x[box]))


def _amplitude(t, y, period=P_V) -> float:
    """sqrt(a^2 + b^2) of an unweighted least-squares sinusoid (with a constant)."""
    w = 2 * np.pi * t / period
    design = np.column_stack([np.ones_like(t), np.cos(w), np.sin(w)])
    coef, *_ = np.linalg.lstsq(design, y, rcond=None)
    return float(math.hypot(coef[1], coef[2]))


def _grid_step(lc: LightCurveData) -> float:
    return 1.0 / (10.0 * float(lc.time.max() - lc.time.min()))


def _bare(seed, noise, spec=None):
    lc, _ = make_lightcurve(spec, seed=seed, red_noise_ppm=NOISE[noise])
    return lc


# --- direct cases ------------------------------------------------------------------------------


@pytest.mark.parametrize(("noise", "seed"), [("white", 6100), ("correlated", 6101)])
def test_d1_a_transit_under_a_stronger_sinusoid_is_kept(noise, seed):
    b = _bare(seed, noise, BOX)
    a = _with(b, _sine(b.time))
    pw = _pw()(a, _plan())
    assert pw.components, pw.reason
    first = pw.components[0]
    assert abs(first.frequency - 1 / P_V) <= _grid_step(a)
    assert first.fap < _plan().gauntlet.corrections.fap_max and first.h >= 0.9
    assert abs(_depth(a, pw.model) - _depth(b)) <= 60e-6


@pytest.mark.parametrize(("noise", "seed"), [("white", 6102), ("correlated", 6103)])
def test_d2_a_pure_sinusoid_is_removed(noise, seed):
    a = _with(_bare(seed, noise), _sine(_bare(seed, noise).time))
    pw = _pw()(a, _plan())
    assert pw.components, pw.reason
    assert abs(pw.components[0].frequency - 1 / P_V) <= _grid_step(a)
    assert _amplitude(a.time, a.flux - 1.0 - pw.model) <= 0.05 * A_V


@pytest.mark.parametrize(("noise", "seed"), [("white", 6104), ("correlated", 6105)])
def test_d3_a_pure_box_is_not_removed_and_a_rejection_ends(noise, seed, monkeypatch):
    import astropy.timeseries as ts

    built = []
    real = ts.LombScargle

    class Counting(real):
        def __init__(self, *args, **kwargs):
            built.append(1)
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(ts, "LombScargle", Counting)
    spec = SignalSpec(period=3.7, t0=1326.3, depth=2000e-6, duration=2.5 / 24)
    pw = _pw()(_bare(seed, noise, spec), _plan())
    assert pw.components == []
    assert pw.reason in ("few_harmonics_fail", "fap_above_max")
    assert pw.rejected is not None and np.all(pw.model == 0.0)
    assert len(built) == 2  # L0 and L1 of the one iteration


def test_the_fap_guard_rejects_a_frequency_at_or_above_fap_max(monkeypatch):
    # written after the sabotage SW2 escaped (map Amendment 24): in white noise h >= h_min
    # already needs an SNR that makes the FAP tiny, so no construction makes the FAP decide; this
    # direct case routes a FAP of 0.5 through the guard
    import astropy.timeseries as ts

    monkeypatch.setattr(ts.LombScargle, "false_alarm_probability", lambda self, *a, **k: 0.5)
    lc = _bare(6141, "white")
    pw = _pw()(_with(lc, _sine(lc.time)), _plan())
    assert pw.components == [] and pw.reason == "fap_above_max"
    assert pw.rejected["fap"] == 0.5 and pw.rejected["h"] >= 0.9


def test_d4_several_components_and_the_limit():
    lc = _bare(6106, "white")
    two = _with(lc, _sine(lc.time) + _sine(lc.time, period=0.43, amp=2500e-6, t0=1325.9))
    pw = _pw()(two, _plan())
    freqs = [c.frequency for c in pw.components]
    assert len(freqs) == 2, (pw.reason, freqs)
    assert abs(freqs[0] - 1 / P_V) <= _grid_step(two)
    assert abs(freqs[1] - 1 / 0.43) <= _grid_step(two)
    one = _pw()(two, _plan(max_components=1))
    assert len(one.components) == 1 and one.reason == "max_components"


def test_d4_max_components_zero_builds_no_periodogram(monkeypatch):
    import astropy.timeseries as ts

    def refuse(*args, **kwargs):
        raise AssertionError("a periodogram was built")

    monkeypatch.setattr(ts, "LombScargle", refuse)
    lc = _bare(6107, "white")
    pw = _pw()(_with(lc, _sine(lc.time)), _plan(max_components=0))
    assert pw.components == [] and pw.reason == "max_components"


def test_d5_the_asymmetric_fit_clips_the_box_and_keeps_the_constants():
    from refute.packs.tess.rednoise import estimate

    plan = _plan()
    c = plan.gauntlet.corrections
    bare = _bare(6130, "white")
    s1, s2 = sorted(np.unique(bare.sector))
    offsets = np.where(bare.sector == s1, 300e-6, -200e-6)
    no_box = _with(
        bare, _sine(bare.time) + offsets
    )  # the scale the operation uses, without the box
    est = estimate(
        no_box.time,
        no_box.flux - 1.0,
        no_box.sector,
        np.ones(no_box.flux.size, bool),
        1,
        c.gap_split,
        120.0 / 86400.0,
        c.b_min,
    )
    sigma_w = float(np.median([v.sigma_w for v in est.sectors.values()]))
    spec = SignalSpec(
        period=3.7, t0=1326.3, depth=8 * sigma_w, duration=2.5 / 24, ingress_fraction=0.0
    )
    lc = _with(_bare(6130, "white", spec), _sine(bare.time) + offsets)
    deficit = 1.0 - synthetic.signal_model(lc.time, spec)
    full = np.isclose(deficit[_in_box(lc.time)], spec.depth, rtol=1e-9, atol=0.0)
    assert np.all(full)  # precondition: every masked cadence at the full depth
    pw = _pw()(lc, plan)
    assert spec.depth >= 2 * c.k_clip * float(np.max(pw.dy)), (spec.depth, np.max(pw.dy))
    assert pw.components, pw.reason
    comp = pw.components[0]
    box = _in_box(lc.time)
    clipped = np.zeros(lc.flux.size, bool)
    clipped[comp.clip_indices] = True
    assert np.all(clipped[box])
    assert abs(comp.amplitude - A_V) <= 0.05 * A_V
    assert np.all(pw.model[box] != 0.0)  # subtracted on the clipped cadences too
    rest = lc.flux - 1.0 - pw.model
    for s, want in ((s1, 300e-6), (s2, -200e-6)):
        assert abs(float(np.mean(rest[(lc.sector == s) & ~box])) - want) <= 20e-6


def test_q1_the_sequence_of_one_iteration_recomputed_independently():
    from astropy.timeseries import LombScargle

    from refute.packs.tess.prewhiten import few_harmonic_test

    plan = _plan()
    c = plan.gauntlet.corrections
    b = _bare(6109, "white", BOX)
    a = _with(b, _sine(b.time))
    pw = _pw()(a, plan)
    comp = pw.components[0]
    idx = pw.used_index
    t, r, dy = a.time[idx], a.flux[idx] - 1.0, pw.dy
    kw = {"fit_mean": True, "center_data": True, "nterms": 1, "normalization": "standard"}
    l0 = LombScargle(t, r, dy, **kw)
    power = l0.power(pw.grid)
    assert comp.frequency == float(pw.grid[int(np.argmax(power))])
    clip = (r - comp.fitted) < -c.k_clip * dy
    assert np.array_equal(np.flatnonzero(clip), np.searchsorted(idx, comp.clip_indices))
    l1 = LombScargle(t[~clip], r[~clip], dy[~clip], **kw)
    p1 = float(l1.power(comp.frequency))
    assert p1 == pytest.approx(comp.p1, rel=1e-12)
    fap = l1.false_alarm_probability(
        p1,
        method="baluev",
        minimum_frequency=pw.f_lo,
        maximum_frequency=12.0,
        samples_per_peak=10,
    )
    assert float(fap) == pytest.approx(comp.fap, rel=1e-9)
    h, n_bins, reason = few_harmonic_test(t[~clip], r[~clip], comp.fitted[~clip], comp.frequency)
    assert reason is None and h == pytest.approx(comp.h, rel=1e-12)
    phase = np.mod(t[~clip] * comp.frequency, 1.0)
    index = np.minimum((phase * 50).astype(int), 49)
    counts = np.bincount(index, minlength=50)
    assert n_bins == int(np.sum(counts >= 3))


def _q2_curve(bins, seed):
    k = np.arange(40)[:, None, None]
    b = np.asarray(bins)[None, :, None]
    j = np.arange(4)[None, None, :]
    t = np.sort((1325.0 + k * P_V + (b + 0.5 + j / 8.0) * P_V / 50.0).ravel())
    rng = np.random.default_rng(seed)
    flux = 1.0 + _sine(t) + rng.normal(0.0, 600e-6, t.size)
    one = np.ones(t.size, dtype=int)
    return LightCurveData(t, flux, np.full(t.size, 600e-6), one, one * 2018)


def test_q2_too_few_phase_bins_at_the_chosen_frequency():
    # Amendment 23: the precondition is its purpose, fewer than 40 bins at the chosen f* (the
    # first run, seed 6110, gave 31 bins, not exactly 30: f* is the nearest grid frequency)
    lc = _q2_curve(range(30), 6131)
    pw = _pw()(lc, _plan())
    rej = pw.rejected
    assert rej is not None and abs(rej["frequency"] - 1 / P_V) <= _grid_step(lc), rej  # precond.
    assert rej["bins"] < 40  # precondition: the occupancy after the clipping at f*
    assert pw.reason == "too_few_phase_bins" and pw.components == []


def _bins_case(cadences_per_bin):
    """Cadences by formula for the helper: bin b gets ``cadences_per_bin[b]`` cadences at f = 1."""
    t = []
    for b, n in enumerate(cadences_per_bin):
        t += [(b + 0.25 + 0.5 * i / max(n, 1)) / 50.0 for i in range(n)]
    t = np.asarray(t)
    rng = np.random.default_rng(6111)
    return t, rng.normal(0.0, 1.0, t.size)


def test_b1_b2_the_three_cadence_and_forty_bin_limits():
    from refute.packs.tess.prewhiten import few_harmonic_test

    t, y = _bins_case([3] * 40)
    h, n_bins, reason = few_harmonic_test(t, y, np.zeros_like(y), 1.0)
    assert (n_bins, reason) == (40, None) and math.isfinite(h)
    t, y = _bins_case([2] + [3] * 39)
    _, n_bins, reason = few_harmonic_test(t, y, np.zeros_like(y), 1.0)
    assert (n_bins, reason) == (39, "too_few_phase_bins")


def test_b3_a_zero_variance_of_the_bin_means_is_not_finite():
    from refute.packs.tess.prewhiten import few_harmonic_test

    t = np.repeat((np.arange(50) + 0.5) / 50.0, 2) + np.tile([-0.001, 0.001], 50)
    y = np.tile([1.0, -1.0], 50)  # every bin's mean is 0: non-constant cadences, zero variance
    t = np.concatenate([t, t + 1e-4])
    y = np.concatenate([y, y])
    _, n_bins, reason = few_harmonic_test(t, y, np.zeros_like(y), 1.0)
    assert n_bins == 50 and reason == "non_finite_statistic"


def test_b4_a_constant_curve_has_no_usable_noise():
    lc = _bare(6112, "white")
    flat = LightCurveData(lc.time, np.ones_like(lc.flux), lc.flux_err, lc.sector, lc.year)
    pw = _pw()(flat, _plan())
    assert pw.reason == "noise_undetermined" and pw.components == []


def test_r1_the_refit_is_one_joint_fit_outside_the_mask():
    from refute.packs.tess.prewhiten import Component, refit
    from refute.packs.tess.rednoise import estimate

    plan = _plan()
    c = plan.gauntlet.corrections
    base = _bare(6113, "white", SignalSpec(period=3.7, t0=1326.3, depth=3000e-6, duration=0.1))
    f1, f2 = 1 / 0.70, 1 / 0.75
    lc = _with(base, _sine(base.time, period=0.70) + _sine(base.time, period=0.75, amp=3000e-6))
    mask = _in_box(lc.time, SignalSpec(period=3.7, t0=1326.3, depth=0.0, duration=0.1))
    comps = [Component(f, 0.0, 1.0, 1.0, 0.0, 0, {}) for f in (f1, f2)]
    got = refit(lc, comps, mask, plan)
    assert got.reason is None
    est = estimate(
        lc.time,
        lc.flux - 1.0,
        lc.sector,
        np.ones(lc.flux.size, bool),
        1,
        c.gap_split,
        120.0 / 86400.0,
        c.b_min,
    )
    sectors = sorted(est.sectors)
    sigma = np.empty(lc.flux.size)
    for s in sectors:
        sigma[lc.sector == s] = est.sectors[s].sigma_w

    def solve(freqs):
        cols, sinus = [], []
        for s in sectors:
            cols.append((lc.sector == s).astype(float))
        for f in freqs:
            for s in sectors:
                on = (lc.sector == s).astype(float)
                for k in (1, 2):
                    for fn in (np.cos, np.sin):
                        sinus.append(len(cols))
                        cols.append(on * fn(2 * np.pi * k * f * lc.time))
        x = np.column_stack(cols)
        root = np.where(mask, 0.0, 1.0 / sigma)
        coef, *_ = np.linalg.lstsq(root[:, None] * x, root * (lc.flux - 1.0), rcond=None)
        return x[:, sinus] @ coef[sinus]

    joint = solve([f1, f2])
    separate = solve([f1]) + solve([f2])
    assert np.max(np.abs(joint - separate)) > 0.01 * A_V  # precondition: distinguishable
    assert np.max(np.abs(got.model - joint)) <= 1e-9
    moved = lc.flux.copy()
    moved[mask] += 0.05  # the masked cadences have no weight
    moved_lc = LightCurveData(lc.time, moved, lc.flux_err, lc.sector, lc.year)
    assert np.max(np.abs(refit(moved_lc, comps, mask, plan).model - got.model)) <= 1e-9


def test_sig_prewhiten_has_no_class_truth_or_candidate():
    assert list(inspect.signature(_pw()).parameters) == ["curve", "plan"]


# --- integrated cases ------------------------------------------------------------------------


def _sinusoid_data(noise, seed, transit_depth=None):
    data = synthetic.scenario_data("sinusoid", seed, noise)
    if transit_depth is None:
        return data
    spec = SignalSpec(period=3.7, t0=1326.3, depth=transit_depth, duration=2.5 / 24)
    lc = data.lc
    lc = LightCurveData(
        lc.time, lc.flux * synthetic.signal_model(lc.time, spec), lc.flux_err, lc.sector, lc.year
    )
    return synthetic.make_data(lc, data.sectors, data.star, aux=data.aux)


def _input_amplitude(data, plan):
    from refute.packs.tess.detrend import detrend

    flat = detrend(data.lc, plan.detrend)
    return _amplitude(flat.time, flat.flux - 1.0)


@pytest.mark.parametrize(("noise", "seed"), [("white", 6114), ("correlated", 6115)])
def test_i1_a_transit_under_variability_is_found(noise, seed):
    from refute.packs.tess.pipeline import analyze_data

    plan = _plan()
    data = _sinusoid_data(noise, seed, 1500e-6)
    assert _input_amplitude(data, plan) >= 0.5 * 0.004  # precondition: the sinusoid reaches it
    analysis = analyze_data(data, plan)
    final = analysis.gauntlet.candidate
    snr = next(t for t in analysis.tests if t.name == "snr")
    assert final is not None and snr.status.value == "PASS", snr.message
    assert any(abs(final.period - f * 3.7) / (f * 3.7) <= 0.001 for f in (1.0, 2.0, 0.5))


class SpuriousCandidatePassedGateError(Exception):
    """Raised only by I2's final predicate, so that its expected failure covers nothing else."""


I2_CORRELATED_FAILED = pytest.mark.xfail(
    strict=True,
    raises=SpuriousCandidatePassedGateError,
    reason=(
        "map Amendment 24: the retest FAILED in correlated noise (a red-noise box passes the gate, "
        "with or without the prewhitening); recorded, NOT an acceptance"
    ),
)


@pytest.mark.parametrize(
    ("noise", "seed"),
    [("white", 6133), pytest.param("correlated", 6134, marks=I2_CORRELATED_FAILED)],
)
def test_i2_a_pure_sinusoid_leaves_no_candidate_passing_the_gate(noise, seed):
    # Amendment 23: new seeds, the same criterion and the same two curves (the first run, seeds
    # 6116 and 6117, FAILED in white noise: recorded)
    from refute.packs.tess.pipeline import analyze_data

    plan = _plan()
    data = _sinusoid_data(noise, seed)
    assert _input_amplitude(data, plan) >= 0.5 * 0.004  # precondition
    analysis = analyze_data(data, plan)
    snr = next(t for t in analysis.tests if t.name == "snr")
    if snr.status.value == "PASS":
        raise SpuriousCandidatePassedGateError(snr.message)


def _box_data(seed):
    spec = SignalSpec(period=3.7, t0=1326.3, depth=2000e-6, duration=2.5 / 24)
    lc, sectors = make_lightcurve(spec, seed=seed)
    return synthetic.make_data(lc, sectors, synthetic.make_star(), aux=synthetic.make_aux(lc))


def test_z_nothing_accepted_leaves_every_curve_bit_equal():
    from refute.packs.tess.detrend import detrend
    from refute.packs.tess.events import transit_mask
    from refute.packs.tess.pipeline import analyze_data

    plan = _plan()
    data = _box_data(6118)
    analysis = analyze_data(data, plan)
    pw = analysis.gauntlet.prewhitening
    assert pw is not None and pw.components == [], pw  # precondition
    assert np.array_equal(analysis.flattened_search.flux, detrend(data.lc, plan.detrend).flux)
    cand = analysis.search.candidate
    half = plan.detrend.transit_mask_half_width_durations * cand.duration
    mask = transit_mask(data.lc.time, cand.period, cand.t0, half)
    assert np.array_equal(
        analysis.gauntlet.flattened.flux, detrend(data.lc, plan.detrend, mask=mask).flux
    )


def test_in_the_curves_reach_their_consumers(monkeypatch):
    import refute.packs.tess.pipeline as pipeline
    from refute.packs.tess.detrend import detrend
    from refute.packs.tess.search import search_period

    plan = _plan()
    data = _sinusoid_data("white", 6119, 1500e-6)
    seen = {"alias": [], "search": [], "finalize": []}
    real_alias, real_finalize = pipeline.check_period_alias, pipeline.finalize_candidate

    def alias(lc, candidate, p):
        seen["alias"].append(lc)
        return real_alias(lc, candidate, p)

    def finalize(lc, *args, **kwargs):
        seen["finalize"].append(lc)
        return real_finalize(lc, *args, **kwargs)

    def search(lc, params):
        seen["search"].append(lc)
        return search_period(lc, params)

    monkeypatch.setattr(pipeline, "check_period_alias", alias)
    monkeypatch.setattr(pipeline, "finalize_candidate", finalize)
    analysis = pipeline.analyze_data(data, plan, search_fn=search)
    pw = analysis.gauntlet.prewhitening
    assert pw.components  # precondition: a component was accepted
    assert all(lc is data.lc for lc in seen["alias"])
    # Amendment 23: the search receives detrend(raw - S_raw), S_raw the joint raw refit
    from refute.packs.tess.prewhiten import refit

    s_raw = refit(data.lc, pw.components, np.zeros(data.lc.time.size, bool), plan).model
    raw_minus = LightCurveData(
        data.lc.time, data.lc.flux - s_raw, data.lc.flux_err, data.lc.sector, data.lc.year
    )
    assert np.array_equal(seen["search"][0].flux, detrend(raw_minus, plan.detrend).flux)
    assert seen["finalize"] and seen["finalize"][0] is analysis.gauntlet.flattened
    target = {"key": "synthetic", "tic_id": 1, "kind": "planet", "name": "planet-0"}
    record = pipeline.build_result(target, data, plan, analysis, {"pass_criteria": {}})
    assert "prewhitening" in record["corrections"]["executed"]
    assert record["corrections"]["prewhitening"]["global"]["components"]


def test_ad_the_adapters_give_the_same_components_and_tests():
    from refute.packs.tess.pipeline import TessGauntlet, TessSearch, analyze_data

    plan = _plan()
    params = plan.model_dump(mode="json")
    data = _sinusoid_data("white", 6120, 1500e-6)
    analysis = analyze_data(data, plan)
    found = TessSearch().run(data, params)
    assert found.candidate == analysis.search.candidate
    tests = TessGauntlet().run(data, found.candidate, {}, params)
    assert [t.to_dict() for t in tests] == [t.to_dict() for t in analysis.gauntlet.tests]


@pytest.mark.parametrize(
    "block", [{"version": 1, "enabled": True}, {"version": 2, "enabled": False}]
)
def test_off_an_inactive_block_gives_the_m3_inputs(block):
    from refute.packs.tess.pipeline import analyze_data

    data = _sinusoid_data("white", 6121, 1500e-6)
    fast = synthetic.fast_plan_dict()
    legacy = analyze_data(data, TessTestPlan.model_validate(fast))
    off = analyze_data(
        data, TessTestPlan.model_validate({**fast, "gauntlet": {"corrections": block}})
    )
    assert np.array_equal(off.flattened_search.flux, legacy.flattened_search.flux)
    assert np.array_equal(off.gauntlet.flattened.flux, legacy.gauntlet.flattened.flux)
    assert off.gauntlet.prewhitening is None
    assert [t.to_dict() for t in off.tests] == [t.to_dict() for t in legacy.tests]


def test_h_the_train_fundamentals_reach_every_window_of_the_round(monkeypatch):
    import refute.packs.tess.holdout as holdout

    calls = {"train_replica_stats": [], "replica_stats": [], "measure_windows": []}
    for name in calls:
        real = getattr(holdout, name)

        def spy(*args, _real=real, _name=name, **kwargs):
            calls[_name].append(kwargs.get("frequencies", args[-1] if args else None))
            return _real(*args, **kwargs)

        monkeypatch.setattr(holdout, name, spy)
    # Amendment 23: the spies see the 2020 round only (the first run counted the three rounds),
    # and the scenario has a new seed
    data = synthetic.scenario_data("variability_train_only", 6132)
    r = holdout._round(data.lc, data.sectors, 2020, _plan())
    comps = r.metrics.get("prewhitening", {}).get("components", [])
    assert comps, r.message  # precondition: train components
    assert r.metrics["capacity"].get("decision_2") == "pass", r.message  # precondition
    assert len(calls["measure_windows"]) == 2  # precondition: transit and control measured
    want = r.metrics["prewhitening"]["fundamentals"]
    for name, got in calls.items():
        assert got and all(list(g) == want for g in got), (name, got, want)


# --- the new cases of Amendment 23 (separate from the retest) -------------------------------


def _raw_data(spec, seed, noise, variability=None, trend=0.0):
    red = {"red_noise_ppm": 600.0, "red_tau_days": 1.0 / 24.0} if noise == "correlated" else {}
    lc, sectors = make_lightcurve(spec, seed=seed, trend_amplitude=trend, **red)
    if variability is not None:
        lc = _with(lc, _sine(lc.time, period=variability))
    return synthetic.make_data(lc, sectors, synthetic.make_star(), aux=synthetic.make_aux(lc))


TRANSIT = SignalSpec(period=3.7, t0=1326.3, depth=1500e-6, duration=2.5 / 24)


def _full_path_ran(analysis, data, plan, period):
    """The preconditions of N1 and N2: the injected frequency among the accepted components, and
    both raw refits of the full path executed without failure."""
    from refute.packs.tess.pipeline import build_result

    pw = analysis.gauntlet.prewhitening
    step = _grid_step(data.lc)
    assert any(abs(c.frequency - 1 / period) <= step for c in pw.components), pw.reason
    target = {"key": "synthetic", "tic_id": 1, "kind": "planet", "name": "planet-0"}
    pre = build_result(target, data, plan, analysis, {"pass_criteria": {}})["corrections"]
    assert pre["prewhitening"]["search_refit_reason"] is None
    assert analysis.gauntlet.candidate is not None
    assert pre["prewhitening"]["refit_reason"] is None


@pytest.mark.parametrize(("noise", "seed"), [("white", 6135), ("correlated", 6136)])
def test_n1_the_full_path_preserves_the_depth_when_the_box_projects_on_the_components(noise, seed):
    from refute.packs.tess.pipeline import analyze_data

    plan = _plan()
    a_data = _raw_data(TRANSIT, seed, noise, variability=0.74)
    a = analyze_data(a_data, plan)
    b = analyze_data(_raw_data(TRANSIT, seed, noise), plan)
    _full_path_ran(a, a_data, plan, 0.74)  # preconditions
    assert b.gauntlet.prewhitening.components == []  # precondition: nothing accepted on B
    d_a = _depth(a.gauntlet.flattened, spec=TRANSIT)
    d_b = _depth(b.gauntlet.flattened, spec=TRANSIT)
    assert abs(d_a - d_b) <= 60e-6, (d_a, d_b)


def test_n2_a_slow_unmodelled_trend_keeps_the_depth_and_the_gate():
    from refute.packs.tess.pipeline import analyze_data

    plan = _plan()
    a_data = _raw_data(TRANSIT, 6137, "white", variability=P_V, trend=0.002)
    a = analyze_data(a_data, plan)
    b = analyze_data(_raw_data(TRANSIT, 6137, "white", trend=0.002), plan)
    _full_path_ran(a, a_data, plan, P_V)  # preconditions
    assert b.gauntlet.prewhitening.components == []  # precondition: nothing accepted on B
    d_a = _depth(a.gauntlet.flattened, spec=TRANSIT)
    d_b = _depth(b.gauntlet.flattened, spec=TRANSIT)
    assert abs(d_a - d_b) <= 60e-6, (d_a, d_b)
    final = a.gauntlet.candidate
    snr = next(t for t in a.tests if t.name == "snr")
    assert final is not None and snr.status.value == "PASS", snr.message
    assert any(abs(final.period - f * 3.7) / (f * 3.7) <= 0.001 for f in (1.0, 2.0, 0.5))


def test_n3_a_singular_raw_refit_is_recorded_for_the_search_and_the_reanalysis(monkeypatch):
    import refute.packs.tess.pipeline as pipeline
    from refute.packs.tess.detrend import detrend
    from refute.packs.tess.events import transit_mask
    from refute.packs.tess.prewhiten import Component

    real = pipeline.prewhiten

    def at_the_cadence(curve, p):
        pw = real(curve, p)
        pw.components = [Component(720.0, 0.0, 1.0, 1.0, 1e-3, 0, {})]  # cos(2 pi f t) constant
        return pw

    monkeypatch.setattr(pipeline, "prewhiten", at_the_cadence)
    plan = _plan()
    data = _raw_data(TRANSIT, 6138, "white")
    analysis = pipeline.analyze_data(data, plan)
    target = {"key": "synthetic", "tic_id": 1, "kind": "planet", "name": "planet-0"}
    record = pipeline.build_result(target, data, plan, analysis, {"pass_criteria": {}})
    pre = record["corrections"]["prewhitening"]
    assert analysis.search.candidate is not None  # precondition: the reanalysis ran
    assert pre["search_refit_reason"] == "singular_design"
    assert pre["refit_reason"] == "singular_design"
    assert np.array_equal(analysis.flattened_search.flux, detrend(data.lc, plan.detrend).flux)
    cand = analysis.search.candidate
    half = plan.detrend.transit_mask_half_width_durations * cand.duration
    mask = transit_mask(data.lc.time, cand.period, cand.t0, half)
    m3 = detrend(data.lc, plan.detrend, mask=mask)
    assert np.array_equal(analysis.gauntlet.flattened.flux, m3.flux)


def test_n3_a_short_sector_is_reported_as_left_out_of_the_raw_refit():
    from refute.packs.tess.pipeline import analyze_data, build_result

    plan = _plan(b_min=15000)  # sector 1 (18720 cadences) used, the shortened sector 2 not
    data = _raw_data(TRANSIT, 6139, "white", variability=P_V)
    lc = data.lc
    second = int(lc.sector.max())
    keep = (lc.sector != second) | (np.cumsum(lc.sector == second) <= 10000)
    short = lc.select(keep)
    data = synthetic.make_data(short, data.sectors, data.star, aux=synthetic.make_aux(short))
    analysis = analyze_data(data, plan)
    pw = analysis.gauntlet.prewhitening
    assert pw.components and pw.sectors_left_out == [second], (pw.reason, pw.sectors_left_out)
    target = {"key": "synthetic", "tic_id": 1, "kind": "planet", "name": "planet-0"}
    record = build_result(target, data, plan, analysis, {"pass_criteria": {}})
    assert record["corrections"]["prewhitening"]["search_left_out"] == [second]
