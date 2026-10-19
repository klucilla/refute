"""The ``R_min`` study's derivation by ``R`` (map Amendment 19; its implementation, Amendment 26,
3), written before the code.

Interface (declared here): ``calibration_measurement`` records, besides its earlier fields,
``stage`` (where the measurement stopped: ``"before_capacity"``, ``"train_counts"``,
``"hidden_noise"``, ``"measurement"``, or ``None`` when the FAIL rule read it), ``n_years``,
``train_n_rep`` and ``hidden_n_rep`` (the replica counts over the grid),
``hidden_noise_undetermined`` (the noise estimate alone, apart from the counts), ``d_train``,
``e_train``, ``d_hidden``,
``e_hidden``, ``dp`` and ``measurement_status``. ``derive_round(record, r_min, b, s, min_snr)``
returns ``{"status", "reason", "decision_1", "decision_2", "eligible"}`` for the round at that
``R`` and pair, in Amendment 19's order.

The two checks of Amendment 26, 3: (a) the measured fields do not depend on ``r_min`` where both
records measure; (b) the derivation from the record made at ``r_min`` 8 equals the official round
(``holdout._round``, the decisions enforced) at ``r_min`` = ``R`` with the same pair, on cases that
reach each impediment and their precedence. Synthetic light curves only.
"""

import math

import pytest

import refute.packs.tess.holdout as holdout
from refute.packs.tess import synthetic
from refute.packs.tess.holdout import calibration_measurement, derive_round
from refute.packs.tess.params import TessTestPlan
from refute.packs.tess.types import LightCurveData

PLANET = synthetic.PLANET
R_VALUES = (8, 10, 12, 15, 20)
TWO_BY_TWO = (1325.0, 1353.0, 2061.0, 2089.0)
THREE_BY_ONE = (1325.0, 1353.0, 1381.0, 1500.0)
MEASURED = (
    "d_train",
    "e_train",
    "d_hidden",
    "e_hidden",
    "dp",
    "s_pred_1",
    "s_pred_2",
    "s_meas",
    "train_n_rep",
    "hidden_n_rep",
    "n_years",
)


def _plan(**corrections):
    plan = synthetic.fast_plan_dict()
    plan["gauntlet"] = {"corrections": {"version": 2, "enabled": True, **corrections}}
    return TessTestPlan.model_validate(plan)


def _spec(depth):
    return synthetic.SignalSpec(
        period=PLANET.period, t0=PLANET.t0, depth=depth, duration=PLANET.duration
    )


def _ident(plan):
    from refute.core.canonical import canonical_sha256

    block = canonical_sha256(plan.gauntlet.corrections.model_dump(mode="json"))
    return {"path": "probe.json", "sha256": "0" * 64, "block_sha256": block}


def _noisy_hidden(seed):
    import numpy as np

    quiet, sectors = synthetic.make_lightcurve(_spec(0.002), sector_starts=TWO_BY_TWO, seed=seed)
    noisy, _ = synthetic.make_lightcurve(
        _spec(0.002), sector_starts=TWO_BY_TWO, seed=seed, red_noise_ppm=5000.0
    )
    flux = np.where(quiet.year == 2020, noisy.flux, quiet.flux)
    return LightCurveData(quiet.time, flux, quiet.flux_err, quiet.sector, quiet.year), sectors


def _few_windows(seed):
    import numpy as np

    lc, sectors = synthetic.make_lightcurve(_spec(0.002), sector_starts=TWO_BY_TWO, seed=seed)
    t = lc.time[lc.year == 2020]
    n0 = math.ceil((t.min() - PLANET.t0) / PLANET.period)
    n1 = math.floor((t.max() - PLANET.t0) / PLANET.period)
    drop = np.zeros(len(lc), bool)
    for n in range(n0 + 1, n1 + 1):
        drop |= (lc.year == 2020) & (np.abs(lc.time - (PLANET.t0 + n * PLANET.period)) <= 0.06)
    return lc.select(~drop), sectors


def _case(name):
    """(light curve, sectors, hidden year, corrections) of each case; the cases of
    tests/test_holdout_capacity.py, whose preconditions are checked there."""
    if name == "strong":
        lc, s = synthetic.make_lightcurve(_spec(0.002), sector_starts=TWO_BY_TWO, seed=3500)
        return lc, s, 2020, {}
    if name == "weak":  # decision 1 fails
        lc, s = synthetic.make_lightcurve(_spec(160e-6), sector_starts=THREE_BY_ONE, seed=3501)
        return lc, s, 2019, {}
    if name == "noisy_hidden":  # decision 2 fails
        lc, s = _noisy_hidden(3502)
        return lc, s, 2020, {}
    if name == "no_hidden_signal":  # FAIL
        lc, s = synthetic.make_lightcurve(
            _spec(0.002), sector_starts=TWO_BY_TWO, seed=3504, inject_years=(2018,)
        )
        return lc, s, 2020, {}
    if name == "one_hidden_sector":  # few hidden replicas
        lc, s = synthetic.make_lightcurve(_spec(0.002), sector_starts=THREE_BY_ONE, seed=3507)
        return lc, s, 2019, {}
    if name == "few_windows":  # too few windows after decision 2
        lc, s = _few_windows(3500)
        return lc, s, 2020, {}
    if name == "train_undetermined":  # an impediment before the capacity rule
        lc, s = synthetic.make_lightcurve(_spec(0.002), sector_starts=TWO_BY_TWO, seed=3500)
        return lc, s, 2020, {"b_min": 100_000}
    raise KeyError(name)


