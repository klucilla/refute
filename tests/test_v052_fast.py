"""The faster code of battery version 4 against the reference, on constructed cases (the criteria
are frozen in docs/validation/v0.5.2/stage2/fast-detrend-equivalence.md). No network, synthetic
data only."""

from __future__ import annotations

import numpy as np
import pytest

from refute.packs.tess import a0, a0_v4, detrend, detrend_fast, rednoise, rednoise_fast
from refute.packs.tess.battery import additive_residuals
from refute.packs.tess.params import DetrendParams
from refute.packs.tess.types import LightCurveData

CADENCE = 2.0 / 1440.0
PARAMS = DetrendParams()


def curve(seed=1, days=12.0, gap=(5.5, 6.5), sector=1, start=100.0):
    rng = np.random.default_rng(seed)
    t = np.arange(start, start + days, CADENCE)
    t = t[(t < start + gap[0]) | (t > start + gap[1])]
    f = 1.0 + 0.001 * np.sin(t) + rng.normal(0.0, 5e-4, t.size)
    return LightCurveData(t, f, np.full(t.size, 5e-4), np.full(t.size, sector), np.zeros(t.size))


def same(a, b, tolerance=1e-11):
    assert np.array_equal(a.time, b.time)
    assert np.max(np.abs(a.flux - b.flux), initial=0.0) <= tolerance
    assert np.max(np.abs(a.flux_err - b.flux_err), initial=0.0) <= tolerance


def test_a_noisy_curve_matches_the_reference():
    lc = curve()
    same(detrend.detrend(lc, PARAMS), detrend_fast.detrend(lc, PARAMS))


def test_a_mask_matches_the_reference():
    lc = curve(2)
    mask = np.abs(np.mod(lc.time, 3.0) - 1.5) < 0.1
    same(detrend.detrend(lc, PARAMS, mask=mask), detrend_fast.detrend(lc, PARAMS, mask=mask))


def test_outliers_are_clipped_as_the_reference_clips_them():
    lc = curve(3)
    lc.flux[::97] += 0.02
    same(detrend.detrend(lc, PARAMS), detrend_fast.detrend(lc, PARAMS))


def test_the_reuse_under_a_further_mask_matches_a_full_detrending():
    lc = curve(4)
    base = np.abs(np.mod(lc.time, 3.0) - 1.5) < 0.1
    extra = np.abs(lc.time - 102.0) < 0.2
    d = detrend_fast.MaskAwareDetrender(lc, PARAMS, base)
    same(detrend.detrend(lc, PARAMS, mask=base | extra), d.flat(extra))
    same(detrend.detrend(lc, PARAMS, mask=base), d.flat())


def test_a_knot_far_from_a_further_mask_reuses_the_base_fit():
    lc = curve(5)
    base = np.zeros(len(lc), dtype=bool)
    extra = np.abs(lc.time - 102.0) < 0.05
    d = detrend_fast.MaskAwareDetrender(lc, PARAMS, base)
    seg = d.segments[0]
    calls = []
    original = detrend_fast._fit_batch

    def counting(x, y, valid, params):
        calls.append(x.shape[0])
        return original(x, y, valid, params)

    detrend_fast._fit_batch = counting
    try:
        d.flat(extra)
    finally:
        detrend_fast._fit_batch = original
    assert sum(calls) < 0.3 * d.base_fits[0].knots.size
    assert seg.stop > seg.start


def test_a_window_with_too_few_cadences_is_skipped_as_the_reference_skips_it():
    lc = curve(6)
    keep = (lc.time < 103.0) | (lc.time > 104.0) | (np.arange(lc.time.size) % 40 == 0)
    sub = lc.select(keep)
    same(detrend.detrend(sub, PARAMS), detrend_fast.detrend(sub, PARAMS))


