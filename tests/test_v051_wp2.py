"""v0.5.1 WP2: the per-event tests on A0's errors, discovery version 3
(docs/plans/v0.5.1-acceptance.md). Mechanism cases on development seeds; the rate rows run in the
acceptance scripts on frozen code."""

from __future__ import annotations

import hashlib

import numpy as np

from refute.packs.tess import a0
from refute.packs.tess.calib05 import c1
from refute.packs.tess.detrend import detrend
from refute.packs.tess.events import per_event_depths
from refute.packs.tess.params import TessTestPlan
from refute.packs.tess.pipeline import attack_candidate, global_prewhitening
from refute.packs.tess.rednoise import event_noise
from refute.packs.tess.search import search_period
from refute.packs.tess.synthetic import discovery_v05_plan_dict


def _plans():
    d = discovery_v05_plan_dict()
    v2 = TessTestPlan.model_validate(d)
    d3 = discovery_v05_plan_dict()
    d3["discovery"]["version"] = 3
    d3["v051"] = {}
    return v2, TessTestPlan.model_validate(d3)


def _seed(text):
    return int(hashlib.sha256(text.encode()).hexdigest()[:16], 16)


def _attack(family, i, plan):
    data, truth = c1.generate(family, _seed(f"refute-v051-dev:wp2-{family}:{i}"))
    flat = detrend(data.lc, plan.detrend)
    pw, searched = global_prewhitening(data, plan, flat)
    cand = search_period(searched, plan.search).candidate
    tests = {t.name: t for t in attack_candidate(data, cand, plan, None, None, pw).tests}
    return data, truth, cand, tests


def test_a0_errors_are_never_below_the_model_errors_and_drop_unmeasured_events():
    _, v3 = _plans()
    # a planet of period at least 3 d (short periods leave A0 few windows: the next test)
    i = 0
    while True:
        data, truth = c1.generate("P", _seed(f"refute-v051-dev:wp2-P:{i}"))
        if truth["period_days"] >= 3.0:
            break
        i += 1
    flat = detrend(data.lc, v3.detrend)
    from refute.packs.tess.types import Candidate

    cand = Candidate(period=truth["period_days"], t0=truth["t0_btjd"],
                     duration=truth["duration_days"], depth=truth["depth"], depth_err=1e-5,
                     snr=20.0, log_likelihood=0.0, sde=10.0, n_transits=10)  # fmt: skip
    cadence = v3.data.exptime_seconds / 86400.0
    noise = event_noise(flat, None, cand.period, cand.t0, cand.duration, v3)
    events = per_event_depths(
        flat, cand.period, cand.t0, cand.duration, cadence, v3.gauntlet.events, 0.0, None, noise
    )
    out, windows, details = a0.empirical_events(flat, cand, events, v3.gauntlet.events, cadence)
    assert len(windows) > 0 and details
    assert len(out) + out.dropped["a0_not_measured"] == len(events)
    model = dict(zip(events.epochs.tolist(), events.errors.tolist(), strict=True))
    for epoch, err in zip(out.epochs.tolist(), out.errors.tolist(), strict=True):
        assert err >= model[epoch]


def test_a_single_event_is_refuted_by_single_event_in_version_3():
    _, v3 = _plans()
    fails = 0
    for i in range(4):
        _, _, cand, tests = _attack("SE", i, v3)
        if cand is not None and tests["single_event"].status.value == "FAIL":
            fails += 1
    assert fails >= 2


def test_version_2_per_event_tests_are_unchanged_by_version_3_code():
    v2, v3 = _plans()
    _, _, _, t2 = _attack("P", 1, v2)
    _, _, _, t3 = _attack("P", 1, v3)
    assert "a0_not_measured" not in str(t2["single_event"].metrics)
    # WP3 (d): version 3 measures odd_even with its own estimator; version 2 keeps v0.5's
    assert "estimator" not in t2["odd_even"].metrics
    assert t3["odd_even"].metrics["estimator"].startswith("matched trapezoid")
    # WP3 (a): version 3 measures the differences on their own series; version 2 keeps v0.5's
    for name in ("aperture_depth", "systematics"):
        assert "estimator" not in t2[name].metrics, name
        assert "A0" in t3[name].metrics["estimator"], name
    assert np.isfinite(len(t3))


def test_short_periods_keep_windows_unless_a_secondary_excludes_phase_half():
    # amendment 5: the phase-0.5 windows enter unless the candidate's secondary_eclipse detects a
    # secondary; with both exclusions, a 1-day period keeps no window (the finding of
    # docs/validation/v0.5.1/feasibility/a0-window-availability.json)
    from refute.packs.tess import synthetic as syn

    t = syn.sector_times(2000.0)
    flux = 1.0 + 1e-3 * np.random.default_rng(0).standard_normal(t.size)
    measure = a0.box_measure(t, flux, 0.08, 0.25, 1.5, 0.5, 2.0 / 1440.0)
    ones = np.ones(t.size, int)
    excluded = a0.pseudo_windows(t, ones, 1.0, 2000.3, 0.08, 1.5, 0.5, measure, True)
    included = a0.pseudo_windows(t, ones, 1.0, 2000.3, 0.08, 1.5, 0.5, measure, False)
    assert excluded == []
    assert len(included) >= 20
