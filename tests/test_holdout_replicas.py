"""M4 piece 4: the holdout's replica spans and the hidden-window variance by empirical replicas
(revision 4 of the corrections plan, section 1; docs/validation/v0.2.1/reopen/
m4-implementation-map.md, Amendments 6, 10 and 11, which declare the interface and the cases).

The numeric cases (white, AR(1), the pulls) use only ``synthetic.make_lightcurve`` with the seeds
3000 to 3399 and 4000 to 4399 declared in Amendment 11.
"""

import math

import numpy as np
import pytest

from refute.core.runner import default_workers, run_processes
from refute.packs.tess import synthetic
from refute.packs.tess.ephemeris import Ephemeris
from refute.packs.tess.holdout import (
    HiddenYear,
    _predict_windows,
    best_dp_index,
    measure_with_replicas,
    period_grid,
    register_replicas,
    replica_stats,
    window_depth,
)
from refute.packs.tess.params import TessTestPlan
from refute.packs.tess.types import LightCurveData

PLANET = synthetic.PLANET
T14 = PLANET.duration
CADENCE = 120.0 / 86400.0
HIDDEN_STARTS = (1325.0, 1353.0)  # two sectors of one observing year (2018)
SIGMA = 600e-6


def _plan(**corrections):
    plan = synthetic.fast_plan_dict()
    plan["gauntlet"] = {"corrections": {"enabled": True, **corrections}}
    return TessTestPlan.model_validate(plan)


def _ephemeris(period_err=0.0):
    return Ephemeris(
        t_ref=PLANET.t0,
        n_ref=0,
        period=PLANET.period,
        cov=((0.0, 0.0), (0.0, period_err**2)),
        chi2_reduced=1.0,
        n_transits=10,
    )


def _hidden_lc(seed, noise="white", spec=None, noise_ppm=600.0, starts=HIDDEN_STARTS):
    extra = synthetic.CORRELATED_PROFILE if noise == "correlated" else {}
    return synthetic.make_lightcurve(
        spec, sector_starts=starts, seed=seed, noise_ppm=noise_ppm, **extra
    )


def _geometry(infos, period_err=0.0, plan=None):
    plan = plan or _plan()
    params = plan.gauntlet.holdout_by_year
    eph = _ephemeris(period_err)
    spans = [(s.t_start, s.t_end) for s in infos]
    windows = _predict_windows(eph, T14, spans, params)
    replicas = register_replicas(eph, windows, spans)
    return eph, windows, replicas, plan


def _measure(task):
    """Top-level for the process pool: (seed, noise, spec_depth or None)."""
    seed, noise, depth = task
    spec = None
    if depth is not None:
        spec = synthetic.SignalSpec(
            period=PLANET.period, t0=PLANET.t0, depth=depth, duration=T14, ingress_fraction=1e-3
        )
    lc, infos = _hidden_lc(seed, noise, spec, noise_ppm=50.0 if depth is not None else 600.0)
    eph, windows, replicas, plan = _geometry(infos)
    hidden = HiddenYear(lc, windows + replicas, plan)
    grid = period_grid(eph, windows, T14, plan.gauntlet.holdout_by_year)
    transit = [w for w in windows if w.kind == "transit"]
    stats = replica_stats(hidden, replicas, eph, T14, CADENCE, plan, infos, grid)
    result = measure_with_replicas(hidden, transit, replicas, eph, T14, CADENCE, plan, infos, grid)
    return lc, replicas, stats, result


def _var_rep(task):
    """(var_rep at dP = 0, the depth of every replica position, None where not usable)."""
    _, _, stats, _ = _measure(task)
    point = stats.per_dp[0]
    return point.var_rep, list(point.depths)


def _pool(fn, tasks):
    return run_processes(fn, tasks, max(1, min(len(tasks), default_workers())))


# --- registration (metadata only) ---------------------------------------------------------------