CASES = (
    "strong",
    "weak",
    "noisy_hidden",
    "no_hidden_signal",
    "one_hidden_sector",
    "few_windows",
    "train_undetermined",
)
PAIRS = ((0.0, 0.0), (0.5, 0.8))  # the default pair and another one


def _official(r):
    cap = r.metrics.get("capacity") or {}
    reason = r.metrics.get("reason")
    if reason is None and r.status.value == "INCONCLUSIVE":
        reason = r.message  # a round decided before the capacity rule
    d1, d2 = cap.get("decision_1"), cap.get("decision_2")
    eligible = (
        d1 == "pass"
        and d2 == "pass"
        and (r.status.value in ("PASS", "FAIL") or reason == "not_detected_not_inconsistent")
    )
    return {
        "status": r.status.value,
        "reason": reason,
        "decision_1": d1,
        "decision_2": d2,
        "eligible": eligible,
    }


@pytest.fixture(scope="module")
def records():
    out = {}
    for name in CASES:
        lc, sectors, year, extra = _case(name)
        plan = _plan(r_min=8, **extra)
        out[name] = calibration_measurement(lc, sectors, year, plan, identity=_ident(plan))
    return out


def test_the_record_carries_the_fields_of_the_derivation(records):
    for name, rec in records.items():
        for key in ("stage", "n_years", "train_n_rep", "hidden_n_rep", "measurement_status"):
            assert key in rec, (name, key)
    assert records["train_undetermined"]["stage"] == "before_capacity"
    assert records["strong"]["stage"] is None
    assert records["few_windows"]["stage"] == "measurement"
    assert records["few_windows"]["measurement_status"] == "too_few_windows"
    strong = records["strong"]
    assert len(strong["train_n_rep"]) == len(strong["hidden_n_rep"]) >= 3
    assert strong["hidden_noise_undetermined"] is False
    for key in ("d_train", "e_train", "d_hidden", "e_hidden", "dp"):
        assert isinstance(strong[key], float) and math.isfinite(strong[key]), key


@pytest.mark.parametrize("name", CASES)
@pytest.mark.parametrize("pair", PAIRS)
def test_the_derivation_equals_the_official_round_at_every_r(records, name, pair):
    lc, sectors, year, extra = _case(name)
    b, s = pair
    for r_min in R_VALUES:
        plan = _plan(r_min=r_min, capacity_b=b, capacity_s=s, **extra)
        official = _official(holdout._round(lc, sectors, year, plan))
        derived = derive_round(records[name], r_min, b, s, plan.gauntlet.holdout_by_year.min_snr)
        assert derived == official, (name, pair, r_min)


def test_the_cases_reach_every_impediment_and_their_precedence(records):
    reasons = set()
    for name in CASES:
        for r_min in R_VALUES:
            for b, s in PAIRS:
                reasons.add(derive_round(records[name], r_min, b, s, 5.0)["reason"])
    for expected in (
        None,  # PASS
        "inconsistent_with_train",
        "insufficient_capacity_train",
        "insufficient_capacity_hidden_noise",
        "train_replicas_below_r_min",
        "hidden_noise_undetermined",
        "too_few_windows",
        "train_noise_undetermined",
    ):
        assert expected in reasons, (expected, reasons)


def test_the_train_counts_take_precedence_over_decision_1(records):
    rec = records["weak"]
    assert derive_round(rec, 8, 0.0, 0.0, 5.0)["reason"] == "insufficient_capacity_train"
    below = min(rec["train_n_rep"]) + 1
    assert below > 8  # precondition: some R of the set is above the train counts
    out = derive_round(rec, below, 0.0, 0.0, 5.0)
    assert out["reason"] == "train_replicas_below_r_min"
    assert out["decision_1"] == "train_replicas_below_r_min" and out["eligible"] is False


@pytest.mark.parametrize("name", ("strong", "no_hidden_signal", "noisy_hidden", "weak"))
def test_the_measured_fields_do_not_depend_on_r_min(records, name):
    lc, sectors, year, extra = _case(name)
    base = records[name]
    compared = 0
    for r_min in R_VALUES[1:]:
        plan = _plan(r_min=r_min, **extra)
        rec = calibration_measurement(lc, sectors, year, plan, identity=_ident(plan))
        if rec["s_meas"] is None or base["s_meas"] is None:
            continue
        compared += 1
        assert {k: rec[k] for k in MEASURED} == {k: base[k] for k in MEASURED}, r_min
    assert compared >= 1  # precondition: at least one R where both records measure
