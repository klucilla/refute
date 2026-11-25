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


def test_f1_passes_a_planet_and_fails_a_binary_at_half_the_period():
    s = screen()
    lc, _ = make_lightcurve(PLANET, seed=3)
    assert s.f1_box(lc.time, lc.flux, lc.flux_err, PLANET.period, PLANET.t0,
                    PLANET.duration)["state"] == "pass"  # fmt: skip
    lc, _ = make_lightcurve(EB_HALF, seed=3)
    r = s.f1_box(lc.time, lc.flux, lc.flux_err, EB_HALF.period, EB_HALF.t0, EB_HALF.duration)
    assert r["state"] == "fail" and r["metrics"]["oe_box"] > r["threshold"] == 3.0


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


def test_ineligible_gives_a_null_outcome_and_empty_maps():
    s = screen()
    lc, _ = make_lightcurve(PLANET, seed=3)
    for cand, tests in ((_candidate(PLANET), _gate(TestStatus.INCONCLUSIVE)), (None, _gate())):
        rec = s.compute_screen(lc, cand, tests, make_star())
        assert rec["eligible"] is False and rec["outcome"] is None
        assert rec["core"] == {} and rec["report_only"] == {}
    rec = s.compute_screen(lc, _candidate(PLANET), [], make_star())  # no gate test at all
    assert rec["eligible"] is False and rec["outcome"] is None


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


def test_an_extreme_flux_error_never_raises_in_f1():
    # Codex's review of the step-2 diff, item 1: a finite, positive error whose weight overflows
    s = screen()
    lc, _ = make_lightcurve(PLANET, seed=3)
    # (and its second review, item 1: the frozen predicate keeps such points valid; the weights
    # on a common scale cannot represent the others, so F1 is not assessed, never a pass)
    err = lc.flux_err.copy()
    err[:5] = 1e-200
    r = s.f1_box(lc.time, lc.flux, err, PLANET.period, PLANET.t0, PLANET.duration)
    assert r["state"] == "not_assessed"
    assert r["metrics"]["dropped"] == 0 and r["metrics"]["valid"] == lc.time.size
    rec = s.compute_screen(
        LightCurveData(lc.time, lc.flux, err, lc.sector, lc.year),
        _candidate(PLANET),
        _gate(),
        make_star(),
    )
    assert rec["outcome"] == "unassessed"
    assert all(v["state"] == "unavailable" for v in rec["report_only"].values())


# --- correction 1 of the specification: the input range of sigma -----------------------------
# docs/plans/v0.5.11-spec-correction-1.md; the maintainer's decision of 2026-11-25, #218 comment
# 7162573384, item 1. Written and pushed before the code (58c308d), where six of them were strict
# expected failures on the module as committed at a896c49 (step2/expected-tests-ir.json). The E1
# test of 912087a (sigma = 1e-154 assessed like ordinary errors) is withdrawn: the rule decides
# the opposite.

CORRECTION_SHA256 = "62a5532f01c498901dd2c1546ad428e33cb4669efa14caf3d80d57f9b19b6df7"
INVALID = "invalid_uncertainty"
# the reviewed path (a896c49) on ordinary errors, recorded before the change
REVIEWED = {"planet": ("pass", 2.507454281461856), "eb_half": ("fail", 43.09203063661559)}
BIN_WITNESS_TIMES = np.array(
    [0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30,
     1.00, 1.05, 1.10, 1.15, 1.20, 1.25, 1.30,
     2.00, 2.05, 2.10, 2.15, 2.20, 2.25]
)  # fmt: skip


def _equal_errors(sigma: float):
    lc, _ = make_lightcurve(PLANET, seed=3)
    err = np.full_like(lc.flux_err, sigma)
    return screen().f1_box(lc.time, lc.flux, err, PLANET.period, PLANET.t0, PLANET.duration)


@pytest.mark.parametrize(("name", "spec"), [("planet", PLANET), ("eb_half", EB_HALF)])
def test_ordinary_errors_keep_the_reviewed_f1(name, spec):
    lc, _ = make_lightcurve(spec, seed=3)
    r = screen().f1_box(lc.time, lc.flux, lc.flux_err, spec.period, spec.t0, spec.duration)
    state, oe = REVIEWED[name]
    assert r["state"] == state
    assert math.isclose(r["metrics"]["oe_box"], oe, rel_tol=1e-9)