GEOMETRIES = [(p, f) for p in (1.5, 2.5, 3.7, 5.5) for f in (0.0, 0.3, 0.6, 0.9)]


def _spans_meta(starts=HIDDEN_STARTS):
    out = []
    for start in starts:
        t = synthetic.sector_times(start)
        out.append((float(t.min()), float(t.max())))
    return out


def _closed_overlap(a0, a1, b0, b1):
    return a0 <= b1 and b0 <= a1


@pytest.mark.parametrize(("period", "timing_frac"), GEOMETRIES)
def test_replicas_never_overlap_a_window_and_keep_the_masked_fraction(period, timing_frac):
    params = _plan().gauntlet.holdout_by_year
    spans = _spans_meta()
    # a period error that gives a timing error of timing_frac * T14 at the farthest epoch
    n_far = (spans[-1][1] - PLANET.t0) / period
    eph = Ephemeris(
        PLANET.t0, 0, period, ((0.0, 0.0), (0.0, (timing_frac * T14 / n_far) ** 2)), 1.0, 9
    )
    windows = _predict_windows(eph, T14, spans, params)
    replicas = register_replicas(eph, windows, spans)
    assert all(r.kind == "replica" for r in replicas)
    spans_w = [(w.t_pred - w.baseline_outer, w.t_pred + w.baseline_outer) for w in windows]
    spans_r = [(r.t_pred - r.baseline_outer, r.t_pred + r.baseline_outer) for r in replicas]
    for a0, a1 in spans_r:
        assert any(lo <= a0 and a1 <= hi for lo, hi in spans)  # inside one sector
        assert not any(_closed_overlap(a0, a1, b0, b1) for b0, b1 in spans_w)
    for i, (a0, a1) in enumerate(spans_r):
        for b0, b1 in spans_r[i + 1 :]:
            assert not _closed_overlap(a0, a1, b0, b1)
    # Revision 4, 1: a replica is accepted only if the sector's masked fraction stays at most 0.5
    # once it is added. (Corrected after the first run: the windows alone can mask more than half
    # of a sector, at short periods with a large timing error; then no replica is accepted there.)
    for lo, hi in spans:
        grid = np.linspace(lo, hi, 200001)

        def fraction(intervals, grid=grid):
            masked = np.zeros(grid.size, bool)
            for a0, a1 in intervals:
                masked |= (grid >= a0) & (grid <= a1)
            return masked.mean()

        own = [(w.t_pred - w.baseline_inner, w.t_pred + w.baseline_inner) for w in windows]
        here = [r for r in replicas if lo <= r.t_pred <= hi]
        reps = [(r.t_pred - r.baseline_inner, r.t_pred + r.baseline_inner) for r in here]
        if here:
            assert fraction(own + reps) <= 0.5 + 1e-4
        if fraction(own) > 0.5 + 1e-4:
            assert not here


def test_the_same_metadata_gives_the_same_replicas():
    params = _plan().gauntlet.holdout_by_year
    spans = _spans_meta()
    eph = _ephemeris(1e-4)
    windows = _predict_windows(eph, T14, spans, params)
    assert register_replicas(eph, windows, spans) == register_replicas(eph, windows, spans)


def test_the_replicas_follow_the_declared_phase_order():
    params = _plan().gauntlet.holdout_by_year
    spans = _spans_meta()
    eph = _ephemeris()
    windows = _predict_windows(eph, T14, spans, params)
    replicas = register_replicas(eph, windows, spans)
    assert len(replicas) >= 20
    phases = [round(((r.t_pred - eph.t_ref) / eph.period) % 1.0, 6) for r in replicas]
    first = {0.25, 0.75}
    # every accepted center at phase 0.25 or 0.75 comes before any other phase in the list
    seen_other = False
    for p in phases:
        if p not in first:
            seen_other = True
        else:
            assert not seen_other


# --- window_depth (the local measurement) ----------------------------------------------------


