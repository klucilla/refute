"""The ``R_min`` study's scenarios (map Amendment 19; Amendment 26, 5): the last year's alteration
``flux + (1 - s) D(t) trend(t)`` and the noiseless model, from a case's recorded final parameters.
On the self-test planets of the population harness (one per mechanism of the study and noise
model)."""

import importlib
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
POPULATION = ROOT / "docs" / "validation" / "v0.2.1" / "population"


@pytest.fixture(scope="module")
def study():
    sys.path.insert(0, str(POPULATION))
    return importlib.import_module("rmin_study")


@pytest.fixture(scope="module")
def built(study):
    pv2 = study.pv2
    out = {}
    for case in pv2.population_cases("selftest"):
        if case["class"] != "planet" or case["band"] != "near":
            continue
        blob, entry = pv2.build_case(case)
        meta, arrays = pv2.deserialize(blob)
        data = pv2.parts_to_data(meta, arrays)
        out[(case["mechanism"], case["noise"])] = (case, meta["parameters"], data.lc)
    assert {m for m, _ in out} == set(study.STUDY_MECHANISMS)  # precondition
    return out


@pytest.mark.parametrize("s", (0.0, 0.3))
def test_the_increment_is_the_expected_one_inside_the_last_years_transits(study, built, s):
    for key, (case, p, lc) in built.items():
        altered = study.alter_last_year(case, p, lc.time, lc.year, lc.flux, s)
        deficit, trend = study.deficit_and_trend(case, p, lc.time)
        last = lc.year == lc.year.max()
        inside = deficit > 0
        assert np.any(last & inside), key  # precondition: transits in the last year
        np.testing.assert_allclose(
            altered[last] - lc.flux[last],
            ((1.0 - s) * deficit * trend)[last],
            rtol=0,
            atol=1e-15,
            err_msg=str(key),
        )
        assert np.all(altered[~last] == lc.flux[~last]), key  # the other years untouched
        assert np.all(altered[last & ~inside] == lc.flux[last & ~inside]), key  # outside transits
        assert np.all(altered[last & inside] > lc.flux[last & inside]), key


def test_s_one_changes_nothing(study, built):
    for case, p, lc in built.values():
        assert np.array_equal(
            study.alter_last_year(case, p, lc.time, lc.year, lc.flux, 1.0), lc.flux
        )


def test_the_deficit_is_the_injected_transit(study, built):
    for key, (case, p, lc) in built.items():
        deficit, _ = study.deficit_and_trend(case, p, lc.time)
        assert deficit.max() == pytest.approx(p["depth"], rel=1e-9), key
        phase = (lc.time - p["t0"] + 0.5 * p["period"]) % p["period"] - 0.5 * p["period"]
        assert np.all(deficit[np.abs(phase) > 0.5 * p["duration"] + 1e-9] == 0.0), key


def test_the_constant_model_leaves_only_the_noise(study, built):
    pv2 = study.pv2
    for (mech, noise), (case, p, lc) in built.items():
        model = study.noiseless_model(case, p, lc.time, lc.year, 1.0)
        residual = lc.flux - model
        if noise == "white":
            assert np.std(residual) == pytest.approx(pv2.NOISE_PPM * 1e-6, rel=0.05), mech
        # nothing of the trend nor of the variability left: their own projections are noise-sized
        _, trend = study.deficit_and_trend(case, p, lc.time)
        shape = trend - trend.mean()
        coef = float(residual @ shape / (shape @ shape))
        assert abs(coef) < 0.05, (mech, noise, coef)


@pytest.mark.parametrize("s", (0.0, 0.3))
def test_the_altered_model_is_the_constant_one_altered(study, built, s):
    for key, (case, p, lc) in built.items():
        constant = study.noiseless_model(case, p, lc.time, lc.year, 1.0)
        altered = study.noiseless_model(case, p, lc.time, lc.year, s)
        expected = study.alter_last_year(case, p, lc.time, lc.year, constant, s)
        np.testing.assert_allclose(altered, expected, rtol=0, atol=1e-15, err_msg=str(key))


def test_a_case_outside_the_study_is_refused(study):
    case = {"id": "x", "class": "false_positive", "mechanism": "blend"}
    with pytest.raises(ValueError):
        study.deficit_and_trend(case, {}, np.zeros(1))
