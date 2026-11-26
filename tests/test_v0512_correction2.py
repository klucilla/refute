"""Correction 2 revision 1's suite (v0.5.12; docs/plans/v0.5.12-spec-correction-2-r1.md, adopted
at SHA-256 c24e7fd936929d713f53755b53233cc453e3e65a043f887b2f9e1511869873db), its section 7,
written before the ``src/`` change. Exploratory, ``method_status: not_validated``.

- **The independent oracle** is ``tests/v0512_oracles.py`` (it never imports ``src/``).
- **Closed forms against the oracle** (section 5): the equal-sigma white and red forms; Codex's
  example (25/18 against the legacy 1); an admissible dominant-bin witness for C; an admissible
  witness with weight ratios near 1e30 (the rounding of Q0, blind review N10); the effective
  epoch count.
- **Strict expected failures against the approval code**, each with its ID and reason, all
  ``xfail(strict=True, raises=AssertionError)``; the ``src/`` change removes them:
  - ``test_p95_witness_passes_under_the_correction`` and
    ``test_b6_witness_passes_under_the_correction``: the approval code fails them;
  - ``test_t2_corrected_sigma_odd_is_smaller``: the corrected sigma_odd is smaller;
  - ``test_src_f1_matches_the_oracle[*]``: the approval code's F1 is not the corrected one.
- **Kept, passing before and after:** the unequal-depth binary test and the report-only tests of
  ``tests/test_v0511_screen.py``; the legacy MES noise (``_noise``), which F2 and U1 keep.
"""

from __future__ import annotations

import importlib
import math
import sys
from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v0512_fixtures as fx  # noqa: E402
import v0512_oracles as oc  # noqa: E402
from screen_reference import f1_reference  # noqa: E402

SIGMA0 = 6e-4
XFAIL = pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="the approval code's F1 is the frozen estimator; correction 2 revision 1 changes it "
    "(removed by the src/ change)",
)


def screen():
    return importlib.import_module("refute.packs.tess.screen_d5")


def family(name: str, seed: int):
    """M1's families on the step-2 geometry: a 0.002 box, sigma0 = 6e-4, one noise draw."""
    g = fx.build({"model": "box", "depth": 0.002, "sigma": SIGMA0, "seed": seed})
    t = g["t"]
    k = fx.epochs(t, fx.P, fx.T0)
    intr = fx.in_transit(t, fx.P, fx.T0, fx.T)
    odd = np.mod(k, 2) == 1
    base = fx.phase_distance(t, fx.P, fx.T0) > fx.T
    box = np.where(intr, 1 - 0.002, 1.0)
    z = (g["f"] - box) / SIGMA0
    s = np.full(t.size, SIGMA0)
    if name == "P9.5":
        s[odd] = 9.5 * SIGMA0
    elif name == "B6":
        s[np.where(base)[0][0]] = SIGMA0 / 1e6
    elif name == "T2":
        s[np.where(intr & odd)[0][0]] = SIGMA0 / 100
    elif name == "binary":
        box = box - np.where(intr & odd, 0.002, 0.0)
    return t, box + s * z, s


def all_baseline(bin_fluxes, bin_sigmas):
    """Points that are all baseline (P huge, t0 far): one bin of width 1 per list entry."""
    t, f, s = [], [], []
    for b, (fl, sg) in enumerate(zip(bin_fluxes, bin_sigmas, strict=True)):
        n = len(fl)
        assert n <= 8  # exact binary times, so that no point rounds into another bin
        t.extend(b + (np.arange(n) + 1) / 8)
        f.extend(fl)
        s.extend([sg] * n if np.isscalar(sg) else sg)
    t, f, s = (np.asarray(x, dtype=float) for x in (t, f, s))
    return t, f, 1.0 / s**2, 1e6, -1e5, 1.0


# --- closed forms against the oracle (section 5) ---------------------------------------------