def _local_cadences(center, half, inner, outer):
    t = center + np.arange(-outer, outer + CADENCE / 2, CADENCE)
    dt = np.abs(t - center)
    keep = (dt <= half) | ((dt > inner) & (dt <= outer))
    t = t[keep]
    in_window = np.abs(t - center) <= half
    return t, in_window


def _analytic(t, in_window, center, half):
    box = in_window & (np.abs(t - center) <= half)
    x = t[~box] - center
    design = np.column_stack([np.ones_like(x), x])
    g = np.array([1.0, float(np.mean(t[box] - center))])
    return SIGMA * math.sqrt(1.0 / box.sum() + g @ np.linalg.inv(design.T @ design) @ g)


def test_window_depth_matches_the_analytic_error_on_white_noise_without_detrending():
    center, half = 1330.0, T14 / 2 + 0.02
    inner, outer = half + 0.25 * T14, half + 1.5 * T14
    t, in_window = _local_cadences(center, half, inner, outer)
    rng = np.random.default_rng(12345)
    depths = []
    for _ in range(3000):
        f = 1.0 + rng.normal(0.0, SIGMA, t.size)
        depths.append(window_depth(t, f, in_window, center, T14 / 2, cadence=CADENCE).depth)
    expected = _analytic(t, in_window, center, T14 / 2)
    assert np.std(depths, ddof=1) == pytest.approx(expected, rel=0.05)


def test_window_depth_of_a_known_box_on_a_line():
    center, half = 1330.0, T14 / 2
    inner, outer = half + 0.25 * T14, half + 1.5 * T14
    t, in_window = _local_cadences(center, half, inner, outer)
    f = 1.0 + 3e-4 * (t - center) - 0.002 * (np.abs(t - center) <= T14 / 2)
    d = window_depth(t, f, in_window, center, T14 / 2, cadence=CADENCE)
    assert d.depth == pytest.approx(0.002, rel=1e-9)
    assert d.n_params == 2 and d.reason is None


def test_window_depth_falls_back_to_a_constant_then_drops():
    center, half = 1330.0, T14 / 2
    t_box = center + np.arange(-half, half, CADENCE)
    few = center + half + CADENCE * np.arange(1, 31)  # 30 baseline cadences: < 2 x 20
    t = np.concatenate([t_box, few])
    in_window = np.ones(t.size, bool)
    f = np.ones(t.size)
    d = window_depth(t, f, in_window, center, T14 / 2, cadence=CADENCE)
    assert d.n_params == 1 and d.depth is not None
    t2 = np.concatenate([t_box, few[:10]])  # 10 baseline cadences: < 20
    d2 = window_depth(
        t2, np.ones(t2.size), np.ones(t2.size, bool), center, T14 / 2, cadence=CADENCE
    )
    assert d2.depth is None and d2.reason == "degenerate_baseline"


def test_window_depth_refuses_a_poorly_covered_box():
    center, half = 1330.0, T14 / 2
    inner, outer = half + 0.25 * T14, half + 1.5 * T14
    t, in_window = _local_cadences(center, half, inner, outer)
    keep = ~((t > center - 0.4 * T14) & (t < center + 0.4 * T14))  # most of the box missing
    d = window_depth(
        t[keep], np.ones(keep.sum()), in_window[keep], center, T14 / 2, cadence=CADENCE
    )
    assert d.depth is None and d.reason == "box_coverage"


# --- the grid and its ties ------------------------------------------------------------------


def test_the_period_grid_is_odd_symmetric_and_contains_zero():
    params = _plan().gauntlet.holdout_by_year
    spans = _spans_meta()
    for err in (0.0, 1e-5, 3e-5, 1e-4):
        eph = _ephemeris(err)
        windows = _predict_windows(eph, T14, spans, params)
        grid = period_grid(eph, windows, T14, params)
        assert grid.size % 2 == 1
        assert np.allclose(grid, -grid[::-1])
        assert 0.0 in grid
        if err == 0.0:
            assert grid.tolist() == [0.0]


