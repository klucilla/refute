"""Synthetic tests of v0.5.3 stage B's candidate battery version 5 (``battery_b1.py``, outside
``src/``; ``docs/plans/v0.5.3-stageB1-design.md``). No network; known answers only."""

from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
PATH = ROOT / "docs/validation/v0.5.3/stageB/battery_b1.py"


@pytest.fixture(scope="module")
def b1():
    spec = importlib.util.spec_from_file_location("battery_b1_under_test", PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    yield module
    module.deactivate()


# --- E1 --------------------------------------------------------------------------------------


def _metas(a0, centres, sector=1, segment=0, stratum="full"):
    return [a0.EventMeta(float(c), sector, segment, stratum) for c in centres]


def test_e1_keeps_version_4_when_finite(b1):
    from refute.packs.tess import a0

    # two events in different sectors: no in-window pair, version 4's variance is finite
    events = _metas(a0, [10.0], sector=1) + _metas(a0, [10.0], sector=2)
    v4 = a0.group_variance([0.5, -0.5], [1.0, 2.0], events, [], 0.1, {})
    assert v4 == pytest.approx(0.25 + 1.0)
    assert b1.group_variance([0.5, -0.5], [1.0, 2.0], events, [], 0.1, {}) == v4


def test_e1_bounds_codex_case(b1):
    from refute.packs.tess import a0

    # two events one grid lag apart, no pseudo-windows: version 4 refuses (r undefined)
    h = 0.1
    events = _metas(a0, [10.0, 10.0 + 2 * h])
    assert a0.group_variance([1.0, -1.0], [1.0, 1.0], events, [], h, {}) is None
    b1.reset_counts()
    var = b1.group_variance([1.0, -1.0], [1.0, 1.0], events, [], h, {})
    # the true variance with r = -0.5 is 3; the completion gives the bound 4
    assert var == pytest.approx(4.0)
    assert b1.counts()["e1.completion_missing"] == 1


# --- E2 --------------------------------------------------------------------------------------


def test_e2_gls_reduces_to_group_means_for_equal_white_errors(b1):
    d = np.array([1.0, 2.0, 1.5, 2.5, 0.5])
    s = np.array([1, -1, 1, -1, 1], dtype=float)
    delta, var = b1.gls_contrast(d, s, np.eye(5) * 4.0)
    assert delta == pytest.approx(d[s > 0].mean() - d[s < 0].mean())
    assert var == pytest.approx(4.0 * (1 / 3 + 1 / 2))


def test_e2_refuses_ill_conditioned_covariance(b1):
    cov = np.array([[1.0, 1.0 - 1e-12], [1.0 - 1e-12, 1.0]])
    assert b1.gls_contrast(np.array([1.0, 2.0]), np.array([1.0, -1.0]), cov) is None


# --- E3 --------------------------------------------------------------------------------------


def _dense(t, phi, sa2, sw2, delta):
    lag = np.abs(t[:, None] - t[None, :]) / delta
    return sw2 * np.eye(t.size) + sa2 * phi**lag


def test_e3_whitening_and_adjoint_match_dense_cholesky(b1):
    delta = 0.01
    t = np.concatenate([np.arange(0, 40) * delta, (np.arange(55, 90)) * delta, [1.2, 1.23]])
    phi, sa2, sw2 = 0.8, 2.0, 0.5
    sigma = _dense(t, phi, sa2, sw2, delta)
    chol = np.linalg.cholesky(sigma)
    rng = np.random.default_rng(1)
    z = rng.normal(size=(t.size, 3))
    out, gains, factors, roots = b1.whiten(t, z, phi, sa2, sw2, delta)
    np.testing.assert_allclose(out, np.linalg.solve(chol, z), rtol=1e-9, atol=1e-12)
    g = rng.normal(size=t.size)
    adj = b1.whiten_adjoint(g, gains, factors, roots)
    np.testing.assert_allclose(adj, np.linalg.solve(chol.T, g), rtol=1e-9, atol=1e-12)
    u = rng.normal(size=t.size)
    k = phi ** (np.abs(t[:, None] - t[None, :]) / delta)
    assert b1.quad_k(t, u, phi, delta) == pytest.approx(float(u @ k @ u), rel=1e-10)


def test_e3_box_after_matches_dense_gls(b1):
    from refute.packs.tess.battery_v51 import _design

    rng = np.random.default_rng(7)
    delta = 2.0 / 1440.0
    parts, sectors = [], []
    for s, start in ((1, 0.0), (2, 30.0)):
        tt = start + np.arange(1500) * delta
        tt = np.delete(tt, np.arange(600, 700))  # an observational gap
        parts.append(tt)
        sectors.append(np.full(tt.size, s))
    time, sector = np.concatenate(parts), np.concatenate(sectors)
    phi_true, sa2_true, sw2_true = 0.9, 4e-8, 1e-8
    flux = np.empty(time.size)
    for s in (1, 2):
        sel = sector == s
        cov = _dense(time[sel], phi_true, sa2_true, sw2_true, delta)
        flux[sel] = 1.0 + np.linalg.cholesky(cov) @ rng.normal(size=sel.sum())
    flux += 1e-4 * np.sin(2 * np.pi * time / 0.7)
    err = np.full(time.size, 1e-4)
    cand = SimpleNamespace(period=0.9, t0=0.31, duration=0.08)
    dt = np.abs(np.mod(time - cand.t0 + 0.5 * cand.period, cand.period) - 0.5 * cand.period)
    kept = dt > cand.duration / 2 + 0.5 * cand.duration
    periods = [0.7]
    x_all = _design(time, sector, periods)
    x_kept = _design(time[kept], sector[kept], periods)
    b1._SINUSOID_SECTOR["sector"] = sector
    b1.reset_counts()
    try:
        box, sig = b1.box_after_model(time, flux, err, kept, x_all, x_kept, cand, 1.0)
    finally:
        b1._SINUSOID_SECTOR["sector"] = None
    assert b1.counts().get("e3.gls") == 1
    # the dense computation with the same estimated parameters
    w = 1.0 / err[kept] ** 2
    coef_w = np.linalg.solve((x_kept.T * w) @ x_kept, (x_kept.T * w) @ flux[kept])
    resid = flux[kept] - x_kept @ coef_w
    big = np.zeros((time.size, time.size))
    for s in (1, 2):
        sel = np.nonzero(sector == s)[0]
        selk = sector[kept] == s
        m = b1.moments(time[kept][selk], resid[selk], b1._cadence(time[kept][selk]))
        phi, sa2, sw2 = b1.arma_parameters(m)
        big[np.ix_(sel, sel)] = _dense(time[sel], phi, sa2, sw2, b1._cadence(time[kept][selk]))
    sk = big[np.ix_(kept, kept)]
    sinv_x = np.linalg.solve(sk, x_kept)
    coef = np.linalg.solve(x_kept.T @ sinv_x, sinv_x.T @ flux[kept])
    inside = dt <= cand.duration / 2
    a = np.where(inside, -1.0 / inside.sum(), 1.0 / (~inside).sum())
    assert box == pytest.approx(float(a @ (flux - x_all @ coef)), rel=1e-6, abs=1e-12)
    h_kept = x_all @ np.linalg.solve(x_kept.T @ sinv_x, sinv_x.T)  # n_all x n_kept
    u = a.copy()
    u[kept] -= h_kept.T @ a
    assert sig == pytest.approx(math.sqrt(float(u @ big @ u)), rel=1e-6)


# --- E4 --------------------------------------------------------------------------------------


def _box(b1, time, flux):
    return b1.quadratic_box(time, flux, 0.1, 0.5, 2.0, 0.5, 2.0 / 1440.0)


@pytest.mark.parametrize("cut_left_band", [False, True])
def test_e4_confined_rise_has_unit_response(b1, cut_left_band):
    delta = 2.0 / 1440.0
    time = np.arange(0, 3.0, delta)
    centre = 1.5
    if cut_left_band:  # fewer than 3 cadences on the left band: the fallback operator
        d = time - centre
        time = time[~((d < -0.1) & (d > -0.2475))]  # at most 2 left-band cadences remain
    rng = np.random.default_rng(3)
    slow = 1e-3 * ((time - 1.4) ** 2) + 5e-4 * np.sin(2 * np.pi * time / 1.3)
    flux = slow + 1e-5 * rng.normal(size=time.size)
    rise = 2e-4 * (np.abs(time - centre) <= 0.05)
    b1.reset_counts()
    with_rise = _box(b1, time, flux + rise)(centre)
    without = _box(b1, time, flux)(centre)
    response = -(with_rise[0] - without[0]) / 2e-4
    assert response == pytest.approx(1.0, abs=0.01)
    key = "e4.window_fallback" if cut_left_band else "e4.window_quadratic"
    assert b1.counts()[key] == 2


def test_e4_removes_curvature_that_the_band_mean_keeps(b1):
    from refute.packs.tess import a0

    delta = 2.0 / 1440.0
    time = np.arange(0, 3.0, delta)
    flux = 1e-3 * ((time - 1.5) / 0.3) ** 2  # pure curvature, no noise
    q = _box(b1, time, flux)(1.5)[0]
    v4 = a0.box_measure(time, flux, 0.1, 0.5, 2.0, 0.5, delta)(1.5)[0]
    assert abs(q) < 1e-9 < abs(v4)


# --- activation --------------------------------------------------------------------------------


def test_activation_round_trip(b1):
    from refute.packs.tess import a0
    from refute.packs.tess import battery_v51_diff as v51d
    from refute.packs.tess import battery_v52 as v52

    originals = (a0.group_variance, v52.check_odd_even, v52.box_after_model, v52.check_sinusoid,
                 v51d.check_systematics)  # fmt: skip
    record = b1.activate(b1.Config())
    assert set(record["replaced"]) == set(b1._TARGETS)
    b1.check_active(b1.Config())
    assert a0.group_variance is b1.group_variance
    b1.deactivate()
    b1.check_active(None)
    assert (a0.group_variance, v52.check_odd_even, v52.box_after_model, v52.check_sinusoid,
            v51d.check_systematics) == originals  # fmt: skip
    b1.activate(b1.Config(e1=False, e3=False))
    assert a0.group_variance is originals[0] and v52.check_odd_even is b1.check_odd_even
    with pytest.raises(RuntimeError):
        b1.check_active(b1.Config())
    b1.deactivate()


def test_results_v4_then_v5_then_v4(b1):
    """Real calls through the patched module attributes: version 4's results before and after
    version 5 are identical, and version 5's differ where it acts."""
    from refute.packs.tess import a0

    h = 0.1
    events = _metas(a0, [10.0, 10.0 + 2 * h])
    args = ([1.0, -1.0], [1.0, 1.0], events, [], h, {})
    first = a0.group_variance(*args)
    b1.activate(b1.Config())
    try:
        middle = a0.group_variance(*args)
    finally:
        b1.deactivate()
    last = a0.group_variance(*args)
    assert first is None and last is None and middle == pytest.approx(4.0)
