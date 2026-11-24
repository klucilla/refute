"""v0.5.11 step 1: the screen of battery version 5, written before its module exists
(docs/plans/v0.5.11-spec.md, frozen at ab828ce, SHA-256 d498a82a...).

The interface step 2 must provide, in ``refute.packs.tess.screen_d5``:
- ``f1_box(time, flux, flux_err, period, t0, duration) -> dict``: the core test F1 by OE_box.
  The keys are ``state`` (pass, fail or not_assessed), ``reason``, ``coverage``,
  ``coverage_unit``, ``metrics`` and ``threshold``.
- ``report_only(flattened, candidate, star) -> dict``: ``F1_trap``, ``F2``, ``F3``, ``F4`` and
  ``U1``, each with ``state`` (computed or unavailable), ``reason``, ``coverage``,
  ``coverage_unit``, ``metrics`` and ``paper_thresholds``.
- ``compute_screen(flattened, candidate, tests, star) -> dict``: the screen record of section 3.
  ``tests`` are the version-2 analysis's final results.
- ``SPEC_SHA256``: the frozen specification's SHA-256.

Every test here is a strict expected failure: it fails with ModuleNotFoundError until step 2.
Synthetic data only; no network.
"""

from __future__ import annotations

import importlib
import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest

from refute.core.verdict import Severity, TestResult, TestStatus
from refute.packs.tess.synthetic import (
    CORRELATED_PROFILE,
    PLANET,
    SignalSpec,
    make_lightcurve,
    make_star,
)
from refute.packs.tess.types import Candidate, LightCurveData

sys.path.insert(0, str(Path(__file__).resolve().parent))
from screen_reference import f1_reference  # noqa: E402

SPEC_SHA256 = "d498a82ada2e31a5b47768d58d6af2e19af0a3c5e35364693f04886068612f15"
NEEDS_SCREEN = pytest.mark.xfail(
    strict=True, raises=ModuleNotFoundError, reason="screen_d5 does not exist before step 2"
)
EB_HALF = SignalSpec(period=1.8, t0=1325.7, depth=0.006, duration=2 / 24, odd_depth_factor=0.75)


def screen():
    return importlib.import_module("refute.packs.tess.screen_d5")


def _candidate(spec: SignalSpec, duration: float | None = None) -> Candidate:
    return Candidate(
        period=spec.period,
        t0=spec.t0,
        duration=spec.duration if duration is None else duration,
        depth=spec.depth,
        depth_err=spec.depth / 20.0,
        snr=20.0,
        log_likelihood=0.0,
        sde=20.0,
        n_transits=10,
    )


def _gate(status=TestStatus.PASS) -> list[TestResult]:
    return [TestResult("snr", status, Severity.GATE, "gate", coverage=10, coverage_unit="u")]


@NEEDS_SCREEN
@pytest.mark.parametrize("correlated", [False, True], ids=["white", "correlated"])
def test_f1_reproduces_the_reference_decisions_on_the_calibration_fixtures(correlated):
    s = screen()
    kwargs = dict(CORRELATED_PROFILE) if correlated else {}
    for seed in range(1, 201):
        lc, _ = make_lightcurve(PLANET, seed=seed, **kwargs)
        args = (lc.time, lc.flux, lc.flux_err, PLANET.period, PLANET.t0, PLANET.duration)
        got, ref = s.f1_box(*args), f1_reference(*args)
        assert got["state"] == ref.state, seed
        assert math.isclose(got["metrics"]["oe_box"], ref.metrics["oe_box"], rel_tol=1e-9)
        assert got["coverage"] == ref.coverage


@NEEDS_SCREEN
def test_f1_passes_a_planet_and_fails_a_binary_at_half_the_period():
    s = screen()
    lc, _ = make_lightcurve(PLANET, seed=3)
    assert s.f1_box(lc.time, lc.flux, lc.flux_err, PLANET.period, PLANET.t0,
                    PLANET.duration)["state"] == "pass"  # fmt: skip
    lc, _ = make_lightcurve(EB_HALF, seed=3)
    r = s.f1_box(lc.time, lc.flux, lc.flux_err, EB_HALF.period, EB_HALF.t0, EB_HALF.duration)
    assert r["state"] == "fail" and r["metrics"]["oe_box"] > r["threshold"] == 3.0


@NEEDS_SCREEN
def test_f1_not_assessed_paths():
    s = screen()
    lc, _ = make_lightcurve(PLANET, seed=3)
    p, t0, d = PLANET.period, PLANET.t0, PLANET.duration
    # fewer than 20 valid points
    assert s.f1_box(lc.time[:10], lc.flux[:10], lc.flux_err[:10], p, t0, d)["state"] == (
        "not_assessed"
    )
    # one transit only: the odd parity has no in-transit point
    win = (lc.time > t0 - 1.0) & (lc.time < t0 + 1.0)
    r = s.f1_box(lc.time[win], lc.flux[win], lc.flux_err[win], p, t0, d)
    assert r["state"] == "not_assessed"
    # non-finite candidate
    assert s.f1_box(lc.time, lc.flux, lc.flux_err, float("nan"), t0, d)["state"] == ("not_assessed")
    # every error invalid
    bad = np.full_like(lc.flux_err, np.nan)
    assert s.f1_box(lc.time, lc.flux, bad, p, t0, d)["state"] == "not_assessed"
    # no baseline: a curve made only of in-transit points
    k = np.floor((lc.time - t0) / p + 0.5)
    intr = np.abs(lc.time - (t0 + k * p)) <= d / 2
    r = s.f1_box(lc.time[intr], lc.flux[intr], lc.flux_err[intr], p, t0, d)
    assert r["state"] == "not_assessed"