def test_best_dp_ties_go_to_the_smaller_magnitude_then_the_negative_side():
    grid = np.array([-2.0, -1.0, 0.0, 1.0, 2.0])
    assert best_dp_index(np.array([1.0, 3.0, 2.0, 3.0, 1.0]), grid) == 1
    assert best_dp_index(np.array([3.0, 1.0, 3.0, 1.0, 3.0]), grid) == 2
    assert best_dp_index(np.array([np.nan, 1.0, np.nan, 2.0, np.nan]), grid) == 3


def test_a_non_trivial_grid_measures_the_replicas_at_the_shifted_centers():
    lc, infos = _hidden_lc(3000)
    # 2e-4 (after the sabotage SR7 was not caught at 2e-5, whose shifts stayed below a cadence):
    # the shifts at the far epochs reach several cadences
    eph, windows, replicas, plan = _geometry(infos, period_err=2e-4)
    grid = period_grid(eph, windows, T14, plan.gauntlet.holdout_by_year)
    assert grid.size >= 3
    hidden = HiddenYear(lc, windows + replicas, plan)
    stats = replica_stats(hidden, replicas, eph, T14, CADENCE, plan, infos, grid)
    assert [p.dp for p in stats.per_dp] == grid.tolist()
    i, r = max(enumerate(replicas), key=lambda item: abs(item[1].epoch - eph.n_ref))
    t_in, f_in = hidden.window(r.t_pred, r.half_width)
    t_b, f_b = hidden.local_baseline(r.t_pred, r.half_width)
    t = np.concatenate([t_in, t_b])
    f = np.concatenate([f_in, f_b])
    in_window = np.concatenate([np.ones(t_in.size, bool), np.zeros(t_b.size, bool)])
    k = grid.size - 1
    center = r.t_pred + (r.epoch - eph.n_ref) * grid[k]
    expected = window_depth(t, f, in_window, center, T14 / 2, cadence=CADENCE).depth
    unshifted = window_depth(t, f, in_window, r.t_pred, T14 / 2, cadence=CADENCE).depth
    assert unshifted != expected  # the shift moves the box by at least one cadence
    assert stats.per_dp[k].depths[i] == pytest.approx(expected, rel=1e-12)
    transit = [w for w in windows if w.kind == "transit"]
    result = measure_with_replicas(hidden, transit, replicas, eph, T14, CADENCE, plan, infos, grid)
    snrs = np.array([p["snr"] for p in result["per_dp"]])
    assert result["dp"] == grid[best_dp_index(snrs, grid)]


# --- the barrier and the hidden noise of O2 -----------------------------------------------------


def test_too_few_replicas_is_inconclusive_and_no_transit_window_is_read():
    lc, infos = _hidden_lc(3001)
    # sigma_t above T14 at the far epochs (6e-3, first written, still left 22 replicas)
    eph, windows, replicas, plan = _geometry(infos, period_err=1.2e-2)
    assert len(replicas) < 20
    hidden = HiddenYear(lc, windows + replicas, plan)
    grid = period_grid(eph, windows, T14, plan.gauntlet.holdout_by_year)
    transit = [w for w in windows if w.kind == "transit"]
    result = measure_with_replicas(hidden, transit, replicas, eph, T14, CADENCE, plan, infos, grid)
    assert result["status"] == "hidden_noise_undetermined"
    assert result.get("depth") is None
    assert not any(e["kind"].startswith("transit") for e in hidden.access_log)


