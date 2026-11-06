"""v0.5.1 A0: the empirical error of an event measurement (docs/plans/v0.5.1-acceptance.md, A0).
Mechanism cases with known truth on development seeds; the per-stratum acceptance rows (A0.1 to
A0.7, 400 curves per stratum on acceptance seeds) run in the acceptance scripts on frozen code."""

from __future__ import annotations

import math

import numpy as np
import pytest

from refute.packs.tess import a0
from refute.packs.tess import synthetic as syn

CADENCE = 2.0 / 1440.0
DUR = 0.1
GAP, OUTER, MINCOV = 0.25, 1.5, 0.5


def _sector(seed, tau=None, sigma=1e-3, red=0.0, start=2000.0):
    rng = np.random.default_rng(seed)
    t = syn.sector_times(start)
    flux = 1.0 + sigma * rng.standard_normal(t.size)
    if red > 0:
        flux += syn.ar1_series(t, red, tau, np.random.default_rng([seed, 1]))
    return t, flux


def _windows(t, flux, period=3.1, t0=2000.7):
    measure = a0.box_measure(t, flux, DUR, GAP, OUTER, MINCOV, CADENCE)
    sector = np.ones(t.size, dtype=int)
    return a0.pseudo_windows(t, sector, period, t0, DUR, OUTER, MINCOV, measure)


# --- the windows (A0.3) --------------------------------------------------------------------


def test_windows_are_disjoint_and_never_touch_an_event_or_phase_half():
    t, flux = _sector(1)
    period, t0 = 3.1, 2000.7
    ws = _windows(t, flux, period, t0)
    h = a0.half_width(DUR, OUTER)
    centres = sorted(w.centre for w in ws)
    assert all(b - a >= 2 * h - 1e-9 for a, b in zip(centres, centres[1:], strict=False))
    for c in centres:
        phase = (c - t0) / period
        assert abs(phase - round(phase)) * period >= 2 * h
        assert abs((phase - 0.5) - round(phase - 0.5)) * period >= 2 * h
    assert len(ws) > 30 and {w.segment for w in ws} == {0, 1}


def test_the_grid_is_deterministic():
    t, flux = _sector(2)
    assert _windows(t, flux) == _windows(t, flux)


# --- the effective count and the corrected variance -----------------------------------------


def test_the_effective_count_formula():
    assert a0.effective_count(100, [0.0] * 5) == 100.0
    assert a0.effective_count(100, [0.5, None, -0.3]) == pytest.approx(100 / (1 + 2 * 0.99 * 0.5))
    assert a0.effective_count(1, [0.9]) == 1.0


def test_white_noise_windows_give_the_true_scatter():
    errs, truths = [], []
    for seed in range(20):
        t, flux = _sector(10 + seed)
        ws = _windows(t, flux)
        sigma, info = a0.stratum_error(ws, 1, "full")
        assert sigma is not None and info["n_eff"] >= 10
        errs.append(sigma)
        n_in, n_base = DUR / CADENCE, 2 * (OUTER - GAP) * DUR / CADENCE
        truths.append(1e-3 * math.sqrt(1 / n_in + 1 / n_base))
    assert np.median(np.asarray(errs) / np.asarray(truths)) == pytest.approx(1.0, abs=0.12)


def test_correlated_windows_raise_the_error_through_the_effective_count():
    raised = 0
    for seed in range(10):
        t, flux = _sector(40 + seed, tau=0.5, red=1e-3)
        ws = _windows(t, flux)
        sigma, info = a0.stratum_error(ws, 1, "full")
        if sigma is None:
            continue
        values = [w.value for w in ws if w.stratum == "full"]
        raised += sigma > float(np.std(values, ddof=1))
        assert info["n_eff"] <= info["n"]
    assert raised >= 7


def test_few_windows_give_no_empirical_error():
    t, flux = _sector(3)
    ws = _windows(t, flux)[:5]
    sigma, info = a0.stratum_error(ws, 1, "full")
    assert sigma is None and info["n"] == 5


# --- the group rule ------------------------------------------------------------------------


def _meta(c, seg=0, st="full"):
    return a0.EventMeta(c, 1, seg, st)