def test_equal_sigma_white_form():
    rng = np.random.default_rng([1, 5122])
    fl = [list(1.0 + 0.01 * rng.standard_normal(8)) for _ in range(6)]
    t, f, w, p, t0, d = all_baseline(fl, [0.01] * 6)
    s2, _, _, _ = oc.corrected_noise(t, f, w, p, t0, d)
    assert math.isclose(s2 * 0.01**2, float(np.var(f, ddof=1)), rel_tol=1e-9)


def test_equal_sigma_equal_counts_red_form():
    rng = np.random.default_rng([2, 5122])
    offsets = 0.05 * rng.standard_normal(7)
    fl = [list(1.0 + o + 0.01 * rng.standard_normal(5)) for o in offsets]
    t, f, w, p, t0, d = all_baseline(fl, [0.01] * 7)
    _, sig_r2, _, _ = oc.corrected_noise(t, f, w, p, t0, d)
    mu = np.array([np.mean(b) for b in fl])
    closed = max(0.0, float(np.var(mu, ddof=1)) - float(np.var(f, ddof=1)) / 5)
    assert closed > 0
    assert math.isclose(sig_r2, closed, rel_tol=1e-9)


def test_codex_example_corrected_25_18_and_legacy_1():
    c = 1e-3
    fl = [[c * m, c * m] for m in (-2, -1, 0, 1, 2)]
    t, f, w, p, t0, d = all_baseline(fl, [0.01] * 5)
    _, sig_r2, _, _ = oc.corrected_noise(t, f, w, p, t0, d)
    assert math.isclose(sig_r2, 25 / 18 * c**2, rel_tol=1e-9)
    # the legacy noise, which F2 and U1 keep: red variance c**2
    _, sigma_r, _ = screen()._noise(t, f, w, p, t0, d)
    assert math.isclose(sigma_r**2, c**2, rel_tol=1e-9)


def test_dominant_bin_c_stays_positive():
    wk = np.array([6e24, 2e-6, 2e-6])
    big_b = float(wk.sum())
    assert float(wk.sum() - (wk**2).sum() / wk.sum()) == 0.0  # the subtraction loses C
    prefix = np.concatenate(([0.0], np.cumsum(wk)[:-1]))
    c = float(2.0 * np.sum(wk * (prefix / big_b)))
    assert math.isclose(c, 8e-6, rel_tol=1e-9)
    # admissible: six points at sigma 1e-12 (weight 1e24 each) and two bins of two at 1e3
    fl = [[1.0 + 1e-13 * j for j in range(6)], [1.0, 1.5], [0.5, 1.0]]
    t, f, w, p, t0, d = all_baseline(fl, [1e-12, 1e3, 1e3])
    out = oc.corrected_noise(t, f, w, p, t0, d)
    assert out is not None
    assert math.isfinite(out[1]) and out[1] >= 0


def test_extreme_weight_ratio_rounding_of_q0():
    # weight ratios near 1e30; the reported sigma (1e-12 and 1e3) greatly overestimate a
    # scatter of 1e-15
    fl = [
        [1.0, 1.0 + 1e-15, 1.0 - 1e-15, 1.0],
        [1.0 + 2e-15, 1.0, 1.0, 1.0 - 2e-15],
        [1.0, 1.0 - 1e-15, 1.0, 1.0 + 1e-15],
    ]
    t, f, w, p, t0, d = all_baseline(fl, [1e-12, 1e3, 1e-12])
    out = oc.corrected_noise(t, f, w, p, t0, d)
    assert out is not None and math.isfinite(out[0]) and out[0] > 0
    mus, wks = [], []
    for b in range(3):
        sel = (t >= b) & (t < b + 1)
        wks.append(float(np.sum(w[sel])))
        mus.append(float(np.sum(w[sel] * f[sel]) / np.sum(w[sel])))
    mu, wk = np.array(mus), np.array(wks)
    mu_bar = float(np.sum(wk * mu) / wk.sum())
    q0 = float(np.sum(wk * (mu - mu_bar) ** 2))
    fw, fm = [Fraction(x) for x in wks], [Fraction(x) for x in mus]
    fbar = sum(a * b for a, b in zip(fw, fm, strict=True)) / sum(fw)
    exact = float(sum(a * (b - fbar) ** 2 for a, b in zip(fw, fm, strict=True)))
    bound = 3 * 16 * max(wks) * (2.3e-16 * max(abs(x) for x in mus)) ** 2
    assert abs(q0 - exact) <= max(1e-12 * abs(exact), bound)


