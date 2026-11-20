"""v0.5.5: C1 version 2 (``docs/validation/v0.5.5/generator_v2.py``): the true star drawn from
the catalog's declared 5 % (no artificial truncation), its own stream, C1 unchanged outside the
durations and what derives from them, and ``src/``'s function restored after every call (an error
inside ``generate`` included). Synthetic data only; no network."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parents[2] / "docs/validation/v0.5.5"
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import generator_v2 as g2  # noqa: E402

from refute.packs.tess.calib05 import c1  # noqa: E402


def test_true_star_is_deterministic_untruncated_and_spread():
    stars = [g2.true_star(s) for s in range(4000)]
    assert g2.true_star(7) == g2.true_star(7)
    r = np.array([x[0] for x in stars])
    m = np.array([x[1] for x in stars])
    assert r.min() > g2.PHYSICAL_MIN and m.min() > g2.PHYSICAL_MIN
    assert abs(r.mean() - 1.0) < 0.004 and abs(r.std() - 0.05) < 0.003
    assert abs(m.mean() - 1.0) < 0.004 and abs(m.std() - 0.05) < 0.003
    # no artificial 3-sigma truncation: about 0.27 % of 4,000 draws per coordinate lie beyond
    assert np.sum(np.abs(r - 1.0) > 0.15) + np.sum(np.abs(m - 1.0) > 0.15) >= 3


def test_effective_radius_and_sigma():
    assert g2.effective_radius(1.0, 1.0) == pytest.approx(1.0)
    assert g2.effective_radius(1.1, 0.9) == pytest.approx(1.1 / 0.9 ** (1 / 3))
    assert g2.effective_sigma() == pytest.approx(math.sqrt(0.05**2 + 0.05**2 / 9))


def test_the_star_patch_scales_kepler_and_is_restored():
    original = c1.a_over_rstar
    with g2._star(1.1, 0.9):
        assert c1.a_over_rstar(3.0) == pytest.approx(original(3.0) * 0.9 ** (1 / 3) / 1.1)
    assert c1.a_over_rstar is original
    with pytest.raises(RuntimeError), g2._star(1.2, 1.0):
        raise RuntimeError("inside")
    assert c1.a_over_rstar is original


def test_an_error_inside_generate_restores_the_function(monkeypatch):
    original = c1.a_over_rstar

    def failing(family, seed):
        assert c1.a_over_rstar is not original  # the drawn star is in place during the call
        raise c1.GenerationFailedError("inside generate")

    monkeypatch.setattr(c1, "generate", failing)
    with pytest.raises(c1.GenerationFailedError):
        g2.generate("P", 11)
    assert c1.a_over_rstar is original


def test_the_oracles_planet_model_uses_the_catalog_star_outside_generate():
    sys.path.insert(
        0, str(Path(__file__).resolve().parents[2] / "docs/validation/v0.5.1/feasibility")
    )
    import forecast

    t = np.linspace(2000.0, 2010.0, 5000)
    before = forecast.planet_model(t, 3.0, 2001.0, 1e-3, 0.3, 1.0)
    g2.generate("P", c1.development_seed("P", 1))
    after = forecast.planet_model(t, 3.0, 2001.0, 1e-3, 0.3, 1.0)
    np.testing.assert_array_equal(before, after)


def test_version_2_changes_the_durations_and_what_derives_from_them():
    seed = c1.development_seed("P", 0)
    data1, truth1 = c1.generate("P", seed)
    data2, truth2 = g2.generate("P", seed)
    assert c1.a_over_rstar is not None and "true_star" in truth2 and "true_star" not in truth1
    for key in ("period_days", "t0_btjd", "impact", "target_snr", "sigma_white_ppm", "correlated"):
        assert truth1[key] == truth2[key]
    star = truth2["true_star"]
    assert (star["radius_rsun"], star["mass_msun"]) == g2.true_star(seed)
    ratio = truth2["duration_days"] / truth1["duration_days"]
    assert ratio != pytest.approx(1.0, abs=1e-9)  # the drawn star changed the duration
    np.testing.assert_array_equal(data1.lc.time, data2.lc.time)
    assert data2.star.radius_rsun == 1.0 and data2.star.radius_err_rsun == 0.05  # the catalog


def test_version_2_at_the_catalog_centre_equals_version_1(monkeypatch):
    monkeypatch.setattr(g2, "true_star", lambda seed: (1.0, 1.0))
    seed = c1.development_seed("EB1", 3)
    data1, truth1 = c1.generate("EB1", seed)
    data2, truth2 = g2.generate("EB1", seed)
    np.testing.assert_array_equal(data1.lc.flux, data2.lc.flux)
    assert truth1["duration_days"] == truth2["duration_days"]