@pytest.mark.parametrize("sigma", [1e-12, 1e3], ids=["floor", "ceiling"])
def test_the_ends_of_the_range_are_assessed_like_ordinary_errors(sigma):
    state, oe = REVIEWED["planet"]
    r = _equal_errors(sigma)
    assert r["state"] == state
    assert math.isclose(r["metrics"]["oe_box"], oe, rel_tol=1e-9)


def test_codex_first_witness_is_unassessed():
    # equal sigma = 4.5e-153 on a curve whose raw reductions are representable (on a896c49 it
    # is assessed by the raw path; E1's bound turned its pass into a fail)
    s = screen()
    lc, _ = make_lightcurve(PLANET, seed=3)
    t, f = lc.time[::12], lc.flux[::12]
    err = np.full_like(f, 4.5e-153)
    assert np.isfinite(np.sum(1.0 / err**2))  # the witness's own precondition
    r = s.f1_box(t, f, err, PLANET.period, PLANET.t0, PLANET.duration)
    assert r["state"] == "not_assessed" and r["reason"] == INVALID


def test_codex_second_witness_is_unassessed():
    # 20 points: the flat total weight is finite, the sum of the three bin totals overflows
    s = screen()
    t = BIN_WITNESS_TIMES
    f = 1.0 - 1e-4 * (np.arange(20) % 3)
    err = 2.931545212024566e-154 * (1.0 + np.arange(20) / 64.0)
    w = 1.0 / err**2
    idx = np.floor((t - t.min()) / 0.5).astype(np.int64)
    totals = np.array([w[idx == m].sum() for m in np.unique(idx)])
    with np.errstate(over="ignore"):
        assert np.isfinite(np.sum(w)) and not np.isfinite(np.sum(totals))  # the precondition
    r = s.f1_box(t, f, err, 10.0, 5.0, 0.5)
    assert r["state"] == "not_assessed" and r["reason"] == INVALID


def test_the_case_of_errata_12_is_unassessed_in_the_core_and_the_report():
    s = screen()
    assert _equal_errors(1e-154)["reason"] == INVALID
    lc, _ = make_lightcurve(PLANET, seed=3)
    tiny = LightCurveData(lc.time, lc.flux, np.full_like(lc.flux_err, 1e-154), lc.sector,
                          lc.year)  # fmt: skip
    rec = s.compute_screen(tiny, _candidate(PLANET), _gate(), make_star())
    assert rec["outcome"] == "unassessed"
    assert rec["core"]["F1"]["state"] == "not_assessed"
    assert rec["core"]["F1"]["reason"] == INVALID
    for v in rec["report_only"].values():
        assert v["state"] == "unavailable" and v["reason"] == INVALID


@pytest.mark.parametrize("sigma", [9.99e-13, 1.001e3], ids=["below", "above"])
def test_just_outside_the_range_is_unassessed(sigma):
    r = _equal_errors(sigma)
    assert r["state"] == "not_assessed" and r["reason"] == INVALID


def test_the_record_cites_the_correction():
    s = screen()
    assert s.CORRECTION_SHA256 == CORRECTION_SHA256
    lc, _ = make_lightcurve(PLANET, seed=3)
    rec = s.compute_screen(lc, _candidate(PLANET), _gate(), make_star())
    assert rec["spec_sha256"] == SPEC_SHA256
    assert rec["spec_correction_sha256"] == CORRECTION_SHA256


def test_the_floor_keeps_the_weighted_reductions_finite_at_1e7_points():
    # section 4 of the correction: w <= 1e24 and N <= 1e7 bound every sum by 4e231 for |f| <= 1e100
    s = screen()
    n = 10_000_000
    w = np.full(n, 1.0 / 1e-12**2)
    x = np.where(np.arange(n) % 2 == 0, 1e100, -1e100)
    m, sd = s._wmean(x, w), s._wstd(x, w)
    assert m is not None and math.isfinite(m)
    assert sd is not None and math.isfinite(sd)