def test_distant_events_are_independent_and_near_ones_need_a_correlation():
    t, flux = _sector(4)
    ws = _windows(t, flux)
    h = a0.half_width(DUR, OUTER)
    far = [_meta(2001.0), _meta(2001.0 + 20 * h)]
    v = a0.group_variance([0.5, 0.5], [1.0, 1.0], far, ws, h, {})
    assert v == pytest.approx(0.5)
    # a partial-coverage event two steps from a full one: r_{2,full,partial} needs 20 pairs
    near = [_meta(2001.0), _meta(2001.0 + 4 * h, st="partial")]
    assert a0.group_variance([0.5, 0.5], [1.0, 1.0], near, ws, h, {}) is None


def test_a_covariance_that_is_not_positive_semidefinite_has_no_error():
    # a fabricated window set whose lag-1 correlation is -1 and lag-2 +1 for full pairs
    values = [(-1) ** i for i in range(60)]
    ws = [a0.Window(1, 0, i, 2000.0 + i, float(v), 1.0, "full") for i, v in enumerate(values)]
    h = 0.5
    events = [_meta(2000.0), _meta(2001.0), _meta(2002.0)]
    sig = [1.0, 1.0, 1.0]
    # r_1 = -1 and r_2 = +1: the 3 x 3 matrix [[1,-1,1],[-1,1,-1],[1,-1,1]] is PSD (rank one)
    assert a0.group_variance([1, 1, 1], sig, events, ws, h, {}) is not None
    # weights that cancel give a zero variance: no calibrated error
    assert a0.group_variance([1, 1, 0], sig, events[:3], ws, h, {}) is None


def test_the_shortcut_needs_three_segments():
    t, flux = _sector(5)
    ws = _windows(t, flux)
    assert a0.shortcut(ws, 1, seed=1) is False


# --- Codex's end-of-round review of round 3 ----------------------------------------------------


def test_a_short_series_keeps_its_dependence_in_the_effective_count():
    # 12 windows of a slow ramp: fewer than 20 lag pairs, but a clear positive correlation; n_eff
    # uses every available pair, so the stratum has no calibrated error (n_eff < 10)
    ws = [a0.Window(1, 0, i, 2000.0 + i, 0.1 * i, 1.0, "full") for i in range(12)]
    sigma, info = a0.stratum_error(ws, 1, "full")
    assert info["r_k"][0] is not None and info["r_k"][0] > 0.5
    assert info["n_eff"] < 10 and sigma is None


def test_the_shortcut_needs_every_bootstrap_replicate(monkeypatch):
    rng = np.random.default_rng(7)
    ws = [
        a0.Window(1, seg, i, 2000.0 + 10 * seg + 0.2 * i, float(rng.standard_normal()), 1.0, "full")
        for seg in range(3)
        for i in range(40)
    ]
    assert a0.shortcut(ws, 1, seed=3) is True
    original = a0.lag_correlation
    state = {"missed": False}

    def one_missing(windows, k, a, b, min_pairs=a0.MIN_PAIRS):
        if a is None and not state["missed"]:
            state["missed"] = True
            return None, 0
        return original(windows, k, a, b, min_pairs)

    monkeypatch.setattr(a0, "lag_correlation", one_missing)
    assert a0.shortcut(ws, 1, seed=3) is False


def test_the_matched_estimator_is_weighted_least_squares():
    rng = np.random.default_rng(11)
    t = np.arange(0.0, 1.0, CADENCE)
    err = np.where(np.arange(t.size) % 3 == 0, 3e-3, 1e-3)
    flux = 1.0 - 2e-3 * (np.abs(t - 0.5) < 0.05) + err * rng.standard_normal(t.size)

    def shape(dt):
        return (np.abs(dt) < 0.05).astype(float)

    _, core = a0.matched_measure(t, flux, err, shape, 0.1, 0.1 / CADENCE, 0.5)
    amp, cov, info = core(0.5)
    sel = np.abs(t - 0.5) <= 0.1
    w, s = 1.0 / err[sel] ** 2, shape(t[sel] - 0.5)
    assert info == pytest.approx(float(np.sum(w * s * s)))
    assert amp == pytest.approx(float(np.sum(w * s * (1.0 - flux[sel])) / np.sum(w * s * s)))
    assert cov > 0.9