def test_a_sector_without_bins_drops_its_windows_and_none_left_is_inconclusive():
    from dataclasses import replace

    lc, infos = _hidden_lc(3002)
    keep = (lc.sector == 1) | (lc.time < 1353.0 + 4.0)  # sector 2 cut to 4 days
    short = lc.select(keep)
    infos2 = [infos[0], replace(infos[1], t_end=float(short.time.max()))]
    # r_min lowered so that the barrier does not stop the case before the sector rule is reached
    eph, windows, replicas, plan = _geometry(infos2, plan=_plan(r_min=5))
    hidden = HiddenYear(short, windows + replicas, plan)
    grid = period_grid(eph, windows, T14, plan.gauntlet.holdout_by_year)
    stats = replica_stats(hidden, replicas, eph, T14, CADENCE, plan, infos2, grid)
    assert 2 in stats.excluded_sectors and 1 not in stats.excluded_sectors
    # added after the sabotage SR5 was not caught: no replica of the excluded sector is counted
    in_two = [i for i, r in enumerate(replicas) if r.t_pred > infos2[1].t_start]
    assert in_two
    assert all(stats.per_dp[0].depths[i] is None for i in in_two)
    transit = [w for w in windows if w.kind == "transit"]
    result = measure_with_replicas(hidden, transit, replicas, eph, T14, CADENCE, plan, infos2, grid)
    assert result["dropped"].get("excluded_sector", 0) >= 1
    plan_none = _plan(b_min=100_000)
    hidden2 = HiddenYear(short, windows + replicas, plan_none)
    stats2 = replica_stats(hidden2, replicas, eph, T14, CADENCE, plan_none, infos2, grid)
    assert stats2.status == "hidden_noise_undetermined"


def test_overlap_is_tested_on_closed_intervals():
    """Added after the sabotage SR2 was not caught: spans that only touch overlap."""
    from refute.packs.tess.holdout import _closed_overlap

    assert _closed_overlap(0.0, 1.0, [(1.0, 2.0)])
    assert _closed_overlap(1.0, 2.0, [(0.0, 1.0)])
    assert not _closed_overlap(0.0, 1.0, [(1.0 + 1e-9, 2.0)])


def test_a_replica_with_a_poorly_covered_band_is_not_used():
    """Added after the sabotage SR6 was not caught: 60% of one replica's bands removed."""
    lc, infos = _hidden_lc(3003)
    eph, windows, replicas, plan = _geometry(infos)
    r = replicas[0]
    dt = np.abs(lc.time - r.t_pred)
    band = (dt > r.baseline_inner) & (dt <= r.baseline_outer)
    idx = np.flatnonzero(band)
    drop = np.zeros(len(lc), bool)
    drop[idx[: int(0.6 * idx.size)]] = True
    cut = lc.select(~drop)
    hidden = HiddenYear(cut, windows + replicas, plan)
    grid = period_grid(eph, windows, T14, plan.gauntlet.holdout_by_year)
    stats = replica_stats(hidden, replicas, eph, T14, CADENCE, plan, infos, grid)
    assert stats.per_dp[0].depths[0] is None
    assert stats.dropped.get("band_coverage", 0) >= 1


def test_windows_sharing_cadences_keep_only_the_earlier():
    from dataclasses import replace

    from refute.packs.tess.holdout import measure_windows

    lc, infos = _hidden_lc(3003)
    eph, windows, replicas, plan = _geometry(infos)
    transit = [w for w in windows if w.kind == "transit"]
    extra = replace(transit[2], t_pred=transit[2].t_pred + 0.1)  # shares cadences with it
    hidden = HiddenYear(lc, windows + [extra] + replicas, plan)
    grid = period_grid(eph, windows, T14, plan.gauntlet.holdout_by_year)
    stats = replica_stats(hidden, replicas, eph, T14, CADENCE, plan, infos, grid)
    assert stats.status == "ok"
    ordered = sorted([*transit, extra], key=lambda w: w.t_pred)
    result = measure_windows(hidden, ordered, eph, T14, CADENCE, plan, infos, grid, stats)
    assert result["dropped"].get("shared_cadences", 0) == 1
    assert result["n_valid"] + sum(result["dropped"].values()) == len(ordered)