def test_the_reference_applies_the_same_rule():
    lc, _ = make_lightcurve(PLANET, seed=3)
    args = (PLANET.period, PLANET.t0, PLANET.duration)
    for sigma in (1e-154, 9.99e-13, 1.001e3, float("inf"), 0.0, -1.0):
        r = f1_reference(lc.time, lc.flux, np.full_like(lc.flux_err, sigma), *args)
        assert r.state == "not_assessed" and r.reason == INVALID, sigma
    ok = f1_reference(lc.time, lc.flux, np.full_like(lc.flux_err, 1e-12), *args)
    assert ok.state == REVIEWED["planet"][0]


def test_an_unrepresentable_epoch_is_not_assessed():
    s = screen()
    lc, _ = make_lightcurve(PLANET, seed=3)
    r = s.f1_box(lc.time, lc.flux, lc.flux_err, 1e-20, PLANET.t0, 1e-21)
    assert r["state"] == "not_assessed"


def test_an_eligible_case_without_a_curve_is_unassessed():
    s = screen()
    rec = s.compute_screen(None, _candidate(PLANET), _gate(), make_star())
    assert rec["eligible"] is True and rec["outcome"] == "unassessed"
    assert rec["core"]["F1"]["state"] == "not_assessed"
    assert all(v["state"] == "unavailable" for v in rec["report_only"].values())


def test_direct_finalization_without_a_curve_keeps_the_legacy_verdict():
    from dataclasses import replace

    from refute.packs.tess.params import TessTestPlan
    from refute.packs.tess.pipeline import analyze_data, conclude_analysis
    from refute.packs.tess.synthetic import discovery_v05_plan_dict, scenario_data

    d = discovery_v05_plan_dict()
    d["discovery"]["version"] = 5
    d["discovery"]["entry"] = "search"
    plan = TessTestPlan.model_validate(d)
    data = scenario_data("planet")
    a = analyze_data(data, plan, stage=1)
    g = replace(a.gauntlet, flattened=None)
    b = conclude_analysis(a.search, a.flattened_search, g, a.holdout, False, plan=plan, stage=1)
    assert b.verdict == a.verdict and b.verdict_reason == a.verdict_reason
    assert b.extras["screen"]["core"]["F1"]["state"] == "not_assessed"


def test_a_shared_fit_failure_stays_in_its_dependents(monkeypatch):
    # Codex's review of the step-2 diff, item 1: a LinAlgError in the shared trapezoid fit makes
    # F1_trap, F3 and F4 unavailable and leaves the core, F2, U1 and the outcome unchanged
    s = screen()
    lc, _ = make_lightcurve(PLANET, seed=3)
    star, cand = make_star(), _candidate(PLANET)
    normal = s.compute_screen(lc, cand, _gate(), star)

    def broken(*args, **kwargs):
        raise np.linalg.LinAlgError("forced by the test")

    monkeypatch.setattr(s, "_trapezoid", broken)
    failed = s.compute_screen(lc, cand, _gate(), star)
    assert failed["outcome"] == normal["outcome"] and failed["core"] == normal["core"]
    for name in ("F1_trap", "F3", "F4"):
        assert failed["report_only"][name]["state"] == "unavailable"
        assert "LinAlgError" in failed["report_only"][name]["reason"]
    for name in ("F2", "U1"):
        assert failed["report_only"][name] == normal["report_only"][name]


def test_f2_always_carries_its_two_flags():
    s = screen()
    lc, _ = make_lightcurve(PLANET, seed=3)
    for duration in (PLANET.duration, 1e-7):
        f2 = s.report_only(lc, _candidate(PLANET, duration=duration), make_star())["F2"]
        assert "would_be_significant" in f2["metrics"]
        assert "exception_first_condition" in f2["metrics"]


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


def test_the_screen_reads_the_curve_without_writing_it():
    s = screen()
    lc, _ = make_lightcurve(PLANET, seed=3)
    copy = LightCurveData(lc.time.copy(), lc.flux.copy(), lc.flux_err.copy(), lc.sector.copy(),
                          lc.year.copy())  # fmt: skip
    s.compute_screen(lc, _candidate(PLANET), _gate(), make_star())
    originals = (lc.time, lc.flux, lc.flux_err)
    for a, b in zip(originals, (copy.time, copy.flux, copy.flux_err), strict=True):
        assert np.array_equal(a, b)
