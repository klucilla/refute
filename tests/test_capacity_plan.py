"""Package 25, part B (map Amendment 25, approved by the maintainer on 2026-10-18): ``b`` and ``s``
of the capacity rule as plan settings (``capacity_b``, ``capacity_s``), and the identity that
``calibration_measurement`` records. Written before the code. Synthetic curves only; the curves are
piece 5's (``tests/test_holdout_capacity.py``: seed 3500, a strong signal, and seed 3502, a noisy
hidden year), used here to check the wiring, not a rate."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pytest
from pydantic import ValidationError

from refute.core.canonical import canonical_sha256
from refute.packs.tess import synthetic
from refute.packs.tess.holdout import calibration_measurement, run_holdout
from refute.packs.tess.params import CorrectionsParams, TessTestPlan
from refute.packs.tess.types import LightCurveData

PLANET = synthetic.PLANET
TWO_BY_TWO = (1325.0, 1353.0, 2061.0, 2089.0)


def _plan(**corrections) -> TessTestPlan:
    plan = synthetic.fast_plan_dict()
    plan["gauntlet"] = {"corrections": {"version": 2, "enabled": True, **corrections}}
    return TessTestPlan.model_validate(plan)


def _spec(depth):
    return synthetic.SignalSpec(
        period=PLANET.period, t0=PLANET.t0, depth=depth, duration=PLANET.duration
    )


def _round(outcome, year):
    return next(r for r in outcome.rounds if r.hidden_year == year)


def _strong():
    return synthetic.make_lightcurve(_spec(0.002), sector_starts=TWO_BY_TWO, seed=3500)


def _noisy_hidden(seed=3502, depth=0.002, red_ppm=5000.0):
    quiet, sectors = synthetic.make_lightcurve(_spec(depth), sector_starts=TWO_BY_TWO, seed=seed)
    noisy, _ = synthetic.make_lightcurve(
        _spec(depth), sector_starts=TWO_BY_TWO, seed=seed, red_noise_ppm=red_ppm
    )
    flux = np.where(quiet.year == 2020, noisy.flux, quiet.flux)
    return LightCurveData(quiet.time, flux, quiet.flux_err, quiet.sector, quiet.year), sectors


def _threshold(min_snr, b, s, n_years):
    """The declared formula, computed here (not by the production helper)."""
    return min_snr - b + NormalDist().inv_cdf(1.0 - 0.005 / n_years) * s


@pytest.mark.parametrize(("b", "s"), [(0.4, 0.8), (-0.6, 0.3)])
def test_b1_the_threshold_and_the_record_use_the_plans_pair(b, s):
    lc, sectors = _strong()
    plan = _plan(capacity_b=b, capacity_s=s)
    cap = _round(run_holdout(lc, sectors, plan), 2020).metrics["capacity"]
    assert (cap["b"], cap["s"]) == (b, s)
    min_snr = plan.gauntlet.holdout_by_year.min_snr
    assert cap["threshold"] == pytest.approx(_threshold(min_snr, b, s, cap["n_years"]), rel=1e-12)


def test_b1_decision_1_follows_the_threshold():
    lc, sectors = _strong()
    base = _round(run_holdout(lc, sectors, _plan()), 2020)
    s1 = base.metrics["capacity"]["s_pred_1"]
    assert base.metrics["capacity"]["decision_1"] == "pass"  # precondition
    min_snr = _plan().gauntlet.holdout_by_year.min_snr
    # b chosen by a rule so that the threshold is one above the round's own S_pred,1
    r = _round(run_holdout(lc, sectors, _plan(capacity_b=min_snr - (s1 + 1.0))), 2020)
    assert r.metrics["capacity"]["decision_1"] == "insufficient_capacity_train"
    assert r.access_log == []  # the hidden year is not read


def test_b1_decision_2_follows_the_threshold():
    lc, sectors = _noisy_hidden()
    base = _round(run_holdout(lc, sectors, _plan()), 2020)
    cap = base.metrics["capacity"]
    assert cap["decision_1"] == "pass"  # preconditions
    assert cap["decision_2"] == "insufficient_capacity_hidden_noise"
    min_snr = _plan().gauntlet.holdout_by_year.min_snr
    # b chosen so that the threshold is one below the round's own S_pred,2 (and below S_pred,1)
    low = min(cap["s_pred_1"], cap["s_pred_2"]) - 1.0
    r = _round(run_holdout(lc, sectors, _plan(capacity_b=min_snr - low)), 2020)
    assert r.metrics["capacity"]["decision_1"] == "pass"
    assert r.metrics["capacity"]["decision_2"] == "pass"


REFERENCE = Path(__file__).resolve().parent / "fixtures" / "capacity" / "strong-rounds-4a26df7.json"


def _cpu_features():
    try:
        from numpy._core._multiarray_umath import __cpu_features__
    except ImportError:
        return []
    return sorted(k for k, v in __cpu_features__.items() if v)


def _close(a, b, path=""):
    """Numeric equality within 1e-9 (relative) through nested values; other values exactly."""
    if isinstance(a, dict) and isinstance(b, dict):
        assert set(a) == set(b), path
        for k in a:
            _close(a[k], b[k], f"{path}/{k}")
    elif isinstance(a, list) and isinstance(b, list):
        assert len(a) == len(b), path
        for i, (x, y) in enumerate(zip(a, b, strict=True)):
            _close(x, y, f"{path}/{i}")
    elif isinstance(a, float) or isinstance(b, float):
        assert a == pytest.approx(b, rel=1e-9, abs=1e-15), path
    else:
        assert a == b, path


def test_b2_the_default_pair_reproduces_the_rounds_of_the_code_before_the_package():
    # added after the Codex review of the package: a reference computed with the code of 4a26df7
    # (tests/fixtures/capacity/make_reference.py); bit-equal on the reference machine, within 1e-9
    # elsewhere (the floats are bound to the platform, numpy and the SIMD features)
    from refute.core.io import dumps_json, to_jsonable

    ref = json.loads(REFERENCE.read_text(encoding="utf-8"))
    lc, sectors = _strong()
    now = json.loads(
        dumps_json(to_jsonable([r.to_dict() for r in run_holdout(lc, sectors, _plan()).rounds]))
    )
    same = (
        ref["platform"] == sys.platform
        and ref["numpy"] == np.__version__
        and tuple(ref["python"]) == sys.version_info[:2]
        and ref["cpu_features"] == _cpu_features()
    )
    if same:
        assert now == ref["rounds"]
    else:
        _close(now, ref["rounds"])


def test_b2_the_default_pair_leaves_the_round_records_unchanged():
    lc, sectors = _strong()
    implicit = run_holdout(lc, sectors, _plan())
    explicit = run_holdout(lc, sectors, _plan(capacity_b=0.0, capacity_s=0.0))
    assert [r.to_dict() for r in implicit.rounds] == [r.to_dict() for r in explicit.rounds]
    cap = _round(implicit, 2020).metrics["capacity"]
    assert (cap["b"], cap["s"]) == (0.0, 0.0)
    assert cap["threshold"] == _plan().gauntlet.holdout_by_year.min_snr


@pytest.mark.parametrize(
    "values",
    [
        {"capacity_s": -0.1},
        {"capacity_b": math.nan},
        {"capacity_b": math.inf},
        {"capacity_b": -math.inf},
        {"capacity_s": math.nan},
        {"capacity_s": math.inf},
    ],
)
def test_b3_invalid_pairs_are_refused(values):
    with pytest.raises(ValidationError):
        CorrectionsParams(**values)


def test_b3_valid_edges_are_accepted():
    assert CorrectionsParams(capacity_s=0.0, capacity_b=-2.5).capacity_b == -2.5
    assert (CorrectionsParams().capacity_b, CorrectionsParams().capacity_s) == (0.0, 0.0)


def _identity(plan, path="docs/validation/v0.2.1/population/m4-configurations/x.json"):
    block = plan.gauntlet.corrections.model_dump(mode="json")
    return {"path": path, "sha256": "0" * 64, "block_sha256": canonical_sha256(block)}


def test_b5_the_calibration_record_carries_the_pair_and_the_identity():
    lc, sectors = _strong()
    plan = _plan(capacity_b=0.4, capacity_s=0.8)
    ident = _identity(plan)
    rec = calibration_measurement(lc, sectors, 2020, plan, identity=ident)
    assert (rec["capacity_b"], rec["capacity_s"]) == (0.4, 0.8)
    assert rec["configuration"] == ident
    assert rec["s_meas"] is not None


def test_b5_past_a_capacity_decision_and_in_the_early_return():
    lc, sectors = _strong()
    base = _round(run_holdout(lc, sectors, _plan()), 2020).metrics["capacity"]
    min_snr = _plan().gauntlet.holdout_by_year.min_snr
    plan = _plan(capacity_b=min_snr - (base["s_pred_1"] + 1.0))
    past = calibration_measurement(lc, sectors, 2020, plan, identity=_identity(plan))
    assert past["decision_1"] == "insufficient_capacity_train"
    assert past["capacity_b"] == plan.gauntlet.corrections.capacity_b
    assert past["configuration"]["block_sha256"] == _identity(plan)["block_sha256"]
    # a round decided before the hidden year (no train candidate: pure noise)
    noise, nsec = synthetic.make_lightcurve(None, sector_starts=TWO_BY_TWO, seed=3500)
    plan0 = _plan()
    early = calibration_measurement(noise, nsec, 2020, plan0, identity=_identity(plan0))
    assert early["decision_1"] is None  # precondition: the round was decided before decision 1
    assert early["s_meas"] is None
    assert (early["capacity_b"], early["capacity_s"]) == (0.0, 0.0)
    assert early["configuration"] == _identity(plan0)


def test_b5_an_identity_of_another_block_raises():
    lc, sectors = _strong()
    plan = _plan(capacity_b=0.4)
    with pytest.raises(ValueError):
        calibration_measurement(lc, sectors, 2020, plan, identity=_identity(_plan()))


@pytest.mark.parametrize(
    "bad",
    [
        None,
        "block-only",
        "no-path",
        "short-sha",
    ],
)
def test_b5_the_identity_is_required_and_complete(bad):
    # added after the Codex review of the package: no measurement without the whole identity
    lc, sectors = _strong()
    plan = _plan()
    good = _identity(plan)
    ident = {
        None: None,
        "block-only": {"block_sha256": good["block_sha256"]},
        "no-path": {**good, "path": ""},
        "short-sha": {**good, "sha256": "0" * 10},
    }[bad]
    with pytest.raises(ValueError):
        calibration_measurement(lc, sectors, 2020, plan, identity=ident)
    with pytest.raises(TypeError):
        calibration_measurement(lc, sectors, 2020, plan)  # the identity has no default