def test_a_cadence_on_the_final_upper_clip_goes_to_the_reference():
    lc = curve(21, days=4.0, gap=(9.0, 9.5))
    mask = np.zeros(len(lc), dtype=bool)
    at = len(lc) // 2
    mask[at] = True
    reference = detrend.detrend(lc, PARAMS, mask=mask)
    d = detrend_fast.MaskAwareDetrender(lc, PARAMS, mask)
    flat = lc.flux / detrend.detrend_parts(lc, PARAMS, mask)[1]
    limit = PARAMS.upper_clip_sigma * detrend.robust_sigma(flat[~mask] - 1.0)
    trend_at = detrend.detrend_parts(lc, PARAMS, mask)[1][at]
    placed = lc.flux.copy()
    placed[at] = trend_at * (1.0 + limit * (1.0 - 1e-15))
    moved = LightCurveData(lc.time, placed, lc.flux_err, lc.sector, lc.year)
    same(detrend.detrend(moved, PARAMS, mask=mask), detrend_fast.detrend(moved, PARAMS, mask=mask))
    assert len(reference) == len(d.flat()), "the construction starts from an agreeing curve"


def test_two_tight_clusters_are_poorly_conditioned_and_go_to_the_reference():
    a = 100.0 + np.linspace(0.0, 1e-6, 30)
    b = 100.5 + np.linspace(0.0, 1e-6, 30)
    t = np.concatenate([a, b])
    rng = np.random.default_rng(22)
    f = 1.0 + rng.normal(0.0, 5e-4, t.size)
    lc = LightCurveData(t, f, np.full(t.size, 5e-4), np.ones(t.size, dtype=int), np.zeros(t.size))
    same(detrend.detrend(lc, PARAMS), detrend_fast.detrend(lc, PARAMS))


def test_the_blocks_do_not_change_the_result(monkeypatch):
    lc = curve(23)
    whole = detrend_fast.detrend(lc, PARAMS)
    monkeypatch.setattr(detrend_fast, "CHUNK_ROWS", 7)
    same(whole, detrend_fast.detrend(lc, PARAMS))


def test_a_narrow_cluster_of_cadences_goes_to_the_reference():
    t = np.concatenate([np.arange(100.0, 100.06, CADENCE), np.arange(101.2, 102.5, CADENCE)])
    rng = np.random.default_rng(7)
    f = 1.0 + rng.normal(0.0, 5e-4, t.size)
    lc = LightCurveData(t, f, np.full(t.size, 5e-4), np.ones(t.size, dtype=int), np.zeros(t.size))
    same(detrend.detrend(lc, PARAMS), detrend_fast.detrend(lc, PARAMS))


def test_a_constant_flux_goes_to_the_reference():
    lc = curve(8)
    flat = LightCurveData(lc.time, np.ones(len(lc)), lc.flux_err, lc.sector, lc.year)
    same(detrend.detrend(flat, PARAMS), detrend_fast.detrend(flat, PARAMS))


def test_a_non_finite_flux_behaves_as_the_reference_behaves():
    lc = curve(9)
    lc.flux[300] = np.nan
    try:
        reference = detrend.detrend(lc, PARAMS)
    except np.linalg.LinAlgError:
        with pytest.raises(np.linalg.LinAlgError):
            detrend_fast.detrend(lc, PARAMS)
        return
    same(reference, detrend_fast.detrend(lc, PARAMS))


def test_a_residual_on_the_clipping_threshold_goes_to_the_reference(monkeypatch):
    lc = curve(10)
    original = detrend_fast._fit_quadratic
    sent = []

    def spy(x, y, params):
        sent.append(x.size)
        return original(x, y, params)

    monkeypatch.setattr(detrend_fast, "_fit_quadratic", spy)
    monkeypatch.setattr(detrend_fast, "BOUNDARY_TOLERANCE", 1.0)
    got = detrend_fast.detrend(lc, PARAMS)
    assert sent, "every knot is near a threshold when the tolerance is 1"
    same(detrend.detrend(lc, PARAMS), got)