def _equal_epochs(sigma_odd_epoch=None):
    """Fourteen epochs with fifteen in-transit cadences each and a common baseline."""
    p, t0, d = fx.P, fx.T0, fx.T
    t = []
    for k in range(14):
        c = t0 + k * p
        t.extend(c + (np.arange(15) - 7) * d / 16)
        t.extend(c + 1.2 * d + np.arange(40) * (p - 2.4 * d) / 40)
    t = np.sort(np.asarray(t))
    rng = np.random.default_rng([3, 5122])
    s = np.full(t.size, 1e-4)
    if sigma_odd_epoch is not None:
        sel = np.abs(t - (t0 + p)) <= d / 2
        s[sel] = sigma_odd_epoch
    f = 1.0 + s * rng.standard_normal(t.size)
    return t, f, s, p, t0, d


def test_effective_epoch_count_equals_n_with_equal_epoch_weights():
    m = oc.f1_corrected(*_equal_epochs())["metrics"]
    assert m["epochs_odd"] == 7 and m["epochs_even"] == 7
    assert math.isclose(m["epochs_eff_odd"], 7, rel_tol=1e-12)
    assert math.isclose(m["epochs_eff_even"], 7, rel_tol=1e-12)


def test_effective_epoch_count_is_smaller_with_unequal_epoch_weights():
    m = oc.f1_corrected(*_equal_epochs(sigma_odd_epoch=1e-3))["metrics"]
    assert m["epochs_odd"] == 7
    assert m["epochs_eff_odd"] < 7
    assert math.isclose(m["epochs_eff_even"], 7, rel_tol=1e-12)


def test_the_oracle_witnesses_are_what_the_suite_needs():
    for name in ("P9.5", "B6"):
        t, f, s = family(name, 1)
        assert f1_reference(t, f, s, fx.P, fx.T0, fx.T).state == "fail"
        assert oc.f1_corrected(t, f, s, fx.P, fx.T0, fx.T)["state"] == "pass"


# --- strict expected failures against the approval code --------------------------------------


@XFAIL
def test_p95_witness_passes_under_the_correction():
    t, f, s = family("P9.5", 1)
    assert screen().f1_box(t, f, s, fx.P, fx.T0, fx.T)["state"] == "pass"


@XFAIL
def test_b6_witness_passes_under_the_correction():
    t, f, s = family("B6", 1)
    assert screen().f1_box(t, f, s, fx.P, fx.T0, fx.T)["state"] == "pass"


@XFAIL
def test_t2_corrected_sigma_odd_is_smaller():
    t, f, s = family("T2", 1)
    frozen = f1_reference(t, f, s, fx.P, fx.T0, fx.T).metrics["sigma_odd"]
    got = screen().f1_box(t, f, s, fx.P, fx.T0, fx.T)["metrics"]["sigma_odd"]
    assert got < 0.5 * frozen


KEYS = ("oe_box", "sigma_odd", "sigma_even", "s2", "sigma_r", "epochs_eff_odd", "epochs_eff_even")


@XFAIL
@pytest.mark.parametrize("name", ["planet", "binary", "P9.5", "B6", "T2"])
def test_src_f1_matches_the_oracle(name):
    t, f, s = family("U" if name == "planet" else name, 1)
    got = screen().f1_box(t, f, s, fx.P, fx.T0, fx.T)
    want = oc.f1_corrected(t, f, s, fx.P, fx.T0, fx.T)
    assert got["state"] == want["state"]
    for key in KEYS:
        a, b = got["metrics"].get(key), want["metrics"][key]
        assert a is not None and math.isclose(a, b, rel_tol=1e-9), (key, a, b)