@NEEDS_SCREEN
def test_ineligible_gives_a_null_outcome_and_empty_maps():
    s = screen()
    lc, _ = make_lightcurve(PLANET, seed=3)
    for cand, tests in ((_candidate(PLANET), _gate(TestStatus.INCONCLUSIVE)), (None, _gate())):
        rec = s.compute_screen(lc, cand, tests, make_star())
        assert rec["eligible"] is False and rec["outcome"] is None
        assert rec["core"] == {} and rec["report_only"] == {}
    rec = s.compute_screen(lc, _candidate(PLANET), [], make_star())  # no gate test at all
    assert rec["eligible"] is False and rec["outcome"] is None


@NEEDS_SCREEN
@pytest.mark.parametrize(
    ("state", "outcome"),
    [("pass", "retained"), ("fail", "rejected"), ("not_assessed", "unassessed")],
)
def test_precedence_and_a4_on_the_screen(monkeypatch, state, outcome):
    s = screen()
    lc, _ = make_lightcurve(PLANET, seed=3)
    fake = {"state": state, "reason": "set by the test", "coverage": 1, "coverage_unit": "u",
            "metrics": {}, "threshold": 3.0}  # fmt: skip
    monkeypatch.setattr(s, "f1_box", lambda *a, **k: dict(fake))
    rec = s.compute_screen(lc, _candidate(PLANET), _gate(), make_star())
    assert rec["outcome"] == outcome
    assert rec["outcome"] != "retained" or all(
        c["state"] in ("pass", "fail") for c in rec["core"].values()
    )


@NEEDS_SCREEN
def test_a_report_only_failure_changes_only_its_own_record(monkeypatch):
    s = screen()
    lc, _ = make_lightcurve(PLANET, seed=3)
    star, cand = make_star(), _candidate(PLANET)
    normal = s.compute_screen(lc, cand, _gate(), star)
    original = s.report_only

    def extreme(*args, **kwargs):
        out = original(*args, **kwargs)
        out["F4"] = dict(out["F4"], state="computed", metrics={"V": 9.0})
        out["F2"] = dict(
            out["F2"],
            state="computed",
            metrics={**out["F2"].get("metrics", {}), "would_be_significant": True},
        )
        return out

    monkeypatch.setattr(s, "report_only", extreme)
    changed = s.compute_screen(lc, cand, _gate(), star)
    assert changed["outcome"] == normal["outcome"] and changed["core"] == normal["core"]
    assert changed["eligible"] == normal["eligible"]
    assert changed["report_only"] != normal["report_only"]


@NEEDS_SCREEN
def test_report_only_unavailable_paths():
    s = screen()
    lc, _ = make_lightcurve(PLANET, seed=3)
    # F3 without a stellar radius
    ro = s.report_only(lc, _candidate(PLANET), make_star(radius=None))
    assert ro["F3"]["state"] == "unavailable"
    # the MES grid bound: 4P/T above the number of valid cadences
    ro = s.report_only(lc, _candidate(PLANET, duration=1e-7), make_star())
    assert ro["F2"]["state"] == "unavailable" and ro["U1"]["state"] == "unavailable"
    for name in ("F1_trap", "F2", "F3", "F4", "U1"):
        assert ro[name]["state"] in ("computed", "unavailable")
        assert "coverage" in ro[name] and "coverage_unit" in ro[name]


@NEEDS_SCREEN
def test_the_screen_record_and_its_determinism():
    s = screen()
    assert s.SPEC_SHA256 == SPEC_SHA256
    lc, _ = make_lightcurve(PLANET, seed=3)
    recs = [s.compute_screen(lc, _candidate(PLANET), _gate(), make_star()) for _ in range(2)]
    assert json.dumps(recs[0], sort_keys=True) == json.dumps(recs[1], sort_keys=True)
    rec = recs[0]
    assert rec["version"] == 5 and rec["entry"] == "search" and rec["spec_sha256"] == SPEC_SHA256
    assert rec["labels"] == ["exploratory", "method_status: not_validated"]
    assert set(rec["core"]) == {"F1"}
    assert set(rec["report_only"]) == {"F1_trap", "F2", "F3", "F4", "U1"}
    assert rec["outcome"] in ("retained", "rejected", "unassessed")


@NEEDS_SCREEN
def test_the_screen_reads_the_curve_without_writing_it():
    s = screen()
    lc, _ = make_lightcurve(PLANET, seed=3)
    copy = LightCurveData(lc.time.copy(), lc.flux.copy(), lc.flux_err.copy(), lc.sector.copy(),
                          lc.year.copy())  # fmt: skip
    s.compute_screen(lc, _candidate(PLANET), _gate(), make_star())
    originals = (lc.time, lc.flux, lc.flux_err)
    for a, b in zip(originals, (copy.time, copy.flux, copy.flux_err), strict=True):
        assert np.array_equal(a, b)