def test_the_additive_path_matches_the_reference():
    a, b = curve(11), curve(12, sector=2, start=120.0)
    t = np.concatenate([a.time, b.time])
    v = np.concatenate([a.flux, b.flux])
    s = np.concatenate([a.sector, b.sector])
    mask = np.abs(np.mod(t, 3.0) - 1.5) < 0.1
    extra = np.abs(t - 102.0) < 0.2

    class Plan:
        detrend = PARAMS

    d = detrend_fast.AdditiveDetrender(t, v, s, PARAMS, mask)
    for further, whole in ((None, mask), (extra, mask | extra)):
        reference = additive_residuals(t, v, s, whole, Plan)
        got = d.residuals(further)
        assert np.array_equal(np.isfinite(reference), np.isfinite(got))
        assert np.nanmax(np.abs(reference - got)) <= 1e-11


def test_the_runs_and_bins_are_the_reference_ones():
    lc = curve(13)
    keep = np.ones(len(lc), dtype=bool)
    keep[50:60] = False
    keep[400] = False
    a = rednoise.segments(lc.time, keep, 5.0, CADENCE)
    b = rednoise_fast.segments(lc.time, keep, 5.0, CADENCE)
    assert len(a) == len(b)
    assert all(np.array_equal(x, y) for x, y in zip(a, b, strict=True))
    bins = rednoise.bins(lc.time, keep, 72, 5.0, CADENCE)
    matrix = rednoise_fast.bin_matrix(lc.time, keep, 72, 5.0, CADENCE)
    assert all(np.array_equal(x, y) for x, y in zip(bins, matrix, strict=True))


def test_no_cadence_kept_gives_no_runs():
    lc = curve(14)
    assert rednoise_fast.segments(lc.time, np.zeros(len(lc), dtype=bool), 5.0, CADENCE) == []
    assert (
        rednoise_fast.bin_matrix(lc.time, np.zeros(len(lc), dtype=bool), 8, 5.0, CADENCE).size == 0
    )


def test_the_estimate_is_the_reference_estimate():
    lc = curve(15)
    resid = lc.flux - 1.0
    keep = np.ones(len(lc), dtype=bool)
    a = rednoise.estimate(lc.time, resid, lc.sector, keep, 72, 5.0, CADENCE, 20)
    b = rednoise_fast.estimate(lc.time, resid, lc.sector, keep, 72, 5.0, CADENCE, 20)
    for s, u in a.sectors.items():
        v = b.sectors[s]
        assert (u.excluded, u.n_bins) == (v.excluded, v.n_bins)
        assert abs(u.beta - v.beta) <= 1e-11


def test_each_tooth_lands_in_its_own_comb():
    t = np.arange(100.0, 110.0, CADENCE)
    h, half = 0.35, 0.1
    masks = a0_v4.comb_masks(t, {1: (100.0, 15)}, h, half)
    assert masks.shape == (a0_v4.J, t.size)
    assert not np.any(masks.sum(axis=0) > 1), "the teeth of different combs never overlap"
    for g in range(14):
        centre = 100.0 + h + 2.0 * g * h
        at = int(np.argmin(np.abs(t - centre)))
        assert masks[g % a0_v4.J, at]
        for j in range(a0_v4.J):
            if j != g % a0_v4.J:
                assert not masks[j, at]


def test_a_window_is_measured_under_its_own_comb():
    lc = curve(16, days=14.0, gap=(20.0, 21.0))
    seen = []

    def preprocess(extra):
        seen.append(extra.copy())
        return lc

    class Ev:
        baseline_gap_durations = 1.0
        baseline_outer_durations = 3.0
        min_coverage = 0.5

    measure = a0_v4.comb_measure(preprocess, lc.time, lc, 0.1, 0.1, Ev, CADENCE)
    h = a0.half_width(0.1, 3.0)
    centre = float(lc.time.min() + h + 2.0 * 5 * h)
    assert measure(centre) is not None
    assert len(seen) == 1
    assert seen[0][int(np.argmin(np.abs(lc.time - centre)))], "the window's own cadences are masked"
    measure(centre)
    assert len(seen) == 1, "a comb is preprocessed once"
