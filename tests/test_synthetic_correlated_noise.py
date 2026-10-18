"""The correlated-noise mode of the synthetic generator: cases G1 to G5 of
docs/validation/v0.2.1/reopen/correlated-noise-acceptance.md."""

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

from refute.packs.tess import synthetic
from refute.packs.tess.synthetic import BLEND_SCENE, PLANET, crowding, scenario_data, scene_aperture

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "validation" / "v0.2.1" / "reopen" / "correlated"
RED_PPM = 600.0
TAU_DAYS = 1.0 / 24.0
CADENCE_DAYS = 120.0 / 86400.0


def _reference_module():
    spec = importlib.util.spec_from_file_location(
        "white_reference", REFERENCE_DIR / "white_reference.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


REFERENCE = json.loads((REFERENCE_DIR / "white-reference.json").read_text(encoding="utf-8"))


def _expected_ar1(lc, seed):
    """The AR(1) series of the definition, by an implementation of this test: one stream
    ``default_rng([seed, 1])``; per sector, in the order of the light curve, a stationary
    start and the recurrence with the real time differences."""
    rng = np.random.default_rng([seed, 1])
    a = RED_PPM * 1e-6
    out = np.empty(len(lc))
    order = list(dict.fromkeys(int(s) for s in lc.sector))
    for sector in order:
        idx = np.flatnonzero(lc.sector == sector)
        t = lc.time[idx]
        n = t.size
        x = np.empty(n)
        x[0] = rng.normal(0.0, a)
        innov = rng.normal(0.0, 1.0, n)
        phi = np.exp(-np.diff(t) / TAU_DAYS)
        scale = a * np.sqrt(1.0 - phi**2)
        for i in range(1, n):
            x[i] = phi[i - 1] * x[i - 1] + scale[i - 1] * innov[i]
        out[idx] = x
    return out


# --- G1. The white mode is the old generator ---------------------------------------------


@pytest.mark.parametrize("key", sorted(REFERENCE["digests"]))
def test_g1_the_default_mode_equals_the_old_generator(key):
    digest = _reference_module().digest
    name, seed = key.split("|")
    assert digest(scenario_data(name, int(seed))) == REFERENCE["digests"][key], key


def test_g1_the_reference_covers_every_scenario_and_seed():
    names = {k.split("|")[0] for k in REFERENCE["digests"]}
    expected = {*synthetic.SCENARIOS, "fp_variability_dominates", "variability_train_only"}
    assert names == expected
    assert len(REFERENCE["digests"]) == len(expected) * 3


# --- G2. The correlated mode adds exactly the AR(1) series --------------------------------


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_g2_correlated_minus_white_is_the_ar1_series(seed):
    white = scenario_data("planet", seed)
    red = scenario_data("planet", seed, noise="correlated")
    assert np.array_equal(red.lc.time, white.lc.time)
    assert np.array_equal(red.lc.sector, white.lc.sector)
    diff = red.lc.flux - white.lc.flux
    np.testing.assert_allclose(diff, _expected_ar1(white.lc, seed), rtol=0, atol=1e-12)


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_g2b_the_series_has_the_declared_amplitude_and_correlation(seed):
    white = scenario_data("planet", seed)
    red = scenario_data("planet", seed, noise="correlated")
    diff = red.lc.flux - white.lc.flux
    assert abs(np.std(diff) / (RED_PPM * 1e-6) - 1.0) < 0.10
    dt = np.diff(white.lc.time)
    same_orbit = np.abs(dt - CADENCE_DAYS) < 1e-6
    lag1 = np.corrcoef(diff[:-1][same_orbit], diff[1:][same_orbit])[0, 1]
    assert abs(lag1 - np.exp(-CADENCE_DAYS / TAU_DAYS)) < 0.02


def test_g2b_the_series_differ_between_seeds():
    diffs = [
        scenario_data("planet", s, noise="correlated").lc.flux - scenario_data("planet", s).lc.flux
        for s in (0, 1)
    ]
    assert not np.allclose(diffs[0], diffs[1])


# --- G3. The pipeline is not told about the red component --------------------------------


def test_g3_flux_errors_are_the_white_sigma_in_both_modes():
    white = scenario_data("planet", 0)
    red = scenario_data("planet", 0, noise="correlated")
    assert np.array_equal(red.lc.flux_err, white.lc.flux_err)


# --- G4. A correlated blend stays coherent with its pixels --------------------------------


def test_g4_a_correlated_blend_light_curve_is_its_aperture_photometry():
    data = scenario_data("blend", 0, noise="correlated")
    aperture = scene_aperture(BLEND_SCENE)
    c = crowding(BLEND_SCENE)
    for px in data.aux.pixels:
        sel = data.lc.sector == px.sector
        ap = px.flux[:, aperture].sum(axis=1)
        ap = ap / np.median(ap)
        np.testing.assert_allclose(data.lc.flux[sel], (ap - (1.0 - c)) / c, rtol=0, atol=1e-12)
    white = scenario_data("blend", 0)
    assert not np.allclose(data.lc.flux, white.lc.flux)


# --- G5. No second generator in the white mode -------------------------------------------


def _count_generators(monkeypatch, **kwargs):
    calls = []
    real = np.random.default_rng

    def counting(*args, **kw):
        calls.append(args)
        return real(*args, **kw)

    monkeypatch.setattr(np.random, "default_rng", counting)
    synthetic.make_lightcurve(PLANET, seed=5, **kwargs)
    return calls


def test_g5_the_white_mode_creates_one_generator(monkeypatch):
    assert len(_count_generators(monkeypatch)) == 1


def test_g5_the_correlated_mode_creates_a_second_generator(monkeypatch):
    calls = _count_generators(monkeypatch, red_noise_ppm=RED_PPM)
    assert len(calls) == 2
    assert list(calls[1][0]) == [5, 1]


def test_an_unknown_noise_mode_is_refused():
    with pytest.raises(ValueError, match="noise"):
        scenario_data("planet", 0, noise="pink")