# --- the numeric criteria of revision 4, 1 (Amendment 11) -------------------------------------


def _analytic_median(lc, replicas):
    values = []
    for r in replicas:
        dt = np.abs(lc.time - r.t_pred)
        sel = (dt <= r.half_width) | ((dt > r.baseline_inner) & (dt <= r.baseline_outer))
        t = lc.time[sel]
        in_window = np.abs(t - r.t_pred) <= r.half_width
        box = in_window & (np.abs(t - r.t_pred) <= T14 / 2)
        if box.sum() == 0 or (~box).sum() < 40:
            continue
        values.append(_analytic(t, in_window, r.t_pred, T14 / 2))
    return float(np.median(values))


def test_white_noise_replica_deviation_is_within_15_percent_of_the_analytic_error():
    tasks = [(seed, "white", None) for seed in range(3000, 3200)]
    out = _pool(_var_rep, tasks)
    lc0, infos0 = _hidden_lc(3000)
    _, _, replicas0, _ = _geometry(infos0)
    analytic = _analytic_median(lc0, replicas0)  # the same cadences for every seed
    ratios = [math.sqrt(v) / analytic for v, _ in out]
    assert len(ratios) == 200
    median = float(np.median(ratios))
    assert 0.85 <= median <= 1.15, median


@pytest.fixture(scope="module")
def ar1_monte_carlo():
    out = _pool(_var_rep, [(seed, "correlated", None) for seed in range(4000, 4400)])
    positions: dict[int, list[float]] = {}
    for _, depths in out:
        for index, d in enumerate(depths):
            if d is not None:
                positions.setdefault(index, []).append(d)
    return float(np.median([np.var(v, ddof=1) for v in positions.values() if len(v) > 1]))


def test_ar1_replica_variance_is_within_15_percent_of_the_monte_carlo(ar1_monte_carlo):
    out = _pool(_var_rep, [(seed, "correlated", None) for seed in range(3000, 3200)])
    ratios = [v / ar1_monte_carlo for v, _ in out]
    assert len(ratios) == 200
    median = float(np.median(ratios))
    assert 0.85 <= median <= 1.15, median


def _pull(task):
    _, _, _, result = _measure(task)
    if result.get("depth") is None or not result.get("error"):
        return None
    return result["depth"] / result["error"]


def test_the_full_operation_pulls_on_ar1_hidden_years_are_within_the_k_margins():
    pulls = _pool(_pull, [(seed, "correlated", None) for seed in range(3200, 3400)])
    assert len(pulls) == 200
    assert all(p is not None for p in pulls), "a year without a measurement: incompatible"
    pulls = np.asarray(pulls, dtype=float)
    one = float(np.mean(np.abs(pulls) <= 1.0))
    two = float(np.mean(np.abs(pulls) <= 2.0))
    median = float(np.median(pulls))
    assert 0.60 <= one <= 0.76, (one, two, median)
    assert 0.92 <= two <= 0.98, (one, two, median)
    assert abs(median) <= 0.2, (one, two, median)


def test_a_known_depth_is_recovered():
    _, _, _, result = _measure((3400, "white", 0.001))
    assert result["status"] == "ok"
    assert result["depth"] == pytest.approx(0.001, rel=0.05)


# --- the hidden-year reading of a replica is logged with its kind --------------------------------


def test_replicas_are_masked_and_read_through_the_logged_accessors():
    lc, infos = _hidden_lc(3004)
    eph, windows, replicas, plan = _geometry(infos)
    hidden = HiddenYear(lc, windows + replicas, plan)
    r = replicas[0]
    hidden.window(r.t_pred, r.half_width)
    hidden.local_baseline(r.t_pred, r.half_width)
    kinds = [e["kind"] for e in hidden.access_log]
    assert kinds == ["replica-window", "replica-baseline"]
    assert isinstance(lc, LightCurveData)
